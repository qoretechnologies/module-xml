#!/usr/bin/env python3
"""Independent checks of retained SOAP XML and every schema consumer.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey
from test_attribute_values import description, NS, XSD

BASE = 'https://example.invalid/xml-consumers/'


def semantic_nodes(node):
    """Compare names, attributes and all text/tails, independently of prefix choice."""
    if isinstance(node, etree._Comment):
        return ('comment', node.text, node.tail)
    return (node.tag, dict(node.attrib), node.text,
            tuple(semantic_nodes(child) for child in node), node.tail)


class XmlConsumersTest(unittest.TestCase):
    maxDiff = None

    def test_retained_parts_headers_providers_and_examples(self):
        models = {
            'record': '<xs:sequence><xs:element name="count" type="xs:int"/>'
                      '<xs:element name="flag" type="xs:boolean"/></xs:sequence>',
            'wildcard': '<xs:sequence><xs:any processContents="skip" maxOccurs="unbounded"/></xs:sequence>',
        }
        contents = {
            'record': '<count>009</count><!--between--><flag><![CDATA[0]]></flag>',
            'wildcard': '<p:item xmlns:p="urn:first" kind="q:Item">before<plain xmlns="">0</plain>after'
                        '<![CDATA[ mixed ]]><!--keep--></p:item><p:item xmlns:p="urn:second">tail</p:item>',
        }
        jobs = []
        invalid_examples = []
        with tempfile.TemporaryDirectory(prefix='wsdl-xml-consumers-') as temporary:
            root = Path(temporary)
            for model, content in models.items():
                source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                    <xs:complexType name="Record">{content}</xs:complexType>
                    <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
                    <xs:element name="Context" type="xs:string"/></xs:schema>'''
                compiled = etree.XMLSchema(etree.fromstring(source.encode()))
                documents = {}
                for version, env_ns in zip(('11', '12'), survey.SOAP_NAMESPACES):
                    for location in ('body', 'header'):
                        wsdl = description(version, source)
                        inputs = []
                        originals = {}
                        for direction, message, element in (('input', 'Request', 'Submit'),
                                                            ('output', 'Response', 'Reply')):
                            wsdl = wsdl.replace(f'<w:part name="body" element="t:{element}"/>',
                                f'<w:part name="body" element="t:{element}"/>'
                                '<w:part name="context" element="t:Context"/>')
                            if location == 'header':
                                wsdl = wsdl.replace(f'<w:{direction}><s:body use="literal"/></w:{direction}>',
                                    f'<w:{direction}><s:body use="literal" parts="body"/>'
                                    f'<s:header message="t:{message}" part="context" use="literal"/></w:{direction}>')
                            context = '<t:Context>q:Account</t:Context>'
                            xml = f'<s:Envelope xmlns:s="{env_ns}" xmlns:t="{NS}" xmlns:q="urn:types">'
                            if location == 'header':
                                xml += f'<s:Header>{context}</s:Header>'
                            xml += f'<s:Body><t:{element}>{contents[model]}</t:{element}>'
                            xml += (context if location == 'body' else '') + '</s:Body></s:Envelope>'
                            path = root / f'{model}-{version}-{location}-{direction}.xml'
                            path.write_text(xml)
                            inputs.append(path)
                            original = etree.fromstring(xml.encode())
                            originals['request' if direction == 'input' else 'response'] = original
                            for payload in original.findall(f'{{{env_ns}}}Body/*'):
                                self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                        wsdl_path = root / f'{model}-{version}-{location}.wsdl'
                        wsdl_path.write_text(wsdl)
                        process = subprocess.run(['qore', '--enable-debug',
                            str(Path(__file__).with_name('xml-consumers.qr')), str(wsdl_path), 'Soap' + version,
                            *(str(path) for path in inputs)], capture_output=True, text=True, timeout=45)
                        self.assertEqual(0, process.returncode, process.stderr)
                        self.assertEqual('', process.stderr)
                        rows = [json.loads(line) for line in process.stdout.splitlines()]
                        self.assertEqual(['request', 'response', 'request', 'response'], [r['direction'] for r in rows])
                        for index, row in enumerate(rows):
                            key = f'{model}/{version}/{location}/{index}'
                            original = originals[row['direction']]
                            emitted = etree.fromstring(row['body'].encode())
                            self.assertEqual(f'{{{env_ns}}}Envelope', emitted.tag)
                            for container in ('Body', 'Header'):
                                old = original.find(f'{{{env_ns}}}{container}')
                                new = emitted.find(f'{{{env_ns}}}{container}')
                                if old is None:
                                    self.assertIsNone(new)
                                else:
                                    self.assertEqual([semantic_nodes(n) for n in old],
                                                     [semantic_nodes(n) for n in new])
                                    for number, node in enumerate(new):
                                        self.assertTrue(compiled.validate(node), str(compiled.error_log))
                                        documents[f'{key}/wire/{container}/{number}'] = etree.tostring(node)
                            parts = dict(row['parts'])
                            for headers in row['headers'].values():
                                parts.update(headers)
                            self.assertEqual({'body', 'context'}, set(parts))
                            for part, xml in parts.items():
                                node = etree.fromstring(xml.encode())
                                self.assertEqual('urn:types', node.nsmap['q'])
                                self.assertTrue(compiled.validate(node), str(compiled.error_log))
                                documents[f'{key}/retained/{part}'] = xml.encode()
                            if model == 'record':
                                node = etree.fromstring(parts['body'].encode())
                                self.assertEqual('009', node.find('count').text)
                                self.assertEqual('0', node.find('flag').text)
                                self.assertIn('<![CDATA[0]]>', parts['body'])
                            else:
                                node = etree.fromstring(parts['body'].encode())
                                self.assertEqual(['{urn:first}item', '{urn:second}item'], [c.tag for c in node])
                                self.assertEqual('q:Item', node[0].get('kind'))
                                self.assertEqual('urn:types', node[0].nsmap['q'])
                                self.assertIn('<![CDATA[ mixed ]]>', parts['body'])
                            example = etree.fromstring(row['example'].encode())
                            self.assertEqual(f'{{{env_ns}}}Envelope', example.tag)
                            example_parts = example.findall(f'{{{env_ns}}}Body/*') + example.findall(f'{{{env_ns}}}Header/*')
                            self.assertEqual(2, len(example_parts))
                            for number, node in enumerate(example_parts):
                                name = f'{key}/example/{number}'
                                if not compiled.validate(node):
                                    invalid_examples.append((name, str(compiled.error_log)))
                                documents[name] = etree.tostring(node)
                jobs.append(SchemaJob(model, BASE + model + '.xsd', source.encode(), documents))
        oracle = run_independent(jobs)
        expected = {name for job in jobs for name in job.documents}
        self.assertEqual(192, len(expected))
        self.assertEqual(expected, set(oracle['documents']))
        self.assertEqual(set(models), set(oracle['schemas']))
        for result in oracle['schemas'].values():
            self.assertTrue(result['ok'], result)
        rejected = [(name, result) for name, result in oracle['documents'].items() if not result['ok']]
        # Complete both independent validator passes before reporting failures. Required wildcard
        # examples are an existing native WSMessageHelper gap owned by P5; they remain failing checks.
        self.assertEqual(([], []), ([name for name, _ in invalid_examples], [name for name, _ in rejected]))


if __name__ == '__main__':
    unittest.main()
