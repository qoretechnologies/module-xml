#!/usr/bin/env python3
"""Concrete substitution names in complete particles and both SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass, field
from decimal import Decimal
import itertools
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_element_substitution import membership_models, ORACLE_DIFFERENCES
from test_attribute_values import NS, XSD

# Supporting-validator discrepancies are explicit and do not change normative outcomes.
# Count/position defects are documented in particle-ambiguity-evidence.md; unused
# groups are not traversed by Xerces fullSchemaChecking(). libxml2's declaration
# consistency checker is disabled, including in the current private provider.
SCHEMA_DIFFERENCES = {
    'fixed-boundary': {'lxml': False},
    'invalid-3': {'lxml': True},
    'invalid-5': {'lxml': True, 'native': True},
    **{f'unused-invalid-{index}': {'lxml': True, 'xerces': True} for index in range(6)},
}
SCHEMA_DIFFERENCES['unused-invalid-5']['native'] = True


@dataclass
class Model:
    name: str
    schema: str
    valid: bool = True
    documents: list[dict] = field(default_factory=list)


def schema(declarations, content):
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
      {declarations}<xs:element name="Container"><xs:complexType>{content}</xs:complexType></xs:element>
    </xs:schema>'''


def document(name, children, valid, matches=None):
    root = etree.fromstring(f'<t:Container xmlns:t="{NS}">{children}</t:Container>'.encode())
    return {'name': name, 'xml': etree.tostring(root).decode(), 'valid': valid,
            'matches': valid if matches is None else matches,
            'names': [child.tag if child.tag.startswith('{') else '{}' + child.tag for child in root]}


def definitions():
    for name, body, head, members, value in membership_models():
        model = Model(name, schema(body, f'<xs:sequence><xs:element ref="t:{head}"/></xs:sequence>'))
        candidates = etree.fromstring(model.schema.encode()).findall(f'{{{XSD}}}element')
        for candidate in sorted(node.get('name') for node in candidates if node.get('name') != 'Container'):
            model.documents.append(document(name + '/' + candidate,
                f'<t:{candidate}>{value}</t:{candidate}>', candidate in members))
        yield model

    declarations = '''<xs:element name="Head" type="xs:decimal" abstract="true"/>
      <xs:element name="Quantity" type="xs:int" substitutionGroup="t:Head"/>
      <xs:element name="Amount" type="xs:decimal" substitutionGroup="t:Head"/>'''
    member = '<xs:element ref="t:Head"/>'
    tail = '<xs:element name="Tail" type="xs:int"/>'
    patterns = [
        ('one', f'<xs:sequence>{member}</xs:sequence>', lambda w: len(w) == 1 and w[0] in 'qa'),
        ('two', '<xs:sequence><xs:element ref="t:Head" minOccurs="2" maxOccurs="2"/></xs:sequence>',
         lambda w: len(w) == 2 and set(w) <= set('qa')),
        ('optional-tail', '<xs:sequence><xs:element ref="t:Head" minOccurs="0" maxOccurs="2"/>' + tail + '</xs:sequence>',
         lambda w: bool(w) and w[-1] == 't' and len(w) <= 3 and set(w[:-1]) <= set('qa')),
        ('choice', f'<xs:choice>{member}{tail}</xs:choice>', lambda w: len(w) == 1 and w[0] in 'qat'),
        ('all', f'<xs:all>{member}{tail}</xs:all>', lambda w: len(w) == 2 and set(w) in (set('qt'), set('at'))),
        ('optional-all', f'<xs:all minOccurs="0">{member}{tail}</xs:all>',
         lambda w: not w or len(w) == 2 and set(w) in (set('qt'), set('at'))),
        ('shared', '<xs:sequence><xs:group ref="t:G"/><xs:group ref="t:G"/></xs:sequence>',
         lambda w: len(w) == 4 and w[0] in 'qa' and w[1] == 't' and w[2] in 'qa' and w[3] == 't'),
        ('fixed-boundary', '<xs:sequence><xs:element ref="t:Head" minOccurs="2" maxOccurs="2"/>'
            '<xs:element ref="t:Quantity"/></xs:sequence>',
         lambda w: len(w) == 3 and set(w[:2]) <= set('qa') and w[2] == 'q'),
    ]
    words = sorted({''.join(word) for size in range(3) for word in itertools.product('qat', repeat=size)}
                   | {'h', 'qqq', 'qaq', 'qqt', 'aat', 'qat', 'qta', 'qaat', 'qtat', 'atqt', 'qtqt', 'atat'})
    tokens = {'q': '<t:Quantity>017</t:Quantity>', 'a': '<t:Amount>1.250</t:Amount>',
              't': '<Tail>29</Tail>', 'h': '<t:Head>17</t:Head>'}
    for name, content, accepts in patterns:
        body = declarations + (f'<xs:group name="G"><xs:sequence>{member}{tail}</xs:sequence></xs:group>'
                               if name == 'shared' else '')
        model = Model(name, schema(body, content))
        model.documents = [document(name + '/' + (word or 'empty'), ''.join(tokens[c] for c in word), accepts(word))
                           for word in words]
        yield model
    invalid = [
        f'<xs:choice>{member}<xs:element ref="t:Quantity"/></xs:choice>',
        '<xs:sequence><xs:element ref="t:Head" minOccurs="0"/><xs:element ref="t:Quantity"/></xs:sequence>',
        '<xs:sequence><xs:element ref="t:Head" minOccurs="2" maxOccurs="3"/><xs:element ref="t:Quantity"/></xs:sequence>',
        f'<xs:all>{member}<xs:element ref="t:Quantity"/></xs:all>',
        f'<xs:choice>{member}<xs:any namespace="##targetNamespace"/></xs:choice>',
        f'<xs:sequence>{member}<xs:element name="Quantity" type="xs:string" form="qualified"/></xs:sequence>',
    ]
    for index, content in enumerate(invalid):
        yield Model(f'invalid-{index}', schema(declarations, content), False)
        yield Model(f'unused-invalid-{index}', schema(declarations
            + f'<xs:group name="Unused">{content}</xs:group>', '<xs:sequence/>'), False)
    model = Model('member-values', schema(declarations, f'<xs:sequence>{member}</xs:sequence>'))
    for name, value, valid in (('int', '017', True), ('fraction', '1.5', False), ('overflow', '2147483648', False),
                               ('bad', 'NaN', False), ('negative', '-2147483648', True)):
        model.documents.append(document('member-values/' + name, f'<t:Quantity>{value}</t:Quantity>', valid, True))
    yield model

    body = '''<xs:complexType name="B" abstract="true"/>
      <xs:complexType name="D"><xs:complexContent><xs:extension base="t:B"/></xs:complexContent></xs:complexType>
      <xs:element name="Head" type="t:B"/><xs:element name="Middle" type="t:B" substitutionGroup="t:Head"/>
      <xs:element name="Member" type="t:D" substitutionGroup="t:Middle"/>'''
    model = Model('abstract-type-candidate', schema(body, '<xs:sequence><xs:element ref="t:Head"/></xs:sequence>'))
    for name in ('Head', 'Middle', 'Member'):
        model.documents.append(document('abstract-type-candidate/' + name, f'<t:{name}/>', name == 'Member', True))
    yield model


def description(version, text):
    soap = 'http://schemas.xmlsoap.org/wsdl/soap' + ('12' if version == '12' else '') + '/'
    return f'''<w:definitions xmlns:w="http://schemas.xmlsoap.org/wsdl/" xmlns:s="{soap}" xmlns:t="{NS}"
      targetNamespace="{NS}"><w:types>{text}</w:types>
      <w:message name="Input"><w:part name="body" element="t:Container"/></w:message>
      <w:message name="Output"><w:part name="body" element="t:Container"/></w:message>
      <w:portType name="Port"><w:operation name="submit"><w:input message="t:Input"/>
        <w:output message="t:Output"/></w:operation></w:portType>
      <w:binding name="Soap" type="t:Port"><s:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <w:operation name="submit"><s:operation soapAction="urn:submit"/><w:input><s:body use="literal"/></w:input>
          <w:output><s:body use="literal"/></w:output></w:operation></w:binding></w:definitions>'''


def values(xml):
    """Compare numeric value and QName identity per field; flat records do not retain cross-field interleaving."""
    result = {}
    for child in etree.fromstring(xml.encode() if isinstance(xml, str) else xml):
        result.setdefault(child.tag, []).append(Decimal(child.text) if child.text else None)
    return result


class SubstitutionParticlesTest(unittest.TestCase):
    def test_independent_members_values_constraints_and_bindings(self):
        models = list(definitions())
        self.assertEqual(53, len(models))
        self.assertEqual(41, sum(model.valid for model in models))
        self.assertEqual(310, sum(len(model.documents) for model in models))
        self.assertEqual(len(models), len({model.name for model in models}))
        compilers, jobs, cases = {}, [], []
        for index, model in enumerate(models):
            if SCHEMA_DIFFERENCES.get(model.name, {}).get('lxml', model.valid):
                compiler = compilers[model.name] = etree.XMLSchema(etree.fromstring(model.schema.encode()))
                for doc in model.documents:
                    self.assertEqual(ORACLE_DIFFERENCES.get(doc['name'], {}).get('lxml', doc['valid']),
                        compiler.validate(etree.fromstring(doc['xml'].encode())), (doc, str(compiler.error_log)))
            else:
                with self.assertRaises(etree.XMLSchemaParseError, msg=model.name):
                    etree.XMLSchema(etree.fromstring(model.schema.encode()))
            jobs.append(SchemaJob(model.name, f'http://example.invalid/particles/{index}.xsd', model.schema.encode(),
                {doc['name']: doc['xml'].encode() for doc in model.documents}))
            for version in ('11', '12'):
                cases.append({'name': model.name + '/' + version, 'schema': model.schema, 'uri': NS,
                    'wsdl': description(version, model.schema), 'documents': model.documents,
                    'envelope': 'http://www.w3.org/2003/05/soap-envelope' if version == '12'
                        else 'http://schemas.xmlsoap.org/soap/envelope/'})
        oracle = run_independent(jobs)
        for model in models:
            self.assertEqual(SCHEMA_DIFFERENCES.get(model.name, {}).get('xerces', model.valid),
                oracle['schemas'][model.name]['ok'], oracle['schemas'][model.name])
            self.assertEqual([], oracle['schemas'][model.name]['warnings'])
            for doc in model.documents:
                result = oracle['documents'][doc['name']]
                self.assertEqual(ORACLE_DIFFERENCES.get(doc['name'], {}).get('xerces', doc['valid']), result['ok'], (doc, result))
                self.assertEqual([], result['warnings'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        worker = os.environ.get('WSDL_SUBSTITUTION_PARTICLES_WORKER', 'substitution-particles.qr')
        with tempfile.TemporaryDirectory(prefix='wsdl-substitution-particles-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(cases))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                str(Path(__file__).parent / worker), str(path)], capture_output=True, text=True, timeout=300)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-3000:])
        self.assertEqual('', process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        outputs = {}
        count = accepted = samples = 0
        for model in models:
            for version in ('11', '12'):
                key = model.name + '/' + version
                construction = next(rows)
                sample = construction.pop('sample', None)
                sample_error = construction.pop('sample_error', '')
                self.assertEqual({'name': key, 'error': '' if model.valid else 'WSDL-ERROR',
                    'native_error': '' if SCHEMA_DIFFERENCES.get(model.name, {}).get('native', model.valid)
                        else 'XSD-SYNTAX-ERROR'}, construction)
                count += 1
                if not model.valid:
                    self.assertIsNone(sample)
                    self.assertEqual('', sample_error)
                    continue
                if any(doc['valid'] for doc in model.documents):
                    self.assertEqual('', sample_error, model.name)
                    self.assertIsNotNone(sample, model.name)
                    if model.name in compilers:
                        self.assertTrue(compilers[model.name].validate(etree.fromstring(sample.encode())), model.name)
                    outputs.setdefault(model.name, {})[key + '/sample'] = sample.encode()
                    samples += 1
                else:
                    self.assertIsNone(sample, model.name)
                    self.assertEqual('XSD-SAMPLE-ERROR', sample_error, model.name)
                for copy in (False, True):
                    for response in (False, True):
                        for doc in model.documents:
                            row = next(rows)
                            count += 1
                            self.assertEqual((key, copy, response, doc['name']),
                                (row['name'], row['copy'], row['response'], row['document']))
                            self.assertEqual(doc['matches'], row['matches'], row)
                            if not doc['valid']:
                                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row.get('error'), row)
                                self.assertEqual('SOAP-SERIALIZATION-ERROR', row.get('retained_error'), row)
                                self.assertNotIn('xml', row)
                                self.assertNotIn('unwrapped_xml', row)
                                continue
                            accepted += 1
                            self.assertNotIn('error', row, row)
                            self.assertEqual(doc['xml'], row.get('retained'), row)
                            for shape in ('xml', 'unwrapped_xml'):
                                envelope = etree.fromstring(row[shape].encode())
                                soap = 'http://www.w3.org/2003/05/soap-envelope' if version == '12' else 'http://schemas.xmlsoap.org/soap/envelope/'
                                self.assertEqual(f'{{{soap}}}Envelope', envelope.tag)
                                payload = envelope.find(f'{{{soap}}}Body')[0]
                                self.assertEqual(f'{{{NS}}}Container', payload.tag)
                                if model.name in compilers:
                                    self.assertTrue(compilers[model.name].validate(payload), str(compilers[model.name].error_log))
                                self.assertEqual(values(doc['xml']), values(etree.tostring(payload)), row)
                                outputs.setdefault(model.name, {})[f'{key}/{copy}/{response}/{doc["name"]}/{shape}'] = etree.tostring(payload)
        self.assertIsNone(next(rows, None))
        self.assertEqual((2586, 496), (count, accepted))
        result = run_independent([SchemaJob(model.name, f'http://example.invalid/particles/output/{index}.xsd',
            model.schema.encode(), outputs[model.name]) for index, model in enumerate(models) if model.name in outputs])
        self.assertEqual((accepted, samples), (496, 58))
        self.assertEqual(accepted * 2 + samples, len(result['documents']))
        for name, value in {**result['schemas'], **result['documents']}.items():
            self.assertTrue(value['ok'], (name, value))
            self.assertEqual([], value['warnings'])
        print(f'{mode}: {len(models)} schemas, {sum(len(model.documents) for model in models)} documents, '
              f'{count} rows, {accepted * 2} independently validated SOAP outputs, {samples} standalone samples', flush=True)


if __name__ == '__main__':
    unittest.main()
