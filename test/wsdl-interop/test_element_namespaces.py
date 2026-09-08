#!/usr/bin/env python3
"""Independent element namespace and alias checks in actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey
from test_attribute_values import description, NS, XSD


class ElementNamespacesTest(unittest.TestCase):
    def test_wildcard_element_names_and_retained_qname_bindings(self):
        schema = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
          <xs:complexType name="Record"><xs:sequence><xs:element name="payload"><xs:complexType>
            <xs:sequence><xs:any processContents="skip" maxOccurs="unbounded"/></xs:sequence>
          </xs:complexType></xs:element></xs:sequence></xs:complexType>
          <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
        </xs:schema>'''
        compiled = etree.XMLSchema(etree.fromstring(schema.encode()))
        cases, documents = [], {}
        with tempfile.TemporaryDirectory(prefix="wsdl-wildcard-namespaces-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                wsdl = root / f"soap{version}.wsdl"
                wsdl.write_text(description(version, schema))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    name = f"{version}/{direction}"
                    text = (f'<s:Envelope xmlns:s="{envelope_ns}" xmlns:t="{NS}"><s:Body>'
                            f'<t:{wrapper}><payload><a:item xmlns:a="urn:first" xmlns:qorexml0="urn:types" '
                            'kind="qorexml0:Specific">0</a:item><b:item xmlns:b="urn:second">false</b:item>'
                            f'<item/></payload></t:{wrapper}></s:Body></s:Envelope>')
                    path = root / name.replace("/", "-")
                    path.write_text(text)
                    payload = etree.fromstring(text.encode()).find("{*}Body")[0]
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    documents[name] = etree.tostring(payload)
                    messages.append({"file": name, "path": str(path), "direction": direction})
                cases.append({"name": "WildcardNames" + version, "wsdl": str(wsdl),
                              "base": "http://example.invalid/", "operation": "submit",
                              "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        self.assertEqual(4, survey.stage_accounting(cases, rows)["counts"]["serialize"]["ok"], rows)
        for row in rows:
            self.assertTrue(row["ok"], row)
            if row["stage"] != "serialize":
                continue
            version, direction = row["file"].split("/")
            envelope = etree.fromstring(row["body"].encode())
            self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
            payload = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
            self.assertTrue(compiled.validate(payload), str(compiled.error_log))
            self.assertEqual([("{urn:first}item", "0"), ("{urn:second}item", "false"), ("item", "")],
                             [(child.tag, child.text or "") for child in payload[0]])
            value = payload[0][0]
            self.assertEqual("qorexml0:Specific", value.attrib["kind"])
            self.assertEqual("urn:types", value.nsmap["qorexml0"])
            documents[row["file"] + "/output"] = etree.tostring(payload)
        results = run_independent([SchemaJob("wildcard-namespaces", "http://example.invalid/wildcards.xsd",
                                             schema.encode(), documents)])
        self.assertEqual(8, len(results["documents"]))
        for name, result in results["documents"].items():
            self.assertTrue(result["ok"], (name, result))

    def test_namespaces_and_aliases_in_both_bindings_and_directions(self):
        schema = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
          <xs:complexType name="Record"><xs:sequence>
            <xs:element name="value" type="xs:string" form="qualified" maxOccurs="3"/>
            <xs:element name="count" type="xs:int" form="unqualified"/>
          </xs:sequence></xs:complexType>
          <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
        </xs:schema>'''
        compiled = etree.XMLSchema(etree.fromstring(schema.encode()))
        cases, documents, expected, expected_values = [], {}, {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-element-namespaces-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                wsdl = root / f"soap{version}.wsdl"
                wsdl.write_text(description(version, schema))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    variants = {
                        "aliases": (f'<t:{wrapper} xmlns:a="{NS}" xmlns:b="{NS}">'
                                    '<a:value/><b:value>0</b:value><t:value>false</t:value>'
                                    f'<count>0</count></t:{wrapper}>', True, ["", "0", "false"]),
                        "default": (f'<{wrapper} xmlns="{NS}"><value>zero</value>'
                                    f'<count xmlns="">0</count></{wrapper}>', True, ["zero"]),
                        "rebound": (f'<p:{wrapper} xmlns:p="{NS}"><p:value>zero</p:value>'
                                    f'<count>0</count></p:{wrapper}>', True, ["zero"]),
                        "wrong-root": (f'<p:{wrapper}><t:value>zero</t:value>'
                                       f'<count>0</count></p:{wrapper}>', False, []),
                        "absent-root-ns": (f'<{wrapper}><t:value>zero</t:value>'
                                           f'<count>0</count></{wrapper}>', False, []),
                        "wrong-child": (f'<t:{wrapper}><p:value>zero</p:value>'
                                        f'<count>0</count></t:{wrapper}>', False, []),
                        "absent-child-ns": (f'<t:{wrapper}><value>zero</value>'
                                            f'<count>0</count></t:{wrapper}>', False, []),
                        "qualified-local": (f'<t:{wrapper}><t:value>zero</t:value>'
                                            f'<t:count>0</t:count></t:{wrapper}>', False, []),
                        "wrong-alias": (f'<t:{wrapper}><t:value>0</t:value><p:value>false</p:value>'
                                        f'<count>0</count></t:{wrapper}>', False, []),
                    }
                    for variant, (payload_text, valid, values) in variants.items():
                        name = f"{version}/{direction}/{variant}"
                        text = (f'<s:Envelope xmlns:s="{envelope_ns}" xmlns:t="{NS}" xmlns:p="urn:wrong">'
                                f'<s:Body>{payload_text}</s:Body></s:Envelope>')
                        payload = etree.fromstring(text.encode()).find("{*}Body")[0]
                        self.assertEqual(valid, compiled.validate(payload), (name, str(compiled.error_log)))
                        documents[name], expected[name] = etree.tostring(payload), valid
                        expected_values[name] = values
                        path = root / name.replace("/", "-")
                        path.write_text(text)
                        messages.append({"file": name, "path": str(path), "direction": direction})
                cases.append({"name": "Elements" + version, "wsdl": str(wsdl),
                              "base": "http://example.invalid/", "operation": "submit",
                              "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        counts = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(2, counts["parse"]["ok"], rows)
        self.assertEqual(12, counts["serialize"]["ok"], rows)
        self.assertEqual(24, counts["deserialize"]["failed"], rows)
        for row in rows:
            if row["stage"] == "parse":
                self.assertTrue(row["ok"], row)
                continue
            if not expected[row["file"]]:
                self.assertFalse(row["ok"], row)
                self.assertEqual("deserialize", row["stage"])
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
                continue
            self.assertTrue(row["ok"], row)
            if row["stage"] != "serialize":
                continue
            version, direction, _ = row["file"].split("/")
            envelope = etree.fromstring(row["body"].encode())
            self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
            payload = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
            self.assertTrue(compiled.validate(payload), str(compiled.error_log))
            self.assertEqual([(f"{{{NS}}}value", value) for value in expected_values[row["file"]]]
                             + [("count", "0")], [(child.tag, child.text or "") for child in payload])
            name = row["file"] + "/output"
            documents[name], expected[name] = etree.tostring(payload), True
        results = run_independent([SchemaJob("element-namespaces", "http://example.invalid/elements.xsd",
                                             schema.encode(), documents)])
        self.assertEqual(48, len(results["documents"]))
        for name, valid in expected.items():
            self.assertEqual(valid, results["documents"][name]["ok"], (name, results["documents"][name]))


if __name__ == "__main__":
    unittest.main()
