#!/usr/bin/env python3
"""All P4-owned W3C strings, names, counts and retained order in actual bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
The SOAP 1.2 descriptions are explicit derivatives changing only the binding
extension namespace; all original descriptions and input messages stay pinned.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

import contract
import corpus
import coverage
from independent import SchemaJob, run as run_independent
import survey


FAMILIES = ('ChoiceChoice', 'ChoiceMaxOccursFinite', 'ChoiceMaxOccursUnbounded', 'ChoiceMinOccursFinite',
            'MinOccurs1', 'SequenceChoice', 'SequenceMaxOccursFinite', 'SequenceMaxOccursUnbounded',
            'SequenceMinOccurs0', 'SequenceMinOccurs0MaxOccursUnbounded', 'SequenceMinOccurs1MaxOccursUnbounded',
            'SequenceMinOccursFinite', 'SequenceSequenceElement')
ROOT = Path(__file__).resolve().parent


class ParticleCorpusTest(unittest.TestCase):
    def setUp(self):
        # a verified corpus root may be supplied; otherwise the pinned archive is extracted for this test
        configured = os.environ.get('WSDL_CORPUS')
        if configured:
            self.base = Path(configured)
        else:
            temporary = tempfile.TemporaryDirectory(prefix='wsdl-particle-corpus-')
            self.addCleanup(temporary.cleanup)
            self.base = corpus.extract(Path(temporary.name) / 'corpus')

    def test_original_corpus_values_and_retained_order(self):
        base = self.base
        records = {r['case']: r for r in corpus.read_manifest(ROOT / 'adjudication-report.json')['cases']}
        selection = corpus.read_manifest(ROOT / 'strict-selection.json')
        cases, expected, schemas, documents, parts, compilers = [], {}, {}, {}, {}, {}
        for name in FAMILIES:
            record = records[name]
            self.assertTrue(record['source_decision']['valid'])
            original = (base / name / ('echo' + name + '.wsdl')).read_bytes()
            corpus.check_digest(original, record['wsdl_sha256'], name)
            tree = etree.fromstring(original)
            schema = tree.find(f'{{{contract.WSDL}}}types/{{{contract.XSD}}}schema')
            schema_bytes = etree.tostring(schema)
            corpus.check_digest(schema_bytes, record['schemas']['inline']['sha256'], name + '/inline')
            schemas[name] = schema_bytes
            compilers[name] = etree.XMLSchema(etree.fromstring(schema_bytes))
            documents[name] = {}
            leaves = sorted({f'{{{schema.get("targetNamespace")}}}' + node.get('name')
                             for node in schema.iter(f'{{{contract.XSD}}}element')
                             if node.get('type') == 'xs:string'})
            self.assertTrue(leaves)
            for version in ('11', '12'):
                source = original.decode()
                if version == '12':
                    source = source.replace('http://schemas.xmlsoap.org/wsdl/soap/',
                                            'http://schemas.xmlsoap.org/wsdl/soap12/')
                identity = contract.describe(etree.fromstring(source.encode()))
                self.assertEqual(1, len(identity['ports']))
                binding_name = identity['ports'][0]['binding']
                binding = identity['bindings'][binding_name]
                self.assertEqual(version, binding['soap_version'])
                operation = identity['port_types'][binding['port_type']]['operations'][0]
                messages = []
                for file, info in record['messages'].items():
                    if not file.endswith('soap' + version + '.xml'):
                        continue
                    raw = (base / file).read_bytes()
                    corpus.check_digest(raw, info['sha256'], file)
                    before = survey.payload(raw, survey.parser(base))
                    valid = info['decision']['valid']
                    assertion = {'elements': [before.tag], 'datatype': 'particle', 'leaves': leaves,
                                 'order': 'per-name'}
                    self.assertEqual([assertion] if valid else [], selection['cases'][name]['messages'][file])
                    expected[file] = before, valid, assertion
                    messages.append({'file': file, 'envelope': raw.decode()})
                for response, direction in ((False, 'input'), (True, 'output')):
                    declaration = identity['messages'][operation[direction]['message']]
                    parts[name, response] = [p['name'] for p in declaration['parts']]
                cases.append({'name': name + '/' + version, 'wsdl': source,
                              'binding': etree.QName(binding_name).localname, 'operation': operation['name'],
                              'messages': messages})
        self.assertEqual(60, len(expected))
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        with tempfile.TemporaryDirectory(prefix='particle-corpus-') as temporary:
            manifest = Path(temporary) / 'cases.json'
            manifest.write_text(json.dumps(cases))
            run = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                  str(ROOT / 'particle-corpus.qr'), str(manifest)],
                                 text=True, capture_output=True, timeout=180, check=True)
        self.assertEqual('', run.stderr)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        identities = {(case['name'], message['file'], copy, response) for case in cases
                      for message in case['messages'] for copy in (False, True) for response in (False, True)}
        self.assertEqual(240, len(rows))
        self.assertEqual(identities, {(r['case'], r['file'], r['copy'], r['response']) for r in rows})
        rejected = 0
        for index, row in enumerate(rows):
            before, valid, assertion = expected[row['file']]
            name, version = row['case'].split('/')
            if not valid:
                rejected += 1
                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['native_error'], row)
                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['retained_error'], row)
                self.assertNotIn('native_xml', row)
                self.assertNotIn('retained_xml', row)
                continue
            self.assertEqual('', row['native_error'], row)
            self.assertEqual('', row['retained_error'], row)
            self.assertEqual(parts[name, row['response']], row['parts'])
            for field, order in (('native_xml', 'per-name'), ('retained_xml', 'exact'), ('retained', 'exact')):
                output = etree.fromstring(row[field].encode())
                if field != 'retained':
                    self.assertEqual('{' + survey.SOAP_NAMESPACES[int(version == '12')] + '}Envelope', output.tag)
                    output = output.find('{*}Body')[0]
                result = coverage.value_checks(before, output, [dict(assertion, order=order)])
                self.assertTrue(result['ok'], (row['file'], field, result))
                compiled = compilers[name]
                self.assertTrue(compiled.validate(output), str(compiled.error_log))
                documents[name][f'{index}/{field}'] = etree.tostring(output)
        jobs = [SchemaJob(name, survey.SOURCE + name + '/echo' + name + '.wsdl', source, documents[name])
                for name, source in schemas.items()]
        oracle = run_independent(jobs)
        self.assertEqual(8, rejected)
        self.assertEqual(696, len(oracle['documents']))
        for identity, result in oracle['documents'].items():
            self.assertTrue(result['ok'], (identity, result))
        print(f'{mode}: {len(rows)} rows; {rejected} required source rejections; '
              f"{len(oracle['documents'])} independently validated outputs", flush=True)


if __name__ == '__main__':
    unittest.main()
