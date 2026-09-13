#!/usr/bin/env python3
"""Document identity closure and independently validated SOAP payloads.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as independent
from test_native_id_bindings import XERCES_DISAGREEMENTS

ROOT = Path(__file__).resolve().parent


class IdBindingTest(unittest.TestCase):
    def test_selected_values_and_independent_outputs(self):
        source = ROOT / 'fixtures/id-bindings.json'
        fixture = json.loads(source.read_text())
        values = json.loads((ROOT / 'fixtures/id-binding-native-values.json').read_text())
        self.assertEqual(values['source_sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        with tempfile.TemporaryDirectory(prefix='wsdl-id-bindings-') as tmp:
            manifest = Path(tmp) / 'manifest.json'
            manifest.write_text(json.dumps(dict(models=fixture['models'], values=values['values'])))
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                     str(ROOT / 'id-bindings.qr'), str(manifest)],
                                    text=True, capture_output=True, timeout=120)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual('', result.stderr)
        rows = json.loads(result.stdout)
        expected = {doc['name']: doc for model in fixture['models'] for doc in model['documents']}
        self.assertEqual(set(expected), set(values['values']))
        self.assertEqual(340, len(rows))
        stages = {'schema', 'soap11-request', 'soap11-response', 'soap12-request', 'soap12-response'}
        self.assertEqual({(case, stage) for case in expected for stage in stages},
                         {(row['name'], row['stage']) for row in rows})
        documents = {name: {name: doc['xml'].encode()} for name, doc in expected.items()}
        output_cases = {}
        for row in rows:
            case = expected[row['name']]
            if not case['valid']:
                self.assertNotIn('xml', row, row)
                self.assertEqual('SOAP-SERIALIZATION-ERROR', row['error']['err'], row)
                self.assertIn('cvc-id.', row['error']['desc'], row)
                continue
            self.assertNotIn('error', row, row)
            xml = etree.fromstring(row['xml'].encode())
            if row['stage'] != 'schema':
                ns = ('http://schemas.xmlsoap.org/soap/envelope/' if row['stage'].startswith('soap11')
                      else 'http://www.w3.org/2003/05/soap-envelope')
                self.assertEqual('{' + ns + '}Envelope', xml.tag)
                body = xml.find('{' + ns + '}Body')
                self.assertIsNotNone(body)
                self.assertEqual(1, len(body))
                xml = body[0]
            self.assertEqual('value', xml.tag)
            name = row['name'] + '/' + row['stage']
            documents[row['name']][name] = etree.tostring(xml)
            output_cases[name] = row['name']
        self.assertEqual(210, len(output_cases))
        jobs = [SchemaJob(model['name'], f'http://example.invalid/identities/{i}.xsd',
                          model['schema'].encode(),
                          {name: xml for doc in model['documents']
                           for name, xml in documents[doc['name']].items()})
                for i, model in enumerate(fixture['models'])]
        oracle = independent(jobs)
        self.assertEqual(278, len(oracle['documents']))
        for schema in oracle['schemas'].values():
            self.assertTrue(schema['ok'], schema)
            self.assertEqual([], schema['warnings'])
        disagreements = set()
        for name, verdict in oracle['documents'].items():
            case = output_cases.get(name, name)
            valid = name in output_cases or expected[case]['valid']
            self.assertEqual([], verdict['warnings'], verdict)
            if verdict['ok'] != valid:
                disagreements.add(name)
        expected_disagreements = XERCES_DISAGREEMENTS | {
            name for name, case in output_cases.items() if case in XERCES_DISAGREEMENTS}
        self.assertEqual(expected_disagreements, disagreements)


if __name__ == '__main__':
    unittest.main()
