#!/usr/bin/env python3
"""The examples of WSDL message providers are schema-valid messages.

Copyright (C) 2026 Qore Technologies, s.r.o.

The data provider types of a WSDL operation's messages produce example values, which applications use as request
templates and to simulate responses. For every builtin type a SOAP message can carry and for a restriction by each
kind of constraining facet, the module serializes the input and output message examples as SOAP 1.1 and 1.2
messages, and both independent validators, the pinned Xerces-J and libxml2, must accept every payload.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NS = "urn:examples"
XSD = "http://www.w3.org/2001/XMLSchema"
SOAP_ENVELOPES = {"11": "http://schemas.xmlsoap.org/soap/envelope/", "12": "http://www.w3.org/2003/05/soap-envelope"}

# ENTITY and ENTITIES values name unparsed entities declared in a DTD, which SOAP messages cannot have
BUILTINS = ("string", "normalizedString", "token", "language", "Name", "NCName", "NMTOKEN", "NMTOKENS", "ID",
            "IDREF", "IDREFS", "QName", "anyURI", "boolean", "decimal", "integer", "nonPositiveInteger",
            "negativeInteger", "long", "int", "short", "byte", "nonNegativeInteger", "unsignedLong", "unsignedInt",
            "unsignedShort", "unsignedByte", "positiveInteger", "float", "double", "duration", "dateTime", "time",
            "date", "gYearMonth", "gYear", "gMonthDay", "gDay", "gMonth", "hexBinary", "base64Binary",
            "anySimpleType")

RESTRICTIONS = {
    "decimal_bounds": '<xs:restriction base="xs:decimal"><xs:minExclusive value="999.5"/>'
                      '<xs:maxInclusive value="1000"/></xs:restriction>',
    "decimal_digits": '<xs:restriction base="xs:decimal"><xs:totalDigits value="4"/><xs:fractionDigits value="2"/>'
                      '<xs:minInclusive value="10"/></xs:restriction>',
    "decimal_enumeration": '<xs:restriction base="xs:decimal"><xs:enumeration value="-2.50"/></xs:restriction>',
    "integer_max": '<xs:restriction base="xs:integer"><xs:maxExclusive value="-100000000000000000000"/>'
                   '</xs:restriction>',
    "short_range": '<xs:restriction base="xs:short"><xs:minInclusive value="-7"/><xs:maxInclusive value="-3"/>'
                   '</xs:restriction>',
    "positive_pattern": '<xs:restriction base="xs:positiveInteger"><xs:pattern value="9[0-9]{5}"/>'
                        '</xs:restriction>',
    "float_max": '<xs:restriction base="xs:float"><xs:maxExclusive value="-1E30"/></xs:restriction>',
    "double_pattern": '<xs:restriction base="xs:double"><xs:pattern value="[0-9]\\.[0-9]+E-[0-9]"/>'
                      '</xs:restriction>',
    "string_length": '<xs:restriction base="xs:string"><xs:length value="7"/></xs:restriction>',
    "string_range": '<xs:restriction base="xs:string"><xs:minLength value="30"/><xs:maxLength value="31"/>'
                    '</xs:restriction>',
    "string_pattern": '<xs:restriction base="xs:string"><xs:pattern value="[A-Z]{2}[0-9]{3}(-[a-z])?"/>'
                      '</xs:restriction>',
    "string_enumeration": '<xs:restriction base="xs:string"><xs:enumeration value="Blue Moon"/></xs:restriction>',
    "token_max": '<xs:restriction base="xs:token"><xs:maxLength value="1"/></xs:restriction>',
    "language_pattern": '<xs:restriction base="xs:language"><xs:pattern value="[a-z]{2}-[A-Z]{2}"/>'
                        '</xs:restriction>',
    "name_length": '<xs:restriction base="xs:Name"><xs:minLength value="9"/></xs:restriction>',
    "nmtokens_length": '<xs:restriction base="xs:NMTOKENS"><xs:length value="2"/></xs:restriction>',
    "uri_pattern": '<xs:restriction base="xs:anyURI"><xs:pattern value="urn:isbn:[0-9]{3}"/></xs:restriction>',
    "date_min": '<xs:restriction base="xs:date"><xs:minInclusive value="2090-06-30"/></xs:restriction>',
    "datetime_max": '<xs:restriction base="xs:dateTime"><xs:maxExclusive value="1900-01-01T00:00:00Z"/>'
                    '</xs:restriction>',
    "time_pattern": '<xs:restriction base="xs:time"><xs:pattern value="1[0-9]:.*"/></xs:restriction>',
    "gmonthday_enumeration": '<xs:restriction base="xs:gMonthDay"><xs:enumeration value="--12-24"/>'
                             '</xs:restriction>',
    "duration_min": '<xs:restriction base="xs:duration"><xs:minInclusive value="P20Y"/></xs:restriction>',
    "hex_length": '<xs:restriction base="xs:hexBinary"><xs:length value="3"/></xs:restriction>',
    "base64_min": '<xs:restriction base="xs:base64Binary"><xs:minLength value="9"/></xs:restriction>',
    "qname_enumeration": '<xs:restriction base="xs:QName"><xs:enumeration value="t:sky"/></xs:restriction>',
    "boolean_pattern": '<xs:restriction base="xs:boolean"><xs:pattern value="false"/></xs:restriction>',
    "int_list": '<xs:list itemType="xs:int"/>',
    "date_list_length": '<xs:restriction><xs:simpleType><xs:list itemType="xs:date"/></xs:simpleType>'
                        '<xs:length value="2"/></xs:restriction>',
    "union": '<xs:union memberTypes="xs:gYear xs:boolean"/>',
    "union_pattern": '<xs:restriction><xs:simpleType><xs:union memberTypes="xs:int xs:date"/></xs:simpleType>'
                     '<xs:pattern value="[0-9]{4}-.*"/></xs:restriction>',
}


def schema_text():
    types = "".join(f'<xs:simpleType name="{name}">{body}</xs:simpleType>' for name, body in RESTRICTIONS.items())
    fields = "".join(f'<xs:element name="f_{name}" type="xs:{name}"/>' for name in BUILTINS)
    fields += "".join(f'<xs:element name="r_{name}" type="t:{name}"/>' for name in RESTRICTIONS)
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}" elementFormDefault="qualified">'
            f'{types}<xs:element name="record"><xs:complexType><xs:sequence>{fields}</xs:sequence></xs:complexType>'
            f'</xs:element></xs:schema>')


def wsdl_text(schema):
    bindings, ports = "", ""
    for version, soap in (("11", "http://schemas.xmlsoap.org/wsdl/soap/"),
                          ("12", "http://schemas.xmlsoap.org/wsdl/soap12/")):
        bindings += (f'<binding name="B{version}" type="t:P"><s{version}:binding style="document" '
                     f'transport="http://schemas.xmlsoap.org/soap/http"/><operation name="put">'
                     f'<s{version}:operation soapAction=""/><input><s{version}:body use="literal"/></input>'
                     f'<output><s{version}:body use="literal"/></output></operation></binding>')
        ports += (f'<port name="p{version}" binding="t:B{version}"><s{version}:address '
                  f'location="http://localhost/examples{version}"/></port>')
    return ('<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:s11="http://schemas.xmlsoap.org/wsdl/soap/" '
            'xmlns:s12="http://schemas.xmlsoap.org/wsdl/soap12/" '
            f'xmlns:t="{NS}" targetNamespace="{NS}"><types>{schema}</types>'
            '<message name="m"><part name="body" element="t:record"/></message>'
            '<portType name="P"><operation name="put"><input message="t:m"/><output message="t:m"/></operation>'
            f'</portType>{bindings}<service name="S">{ports}</service></definitions>')


class ProviderExamplesTest(unittest.TestCase):
    def test_message_examples_are_schema_valid(self):
        schema = schema_text().encode()
        documents = {}
        with tempfile.TemporaryDirectory(prefix="provider-examples-") as temp:
            path = Path(temp) / "examples.wsdl"
            path.write_text(wsdl_text(schema.decode()))
            env = dict(os.environ, QORE_MODULE_DIR=os.pathsep.join(
                (str(REPO / "build-debug"), str(REPO / "qlib"), os.environ.get("QORE_MODULE_DIR", ""))))
            for version in ("11", "12"):
                result = subprocess.run([os.environ.get("QORE", "qore"), "-b", "--enable-debug",
                                         str(HERE / "provider-examples.qr"), str(path), f"B{version}", "put"],
                                        capture_output=True, text=True, env=env, timeout=300)
                self.assertEqual((0, ""), (result.returncode, result.stderr), result.stdout)
                output = json.loads(result.stdout)
                self.assertNotIn("error", output)
                for direction in ("request", "response"):
                    envelope = etree.fromstring(output[direction].encode())
                    self.assertEqual(f"{{{SOAP_ENVELOPES[version]}}}Envelope", envelope.tag)
                    payload = envelope.find(f"{{{SOAP_ENVELOPES[version]}}}Body")[0]
                    self.assertEqual(f"{{{NS}}}record", payload.tag)
                    # every declared field, in order, carries a value
                    self.assertEqual([f"{{{NS}}}f_{name}" for name in BUILTINS]
                                     + [f"{{{NS}}}r_{name}" for name in RESTRICTIONS],
                                     [child.tag for child in payload])
                    documents[f"{version}/{direction}"] = etree.tostring(payload)
        self.assertEqual(4, len(documents))
        validator = etree.XMLSchema(etree.fromstring(schema))
        for name, document in documents.items():
            with self.subTest(document=name):
                self.assertTrue(validator.validate(etree.fromstring(document)), str(validator.error_log))
        oracle = run_independent([SchemaJob("examples", f"{NS}.xsd", schema, documents)])
        self.assertTrue(oracle["schemas"]["examples"]["ok"], oracle["schemas"]["examples"])
        self.assertEqual(set(documents), set(oracle["documents"]))
        for name, result in oracle["documents"].items():
            with self.subTest(xerces=name):
                self.assertTrue(result["ok"], result)
                self.assertEqual([], result["warnings"])


if __name__ == "__main__":
    unittest.main()
