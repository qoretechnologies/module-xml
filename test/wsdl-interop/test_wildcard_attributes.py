#!/usr/bin/env python3
"""XSD 1.0 wildcard attribute instances, values, names and SOAP consumers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import NS, XSD
from test_substitution_particles import description


def models():
    declarations = '''<xs:attribute name="number" type="xs:int"/>
      <xs:attribute name="flag" type="xs:boolean"/><xs:attribute name="category" type="xs:QName"/>
      <xs:attribute name="first" type="xs:ID"/><xs:attribute name="second" type="xs:ID"/>
      <xs:attribute name="unit" type="xs:string" fixed="kg"/>'''
    examples = [('', {}, True), ('t:number="017"', {f'{{{NS}}}number':'017'}, True),
                ('t:number="2147483648"', {f'{{{NS}}}number':'2147483648'}, False),
                ('t:flag="1"', {f'{{{NS}}}flag':'1'}, True),
                ('t:flag="yes"', {f'{{{NS}}}flag':'yes'}, False),
                ('t:category="p:Stock"', {f'{{{NS}}}category':'p:Stock'}, True),
                ('unknown="keep"', {'unknown':'keep'}, None),
                ('p:unknown="p:Stock"', {'{urn:products}unknown':'p:Stock'}, None),
                ('t:unit="kg"', {f'{{{NS}}}unit':'kg'}, True),
                ('t:unit="lb"', {f'{{{NS}}}unit':'lb'}, False)]
    for process in ('strict', 'lax', 'skip'):
        for constraint in ('##any', '##other', '##local', '##targetNamespace', 'urn:products', '##local ##targetNamespace'):
            name = process + '-' + constraint.replace(' ', '-')
            source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
              {declarations}<xs:element name="Container"><xs:complexType>
              <xs:anyAttribute namespace="{constraint}" processContents="{process}"/>
              </xs:complexType></xs:element></xs:schema>'''
            documents = []
            for index, (lexical, attrs, valid) in enumerate(examples):
                permitted = True
                for key in attrs:
                    uri = etree.QName(key).namespace or ''
                    permitted &= (constraint == '##any' or (constraint == '##other' and uri not in ('', NS))
                                  or (constraint == '##local' and not uri)
                                  or (constraint == '##targetNamespace' and uri == NS)
                                  or constraint == uri
                                  or (constraint == '##local ##targetNamespace' and uri in ('', NS)))
                accepted = permitted and (not attrs or process == 'skip' or (valid is None and process == 'lax') or valid is True)
                documents.append({'name':f'{name}/{index}', 'valid':bool(accepted), 'attributes':attrs,
                                  'xml':f'<t:Container xmlns:t="{NS}" xmlns:p="urn:products" {lexical}/>'})
            yield {'name':name, 'schema':source, 'process':process, 'documents':documents}
    for process in ('strict', 'lax', 'skip'):
        for declared in (False, True):
            name = f'ids-{process}-{declared}'
            source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
              {declarations}<xs:element name="Container"><xs:complexType>
              {'<xs:attribute name="id" type="xs:ID"/>' if declared else ''}
              <xs:anyAttribute processContents="{process}"/></xs:complexType></xs:element></xs:schema>'''
            documents = []
            for two in (False, True):
                attrs = {f'{{{NS}}}first':'one'}
                if two:
                    attrs[f'{{{NS}}}second']='two'
                documents.append({'name':f'{name}/{two}', 'valid':process == 'skip' or (not two and not declared),
                                  'attributes':attrs, 'xml':f'<t:Container xmlns:t="{NS}" t:first="one"'
                                  + (' t:second="two"' if two else '') + '/>'})
            yield {'name':name, 'schema':source, 'process':process, 'documents':documents}



def extended_models():
    original = list(models())
    yield from original
    for process in ('strict', 'lax', 'skip'):
        base = next(model for model in original if model['name'] == process + '-##any')
        wildcard = f'<xs:anyAttribute processContents="{process}"/>'
        variants = {
            'simple': '<xs:simpleContent><xs:extension base="xs:int">' + wildcard
                      + '</xs:extension></xs:simpleContent>',
            'group': '<xs:attributeGroup ref="t:Common"/>',
            'extension': '<xs:complexContent><xs:extension base="t:Base"/></xs:complexContent>',
            'restriction': '<xs:complexContent><xs:restriction base="t:Base">' + wildcard
                           + '</xs:restriction></xs:complexContent>',
        }
        for kind, content in variants.items():
            name = process + '-' + kind
            root = etree.fromstring(base['schema'].encode())
            element = root.find(f'{{{XSD}}}element')
            root.remove(element)
            if kind == 'group':
                root.append(etree.fromstring(f'<xs:attributeGroup xmlns:xs="{XSD}" name="Common">'
                                             + wildcard + '</xs:attributeGroup>'))
            elif kind in ('extension', 'restriction'):
                root.append(etree.fromstring(f'<xs:complexType xmlns:xs="{XSD}" name="Base">'
                                             + wildcard + '</xs:complexType>'))
            root.append(etree.fromstring(f'<xs:element xmlns:xs="{XSD}" name="Container"><xs:complexType>'
                                         + content + '</xs:complexType></xs:element>'))
            documents = []
            for index, document in enumerate(base['documents']):
                xml = document['xml']
                if kind == 'simple':
                    xml = xml.removesuffix('/>') + '>023</t:Container>'
                documents.append({**document, 'name': f'{name}/{index}', 'xml': xml})
            yield {**base, 'name': name, 'schema': etree.tostring(root).decode(), 'documents': documents,
                   'simple': kind == 'simple'}
        name = process + '-imports'
        resources = {
            'http://example.invalid/foreign.xsd': f'''<xs:schema xmlns:xs="{XSD}" targetNamespace="urn:foreign">
              <xs:attribute name="numbers"><xs:simpleType><xs:list itemType="xs:int"/></xs:simpleType></xs:attribute>
              <xs:attribute name="categories"><xs:simpleType><xs:list itemType="xs:QName"/></xs:simpleType></xs:attribute>
              </xs:schema>''',
            'http://example.invalid/bare.xsd': f'''<xs:schema xmlns:xs="{XSD}">
              <xs:attribute name="flag" type="xs:boolean"/></xs:schema>''',
        }
        source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
          <xs:import namespace="urn:foreign" schemaLocation="http://example.invalid/foreign.xsd"/>
          <xs:import schemaLocation="http://example.invalid/bare.xsd"/>
          <xs:element name="Container"><xs:complexType>{wildcard}</xs:complexType></xs:element></xs:schema>'''
        documents = []
        for index, (attributes, valid) in enumerate((('f:numbers="017 -23" flag="0"', True),
                ('f:categories="p:Stock Local"', True), ('f:numbers="17 invalid"', False),
                ('f:categories="unknown:Stock"', False))):
            xml = f'<t:Container xmlns:t="{NS}" xmlns:f="urn:foreign" xmlns:p="urn:products" {attributes}/>'
            documents.append({'name': f'{name}/{index}', 'valid': valid or process == 'skip', 'xml': xml})
        yield {'name': name, 'schema': source, 'process': process, 'documents': documents, 'resources': resources}


def qname(value, root):
    if ':' in value:
        prefix, local = value.split(':', 1)
        return (root.nsmap[prefix], local)
    return (root.nsmap.get(None, ''), value)


def attribute_values(root, process):
    values = {}
    for key, value in root.attrib.items():
        if process != 'skip' and key == f'{{{NS}}}number':
            value = Decimal(value)
        elif process != 'skip' and key in (f'{{{NS}}}flag', 'flag'):
            value = value in ('true', '1')
        elif process != 'skip' and key == f'{{{NS}}}category':
            value = qname(value, root)
        elif process != 'skip' and key == '{urn:foreign}numbers':
            value = tuple(Decimal(token) for token in value.split())
        elif process != 'skip' and key == '{urn:foreign}categories':
            value = tuple(qname(token, root) for token in value.split())
        elif ':' in value:
            # Unassessed lexical text keeps bindings used only by that text.
            value = (value, tuple((token.split(':', 1)[0], root.nsmap.get(token.split(':', 1)[0]))
                                  for token in value.split() if ':' in token))
        values[key] = value
    return values


class ResourceResolver(etree.Resolver):
    def __init__(self, resources):
        super().__init__()
        self.resources = resources

    def resolve(self, url, public_id, context):
        if url not in self.resources:
            raise OSError('Unknown schema resource: ' + url)
        return self.resolve_string(self.resources[url], context, base_url=url)


class WildcardAttributesTest(unittest.TestCase):
    def test_names_processing_values_and_both_bindings(self):
        fixtures = list(extended_models())
        self.assertEqual(39, len(fixtures))
        self.assertEqual(324, sum(len(model['documents']) for model in fixtures))
        jobs, cases, compilers, resources = [], [], {}, {}
        for index, model in enumerate(fixtures):
            parser = etree.XMLParser(no_network=True)
            parser.resolvers.add(ResourceResolver(model.get('resources', {})))
            compiler = compilers[model['name']] = etree.XMLSchema(etree.fromstring(model['schema'].encode(), parser))
            resources.update({uri: text.encode() for uri, text in model.get('resources', {}).items()})
            documents = {document['name']: document['xml'].encode() for document in model['documents']}
            for document in model['documents']:
                # libxml2 records wildcard-ID errors but omits both reporting cases.
                # The normative rejection remains mandatory for Qore and Xerces.
                lxml_valid = True if model['name'].startswith('ids-') else document['valid']
                self.assertEqual(lxml_valid, compiler.validate(etree.fromstring(document['xml'].encode())),
                                 (document, str(compiler.error_log)))
            jobs.append(SchemaJob(model['name'], f'http://example.invalid/attributes/{index}.xsd',
                                  model['schema'].encode(), documents))
            for version in ('11', '12'):
                cases.append({**model, 'name': model['name'] + '/' + version,
                              'wsdl': description(version, model['schema']), 'uri': NS,
                              'envelope': 'http://www.w3.org/2003/05/soap-envelope' if version == '12'
                              else 'http://schemas.xmlsoap.org/soap/envelope/'})
        oracle = run_independent(jobs, resources)
        for model in fixtures:
            schema = oracle['schemas'][model['name']]
            self.assertTrue(schema['ok'], schema)
            self.assertEqual([], schema['warnings'])
            for document in model['documents']:
                result = oracle['documents'][document['name']]
                self.assertEqual(document['valid'], result['ok'], (document, result))
                self.assertEqual([], result['warnings'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        worker = os.environ.get('WSDL_WILDCARD_ATTRIBUTES_WORKER', 'wildcard-attributes.qr')
        with tempfile.TemporaryDirectory(prefix='wsdl-wildcard-attributes-') as folder:
            path = Path(folder) / 'cases.json'
            path.write_text(json.dumps(cases))
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                     str(Path(__file__).parent / worker), str(path)],
                                    capture_output=True, text=True, timeout=300)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = iter(json.loads(line) for line in result.stdout.splitlines())
        count = accepted = 0
        outputs = {model['name']: {} for model in fixtures}
        for model in fixtures:
            for version in ('11', '12'):
                for copy in (False, True):
                    for response in (False, True):
                        for document in model['documents']:
                            row = next(rows)
                            count += 1
                            self.assertEqual((model['name'] + '/' + version, copy, response, document['name']),
                                             (row['name'], row['copy'], row['response'], row['document']))
                            if not document['valid']:
                                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row.get('error'), row)
                                continue
                            accepted += 1
                            self.assertNotIn('error', row, row)
                            self.assertEqual(row['native'], row['provider'])
                            expected = attribute_values(etree.fromstring(document['xml'].encode()), model['process'])
                            for form in ('xml', 'standalone', 'retained'):
                                root = etree.fromstring(row[form].encode())
                                if form == 'xml':
                                    self.assertEqual(cases[0]['envelope'] if version == '11'
                                                     else 'http://www.w3.org/2003/05/soap-envelope', root.tag[1:].split('}')[0])
                                    root = root.find('{*}Body')[0]
                                self.assertEqual('{' + NS + '}Container', root.tag)
                                self.assertEqual(expected, attribute_values(root, model['process']), row)
                                if model.get('simple'):
                                    self.assertEqual(Decimal(23), Decimal(root.text))
                                self.assertTrue(compilers[model['name']].validate(root), row)
                                name = f'{version}/{copy}/{response}/{document["name"]}/{form}'
                                outputs[model['name']][name] = etree.tostring(root)
        self.assertIsNone(next(rows, None))
        self.assertEqual(2592, count)
        final = run_independent([SchemaJob(model['name'], f'http://example.invalid/output/{index}.xsd',
                                          model['schema'].encode(), outputs[model['name']])
                                 for index, model in enumerate(fixtures)], resources)
        for name, row in {**final['schemas'], **final['documents']}.items():
            self.assertTrue(row['ok'], (name, row))
            self.assertEqual([], row['warnings'])
        print(f'{mode}: 39 schemas, 324 documents, {count} rows, '
              f'{accepted * 3} independently validated outputs', flush=True)


if __name__ == '__main__':
    unittest.main()
