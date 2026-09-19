#!/usr/bin/env python3
"""Independent nested HTTP MIME interoperability. Copyright (C) 2026 Qore Technologies, s.r.o."""
import base64
import copy
from email import encoders, policy
from email.parser import BytesParser
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
BASE=ROOT/'mime-tree-peer'
from test_cxf_peer import endpoint

EXPECTED={'format':'multipart:0','root':1,'parts':[
 {'format':'multipart:0','content_id':'inner@peer','root':0,'parts':[
  {'format':'xml:first','content_id':'xml@peer','value':'A & č'}]},
 {'format':'content:second','content_id':'binary@peer','hex':'00ff0d0a'}]}

def command(mode,state,*args):
    return ['qore','-b','--enable-debug',str(BASE/'qore-peer.qr'),mode,str(BASE/'nested.wsdl'),state,*args]

def checked(cmd):
    result=subprocess.run(cmd,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    if result.returncode or result.stderr:
        raise AssertionError((result.returncode,result.stdout,result.stderr))
    return result.stdout

def parsed(wire):
    message=BytesParser(policy=policy.default).parsebytes(
        ('Content-Type: '+wire['headers']['Content-Type']+'\r\n\r\n').encode('ascii')+base64.b64decode(wire['body'],validate=True))
    for entity in message.walk():
        if entity.defects: raise AssertionError(entity.defects)
    return message

def verify(wire):
    def entity_map(msg):
        assert msg.get_content_type()=='multipart/related'
        parts={str(part['Content-ID']):part for part in msg.iter_parts()}
        assert len(parts)==len(list(msg.iter_parts()))
        assert msg.get_param('start') in parts
        assert parts[msg.get_param('start')].get_content_type()==msg.get_param('type')
        return parts
    outer=parsed(wire);parts=entity_map(outer)
    assert outer.get_param('start')=='<binary@peer>'
    assert set(parts)=={'<binary@peer>','<inner@peer>'}
    assert parts['<binary@peer>'].get_payload(decode=True)==bytes.fromhex('00ff0d0a')
    inner=parts['<inner@peer>'];leaves=entity_map(inner)
    assert set(leaves)=={'<xml@peer>'}
    assert inner.get_param('start')=='<xml@peer>'
    xml=ET.fromstring(leaves['<xml@peer>'].get_payload(decode=True))
    assert xml.tag=='first' and xml.text=='A & č'

def independent(encoding='base64', reverse=False):
    xml=MIMEBase('text','xml',charset='utf-8');xml['Content-ID']='<xml@peer>'
    xml.set_payload('<first>A &amp; č</first>'.encode())
    (encoders.encode_base64 if encoding=='base64' else encoders.encode_quopri)(xml)
    inner=MIMEMultipart('related',boundary='inner-python',type='text/xml',start='<xml@peer>')
    inner['Content-ID']='<inner@peer>';inner.attach(xml)
    binary=MIMEBase('application','octet-stream');binary['Content-ID']='<binary@peer>'
    binary.set_payload(bytes.fromhex('00ff0d0a'));encoders.encode_base64(binary)
    outer=MIMEMultipart('related',boundary='outer-python',type='application/octet-stream',start='<binary@peer>')
    for part in ([binary,inner] if reverse else [inner,binary]):outer.attach(part)
    full=outer.as_bytes(policy=policy.SMTP)
    _,body=full.split(b'\r\n\r\n',1)
    return {'headers':{'Content-Type':str(outer['Content-Type'])},'body':base64.b64encode(body).decode()}

class TreePeerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=tempfile.TemporaryDirectory(prefix='xml-mime-tree-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.output=Path(cls.directory.name)

    def test_qore_output(self):
        for state in ('source','saved'):
            for wire in json.loads(checked(command('encode',state))):verify(wire)
    def test_python_input(self):
        for encoding in ('base64','quoted-printable'):
            for reverse in (False,True):
                wire=independent(encoding,reverse);verify(wire)
                fixture=self.output/'input.json';fixture.write_text(json.dumps(wire))
                for state in ('source','saved'):
                    self.assertEqual([EXPECTED]*4,json.loads(checked(command('decode',state,str(fixture)))))
    def test_invalid_entities_and_recovery(self):
        valid=independent()
        cases=[]
        for name,error in [('missing','SOAP-DESERIALIZATION-ERROR'),('extra','SOAP-DESERIALIZATION-ERROR'),
                           ('duplicate-id','SOAP-MESSAGE-ERROR'),('wrong-media','SOAP-DESERIALIZATION-ERROR'),
                           ('missing-root','SOAP-MESSAGE-ERROR'),('wrong-root-type','SOAP-MESSAGE-ERROR'),
                           ('nested-root','SOAP-MESSAGE-ERROR'),('wrong-schema','SOAP-DESERIALIZATION-ERROR')]:
            msg=parsed(valid)
            parts=list(msg.iter_parts())
            if name=='missing':msg.set_payload(parts[1:])
            elif name=='extra':
                extra=copy.deepcopy(parts[1]);extra.replace_header('Content-ID','<extra@peer>')
                msg.set_payload(parts+[extra])
            elif name=='duplicate-id':parts[1].replace_header('Content-ID',parts[0]['Content-ID'])
            elif name=='wrong-media':
                parts[1].replace_header('Content-Type','image/png');msg.set_param('type','image/png')
            elif name=='missing-root':msg.set_param('start','<absent@peer>')
            elif name=='wrong-root-type':msg.set_param('type','text/xml')
            elif name=='nested-root':parts[0].set_param('start','<absent@peer>')
            elif name=='wrong-schema':
                leaf=list(parts[0].iter_parts())[0]
                del leaf['Content-Transfer-Encoding']
                leaf.set_payload(b'<wrong>value</wrong>');encoders.encode_base64(leaf)
            full=msg.as_bytes(policy=policy.SMTP);_,body=full.split(b'\r\n\r\n',1)
            cases.append({'name':name,'error':error,'wire':{'headers':{'Content-Type':str(msg['Content-Type'])},
                                                        'body':base64.b64encode(body).decode()}})
        fixture=self.output/'negative.json';fixture.write_text(json.dumps({'valid':valid,'cases':cases}))
        for state in ('source','saved'):
            self.assertEqual(str(len(cases)*2)+'\n',checked(command('decode-errors',state,str(fixture))))

    def test_qore_client(self):
        for state in ('source','saved'):
            errors=queue.Queue()
            class Handler(BaseHTTPRequestHandler):
                def log_message(self,*args):pass
                def do_POST(self):
                    try:
                        assert self.path=='/call'
                        request={'headers':{'Content-Type':self.headers['Content-Type']},
                                 'body':base64.b64encode(self.rfile.read(int(self.headers['Content-Length']))).decode()}
                        verify(request)
                        response=independent('quoted-printable');body=base64.b64decode(response['body'])
                        self.send_response(200);self.send_header('Content-Type',response['headers']['Content-Type'])
                        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
                    except BaseException as exc:errors.put(exc);self.send_error(500)
            with HTTPServer(('127.0.0.1',0),Handler) as server:
                server.timeout=30
                worker=threading.Thread(target=server.handle_request);worker.start()
                try:self.assertEqual('PASS\n',checked(command('client',state,f'http://127.0.0.1:{server.server_port}/')))
                finally:worker.join(35)
                self.assertFalse(worker.is_alive())
            if not errors.empty():raise errors.get_nowait()
    def test_qore_server(self):
        for state in ('source','saved'):
            with endpoint(command('server',state)) as (_,port):
                client=http.client.HTTPConnection('127.0.0.1',port,timeout=30)
                try:
                    wire=independent();body=base64.b64decode(wire['body'])
                    client.request('POST','/call',body,wire['headers'])
                    response=client.getresponse();data=response.read()
                    self.assertEqual(200,response.status,data)
                    verify({'headers':{'Content-Type':response.getheader('Content-Type')},'body':base64.b64encode(data).decode()})
                finally:client.close()

if __name__=='__main__':unittest.main(verbosity=2)
