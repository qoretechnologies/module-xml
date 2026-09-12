#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Native character-event semantics against XSD-derived verdicts and pinned Xerces."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from independent import SchemaJob, run as independent

XSD = 'http://www.w3.org/2001/XMLSchema'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def models():
    contents = [('empty', '', True, False), ('text', '17', False, False),
                ('space', ' ', False, False), ('child', '<child/>', False, True),
                ('comment', '<!--comment-->', True, False), ('empty-cdata', '<![CDATA[]]>', True, False),
                ('space-cdata', '<![CDATA[ ]]>', False, False)]
    for datatype in ('anyType', 'anySimpleType', 'int'):
        for nillable in (False, True):
            for fixed in (False, True):
                name = f'{datatype}/{nillable}/{fixed}'
                source = (f'<xs:schema xmlns:xs="{XSD}"><xs:element name="root" type="xs:{datatype}"'
                          + f' nillable="{str(nillable).lower()}"' + (' fixed="17"' if fixed else '')
                          + '/></xs:schema>')
                documents = []
                for lexical in ('true', '1', 'false', '0', ' true ', ' false ', 'invalid', 'TRUE', ''):
                    for label, text, empty, children in contents:
                        valid = False
                        normalized = lexical.strip()
                        if nillable and normalized in ('true', '1', 'false', '0'):
                            if normalized in ('true', '1'):
                                valid = empty and not fixed
                            else:
                                valid = (datatype == 'anyType' or (not children and
                                         (datatype == 'anySimpleType' or label == 'text' or (fixed and empty))))
                                if fixed:
                                    valid = valid and not children and (empty or label == 'text')
                        xml = f'<root xmlns:xsi="{XSI}" xsi:nil="{lexical}">{text}</root>'
                        documents.append({'name': f'{name}/{lexical!r}/{label}', 'xml': xml, 'valid': valid})
                yield {'name': name, 'schema': source, 'documents': documents}
    contents = [
        ('empty', '', (True, True, False, True)),
        ('empty-cdata', '<![CDATA[]]>', (True, True, False, True)),
        ('comment', '<!--comment-->', (True, True, False, True)),
        ('empty-boundaries', '<![CDATA[]]><!--comment--><![CDATA[]]>', (True, True, False, True)),
        ('space', ' \t\n', (False, True, False, True)),
        ('space-cdata', '<![CDATA[ \t\n]]>', (False, True, False, True)),
        ('text', 'text', (False, False, False, True)),
        ('text-cdata', '<![CDATA[text]]>', (False, False, False, True)),
        ('non-xml-space', '<![CDATA[\u00a0]]>', (False, False, False, True)),
        ('child', '<child>shipment</child>', (False, True, True, True)),
        ('child-space', '<![CDATA[ ]]><child>shipment</child><![CDATA[\t]]>', (False, True, True, True)),
        ('child-text', 'before<child>shipment</child>after', (False, False, False, True)),
        ('wrong-child', '<other/>', (False, False, False, False)),
        ('two-children', '<child/><child/>', (False, False, False, False)),
    ]
    for index, name in enumerate(('empty-content', 'element-only', 'required-child', 'mixed')):
        child = ('' if index == 0 else '<xs:sequence><xs:element name="child" type="xs:string"'
                 + (' minOccurs="0"' if index != 2 else '') + '/></xs:sequence>')
        source = (f'<xs:schema xmlns:xs="{XSD}"><xs:element name="root"><xs:complexType'
                  + (' mixed="true"' if index == 3 else '') + '>' + child
                  + '</xs:complexType></xs:element></xs:schema>')
        documents = [{'name': name + '/' + label, 'xml': '<root>' + text + '</root>', 'valid': verdicts[index]}
                     for label, text, verdicts in contents]
        yield {'name': name, 'schema': source, 'documents': documents}


class CharacterContentTest(unittest.TestCase):
    def test_character_content(self):
        fixtures = list(models())
        self.assertEqual(16, len(fixtures))
        expected = {document['name']: document for model in fixtures for document in model['documents']}
        self.assertEqual(812, len(expected))
        with tempfile.TemporaryDirectory(prefix='wsdl-character-content-') as folder:
            manifest = Path(folder) / 'manifest.json'
            manifest.write_text(json.dumps(fixtures))
            worker = Path(__file__).with_name('character-content.qr')
            result = subprocess.run(['qore', '-b', '--enable-debug', str(worker), str(manifest)],
                                    capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-3000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(812, len(rows))
        self.assertEqual(set(expected), {row['name'] for row in rows})
        for row in rows:
            for path, category in (('dom', 'PARSE-XML-EXCEPTION'), ('reader', 'PARSE-XML-EXCEPTION'),
                                   ('document', 'XSD-ERROR')):
                self.assertEqual(expected[row['name']]['valid'], row[path], (path, row))
                if not row[path]:
                    self.assertEqual(category, row[path + '_error'], row)
                elif path != 'reader':
                    self.assertTrue(row[path + '_preserved'], row)
        jobs = [SchemaJob(model['name'], f'http://example.invalid/characters/{index}.xsd',
                          model['schema'].encode(), {d['name']: d['xml'].encode() for d in model['documents']})
                for index, model in enumerate(fixtures)]
        oracle = independent(jobs)
        self.assertEqual({model['name'] for model in fixtures}, set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        for row in oracle['schemas'].values():
            self.assertTrue(row['ok'], row)
            self.assertEqual([], row['warnings'])
        for name, document in expected.items():
            self.assertEqual(document['valid'], oracle['documents'][name]['ok'], name)
            self.assertEqual([], oracle['documents'][name]['warnings'])
        print('16 schemas, 812 documents: DOM/reader/document and Xerces agree; valid XML data preserved')


if __name__ == '__main__':
    unittest.main()
