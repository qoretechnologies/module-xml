#!/usr/bin/env python3
"""XSD declaration constraints and typed SOAP consumers.

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
from test_attribute_values import description, NS, XSD

BASE = "https://example.invalid/declaration-constraints/"
SIMPLE = '<xs:simpleType><xs:restriction base="xs:int"/></xs:simpleType>'
IDENTIFIER = '<xs:simpleType name="Identifier"><xs:restriction base="xs:ID"/></xs:simpleType>'


def record(content, name="Record"):
    return f'<xs:complexType name="{name}">{content}</xs:complexType>'


def local(content):
    return record('<xs:sequence>' + content + '</xs:sequence>')


def schema(body, roots=True):
    roots = ('<xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>'
             if roots else '')
    return f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{body}{roots}</xs:schema>'


def cases():
    sources, expected, errors = {}, {}, {}

    def add(name, body, valid=False, error="WSDL-ERROR"):
        sources[name], expected[name], errors[name] = schema(body), valid, error

    contradictions = {
        "type-simple": '<xs:element name="value" type="xs:int">' + SIMPLE + '</xs:element>',
        "type-complex": '<xs:element name="value" type="xs:int"><xs:complexType/></xs:element>',
        "both-inline": '<xs:element name="value">' + SIMPLE + '<xs:complexType/></xs:element>',
        "duplicate-simple": '<xs:element name="value">' + SIMPLE * 2 + '</xs:element>',
        "duplicate-complex": '<xs:element name="value"><xs:complexType/><xs:complexType/></xs:element>',
        "default-fixed": '<xs:element name="value" type="xs:int" default="0" fixed="0"/>',
        "named-simple": '<xs:element name="value"><xs:simpleType name="Invalid"><xs:restriction base="xs:int"/></xs:simpleType></xs:element>',
        "named-complex": '<xs:element name="value"><xs:complexType name="Invalid"/></xs:element>',
        "name-ref": '<xs:element name="value" ref="t:Submit"/>',
        "missing-name": '<xs:element type="xs:int"/>',
        "empty": '<xs:element/>',
        "empty-repeated": '<xs:element/><xs:element name="value" type="xs:int"/>',
    }
    for name, element in contradictions.items():
        add("local-" + name, local(element))
        add("global-" + name, record('') + element)
    for group in (False, True):
        for kind in ("sequence", "choice", "all"):
            for name in ("empty", "empty-repeated"):
                content = f'<xs:{kind}>{contradictions[name]}</xs:{kind}>'
                body = ('<xs:group name="G">' + content + '</xs:group>'
                        + record('<xs:group ref="t:G"/>') if group else record(content))
                add(f"nested-{group}-{kind}-{name}", body)
    for prop in ('type="xs:int"', 'nillable="true"', 'default="0"', 'fixed="0"',
                 'block="extension"', 'form="qualified"'):
        add("ref-" + prop, local('<xs:element ref="t:value" ' + prop + '/>')
            + '<xs:element name="value" type="xs:int"/>')
    for name, content in (("simple", SIMPLE), ("complex", '<xs:complexType/>'),
                          ("key", '<xs:key name="K"><xs:selector xpath="."/><xs:field xpath="@id"/></xs:key>')):
        add("ref-child-" + name, local('<xs:element ref="t:value">' + content + '</xs:element>')
            + '<xs:element name="value" type="xs:int"/>')
    for prop in ('form="qualified"', 'minOccurs="1"', 'maxOccurs="1"'):
        add("global-" + prop, record('') + '<xs:element name="value" type="xs:int" ' + prop + '/>')
    for prop in ('abstract="false"', 'final=""', 'substitutionGroup="t:Submit"'):
        add("local-" + prop, local('<xs:element name="value" type="xs:int" ' + prop + '/>'))
    for property_name in ("type", "ref"):
        attrs = ('name="value" ' if property_name == 'type' else '') + property_name + '=""'
        add("empty-" + property_name, local('<xs:element ' + attrs + '/>'), error="WSDL-NAMESPACE-ERROR")
    add("empty-simple", local('<xs:element name="value"><xs:simpleType/></xs:element>'),
        error="XSD-SIMPLETYPE-ERROR")
    for prop in ("nillable", "abstract"):
        for value in ("true", "false", "1", "0", " 1 ", "", "yes", "TRUE", "2"):
            element = f'<xs:element name="value" type="xs:int" {prop}="{value}"/>'
            body = local(element) if prop == 'nillable' else record('') + element
            add(f"boolean-{prop}-{value}", body, value in ("true", "false", "1", "0", " 1 "))
    for kind in ("element", "attribute"):
        for type_name in ("xs:ID", "t:Identifier"):
            for constraint in ("default", "fixed"):
                declaration = f'<xs:{kind} name="id" type="{type_name}" {constraint}="id1"/>'
                add(f"id-{kind}-{type_name}-{constraint}", IDENTIFIER + record('') + declaration)
        inline_id = f'<xs:{kind} name="id" default="id1"><xs:simpleType><xs:restriction base="t:Identifier"/></xs:simpleType></xs:{kind}>'
        add("id-inline-" + kind, IDENTIFIER + (local(inline_id) if kind == 'element' else record(inline_id)))
    content = record('<xs:simpleContent><xs:extension base="t:Identifier"/></xs:simpleContent>', "Content")
    add("id-simple-content", content + IDENTIFIER + record('')
        + '<xs:element name="id" type="t:Content" fixed="id1"/>')
    add("id-anonymous-content", IDENTIFIER + local('<xs:element name="id" fixed="id1"><xs:complexType>'
        '<xs:simpleContent><xs:extension base="t:Identifier"/></xs:simpleContent></xs:complexType></xs:element>'))
    first = '<xs:attribute name="first" type="xs:ID"/>'
    second = '<xs:attribute name="second" type="t:Identifier"/>'
    add("id-two-local", record(first + second) + IDENTIFIER)
    add("id-two-simple", record('<xs:simpleContent><xs:extension base="xs:string">' + first + second
                               + '</xs:extension></xs:simpleContent>') + IDENTIFIER)
    add("id-two-extension", record(first, "Base") + record('<xs:complexContent><xs:extension base="t:Base">'
        + second + '</xs:extension></xs:complexContent>') + IDENTIFIER)
    add("id-two-group", '<xs:attributeGroup name="G">' + first + '</xs:attributeGroup>'
        + record('<xs:attributeGroup ref="t:G"/>' + second) + IDENTIFIER)
    add("id-prohibited", record(first, "Base") + record('<xs:complexContent><xs:restriction base="t:Base">'
        '<xs:attribute name="first" use="prohibited"/></xs:restriction></xs:complexContent>'), True)
    add("id-and-ref", record(first + '<xs:attribute name="reference" type="xs:IDREF"/>'), True)
    add("idref-default", record('<xs:attribute name="reference" type="xs:IDREF" default="id1"/>'), True)
    add("inline-simple", local('<xs:element name="value">' + SIMPLE + '</xs:element>'), True)
    add("inline-empty-complex", local('<xs:element name="value"><xs:complexType/></xs:element>'), True)
    add("ref-annotation", '<xs:element name="value" type="xs:int"/>' + local('<xs:element ref="t:value" '
        'minOccurs="0" maxOccurs="2"><xs:annotation><xs:documentation>Account code</xs:documentation>'
        '</xs:annotation></xs:element>'), True)
    return sources, expected, errors


class DeclarationConstraintsTest(unittest.TestCase):
    def test_construction_matrix(self):
        sources, expected, errors = cases()
        jobs, worker_cases = [], []
        lxml_gaps = set()
        with tempfile.TemporaryDirectory(prefix="wsdl-declaration-constraints-") as temporary:
            root = Path(temporary)
            for index, (name, source) in enumerate(sources.items()):
                try:
                    etree.XMLSchema(etree.fromstring(source.encode()))
                    valid = True
                except etree.XMLSchemaParseError:
                    valid = False
                if valid != expected[name]:
                    lxml_gaps.add(name)
                jobs.append(SchemaJob(name, BASE + str(index) + '.xsd', source.encode()))
                for version in ("11", "12"):
                    path = root / f"{index}-{version}.wsdl"
                    path.write_text(description(version, source))
                    worker_cases.append({"name": name + "/" + version, "wsdl": str(path), "base": BASE,
                                         "operation": "submit", "binding": "Soap" + version, "messages": []})
            rows = survey.run_worker(worker_cases, {})
        # libxml2 misses ID derivation checks and rejects legal collapsed boolean whitespace.
        self.assertEqual({'boolean-nillable- 1 ', 'boolean-abstract- 1 ',
                          'id-attribute-t:Identifier-default', 'id-attribute-t:Identifier-fixed',
                          'id-element-t:Identifier-default', 'id-element-t:Identifier-fixed',
                          'id-inline-attribute', 'id-inline-element', 'id-simple-content', 'id-anonymous-content',
                          'id-two-local', 'id-two-simple', 'id-two-extension', 'id-two-group'}, lxml_gaps)
        self.assertEqual(94, len(sources))
        self.assertEqual(188, len(rows))
        self.assertEqual({c["name"] for c in worker_cases}, {r["case"] for r in rows})
        for row in rows:
            name = row["case"].rsplit("/", 1)[0]
            with self.subTest(case=row["case"]):
                self.assertEqual("parse", row["stage"])
                self.assertEqual(expected[name], row["ok"], row)
                if not row["ok"]:
                    self.assertEqual(errors[name], row["err"])
        oracle = run_independent(jobs)
        self.assertEqual(set(sources), set(oracle["schemas"]))
        # e-props-correct.5 also applies to the content type of a complex type.
        xerces_gaps = {'id-simple-content', 'id-anonymous-content'}
        for name, result in oracle["schemas"].items():
            with self.subTest(oracle=name):
                self.assertEqual(True if name in xerces_gaps else expected[name], result["ok"], result)

    def test_typed_values_and_reconstructed_consumers(self):
        source = schema(local('<xs:element name="count">' + SIMPLE + '</xs:element>'
                              '<xs:element name="active" type="xs:boolean" nillable="1"/>'))
        compiled = etree.XMLSchema(etree.fromstring(source.encode()))
        documents, expected = {}, {}
        cases = []
        with tempfile.TemporaryDirectory(prefix="wsdl-declaration-values-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                path = root / f"{version}.wsdl"
                path.write_text(description(version, source))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for variant in ("valid", "missing", "namespace"):
                        name = f"{version}/{direction}/{variant}"
                        count = '' if variant == "missing" else '<count>0</count>'
                        tag = 't:active' if variant == 'namespace' else 'active'
                        payload = f'<t:{wrapper} xmlns:t="{NS}">{count}<{tag}>false</{tag}></t:{wrapper}>'
                        documents[name], expected[name] = payload.encode(), variant == "valid"
                        self.assertEqual(expected[name], compiled.validate(etree.fromstring(documents[name])))
                        message = root / name.replace('/', '-')
                        message.write_text(f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{payload}</s:Body></s:Envelope>')
                        messages.append({"file": name, "path": str(message), "direction": direction})
                cases.append({"name": version, "wsdl": str(path), "base": BASE, "operation": "submit",
                              "binding": "Soap" + version, "messages": messages})
                process = subprocess.run(['qore', '--enable-debug',
                    str(Path(__file__).with_name('declaration-constraints.qr')), str(path), 'Soap' + version],
                    capture_output=True, text=True, timeout=30)
                self.assertEqual(0, process.returncode, process.stderr)
                self.assertEqual('', process.stderr)
                values = [json.loads(line) for line in process.stdout.splitlines()]
                self.assertEqual(4, len(values))
                for row in values:
                    self.assertIs(int, type(row['value']['count']))
                    self.assertIs(bool, type(row['value']['active']))
                    if row['kind'] == 'native':
                        self.assertEqual(0, row['value']['count'])
                        self.assertIs(False, row['value']['active'])
                    envelope = etree.fromstring(row['body'].encode())
                    self.assertEqual(f'{{{envelope_ns}}}Envelope', envelope.tag)
                    payload = envelope.find('{*}Body')[0]
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    self.assertEqual(['count', 'active'], [e.tag for e in payload])
                    self.assertEqual(str(row['value']['count']), payload[0].text)
                    self.assertEqual(str(row['value']['active']).lower(), payload[1].text)
                    name = f"{version}/{row['direction']}/{row['kind']}"
                    documents[name], expected[name] = etree.tostring(payload), True
            rows = survey.run_worker(cases, {})
        counts = survey.stage_accounting(cases, rows)['counts']
        self.assertEqual(4, counts['serialize']['ok'], rows)
        self.assertEqual(8, counts['deserialize']['failed'], rows)
        for row in rows:
            if row['stage'] == 'parse':
                self.assertTrue(row['ok'], row)
            elif not expected[row['file']]:
                self.assertFalse(row['ok'], row)
                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['err'])
            elif row['stage'] == 'deserialize':
                self.assertTrue(row['ok'], row)
            else:
                self.assertTrue(row['ok'], row)
                payload = etree.fromstring(row['body'].encode()).find('{*}Body')[0]
                self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                self.assertEqual(['count', 'active'], [e.tag for e in payload])
                self.assertEqual(['0', 'false'], [e.text for e in payload])
                documents[row['file'] + '/output'], expected[row['file'] + '/output'] = etree.tostring(payload), True
        self.assertEqual(24, len(documents))
        oracle = run_independent([SchemaJob('declarations', BASE + 'values.xsd', source.encode(), documents)])
        self.assertTrue(oracle['schemas']['declarations']['ok'], oracle)
        self.assertEqual(set(documents), set(oracle['documents']))
        for name, result in oracle['documents'].items():
            self.assertEqual(expected[name], result['ok'], (name, result))


if __name__ == '__main__':
    unittest.main()
