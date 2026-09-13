#!/usr/bin/env python3
"""NOTATION binding coverage, typed identities and explicit outstanding P5 findings.

Copyright (C) 2026 Qore Technologies, s.r.o.
This test verifies the coverage report as well as implemented conversions. The
report's open findings remain failed compatibility rows, not passing verdicts.
"""
import collections
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run

ROOT = Path(__file__).parent


def models():
    result = json.loads((ROOT / 'fixtures/notations.json').read_text())
    result += [dict(m, schema_valid=True) for m in json.loads((ROOT / 'fixtures/element-defaults.json').read_text())
               if m['name'].startswith('notation/')]
    return result


class WsdlNotationValuesTest(unittest.TestCase):
    def test_bindings_and_reported_identity_gaps(self):
        fixtures = models()
        self.assertEqual(66, len(fixtures))
        with tempfile.TemporaryDirectory(prefix='wsdl-notation-values-') as directory:
            fixture = Path(directory) / 'models.json'
            fixture.write_text(json.dumps(fixtures))
            completed = subprocess.run([os.environ.get('QORE', 'qore'), '-b', '--enable-debug',
                str(ROOT / 'notation-values.qr'), str(fixture)], capture_output=True, text=True, timeout=300)
        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout[-2000:])
        self.assertEqual('', completed.stderr)
        rows = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([m['name'] for m in fixtures], [r['name'] for r in rows])
        resources = {k: v.encode() for m in fixtures for k, v in m.get('resources', {}).items()}
        jobs = []
        output_expected = {}
        oracle_disagreements = []
        findings = []
        counts = collections.Counter()
        for index, (model, row) in enumerate(zip(fixtures, rows)):
            with self.subTest(schema=model['name']):
                self.assertEqual(model['schema_valid'], row['schema_valid'], row)
                if not model['schema_valid']:
                    self.assertEqual('XSD-SIMPLETYPE-ERROR' if model['name'] == 'missing-notation'
                                     else 'WSDL-ERROR', row['error'])
                    self.assertEqual([], row['documents'])
                    counts['invalid_schema_rejected'] += 1
                    continue
            expected = {(d['name'], v, s, r, p) for d in model['documents'] for v in ['11', '12']
                        for s in [False, True] for r in [False, True] for p in [False, True]}
            documents = {d['name']: d for d in model['documents']}
            self.assertEqual(expected, {(r['name'], r['version'], r['saved'], r['response'], r['preserve'])
                                        for r in row['documents']})
            self.assertEqual(len(expected), len(row['documents']))
            outputs = {}
            for ordinal, result in enumerate(row['documents']):
                document = documents[result['name']]
                label = {key: result[key] for key in ['name', 'version', 'saved', 'response', 'preserve']}
                failures = []
                with self.subTest(**label):
                    # These diagnoses are retained in the report as failures. All
                    # additional verdict or typed-value differences fail this gate.
                    duplicate = result['name'] == 'primitive-identity/notation-alias'
                    legacy_loss = result['name'] == 'primitive-identity/qname-same-name' and not result['preserve']
                    self.assertEqual(document['expected'] or duplicate, result['decoded'], result)
                    if not result['decoded']:
                        self.assertEqual('SOAP-DESERIALIZATION-ERROR', result['error'], result)
                        counts['invalid_document_rejected'] += 1
                        continue
                    self.assertNotIn('error', result)
                    if duplicate:
                        failures.append('invalid_input_accepted')
                    self.assertEqual(not (duplicate or legacy_loss), result['output_valid'], result)
                    if not result['output_valid']:
                        self.assertEqual('XSD-ERROR', result['output_error'])
                        failures.append('invalid_output')
                    same = result['identity'] == result['output_identity']
                    self.assertEqual(not legacy_loss, same, result)
                    if not same:
                        failures.append('primitive_identity_changed')
                    if failures:
                        findings.append(dict(label, status='failed', failures=failures,
                                             owner='P5 identity constraints and typed accounting'))
                        counts['failed_compatibility_rows'] += 1
                    else:
                        counts['valid_document_preserved'] += 1
                    envelope = etree.fromstring(result['xml'].encode())
                    namespace = 'http://schemas.xmlsoap.org/soap/envelope/' if result['version'] == '11' else 'http://www.w3.org/2003/05/soap-envelope'
                    self.assertEqual('{' + namespace + '}Envelope', envelope.tag)
                    body = envelope.find('{' + namespace + '}Body')
                    self.assertIsNotNone(body)
                    self.assertEqual(1, len(body))
                    key = f'{index}-{ordinal}'
                    outputs[key] = etree.tostring(body[0])
                    disagreement = result['preserve'] and result['name'] in {
                        'default/empty', 'fixed/empty', 'constraint-default/empty', 'constraint-fixed/empty',
                        'notation/default/empty', 'notation/fixed/empty'}
                    output_expected[key] = result['output_valid'] and not disagreement
                    if disagreement:
                        oracle_disagreements.append(dict(label, native=True, xerces=False,
                            reason='Xerces resolves the schema default in the instance namespace context'))
            if outputs:
                jobs.append(SchemaJob(model['name'], f'http://example.invalid/notations/{index}.xsd',
                                      model['schema'].encode(), outputs))
        oracle = run(jobs, resources)
        if target := os.environ.get('QORE_NOTATION_REPORT'):
            Path(target + '.oracle.json').write_text(json.dumps({'rows': rows, 'oracle': oracle, 'expected': output_expected}, indent=2) + '\n')
        self.assertEqual(set(output_expected), set(oracle['documents']))
        for name, row in oracle['schemas'].items():
            self.assertTrue(row['ok'], (name, row))
            self.assertEqual([], row['warnings'])
        for name, row in oracle['documents'].items():
            self.assertEqual(output_expected[name], row['ok'], (name, row))
            self.assertEqual([], row['warnings'])
        self.assertEqual(24, len(findings))
        self.assertEqual(48, len(oracle_disagreements))
        report = {'schema_count': len(fixtures), 'binding_rows': sum(len(r['documents']) for r in rows),
                  'counts': dict(counts), 'open_findings': findings, 'oracle_disagreements': oracle_disagreements,
                  'independently_validated_outputs': len(output_expected)}
        if target := os.environ.get('QORE_NOTATION_REPORT'):
            Path(target).write_text(json.dumps(report, indent=2) + '\n')
        print('NOTATION compatibility report: ' + json.dumps(report['counts'], sort_keys=True))

    def test_default_namespace_oracle_reduction(self):
        fixture = ROOT / 'fixtures/notation-default-context.json'
        cases = json.loads(fixture.read_text())
        self.assertEqual(4, len(cases))
        completed = subprocess.run([os.environ.get('QORE', 'qore'), '-b', '--enable-debug',
            str(ROOT / 'notations.qr'), str(fixture)], capture_output=True, text=True, timeout=120)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual('', completed.stderr)
        rows = [json.loads(line) for line in completed.stdout.splitlines()]
        expected = [d for m in cases for d in m['documents']]
        self.assertEqual([d['name'] for d in expected], [r['name'] for r in rows])
        for row in rows:
            for path in ['dom', 'reader', 'document']:
                self.assertTrue(row[path], row)
        oracle = run([SchemaJob(m['name'], f'http://example.invalid/default-context/{i}.xsd',
            m['schema'].encode(), {d['name']: d['xml'].encode() for d in m['documents']})
            for i, m in enumerate(cases)])
        for model in cases:
            self.assertTrue(oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for document in model['documents']:
                row = oracle['documents'][document['name']]
                self.assertEqual(document['xerces_expected'], row['ok'], (document['name'], row))
                self.assertEqual([], row['warnings'])


if __name__ == '__main__':
    unittest.main()
