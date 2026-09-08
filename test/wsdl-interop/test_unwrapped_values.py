#!/usr/bin/env python3
"""Independent XML checks for unwrapped SOAP document arguments.

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

BASE = 'https://example.invalid/unwrapped-values/'


class UnwrappedValuesTest(unittest.TestCase):
    def test_document_values_and_header_separation(self):
        choice = '<xs:choice><xs:element name="flag" type="xs:boolean"/><xs:element name="other" type="xs:string"/></xs:choice>'
        models = {
            'wildcard': '<xs:sequence><xs:any processContents="skip" maxOccurs="unbounded"/></xs:sequence>',
            'choice': '<xs:sequence>' + choice + '</xs:sequence>',
            'sequence': '<xs:sequence><xs:element name="count" type="xs:int"/>' + choice + '</xs:sequence>',
        }
        models['header'] = models['wildcard']
        jobs = []
        with tempfile.TemporaryDirectory(prefix='wsdl-unwrapped-values-') as temporary:
            root = Path(temporary)
            for model, content in models.items():
                source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                    <xs:complexType name="Record">{content}</xs:complexType>
                    <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
                    <xs:element name="Context" type="xs:string"/></xs:schema>'''
                compiled = etree.XMLSchema(etree.fromstring(source.encode()))
                documents = {}
                for version, envelope_ns in zip(('11', '12'), survey.SOAP_NAMESPACES):
                    text = description(version, source)
                    if model == 'header':
                        text = text.replace('<w:part name="body" element="t:Submit"/>',
                            '<w:part name="body" element="t:Submit"/><w:part name="context" element="t:Context"/>')
                        text = text.replace('<w:part name="body" element="t:Reply"/>',
                            '<w:part name="body" element="t:Reply"/><w:part name="context" element="t:Context"/>')
                        for direction, message in (('input', 'Request'), ('output', 'Response')):
                            text = text.replace(f'<w:{direction}><s:body use="literal"/></w:{direction}>',
                                f'<w:{direction}><s:body use="literal" parts="body"/>'
                                f'<s:header message="t:{message}" part="context" use="literal"/></w:{direction}>')
                    path = root / f'{model}-{version}.wsdl'
                    path.write_text(text)
                    process = subprocess.run(['qore', '--enable-debug',
                        str(Path(__file__).with_name('unwrapped-values.qr')), str(path), 'Soap' + version, model],
                        text=True, capture_output=True, timeout=30)
                    self.assertEqual(0, process.returncode, process.stderr)
                    self.assertEqual('', process.stderr)
                    rows = [json.loads(line) for line in process.stdout.splitlines()]
                    self.assertEqual({(d, m) for d in ('request', 'response') for m in ('bare', 'wrapped', 'message')},
                                     {(r['direction'], r['mode']) for r in rows})
                    self.assertEqual(6, len(rows))
                    bodies = {}
                    for row in rows:
                        envelope = etree.fromstring(row['body'].encode())
                        self.assertEqual(f'{{{envelope_ns}}}Envelope', envelope.tag)
                        body = envelope.find(f'{{{envelope_ns}}}Body')
                        self.assertEqual(1, len(body))
                        payload = body[0]
                        wrapper = 'Submit' if row['direction'] == 'request' else 'Reply'
                        self.assertEqual(f'{{{NS}}}{wrapper}', payload.tag)
                        self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                        fields = [(child.tag, child.text) for child in payload]
                        expected = ([('{urn:first}item', '0'), ('{urn:second}item', 'false'), ('empty', None)]
                                    if model in ('wildcard', 'header') else
                                    ([('count', '0')] if model == 'sequence' else []) + [('flag', 'false')])
                        self.assertEqual(expected, fields)
                        bodies[row['direction'], row['mode']] = fields
                        name = f"{model}/{version}/{row['direction']}/{row['mode']}"
                        documents[name] = etree.tostring(payload)
                        header = envelope.find(f'{{{envelope_ns}}}Header')
                        if model == 'header':
                            self.assertIsNotNone(header)
                            self.assertEqual(1, len(header))
                            self.assertEqual(f'{{{NS}}}Context', header[0].tag)
                            self.assertEqual('account1', header[0].text)
                            self.assertTrue(compiled.validate(header[0]), str(compiled.error_log))
                            documents[name + '/header'] = etree.tostring(header[0])
                        else:
                            self.assertIsNone(header)
                    for direction in ('request', 'response'):
                        self.assertEqual(bodies[direction, 'wrapped'], bodies[direction, 'bare'])
                        self.assertEqual(bodies[direction, 'wrapped'], bodies[direction, 'message'])
                jobs.append(SchemaJob(model, BASE + model + '.xsd', source.encode(), documents))
        oracle = run_independent(jobs)
        expected_documents = {name for job in jobs for name in job.documents}
        self.assertEqual(60, len(expected_documents))
        self.assertEqual(expected_documents, set(oracle['documents']))
        self.assertEqual(set(models), set(oracle['schemas']))
        for result in oracle['schemas'].values():
            self.assertTrue(result['ok'], result)
        for name, result in oracle['documents'].items():
            self.assertTrue(result['ok'], (name, result))


if __name__ == '__main__':
    unittest.main()
