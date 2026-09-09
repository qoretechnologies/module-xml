#!/usr/bin/env python3
"""Independent XSD QName enumeration declaration identity and derivation checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
from pathlib import Path
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
from test_facet_declarations import facet
import survey


@dataclass(frozen=True)
class Declaration:
    name: str
    parent: str
    own: str
    valid: bool
    attributes: str = ""


def enumeration(value, uri=None, prefix="p"):
    attributes = "" if uri is None else f' xmlns{":" + prefix if prefix else ""}="{uri}"'
    return facet("enumeration", value, attributes)


def declarations():
    for parent_uri in ("urn:one", "urn:two", "urn:a&amp;b", "urn:%41", "urn:A", "urn:%C3%A9", "urn:e%CC%81"):
        for child_uri in (parent_uri, "urn:other"):
            for prefix in ("p", "alias"):
                index = f"identity-{parent_uri}-{child_uri}-{prefix}"
                yield Declaration(index, enumeration("p:Name", parent_uri),
                                  enumeration(prefix + ":Name", child_uri, prefix), parent_uri == child_uri)
    parent = enumeration("p:Name", "urn:one")
    for local in ("Name", "name", "Other"):
        yield Declaration("local-" + local, parent, enumeration("a:" + local, "urn:one", "a"), local == "Name")
    yield Declaration("unicode-local-same", enumeration("p:é", "urn:one"),
                      enumeration("a:é", "urn:one", "a"), True)
    yield Declaration("unicode-local-distinct", enumeration("p:é", "urn:one"),
                      enumeration("a:e\u0301", "urn:one", "a"), False)
    for index, value in enumerate(("unbound:Name", "xmlns:Name", "", ":Name", "a:b:c", "0Name", "xml:")):
        yield Declaration("unbound-or-invalid-" + str(index), "", enumeration(value), False)
    for parent_xmlns, child_xmlns, valid in ((None, None, True), ("", "", True),
            ("urn:one", "urn:one", True), ("urn:one", "urn:two", False), ("urn:one", "", False)):
        yield Declaration(f"default-{parent_xmlns}-{child_xmlns}", enumeration("Name", parent_xmlns, ""),
                          enumeration("Name", child_xmlns, ""), valid)
    yield Declaration("default-to-alias", enumeration("Name", "urn:one", ""),
                      enumeration("a:Name", "urn:one", "a"), True)
    yield Declaration("inherited-default", parent, enumeration("Name"), True, 'xmlns="urn:one"')
    yield Declaration("facet-default-reset", enumeration("Name", "", ""), enumeration("Name", "", ""),
                      True, 'xmlns="urn:outer"')
    yield Declaration("implicit-xml", enumeration("xml:lang"), enumeration("xml:lang"), True)
    yield Declaration("implicit-xml-wrong-local", enumeration("xml:lang"), enumeration("xml:space"), False)
    yield Declaration("implicit-xml-vs-local", enumeration("xml:lang"), enumeration("lang"), False)
    both = parent + enumeration("p:Name", "urn:two")
    for uri in ("urn:one", "urn:two", "urn:three"):
        yield Declaration("duplicate-parent-" + uri, both, enumeration("a:Name", uri, "a"), uri != "urn:three")
    valid, invalid = enumeration("a:Name", "urn:one", "a"), enumeration("a:Name", "urn:three", "a")
    yield Declaration("duplicate-child-valid-first", both, valid + invalid, False)
    yield Declaration("duplicate-child-invalid-first", both, invalid + valid, False)
    yield Declaration("duplicate-child-same-value", both, valid + valid, True)
    yield Declaration("inherited-pattern-match", facet("pattern", "a:Name"), valid, True)
    yield Declaration("inherited-pattern-alias-reject", facet("pattern", "p:Name"), valid, False)
    yield Declaration("own-pattern-alias", parent, valid + facet("pattern", "p:Name"), True)
    yield Declaration("inherited-pattern-branches", facet("pattern", "a:Name") + facet("pattern", "p:Name"),
                      valid, True)
    yield Declaration("whitespace-collapse", parent, enumeration(" a:Name &#x9;&#xA;", "urn:one", "a"), True)
    for level in ("schema", "type", "restriction", "facet"):
        yield Declaration("namespace-scope-" + level, parent, enumeration("alias:Name"), True, level)


def schema(case, model):
    parent = f'<xs:simpleType name="Base"><xs:restriction base="xs:QName">{case.parent}</xs:restriction></xs:simpleType>'
    attributes = case.attributes
    own = case.own
    type_attributes = restriction_attributes = ""
    if attributes in ("schema", "type", "restriction", "facet"):
        binding = 'xmlns:alias="urn:one"'
        if attributes == "type":
            type_attributes = binding
        elif attributes == "restriction":
            restriction_attributes = binding
        elif attributes == "facet":
            own = own.replace("<xs:enumeration ", "<xs:enumeration " + binding + " ")
        attributes = binding if attributes == "schema" else ""
    if model == "simple-content":
        middle = '<xs:complexType name="BaseRecord"><xs:simpleContent><xs:extension base="t:Base"/></xs:simpleContent></xs:complexType>'
        child = f'''<xs:complexType name="Value" {type_attributes}><xs:simpleContent>
            <xs:restriction base="t:BaseRecord" {restriction_attributes}>{own}</xs:restriction>
            </xs:simpleContent></xs:complexType>'''
        definitions = parent + middle + child
    else:
        child = f'''<xs:simpleType name="Value" {type_attributes}><xs:restriction base="t:Base"
            {restriction_attributes}>{own}</xs:restriction></xs:simpleType>'''
        definitions = child + parent if model == "forward" else parent + child
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}" {attributes}>
        {definitions}<xs:element name="Submit" type="t:Value"/><xs:element name="Reply" type="t:Value"/>
        </xs:schema>'''.encode()


class QNameDeclarationsTest(unittest.TestCase):
    def test_declaration_identity_in_both_binding_contracts(self):
        jobs, cases, expected = [], [], {}
        definitions = list(declarations())
        self.assertEqual(66, len(definitions))
        with tempfile.TemporaryDirectory(prefix="wsdl-qname-declaration-context-") as temporary:
            for index, case in enumerate(definitions):
                for model in ("atomic", "forward", "simple-content"):
                    key = f"{index}-{model}"
                    source = schema(case, model)
                    expected[key] = case
                    jobs.append(SchemaJob(key, f"http://example.invalid/{key}.xsd", source))
                    try:
                        etree.XMLSchema(etree.fromstring(source))
                        accepted = True
                    except etree.XMLSchemaParseError:
                        accepted = False
                    self.assertEqual(case.valid, accepted, (case.name, model))
                    for version in ("11", "12"):
                        path = Path(temporary) / f"{key}-{version}.wsdl"
                        path.write_text(description(version, source.decode()))
                        cases.append({"name": key + "/" + version, "wsdl": str(path),
                                      "base": "http://example.invalid/", "operation": "submit",
                                      "binding": "Soap" + version, "messages": []})
            rows = survey.run_worker(cases, {})
        self.assertEqual(396, len(rows))
        self.assertEqual([case["name"] for case in cases], [row["case"] for row in rows])
        for row in rows:
            case = expected[row["case"].split("/")[0]]
            self.assertEqual("parse", row["stage"])
            self.assertEqual(case.valid, row["ok"], (case.name, row))
            if not case.valid:
                self.assertEqual("XSD-SIMPLETYPE-ERROR", row["err"])
        oracle = run_independent(jobs)
        self.assertEqual(set(expected), set(oracle["schemas"]))
        for key, case in expected.items():
            result = oracle["schemas"][key]
            if case.name == "unbound-or-invalid-1":
                # Xerces NamespaceSupport.reset() seeds xmlns as an ordinary binding.
                # Infoset 2.2 [in-scope namespaces] explicitly excludes this prefix.
                # Preserve this exact independent disagreement; libxml and WSDL reject it.
                self.assertFalse(case.valid)
                self.assertTrue(result["ok"], result)
                self.assertEqual("", result["desc"])
            else:
                self.assertEqual(case.valid, result["ok"], (case.name, result))
            self.assertEqual([], result["warnings"])


if __name__ == "__main__":
    unittest.main()
