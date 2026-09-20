#!/usr/bin/env python3
"""SOAP HTTP media boundaries. Copyright (C) 2026 Qore Technologies, s.r.o."""
import http.client
import json
from pathlib import Path
import queue
import subprocess
import unittest
from lxml import etree
from test_cxf_peer import endpoint
from test_http_request_url import origin, contract, PEER as HTTP_PEER
from test_soap_actions import multipart
from test_soap_envelope import ENV, URI
import test_soap_oneway

PEER = Path(__file__).resolve().parent / 'soap-http-binding-peer'


def envelope(version):
    return (f'<s:Envelope xmlns:s="{URI[version]}"><s:Header><h:Track xmlns:h="urn:headers"/>'
            '</s:Header><s:Body><t:value xmlns:t="urn:soap-envelope-test">response</t:value></s:Body></s:Envelope>').encode()


def media(version):
    return 'application/soap+xml' if version == '12' else 'text/xml'


class SoapHttpBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_soap_oneway.OneWayTests.setUpClass()
        cls.schemas = test_soap_oneway.OneWayTests.schemas

    def test_handler_media_methods_and_recovery(self):
        total = 0
        for version in URI:
            body = envelope(version)
            rows = [('POST', ct, body, 200) for ct in ('text/xml', 'application/xml', media(version),
                media(version).upper()+';CHARSET="UTF-8"')]
            rows += [('POST', media(version)+';charset=UTF-16', body.decode().encode('utf-16'), 200)]
            ct, parts = multipart(media(version), body)
            rows += [('POST', ct, parts, 200)]
            ct, parts = multipart('application/xop+xml;type="'+media(version)+'"', body)
            rows += [('POST', ct, parts, 200)]
            for ct in (None, 'text/plain', 'application/json', 'application/octet-stream',
                    'application/vendor+xml', 'multipart/mixed;boundary="x"',
                    'application/xop+xml;type="application/json"',media(version)+';charset=unknown-qore-test'):
                rows.append(('POST', ct, body, 415))
            for ct in ('broken;type', 'text/xml;charset', 'text/xml;charset=UTF-8;charset=ISO-8859-1',
                    'application/xop+xml', 'application/xop+xml;type=broken', 'text/xml;charset=""',
                    'multipart/related;boundary="x";type="text/xml"'):
                rows.append(('POST', ct, body, 400))
            ct, parts = multipart('application/json', body)
            rows.append(('POST', ct, parts, 415))
            if version == '11':
                rows.append(('POST', 'application/soap+xml', body, 415))
            for method in ('GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'):
                rows.append((method, media(version), body, 405))
            # A valid same-connection request after every rejection checks cleanup and callback isolation.
            rows = [entry for row in rows for entry in (row, ('POST', media(version), body, 200))]
            expected_calls = sum(row[3] == 200 for row in rows)
            for state in ('source', 'saved', 'data'):
                for mode in ('native', 'retained'):
                    with endpoint(['qore','-b','--enable-debug',str(PEER/'handler.qr'),version,state,mode,
                                   str(expected_calls)], ENV) as (_, port):
                        connection = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                        try:
                            for method, ct, payload, status in rows:
                                connection.request(method,'/service',payload,{} if ct is None else {'Content-Type':ct})
                                response = connection.getresponse(); raw = response.read(); total += 1
                                self.assertEqual(status,response.status,(version,method,ct,raw))
                                if status == 200:
                                    document = etree.fromstring(raw); self.schemas[version].assertValid(document)
                                    self.assertEqual('response',document.find('{'+URI[version]+'}Body/{urn:soap-envelope-test}value').text)
                                else:
                                    self.assertTrue(response.getheader('Content-Type').startswith('text/plain'),raw)
                                    self.assertNotIn(b'Envelope',raw)
                                    self.assertEqual('POST' if status == 405 else None,response.getheader('Allow'))
                            connection.request('GET','/service?wsdl')
                            response = connection.getresponse(); raw = response.read()
                            self.assertEqual(200,response.status,raw)
                            self.assertEqual('{http://schemas.xmlsoap.org/wsdl/}definitions',etree.fromstring(raw).tag)
                        finally:
                            connection.close()
        self.assertEqual(708,total)

    def test_client_media_and_header_callback_boundaries(self):
        total = 0
        for version in URI:
            body = envelope(version)
            rows = [(ct, body, 'OK') for ct in ('text/xml','application/xml',media(version))]
            for ct in (None,'text/plain','application/json','application/octet-stream',
                    'multipart/mixed;boundary="x"','application/xop+xml;type="application/json"',media(version)+';charset=unknown-qore-test'):
                rows.append((ct,body,'SOAP-MEDIA-TYPE-ERROR'))
            for ct in ('broken;type','application/xop+xml','text/xml;charset=UTF-8;charset=ISO-8859-1','text/xml;charset=""'):
                rows.append((ct,body,'SOAP-MESSAGE-ERROR'))
            if version == '11':
                rows.append(('application/soap+xml',body,'SOAP-MEDIA-TYPE-ERROR'))
            ct, parts = multipart(media(version),body); rows.append((ct,parts,'OK'))
            ct, parts = multipart('application/xop+xml;type="'+media(version)+'"',body); rows.append((ct,parts,'OK'))
            rows = [entry for row in rows for entry in (row,(media(version),body,'OK'))]
            responses = queue.Queue(); requests = queue.Queue(); expected = []
            for _ in range(6):
                for ct,payload,error in rows:
                    responses.put((200,{} if ct is None else {'Content-Type':ct},payload))
                    row = {'error':error,'status':200,'headers_processed':int(error=='OK')}
                    if error == 'OK': row['value'] = 'response'
                    expected.append(row)
            with origin('soap-media',requests,lambda _:responses.get_nowait(),content_type=None) as url:
                result = subprocess.run(['qore','-b','--enable-debug',str(PEER/'client.qr')],
                    input=json.dumps({'version':version,'url':url,'count':len(rows)}),env=ENV,
                    text=True,capture_output=True,timeout=120)
                self.assertEqual((0,''),(result.returncode,result.stderr),result.stdout)
            self.assertEqual(expected,json.loads(result.stdout))
            self.assertTrue(responses.empty()); self.assertEqual(len(expected),requests.qsize()); total += len(expected)
        self.assertEqual(396,total)

    def test_invalid_encoded_bytes_keep_the_protocol_error(self):
        for version in URI:
            for state in ('source','saved','data'):
                for mode in ('native','retained'):
                    with endpoint(['qore','-b','--enable-debug',str(PEER/'handler.qr'),version,state,mode,'1'],ENV) as (_,port):
                        connection = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                        try:
                            connection.request('POST','/service',b'\xff',{'Content-Type':media(version)+';charset=UTF-16LE'})
                            response = connection.getresponse(); raw=response.read()
                            self.assertEqual(400 if version=='12' else 500,response.status,raw)
                            document=etree.fromstring(raw);self.schemas[version].assertValid(document)
                            self.assertIn(b'ENCODING-CONVERSION-ERROR',raw)
                            connection.request('POST','/service',envelope(version),{'Content-Type':media(version)})
                            response=connection.getresponse();raw=response.read();self.assertEqual(200,response.status,raw)
                        finally: connection.close()

    def test_http_bindings_retain_their_allowed_methods(self):
        for state in ('source','saved','data'):
            for verb in ('GET','POST'):
                wsdl = contract('http://example.invalid/','/orders',verb=verb)
                job = {'contracts':[wsdl],'state':state,'expected':[{'id':'invoice'}]}
                with endpoint(['qore','-b','--enable-debug',str(HTTP_PEER/'handler.qr'),json.dumps(job)],ENV) as (_,port):
                    connection = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                    try:
                        for method in ('DELETE','POST' if verb=='GET' else 'GET'):
                            connection.request(method,'/orders',b'',{'Content-Type':'application/octet-stream'})
                            response = connection.getresponse(); raw = response.read()
                            self.assertEqual(405,response.status,raw); self.assertEqual(verb,response.getheader('Allow'))
                        connection.request(verb,'/orders?id=invoice' if verb=='GET' else '/orders',
                            None if verb=='GET' else b'id=invoice',{'Content-Type':'application/x-www-form-urlencoded'})
                        response = connection.getresponse(); raw=response.read(); self.assertEqual(200,response.status,raw)
                    finally: connection.close()

    def test_mixed_http_methods_are_advertised_together(self):
        for state in ('source','saved','data'):
            contracts = [contract('http://example.invalid/','/orders',verb=verb) for verb in ('GET','POST')]
            job = {'contracts':contracts,'state':state,'expected':[{'id':'invoice'},{'id':'invoice'}]}
            with endpoint(['qore','-b','--enable-debug',str(HTTP_PEER/'handler.qr'),json.dumps(job)],ENV) as (_,port):
                connection = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                try:
                    connection.request('PUT','/orders',b'')
                    response = connection.getresponse(); raw=response.read()
                    self.assertEqual(405,response.status,raw); self.assertEqual('GET, POST',response.getheader('Allow'))
                    for verb in ('GET','POST'):
                        connection.request(verb,'/orders?id=invoice' if verb=='GET' else '/orders',
                            None if verb=='GET' else b'id=invoice',{'Content-Type':'application/x-www-form-urlencoded'})
                        response = connection.getresponse(); raw=response.read(); self.assertEqual(200,response.status,raw)
                finally: connection.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
