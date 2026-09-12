#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""WSDL element wildcard assessment, values, outgoing validation and providers."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_native_wildcard_types import models, XSI, XSD


def qname(node, lexical):
    parts = lexical.split(':', 1)
    prefix, local = parts if len(parts) == 2 else (None, parts[0])
    uri = node.nsmap.get(prefix)
    return (uri if prefix is not None else uri or '', local)


def content(node):
    attributes = dict(node.attrib)
    selected = attributes.get('{' + XSI + '}type')
    if selected is not None:
        attributes['{' + XSI + '}type'] = qname(node, selected)
    value = node.text or ''
    if selected is not None and qname(node, selected) == (XSD, 'QName'):
        value = qname(node, value)
    return (node.tag, attributes, value, [(content(child), child.tail or '') for child in node])


class WildcardElementsTest(unittest.TestCase):
    def test_assessment_values_serialization_and_providers(self):
        fixtures = list(models())
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        worker = os.environ.get('WSDL_WILDCARD_ELEMENTS_WORKER',
                                str(Path(__file__).with_name('wildcard-elements.qr')))
        with tempfile.TemporaryDirectory(prefix='wsdl-wildcard-elements-') as folder:
            manifest = Path(folder) / 'manifest.json'
            manifest.write_text(json.dumps(fixtures))
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode, worker, str(manifest)],
                                    capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(684, len(rows))
        jobs = []
        index = 0
        for model in fixtures:
            documents = {}
            for document in model['documents']:
                row = rows[index]
                index += 1
                self.assertEqual((model['name'], document['name']), (row['model'], row['document']))
                for path in ('decoded', 'encoded', 'provider'):
                    self.assertEqual(document['valid'], bool(row.get(path)), (path, row))
                if document['valid']:
                    self.assertNotIn('error', row, row)
                    self.assertTrue(row['native_output'], row)
                    self.assertTrue(row['reader_output'], row)
                    expected = content(etree.fromstring(document['xml'].encode()))
                    for path in ('output', 'direct_output'):
                        self.assertEqual(expected, content(etree.fromstring(row[path].encode())), (path, row))
                        documents[document['name'] + '/' + path] = row[path].encode()
                else:
                    self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['error'], row)
                    self.assertEqual('SOAP-SERIALIZATION-ERROR', row['encode_error'], row)
                    self.assertEqual('RUNTIME-TYPE-ERROR', row['provider_error'], row)
                documents[document['name'] + '/input'] = document['xml'].encode()
            jobs.append(SchemaJob(model['name'], f'http://example.invalid/wsdl-wildcards/{len(jobs)}.xsd',
                                  model['schema'].encode(), documents))
        oracle = run_independent(jobs)
        self.assertEqual({model['name'] for model in fixtures}, set(oracle['schemas']))
        expected_documents = set()
        for model in fixtures:
            self.assertTrue(oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for document in model['documents']:
                paths = ('input', 'output', 'direct_output') if document['valid'] else ('input',)
                for path in paths:
                    key = document['name'] + '/' + path
                    expected_documents.add(key)
                    self.assertEqual(document['valid'], oracle['documents'][key]['ok'], key)
                    self.assertEqual([], oracle['documents'][key]['warnings'], key)
        self.assertEqual(expected_documents, set(oracle['documents']))


if __name__ == '__main__':
    unittest.main()
