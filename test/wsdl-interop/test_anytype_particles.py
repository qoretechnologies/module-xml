#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Builtin anyType particle inheritance against pinned Xerces and all native XML APIs."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from independent import SchemaJob, run as independent

XSD = 'http://www.w3.org/2001/XMLSchema'


def models():
    base = ('<xs:complexType name="Base"><xs:complexContent><xs:extension base="xs:anyType">'
            '<xs:sequence/></xs:extension></xs:complexContent></xs:complexType>')
    for name, parent, content, declarations, restriction in (
        ('direct', '', '', '', False),
        ('empty', 'xs:anyType', '', '', False),
        ('sequence', 'xs:anyType', '<xs:sequence/>', '', False),
        ('group', 'xs:anyType', '<xs:group ref="Empty"/>',
         '<xs:group name="Empty"><xs:sequence/></xs:group>', False),
        ('group-mixed', 'xs:anyType', '<xs:group ref="Empty"/>',
         '<xs:group name="Empty"><xs:sequence/></xs:group>', False),
        ('transitive', 'Base', '', base, False),
        ('restriction', 'xs:anyType', '<xs:sequence><xs:element ref="known"/></xs:sequence>', '', True),
        ('derived-restriction', 'Base', '<xs:sequence><xs:element ref="known"/></xs:sequence>', base, True),
        ('ambiguous', 'xs:anyType', '<xs:sequence><xs:element ref="known"/></xs:sequence>', '', False),
        ('derived-ambiguous', 'Base', '<xs:sequence><xs:element ref="known"/></xs:sequence>', base, False)):
        method = 'restriction' if restriction else 'extension'
        mixed = ' mixed="true"' if name == 'group-mixed' or 'ambiguous' in name else ''
        element = (f'<xs:element name="r"><xs:complexType><xs:complexContent{mixed}>'
                   f'<xs:{method} base="{parent}">{content}</xs:{method}>'
                   '</xs:complexContent></xs:complexType></xs:element>') if parent else (
                   '<xs:element name="r" type="xs:anyType"/>')
        schema = (f'<xs:schema xmlns:xs="{XSD}"><xs:element name="known" type="xs:int"/>'
                  '<xs:attribute name="code" type="xs:int"/>' + declarations + element + '</xs:schema>')
        schema_valid = 'ambiguous' not in name and name != 'group'
        documents = []
        for index, (xml, valid) in enumerate((
            ('<r/>', not restriction),
            ('<r><known>17</known></r>', True),
            ('<r>before<unknown/><known>17</known>after</r>', not restriction),
            ('<r code="17" other="shipment"><unknown><known>23</known></unknown></r>', not restriction),
            ('<r xmlns:p="urn:shipment"><p:part>17</p:part><p:part>18</p:part></r>', not restriction),
            ('<r><known>bad</known></r>', False),
            ('<r code="bad"/>', False),
            ('<r><unknown><known>bad</known></unknown></r>', False),
            ('<r><known>17</known><unknown/></r>', not restriction),
            ('<r>text<known>17</known></r>', not restriction))):
            documents.append({'name': f'{name}/{index}', 'xml': xml, 'valid': schema_valid and valid})
        yield {'name': name, 'schema': schema, 'schema_valid': schema_valid, 'documents': documents}


class AnyTypeParticlesTest(unittest.TestCase):
    def test_inheritance(self):
        fixtures = list(models())
        self.assertEqual(10, len(fixtures))
        expected = {doc['name']: dict(doc, schema_valid=model['schema_valid'])
                    for model in fixtures for doc in model['documents']}
        self.assertEqual(100, len(expected))
        with tempfile.TemporaryDirectory(prefix='xml-anytype-') as directory:
            manifest = Path(directory) / 'manifest.json'
            manifest.write_text(json.dumps(fixtures))
            result = subprocess.run(['qore', '-b', '--enable-debug',
                                     str(Path(__file__).with_name('character-content.qr')), str(manifest)],
                                    capture_output=True, text=True, timeout=120)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-3000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(expected), len(rows))
        self.assertEqual(set(expected), {row['name'] for row in rows})
        for row in rows:
            wanted = expected[row['name']]
            for path, category in (('dom', 'PARSE-XML-EXCEPTION'), ('reader', 'PARSE-XML-EXCEPTION'),
                                   ('document', 'XSD-ERROR')):
                self.assertEqual(wanted['valid'], row[path], (path, row))
                if not row[path]:
                    self.assertEqual(category if wanted['schema_valid'] else 'XSD-SYNTAX-ERROR',
                                     row[path + '_error'], row)
                elif path != 'reader':
                    self.assertTrue(row[path + '_preserved'], row)
        oracle = independent([SchemaJob(model['name'], f'http://example.invalid/anytype/{index}.xsd',
                              model['schema'].encode(), {d['name']: d['xml'].encode() for d in model['documents']})
                              for index, model in enumerate(fixtures)])
        self.assertEqual({m['name'] for m in fixtures}, set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        for model in fixtures:
            self.assertEqual(model['schema_valid'], oracle['schemas'][model['name']]['ok'], model['name'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            for doc in model['documents']:
                self.assertEqual(doc['valid'] if model['schema_valid'] else None,
                                 oracle['documents'][doc['name']]['ok'], doc['name'])
                self.assertEqual([], oracle['documents'][doc['name']]['warnings'])
        print(f'{len(fixtures)} schemas, {len(expected)} documents: native XML and Xerces agree')


if __name__ == '__main__':
    unittest.main()
