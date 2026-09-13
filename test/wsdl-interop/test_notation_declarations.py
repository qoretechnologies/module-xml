#!/usr/bin/env python3
"""Independent notation declaration grammar and saved metadata checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from independent import SchemaJob, run

ROOT = Path(__file__).parent
XSD = 'http://www.w3.org/2001/XMLSchema'


def models():
    cases = [
        ('public', 'name="jpeg" public="image/jpeg"', '', True, 'image/jpeg', None),
        ('system', 'name="jpeg" system="formats/jpeg"', '', True, None, 'formats/jpeg'),
        ('both', 'name="jpeg" public="p" system="s"', '', True, 'p', 's'),
        ('empty-public', 'name="jpeg" public=""', '', True, '', None),
        ('empty-system', 'name="jpeg" system=""', '', True, None, ''),
        ('normalized', 'name=" &#x9;jpeg&#xA; " public=" [bad]&#x9; token " system="a&#xA;b"', '',
         True, '[bad] token', 'a b'),
        ('foreign', 'name="jpeg" public="p" xmlns:m="urn:meta" m:public="other" m:name="other"', '',
         True, 'p', None),
        ('annotation', 'name="jpeg" public="p"', '<xs:annotation><xs:documentation>JPEG'
         '<m:link xmlns:m="urn:meta">image</m:link></xs:documentation></xs:annotation>', True, 'p', None),
        ('comments', 'name="jpeg" public="p"', '\n<!-- comment --><?note text?>\t', True, 'p', None),
        ('id', 'name="jpeg" public="p" id=" image "', '', True, 'p', None),
    ]
    for name, attributes, content in [
        ('no-name', 'public="p"', ''), ('no-identifier', 'name="jpeg"', ''),
        ('empty-name', 'name="" public="p"', ''), ('qualified-name', 'name="p:jpeg" public="p"', ''),
        ('digit-name', 'name="0jpeg" public="p"', ''), ('space-name', 'name="two names" public="p"', ''),
        ('empty-id', 'name="jpeg" public="p" id=""', ''),
        ('qualified-id', 'name="jpeg" public="p" id="a:b"', ''),
        ('unknown', 'name="jpeg" public="p" bad="x"', ''),
        ('schema-attribute', 'name="jpeg" public="p" xs:bad="x"', ''),
        ('schema-public', 'name="jpeg" xs:public="p"', ''),
        ('foreign-public', 'name="jpeg" xmlns:m="urn:meta" m:public="p"', ''),
        ('child', 'name="jpeg" public="p"', '<xs:element/>'),
        ('foreign-annotation', 'name="jpeg" public="p"', '<annotation/>'),
        ('duplicate-annotation', 'name="jpeg" public="p"', '<xs:annotation/><xs:annotation/>'),
        ('text', 'name="jpeg" public="p"', 'text'),
        ('cdata', 'name="jpeg" public="p"', '<![CDATA[text]]>'),
    ]:
        cases.append((name, attributes, content, False, None, None))
    for namespace in ('', 'urn:notations'):
        for name, attributes, content, valid, public, system in cases:
            schema = f'<xs:schema xmlns:xs="{XSD}"'
            if namespace:
                schema += f' targetNamespace="{namespace}"'
            schema += f'><xs:notation {attributes}>{content}</xs:notation>'
            schema += '<xs:element name="value" type="xs:string"/></xs:schema>'
            yield {'name': ('qualified-' if namespace else 'local-') + name, 'schema': schema,
                   'xml': f'<value xmlns="{namespace}">text</value>', 'valid': valid,
                   'key': f'{{{namespace}}}jpeg', 'metadata': {'namespace_uri': namespace,
                   'local_name': 'jpeg', 'public_id': public, 'system_id': system}}


class NotationDeclarationsTest(unittest.TestCase):
    def test_native_wsdl_and_saved_metadata(self):
        cases = list(models())
        self.assertEqual(54, len(cases))
        self.assertEqual(len(cases), len({m['name'] for m in cases}))
        with tempfile.TemporaryDirectory(prefix='wsdl-notation-declarations-') as directory:
            fixture = Path(directory) / 'models.json'
            fixture.write_text(json.dumps(cases))
            completed = subprocess.run([os.environ.get('QORE', 'qore'), '-b', '--enable-debug',
                str(ROOT / 'notation-declarations.qr'), str(fixture)], capture_output=True, text=True, timeout=90)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual('', completed.stderr)
        rows = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([m['name'] for m in cases], [r['name'] for r in rows])
        for model, row in zip(cases, rows):
            with self.subTest(name=model['name']):
                self.assertEqual(model['valid'], row['native'], row)
                self.assertEqual(model['valid'], row['wsdl'], row)
                if model['valid']:
                    self.assertEqual([model['metadata']] * 6, row['metadata'])
                else:
                    self.assertEqual('XSD-SYNTAX-ERROR', row['native_error'])
                    self.assertEqual('WSDL-ERROR', row['wsdl_error'])

    def test_pinned_xerces(self):
        cases = list(models())
        report = run([SchemaJob(m['name'], f'http://example.invalid/notations/{i}.xsd',
            m['schema'].encode(), {m['name']: m['xml'].encode()}) for i, m in enumerate(cases)], {})
        for model in cases:
            with self.subTest(name=model['name']):
                schema = report['schemas'][model['name']]
                document = report['documents'][model['name']]
                self.assertEqual(model['valid'], schema['ok'], schema)
                self.assertEqual(True if model['valid'] else None, document['ok'], document)
                self.assertEqual([], schema['warnings'])
                self.assertEqual([], document['warnings'])


if __name__ == '__main__':
    unittest.main()
