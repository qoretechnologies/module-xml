#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Exact calendar values through saved services and both real SOAP binding models."""
import json
import os
from pathlib import Path
import subprocess
import unittest
from lxml import etree
from independent import SchemaJob, run
from calendar_reference import value as calendar_value
from temporal_reference import value as clock_value
from duration_reference import value as duration_value
from test_calendar_constraints import fixtures, FIXTURE, oracle_document_valid
from survey import SOAP_NAMESPACES


def meaning(node, model):
    name = model['name']
    builtin = name.split('/')[1] if name.startswith('control/') else name.split('/')[0].split('-')[0]
    if builtin in ('empty-list', 'singleton-list', 'mixed', 'time'):
        builtin = 'time'

    def scalar(text):
        if 'string-first' in name:
            return 'string', text
        if 'mixed-list' in name and not text[0].isdigit():
            prefix, separator, local = text.partition(':')
            return 'QName', node.nsmap[prefix] if separator else node.nsmap.get(None, ''), local if separator else prefix
        if builtin == 'duration':
            return 'duration', duration_value(text)
        return builtin, (clock_value(builtin, text) if builtin in ('time', 'dateTime')
                         else calendar_value(builtin, text))

    def value(text):
        return tuple(scalar(token) for token in text.split()) if 'list' in name else scalar(text)

    return (node.tag, tuple(sorted((key, value(text)) for key, text in node.attrib.items())),
            value(node.text or '') if len(node) == 0 and not node.attrib else None,
            tuple(meaning(child, model) for child in node))


class WsdlCalendarConstraintsTest(unittest.TestCase):
    def test_source_saved_providers_and_both_bindings(self):
        models = fixtures()
        self.assertEqual(306, len(models))
        self.assertEqual(models, json.loads(FIXTURE.read_text()))
        worker = Path(os.environ.get('QORE_CALENDAR_CONSTRAINT_WORKER',
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
        self.assertEqual(2214, len(expected))
        self.assertEqual(len(expected), len(rows))
        self.assertEqual(expected, {(row['name'], row['stage']) for row in rows})
        indexed = {model['name']: model for model in models}
        jobs = {m['name']: SchemaJob(m['name'], f'http://example.invalid/wsdl-calendar/{i}.xsd',
                                    m['schema'].encode(), {m['name'] + '/input': m['xml'].encode()})
                for i, m in enumerate(models)}
        payloads = 0
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
                payloads += 1
        self.assertEqual(1296, payloads)
        oracle = run(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(1602, len(oracle['documents']))
        differences = []
        for model in models:
            self.assertEqual(model['oracle_valid'], oracle['schemas'][model['name']]['ok'], model['name'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            if model['valid'] != model['oracle_valid']:
                self.assertTrue(model['oracle_reason'])
                differences.append(model['name'])
            for key in jobs[model['name']].documents:
                self.assertEqual(oracle_document_valid(model, jobs[model['name']].documents[key].decode()),
                                 oracle['documents'][key]['ok'], key)
                self.assertEqual([], oracle['documents'][key]['warnings'])
        self.assertEqual(48, len(differences))
        # The original oracle records above retain every schema rejection and
        # unreachable document. Separately identified derivatives remove only
        # default/fixed declaration attributes to assess the explicit instance
        # values, retaining all type restrictions and original fixture bytes.
        derivatives = []
        document_differences = [m['name'] for m in models if m['oracle_document_valid'] is False]
        self.assertEqual(30, len(document_differences))
        for name in differences + document_differences:
            original = jobs[name]
            schema = etree.fromstring(original.schema)
            removed = []
            for declaration in schema.iter():
                for attribute in ('default', 'fixed'):
                    if attribute in declaration.attrib:
                        removed.append((declaration.tag, attribute, declaration.attrib.pop(attribute)))
            self.assertEqual(1, len(removed))
            key = name + '/explicit-instance-derivative'
            derivatives.append(SchemaJob(key, original.uri + '.explicit-instance.xsd',
                                         etree.tostring(schema), {key + '/' + k: v for k, v in original.documents.items()}))
        independent_instances = run(derivatives)
        self.assertEqual(78, len(independent_instances['schemas']))
        self.assertEqual(702, len(independent_instances['documents']))
        for row in list(independent_instances['schemas'].values()) + list(independent_instances['documents'].values()):
            self.assertTrue(row['ok'], row)
            self.assertEqual([], row['warnings'])


if __name__ == '__main__':
    unittest.main()
