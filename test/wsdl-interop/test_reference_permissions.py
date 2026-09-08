#!/usr/bin/env python3
"""Per-source XSD import permissions and independent SOAP consumer checks.

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


BASE = "https://example.invalid/reference-permissions/"
FOREIGN = "urn:foreign"
FOREIGN_URI = BASE + "foreign.xsd"


def schema(body, ns=NS):
    target = f'targetNamespace="{ns}"' if ns else ""
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" xmlns:f="{FOREIGN}" {target}>'
            + body + '</xs:schema>')


def foreign():
    return schema('<xs:simpleType name="T"><xs:restriction base="xs:int"/></xs:simpleType>'
                  '<xs:complexType name="C"><xs:attribute name="flag" type="xs:boolean"/></xs:complexType>'
                  '<xs:element name="E" type="xs:int"/>'
                  '<xs:attribute name="A" type="xs:boolean" fixed="false"/>'
                  '<xs:group name="G"><xs:sequence><xs:element name="child" type="xs:int"/>'
                  '</xs:sequence></xs:group>'
                  '<xs:attributeGroup name="AG"><xs:attribute name="unit" type="xs:string"/>'
                  '</xs:attributeGroup>', FOREIGN)


class Resources(etree.Resolver):
    def __init__(self, resources):
        super().__init__()
        self.resources = resources

    def resolve(self, url, public_id, context):
        if url not in self.resources:
            raise OSError("resource unavailable offline: " + url)
        return self.resolve_string(self.resources[url], context, base_url=url)


def compile_schema(source, uri, resources):
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    parser.resolvers.add(Resources(resources))
    return etree.XMLSchema(etree.fromstring(source.encode(), parser, base_url=uri))


def schema_cases():
    declarations = {
        "element-type": '<xs:element name="value" type="f:T"/>',
        "simple-base": '<xs:simpleType name="Value"><xs:restriction base="f:T"/></xs:simpleType>',
        "list-item": '<xs:simpleType name="Value"><xs:list itemType="f:T"/></xs:simpleType>',
        "union-member": '<xs:simpleType name="Value"><xs:union memberTypes="xs:boolean f:T"/></xs:simpleType>',
        "complex-base": '<xs:complexType name="Value"><xs:complexContent><xs:extension base="f:C"/>'
                        '</xs:complexContent></xs:complexType>',
        "element-ref": '<xs:complexType name="Value"><xs:sequence><xs:element ref="f:E"/>'
                       '</xs:sequence></xs:complexType>',
        "attribute-ref": '<xs:complexType name="Value"><xs:attribute ref="f:A"/></xs:complexType>',
        "group-ref": '<xs:complexType name="Value"><xs:group ref="f:G"/></xs:complexType>',
        "attribute-group-ref": '<xs:complexType name="Value"><xs:attributeGroup ref="f:AG"/></xs:complexType>',
    }
    sources, expected, resources = {}, {}, {FOREIGN_URI: foreign()}
    for kind, declaration in declarations.items():
        for allowed in (False, True):
            name = f"{kind}-{allowed}"
            uri = BASE + name + ".xsd"
            local = schema((f'<xs:import namespace="{FOREIGN}"/>' if allowed else "") + declaration)
            resources[uri] = local
            # Preload the foreign components before the referencing document. Availability
            # does not replace that document's own import permission (src-resolve.4).
            sources[name] = schema(f'<xs:import namespace="{FOREIGN}" schemaLocation="{FOREIGN_URI}"/>'
                                   f'<xs:import namespace="{NS}" schemaLocation="{uri}"/>', "urn:master")
            expected[name] = allowed
    bare_uri = BASE + "bare.xsd"
    resources[bare_uri] = schema('<xs:simpleType name="T"><xs:restriction base="xs:int"/></xs:simpleType>', "")
    for allowed in (False, True):
        name = f"absent-{allowed}"
        uri = BASE + name + ".xsd"
        resources[uri] = schema(('<xs:import/>' if allowed else "") + '<xs:element name="value" type="T"/>')
        sources[name] = schema(f'<xs:import schemaLocation="{bare_uri}"/>'
                               f'<xs:import namespace="{NS}" schemaLocation="{uri}"/>', "urn:master")
        expected[name] = allowed
    empty_uri = BASE + "empty-namespace.xsd"
    resources[empty_uri] = schema('<xs:import namespace=""/><xs:element name="value" type="T"/>')
    sources["empty-namespace"] = schema(f'<xs:import schemaLocation="{bare_uri}"/>'
                                        f'<xs:import namespace="{NS}" schemaLocation="{empty_uri}"/>', "urn:master")
    expected["empty-namespace"] = False
    sources["empty-unused"] = schema('<xs:import namespace=""/>', "")
    expected["empty-unused"] = True
    sources["empty-target"] = schema(f'<xs:import schemaLocation="{bare_uri}"/>'
                                     f'<xs:import namespace="" schemaLocation="{bare_uri}"/>')
    expected["empty-target"] = False
    for label, value in (("empty", ""), ("whitespace", " ")):
        sources["declared-target-" + label] = (f'<xs:schema xmlns:xs="{XSD}" targetNamespace="{value}">'
                                               '<xs:element name="bad" type="xs:int"/></xs:schema>')
        expected["declared-target-" + label] = False
    middle_uri = BASE + "middle.xsd"
    resources[middle_uri] = schema(f'<xs:import namespace="{FOREIGN}" schemaLocation="{FOREIGN_URI}"/>',
                                   "urn:middle")
    for allowed in (False, True):
        name = f"transitive-{allowed}"
        uri = BASE + name + ".xsd"
        resources[uri] = schema('<xs:import namespace="urn:middle"/>'
                                + (f'<xs:import namespace="{FOREIGN}"/>' if allowed else "")
                                + '<xs:element name="value" type="f:T"/>')
        sources[name] = schema(f'<xs:import namespace="urn:middle" schemaLocation="{middle_uri}"/>'
                               f'<xs:import namespace="{NS}" schemaLocation="{uri}"/>', "urn:master")
        expected[name] = allowed
        name = f"include-{allowed}"
        uri = BASE + name + ".xsd"
        resources[uri] = schema((f'<xs:import namespace="{FOREIGN}"/>' if allowed else "")
                                + '<xs:element name="value" type="f:T"/>')
        sources[name] = schema(f'<xs:import namespace="{FOREIGN}" schemaLocation="{FOREIGN_URI}"/>'
                               f'<xs:include schemaLocation="{uri}"/>')
        expected[name] = allowed
    return sources, expected, resources


class ReferencePermissionsTest(unittest.TestCase):
    def test_component_and_source_scope_matrix(self):
        sources, expected, resources = schema_cases()
        cases, jobs = [], []
        with tempfile.TemporaryDirectory(prefix="wsdl-reference-permissions-") as temporary:
            root = Path(temporary)
            for name, source in sources.items():
                uri = BASE + name + "-master.xsd"
                try:
                    compile_schema(source, uri, resources)
                    valid = True
                except etree.XMLSchemaParseError:
                    valid = False
                # libxml2 omits src-resolve.4 checks on these already-loaded type references.
                lxml_gap = name in ("simple-base-False", "list-item-False", "union-member-False", "complex-base-False",
                                    "empty-target", "declared-target-empty", "declared-target-whitespace")
                self.assertEqual(expected[name] or lxml_gap, valid, name)
                path = root / (name + ".xsd")
                path.write_text(source)
                cases.append({"name": name, "wsdl": str(path), "schema_only": True,
                              "base": BASE, "messages": []})
                jobs.append(SchemaJob(name, uri, source.encode()))
            rows = survey.run_worker(cases, resources)
        self.assertEqual(29, len(sources))
        self.assertEqual(set(sources), {row["case"] for row in rows})
        self.assertEqual(29, len(rows))
        for row in rows:
            self.assertEqual(expected[row["case"]], row["ok"], row)
            if not row["ok"]:
                self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs, {uri: data.encode() for uri, data in resources.items()})
        self.assertEqual(set(sources), set(oracle["schemas"]))
        for name, result in oracle["schemas"].items():
            # Xerces conflates absent and explicitly empty namespace attributes. src-resolve.4.1
            # requires an absent attribute; src-import.3.1 requires a matching target attribute.
            warned_targets = {"declared-target-empty", "declared-target-whitespace"}
            self.assertEqual(expected[name] or name in {"empty-namespace", "empty-target", *warned_targets},
                             result["ok"], (name, result))
            if name in warned_targets:
                # Xerces diagnoses the forbidden target but reports a warning, not a validity error.
                # Qore's mandatory rejection above remains unchanged.
                self.assertEqual(1, len(result["warnings"]), (name, result))
                self.assertIn("EmptyTargetNamespace", result["warnings"][0])
                self.assertIn("cannot be an empty string", result["warnings"][0])
            else:
                self.assertEqual([], result["warnings"], (name, result))

    def test_imported_components_in_real_bindings_and_consumers(self):
        source = schema(f'<xs:import namespace="{FOREIGN}" schemaLocation="{FOREIGN_URI}"/>'
                        '<xs:complexType name="Record"><xs:group ref="f:G"/>'
                        '<xs:attribute ref="f:A" use="required"/></xs:complexType>'
                        '<xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>')
        resources = {FOREIGN_URI: foreign()}
        compiled = compile_schema(source, BASE + "local.xsd", resources)
        documents, expected, cases = {}, {}, []
        with tempfile.TemporaryDirectory(prefix="wsdl-reference-consumers-") as temporary:
            root = Path(temporary)
            foreign_path = root / "foreign.xsd"
            foreign_path.write_text(foreign())
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                path = root / f"{version}.wsdl"
                path.write_text(description(version, source))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for variant, attrs, child in (("valid", 'f:A="false"', '<child>0</child>'),
                                                  ("namespace", 'A="false"', '<child>0</child>'),
                                                  ("missing", 'f:A="false"', "")):
                        name = f"{version}/{direction}/{variant}"
                        payload_text = f'<t:{wrapper} xmlns:t="{NS}" xmlns:f="{FOREIGN}" {attrs}>{child}</t:{wrapper}>'
                        payload = etree.fromstring(payload_text.encode())
                        valid = variant == "valid"
                        self.assertEqual(valid, compiled.validate(payload), (name, str(compiled.error_log)))
                        documents[name], expected[name] = etree.tostring(payload), valid
                        message = root / name.replace("/", "-")
                        message.write_text(f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{payload_text}'
                                           '</s:Body></s:Envelope>')
                        messages.append({"file": name, "path": str(message), "direction": direction})
                cases.append({"name": version, "wsdl": str(path), "base": BASE, "operation": "submit",
                              "binding": "Soap" + version, "messages": messages})
                process = subprocess.run(["qore", "--enable-debug",
                                          str(Path(__file__).with_name("reference-permissions.qr")), str(path),
                                          "Soap" + version, str(foreign_path)], capture_output=True, text=True,
                                         check=True, timeout=30)
                self.assertEqual("", process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                self.assertEqual(4, len(rows))
                for row in rows:
                    self.assertIs(int, type(row["value"]["child"]))
                    self.assertIs(False, row["value"]["^attributes^"]["A"])
                    if row["kind"] == "native":
                        self.assertEqual(0, row["value"]["child"])
                    envelope = etree.fromstring(row["body"].encode())
                    self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                    payload = envelope.find("{*}Body")[0]
                    self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"), payload.tag)
                    self.assertEqual({f"{{{FOREIGN}}}A": "false"}, dict(payload.attrib))
                    self.assertEqual([("child", str(row["value"]["child"]))], [(c.tag, c.text) for c in payload])
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    name = f"{version}/{row['direction']}/{row['kind']}"
                    documents[name], expected[name] = etree.tostring(payload), True
            rows = survey.run_worker(cases, resources)
        counts = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(4, counts["serialize"]["ok"], rows)
        self.assertEqual(8, counts["deserialize"]["failed"], rows)
        for row in rows:
            if row["stage"] == "parse":
                self.assertTrue(row["ok"], row)
            elif not expected[row["file"]]:
                self.assertFalse(row["ok"], row)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
            else:
                self.assertTrue(row["ok"], row)
                if row["stage"] == "serialize":
                    version, direction, _ = row["file"].split("/")
                    envelope = etree.fromstring(row["body"].encode())
                    self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                    payload = envelope.find("{*}Body")[0]
                    self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
                    self.assertEqual({f"{{{FOREIGN}}}A": "false"}, dict(payload.attrib))
                    self.assertEqual([("child", "0")], [(c.tag, c.text) for c in payload])
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    documents[row["file"] + "/output"] = etree.tostring(payload)
                    expected[row["file"] + "/output"] = True
        self.assertEqual(24, len(documents))
        oracle = run_independent([SchemaJob("imported", BASE + "local.xsd", source.encode(), documents)],
                                 {uri: data.encode() for uri, data in resources.items()})
        self.assertEqual(set(documents), set(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertEqual(expected[name], result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
