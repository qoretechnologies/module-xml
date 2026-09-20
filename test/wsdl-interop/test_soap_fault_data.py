#!/usr/bin/env python3
"""Independent fault metadata/generation checks. Copyright (C) 2026 Qore Technologies, s.r.o."""
import copy
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
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'


def qname(element):
    lexical = element.text.strip()
    if ':' in lexical:
        prefix, local = lexical.split(':')
        namespace = element.nsmap[prefix]
    else:
        local, namespace = lexical, element.nsmap.get(None, '')
    return f'{{{namespace}}}{local}'


def metadata(xml, version):
    root = etree.fromstring(xml.encode())
    env = f'{{{URI[version]}}}'
    fault = root.find(env + 'Body/' + env + 'Fault')
    codes = []
    if version == '12':
        code = fault.find(env + 'Code')
        while code is not None:
            codes.append(qname(code.find(env + 'Value')))
            code = code.find(env + 'Subcode')
        reasons = fault.findall(env + 'Reason/' + env + 'Text')
    else:
        codes = [qname(fault.find('faultcode'))]
        reasons = [fault.find('faultstring')]
    def field(name):
        element = fault.find(name)
        return None if element is None else ' '.join((element.text or '').split())
    header = root.find(env + 'Header')
    return dict(error='SOAP-SERVER-FAULT-RESPONSE', status=500, codes=codes,
                reasons=[dict(text=r.text or '', language=r.get(XML_LANG)) for r in reasons],
                actor=field('faultactor') if version == '11' else None,
                node=field(env + 'Node') if version == '12' else None,
                role=field(env + 'Role') if version == '12' else None,
                detail=fault.find(env + 'Detail' if version == '12' else 'detail') is not None,
                headers=len(header) if header is not None else 0)


class FaultDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for row in json.loads((SCHEMA_PEER / 'schemas.json').read_text())['schemas']:
            raw = (SCHEMA_PEER / row['path']).read_bytes()
            if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('changed pinned W3C schema')
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        cls.schemas = {v: etree.XMLSchema(etree.fromstring((SCHEMA_PEER / f'soap{v}.xsd').read_bytes(), parser))
                       for v in ('11', '12')}
        result = subprocess.run(['qore', '-b', '--enable-debug', str(ROOT / 'generate.qr')],
                                capture_output=True, text=True, env=ENV, timeout=90)
        if result.returncode or result.stderr:
            raise ValueError(result.stdout + result.stderr)
        cls.rows = json.loads(result.stdout)
        if len(cls.rows) != 63 or len({(r['version'], r['state'], r['code'], r['kind']) for r in cls.rows}) != 63:
            raise ValueError('missing or repeated fault generation cases')

    def test_generated_fields_and_pinned_schema(self):
        for row in self.rows:
            with self.subTest(version=row['version'], state=row['state'], code=row['code'], kind=row['kind']):
                version = row['version']
                env = f'{{{URI[version]}}}'
                root = etree.fromstring(row['xml'].encode())
                schema_root = copy.deepcopy(root)
                if version == '11':
                    # WS-I R1016 permits xml:lang; the unamended SOAP 1.1 schema omits that attribute.
                    del schema_root.find(env + 'Body/' + env + 'Fault/faultstring').attrib[XML_LANG]
                self.assertTrue(self.schemas[version].validate(schema_root), str(self.schemas[version].error_log))
                info = metadata(row['xml'], version)
                self.assertEqual([env + row['code']] + (['{urn:order}Rejected', '{}Missing'] if version == '12' else []),
                                 info['codes'])
                self.assertEqual([dict(text='Refusé & <réessayer>', language='fr')]
                                 + ([dict(text='拒否', language='ja')] if version == '12' else []), info['reasons'])
                self.assertEqual('../node#71' if version == '12' else None, info['node'])
                self.assertEqual('urn:receiver' if version == '12' else None, info['role'])
                self.assertEqual('https://example.test/actor' if version == '11' else None, info['actor'])
                self.assertEqual(row['kind'] == 'declared', info['detail'])
                self.assertEqual(int(row['kind'] == 'header'), info['headers'])
                token = root.find('.//{urn:parts}Token')
                self.assertEqual('71' if row['kind'] != 'generic' else None, token.text if token is not None else None)

    def test_fault_encoding_attributes(self):
        cases = json.loads((ROOT / 'soap12-attributes.json').read_text())['cases']
        self.assertEqual(14, len(cases))
        self.assertEqual(14, len({r['name'] for r in cases}))
        self.assertEqual(3, sum(r['valid'] for r in cases))
        for row in cases:
            with self.subTest(case=row['name']):
                self.assertEqual(row['schema_valid'], self.schemas['12'].validate(etree.fromstring(row['xml'].encode())),
                                 str(self.schemas['12'].error_log))
        requests, replies = queue.Queue(), queue.Queue()
        for _ in range(6):
            for row in cases:
                replies.put(row['xml'])
        def reply(request):
            self.assertEqual(f"{{{URI['12']}}}Envelope", etree.fromstring(request['body']).tag)
            return 500, {}, replies.get_nowait().encode()
        with origin('fault-attributes', requests, reply, content_type='application/soap+xml') as url:
            result = subprocess.run(['qore', '-b', '--enable-debug', str(ROOT / 'client.qr')],
                                    input=json.dumps(dict(url=url, count=len(cases), version='12', metadata=True)),
                                    capture_output=True, text=True, env=ENV, timeout=90)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual('', result.stderr)
        expected = [metadata(r['xml'], '12') if r['valid'] else dict(error='SOAP-DESERIALIZATION-ERROR', status=500)
                    for r in cases] * 6
        self.assertEqual(expected, json.loads(result.stdout))
        self.assertTrue(replies.empty())
        self.assertEqual(84, requests.qsize())

    def test_http_metadata_matches_independent_decoder(self):
        for version in ('11', '12'):
            cases = [r for r in self.rows if r['version'] == version]
            requests, replies = queue.Queue(), queue.Queue()
            for _ in range(6):
                for row in cases:
                    replies.put(row['xml'])
            def reply(request):
                self.assertEqual(f"{{{URI[version]}}}Envelope", etree.fromstring(request['body']).tag)
                return 500, {}, replies.get_nowait().encode()
            with origin('fault-data', requests, reply,
                        content_type='application/soap+xml' if version == '12' else 'text/xml') as url:
                result = subprocess.run(['qore', '-b', '--enable-debug', str(ROOT / 'client.qr')],
                                        input=json.dumps(dict(url=url, count=len(cases), version=version, metadata=True)),
                                        capture_output=True, text=True, env=ENV, timeout=90)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual('', result.stderr)
            expected = [metadata(row['xml'], version) for row in cases] * 6
            self.assertEqual(expected, json.loads(result.stdout))
            self.assertTrue(replies.empty())
            self.assertEqual(len(expected), requests.qsize())


if __name__ == '__main__':
    unittest.main(verbosity=2)
