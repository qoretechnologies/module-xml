#!/usr/bin/env python3
"""Check contextual XML meanings and schema-authored attributes independently.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from urllib.parse import urljoin

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey
from test_attribute_values import description, NS, XSD
from test_xml_consumers import semantic_nodes

XML = 'http://www.w3.org/XML/1998/namespace'


def inherited_attribute(node, name):
    """Walk actual ancestors, including explicit empty attribute values."""
    while node is not None:
        value = node.get(f'{{{XML}}}{name}')
        if value is not None:
            return value
        node = node.getparent()
    return None


def effective_context(node):
    result = {f'xml:{name}': inherited_attribute(node, name) for name in ('lang', 'space')}
    # libxml2 2.12.10 returns no base for Unicode LEIRIs. Resolve the authored
    # ancestor attributes with Python's independent URI implementation instead.
    lineage = list(node.iterancestors())
    lineage.reverse()
    base = None
    for ancestor in [*lineage, node]:
        value = ancestor.get(f'{{{XML}}}base')
        if value is not None:
            base = urljoin(base, value) if base is not None else value
    result['xml:base'] = base
    return {name: value for name, value in result.items() if value is not None}


class XmlContextTest(unittest.TestCase):
    maxDiff = None

    def test_context_and_schema_validity_in_both_directions(self):
        jobs = []
        with tempfile.TemporaryDirectory(prefix='wsdl-xml-context-') as temporary:
            root = Path(temporary)
            for overrides in (False, True):
                model = 'overridden' if overrides else 'strict'
                attributes = (f'<xs:anyAttribute namespace="{XML}" processContents="skip"/>'
                              if overrides else '')
                source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                    <xs:complexType name="Record"><xs:sequence>
                    <xs:element name="count" type="xs:int"/><xs:element name="flag" type="xs:boolean"/>
                    </xs:sequence><xs:attribute name="label" type="xs:string"/>{attributes}</xs:complexType>
                    <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
                    <xs:element name="Context" type="xs:string"/></xs:schema>'''
                compiled = etree.XMLSchema(etree.fromstring(source.encode()))
                documents = {}
                for version, env_ns in zip(('11', '12'), survey.SOAP_NAMESPACES):
                    wsdl = description(version, source)
                    inputs = []
                    originals = {}
                    for direction, message, element in (('input', 'Request', 'Submit'),
                                                        ('output', 'Response', 'Reply')):
                        wsdl = wsdl.replace(f'<w:part name="body" element="t:{element}"/>',
                            f'<w:part name="body" element="t:{element}"/>'
                            '<w:part name="context" element="t:Context"/>')
                        wsdl = wsdl.replace(f'<w:{direction}><s:body use="literal"/></w:{direction}>',
                            f'<w:{direction}><s:body use="literal" parts="body"/>'
                            f'<s:header message="t:{message}" part="context" use="literal"/></w:{direction}>')
                        own = ' xml:lang="" xml:space="default" xml:base="../rosé/"' if overrides else ''
                        xml = f'''<s:Envelope xmlns:s="{env_ns}" xmlns:t="{NS}"
                            xml:lang="en" xml:space="preserve" xml:base="https://example.org/a/">
                            <s:Header xml:lang="" xml:space="default" xml:base="headers/">
                            <t:Context>account1</t:Context></s:Header>
                            <s:Body xml:lang="cs" xml:base="../orders/">
                            <t:{element}{own} label="before&#9;middle&#10;after&#13;end"><count>009</count>
                            <!--keep--><flag><![CDATA[0]]></flag></t:{element}>
                            </s:Body></s:Envelope>'''
                        path = root / f'{model}-{version}-{direction}.xml'
                        path.write_text(xml)
                        inputs.append(path)
                        originals['request' if direction == 'input' else 'response'] = etree.fromstring(xml.encode())
                    wsdl_path = root / f'{model}-{version}.wsdl'
                    wsdl_path.write_text(wsdl)
                    process = subprocess.run(['qore', '--enable-debug',
                        str(Path(__file__).with_name('xml-consumers.qr')), str(wsdl_path), 'Soap' + version,
                        *(str(path) for path in inputs)], capture_output=True, text=True, timeout=45)
                    self.assertEqual(0, process.returncode, process.stderr)
                    self.assertEqual('', process.stderr)
                    rows = [json.loads(line) for line in process.stdout.splitlines()]
                    self.assertEqual(['request', 'response', 'request', 'response'], [r['direction'] for r in rows])
                    for index, row in enumerate(rows):
                        original = originals[row['direction']]
                        emitted = etree.fromstring(row['body'].encode(), etree.XMLParser(strip_cdata=False))
                        self.assertEqual(f'{{{env_ns}}}Envelope', emitted.tag)
                        for container in ('Body', 'Header'):
                            old_parent = original.find(f'{{{env_ns}}}{container}')
                            new_parent = emitted.find(f'{{{env_ns}}}{container}')
                            old, new = old_parent[0], new_parent[0]
                            # Compare the authored root attributes, XML nodes and effective ancestor context.
                            # A carrier owns its element, not the inter-element tail on its parent.
                            self.assertEqual(semantic_nodes(old)[:-1], semantic_nodes(new)[:-1])
                            self.assertEqual(effective_context(old), effective_context(new))
                            self.assertEqual(effective_context(old_parent), effective_context(new_parent))
                            self.assertTrue(compiled.validate(old), str(compiled.error_log))
                            self.assertTrue(compiled.validate(new), str(compiled.error_log))
                            documents[f'{model}/{version}/{index}/wire/{container}'] = etree.tostring(new)
                            if container == 'Body':
                                carrier_xml = row['parts']['body']
                                reported = row['part_contexts']['body']
                                self.assertIn('<![CDATA[0]]>', carrier_xml)
                                self.assertEqual('009', new.find('count').text)
                                self.assertEqual('before\tmiddle\nafter\rend', new.get('label'))
                                direct = etree.fromstring(row['direct']['body'].encode())
                                self.assertEqual(effective_context(old), effective_context(direct[0]))
                                self.assertEqual(semantic_nodes(old)[:-1], semantic_nodes(direct[0])[:-1])
                                self.assertTrue(compiled.validate(direct[0]), str(compiled.error_log))
                                documents[f'{model}/{version}/{index}/direct'] = etree.tostring(direct[0])
                            else:
                                message = 'Response' if row['direction'] == 'response' else 'Request'
                                carrier_xml = row['headers'][message]['context']
                                reported = row['header_contexts'][message]['context']
                            self.assertEqual(effective_context(old), reported)
                            carrier = etree.fromstring(carrier_xml.encode())
                            self.assertEqual(dict(old.attrib), dict(carrier.attrib))
                            self.assertTrue(compiled.validate(carrier), str(compiled.error_log))
                            documents[f'{model}/{version}/{index}/carrier/{container}'] = carrier_xml.encode()
                jobs.append(SchemaJob(model, f'https://example.invalid/xml-context/{model}.xsd',
                                      source.encode(), documents))
        oracle = run_independent(jobs)
        expected = {name for job in jobs for name in job.documents}
        self.assertEqual(80, len(expected))
        self.assertEqual(expected, set(oracle['documents']))
        self.assertEqual({'strict', 'overridden'}, set(oracle['schemas']))
        for result in oracle['schemas'].values():
            self.assertTrue(result['ok'], result)
        for name, result in oracle['documents'].items():
            self.assertTrue(result['ok'], (name, result))


if __name__ == '__main__':
    unittest.main()
