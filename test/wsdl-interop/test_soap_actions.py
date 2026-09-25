#!/usr/bin/env python3
"""Independent SOAP action HTTP checks. Copyright (C) 2026 Qore Technologies, s.r.o."""
from email.message import Message
import http.client
from pathlib import Path
import queue
import subprocess
import unittest
from lxml import etree
from test_cxf_peer import endpoint, root_entity
from test_http_request_url import origin
from test_soap_envelope import ENV, URI
import test_soap_oneway
from test_soap_fault_data import qname

PEER = Path(__file__).resolve().parent / 'soap-action-peer'


def envelope(version, body=''):
    return f'<e:Envelope xmlns:e="{URI[version]}"><e:Body>{body}</e:Body></e:Envelope>'.encode()


def media(version, action=None):
    value = 'application/soap+xml' if version == '12' else 'text/xml'
    if version == '12' and action is not None:
        value += ';action="' + action + '"'
    return value


def multipart(ct, xml):
    root_type = ct.split(';')[0]
    return (f'multipart/related;boundary="root";type="{root_type}";start="<body>"',
        f'--root\r\nContent-Type: {ct}\r\nContent-ID: <body>\r\n\r\n'.encode()+xml+b'\r\n--root--\r\n')


class SoapActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_soap_oneway.OneWayTests.setUpClass()
        cls.schemas = test_soap_oneway.OneWayTests.schemas

    def test_client_wire_headers(self):
        count = 0
        for version in URI:
            received = queue.Queue()
            reply = envelope(version,'<t:value xmlns:t="urn:empty-route">external</t:value>')
            with origin('actions',received,lambda _: (200,{},reply),content_type=media(version)) as url:
                result = subprocess.run(['qore','-b','--enable-debug',str(PEER/'client.qr'),version,url],
                    env=ENV,capture_output=True,text=True,timeout=90)
                self.assertEqual((0,'DONE\n',''),(result.returncode,result.stdout,result.stderr))
            for _ in range(6):
                for action in ('urn:first','urn:override',None,'HTTP://Example.org/a%2fb'):
                    request = received.get_nowait(); count += 1
                    self.assertEqual('POST',request['method'])
                    headers = request['headers']
                    content_type = Message(); content_type['Content-Type'] = headers['content-type']
                    self.assertEqual('application/soap+xml' if version == '12' else 'text/xml',content_type.get_content_type())
                    self.assertEqual(action if version == '12' else None,content_type.get_param('action'))
                    # SOAP 1.1 always carries SOAPAction, "" for an explicit empty action (WS-I R2745)
                    self.assertEqual(('"'+(action or '')+'"') if version == '11' else None,headers.get('soapaction'))
                    if version == '12' and action:
                        self.assertIn(';action="'+action+'"',headers['content-type'])
                    document = etree.fromstring(request['body']); self.schemas[version].assertValid(document)
                    self.assertEqual(0,len(document.find('{'+URI[version]+'}Body')))
            self.assertTrue(received.empty())
        self.assertEqual(48,count)

    def test_handler_routing_errors_and_recovery(self):
        count = 0
        for version in URI:
            scalar = envelope(version,'<t:value xmlns:t="urn:empty-route">invoice</t:value>')
            rows = []
            for name in ('first','second'):
                for parts in (False,True):
                    ct = media(version,'urn:'+name); body = envelope(version)
                    if parts: ct,body = multipart(ct,body)
                    rows.append((body,ct,('"urn:'+name+'"') if version == '11' else None,name))
            rows.append((scalar,media(version),None,'scalar'))
            rows.append((scalar,media(version,'urn:scalar'),'"urn:scalar"' if version == '11' else 'urn:first','scalar'))
            rows.append((scalar,media(version,'urn:unknown'),'"urn:unknown"' if version == '11' else None,None))
            rows.append((scalar,media(version,'urn:bad{uri'),'"urn:bad{uri"' if version == '11' else None,None))
            rows.append((envelope(version),media(version),'urn:first' if version == '12' else None,None))
            if version == '11':
                rows.extend([(scalar,media(version),'"urn:scalar" trailing',None),
                    (scalar,media(version),'"urn:scalar","urn:first"',None),
                    (scalar,media(version),'""','scalar'),
                    (envelope(version),media(version),'urn:first','first'),
                    (envelope(version),media(version),' "urn:first"\t','first')])
            else:
                rows.extend([(scalar,media(version,''),None,None),(scalar,media(version,'relative'),None,None),
                    (scalar,media(version,'urn:scalar')+';action="urn:first"',None,None),
                    (scalar,media(version,'urn:scalar')+';action="urn:scalar"',None,'scalar'),
                    (scalar,media(version),'"malformed legacy header','scalar')])
                ct,body = multipart('application/xop+xml;type="application/soap+xml;action=\\"urn:first\\""',envelope(version))
                rows.append((body,ct,None,'first'))
            # A valid request after each row tests reuse after failures and fixes the expected callback count.
            rows = [entry for row in rows for entry in (row,(scalar,media(version),None,'scalar'))]
            successful = sum(row[3] is not None for row in rows)
            for state in ('source','saved','data'):
                for mode in ('native','retained'):
                    command = ['qore','-b','--enable-debug',str(PEER/'handler.qr'),version,state,mode,str(successful)]
                    with endpoint(command,ENV) as (_,port):
                        connection = http.client.HTTPConnection('127.0.0.1',port,timeout=10)
                        try:
                            for body,ct,action,expected in rows:
                                headers = {'Content-Type':ct}
                                if action is not None: headers['SOAPAction'] = action
                                connection.request('POST','/service',body,headers)
                                response = connection.getresponse(); raw = response.read(); count += 1
                                self.assertEqual(200 if expected else 400 if version == '12' else 500,response.status,raw)
                                self.assertIsNone(response.getheader('SOAPAction'))
                                cm = Message(); cm['Content-Type'] = response.getheader('Content-Type')
                                self.assertIsNone(cm.get_param('action'))
                                # an MTOM request is answered with an MTOM response
                                document = etree.fromstring(root_entity(response.getheader('Content-Type'), raw))
                                self.schemas[version].assertValid(document)
                                root = '{'+URI[version]+'}'
                                if expected:
                                    self.assertEqual(expected,document.find(root+'Body/{urn:empty-route}value').text)
                                else:
                                    code = document.find(root+'Body/'+root+'Fault/'+(root+'Code/'+root+'Value' if version == '12' else 'faultcode'))
                                    self.assertEqual(root+('Sender' if version == '12' else 'Client'),qname(code))
                        finally:
                            connection.close()
        self.assertEqual(348,count)


if __name__ == '__main__':
    unittest.main(verbosity=2)
