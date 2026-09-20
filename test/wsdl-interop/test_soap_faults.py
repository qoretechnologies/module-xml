#!/usr/bin/env python3
"""SOAP fault grammar. Copyright (C) 2026 Qore Technologies, s.r.o."""
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import unittest
from lxml import etree
from test_soap_envelope import ENV, PEER as SCHEMA_PEER, LocalSchemas, URI
from test_http_request_url import origin
ROOT = Path(__file__).resolve().parent / 'soap-fault-peer'
class SoapFaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for entry in json.loads((SCHEMA_PEER / 'schemas.json').read_text())['schemas']:
            data = (SCHEMA_PEER / entry['path']).read_bytes()
            if len(data) != entry['size'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('changed pinned schema')
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        cls.schema = etree.XMLSchema(etree.fromstring((SCHEMA_PEER / 'soap12.xsd').read_bytes(), parser))
        cls.soap11_schema = etree.XMLSchema(etree.fromstring((SCHEMA_PEER / 'soap11.xsd').read_bytes(), parser))
        cls.soap11_cases = json.loads((ROOT / 'soap11-cases.json').read_text())['cases']
        if len(cls.soap11_cases) != 45 or len({r['name'] for r in cls.soap11_cases}) != 45:
            raise ValueError('missing or duplicate SOAP 1.1 fault cases')
        cls.cases = json.loads((ROOT / 'soap12-cases.json').read_text())['cases']
        if len(cls.cases) != 73 or len({r['name'] for r in cls.cases}) != 73:
            raise ValueError('missing or duplicate fault cases')

    def test_pinned_w3c_schema_oracle(self):
        for row in self.cases:
            with self.subTest(case=row['name']):
                self.assertEqual(row['schema_valid'], self.schema.validate(etree.fromstring(row['xml'].encode())),
                                 str(self.schema.error_log))
        self.assertEqual(26, sum(row['valid'] for row in self.cases))
        # The schema's Body wildcard permits siblings, and xs:anyURI accepts characters SOAP forbids.
        self.assertEqual({'duplicate-Fault','Fault-with-sibling','Node-unescaped-brace','Role-unescaped-brace',
                          'Node-non-ASCII','Role-non-ASCII'},
                         {r['name'] for r in self.cases if r['schema_valid'] != r['valid']})

    def test_soap11_pinned_w3c_schema_oracle(self):
        for row in self.soap11_cases:
            with self.subTest(case=row['name']):
                self.assertEqual(row['schema_valid'], self.soap11_schema.validate(etree.fromstring(row['xml'].encode())),
                                 str(self.soap11_schema.error_log))
        self.assertEqual(21, sum(row['valid'] for row in self.soap11_cases))
        self.assertEqual({'faultstring-xml-lang','faultstring-empty-language','qualified-extension',
                          'qualified-extension-same-local-name','duplicate-Fault','actor-unescaped-brace','actor-non-ASCII'},
                         {r['name'] for r in self.soap11_cases if r['schema_valid'] != r['valid']})

    def test_client_fault_validation_and_recovery(self):
        self.check_client('12', self.cases)

    def test_soap11_client_fault_validation_and_recovery(self):
        self.check_client('11', self.soap11_cases)

    def check_client(self, version, fixtures):
        requests = queue.Queue()
        replies = queue.Queue()
        # End each sequence with a valid fault to verify recovery after negative messages.
        cases = fixtures + [fixtures[0]]
        for _ in range(6):
            for row in cases:
                replies.put(row)
        def reply(request):
            root = etree.fromstring(request['body'])
            self.assertEqual(f"{{{URI[version]}}}Envelope", root.tag)
            self.assertEqual('invoice-71',root.find(f"{{{URI[version]}}}Body/{{urn:soap-envelope-test}}value").text)
            return 500, {}, replies.get_nowait()['xml'].encode()
        with origin('faults', requests, reply, content_type='application/soap+xml' if version == '12' else 'text/xml') as url:
            result = subprocess.run(['qore','-b','--enable-debug',str(ROOT / 'client.qr')],
                input=json.dumps({'url':url,'count':len(cases),'version':version}),capture_output=True,text=True,env=ENV,timeout=90)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertEqual('',result.stderr)
        expected = [{'error':'SOAP-SERVER-FAULT-RESPONSE' if r['valid'] else 'SOAP-DESERIALIZATION-ERROR',
                     'status':500} for r in cases] * 6
        self.assertEqual(expected,json.loads(result.stdout))
        self.assertTrue(replies.empty())
        self.assertEqual(len(expected),requests.qsize())
if __name__ == '__main__':
    unittest.main(verbosity=2)
