#!/usr/bin/env python3
"""Complete substitution roots retain identity in schema, provider and SOAP paths.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import NS, XSD
from test_element_substitution import membership_models, ORACLE_DIFFERENCES
from test_substitution_particles import description


def witness(xml):
    # Reparenting with lxml can replace a child's element prefix and discard its
    # declaration without rewriting QName-valued attribute text such as xsi:type.
    # Embed the complete standalone serialization so all lexical bindings survive.
    root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml)
    return f'<w:Witness xmlns:w="{NS}">'.encode() + etree.tostring(root) + b'</w:Witness>'


def models():
    for name, declarations, head, members, value in membership_models():
        schema = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
          {declarations}<xs:element name="Witness"><xs:complexType><xs:sequence>
            <xs:element ref="t:{head}"/></xs:sequence></xs:complexType></xs:element></xs:schema>'''
        candidates = sorted(node.get('name') for node in etree.fromstring(schema.encode()).findall(f'{{{XSD}}}element')
                            if node.get('name') != 'Witness')
        documents = [{'name': name + '/' + candidate, 'local': candidate,
                      'xml': f'<t:{candidate} xmlns:t="{NS}">{value}</t:{candidate}>',
                      'valid': candidate in members} for candidate in candidates]
        yield {'name': name, 'schema': schema, 'head': head, 'documents': documents}

    records = '''<xs:complexType name="Base"><xs:sequence><xs:element name="number" type="xs:int"/>
      </xs:sequence></xs:complexType><xs:complexType name="Detail"><xs:complexContent>
      <xs:extension base="t:Base"><xs:sequence><xs:element name="description" type="xs:string"/>
      </xs:sequence></xs:extension></xs:complexContent></xs:complexType>'''
    examples = [
        ('numeric-members', '<xs:element name="Head" type="xs:decimal" abstract="true"/>'
         '<xs:element name="Quantity" type="xs:int" substitutionGroup="t:Head"/>'
         '<xs:element name="Amount" type="xs:decimal" substitutionGroup="t:Head"/>', [
             ('Quantity', '017', True, ''), ('Quantity', '2147483648', False, ''),
             ('Amount', '1.250', True, ''), ('Quantity', '1.5', False, ''), ('Unknown', '17', False, '')]),
        ('record-members', records + '<xs:element name="Head" type="t:Base" abstract="true"/>'
         '<xs:element name="Member" type="t:Detail" substitutionGroup="t:Head"/>', [
             ('Member', '<number>017</number><description>Replacement part</description>', True, ''),
             ('Head', '<number>17</number>', False, ''), ('Member', '<number>17</number>', False, ''),
             ('Member', '<number>17</number><description>Replacement part</description><extra/>', False, ''),
             ('Member', '<t:number>17</t:number><description>Replacement part</description>', False, '')]),
        ('dynamic-members', records + '<xs:element name="Head" type="t:Base" abstract="true"/>'
         '<xs:element name="Member" type="t:Base" substitutionGroup="t:Head"/>', [
             ('Member', '<number>017</number><description>Replacement part</description>', True, 't:Detail'),
             ('Member', '<number>17</number>', True, ''), ('Member', 'Text', False, 'xs:string'),
             ('Member', '<number>17</number>', False, 't:Missing')]),
    ]
    for name, declarations, examples in examples:
        schema = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
          {declarations}<xs:element name="Witness"><xs:complexType><xs:sequence>
            <xs:element ref="t:Head"/></xs:sequence></xs:complexType></xs:element></xs:schema>'''
        documents = []
        for index, (local, content, valid, datatype) in enumerate(examples):
            attributes = f' xmlns:xs="{XSD}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="{datatype}"' if datatype else ''
            documents.append({'name': f'{name}/{index}', 'local': local, 'valid': valid,
                              'xml': f'<t:{local} xmlns:t="{NS}"{attributes}>{content}</t:{local}>'})
        yield {'name': name, 'schema': schema, 'head': 'Head', 'documents': documents}


def infoset(xml):
    """These fixtures have numeric scalars and nonnumeric description text; xsi:type is a QName."""
    root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml)
    text = root.text or ''
    try:
        value = Decimal(text) if text else None
    except InvalidOperation:
        value = text
    attributes = dict(root.attrib)
    key = '{http://www.w3.org/2001/XMLSchema-instance}type'
    if key in attributes:
        name = attributes[key].split(':')
        attributes[key] = (root.nsmap.get(name[0] if len(name) == 2 else None, ''), name[-1])
    return root.tag, value, attributes, [infoset(etree.tostring(child)) for child in root]


class SubstitutionRootsTest(unittest.TestCase):
    def test_independent_root_context_values_and_consumers(self):
        fixtures = list(models())
        self.assertEqual(34, len(fixtures))
        self.assertEqual(116, sum(len(model['documents']) for model in fixtures))
        self.assertEqual(len(fixtures), len({model['name'] for model in fixtures}))
        compilers, jobs, cases = {}, [], []
        for index, model in enumerate(fixtures):
            compiler = compilers[model['name']] = etree.XMLSchema(etree.fromstring(model['schema'].encode()))
            documents = {}
            for document in model['documents']:
                documents[document['name']] = witness(document['xml'])
                self.assertEqual(ORACLE_DIFFERENCES.get(document['name'], {}).get('lxml', document['valid']),
                                 compiler.validate(etree.fromstring(documents[document['name']])),
                                 (document, str(compiler.error_log)))
            jobs.append(SchemaJob(model['name'], f'http://example.invalid/root/{index}.xsd',
                                  model['schema'].encode(), documents))
            for version in ('11', '12'):
                wsdl = description(version, model['schema']).replace('element="t:Container"', f'element="t:{model["head"]}"')
                cases.append({**model, 'name': model['name'] + '/' + version, 'wsdl': wsdl, 'uri': NS,
                              'envelope': 'http://www.w3.org/2003/05/soap-envelope' if version == '12'
                              else 'http://schemas.xmlsoap.org/soap/envelope/'})
        oracle = run_independent(jobs)
        for model in fixtures:
            self.assertTrue(oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for document in model['documents']:
                result = oracle['documents'][document['name']]
                self.assertEqual(ORACLE_DIFFERENCES.get(document['name'], {}).get('xerces', document['valid']), result['ok'],
                                 (document, result))
                self.assertEqual([], result['warnings'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        worker = os.environ.get('WSDL_SUBSTITUTION_ROOTS_WORKER', 'substitution-roots.qr')
        with tempfile.TemporaryDirectory(prefix='wsdl-substitution-roots-') as directory:
            manifest = Path(directory) / 'cases.json'
            manifest.write_text(json.dumps(cases))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                      str(Path(__file__).parent / worker), str(manifest)],
                                     capture_output=True, text=True, timeout=300)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-4000:])
        self.assertEqual('', process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        outputs = {}
        count = accepted = samples = 0
        for model in fixtures:
            output = outputs[model['name']] = {}
            for version in ('11', '12'):
                key = model['name'] + '/' + version
                construction = next(rows)
                self.assertEqual(key, construction['name'])
                count += 1
                if any(document['valid'] for document in model['documents']):
                    self.assertNotIn('sample_error', construction, construction)
                    sample = witness(construction['sample'])
                    self.assertTrue(compilers[model['name']].validate(etree.fromstring(sample)), construction)
                    output[key + '/sample'] = sample
                    samples += 1
                else:
                    self.assertNotIn('sample', construction)
                    self.assertEqual('XSD-SAMPLE-ERROR', construction['sample_error'])
                for copy in (False, True):
                    for response in (False, True):
                        for document in model['documents']:
                            row = next(rows)
                            count += 1
                            self.assertEqual((key, copy, response, document['name']),
                                             (row['name'], row['copy'], row['response'], row['document']))
                            if not document['valid']:
                                self.assertEqual('SOAP-SERIALIZATION-ERROR', row.get('retained_error'), row)
                                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row.get('error'), row)
                                self.assertNotIn('xml', row)
                                continue
                            accepted += 1
                            self.assertNotIn('error', row, row)
                            self.assertEqual(document['xml'], row['retained'])
                            self.assertEqual(row['native'], row['provider'])
                            if document['local'] != model['head']:
                                self.assertEqual({'namespace_uri': NS, 'local_name': document['local']}, row['native']['^element^'])
                            for form in ('xml', 'retained_xml', 'standalone'):
                                payload = etree.fromstring(row[form].encode())
                                if form != 'standalone':
                                    soap = 'http://www.w3.org/2003/05/soap-envelope' if version == '12' else 'http://schemas.xmlsoap.org/soap/envelope/'
                                    self.assertEqual(f'{{{soap}}}Envelope', payload.tag)
                                    body = payload.find(f'{{{soap}}}Body')
                                    self.assertEqual(1, len(body))
                                    payload = body[0]
                                xml = etree.tostring(payload)
                                self.assertEqual(infoset(document['xml']), infoset(xml), row)
                                checked = witness(xml)
                                self.assertTrue(compilers[model['name']].validate(etree.fromstring(checked)), row)
                                output[f'{key}/{copy}/{response}/{document["name"]}/{form}'] = checked
        self.assertIsNone(next(rows, None))
        self.assertEqual((996, 272, 44), (count, accepted, samples))
        self.assertEqual(accepted * 3 + samples, sum(len(documents) for documents in outputs.values()))
        results = run_independent([SchemaJob(model['name'], f'http://example.invalid/root/output/{index}.xsd',
                                  model['schema'].encode(), outputs[model['name']]) for index, model in enumerate(fixtures)])
        for name, result in {**results['schemas'], **results['documents']}.items():
            self.assertTrue(result['ok'], (name, result))
            self.assertEqual([], result['warnings'])
        print(f'{mode}: {len(fixtures)} schemas, 116 context documents, {count} rows, '
              f'{accepted * 3} independently validated outputs, {samples} samples', flush=True)


if __name__ == '__main__':
    unittest.main()
