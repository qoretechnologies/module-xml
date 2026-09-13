#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Preserved binary constraint values through saved services and SOAP bindings."""
import base64
import json
import os
from pathlib import Path
import subprocess
import unittest
from lxml import etree
from independent import SchemaJob, run
from test_binary_constraints import fixtures, FIXTURE
from survey import SOAP_NAMESPACES


def meaning(node, model):
    name = model['name']

    def octets(text):
        return base64.b64decode(''.join(text.split()), validate=True) if 'base64' in name else bytes.fromhex(text)

    def value(text):
        if 'string-first' in name:
            return 'string', text
        if 'list' in name:
            return tuple(('QName', node.nsmap[token.split(':')[0]], token.split(':')[1]) if ':' in token
                         else ('bytes', octets(token)) for token in text.split())
        return 'bytes', octets(text)

    return (node.tag, tuple(sorted((k, value(v)) for k, v in node.attrib.items())),
            value(node.text or '') if len(node) == 0 else None, tuple(meaning(child, model) for child in node))


class WsdlBinaryConstraintsTest(unittest.TestCase):
    def test_source_saved_providers_and_both_bindings(self):
        models = fixtures()
        self.assertEqual(206, len(models))
        self.assertEqual(models, json.loads(FIXTURE.read_text()))
        # This worker takes an arbitrary constraint fixture file. Sharing it with
        # the numeric matrix keeps identical saved-provider/direction accounting.
        worker = Path(os.environ.get('QORE_BINARY_CONSTRAINT_WORKER',
                                     Path(__file__).with_name('numeric-constraints.qr')))
        process = subprocess.run(['qore', '-b', '--enable-debug', str(worker), str(FIXTURE)],
                                 capture_output=True, text=True, timeout=180)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual('', process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        expected = {(model['name'], stage) for model in models
                    for stage in ['schema-construction', 'soap11-construction', 'soap12-construction']}
        expected |= {(model['name'], 'soap' + version + '-' + direction + '-' + source)
                     for model in models if model['valid'] for version in ['11', '12']
                     for direction in ['request', 'response'] for source in ['source', 'saved']}
        self.assertEqual(1498, len(expected))
        self.assertEqual(len(expected), len(rows))
        self.assertEqual(expected, {(row['name'], row['stage']) for row in rows})
        indexed = {model['name']: model for model in models}
        jobs = {m['name']: SchemaJob(m['name'], 'http://example.invalid/binary-constraints/' + str(i) + '.xsd',
                                    m['schema'].encode(), {m['name'] + '/input': m['xml'].encode()})
                for i, m in enumerate(models)}
        for row in rows:
            model = indexed[row['name']]
            with self.subTest(name=row['name'], stage=row['stage']):
                if row['stage'].endswith('construction'):
                    self.assertEqual(None if model['valid'] else 'WSDL-ERROR', row['error'])
                    continue
                envelope = etree.fromstring(row['xml'].encode())
                namespace = SOAP_NAMESPACES[0 if row['stage'].startswith('soap11') else 1]
                self.assertEqual('{' + namespace + '}Envelope', envelope.tag)
                body = envelope.find('{' + namespace + '}Body')
                self.assertEqual(1, len(body))
                self.assertEqual(meaning(etree.fromstring(model['xml'].encode()), model), meaning(body[0], model))
                jobs[row['name']].documents[row['name'] + '/' + row['stage']] = etree.tostring(body[0])
        oracle = run(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(1086, len(oracle['documents']))
        for model in models:
            self.assertEqual(model['valid'], oracle['schemas'][model['name']]['ok'], model['name'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for key in jobs[model['name']].documents:
                self.assertEqual(True if model['valid'] else None, oracle['documents'][key]['ok'], key)
                self.assertEqual([], oracle['documents'][key]['warnings'])


if __name__ == '__main__':
    unittest.main()
