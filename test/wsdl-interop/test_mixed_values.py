#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Independent mixed-content values, order, providers and actual SOAP bindings."""
from pathlib import Path
import json
import os
import re
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as independent
from test_attribute_values import description, NS, XSD
import survey

XSI = 'http://www.w3.org/2001/XMLSchema-instance'
ATTRIBUTES = '<xs:attribute name="tag" type="xs:int" use="required"/>'


def fixtures():
    specs = [
        ('empty', '', '', [('', True), ('<a>17</a>', False)], False),
        ('sequence', '<xs:sequence><xs:element name="a" type="xs:int"/>'
         '<xs:element name="b" type="xs:QName"/></xs:sequence>', '',
         [('<a>+017</a><b>p:Part</b>', True), ('', False), ('<b>p:Part</b><a>17</a>', False),
          ('<a>bad</a><b>p:Part</b>', False), ('<a>17</a><b>unbound:Part</b>', False)], False),
        ('groups', '<xs:sequence minOccurs="2" maxOccurs="2"><xs:element name="a" type="xs:int"/>'
         '<xs:element name="b" type="xs:QName"/></xs:sequence>', '',
         [('<a>17</a><b>p:A</b><a>29</a><b>p:B</b>', True), ('<a>17</a><b>p:A</b>', False),
          ('<a>17</a><a>29</a><b>p:A</b><b>p:B</b>', False)], False),
        ('choice', '<xs:choice minOccurs="0" maxOccurs="4"><xs:element name="a" type="xs:int"/>'
         '<xs:element name="b" type="xs:QName"/></xs:choice>', '',
         [('', True), ('<a>17</a>', True), ('<b>p:A</b><a>17</a><b>p:B</b><a>29</a>', True),
          ('<a>1</a>' * 5, False), ('<unknown/>', False)], False),
        ('lists', '<xs:sequence><xs:element name="codes" type="t:Codes" maxOccurs="3"/></xs:sequence>',
         '<xs:simpleType name="Codes"><xs:list itemType="xs:int"/></xs:simpleType>',
         [('<codes>1 2</codes><codes>3 4</codes>', True), ('<codes/>', True),
          ('<codes>1 bad</codes>', False), ('<codes>1 2</codes>' * 4, False)], False),
        ('collision', '<xs:sequence><xs:element name="item" type="xs:int" form="qualified"/>'
         '<xs:element name="item" type="xs:QName" form="unqualified"/></xs:sequence>', '',
         [('<t:item>17</t:item><item>p:Part</item>', True),
          ('<item>p:Part</item><t:item>17</t:item>', False), ('<t:item>17</t:item>', False)], False),
        ('substitution', '<xs:sequence><xs:element ref="t:head" maxOccurs="3"/></xs:sequence>',
         '<xs:element name="head" type="xs:int" abstract="true"/>'
         '<xs:element name="member" type="xs:int" substitutionGroup="t:head"/>',
         [('<t:member>17</t:member><t:member>29</t:member>', True), ('<t:head>17</t:head>', False),
          ('<t:member>bad</t:member>', False)], False),
        ('nested', '<xs:sequence><xs:element name="nested" minOccurs="1" maxOccurs="2">'
         '<xs:complexType mixed="true"><xs:sequence><xs:element name="a" type="xs:int"/>'
         '</xs:sequence></xs:complexType></xs:element></xs:sequence>', '',
         [('<nested>p:Inner<a>17</a>p:After</nested><nested>x<a>29</a>y</nested>', True),
          ('<nested>p:Inner<a>bad</a>p:After</nested>', False), ('<nested>text</nested>', False)], False),
    ]
    for mode in ['skip', 'lax', 'strict']:
        specs.append(('wildcard-' + mode,
                      f'<xs:sequence><xs:any processContents="{mode}" minOccurs="0" maxOccurs="3"/></xs:sequence>',
                      '<xs:element name="known" type="xs:int"/>',
                      [('<t:known>17</t:known><t:known>29</t:known>', True),
                       ('<q:unknown xmlns:q="urn:other">007<q:part/>p:Text</q:unknown>', mode != 'strict'),
                       ('<t:known>bad</t:known>', mode == 'skip')], False))
    specs.append(('selected', '<xs:sequence><xs:element name="a" type="xs:int"/></xs:sequence>',
                  '<xs:complexType name="Derived"><xs:complexContent mixed="true">'
                  '<xs:extension base="t:Record"><xs:sequence><xs:element name="b" type="xs:QName"/>'
                  '</xs:sequence></xs:extension></xs:complexContent></xs:complexType>',
                  [('<a>17</a><b>p:Part</b>', True), ('<a>17</a>', False),
                   ('<b>p:Part</b><a>17</a>', False)], True))
    variants = [('bare', '', '', ''), ('text', 'p:Before', 'p:Between', 'p:After'),
                ('cdata', '<![CDATA[p:Before]]>', '<![CDATA[]]>', '<![CDATA[p:After]]>'),
                ('comment', 'before<!--first-->', '<!--between-->', '<!--last-->after')]
    for name, particle, extra, samples, selected in specs:
        schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">'
                  f'<xs:complexType name="Record" mixed="true">{particle}{ATTRIBUTES}</xs:complexType>{extra}'
                  + ''.join(f'<xs:element name="{root}" type="t:Record"/>' for root in ['value', 'Submit', 'Reply'])
                  + '</xs:schema>')
        documents = []
        for index, (content, valid) in enumerate(samples):
            # Insert between top-level children only; nested child order is an independent part of the value.
            wrapper = etree.fromstring((f'<wrapper xmlns:t="{NS}" xmlns:p="urn:products">{content}</wrapper>').encode(),
                                       etree.XMLParser(strip_cdata=False))
            children = [etree.tostring(child, encoding='unicode', with_tail=False) for child in wrapper]
            for variant, before, between, after in variants:
                joined = before + between.join(children) + after
                for supplied, expected in [('tag="+017"', valid), ('', False), ('tag="bad"', False)]:
                    identity = f'{name}/{index}/{variant}/{supplied}'
                    def payload(root):
                        selected_type = 'i:type="t:Derived"' if selected else ''
                        return (f'<t:{root} xmlns:t="{NS}" xmlns:p="urn:products" xmlns:i="{XSI}" '
                                f'{supplied} {selected_type}>{joined}</t:{root}>')
                    messages = []
                    for version, envelope in zip(['11', '12'], survey.SOAP_NAMESPACES):
                        for direction, root in [('request', 'Submit'), ('response', 'Reply')]:
                            messages.append({'binding': 'Soap' + version, 'direction': direction,
                                             'xml': f'<s:Envelope xmlns:s="{envelope}"><s:Body>'
                                                    + payload(root) + '</s:Body></s:Envelope>'})
                    documents.append({'name': identity, 'xml': payload('value'), 'valid': expected,
                                      'messages': messages})
        yield {'name': name, 'schema': schema, 'selected': selected,
               'bindings': {'Soap' + version: description(version, schema) for version in ['11', '12']},
               'documents': documents}


def qname(node, text):
    if ':' in text:
        prefix, local = text.split(':')
        return node.nsmap.get(prefix, '#unbound'), local
    return node.nsmap.get(None, ''), text


def text_value(node, text):
    return text, tuple((word, qname(node, word)) for word in re.findall(r'[A-Za-z_][\w.-]*:[\w.-]+', text))


def meaning(node, model, root=True):
    # Expanded child names, typed values and ordered text/comment events are compared independently
    # of serializer prefix choices. CDATA boundaries themselves are not XML infoset properties.
    attributes = tuple(sorted((key, qname(node, value) if key == '{' + XSI + '}type'
                               else int(value) if key == 'tag' else value) for key, value in node.attrib.items()))
    if not root:
        integer = node.tag in ['a', '{' + NS + '}item', '{' + NS + '}member']
        integer |= node.tag == '{' + NS + '}known' and model['name'] != 'wildcard-skip'
        if integer:
            return node.tag, attributes, int(node.text or '')
        if node.tag in ['b', 'item']:
            return node.tag, attributes, qname(node, node.text or '')
        if node.tag == 'codes':
            return node.tag, attributes, tuple(int(part) for part in (node.text or '').split())
    events = []
    if node.text:
        events.append(('text', text_value(node, node.text)))
    for child in node:
        if isinstance(child.tag, str):
            events.append(('element', meaning(child, model, False)))
        else:
            events.append(('comment', child.text or ''))
        if child.tail:
            events.append(('text', text_value(node, child.tail)))
    return None if root else node.tag, attributes, tuple(events)


class MixedValuesTest(unittest.TestCase):
    def test_mixed_values_order_and_both_bindings(self):
        models = list(fixtures())
        cases = {document['name']: (model, document) for model in models for document in model['documents']}
        self.assertEqual(12, len(models))
        self.assertEqual(sum(len(model['documents']) for model in models), len(cases))
        jobs = [SchemaJob(model['name'], f'http://example.invalid/mixed/{index}.xsd', model['schema'].encode(),
                          {document['name']: document['xml'].encode() for document in model['documents']})
                for index, model in enumerate(models)]
        oracle = independent(jobs)
        self.assertEqual(set(cases), set(oracle['documents']))
        validators = {}
        for model in models:
            self.assertTrue(oracle['schemas'][model['name']]['ok'], oracle['schemas'][model['name']])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            validators[model['name']] = etree.XMLSchema(etree.fromstring(model['schema'].encode()))
        for name, (model, document) in cases.items():
            self.assertEqual(document['valid'], oracle['documents'][name]['ok'], (name, oracle['documents'][name]))
            self.assertEqual([], oracle['documents'][name]['warnings'])
            self.assertEqual(document['valid'], validators[model['name']].validate(etree.fromstring(document['xml'].encode())), name)
        with tempfile.TemporaryDirectory(prefix='wsdl-mixed-values-') as folder:
            path = Path(folder) / 'fixtures.json'
            path.write_text(json.dumps(models))
            command = ['qore', '-b', '--enable-debug', '--exec-mode=' + os.environ.get('QORE_EXEC_MODE', 'jit'),
                       str(Path(__file__).with_name('mixed-values.qr')), str(path)]
            process = subprocess.run(command, capture_output=True, text=True, timeout=240)
            self.assertEqual(0, process.returncode, process.stdout + process.stderr)
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
                    actual = etree.fromstring(output.encode())
                    self.assertEqual(expected, meaning(actual, model), (key, row))
                    self.assertTrue(validators[model['name']].validate(actual), validators[model['name']].error_log)
                    outputs[model['name']][row['name'] + '/' + key] = output.encode()
                for message in row['messages']:
                    self.assertTrue(message.get('decoded'), message)
                    self.assertNotIn('error', message, message)
                    envelope = etree.fromstring(message['output'].encode())
                    self.assertEqual('{' + survey.SOAP_NAMESPACES[message['binding'] == 'Soap12'] + '}Envelope', envelope.tag)
                    payload = envelope.find('{*}Body')[0]
                    self.assertEqual('{' + NS + '}' + ('Reply' if message['direction'] == 'response' else 'Submit'), payload.tag)
                    self.assertEqual(expected, meaning(payload, model), message)
                    self.assertTrue(validators[model['name']].validate(payload), validators[model['name']].error_log)
                    outputs[model['name']][row['name'] + '/' + message['binding'] + '/' + message['direction']] = etree.tostring(payload)
        oracle = independent([SchemaJob(model['name'], f'http://example.invalid/mixed/{index}.xsd', model['schema'].encode(),
                                        outputs[model['name']]) for index, model in enumerate(models)])
        self.assertEqual(sum(len(documents) for documents in outputs.values()), len(oracle['documents']))
        for name, result in oracle['documents'].items():
            self.assertTrue(result['ok'], (name, result))
            self.assertEqual([], result['warnings'])
        print(f'{len(models)} schemas, {len(cases)} documents, {len(cases) * 4} real SOAP directions, '
              f'{len(oracle["documents"])} independently valid outputs')


if __name__ == '__main__':
    unittest.main()
