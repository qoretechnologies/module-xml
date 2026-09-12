#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Generic XML content conversion, namespace/value preservation and providers."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from lxml import etree
from independent import SchemaJob, run as independent

XSD = 'http://www.w3.org/2001/XMLSchema'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def models():
    for qualified in (False, True):
        target = 'urn:generic' if qualified else ''
        prefix = 't:' if qualified else ''
        for datatype in ('anyType', 'anySimpleType'):
            model = f'{qualified}/{datatype}'
            schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="urn:generic"'
                      + (f' targetNamespace="{target}"' if target else '') + '>'
                      + f'<xs:element name="root" type="xs:{datatype}"/>'
                      + '<xs:element name="known" type="xs:int"/><xs:attribute name="count" type="xs:int"/>'
                      + '<xs:simpleType name="Positive"><xs:restriction base="xs:int"><xs:minInclusive value="0"/>'
                      + '</xs:restriction></xs:simpleType><xs:complexType name="Record"><xs:sequence>'
                      + '<xs:element name="code" type="xs:int"/></xs:sequence><xs:attribute name="tag" use="required"/>'
                      + '</xs:complexType><xs:complexType name="Abstract" abstract="true"/></xs:schema>')
            cases = [
                ('empty', '', '', True, True),
                ('text', '', ' shipment ', True, True),
                ('cdata', '', ' before<![CDATA[ middle]]> after ', True, True),
                ('mixed', '', 'before<free>value</free>after', True, False),
                ('known', '', f'<{prefix}known>017</{prefix}known>', True, False),
                ('bad-known', '', f'<{prefix}known>bad</{prefix}known>', False, False),
                ('nested-known', '', f'<free><{prefix}known>023</{prefix}known></free>', True, False),
                ('nested-bad', '', f'<free><{prefix}known>bad</{prefix}known></free>', False, False),
                ('free-attribute', ' free="p:Stock"', 'text', True, False),
                ('known-attribute', f' {prefix}count="017"', 'text', True, False),
                ('bad-attribute', f' {prefix}count="bad"', 'text', False, False),
                ('typed-int', ' xsi:type="xs:int"', '017', True, True),
                ('bad-int', ' xsi:type="xs:int"', 'bad', False, False),
                ('qname', ' xsi:type="xs:QName"', 'p:Stock', True, True),
                ('unbound-qname', ' xsi:type="xs:QName"', 'unbound:Stock', False, False),
                ('unknown-type', ' xsi:type="xs:Missing"', 'text', False, False),
                ('same-type', f' xsi:type="xs:{datatype}"', 'text', True, True),
                ('positive', f' xsi:type="{prefix}Positive"', '023', True, True),
                ('negative', f' xsi:type="{prefix}Positive"', '-1', False, False),
                ('record', f' xsi:type="{prefix}Record" tag="shipment"', '<code>017</code>', True, False),
                ('bad-record', f' xsi:type="{prefix}Record" tag="shipment"', '<code>bad</code>', False, False),
                ('missing-attribute', f' xsi:type="{prefix}Record"', '<code>017</code>', False, False),
                ('abstract', f' xsi:type="{prefix}Abstract"', '', False, False),
                ('ordered', '', 'before<p:item>p:Stock</p:item>middle<p:item>p:Part</p:item>after', True, False),
                ('rebound', '', '<p:item>p:Stock</p:item><p:item xmlns:p="urn:other">p:Part</p:item>', True, False),
                ('unknown-type-descendant', '', '<free xsi:type="xs:Missing"/>', False, False),
                ('unbound-text', '', 'xsd:Start<free>xsd:Stock</free>xsd:End', True, False),
                ('schema-location', ' xsi:noNamespaceSchemaLocation="urn:schema"', 'text', True, True),
            ]
            documents = []
            for name, attributes, content, any_type, simple in cases:
                xml = (f'<{prefix}root xmlns:t="urn:generic" xmlns:p="urn:products" xmlns:xs="{XSD}"'
                       + f' xmlns:xsi="{XSI}"{attributes}>{content}</{prefix}root>')
                documents.append({'name': model + '/' + name, 'xml': xml,
                                  'valid': any_type if datatype == 'anyType' else simple})
            yield {'name': model, 'schema': schema, 'datatype': datatype, 'target': target, 'documents': documents}


def qname(node, value):
    parts = value.split(':', 1)
    prefix, local = parts if len(parts) == 2 else (None, parts[0])
    return node.nsmap.get(prefix, ''), local


def content(node, model, root=False, native=False):
    attributes = dict(node.attrib)
    if root and native and model['datatype'] == 'anySimpleType':
        # The established scalar projection carries the typed value. Complete XML
        # carriers (checked separately below) also retain schema-location hints.
        attributes.pop('{' + XSI + '}schemaLocation', None)
        attributes.pop('{' + XSI + '}noNamespaceSchemaLocation', None)
    selected = attributes.pop('{' + XSI + '}type', None)
    selected = qname(node, selected) if selected is not None else ((XSD, model['datatype']) if root else None)
    if selected == (XSD, model['datatype']) and root:
        selected = None
    text = node.text or ''
    if selected == (XSD, 'QName'):
        text = qname(node, text.strip())
    elif selected in ((XSD, 'int'), (model['target'], 'Positive')):
        text = int(text)
    elif selected == (model['target'], 'Record'):
        # This selected complex type owns the native integer conversion of code.
        children = [(child.tag, int(child.text), child.tail or '') for child in node]
        return node.tag, attributes, selected, text, children
    return node.tag, attributes, selected, text, [(content(child, model), child.tail or '') for child in node]


class GenericValuesTest(unittest.TestCase):
    def test_generic_values(self):
        fixtures = list(models())
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        worker = os.environ.get('WSDL_GENERIC_VALUES_WORKER', str(Path(__file__).with_name('generic-values.qr')))
        with tempfile.TemporaryDirectory(prefix='wsdl-generic-values-') as folder:
            manifest = Path(folder) / 'manifest.json'
            manifest.write_text(json.dumps(fixtures))
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode, worker, str(manifest)],
                                    capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-3000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(112, len(rows))
        row_map = {row['name']: row for row in rows}
        self.assertEqual(112, len(row_map))
        jobs = []
        for model in fixtures:
            native = etree.XMLSchema(etree.fromstring(model['schema'].encode()))
            documents = {}
            for document in model['documents']:
                row = row_map[document['name']]
                self.assertEqual(document['valid'], native.validate(etree.fromstring(document['xml'].encode())), document)
                for path in ('decoded', 'encoded', 'provider', 'retained'):
                    self.assertEqual(document['valid'], bool(row.get(path)), (path, row))
                documents[document['name'] + '/input'] = document['xml'].encode()
                if not document['valid']:
                    for error, expected in (('error', 'SOAP-DESERIALIZATION-ERROR'),
                                            ('encode_error', 'SOAP-SERIALIZATION-ERROR'),
                                            ('provider_error', 'RUNTIME-TYPE-ERROR'),
                                            ('retained_error', 'SOAP-SERIALIZATION-ERROR')):
                        self.assertEqual(expected, row[error], row)
                    continue
                self.assertNotIn('error', row, row)
                for path in ('output', 'direct_output', 'retained_output'):
                    expected = content(etree.fromstring(document['xml'].encode()), model, True, path == 'output')
                    self.assertIn(path + '_dom', row, row)
                    self.assertTrue(row[path + '_dom'], row)
                    self.assertTrue(row[path + '_reader'], row)
                    output = etree.fromstring(row[path].encode())
                    self.assertEqual(expected, content(output, model, True, path == 'output'), (path, row))
                    documents[document['name'] + '/' + path] = row[path].encode()
                    if document['name'].endswith('/unbound-text'):
                        self.assertNotIn('xsd', output.nsmap)
                        self.assertNotIn('xsd', output[0].nsmap)
            jobs.append(SchemaJob(model['name'], f'http://example.invalid/generic/{len(jobs)}.xsd',
                                  model['schema'].encode(), documents))
        oracle = independent(jobs)
        self.assertEqual({model['name'] for model in fixtures}, set(oracle['schemas']))
        for model in fixtures:
            self.assertTrue(oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for document in model['documents']:
                for path in ('input', 'output', 'direct_output', 'retained_output') if document['valid'] else ('input',):
                    row = oracle['documents'][document['name'] + '/' + path]
                    self.assertEqual(document['valid'], row['ok'], row)
                    self.assertEqual([], row['warnings'])


if __name__ == '__main__':
    unittest.main()
