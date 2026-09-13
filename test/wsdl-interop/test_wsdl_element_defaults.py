#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Canonical defaults through saved providers and both SOAP binding directions."""
import json
import os
from pathlib import Path
import subprocess
import unittest

from lxml import etree
from independent import SchemaJob, run
from test_element_defaults import FIXTURE, fixtures, XSI
from survey import SOAP_NAMESPACES


class WsdlElementDefaultsTest(unittest.TestCase):
    def test_binding_matrix(self):
        models = [model for model in fixtures() if model['wsdl']]
        self.assertEqual(40, len(models))
        self.assertEqual(fixtures(), json.loads(FIXTURE.read_text()))
        worker = Path(os.environ.get('QORE_ELEMENT_DEFAULT_WORKER',
                                     Path(__file__).with_name('element-defaults.qr')))
        result = subprocess.run(['qore', '-b', '--enable-debug', str(worker), str(FIXTURE)],
                                capture_output=True, text=True, timeout=300)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        expected = {(document['name'], version, saved, response, preserve)
                    for model in models for document in model['documents']
                    for version in ['11', '12'] for saved in [False, True]
                    for response in [False, True] for preserve in [False, True]}
        self.assertEqual(3200, len(expected))
        self.assertEqual(len(expected), len(rows))
        self.assertEqual(expected, {(r['name'], r['version'], r['saved'], r['response'], r['preserve']) for r in rows})
        documents = {d['name']: d for m in models for d in m['documents']}
        jobs = {m['name']: SchemaJob(m['name'], f'http://example.invalid/wsdl-defaults/{i}.xsd',
                                    m['schema'].encode(), {}) for i, m in enumerate(models)}
        # Retain every pinned-Xerces difference from the native source matrix.
        # Legacy projection can omit xsi:type and materialize canonical text;
        # those outputs are assessed as written, without inventing retained type.
        oracle_expected = {}
        valid = 0
        for index, row in enumerate(rows):
            document = documents[row['name']]
            with self.subTest(name=row['name'], version=row['version'], saved=row['saved'],
                              response=row['response'], preserve=row['preserve']):
                self.assertEqual(None if document['expected'] else 'SOAP-DESERIALIZATION-ERROR', row.get('error'), row)
                if not document['expected']:
                    continue
                valid += 1
                empty = row['name'].split('/')[-1] in ('empty', 'comment', 'cdata')
                self.assertEqual(empty and row['preserve'], row['defaulted'])
                root = etree.fromstring(row['xml'].encode())
                ns = SOAP_NAMESPACES[0 if row['version'] == '11' else 1]
                self.assertEqual('{' + ns + '}Envelope', root.tag)
                body = root.find('{' + ns + '}Body')
                self.assertEqual(1, len(body))
                payload = body[0]
                self.assertEqual('value', payload.tag)
                if row['preserve']:
                    self.assertEqual(empty, not bool(payload.text))
                    selected = payload.get('{' + XSI + '}type')
                    self.assertIsNotNone(selected)
                    self.assertEqual('Actual', selected.split(':')[-1])
                model_name = row['name'].rsplit('/', 1)[0]
                key = str(index)
                jobs[model_name].documents[key] = etree.tostring(payload)
                oracle_expected[key] = not (
                    row['name'] == 'time/fixed/source/source'
                    or row['name'].startswith('date/fixed/')
                    or (row['preserve'] and row['name'].startswith('date/default/canonical/') and empty))
        self.assertEqual(1760, valid)
        oracle = run(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(oracle_expected), set(oracle['documents']))
        for name, row in oracle['schemas'].items():
            self.assertTrue(row['ok'], name)
            self.assertEqual([], row['warnings'])
        for name, row in oracle['documents'].items():
            self.assertEqual(oracle_expected[name], row['ok'], (name, row))
            self.assertEqual([], row['warnings'])


if __name__ == '__main__':
    unittest.main()
