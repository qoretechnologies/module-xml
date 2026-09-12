#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Receiving fixed constraints through saved schemas, providers and actual SOAP bindings."""
import base64
import copy
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as independent
from test_attribute_values import description, NS, XSD
from test_native_value_spaces import fixed_models, dynamic_fixed_models
from test_mixed_values import qname
import calendar_reference
import duration_reference
import survey

XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def fixtures():
    originals = list(fixed_models()) + list(dynamic_fixed_models())
    for model in originals:
        schema = etree.fromstring(model['schema'].encode())
        schema.set('targetNamespace', NS)
        scoped = etree.Element(schema.tag, nsmap=dict(schema.nsmap, t=NS))
        scoped.attrib.update(schema.attrib)
        scoped.extend(list(schema))
        schema = scoped
        for child in schema.iter():
            for key in ['type', 'base', 'itemType', 'memberTypes']:
                if key in child.attrib:
                    child.set(key, ' '.join('t:' + part if ':' not in part else part
                                           for part in child.get(key).split()))
        element = schema.find('{' + XSD + '}element')
        fixed = element.get('fixed')
        for root in ['value', 'Submit', 'Reply']:
            clone = copy.deepcopy(element)
            clone.set('name', root)
            schema.append(clone)
        schema.remove(element)
        source = etree.tostring(schema).decode()
        documents = []
        for document in model['documents']:
            original = etree.fromstring(document['xml'].encode())
            def payload(root):
                value = etree.Element('{' + NS + '}' + root, nsmap=dict(original.nsmap, t=NS))
                value.attrib.update(original.attrib)
                value.text = original.text
                value.extend(copy.deepcopy(list(original)))
                return etree.tostring(value).decode()
            messages = []
            for version, envelope in zip(['11', '12'], survey.SOAP_NAMESPACES):
                for direction, root in [('request', 'Submit'), ('response', 'Reply')]:
                    messages.append({'binding': 'Soap' + version, 'direction': direction,
                                     'xml': f'<s:Envelope xmlns:s="{envelope}"><s:Body>'
                                     + payload(root) + '</s:Body></s:Envelope>'})
            documents.append(dict(document, xml=payload('value'), messages=messages))
        yield dict(model, schema=source, documents=documents, fixed=fixed,
                   declared_type=qname(schema, element.get('type')),
                   selected=model['name'].startswith('dynamic-fixed/'),
                   bindings={'Soap' + version: description(version, source) for version in ['11', '12']})


def scalar(node, model):
    text = ''.join(node.itertext())
    # Empty XML elements use their receiving constraint, including empty-list values.
    # This compares the XML schema value; native empty-element default projection
    # is tracked separately from explicit fixed-value checking.
    if not text:
        text = model['fixed']
    kind = model['name'].split('/')[1]
    if model['selected']:
        kind = (qname(node, node.get('{' + XSI + '}type')) if node.get('{' + XSI + '}type')
                else model['declared_type'])[1]
    if kind in ['int', 'integer', 'integer-precision', 'decimal', 'decimal-precision']:
        return 'decimal', Decimal(text)
    if kind == 'boolean':
        return 'boolean', text.strip() in ['true', '1']
    if kind in ['float', 'float-zero', 'double', 'double-NaN', 'double-INF']:
        value = Decimal(text)
        return kind.split('-')[0], 'NaN' if value.is_nan() else value
    if kind.startswith('list-'):
        return 'list', tuple(Decimal(part) for part in text.split())
    if kind == 'QName':
        return 'QName', qname(node, text.strip())
    if kind == 'date':
        return 'date', calendar_reference.value('date', text)
    if kind == 'duration':
        return 'duration', duration_reference.value(text)
    if kind in ['dateTime', 'time']:
        match = re.fullmatch(r'(?:(\d{4})-(\d{2})-(\d{2})T)?(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)(Z|[+-]\d{2}:\d{2})?', text)
        if not match:
            raise ValueError(text)
        year, month, day, hour, minute, second, zone = match.groups()
        seconds = Decimal(hour) * 3600 + Decimal(minute) * 60 + Decimal(second)
        if zone and zone != 'Z':
            seconds -= (1 if zone[0] == '+' else -1) * (int(zone[1:3]) * 3600 + int(zone[4:]) * 60)
        if kind == 'dateTime':
            seconds += calendar_reference.ordinal(int(year), int(month), int(day)) * 86400
        else:
            seconds %= 86400
        return kind, bool(zone), seconds
    if kind == 'hexBinary':
        return kind, bytes.fromhex(text)
    if kind == 'base64Binary':
        return kind, base64.b64decode(re.sub(r'[ \t\r\n]', '', text), validate=True)
    if kind == 'normalizedString':
        text = re.sub(r'[\t\r\n]', ' ', text)
    if kind in ['token', 'anyURI']:
        text = re.sub(r'[ \t\r\n]+', ' ', text).strip(' ')
    return 'anyURI' if kind == 'anyURI' else 'string', text


def meaning(node, model):
    attributes = tuple(sorted((key, qname(node, value) if key == '{' + XSI + '}type'
                               else int(value) if key == 'tag' else value) for key, value in node.attrib.items()
                               if key != '{' + XSI + '}type'))
    children = tuple(etree.QName(child).text for child in node if isinstance(child.tag, str))
    selected = qname(node, node.get('{' + XSI + '}type')) if node.get('{' + XSI + '}type') else tuple(model['declared_type'])
    return attributes, selected, children, scalar(node, model)


class FixedValuesTest(unittest.TestCase):
    def test_fixed_values_and_bindings(self):
        models = list(fixtures())
        self.assertEqual(53, len(models))
        cases = {document['name']: (model, document) for model in models for document in model['documents']}
        self.assertEqual(172, len(cases))
        jobs = [SchemaJob(model['name'], f'http://example.invalid/fixed/{index}.xsd', model['schema'].encode(),
                          {doc['name']: doc['xml'].encode() for doc in model['documents']})
                for index, model in enumerate(models)]
        oracle = independent(jobs)
        self.assertEqual(set(cases), set(oracle['documents']))
        for model in models:
            self.assertTrue(oracle['schemas'][model['name']]['ok'], oracle['schemas'][model['name']])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
        for name, (_, document) in cases.items():
            self.assertEqual(document['valid'], oracle['documents'][name]['ok'], (name, oracle['documents'][name]))
            self.assertEqual([], oracle['documents'][name]['warnings'])
        with tempfile.TemporaryDirectory(prefix='wsdl-fixed-values-') as folder:
            path = Path(folder) / 'fixtures.json'
            path.write_text(json.dumps(models))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + os.environ.get('QORE_EXEC_MODE', 'jit'),
                                      str(Path(__file__).with_name('mixed-values.qr')), str(path)],
                                     capture_output=True, text=True, timeout=240)
            self.assertEqual(0, process.returncode, process.stdout[-5000:] + process.stderr)
            self.assertEqual('', process.stderr)
            rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(cases), len(rows))
        self.assertEqual(set(cases), {row['name'] for row in rows})
        outputs = {model['name']: {} for model in models}
        for row in rows:
            model, document = cases[row['name']]
            with self.subTest(document=row['name']):
                self.assertEqual(document['valid'], bool(row.get('decoded')), row)
                self.assertEqual(document['valid'], bool(row.get('retained')), row)
                self.assertEqual(4, len(row['messages']))
                self.assertEqual({(version, direction) for version in ['Soap11', 'Soap12'] for direction in ['request', 'response']},
                                 {(message['binding'], message['direction']) for message in row['messages']})
                if not document['valid']:
                    self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['error'], row)
                    self.assertEqual('SOAP-SERIALIZATION-ERROR', row['retained_error'], row)
                    self.assertEqual({}, row['outputs'])
                    for message in row['messages']:
                        self.assertFalse(message.get('decoded'), message)
                        self.assertEqual('SOAP-DESERIALIZATION-ERROR', message['error'], message)
                    continue
                self.assertNotIn('error', row, row)
                self.assertEqual(5 if model['selected'] else 8, len(row['outputs']))
                expected = meaning(etree.fromstring(document['xml'].encode()), model)
                for key, output in row['outputs'].items():
                    self.assertEqual(expected, meaning(etree.fromstring(output.encode()), model), (key, row))
                    outputs[model['name']][row['name'] + '/' + key] = output.encode()
                for message in row['messages']:
                    self.assertTrue(message.get('decoded'), message)
                    self.assertNotIn('error', message, message)
                    envelope = etree.fromstring(message['output'].encode())
                    self.assertEqual('{' + survey.SOAP_NAMESPACES[message['binding'] == 'Soap12'] + '}Envelope', envelope.tag)
                    payload = envelope.find('{*}Body')[0]
                    self.assertEqual('{' + NS + '}' + ('Reply' if message['direction'] == 'response' else 'Submit'), payload.tag)
                    self.assertEqual(expected, meaning(payload, model), message)
                    outputs[model['name']][row['name'] + '/' + message['binding'] + '/' + message['direction']] = etree.tostring(payload)
        checked = independent([SchemaJob(model['name'], jobs[index].uri, model['schema'].encode(), outputs[model['name']])
                               for index, model in enumerate(models)])
        self.assertEqual(sum(len(records) for records in outputs.values()), len(checked['documents']))
        for name, result in checked['documents'].items():
            self.assertTrue(result['ok'], (name, result))
            self.assertEqual([], result['warnings'])
        print(f'{len(models)} schemas, {len(cases)} documents, {len(cases) * 4} real SOAP directions, '
              f'{len(checked["documents"])} independently valid outputs')


if __name__ == '__main__':
    unittest.main()
