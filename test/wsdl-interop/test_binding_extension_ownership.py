#!/usr/bin/env python3
"""Independently assess protocol ownership apart from extension XSD grammar.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from independent import SchemaJob, run

ROOT = Path(__file__).resolve().parent
WSDL = 'http://schemas.xmlsoap.org/wsdl/'
SOAP = {WSDL + 'soap/', WSDL + 'soap12/'}
HTTP = WSDL + 'http/'


def protocol_owners_match(source):
    root = ET.fromstring(source)
    for binding in root.findall(f'{{{WSDL}}}binding'):
        protocols = [child for child in binding
                     if child.tag in {f'{{{ns}}}binding' for ns in SOAP | {HTTP}}]
        if len(protocols) != 1:
            return False
        namespace = protocols[0].tag[1:].split('}')[0]
        for operation in binding.findall(f'{{{WSDL}}}operation'):
            declarations = [child for child in operation
                            if child.tag in {f'{{{ns}}}operation' for ns in SOAP | {HTTP}}]
            if len(declarations) > 1 or any(child.tag != f'{{{namespace}}}operation'
                                            for child in declarations):
                return False
            for direction in ('input', 'output'):
                for message in operation.findall(f'{{{WSDL}}}{direction}'):
                    if any(child.tag.startswith(f'{{{ns}}}') and ns != namespace
                           for child in message for ns in SOAP | {HTTP}):
                        return False
                    formats = [child for child in message
                               if child.tag in {f'{{{ns}}}body' for ns in SOAP}
                               or child.tag in {f'{{{HTTP}}}urlEncoded', f'{{{HTTP}}}urlReplacement'}]
                    if namespace == HTTP:
                        allowed = ({f'{{{HTTP}}}urlEncoded', f'{{{HTTP}}}urlReplacement'}
                                   if direction == 'input' else set())
                    else:
                        allowed = {f'{{{namespace}}}body'}
                    if len(formats) > 1 or any(child.tag not in allowed for child in formats):
                        return False
    return True


class BindingOwnershipTest(unittest.TestCase):
    def test_namespaces_and_schema(self):
        rows = json.loads((ROOT / 'regressions/wsdl-binding-extension-ownership/cases.json').read_text())['cases']
        self.assertEqual(65, len(rows))
        self.assertEqual(24, sum(row['valid'] for row in rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        resources = {}
        imports = []
        core = ROOT / 'regressions/wsdl-grammar'
        manifest = json.loads((core / 'cases.json').read_text())
        content = (core / manifest['schema_file']).read_bytes()
        self.assertEqual(manifest['schema_sha256'], hashlib.sha256(content).hexdigest())
        resources['urn:wsdl:core'] = content
        imports.append(f'<xs:import namespace="{WSDL}" schemaLocation="urn:wsdl:core"/>')
        namespaces = {'soap11.xsd': WSDL + 'soap/', 'soap12.xsd': WSDL + 'soap12/',
                      'http.xsd': HTTP, 'mime.xsd': WSDL + 'mime/'}
        for directory in ('wsdl-soap-grammar', 'wsdl-http-mime-grammar'):
            path = ROOT / 'regressions' / directory
            manifest = json.loads((path / 'cases.json').read_text())
            for source in manifest['schemas']:
                content = (path / source['file']).read_bytes()
                self.assertEqual(source['sha256'], hashlib.sha256(content).hexdigest())
                resources[source['url']] = content
                imports.append(f'<xs:import namespace="{namespaces[source["file"]]}" '
                               f'schemaLocation="{source["url"]}"/>')
        schema = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                  + ''.join(imports) + '</xs:schema>').encode()
        report = run([SchemaJob('ownership', 'urn:ownership:schema', schema,
                               {row['name']: row['xml'].encode() for row in rows})], resources)
        self.assertTrue(report['schemas']['ownership']['ok'], report['schemas'])
        self.assertEqual([], report['schemas']['ownership']['warnings'])
        for row in rows:
            with self.subTest(case=row['name']):
                self.assertEqual(row['valid'], protocol_owners_match(row['xml']))
                # The extension schemas validate individual declarations; they do
                # not express binding-wide protocol ownership or cardinality.
                actual = report['documents'][row['name']]
                self.assertTrue(actual['ok'], actual)
                self.assertEqual([], actual['warnings'])


if __name__ == '__main__':
    unittest.main()
