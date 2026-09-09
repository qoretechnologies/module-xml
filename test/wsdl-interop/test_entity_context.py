#!/usr/bin/env python3
"""Standalone ENTITY context, independent XSD verdicts and seven native APIs.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from xml.sax.saxutils import escape, quoteattr

from independent import SchemaJob, run, run_entity_documents


ROOT = Path(__file__).resolve().parent
XSD = 'http://www.w3.org/2001/XMLSchema'
DEFINITIONS = '''
<xs:simpleType name="Choice"><xs:restriction base="xs:ENTITY"><xs:enumeration value="photo"/></xs:restriction></xs:simpleType>
<xs:simpleType name="Two"><xs:restriction base="xs:ENTITIES"><xs:length value="2"/></xs:restriction></xs:simpleType>
<xs:simpleType name="Items"><xs:list itemType="xs:ENTITY"/></xs:simpleType>
<xs:simpleType name="EnumItems"><xs:restriction base="Items"><xs:enumeration value="photo other"/></xs:restriction></xs:simpleType>
<xs:simpleType name="OrInt"><xs:union memberTypes="xs:ENTITY xs:int"/></xs:simpleType>
<xs:simpleType name="OrString"><xs:union memberTypes="xs:ENTITY xs:string"/></xs:simpleType>
<xs:simpleType name="StringFirst"><xs:union memberTypes="xs:string xs:ENTITY"/></xs:simpleType>
<xs:simpleType name="EnumUnion"><xs:restriction base="OrString"><xs:enumeration value="photo"/></xs:restriction></xs:simpleType>
<xs:simpleType name="MixedItems"><xs:list itemType="OrInt"/></xs:simpleType>
<xs:simpleType name="DerivedEntities"><xs:restriction base="xs:ENTITIES"/></xs:simpleType>
<xs:simpleType name="NestedUnion"><xs:union memberTypes="OrInt xs:string"/></xs:simpleType>
'''
NOTATION = '<!NOTATION gif SYSTEM "image/gif">'
UNPARSED = '<!ENTITY photo SYSTEM "photo.gif" NDATA gif>'
# The set records the first general-entity bindings independently of the validators.
DECLARATIONS = {
    'none': ('', set()),
    'declared': (NOTATION + UNPARSED + '<!ENTITY other SYSTEM "other.gif" NDATA gif>'
                 '<!ENTITY é中文 SYSTEM "unicode.gif" NDATA gif>', {'photo', 'other', 'é中文'}),
    'parsed': ('<!ENTITY photo "data">', set()),
    'external-parsed': ('<!ENTITY photo SYSTEM "photo.xml">', set()),
    'wrong': (NOTATION + '<!ENTITY other SYSTEM "other.gif" NDATA gif>', {'other'}),
    'parsed-first': (NOTATION + '<!ENTITY photo "data">' + UNPARSED, set()),
    'unparsed-first': (NOTATION + UNPARSED + '<!ENTITY photo "data">', {'photo'}),
    'parameter': ('<!ENTITY % photo "ignored">', set()),
    'parameter-first': ('<!ENTITY % photo "ignored">' + NOTATION + UNPARSED, {'photo'}),
}
VALUES = ('photo', 'other', 'missing', ' photo ', 'photo other', '', '17', 'photo 17',
          'photo photo', 'p:photo', 'photo:bad:bad', '\tphoto\nother\r', 'é中文', 'photo\u00a0', ' \t\n')
TYPES = ('xs:ENTITY', 'xs:ENTITIES', 'Choice', 'Two', 'Items', 'EnumItems', 'OrInt', 'OrString',
         'StringFirst', 'EnumUnion', 'MixedItems', 'DerivedEntities', 'NestedUnion')
SHAPES = ('element', 'attribute', 'simple-content', 'default-element', 'default-attribute',
          'fixed-element', 'nil-element')
PATHS = ('parse', 'doc', 'reader', 'cursor', 'grouped', 'attached-text', 'attached-file')


def collapse(value):
    return ' '.join(piece for piece in value.translate(str.maketrans('\t\r\n', '   ')).split(' ') if piece)


def expected_value(type_name, value, entities):
    """Expected semantics for this finite fixture vocabulary, not a second parser."""
    normalized = collapse(value)
    # Avoid treating non-XML whitespace as a list separator.
    tokens = normalized.split(' ') if normalized else []
    entity_tokens = {'photo', 'other', 'missing', 'é中文'}
    if type_name == 'StringFirst':
        return True
    if type_name in ('xs:ENTITY', 'Choice'):
        return normalized in entities and (type_name != 'Choice' or normalized == 'photo')
    if type_name in ('xs:ENTITIES', 'DerivedEntities', 'Two', 'Items', 'EnumItems'):
        if not tokens and type_name != 'Items':
            return False
        if type_name == 'Two' and len(tokens) != 2:
            return False
        if type_name == 'EnumItems' and tokens != ['photo', 'other']:
            return False
        return all(token in entities for token in tokens)
    if type_name == 'MixedItems':
        return all(token == '17' or token in entities for token in tokens)
    if type_name == 'EnumUnion':
        return normalized == 'photo' and normalized in entities
    if normalized in entity_tokens:
        # Select ENTITY by lexical/facet matching, then apply document constraints.
        return normalized in entities
    if type_name == 'OrInt':
        return normalized == '17'
    assert type_name in ('OrString', 'NestedUnion'), type_name
    return True


def fixtures():
    jobs, rows, schema_validity = [], [], {}
    for type_name in TYPES:
        for shape in SHAPES:
            name = type_name.replace(':', '-') + '-' + shape
            source = f'<xs:schema xmlns:xs="{XSD}">' + DEFINITIONS
            if shape in ('attribute', 'default-attribute'):
                option = 'default="photo"' if shape == 'default-attribute' else 'use="required"'
                source += ('<xs:element name="value"><xs:complexType>'
                           f'<xs:attribute name="category" type="{type_name}" {option}/>'
                           '</xs:complexType></xs:element>')
            elif shape == 'simple-content':
                source += ('<xs:element name="value"><xs:complexType><xs:simpleContent>'
                           f'<xs:extension base="{type_name}"/></xs:simpleContent></xs:complexType></xs:element>')
            else:
                option = {'default-element': 'default="photo"', 'fixed-element': 'fixed="photo"',
                          'nil-element': 'nillable="true"'}.get(shape, '')
                source += f'<xs:element name="value" type="{type_name}" {option}/>'
            source += '</xs:schema>'
            # A one-item default cannot satisfy these types' length/enumeration.
            schema_valid = not (type_name in ('Two', 'EnumItems')
                                and shape in ('default-element', 'fixed-element', 'default-attribute'))
            schema_validity[name] = schema_valid
            documents = {}
            for declaration_name, (declaration, entities) in DECLARATIONS.items():
                values = ('',) if shape.startswith(('default', 'fixed', 'nil')) else VALUES
                for index, value in enumerate(values):
                    case = f'{name}-{declaration_name}-{index}'
                    xml = f'<!DOCTYPE value [{declaration}]>' if declaration else ''
                    if shape == 'default-attribute':
                        xml += '<value/>'
                    elif shape == 'attribute':
                        xml += '<value category=' + quoteattr(value) + '/>'
                    elif shape == 'nil-element':
                        xml += '<value xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>'
                    else:
                        xml += '<value>' + escape(value) + '</value>'
                    documents[case] = xml.encode()
                    if schema_valid:
                        valid = (True if shape in ('nil-element', 'default-attribute')
                                 else expected_value(type_name, 'photo' if shape.startswith(('default', 'fixed'))
                                                     else value, entities))
                        rows.append({'name': case, 'group': name, 'schema': source, 'xml': xml,
                                     'valid': valid, 'shape': shape, 'value': value})
            jobs.append(SchemaJob(name, 'urn:entity-context:' + name, source.encode(), documents))
    return jobs, rows, schema_validity


class EntityContextTest(unittest.TestCase):
    def test_length_facet_schema_construction(self):
        jobs, expected, xerces_defects = [], {}, set()
        types = ('xs:ENTITIES', 'xs:IDREFS', 'xs:NMTOKENS', 'xs:string', 'xs:ENTITY',
                 'xs:hexBinary', 'xs:base64Binary', 'Items')
        for type_name in types:
            for minimum, maximum in ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1)):
                for layout in ('same', 'minimum-inherited', 'maximum-inherited'):
                    for depth in range(3):
                        name = f'{type_name.replace(":", "-")}-{minimum}-{maximum}-{layout}-{depth}'
                        minimum_facet = f'<xs:minLength value="{minimum}"/>'
                        maximum_facet = f'<xs:maxLength value="{maximum}"/>'
                        inherited = (minimum_facet if layout == 'minimum-inherited'
                                     else maximum_facet if layout == 'maximum-inherited' else '')
                        current = (maximum_facet if layout == 'minimum-inherited'
                                   else minimum_facet if layout == 'maximum-inherited'
                                   else minimum_facet + maximum_facet)
                        schema = f'<xs:schema xmlns:xs="{XSD}">' + DEFINITIONS
                        base = type_name
                        for level in range(depth + 1):
                            next_type = f'Level{level}'
                            facets = inherited if level == 0 else ''
                            schema += (f'<xs:simpleType name="{next_type}"><xs:restriction base="{base}">'
                                       f'{facets}</xs:restriction></xs:simpleType>')
                            base = next_type
                        schema += (f'<xs:simpleType name="Reduced"><xs:restriction base="{base}">'
                                   f'{current}</xs:restriction></xs:simpleType>'
                                   '<xs:element name="value" type="Reduced"/></xs:schema>')
                        jobs.append(SchemaJob(name, 'urn:entity-length:' + name, schema.encode()))
                        expected[name] = (minimum <= maximum
                                          and (type_name not in types[:3] or minimum >= 1))
                        # Xerces 2.12.2 applyFacets uses "else if" for the
                        # inherited minimum when an inherited maximum exists.
                        # XSD 1.0 4.3.2.4 still forbids lowering that minimum.
                        if (type_name in types[:3] and minimum == 0 and maximum == 1
                                and layout == 'maximum-inherited'):
                            xerces_defects.add(name)
        self.assertEqual(432, len(jobs))
        self.assertEqual(9, len(xerces_defects))
        oracle = run_entity_documents(jobs)
        with tempfile.TemporaryDirectory(prefix='wsdl-entity-length-') as temporary:
            manifest = Path(temporary) / 'schemas.json'
            manifest.write_text(json.dumps({'schemas': {job.name: job.schema.decode() for job in jobs}, 'rows': []}))
            process = subprocess.run(['qore', '-b', '--enable-debug', str(ROOT / 'entity-validator.qr'), str(manifest)],
                                     text=True, capture_output=True, timeout=120)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual('', process.stderr)
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([job.name for job in jobs], [row['name'] for row in results])
        for result in results:
            with self.subTest(schema=result['name']):
                reference = oracle['schemas'][result['name']]
                self.assertEqual(True if result['name'] in xerces_defects else expected[result['name']],
                                 reference['ok'], reference)
                self.assertEqual([], reference['warnings'])
                self.assertEqual(expected[result['name']], result['valid'], result)
                self.assertEqual('schema', result['stage'])
                if not result['valid']:
                    self.assertEqual('XSD-SYNTAX-ERROR', result['error'])

    def test_document_context_and_native_apis(self):
        jobs, rows, schema_validity = fixtures()
        self.assertEqual(91, len(jobs))
        self.assertEqual(5679, len(rows))
        oracle = run_entity_documents(jobs)
        for job in jobs:
            with self.subTest(schema=job.name):
                self.assertEqual(schema_validity[job.name], oracle['schemas'][job.name]['ok'])
                self.assertEqual([], oracle['schemas'][job.name]['warnings'])
                if not schema_validity[job.name]:
                    for name in job.documents:
                        self.assertEqual('unreachable', oracle['documents'][name]['status'])
        with tempfile.TemporaryDirectory(prefix='wsdl-entity-context-') as temporary:
            manifest = Path(temporary) / 'fixtures.json'
            schemas = Path(str(manifest) + '.schemas')
            schemas.mkdir()
            for job in jobs:
                (schemas / (job.name + '.xsd')).write_bytes(job.schema)
            manifest.write_text(json.dumps({'schemas': {job.name: job.schema.decode() for job in jobs}, 'rows': rows}))
            process = subprocess.run(['qore', '-b', '--enable-debug', str(ROOT / 'entity-validator.qr'), str(manifest)],
                                     text=True, capture_output=True, timeout=120)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual('', process.stderr)
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([job.name for job in jobs], [row['name'] for row in results[:len(jobs)]])
        for result in results[:len(jobs)]:
            self.assertEqual('schema', result['stage'])
            self.assertEqual(schema_validity[result['name']], result['valid'], result)
            if not result['valid']:
                self.assertEqual('XSD-SYNTAX-ERROR', result['error'])
        results = results[len(jobs):]
        self.assertEqual([row['name'] for row in rows], [row['name'] for row in results])
        for row, result in zip(rows, results):
            with self.subTest(case=row['name']):
                verdict = oracle['documents'][row['name']]
                self.assertEqual(row['valid'], verdict['ok'], verdict)
                self.assertEqual([], verdict['warnings'])
                for path in PATHS:
                    self.assertEqual(row['valid'], result[path], (path, result))
                    if not row['valid']:
                        self.assertEqual('XSD-ERROR' if path == 'doc' else 'PARSE-XML-EXCEPTION',
                                         result[path + '_error'])
                if row['valid']:
                    self.assertTrue(result['preserved'])
                    if row['shape'] == 'attribute':
                        # quoteattr emits character references for control whitespace.
                        self.assertEqual(row['value'], result['attribute'])
                    elif row['shape'] in ('element', 'simple-content'):
                        self.assertEqual(row['value'].replace('\r\n', '\n').replace('\r', '\n'), result['text'])

    def test_soap_oracle_keeps_doctype_prohibition(self):
        schema = f'<xs:schema xmlns:xs="{XSD}"><xs:element name="value" type="xs:ENTITY"/></xs:schema>'
        xml = f'<!DOCTYPE value [{NOTATION}{UNPARSED}]><value>photo</value>'
        job = SchemaJob('entity', 'urn:entity-oracle-policy', schema.encode(), {'declared': xml.encode()})
        standalone = run_entity_documents([job])
        soap = run([job])
        self.assertTrue(standalone['documents']['declared']['ok'])
        self.assertEqual([], standalone['documents']['declared']['warnings'])
        self.assertFalse(soap['documents']['declared']['ok'])
        self.assertIn('DOCTYPE', soap['documents']['declared']['desc'])

    def test_standalone_oracle_keeps_external_resources_disabled(self):
        entity_schema = (f'<xs:schema xmlns:xs="{XSD}">'
                         '<xs:element name="value" type="xs:ENTITY"/></xs:schema>')
        empty_schema = (f'<xs:schema xmlns:xs="{XSD}"><xs:element name="value">'
                        '<xs:simpleType><xs:restriction base="xs:string"><xs:length value="0"/>'
                        '</xs:restriction></xs:simpleType></xs:element></xs:schema>')
        with tempfile.TemporaryDirectory(prefix='wsdl-entity-offline-') as temporary:
            root = Path(temporary)
            content = root / 'content.txt'
            content.write_text('external content must not be read', encoding='utf-8')
            declarations = root / 'entities.dtd'
            declarations.write_text(NOTATION + UNPARSED, encoding='utf-8')
            jobs = [
                SchemaJob('empty', 'urn:entity-offline:empty', empty_schema.encode(), {
                    'external-general': (f'<!DOCTYPE value [<!ENTITY external SYSTEM "{content.as_uri()}">]>'
                                         '<value>&external;</value>').encode(),
                    'internal-text-control': b'<!DOCTYPE value [<!ENTITY internal "text">]><value>&internal;</value>',
                }),
                SchemaJob('entity', 'urn:entity-offline:entity', entity_schema.encode(), {
                    'external-subset': (f'<!DOCTYPE value SYSTEM "{declarations.as_uri()}">'
                                        '<value>photo</value>').encode(),
                    'external-parameter': (f'<!DOCTYPE value [<!ENTITY % external SYSTEM "{declarations.as_uri()}">'
                                           '%external;]><value>photo</value>').encode(),
                    'internal-control': f'<!DOCTYPE value [{NOTATION}{UNPARSED}]><value>photo</value>'.encode(),
                }),
            ]
            oracle = run_entity_documents(jobs)
        for name, valid in {'external-general': True, 'internal-text-control': False,
                            'external-subset': False, 'external-parameter': False,
                            'internal-control': True}.items():
            with self.subTest(document=name):
                self.assertEqual(valid, oracle['documents'][name]['ok'])
                self.assertEqual([], oracle['documents'][name]['warnings'])
        dtd_schema = b'<!DOCTYPE xs:schema []>' + entity_schema.encode()
        rejected = run_entity_documents([SchemaJob('dtd-schema', 'urn:entity-offline:schema', dtd_schema,
                                                   {'unreachable': b'<value/>'})])
        self.assertFalse(rejected['schemas']['dtd-schema']['ok'])
        self.assertIn('DOCTYPE', rejected['schemas']['dtd-schema']['desc'])
        self.assertEqual('unreachable', rejected['documents']['unreachable']['status'])


if __name__ == '__main__':
    unittest.main()
