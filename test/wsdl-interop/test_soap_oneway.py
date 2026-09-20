#!/usr/bin/env python3
"""SOAP one-way response interoperability. Copyright (C) 2026 Qore Technologies, s.r.o."""
import hashlib
import http.client
import json
from pathlib import Path
import queue
import subprocess
import unittest
from lxml import etree
from test_cxf_peer import endpoint
from test_http_request_url import origin
from test_soap_envelope import ENV, URI, LocalSchemas, PEER as SCHEMA_PEER
from test_soap_http_faults import envelope, fault, success
from test_soap_fault_data import qname
ROOT = Path(__file__).resolve().parent / 'soap-fault-peer'


def header(name='Received'):
    return f'<e:Header xmlns:e="PLACEHOLDER"><a:{name} xmlns:a="urn:ack" e:mustUnderstand="1">invoice-71</a:{name}></e:Header>'


class OneWayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for row in json.loads((SCHEMA_PEER / 'schemas.json').read_text())['schemas']:
            data = (SCHEMA_PEER / row['path']).read_bytes()
            if row['size'] != len(data) or row['sha256'] != hashlib.sha256(data).hexdigest():
                raise ValueError('changed pinned SOAP schema')
        parser = etree.XMLParser(no_network=True,resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        cls.schemas = {v:etree.XMLSchema(etree.fromstring((SCHEMA_PEER/f'soap{v}.xsd').read_bytes(),parser)) for v in URI}

    def test_client_empty_acknowledgments_and_protocol_envelopes(self):
        count = 0
        for version in URI:
            known = envelope(version,' \n',header().replace('PLACEHOLDER',URI[version]))
            unknown = envelope(version,'',header('Unknown').replace('PLACEHOLDER',URI[version]))
            self.schemas[version].assertValid(etree.fromstring(known.encode()))
            self.schemas[version].assertValid(etree.fromstring(fault(version).encode()))
            rows = [(status,'','OK',False) for status in (200,202,204)]
            rows += [(status,known,'OK',True) for status in (200,202)]
            for status,xml,error in [(500,fault(version),'SOAP-SERVER-FAULT-RESPONSE'),
                    (400,fault(version),'SOAP-SERVER-FAULT-RESPONSE'),
                    (200,unknown,'SOAP-MUST-UNDERSTAND'),
                    (200,success(version),'SOAP-DESERIALIZATION-ERROR'),
                    (500,fault(version).replace('refusé','<invalid/>'),'SOAP-DESERIALIZATION-ERROR')]:
                rows.extend([(status,xml,error,False),(202,'','OK',False)])
            self.assertEqual(15,len(rows))
            requests = queue.Queue(); replies = queue.Queue(); expected = []
            for _ in range(6):
                for status,xml,error,ack in rows:
                    replies.put((status,{},xml.encode()))
                    result = {'error':error,'status':status}
                    if error == 'OK':
                        result['value_is_nothing'] = True
                    if ack:
                        result['ack'] = 'acknowledged'
                    expected.append(result)
            def response(request):
                root = etree.fromstring(request['body'])
                self.assertEqual('invoice-71',root.find(f'{{{URI[version]}}}Body/{{urn:soap-envelope-test}}value').text)
                return replies.get_nowait()
            with origin('oneway',requests,response,content_type='application/soap+xml' if version == '12' else 'text/xml') as url:
                result = subprocess.run(['qore','-b','--enable-debug',str(ROOT/'oneway-client.qr')],
                    input=json.dumps({'url':url,'version':version,'count':len(rows)}),capture_output=True,text=True,env=ENV,timeout=90)
                self.assertEqual(0,result.returncode,result.stdout+result.stderr)
                self.assertEqual('',result.stderr)
            self.assertEqual(expected,json.loads(result.stdout))
            self.assertTrue(replies.empty()); self.assertEqual(len(expected),requests.qsize())
            count += len(expected)
        self.assertEqual(180,count)

    def test_handler_empty_status_and_faults(self):
        count = 0
        for version in URI:
            for state in ('source','saved','data'):
                for retained in ('native','retained'):
                    command = ['qore','-b','--enable-debug',str(ROOT/'oneway-handler.qr'),version,state,retained,'3']
                    with endpoint(command,ENV) as (_,port):
                        connection = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                        self.addCleanup(connection.close)
                        rows = [('invoice-71',False,202),('error',False,500),('invoice-71',True,500),('invoice-71',False,202)]
                        for value,unknown,status in rows:
                            payload = f'<t:value xmlns:t="urn:soap-envelope-test">{value}</t:value>'
                            xml = envelope(version,payload,header('Unknown').replace('PLACEHOLDER',URI[version]) if unknown else '')
                            connection.request('POST','/service',xml.encode(),{'Content-Type':
                                'application/soap+xml' if version == '12' else 'text/xml'})
                            response = connection.getresponse(); data = response.read()
                            self.assertEqual(status,response.status,data)
                            if status == 202:
                                self.assertEqual(b'',data)
                                self.assertIsNone(response.getheader('Content-Type'))
                                self.assertEqual('0',response.getheader('Content-Length'))
                            else:
                                root = etree.fromstring(data); self.schemas[version].assertValid(root)
                                env = f'{{{URI[version]}}}'
                                code = root.find(env+'Body/'+env+'Fault/'+(env+'Code/'+env+'Value' if version == '12' else 'faultcode'))
                                self.assertEqual(env+('MustUnderstand' if unknown else ('Receiver' if version == '12' else 'Server')),qname(code))
                            count += 1
                        connection.close()
        self.assertEqual(48,count)


if __name__ == '__main__':
    unittest.main(verbosity=2)
