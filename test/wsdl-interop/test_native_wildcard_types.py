#!/usr/bin/env python3
"""Native strict/lax/skip wildcard assessment against pinned Xerces.

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
XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def models():
    for mode in ('strict', 'lax', 'skip'):
        for qualified in (False, True):
            prefix = 't:' if qualified else ''
            target = 'urn:wild-type' if qualified else ''
            target_attribute = f' targetNamespace="{target}"' if qualified else ''
            for namespace in ('##any', '##other', '##local', '##targetNamespace', 'urn:child', 'urn:child ##local'):
                name = f'{mode}/{qualified}/{namespace}'
                source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="urn:wild-type"{target_attribute}>
                    <xs:element name="known" type="xs:int"/>
                    <xs:simpleType name="Restricted"><xs:restriction base="xs:int">
                      <xs:maxInclusive value="9"/></xs:restriction></xs:simpleType>
                    <xs:complexType name="Record"><xs:sequence><xs:element name="code" type="xs:int"/>
                      </xs:sequence><xs:attribute name="tag" type="xs:string" use="required"/></xs:complexType>
                    <xs:complexType name="Abstract" abstract="true"/>
                    <xs:element name="root"><xs:complexType><xs:sequence>
                      <xs:any namespace="{namespace}" processContents="{mode}" minOccurs="0" maxOccurs="unbounded"/>
                    </xs:sequence></xs:complexType></xs:element></xs:schema>'''
                content_cases = (
                    ('empty', '', True, True),
                    ('known', f'<{prefix}known>17</{prefix}known>', True, True),
                    ('known-invalid', f'<{prefix}known>bad</{prefix}known>', False, False),
                    ('unknown', '<q:unknown>text</q:unknown>', False, True),
                    ('builtin', '<q:unknown xsi:type="xs:int">17</q:unknown>', True, True),
                    ('builtin-invalid', '<q:unknown xsi:type="xs:int">bad</q:unknown>', False, False),
                    ('unresolved', '<q:unknown xsi:type="xs:Missing">17</q:unknown>', False, False),
                    ('restricted', f'<q:unknown xsi:type="{prefix}Restricted">5</q:unknown>', True, True),
                    ('restricted-invalid', f'<q:unknown xsi:type="{prefix}Restricted">99</q:unknown>', False, False),
                    ('record', f'<q:unknown xsi:type="{prefix}Record" tag="shipment"><code>17</code></q:unknown>', True, True),
                    ('record-invalid', f'<q:unknown xsi:type="{prefix}Record" tag="shipment"><code>bad</code></q:unknown>', False, False),
                    ('missing-attribute', f'<q:unknown xsi:type="{prefix}Record"><code>17</code></q:unknown>', False, False),
                    ('abstract', f'<q:unknown xsi:type="{prefix}Abstract"/>', False, False),
                    ('unbound-type', '<q:unknown xsi:type="unbound:Type"/>', False, False),
                    ('qname', '<q:unknown xsi:type="xs:QName">p:Stock</q:unknown>', True, True),
                    ('qname-invalid', '<q:unknown xsi:type="xs:QName">unbound:Stock</q:unknown>', False, False),
                    ('nested-invalid', f'<q:unknown><{prefix}known>bad</{prefix}known></q:unknown>', False, False),
                    ('nested', f'<q:unknown><{prefix}known>17</{prefix}known></q:unknown>', False, True),
                    ('derivation', f'<{prefix}known xsi:type="xs:string">17</{prefix}known>', False, False),
                )
                documents = []
                for label, content, strict, lax in content_cases:
                    xml = (f'<{prefix}root xmlns:t="urn:wild-type" xmlns:q="urn:child" xmlns:p="urn:products" '
                           f'xmlns:xs="{XSD}" xmlns:xsi="{XSI}">{content}</{prefix}root>')
                    tree = etree.fromstring(xml.encode())
                    allowed = True
                    for child in tree:
                        uri = etree.QName(child).namespace or ''
                        if namespace == '##other':
                            allowed = uri not in ('', target)
                        elif namespace != '##any':
                            uris = {'' if token == '##local' else target if token == '##targetNamespace' else token
                                    for token in namespace.split()}
                            allowed = uri in uris
                    valid = allowed and (mode == 'skip' or (strict if mode == 'strict' else lax))
                    # Pinned lxml/libxml2 rejects every undeclared strict wildcard
                    # before considering xsi:type. Keep this discrepancy explicit.
                    lxml_valid = valid and not (mode == 'strict' and label in ('builtin', 'restricted', 'record', 'qname'))
                    documents.append({'name': name + '/' + label, 'xml': xml, 'valid': valid,
                                      'lxml_valid': lxml_valid})
                yield {'name': name, 'schema': source, 'documents': documents}


class NativeWildcardTypesTest(unittest.TestCase):
    def test_namespace_constraints_and_instance_assessment(self):
        fixtures = list(models())
        self.assertEqual(36, len(fixtures))
        self.assertEqual(684, sum(len(model['documents']) for model in fixtures))
        jobs = []
        for index, model in enumerate(fixtures):
            validator = etree.XMLSchema(etree.fromstring(model['schema'].encode()))
            for document in model['documents']:
                self.assertEqual(document['lxml_valid'], validator.validate(etree.fromstring(document['xml'].encode())),
                                 (document, str(validator.error_log)))
            jobs.append(SchemaJob(model['name'], f'http://example.invalid/wildcard-types/{index}.xsd',
                                  model['schema'].encode(), {d['name']: d['xml'].encode() for d in model['documents']}))
        oracle = run_independent(jobs)
        self.assertEqual({m['name'] for m in fixtures}, set(oracle['schemas']))
        self.assertEqual({d['name'] for m in fixtures for d in m['documents']}, set(oracle['documents']))
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        worker = os.environ.get('WSDL_NATIVE_WILDCARD_TYPES_WORKER',
                                str(Path(__file__).with_name('native-wildcard-types.qr')))
        with tempfile.TemporaryDirectory(prefix='native-wildcard-types-') as folder:
            manifest = Path(folder) / 'manifest.json'
            manifest.write_text(json.dumps(fixtures))
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode, worker, str(manifest)],
                                    capture_output=True, text=True, timeout=120)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(684, len(rows))
        expected_rows = [(m, d) for m in fixtures for d in m['documents']]
        for (model, document), row in zip(expected_rows, rows):
            self.assertEqual((model['name'], document['name']), (row['model'], row['document']))
            self.assertTrue(oracle['schemas'][model['name']]['ok'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            self.assertEqual(document['valid'], oracle['documents'][document['name']]['ok'], document)
            self.assertEqual([], oracle['documents'][document['name']]['warnings'])
            for path in ('dom', 'reader'):
                self.assertEqual(document['valid'], row[path], row)
                if document['valid']:
                    self.assertNotIn(path + '_error', row)
                else:
                    self.assertEqual('PARSE-XML-EXCEPTION', row.get(path + '_error'), row)
        print(f'{mode}: 36 schemas, 684 documents, 1368 native paths', flush=True)


if __name__ == '__main__':
    unittest.main()
