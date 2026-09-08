#!/usr/bin/env python3
"""Independent WSDL multipart element identity, header, provider and sample checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey


XSD = "http://www.w3.org/2001/XMLSchema"
PARTS = {"first": ("urn:first", "boolean"), "second": ("urn:second", "int"), "plain": ("", "string")}


def schema(namespace, type_name):
    target = f' targetNamespace="{namespace}"' if namespace else ""
    return f'<xs:schema xmlns:xs="{XSD}"{target}><xs:element name="item" type="xs:{type_name}"/></xs:schema>'


def description(version, header):
    soap = "http://schemas.xmlsoap.org/wsdl/soap" + ("12" if version == "12" else "") + "/"
    definitions = ''.join(schema(*part) for part in PARTS.values())
    parts = ('<w:part name="first" xmlns="urn:first" element="item"/>'
             '<w:part name="second" xmlns:a="urn:second" element="a:item"/>'
             '<w:part name="plain" xmlns="" element="item"/>')
    body = '<s:body use="literal" parts="first plain"/>' if header else '<s:body use="literal"/>'
    input_binding = body + ('<s:header use="literal" message="t:Request" part="second"/>' if header else '')
    output_binding = input_binding.replace('t:Request', 't:Response')
    return (f'<w:definitions xmlns:w="http://schemas.xmlsoap.org/wsdl/" xmlns:s="{soap}" '
            'xmlns:t="urn:message" xmlns:a="urn:first" targetNamespace="urn:message">'
            f'<w:types>{definitions}</w:types><w:message name="Request">{parts}</w:message>'
            f'<w:message name="Response">{parts}</w:message><w:portType name="Port"><w:operation name="submit">'
            '<w:input message="t:Request"/><w:output message="t:Response"/></w:operation></w:portType>'
            '<w:binding name="Soap" type="t:Port"><s:binding style="document" '
            'transport="http://schemas.xmlsoap.org/soap/http"/><w:operation name="submit">'
            f'<s:operation soapAction="urn:submit"/><w:input>{input_binding}</w:input>'
            f'<w:output>{output_binding}</w:output></w:operation></w:binding>'
            '<w:service name="Service"><w:port name="Port" binding="t:Soap">'
            '<s:address location="http://example.invalid/"/></w:port></w:service></w:definitions>')


def envelope(version, header, variant="valid"):
    namespace = survey.SOAP_NAMESPACES[int(version == "12")]
    first = '<a:item>false</a:item>' if variant != "missing" else ''
    second = '<b:item>0</b:item>'
    text = (f'<e:Envelope xmlns:e="{namespace}" xmlns:a="urn:first" xmlns:b="urn:second">'
            + (f'<e:Header>{second}</e:Header>' if header else '') + f'<e:Body>{first}'
            + ('' if header else second) + '<item/></e:Body></e:Envelope>')
    if variant == "wrong":
        text = text.replace('xmlns:a="urn:first"', 'xmlns:a="urn:wrong"')
    elif variant == "invalid-int":
        text = text.replace('<b:item>0</b:item>', '<b:item>invalid</b:item>')
    return text


class MessageIdentityTest(unittest.TestCase):
    def test_parts_scopes_headers_and_reconstructed_consumers(self):
        jobs = {part: SchemaJob(part, f'http://example.invalid/{part}.xsd', schema(*definition).encode())
                for part, definition in PARTS.items()}
        validators = {part: etree.XMLSchema(etree.fromstring(job.schema)) for part, job in jobs.items()}
        verdicts = {}

        def record_parts(name, text, header, expected_values=None, variant="valid"):
            root = etree.fromstring(text.encode())
            body = root.find('{*}Body')
            header_element = root.find('{*}Header')
            nodes = {"plain": body[-1]}
            first = body.find('{urn:wrong}item' if variant == 'wrong' else '{urn:first}item')
            if first is not None:
                nodes['first'] = first
            nodes['second'] = header_element[0] if header else body[-2]
            self.assertEqual(2 if header else 3, len(body) + int(variant == "missing"))
            if expected_values is not None:
                expected_names = ['{urn:first}item', 'item'] if header else [
                    '{urn:first}item', '{urn:second}item', 'item']
                self.assertEqual(expected_names, [child.tag for child in body])
                if header:
                    self.assertEqual(['{urn:second}item'], [child.tag for child in header_element])
                self.assertEqual({"first": 'true' if expected_values['first'] else 'false',
                                  "second": str(expected_values['second']), "plain": expected_values['plain']},
                                 {part: node.text or '' for part, node in nodes.items()})
            for part, node in nodes.items():
                valid = not (part == 'first' and variant == 'wrong') and not (
                    part == 'second' and variant == 'invalid-int')
                self.assertEqual(valid, validators[part].validate(node), (name, part, str(validators[part].error_log)))
                key = name + '/' + part
                jobs[part].documents[key], verdicts[key] = etree.tostring(node), valid

        with tempfile.TemporaryDirectory(prefix="wsdl-message-identity-") as temporary:
            root = Path(temporary)
            for version, namespace in zip(("11", "12"), survey.SOAP_NAMESPACES):
                for header in (False, True):
                    prefix = f'{version}/{"header" if header else "body"}'
                    wsdl = root / (prefix.replace('/', '-') + '.wsdl')
                    wsdl.write_text(description(version, header))
                    messages = []
                    for direction in ('request', 'response'):
                        for variant in ('valid', 'wrong', 'missing', 'invalid-int'):
                            name = f'{prefix}/{direction}/{variant}'
                            text = envelope(version, header, variant)
                            path = root / name.replace('/', '-')
                            path.write_text(text)
                            messages.append({'file': name, 'path': str(path), 'direction': direction})
                            record_parts(name, text, header, variant=variant)
                    case = {'name': prefix, 'wsdl': str(wsdl), 'base': 'http://example.invalid/',
                            'operation': 'submit', 'binding': 'Soap', 'messages': messages}
                    rows = survey.run_worker([case], {})
                    counts = survey.stage_accounting([case], rows)['counts']
                    self.assertEqual(2, sum(row['stage'] == 'serialize' and row['ok']
                                           and row.get('file', '').endswith('/valid') for row in rows), rows)
                    self.assertEqual(0, counts['deserialize']['missing'])
                    self.assertEqual(0, counts['deserialize']['skipped'])
                    for row in rows:
                        if row['stage'] == 'parse':
                            self.assertTrue(row['ok'], row)
                        elif row['file'].endswith('/invalid-int'):
                            if row['stage'] == 'deserialize':
                                with self.subTest(file=row['file'], requirement='P3-integer-lexical-rejection'):
                                    self.assertFalse(row['ok'], row)
                                    self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['err'])
                        elif not row['file'].endswith('/valid'):
                            self.assertFalse(row['ok'], row)
                            self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['err'])
                        elif row['stage'] == 'serialize':
                            self.assertEqual(f'{{{namespace}}}Envelope', etree.fromstring(row['body'].encode()).tag)
                            record_parts(row['file']+'/output', row['body'], header,
                                         {'first': False, 'second': 0, 'plain': ''})
                        else:
                            self.assertTrue(row['ok'], row)
                    process = subprocess.run(
                        ['qore', '--enable-debug', str(Path(__file__).with_name('message-identity.qr')), str(wsdl)],
                        text=True, capture_output=True, timeout=30, check=True)
                    self.assertEqual('', process.stderr)
                    values = [json.loads(line) for line in process.stdout.splitlines()]
                    self.assertEqual(4, len(values))
                    for row in values:
                        value = row['value']
                        self.assertIs(bool, type(value['first']))
                        self.assertIs(int, type(value['second']))
                        self.assertEqual({'first': False, 'second': 0, 'plain': ''} if row['mode'] == 'values'
                                         else {'first': True, 'second': 123, 'plain': 'abc'}, value)
                        expected = dict(value)
                        if header:
                            message = 'Request' if row['direction'] == 'request' else 'Response'
                            expected[message] = {'second': expected.pop('second')}
                        self.assertEqual(expected, row['decoded'])
                        self.assertEqual(f'{{{namespace}}}Envelope', etree.fromstring(row['body'].encode()).tag)
                        record_parts(prefix+'/'+row['direction']+'/'+row['mode'], row['body'], header, value)
        results = run_independent(list(jobs.values()))
        self.assertEqual(160, len(results['documents']))
        self.assertEqual(set(verdicts), set(results['documents']))
        for name, valid in verdicts.items():
            self.assertEqual(valid, results['documents'][name]['ok'], (name, results['documents'][name]))


if __name__ == '__main__':
    unittest.main()
