#!/usr/bin/env python3
"""Native XSD wildcard IDs against pinned Xerces, including absent ID uses.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent

XSD = 'http://www.w3.org/2001/XMLSchema'


def models():
    for processing in ('strict', 'lax', 'skip'):
        for declared in (False, True):
            for derived in (False, True):
                for qualified in (False, True):
                    name = f'{processing}/{declared}/{derived}/{qualified}'
                    prefix = 't:' if qualified else ''
                    datatype = prefix + 'Identifier' if derived else 'xs:ID'
                    target = ' targetNamespace="urn:wild-id"' if qualified else ''
                    use = f'<xs:attribute name="id" type="{datatype}"/>' if declared else ''
                    source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="urn:wild-id"{target}>
                      <xs:simpleType name="Identifier"><xs:restriction base="xs:ID"/></xs:simpleType>
                      <xs:attribute name="first" type="{datatype}"/><xs:attribute name="second" type="{datatype}"/>
                      <xs:element name="root"><xs:complexType>{use}<xs:anyAttribute processContents="{processing}"/>
                      </xs:complexType></xs:element></xs:schema>'''
                    documents = []
                    for present in ((False, True) if declared else (False,)):
                        for mask in range(4):
                            attributes = []
                            if mask & 1:
                                attributes.append(prefix + 'first="one"')
                            if mask & 2:
                                attributes.append(prefix + 'second="two"')
                            for reverse in ((False, True) if mask == 3 else (False,)):
                                attrs = ('id="three" ' if present else '') + ' '.join(
                                    reversed(attributes) if reverse else attributes)
                                documents.append({'name': f'{name}/{present}/{mask}/{reverse}',
                                    'xml': f'<{prefix}root xmlns:t="urn:wild-id" {attrs}/>',
                                    'valid': processing == 'skip' or (not declared and mask != 3) or not mask})
                    yield {'name': name, 'schema': source, 'documents': documents}


def schema_models():
    definitions = """<xs:simpleType name="Identifier"><xs:restriction base="xs:ID"/></xs:simpleType>
      <xs:simpleType name="DeepId"><xs:restriction base="Identifier"/></xs:simpleType>
      <xs:simpleType name="Text"><xs:restriction base="xs:string"/></xs:simpleType>
      <xs:simpleType name="IdList"><xs:list itemType="xs:ID"/></xs:simpleType>
      <xs:simpleType name="InlineList"><xs:list><xs:simpleType><xs:restriction base="xs:ID"/>
        </xs:simpleType></xs:list></xs:simpleType>
      <xs:simpleType name="IdUnion"><xs:union memberTypes="xs:ID xs:string"/></xs:simpleType>
      <xs:simpleType name="InlineUnion"><xs:union><xs:simpleType><xs:restriction base="xs:ID"/>
        </xs:simpleType><xs:simpleType><xs:restriction base="xs:string"/></xs:simpleType></xs:union></xs:simpleType>
      <xs:simpleType name="ListRestriction"><xs:restriction base="IdList"/></xs:simpleType>
      <xs:simpleType name="UnionRestriction"><xs:restriction base="IdUnion"/></xs:simpleType>"""
    for datatype in ('xs:ID', 'Identifier', 'DeepId', 'Text', 'IdList', 'InlineList', 'IdUnion',
                     'InlineUnion', 'ListRestriction', 'UnionRestriction'):
        shapes = {
            'two-uses': f'<xs:complexType name="Record"><xs:attribute name="one" type="{datatype}"/>'
                        f'<xs:attribute name="two" type="{datatype}"/></xs:complexType>',
            'two-group-uses': f'<xs:attributeGroup name="Group"><xs:attribute name="one" type="{datatype}"/>'
                              f'<xs:attribute name="two" type="{datatype}"/></xs:attributeGroup>'}
        for constraint in ('default', 'fixed'):
            shapes['attribute-' + constraint] = f'<xs:attribute name="a" type="{datatype}" {constraint}="one"/>'
            shapes['use-' + constraint] = f'<xs:attribute name="a" type="{datatype}"/>' + \
                f'<xs:complexType name="Record"><xs:attribute ref="a" {constraint}="one"/></xs:complexType>'
            shapes['element-' + constraint] = f'<xs:element name="value" type="{datatype}" {constraint}="one"/>'
            shapes['content-' + constraint] = f'<xs:element name="value" {constraint}="one"><xs:complexType>' + \
                f'<xs:simpleContent><xs:extension base="{datatype}"/></xs:simpleContent></xs:complexType></xs:element>'
        for shape, content in shapes.items():
            yield {'name': f'schema/{datatype}/{shape}', 'valid': datatype not in ('xs:ID', 'Identifier', 'DeepId'),
                   'schema': f'<xs:schema xmlns:xs="{XSD}">{definitions}{content}'
                             '<xs:element name="probe" type="xs:string"/></xs:schema>',
                   'documents': []}


class NativeWildcardIdsTest(unittest.TestCase):
    def test_id_ancestry_schema_constraints_exclude_list_and_union_members(self):
        fixtures = list(schema_models())
        self.assertEqual(100, len(fixtures))
        oracle = run_independent([SchemaJob(m['name'], f'http://example.invalid/id-types/{i}.xsd',
                                           m['schema'].encode()) for i, m in enumerate(fixtures)])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        with tempfile.TemporaryDirectory(prefix='native-id-schema-') as folder:
            path = Path(folder) / 'manifest.json'
            path.write_text(json.dumps(fixtures))
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                str(Path(__file__).with_name('native-wildcard-ids.qr')), str(path)],
                capture_output=True, text=True, timeout=120)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(fixtures), len(rows))
        for model, row in zip(fixtures, rows):
            self.assertEqual(model['name'], row['model'])
            # XSD 1.0 Structures 2.2.1.1/3.14.2 define ancestry through the
            # base type, not list items or union members. Xerces instead counts
            # ID-containing lists/unions here and misses simple-content IDs.
            # Keep both discrepancies explicit; native expectations stay normative.
            _, datatype, shape = model['name'].split('/')
            xerces_expected = shape.startswith('content-') or datatype == 'Text'
            self.assertEqual(xerces_expected, oracle['schemas'][model['name']]['ok'], model)
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            self.assertEqual(model['valid'], row['schema'], row)
            if not model['valid']:
                self.assertEqual('XSD-SYNTAX-ERROR', row.get('error'), row)
        print(f'{mode}: 100 ID ancestry schema cases, 30 required schema rejections', flush=True)

    def test_dom_streaming_diagnostics_and_independent_rejections(self):
        fixtures = list(models())
        self.assertEqual(24, len(fixtures))
        self.assertEqual(180, sum(len(model['documents']) for model in fixtures))
        self.assertEqual(80, sum(not document['valid'] for model in fixtures for document in model['documents']))
        jobs = []
        for index, model in enumerate(fixtures):
            validator = etree.XMLSchema(etree.fromstring(model['schema'].encode()))
            for document in model['documents']:
                # Pinned lxml/libxml2 2.12.10 omits both wildcard-ID reports.
                # The normative negative is mandatory for native Qore and Xerces below.
                self.assertTrue(validator.validate(etree.fromstring(document['xml'].encode())),
                                (document, str(validator.error_log)))
            jobs.append(SchemaJob(model['name'], f'http://example.invalid/wildcard-ids/{index}.xsd',
                                  model['schema'].encode(), {d['name']: d['xml'].encode() for d in model['documents']}))
        oracle = run_independent(jobs)
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        with tempfile.TemporaryDirectory(prefix='native-wildcard-ids-') as folder:
            path = Path(folder) / 'manifest.json'
            path.write_text(json.dumps(fixtures))
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                str(Path(__file__).with_name('native-wildcard-ids.qr')), str(path)],
                capture_output=True, text=True, timeout=120)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = iter(json.loads(line) for line in result.stdout.splitlines())
        count = 0
        for model in fixtures:
            self.assertTrue(oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for document in model['documents']:
                row = next(rows)
                count += 1
                self.assertEqual((model['name'], document['name']), (row['model'], row['document']))
                expected = bool(document['valid'])
                self.assertEqual(expected, oracle['documents'][document['name']]['ok'], document)
                self.assertEqual([], oracle['documents'][document['name']]['warnings'])
                for path in ('dom', 'reader'):
                    self.assertEqual(expected, row[path], row)
                    if expected:
                        self.assertNotIn(path + '_error', row)
                    else:
                        self.assertEqual('PARSE-XML-EXCEPTION', row.get(path + '_error'), row)
        self.assertIsNone(next(rows, None))
        self.assertEqual(180, count)
        print(f'{mode}: 24 schemas, 180 documents, 360 native paths, 160 required rejections', flush=True)


if __name__ == '__main__':
    unittest.main()
