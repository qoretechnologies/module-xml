#!/usr/bin/env python3
"""Independent XML character preservation through actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
Every node in these models has mixed/generic content: whitespace is data.
Schema validity alone cannot detect its deletion. Legacy decoding of a declared
anyType scalar infers xs:string on output under the established generic-value
contract; those exact annotation additions are counted and checked separately.
"""
import itertools
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run
from survey import SOAP_NAMESPACES


XSD = 'http://www.w3.org/2001/XMLSchema'


def models():
    declarations = {
        'generic': '<xs:element name="root" type="xs:anyType"/>',
        'mixed': '<xs:element name="root"><xs:complexType mixed="true"><xs:sequence>'
                 '<xs:element name="a" type="xs:anyType" minOccurs="0" maxOccurs="unbounded"/>'
                 '</xs:sequence><xs:anyAttribute processContents="lax"/></xs:complexType></xs:element>',
        'skip': '<xs:element name="root"><xs:complexType mixed="true"><xs:sequence>'
                '<xs:any processContents="skip" minOccurs="0" maxOccurs="unbounded"/>'
                '</xs:sequence><xs:anyAttribute processContents="skip"/></xs:complexType></xs:element>',
    }
    documents = [
        '<root> <a/> <a/> </root>',
        '<root>&#9;<a>17</a>&#10;<a>23</a>&#13;</root>',
        '<root xml:space="preserve"> <a xml:space="default"> <inner/> <inner/> </a> </root>',
        '<root> <a> <inner/> <inner/> </a> <a/> </root>',
        '<root><a/> </root>',
        '<root> <a/></root>',
    ]
    return [{'name': name, 'schema': f'<xs:schema xmlns:xs="{XSD}">{declaration}</xs:schema>',
             'documents': [{'name': f'{name}/{index}', 'xml': xml} for index, xml in enumerate(documents)]}
            for name, declaration in declarations.items()]


def characters(node):
    """Observe all expanded names, attributes, ordered children and character data."""
    return (node.tag, sorted(node.attrib.items()), node.text or '',
            [(characters(child), child.tail or '') for child in node])


class CharacterWhitespaceTest(unittest.TestCase):
    def test_comparison_detects_schema_valid_deletion(self):
        schema = etree.XMLSchema(etree.fromstring(models()[0]['schema'].encode()))
        before, after = (etree.fromstring(xml) for xml in (b'<root><a/> <a/></root>', b'<root><a/><a/></root>'))
        self.assertTrue(schema.validate(before))
        self.assertTrue(schema.validate(after))
        self.assertNotEqual(characters(before), characters(after))
        self.assertNotEqual(characters(etree.fromstring(b'<root> <a/></root>')),
                            characters(etree.fromstring(b'<root><a/> </root>')))

    def test_saved_binding_matrix(self):
        cases = models()
        documents = {d['name']: d for model in cases for d in model['documents']}
        self.assertEqual(18, len(documents))
        with tempfile.TemporaryDirectory(prefix='wsdl-character-whitespace-') as directory:
            fixture = Path(directory) / 'models.json'
            fixture.write_text(json.dumps(cases))
            worker = Path(__file__).with_name('character-whitespace.qr')
            result = subprocess.run(['qore', '-b', '--enable-debug', str(worker), str(fixture)],
                                    capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        expected = set(itertools.product(documents, ['11', '12'], [False, True], [False, True], [False, True]))
        self.assertEqual(288, len(expected))
        self.assertEqual(len(expected), len(rows))
        self.assertEqual(expected, {(r['name'], r['version'], r['saved'], r['response'], r['preserve']) for r in rows})
        jobs = {model['name']: SchemaJob(model['name'], f'http://example.invalid/whitespace/{model["name"]}.xsd',
                model['schema'].encode(), {d['name'] + '/source': d['xml'].encode() for d in model['documents']})
                for model in cases}
        legacy_rows = legacy_annotations = 0
        for index, row in enumerate(rows):
            with self.subTest(name=row['name'], version=row['version'], saved=row['saved'],
                              response=row['response'], preserve=row['preserve']):
                self.assertNotIn('error', row, row)
                envelope = etree.fromstring(row['xml'].encode())
                namespace = SOAP_NAMESPACES[0 if row['version'] == '11' else 1]
                self.assertEqual('{' + namespace + '}Envelope', envelope.tag)
                body = envelope.find('{' + namespace + '}Body')
                self.assertIsNotNone(body)
                self.assertEqual(1, len(body))
                payload = body[0]
                jobs[row['name'].split('/')[0]].documents[f'output/{index}'] = etree.tostring(payload)
                original = etree.fromstring(documents[row['name']]['xml'].encode())
                if row['name'].startswith('mixed/') and not row['preserve']:
                    # This model declares a as anyType. Legacy scalar projection
                    # emits an inferred type; native projection retains absence.
                    annotated = 0
                    self.assertEqual(len(original), len(payload))
                    for source, actual in zip(original, payload):
                        if len(source) or source.attrib:
                            continue
                        lexical = actual.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                        self.assertIsNotNone(lexical)
                        prefix, local = lexical.split(':') if ':' in lexical else (None, lexical)
                        self.assertEqual((XSD, 'string'), (actual.nsmap.get(prefix), local))
                        del actual.attrib['{http://www.w3.org/2001/XMLSchema-instance}type']
                        annotated += 1
                    legacy_rows += bool(annotated)
                    legacy_annotations += annotated
                self.assertEqual(characters(original), characters(payload))
        self.assertEqual(40, legacy_rows)
        self.assertEqual(56, legacy_annotations)
        oracle = run(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual({key for job in jobs.values() for key in job.documents}, set(oracle['documents']))
        for result in [*oracle['schemas'].values(), *oracle['documents'].values()]:
            self.assertTrue(result['ok'], result)
            self.assertEqual([], result['warnings'])


if __name__ == '__main__':
    unittest.main()
