#!/usr/bin/env python3
"""XSD 1.0 final exclusions, independent construction and actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD


@dataclass(frozen=True)
class Case:
    name: str
    schema: str
    valid: bool
    value: object = 17
    lxml_valid: bool | None = None
    xerces_valid: bool | None = None
    xerces_reference: str | None = None


def simple(name, content, control=None):
    attribute = '' if control is None else f' final="{control}"'
    return f'<xs:simpleType name="{name}"{attribute}>{content}</xs:simpleType>'


def source(definitions, default=None, datatype='t:T'):
    attribute = '' if default is None else f' finalDefault="{default}"'
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}"{attribute}>
      {definitions}<xs:complexType name="Record" final=""><xs:sequence>
        <xs:element name="item" type="{datatype}"/></xs:sequence></xs:complexType>
      <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
    </xs:schema>'''


def definitions():
    for variety, body, value in (('atomic', '<xs:restriction base="xs:int"/>', 17),
                                 ('list', '<xs:list itemType="xs:int"/>', [17, 18]),
                                 ('union', '<xs:union memberTypes="xs:int xs:boolean"/>', 17)):
        for control in ('', 'restriction', 'list', 'union', '#all', 'list union', ' restriction restriction '):
            yield Case(f'restrict-{variety}-{control!r}', source(simple('B', body, control)
                + simple('T', '<xs:restriction base="t:B"/>')), 'restriction' not in control and control != '#all', value)
    for method in ('list', 'union'):
        body = '<xs:list itemType="t:B"/>' if method == 'list' else '<xs:union memberTypes="t:B xs:boolean"/>'
        for control in ('', 'restriction', 'list', 'union', '#all'):
            yield Case(f'{method}-atomic-{control!r}', source(simple('B', '<xs:restriction base="xs:int"/>', control)
                + simple('T', body)), method not in control and control != '#all', [17, 18] if method == 'list' else 17)
    for method in ('extension', 'restriction'):
        for content in ('complexContent', 'simpleContent'):
            base = ('<xs:sequence><xs:element name="code" type="xs:int"/></xs:sequence>'
                    if content == 'complexContent' else '<xs:simpleContent><xs:extension base="xs:int"/></xs:simpleContent>')
            restricted = base if content == 'complexContent' and method == 'restriction' else ''
            derived = f'<xs:complexType name="T"><xs:{content}><xs:{method} base="t:B">{restricted}</xs:{method}></xs:{content}></xs:complexType>'
            for control in ('', 'extension', 'restriction', '#all'):
                yield Case(f'{content}-{method}-{control!r}', source(f'<xs:complexType name="B" final="{control}">{base}</xs:complexType>'
                    + derived), method not in control and control != '#all', {'code': 17} if content == 'complexContent' else 17)
    for default in ('restriction', 'list', 'union', '#all', '', 'extension'):
        for override in (None, ''):
            yield Case(f'default-{default!r}-{override!r}', source(simple('B', '<xs:restriction base="xs:int"/>', override)
                + simple('T', '<xs:restriction base="t:B"/>', ''), default),
                override == '' or default not in ('restriction', '#all'))
    for method in ('restriction', 'list', 'union'):
        body = f'<xs:{method}><xs:simpleType><xs:restriction base="xs:int"/></xs:simpleType></xs:{method}>'
        # Both pinned validators fail to enforce anonymous simple-type finalDefault. Normative Part 2 4.1.2 does not.
        yield Case('anonymous-default-' + method, source(simple('T', body, ''), method), False,
                   lxml_valid=True, xerces_valid=True)
        yield Case('anonymous-permitted-' + method, source(simple('T', body)), True,
                   [17, 18] if method == 'list' else 17)
    for kind in ('simple', 'complex'):
        body = '<xs:restriction base="xs:int"/>' if kind == 'simple' else ''
        declaration = f'<xs:complexType name="T"><xs:sequence><xs:element name="value"><xs:{kind}Type final="">{body}</xs:{kind}Type></xs:element></xs:sequence></xs:complexType>'
        yield Case('anonymous-explicit-' + kind, source(declaration), False,
                   xerces_valid=True if kind == 'simple' else None)
    for control in ('bad', '#all restriction', 'restriction #all', '#ALL', 'restriction,union', 'restriction&#160;union'):
        yield Case('bad-default-' + control, source(simple('T', '<xs:restriction base="xs:int"/>'), control), False)
        yield Case('bad-simple-' + control, source(simple('T', '<xs:restriction base="xs:int"/>', control)), False)
    yield Case('simple-extension-token', source(simple('T', '<xs:restriction base="xs:int"/>', 'extension')), False)
    yield Case('complex-list-token', source('<xs:complexType name="T" final="list"/>'), False)
    for default in ('extension', '#all'):
        body = simple('B', '<xs:restriction base="xs:int"/>') + '<xs:complexType name="T"><xs:simpleContent><xs:extension base="t:B"/></xs:simpleContent></xs:complexType>'
        # Structures 3.14.2 is explicitly non-normative; Datatypes 4.1.2 filters extension out.
        text = source(body, default)
        reference = text.replace(f'finalDefault="{default}"', 'finalDefault="restriction list union"')
        yield Case('simple-extension-default-' + default, text, True, xerces_valid=False, xerces_reference=reference)
    for variety in ('union', 'restricted-union'):
        inner = simple('B', '<xs:union memberTypes="xs:int xs:boolean"/>', 'union')
        if variety == 'restricted-union':
            inner = simple('U', '<xs:union memberTypes="xs:int xs:boolean"/>') + simple('B', '<xs:restriction base="t:U"/>', 'union')
        text = source(inner + simple('T', '<xs:union memberTypes="t:B"/>'))
        # Union composition in XSD 1.0 replaces the union with its actual atomic/list definitions.
        yield Case('composed-' + variety, text, True, xerces_valid=False,
                   xerces_reference=text.replace('final="union"', 'final=""'))
    content = simple('S', '<xs:restriction base="xs:int"/>', 'restriction') + '<xs:complexType name="B"><xs:simpleContent><xs:extension base="t:S"/></xs:simpleContent></xs:complexType><xs:complexType name="T"><xs:simpleContent><xs:restriction base="t:B"><xs:maxInclusive value="100"/></xs:restriction></xs:simpleContent></xs:complexType>'
    yield Case('simple-content-restriction-final', source(content), False, xerces_valid=True)
    yield Case('xml-whitespace', source(simple('T', '<xs:restriction base="xs:int"/>',
                                               ' &#9;restriction&#10;union&#13;restriction ')), True)


class TypeFinalTest(unittest.TestCase):
    def test_exclusions_and_values_in_both_bindings(self):
        models = list(definitions())
        self.assertEqual(87, len(models))
        self.assertEqual(44, sum(case.valid for case in models))
        self.assertEqual(len(models), len({case.name for case in models}))
        jobs = []
        compilers = {}
        cases = []
        for index, case in enumerate(models):
            with self.subTest(case=case.name):
                expected = case.valid if case.lxml_valid is None else case.lxml_valid
                if expected:
                    compilers[case.name] = etree.XMLSchema(etree.fromstring(case.schema.encode()))
                else:
                    with self.assertRaises(etree.XMLSchemaParseError):
                        etree.XMLSchema(etree.fromstring(case.schema.encode()))
                jobs.append(SchemaJob(case.name, f'http://example.invalid/final/{index}.xsd', case.schema.encode()))
            for version in ('11', '12'):
                cases.append({'name': case.name + '/' + version, 'schema': case.schema,
                              'wsdl': description(version, case.schema), 'binding': 'Soap' + version, 'value': case.value})
        oracle = run_independent(jobs)
        for case in models:
            expected = case.valid if case.xerces_valid is None else case.xerces_valid
            self.assertEqual(expected, oracle['schemas'][case.name]['ok'], (case.name, oracle['schemas'][case.name]))
            self.assertEqual([], oracle['schemas'][case.name]['warnings'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        with tempfile.TemporaryDirectory(prefix='wsdl-type-final-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(cases))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                      str(Path(__file__).with_name('type-final.qr')), str(path)],
                                     capture_output=True, text=True, timeout=180)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual('', process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        outputs = {}
        count = rejected = 0
        for case in models:
            for version in ('11', '12'):
                key = case.name + '/' + version
                if not case.valid:
                    row = next(rows)
                    count += 1
                    rejected += 1
                    self.assertEqual(key, row['name'])
                    self.assertEqual('WSDL-ERROR', row.get('error'), row)
                    self.assertEqual('XSD-SYNTAX-ERROR', row['native_error'], row)
                    continue
                for copy in (False, True):
                    for response in (False, True):
                        row = next(rows)
                        count += 1
                        self.assertEqual((key, copy, response), (row['name'], row.get('copy'), row.get('response')), row)
                        self.assertEqual('', row['native_error'], row)
                        self.assertEqual({'item': case.value}, row['value'], row)
                        envelope = etree.fromstring(row['xml'].encode())
                        soap = 'http://schemas.xmlsoap.org/soap/envelope/' if version == '11' else 'http://www.w3.org/2003/05/soap-envelope'
                        self.assertEqual(f'{{{soap}}}Envelope', envelope.tag)
                        payload = envelope.find(f'{{{soap}}}Body')[0]
                        self.assertEqual(f'{{{NS}}}' + ('Reply' if response else 'Submit'), payload.tag)
                        self.assertTrue(compilers[case.name].validate(payload), str(compilers[case.name].error_log))
                        outputs.setdefault(case.name, {})[f'{case.name}/{version}/{copy}/{response}'] = etree.tostring(payload)
        self.assertIsNone(next(rows, None))
        jobs = [SchemaJob(case.name, f'http://example.invalid/final/output/{index}.xsd',
                          (case.xerces_reference or case.schema).encode(), outputs[case.name])
                for index, case in enumerate(models) if case.valid]
        validated = run_independent(jobs)
        self.assertEqual(sum(map(len, outputs.values())), len(validated['documents']))
        for key, result in {**validated['schemas'], **validated['documents']}.items():
            self.assertTrue(result['ok'], (key, result))
            self.assertEqual([], result['warnings'])
        self.assertEqual((438, 86, 352), (count, rejected, len(validated['documents'])))
        print(f'{mode}: {len(models)} schemas, {count} rows, {rejected} construction errors, '
              f'{len(validated["documents"])} independently validated outputs', flush=True)


if __name__ == '__main__':
    unittest.main()
