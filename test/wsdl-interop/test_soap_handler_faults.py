#!/usr/bin/env python3
"""Independent handler fault mapping. Copyright (C) 2026 Qore Technologies, s.r.o."""
import hashlib
import http.client
import json
from pathlib import Path
import unittest
from lxml import etree
from test_cxf_peer import endpoint
from test_soap_envelope import ENV, URI, LocalSchemas, PEER as SCHEMA_PEER
from test_soap_fault_data import qname
ROOT = Path(__file__).resolve().parent / 'soap-fault-peer'


def request(version, token=None, unknown=False, invalid=False):
    env = f'{{{URI[version]}}}'
    root = etree.Element(env + 'Envelope', nsmap={'e': URI[version], 't': 'urn:parts'})
    if token is not None or unknown:
        header = etree.SubElement(root, env + 'Header')
        if token is not None:
            block = etree.SubElement(header, '{urn:parts}Token')
            block.set(env + 'mustUnderstand', '1')
            block.text = token
        if unknown:
            etree.SubElement(header, '{urn:parts}Unknown').set(env + 'mustUnderstand', '1')
    body = etree.SubElement(root, env + 'Body')
    etree.SubElement(body, '{urn:parts}Left').text = 'invalid' if invalid else '1'
    etree.SubElement(body, '{urn:parts}Right').text = '2'
    return etree.tostring(root)


class HandlerFaultTests(unittest.TestCase):
    def test_handler_fault_boundaries_and_recovery(self):
        for row in json.loads((SCHEMA_PEER / 'schemas.json').read_text())['schemas']:
            data = (SCHEMA_PEER / row['path']).read_bytes()
            self.assertEqual(row['size'], len(data))
            self.assertEqual(row['sha256'], hashlib.sha256(data).hexdigest())
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        schemas = {v: etree.XMLSchema(etree.fromstring((SCHEMA_PEER / f'soap{v}.xsd').read_bytes(), parser)) for v in URI}
        total = 0
        for version in URI:
            env = f'{{{URI[version]}}}'
            sender, receiver = ('Sender', 'Receiver') if version == '12' else ('Client', 'Server')
            rejected = 400 if version == '12' else 500
            # (token, unknown MU, invalid body, callback mode, HTTP, fault code, header/detail placement, processor calls, body calls)
            cases = [('7', False, False, 'success', rejected, sender, 'header', 1, 0),
                     ('7', False, True, 'success', rejected, sender, 'header', 1, 0),
                     ('8', False, False, 'success', 500, receiver, None, 1, 0),
                     ('9', False, False, 'success', 500, receiver, None, 1, 0),
                     ('7', True, True, 'success', 500, 'MustUnderstand', None, 0, 0),
                     (None, False, False, 'runtime', 500, receiver, None, 0, 1),
                     (None, False, False, 'output', 500, receiver, None, 0, 1),
                     (None, False, False, 'structured', 500, receiver, None, 0, 1),
                     (None, False, False, 'control', 500, receiver, None, 0, 1),
                     (None, False, False, 'declared', rejected, sender, 'detail', 0, 1),
                     (None, False, False, 'header', rejected, sender, 'header', 0, 1),
                     (None, False, True, 'success', rejected, sender, None, 0, 0)]
            success = (None, False, False, 'success', 200, None, None, 0, 1)
            rows = [(action, item) for action in (False, True) for case in cases for item in (case, success)]
            self.assertEqual(48, len(rows))
            for state in ('source', 'saved', 'data'):
                for retained in (False, True):
                    command = ['qore', '-b', '--enable-debug', str(ROOT / 'handler.qr'), version, state,
                               'retained' if retained else 'native', str(sum(r[-2] for _, r in rows)),
                               str(sum(r[-1] for _, r in rows))]
                    with endpoint(command, ENV) as (_, port):
                        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
                        self.addCleanup(connection.close)
                        for action, row in rows:
                            token, unknown, invalid, mode, status, code, placement, _, _ = row
                            headers = {'Content-Type': 'application/soap+xml' if version == '12' else 'text/xml',
                                       'X-Fault-Mode': mode}
                            if action:
                                headers['SOAPAction'] = 'urn:exchange'
                            connection.request('POST', '/service', request(version, token, unknown, invalid), headers)
                            response = connection.getresponse()
                            xml = response.read()
                            self.assertEqual(status, response.status, (row, xml))
                            root = etree.fromstring(xml)
                            schemas[version].assertValid(root)
                            if code is None:
                                self.assertEqual(['1', '2'], [n.text for n in root.find(env + 'Body')])
                            else:
                                fault = root.find(env + 'Body/' + env + 'Fault')
                                value = fault.find(env + 'Code/' + env + 'Value') if version == '12' else fault.find('faultcode')
                                self.assertEqual(env + code, qname(value))
                                header = root.find(env + 'Header/{urn:parts}Token')
                                detail = fault.find((env + 'Detail' if version == '12' else 'detail') + '/{urn:parts}Token')
                                self.assertEqual('71' if placement == 'header' else None, header.text if header is not None else None)
                                self.assertEqual('71' if placement == 'detail' else None, detail.text if detail is not None else None)
                                reason = fault.find(env + 'Reason/' + env + 'Text') if version == '12' else fault.find('faultstring')
                                if mode == 'control':
                                    self.assertEqual(r'CONTROL: bad\u{0000}after\u{0001}end', reason.text)
                                if mode == 'structured':
                                    self.assertTrue(reason.text.startswith('71:'))
                                    self.assertIn('order', reason.text)
                                if unknown and version == '12':
                                    block = root.find(env + 'Header/' + env + 'NotUnderstood')
                                    prefix, local = block.get('qname').split(':')
                                    self.assertEqual(('urn:parts', 'Unknown'), (block.nsmap[prefix], local))
                            total += 1
                        connection.close()
        self.assertEqual(576, total)


if __name__ == '__main__':
    unittest.main(verbosity=2)
