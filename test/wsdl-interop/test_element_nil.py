#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Receiving-element nil rules through schemas, providers and actual SOAP bindings."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest
from xml.sax.saxutils import quoteattr

from lxml import etree
from independent import SchemaJob, run as independent
from test_attribute_values import description, NS, XSD
import survey

XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def models():
    attributes = ('<xs:attribute name="tag" type="xs:int" use="required"/>'
                  '<xs:attribute name="category" type="xs:QName" default="xs:int"/>'
                  '<xs:attribute name="prohibited" use="prohibited"/>')
    sequence = '<xs:sequence><xs:element name="child" type="xs:int"/></xs:sequence>'
    specs = [
        ('int', 'type="xs:int"', '', 'int', False, ''),
        ('anySimpleType', 'type="xs:anySimpleType"', '', 'text', False, ''),
        ('anyType', 'type="xs:anyType"', '', 'any', False, ''),
        ('empty', '', '<xs:complexType>' + attributes + '</xs:complexType>', 'empty', True, ''),
        ('sequence', '', '<xs:complexType>' + sequence + attributes + '</xs:complexType>', 'sequence', True, ''),
        ('simple', '', '<xs:complexType><xs:simpleContent><xs:extension base="xs:int">'
         + attributes + '</xs:extension></xs:simpleContent></xs:complexType>', 'int', True, ''),
        ('mixed', '', '<xs:complexType mixed="true"><xs:sequence><xs:element name="child" type="xs:int" '
         'minOccurs="0"/></xs:sequence>' + attributes + '</xs:complexType>', 'mixed', True, ''),
        ('selected-int', 'type="xs:anyType"', '', 'int', False, 'i:type="xs:int"'),
        ('selected-record', 'type="xs:anyType"', '', 'sequence', True, 'i:type="t:Record"'),
        ('fixed-int-nil', 'type="xs:int" fixed="17"', '', 'int', False, ''),
    ]
    contents = [('empty', ''), ('integer', '17'), ('space', ' '), ('child', '<child>17</child>'),
                ('comment', '<!--shipment-->'), ('empty-cdata', '<![CDATA[]]>'), ('space-cdata', '<![CDATA[ ]]>')]
    empty = {'empty', 'comment', 'empty-cdata'}
    for name, datatype, body, kind, attributed, selected in specs:
        for nullable in (False, True):
            model_name = name + '/' + str(nullable)
            fixed = name == 'fixed-int-nil'
            declarations = ''.join(f'<xs:element name="{root}" {datatype} nillable="{str(nullable).lower()}">'
                                   f'{body}</xs:element>' for root in ['value', 'Submit', 'Reply'])
            extra = ('<xs:complexType name="Record">' + sequence + attributes + '</xs:complexType>'
                     if name == 'selected-record' else '')
            schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">'
                      + declarations + extra + '</xs:schema>')
            documents = []
            for lexical in ('true', '1', ' true ', 'false', '0', ' false ', '', 'TRUE', 'invalid'):
                for content_name, content in contents:
                    # Fixed non-nilled empty/default assessment belongs to the subsequent value increment.
                    if fixed and lexical.strip() in ('false', '0') and content_name != 'integer':
                        continue
                    nilled = lexical.strip() in ('true', '1')
                    valid = nullable and lexical.strip() in ('true', '1', 'false', '0')
                    if nilled:
                        valid = valid and content_name in empty and not fixed
                    elif kind == 'int':
                        valid = valid and content_name == 'integer'
                    elif kind == 'text':
                        valid = valid and content_name != 'child'
                    elif kind == 'empty':
                        valid = valid and content_name in empty
                    elif kind == 'sequence':
                        valid = valid and content_name == 'child'
                    supplied = (('tag="+017" ' if attributed else '') + selected + ' i:nil=' + quoteattr(lexical))
                    cases = [(content_name, supplied, valid)]
                    if attributed and lexical == 'true' and content_name == 'empty':
                        cases += [(label, bad + ' ' + selected + ' i:nil="true"', False) for label, bad in
                                  [('missing-attribute', ''), ('bad-attribute', 'tag="bad"'),
                                   ('prohibited-attribute', 'tag="17" prohibited="no"'),
                                   ('unknown-attribute', 'tag="17" unknown="no"')]]
                    for case_name, supplied, valid in cases:
                        identity = f'{model_name}/{lexical!r}/{case_name}'
                        def payload(root):
                            return (f'<t:{root} xmlns:t="{NS}" xmlns:xs="{XSD}" xmlns:i="{XSI}" '
                                    + supplied + '>' + content + f'</t:{root}>')
                        messages = []
                        for version, envelope in zip(('11', '12'), survey.SOAP_NAMESPACES):
                            for direction, root in [('request', 'Submit'), ('response', 'Reply')]:
                                messages.append({'binding': 'Soap' + version, 'direction': direction,
                                                 'xml': f'<s:Envelope xmlns:s="{envelope}"><s:Body>'
                                                        + payload(root) + '</s:Body></s:Envelope>'})
                        documents.append({'name': identity, 'xml': payload('value'), 'valid': valid,
                                          'nilled': nilled, 'content_name': content_name, 'messages': messages})
            yield {'name': model_name, 'schema': schema, 'kind': kind, 'attributed': attributed,
                   'generic': datatype.startswith('type="xs:anyType"'), 'selected': bool(selected),
                   'bindings': {'Soap' + version: description(version, schema) for version in ['11', '12']},
                   'documents': documents}


def expanded_qname(node, text):
    if ':' in text:
        prefix, local = text.split(':')
        return node.nsmap[prefix], local
    return node.nsmap.get(None, ''), text


def meaning(node, model):
    nilled = node.get('{' + XSI + '}nil', '').strip() in ('true', '1')
    attributes = {}
    for key, value in node.attrib.items():
        if key.startswith('{' + XSI + '}'):
            continue
        attributes[key] = int(value) if key == 'tag' else expanded_qname(node, value) if key == 'category' else value
    if model['attributed'] and 'category' not in attributes:
        attributes['category'] = (XSD, 'int')
    children = [(child.tag, int(child.text)) for child in node if isinstance(child.tag, str)]
    text = ''.join(node.itertext()) if not children else node.text or ''
    if model['kind'] == 'int' and not nilled:
        text = int(text)
    return nilled, attributes, text, children


class ElementNilTest(unittest.TestCase):
    def test_nil_rules_values_and_both_bindings(self):
        fixtures = list(models())
        cases = {d['name']: (model, d) for model in fixtures for d in model['documents']}
        self.assertEqual(sum(len(m['documents']) for m in fixtures), len(cases))
        jobs = [SchemaJob(model['name'], f'http://example.invalid/nil/{index}.xsd', model['schema'].encode(),
                          {d['name']: d['xml'].encode() for d in model['documents']})
                for index, model in enumerate(fixtures)]
        oracle = independent(jobs)
        self.assertEqual(set(cases), set(oracle['documents']))
        for model in fixtures:
            self.assertTrue(oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
        for name, (_, document) in cases.items():
            self.assertEqual(document['valid'], oracle['documents'][name]['ok'], (name, oracle['documents'][name]))
            self.assertEqual([], oracle['documents'][name]['warnings'])
        with tempfile.TemporaryDirectory(prefix='wsdl-element-nil-') as folder:
            path = Path(folder) / 'fixtures.json'
            path.write_text(json.dumps(fixtures))
            command = ['qore', '-b', '--enable-debug', '--exec-mode=' + os.environ.get('QORE_EXEC_MODE', 'jit'),
                       str(Path(__file__).with_name('element-nil.qr')), str(path)]
            process = subprocess.run(command, capture_output=True, text=True, timeout=240)
            self.assertEqual(0, process.returncode, process.stdout + process.stderr)
            self.assertEqual('', process.stderr)
            rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(cases), len(rows))
        self.assertEqual(set(cases), {row['name'] for row in rows})
        outputs = {model['name']: {} for model in fixtures}
        for row in rows:
            model, document = cases[row['name']]
            with self.subTest(document=row['name']):
                self.assertEqual(document['valid'], bool(row.get('decoded')), row)
                self.assertEqual(document['valid'], bool(row.get('retained')), row)
                if model['generic']:
                    self.assertEqual(document['valid'], bool(row.get('encoded')), row)
                self.assertEqual({(v, d) for v in ['Soap11', 'Soap12'] for d in ['request', 'response']},
                                 {(r['binding'], r['direction']) for r in row['messages']})
                self.assertEqual(4, len(row['messages']))
                for message in row['messages']:
                    self.assertEqual(document['valid'], bool(message.get('decoded')), message)
                    if not document['valid']:
                        self.assertEqual('SOAP-DESERIALIZATION-ERROR', message['error'], message)
                if not document['valid']:
                    self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['error'], row)
                    self.assertEqual('SOAP-SERIALIZATION-ERROR', row['retained_error'], row)
                    if model['generic']:
                        self.assertEqual('SOAP-SERIALIZATION-ERROR', row['encode_error'], row)
                    continue
                self.assertNotIn('error', row, row)
                self.assertEqual(row['value'], row['provider_value'])
                if document['nilled']:
                    native = row['value'].get('^val^', row['value']) if model['selected'] else row['value']
                    if model['selected'] and not model['attributed']:
                        self.assertIsNone(native)
                    else:
                        self.assertTrue(native['nil'])
                        expected = {'tag': 17, 'category': {'qname': [XSD, 'int']}} if model['attributed'] else {}
                        self.assertEqual(expected, native['attributes'])
                expected = meaning(etree.fromstring(document['xml'].encode()), model)
                for key in ['output', 'retained_output'] + (['direct_output'] if model['generic'] else []):
                    actual = etree.fromstring(row[key].encode())
                    self.assertEqual(expected, meaning(actual, model), (key, row))
                    outputs[model['name']][row['name'] + '/' + key] = row[key].encode()
                for message in row['messages']:
                    self.assertNotIn('error', message, message)
                    envelope = etree.fromstring(message['output'].encode())
                    self.assertEqual('{' + survey.SOAP_NAMESPACES[message['binding'] == 'Soap12'] + '}Envelope', envelope.tag)
                    payload = envelope.find('{*}Body')[0]
                    self.assertEqual('{' + NS + '}' + ('Reply' if message['direction'] == 'response' else 'Submit'), payload.tag)
                    self.assertEqual(expected, meaning(payload, model), message)
                    outputs[model['name']][row['name'] + '/' + message['binding'] + '/' + message['direction']] = etree.tostring(payload)
        output_jobs = [SchemaJob(model['name'], f'http://example.invalid/nil/{index}.xsd', model['schema'].encode(),
                                 outputs[model['name']]) for index, model in enumerate(fixtures)]
        oracle = independent(output_jobs)
        self.assertEqual(sum(len(docs) for docs in outputs.values()), len(oracle['documents']))
        for name, result in oracle['documents'].items():
            self.assertTrue(result['ok'], (name, result))
            self.assertEqual([], result['warnings'])
        print(f'{len(fixtures)} schemas, {len(cases)} documents, {len(cases) * 4} real SOAP directions, '
              f'{len(oracle["documents"])} independently valid outputs')


if __name__ == '__main__':
    unittest.main()
