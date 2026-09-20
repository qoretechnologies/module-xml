#!/usr/bin/env python3
"""SOAP 1.2 response MEP. Copyright (C) 2026 Qore Technologies, s.r.o."""
import http.client
import json
from pathlib import Path
import queue
import subprocess
import unittest
from lxml import etree
from test_cxf_peer import endpoint
from test_http_request_url import origin
from test_soap_envelope import ENV, URI
from test_soap_http_binding import envelope
import test_soap_oneway

PEER = Path(__file__).resolve().parent / 'soap-response-peer'
MEDIA = 'application/soap+xml'


def client(job):
    result = subprocess.run(['qore','-b','--enable-debug',str(PEER/'client.qr')],
        input=json.dumps(job),env=ENV,text=True,capture_output=True,timeout=120)
    if result.returncode or result.stderr:
        raise AssertionError((result.returncode,result.stdout,result.stderr))
    return json.loads(result.stdout)


def fault():
    return (f'<e:Envelope xmlns:e="{URI["12"]}"><e:Body><e:Fault><e:Code><e:Value>e:Receiver</e:Value>'
        '</e:Code><e:Reason><e:Text xml:lang="en">invoice unavailable</e:Text></e:Reason>'
        '</e:Fault></e:Body></e:Envelope>').encode()


class SoapResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_soap_oneway.OneWayTests.setUpClass()
        cls.schema = test_soap_oneway.OneWayTests.schemas['12']

    def test_client_wire_and_response_processing(self):
        body = envelope('12')
        rows = [(200,MEDIA,body,'OK',1), (200,'text/plain',body,'SOAP-MEDIA-TYPE-ERROR',0),
            (200,MEDIA+';charset=unknown-qore-test',body,'SOAP-MEDIA-TYPE-ERROR',0),
            (200,MEDIA,envelope('11'),'SOAP-VERSION-MISMATCH',0),
            (200,MEDIA,body.replace(b'<h:Track ',b'<h:Unknown s:mustUnderstand="true" '),'SOAP-MUST-UNDERSTAND',0),
            (404,'text/plain',b'missing','HTTP-CLIENT-RECEIVE-ERROR',0)]
        rows += [(status,MEDIA,fault(),'SOAP-SERVER-FAULT-RESPONSE',0) for status in (200,400,500)]
        rows = [item for row in rows for item in (row,(200,MEDIA,body,'OK',1))]
        responses = queue.Queue(); requests = queue.Queue(); expected = []
        for _ in range(6):
            for status,ct,payload,error,processed in rows:
                responses.put((status,{'Content-Type':ct},payload))
                value = {'error':error,'status':status,'headers_processed':processed,'request_body':False}
                if error == 'OK': value['value'] = 'response'
                expected.append(value)
        with origin('resource',requests,lambda _:responses.get_nowait(),content_type=None) as url:
            actual = client({'url':url+'/endpoint','entity_defaults':True,
                'calls':[{'path':'/invoices/71?revision=2'} for _ in rows]})
        self.assertEqual(expected,actual)
        self.assertTrue(responses.empty()); self.assertEqual(len(expected),requests.qsize())
        while not requests.empty():
            r = requests.get_nowait()
            self.assertEqual(('GET','/invoices/71?revision=2',b''),(r['method'],r['path'],r['body']))
            self.assertEqual(MEDIA,r['headers']['accept'])
            self.assertFalse([h for h in r['headers'] if h.startswith('content-') or h in ('soapaction','transfer-encoding','trailer')],r)

    def test_client_request_local_urls_origins_redirects_and_post(self):
        requests = queue.Queue()
        def response(record):
            if record['path'] == '/redirect': return (302,{'Location':'/invoices/71'},b'')
            return (200,{},envelope('12'))
        with origin('A',requests,response,content_type=MEDIA) as a, origin('B',requests,response,content_type=MEDIA) as b:
            calls = [{'path':p} for p in ('../invoices/71','?revision=2','','/café','/invoice%2F71',b+'/invoices/71','/redirect')]
            calls += [{'path':b+'/explicit','opts':{'http_header':{'Authorization':'Bearer explicit-test','Cookie':'explicit=1'}}}, {'post':True}]
            actual = client({'url':a+'/base/endpoint','headers':{'Authorization':'Bearer default-test','Cookie':'default=1'},'calls':calls})
        self.assertTrue(all(r['error']=='OK' and r['headers_processed']==1 for r in actual),actual)
        for _ in range(6):
            for path,where,explicit in [('/invoices/71','A',False),('/base/endpoint?revision=2','A',False),
                    ('/base/endpoint','A',False),('/caf%C3%A9','A',False),('/invoice%2F71','A',False),
                    ('/invoices/71','B',False),('/redirect','A',False),('/invoices/71','A',False),
                    ('/explicit','B',True),('/base/endpoint','A',False)]:
                r=requests.get_nowait();self.assertEqual((where,path),(r['origin'],r['path']))
                self.assertEqual(('Bearer explicit-test' if explicit else 'Bearer default-test' if where=='A' else None),r['headers'].get('authorization'))
                self.assertEqual(('explicit=1' if explicit else 'default=1' if where=='A' else None),r['headers'].get('cookie'))
                self.assertEqual('POST' if path=='/base/endpoint' and r['body'] else 'GET',r['method'])
            self.assertTrue(actual[_*len(calls)+len(calls)-1]['request_body'])
        self.assertTrue(requests.empty())

    def test_handler_safe_resources_and_post_coexist(self):
        for state in ('source','saved','data'):
            for mode in ('native','retained'):
                for mount in ('default','mount'):
                    prefix='/mount' if mount=='mount' else ''
                    with endpoint(['qore','-b','--enable-debug',str(PEER/'handler.qr'),state,mode,mount,'7'],ENV) as (_,port):
                        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                        try:
                            rows=[('GET','/service?revision=2',None,200),('GET','/invoice%2F71',None,200),
                                ('GET','/caf%C3%A9',None,200),('GET','/',None,200),('GET','/service?error',None,500),
                                ('GET','/service',b'unexpected',400),('HEAD','/service',None,405),
                                ('PUT','/service',None,405),('GET','/service/child',None,405),
                                ('GET','/service?wsdl',None,200),('POST','/service',envelope('12'),200),
                                ('GET','/service',None,200),('GET','/service?remove',None,200),('GET','/service',None,405)]
                            for verb,path,body,status in rows:
                                connection.request(verb,prefix+path,body,{'Content-Type':MEDIA} if verb=='POST' else {})
                                response=connection.getresponse();raw=response.read()
                                self.assertEqual(status,response.status,(state,mode,mount,verb,path,raw))
                                if path.endswith('?wsdl'):
                                    self.assertEqual('{http://schemas.xmlsoap.org/wsdl/}definitions',etree.fromstring(raw).tag)
                                elif status in (200,500):
                                    document=etree.fromstring(raw);self.schema.assertValid(document)
                                    self.assertTrue(response.getheader('Content-Type').startswith(MEDIA))
                                    if status==200:
                                        self.assertEqual('response',document.find('{'+URI['12']+'}Body/{urn:soap-envelope-test}value').text)
                                    else:self.assertIn(b'RESOURCE-ERROR',raw)
                                elif status==405:
                                    self.assertEqual('POST' if verb=='GET' else 'GET, POST',response.getheader('Allow'))
                        finally:connection.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
