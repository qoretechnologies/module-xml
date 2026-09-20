#!/usr/bin/env python3
"""SOAP HTTP error identity and encoding. Copyright (C) 2026 Qore Technologies, s.r.o."""
import hashlib
import http.client
import json
from pathlib import Path
import queue
import subprocess
import unittest
from lxml import etree
from test_http_request_url import origin
from test_cxf_peer import endpoint
from test_soap_envelope import ENV, URI, LocalSchemas, PEER as SCHEMA_PEER

ROOT = Path(__file__).resolve().parent / 'soap-fault-peer'


def envelope(version, payload, header=''):
    return f'<s:Envelope xmlns:s="{URI[version]}">{header}<s:Body>{payload}</s:Body></s:Envelope>'


def fault(version):
    content = ('<s:Code><s:Value>s:Receiver</s:Value></s:Code><s:Reason>'
               '<s:Text xml:lang="fr">refusé</s:Text></s:Reason>') if version == '12' else (
               '<faultcode>s:Server</faultcode><faultstring>refusé</faultstring>')
    return envelope(version, '<s:Fault>' + content + '</s:Fault>')


def success(version):
    return envelope(version, '<t:value xmlns:t="urn:soap-envelope-test">réponse</t:value>')


class HttpFaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for row in json.loads((SCHEMA_PEER / 'schemas.json').read_text())['schemas']:
            data = (SCHEMA_PEER / row['path']).read_bytes()
            if row['size'] != len(data) or row['sha256'] != hashlib.sha256(data).hexdigest():
                raise ValueError('changed pinned SOAP schema')
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        cls.schemas = {v: etree.XMLSchema(etree.fromstring((SCHEMA_PEER / f'soap{v}.xsd').read_bytes(), parser)) for v in URI}

    def run_peer(self, version, rows, encoding='utf-8', media=None):
        requests = queue.Queue()
        replies = queue.Queue()
        expected = []
        for _ in range(6):
            for status, xml, error in rows:
                replies.put((status, {}, xml.encode(encoding)))
                result = {'error': error, 'status': status}
                if error == 'OK':
                    result['value'] = 'réponse'
                elif error == 'SOAP-SERVER-FAULT-RESPONSE':
                    result['accent'] = True
                elif error == 'HTTP-CLIENT-RECEIVE-ERROR':
                    result['original_status'] = status
                expected.append(result)
        def response(request):
            root = etree.fromstring(request['body'])
            self.assertEqual(f'{{{URI[version]}}}Envelope', root.tag)
            self.assertEqual('invoice-71', root.find(f'{{{URI[version]}}}Body/{{urn:soap-envelope-test}}value').text)
            return replies.get_nowait()
        content_type = media or (('application/soap+xml' if version == '12' else 'text/xml') + f';charset="{encoding}"')
        with origin('soap-http-fault', requests, response, content_type=content_type) as url:
            result = subprocess.run(['qore','-b','--enable-debug',str(ROOT/'http-client.qr')],
                input=json.dumps({'url':url,'version':version,'count':len(rows)}),text=True,
                capture_output=True,env=ENV,timeout=90)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertEqual('',result.stderr)
        self.assertEqual(expected,json.loads(result.stdout),(version,encoding,content_type))
        self.assertTrue(replies.empty())
        self.assertEqual(len(expected),requests.qsize())
        return len(expected)

    def test_charset_faults_and_recovery(self):
        count = 0
        for version in URI:
            xml = fault(version)
            variants = [xml,xml.replace('Fault>','Fault >'),
                        xml.replace('<s:Fault>','<f:Fault xmlns:f="'+URI[version]+'">').replace('</s:Fault>','</f:Fault>')]
            for variant in variants:
                self.schemas[version].assertValid(etree.fromstring(variant.encode()))
            for encoding in ('utf-8','utf-16','utf-16le','utf-16be','iso-8859-1'):
                rows = []
                for status in (200,400,500,503):
                    for variant in variants:
                        rows.extend([(status,variant,'SOAP-SERVER-FAULT-RESPONSE'),(200,success(version),'OK')])
                count += self.run_peer(version,rows,encoding)
        self.assertEqual(1440,count)

    def test_nonfault_transport_errors_and_recovery(self):
        count = 0
        for version in URI:
            variants = [success(version),envelope(version,'<t:Fault xmlns:t="urn:application">failed</t:Fault>'),
                        envelope(version,'<s:Fault xmlns:s="urn:application">failed</s:Fault>'),
                        envelope(version,'<s:fault/>'),
                        envelope(version,'<t:value xmlns:t="urn:soap-envelope-test"><![CDATA[<Fault>]]></t:value>'),
                        envelope(version,'<!-- <s:Fault> --><t:value xmlns:t="urn:soap-envelope-test">value</t:value>'),
                        envelope(version,'<t:value xmlns:t="urn:soap-envelope-test">value</t:value>',
                                 '<s:Header><s:Fault>application header</s:Fault></s:Header>'),
                        fault(version).replace('<s:Body>','<x:Body xmlns:x="urn:application">').replace('</s:Body>','</x:Body>'),
                        '<html><Fault>Gateway unavailable</Fault></html>']
            rows=[]
            for xml in variants:
                root = etree.fromstring(xml.encode())
                self.assertIsNone(root.find(f'{{{URI[version]}}}Body/{{{URI[version]}}}Fault'))
                rows.extend([(500,xml,'HTTP-CLIENT-RECEIVE-ERROR'),(200,success(version),'OK')])
            rows.extend([(404,fault(version),'HTTP-CLIENT-RECEIVE-ERROR'),(200,success(version),'OK'),
                         (500,'<broken>','PARSE-XML-EXCEPTION'),(200,success(version),'OK'),
                         (500,fault(version).replace('<s:Body>','<s:Body/><s:Header/><s:Body>'),
                          'SOAP-DESERIALIZATION-ERROR'),(200,success(version),'OK'),
                         (500,'<!DOCTYPE s:Envelope>'+fault(version),'SOAP-DESERIALIZATION-ERROR'),(200,success(version),'OK')])
            count += self.run_peer(version,rows)
            count += self.run_peer(version,[(500,fault(version),'HTTP-CLIENT-RECEIVE-ERROR'),
                                           (500,'Gateway unavailable','HTTP-CLIENT-RECEIVE-ERROR')],media='text/plain')
        self.assertEqual(336,count)

    def test_handler_request_charsets(self):
        count = 0
        for version in URI:
            for state in ('source','saved','data'):
                command = ['qore','-b','--enable-debug',str(SCHEMA_PEER/'peer.qr'),'server',version,state,'5']
                with endpoint(command,ENV) as (_,port):
                    connection = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                    self.addCleanup(connection.close)
                    for encoding in ('utf-8','utf-16','utf-16le','utf-16be','iso-8859-1'):
                        xml = success(version).replace('réponse','invoice-71')
                        connection.request('POST','/service',xml.encode(encoding),{'Content-Type':
                            ('application/soap+xml' if version == '12' else 'text/xml')+f';charset="{encoding}"'})
                        response = connection.getresponse()
                        output = response.read()
                        self.assertEqual(200,response.status,output)
                        root = etree.fromstring(output)
                        self.schemas[version].assertValid(root)
                        self.assertEqual('invoice-71',root.find(f'{{{URI[version]}}}Body/{{urn:soap-envelope-test}}value').text)
                        count += 1
                    connection.close()
        self.assertEqual(30,count)


if __name__ == '__main__':
    unittest.main(verbosity=2)
