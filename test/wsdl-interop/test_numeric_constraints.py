#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Canonical WSDL declarations and preserved SOAP values against pinned Xerces."""
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import unittest

from lxml import etree
from independent import SchemaJob, run
from test_numeric_defaults import FIXTURE, fixtures
from survey import SOAP_NAMESPACES


def atom(text, model, node):
    name = model['name'].split('/')[0]
    if name == 'control':
        name = model['name'].split('/')[1]
    if name == 'empty-list':
        return ()
    if name.startswith('list-') or name == 'QName-list':
        return tuple(token(part, name, node) for part in text.split())
    return token(text, name, node)


def token(text, name, node):
    if ':' in text:
        prefix, local = text.strip().split(':')
        return 'QName', node.nsmap[prefix], local
    if 'boolean' in name or name in ['union-bool-first', 'list-bool', 'list-single', 'list-union']:
        if text.strip() not in ['true', 'false', '0', '1']:
            raise ValueError(text)
        return 'boolean', text.strip() in ['true', '1']
    if name.startswith('atomic-') or name in ['list-int', 'list-decimal', 'union-int-first']:
        return 'decimal', Decimal(text)
    return 'string', text


def meaning(node, model):
    return (node.tag,
            tuple(sorted((key, atom(text, model, node)) for key, text in node.attrib.items())),
            atom(node.text or '', model, node) if node.text is not None else None,
            tuple(meaning(child, model) for child in node))


class NumericConstraintsTest(unittest.TestCase):
    def test_saved_services_and_both_bindings(self):
        models = fixtures()
        self.assertEqual(396, len(models))
        self.assertEqual(models, json.loads(FIXTURE.read_text()))
        worker = Path(os.environ.get('QORE_NUMERIC_CONSTRAINT_WORKER',
                                     Path(__file__).with_name('numeric-constraints.qr')))
        process = subprocess.run(['qore', '-b', '--enable-debug', str(worker), str(FIXTURE)],
                                 text=True, capture_output=True, timeout=180)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual('', process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        expected = {(model['name'], stage) for model in models
                    for stage in ['schema-construction', 'soap11-construction', 'soap12-construction']}
        expected |= {(model['name'], 'soap' + version + '-' + direction + '-' + source)
                     for model in models if model['valid'] for version in ['11', '12']
                     for direction in ['request', 'response'] for source in ['source', 'saved']}
        self.assertEqual(len(expected), len(rows))
        self.assertEqual(expected, {(r['name'], r['stage']) for r in rows})
        indexed = {m['name']: m for m in models}
        documents = {m['name']: {m['name'] + '/input': m['xml'].encode()} for m in models}
        for row in rows:
            model = indexed[row['name']]
            with self.subTest(name=row['name'], stage=row['stage']):
                if row['stage'].endswith('construction'):
                    self.assertEqual(None if model['valid'] else 'WSDL-ERROR', row['error'])
                    continue
                envelope = etree.fromstring(row['xml'].encode())
                self.assertEqual('{' + SOAP_NAMESPACES[0 if row['stage'].startswith('soap11') else 1]
                                 + '}Envelope', envelope.tag)
                body = envelope.find('{*}Body')
                self.assertEqual(1, len(body))
                value = body[0]
                self.assertEqual(meaning(etree.fromstring(model['xml'].encode()), model), meaning(value, model))
                documents[model['name']][model['name'] + '/' + row['stage']] = etree.tostring(value)
        oracle = run([SchemaJob(m['name'], f'http://example.invalid/numeric-constraints/{i}.xsd',
                                m['schema'].encode(), documents[m['name']]) for i, m in enumerate(models)])
        self.assertEqual(set(indexed), set(oracle['schemas']))
        for model in models:
            self.assertEqual(model['valid'], oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for key in documents[model['name']]:
                self.assertEqual(True if model['valid'] else None, oracle['documents'][key]['ok'],
                                 (key, oracle['documents'][key]))
                self.assertEqual([], oracle['documents'][key]['warnings'])


if __name__ == '__main__':
    unittest.main()
