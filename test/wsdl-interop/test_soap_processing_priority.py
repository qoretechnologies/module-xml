#!/usr/bin/env python3
"""SOAP mandatory-header fault priority. Copyright (C) 2026 Qore Technologies, s.r.o."""
import http.client
import json
import queue
import subprocess
import unittest
from lxml import etree
from test_cxf_peer import endpoint
from test_http_request_url import origin
from test_soap_http_binding import PEER, ENV, URI, media, envelope
from test_soap_fault_data import qname
import test_soap_oneway


def malformed(version, body):
    return (f'<e:Envelope xmlns:e="{URI[version]}"><e:Header><h:Track xmlns:h="urn:headers"/>'
        '<h:Unknown xmlns:h="urn:headers" e:mustUnderstand="1"/></e:Header><e:Body>'+body+'</e:Body></e:Envelope>').encode()


class SoapProcessingPriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_soap_oneway.OneWayTests.setUpClass()
        cls.schemas = test_soap_oneway.OneWayTests.schemas

    def test_handler_must_understand_precedes_body_errors(self):
        total = 0
        for version in URI:
            bodies = ('<e:Fault/>','<e:Fault/><other xmlns="urn:application"/>','invalid body text')
            for state in ('source','saved','data'):
                for mode in ('native','retained'):
                    with endpoint(['qore','-b','--enable-debug',str(PEER/'handler.qr'),version,state,mode,str(len(bodies))],ENV) as (_,port):
                        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                        try:
                            for body in bodies:
                                connection.request('POST','/service',malformed(version,body),{'Content-Type':media(version)})
                                response=connection.getresponse();raw=response.read();total+=1
                                self.assertEqual(500,response.status,raw)
                                document=etree.fromstring(raw);self.schemas[version].assertValid(document)
                                root='{'+URI[version]+'}'
                                code=document.find(root+'Body/'+root+'Fault/'+(root+'Code/'+root+'Value' if version=='12' else 'faultcode'))
                                self.assertEqual(root+'MustUnderstand',qname(code))
                                connection.request('POST','/service',envelope(version),{'Content-Type':media(version)})
                                response=connection.getresponse();raw=response.read();total+=1;self.assertEqual(200,response.status,raw)
                        finally:connection.close()
        self.assertEqual(72,total)

    def test_client_must_understand_precedes_body_errors(self):
        total=0
        for version in URI:
            rows=[]
            for status in (200,500):
                for body in ('<e:Fault/>','<e:Fault/><other xmlns="urn:application"/>'):
                    rows += [(status,malformed(version,body),'SOAP-MUST-UNDERSTAND'),(200,envelope(version),'OK')]
            rows += [(200,malformed(version,'invalid body text'),'SOAP-MUST-UNDERSTAND'),(200,envelope(version),'OK')]
            responses=queue.Queue();requests=queue.Queue();expected=[]
            for _ in range(6):
                for status,body,error in rows:
                    responses.put((status,{},body));row={'error':error,'status':status,'headers_processed':int(error=='OK')}
                    if error=='OK':row['value']='response'
                    expected.append(row)
            with origin('priority',requests,lambda _:responses.get_nowait(),content_type=media(version)) as url:
                result=subprocess.run(['qore','-b','--enable-debug',str(PEER/'client.qr')],
                    input=json.dumps({'version':version,'url':url,'count':len(rows)}),env=ENV,text=True,capture_output=True,timeout=90)
                self.assertEqual((0,''),(result.returncode,result.stderr),result.stdout)
            self.assertEqual(expected,json.loads(result.stdout));self.assertTrue(responses.empty())
            self.assertEqual(len(expected),requests.qsize());total+=len(expected)
        self.assertEqual(120,total)


if __name__=='__main__':
    unittest.main(verbosity=2)
