#!/usr/bin/env python3
"""XSD 1.0 attribute wildcard composition and restriction admission.

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
from test_reference_permissions import compile_schema

BASE = "https://example.invalid/attribute-wildcards/"
FOREIGN = "urn:foreign"
FOREIGN_URI = BASE + "foreign.xsd"


def wildcard(namespaces="##any", processing="strict"):
    return f'<xs:anyAttribute namespace="{namespaces}" processContents="{processing}"/>'


def attribute(qualified=False):
    return ('<xs:attribute name="flag" type="xs:boolean" use="required" fixed="false"'
            + (' form="qualified"' if qualified else '') + '/>')


def record(content, name="Record"):
    return f'<xs:complexType name="{name}">{content}</xs:complexType>'


def restriction(content, base="t:Base", name="Record", simple=False):
    kind = "simpleContent" if simple else "complexContent"
    return record(f'<xs:{kind}><xs:restriction base="{base}">{content}</xs:restriction></xs:{kind}>', name)


def schema(body, namespace=NS, roots=True):
    attrs = f'targetNamespace="{namespace}"' if namespace else ''
    declarations = ('<xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>'
                    if roots else '')
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{namespace}" xmlns:f="{FOREIGN}" {attrs}>'
            + body + declarations + '</xs:schema>')


def derived(base_content, own, simple=False):
    if simple:
        base_content = '<xs:simpleContent><xs:extension base="xs:int">' + base_content + '</xs:extension></xs:simpleContent>'
    return record(base_content, "Base") + restriction(own, simple=simple)


def cases():
    sources, expected = {}, {}
    for simple in (False, True):
        for namespace, allowed in ((None, (False, False)), ("##any", (True, True)), ("##local", (True, False)),
                                   ("##targetNamespace", (False, True)), ("##other", (False, False)),
                                   ("##local ##targetNamespace", (True, True)), ("urn:foreign", (False, False)),
                                   ("", (False, False))):
            for qualified in (False, True):
                name = f"admission-{simple}-{namespace}-{qualified}"
                sources[name] = schema(derived(wildcard(namespace) if namespace is not None else '',
                                               attribute(qualified), simple))
                expected[name] = allowed[qualified]
    for name, base, own, valid in (
            ("wildcard-new", '', wildcard(), False),
            ("wildcard-removed", wildcard(), '', True),
            ("subset-valid", wildcard(), wildcard("##local"), True),
            ("subset-invalid", wildcard("##local"), wildcard(), False),
            ("subset-other", wildcard("##other"), wildcard("urn:foreign"), True),
            ("subset-other-local", wildcard("##other"), wildcard("##local"), False),
            ("subset-other-target", wildcard("##other"), wildcard("##targetNamespace"), False),
            ("subset-empty", wildcard("##other"), wildcard(""), True),
            ("subset-same-other", wildcard("##other"), wildcard("##other"), True)):
        sources[name], expected[name] = schema(derived(base, own)), valid
    for base in ("skip", "lax", "strict"):
        for own in ("skip", "lax", "strict"):
            name = f"processing-{base}-{own}"
            sources[name] = schema(derived(wildcard("##any", base), wildcard("##local", own)))
            expected[name] = ("skip", "lax", "strict").index(own) >= ("skip", "lax", "strict").index(base)
    for process in ("skip", "lax", "strict"):
        name = "ur-" + process
        sources[name], expected[name] = schema(restriction(wildcard("##any", process), "xs:anyType")), True
    for namespace in ("##any ##local", "##other ##targetNamespace", "##invalid"):
        name = "invalid-namespace-" + namespace
        sources[name], expected[name] = schema(record(wildcard(namespace))), False
    sources["invalid-processing"], expected["invalid-processing"] = schema(record(wildcard("##any", "invalid"))), False
    sources["duplicate-wildcard"], expected["duplicate-wildcard"] = schema(record(wildcard() + wildcard())), False
    groups = ('<xs:attributeGroup name="A">' + wildcard("##local ##targetNamespace", "skip")
              + '</xs:attributeGroup><xs:attributeGroup name="B">' + wildcard("##local", "strict")
              + '</xs:attributeGroup>')
    refs = '<xs:attributeGroup ref="t:A"/><xs:attributeGroup ref="t:B"/>'
    for qualified in (False, True):
        name = "intersection-" + str(qualified)
        sources[name], expected[name] = schema(groups + derived(refs, attribute(qualified))), not qualified
    for first, second, valid in (("##other", "##local", False), ("##other", "##targetNamespace", True),
                                 ("##other", "##local ##targetNamespace", True), ("##local", "##targetNamespace", True),
                                 ("##any", "##local", True), ("##other", "urn:foreign", True)):
        name = f"union-{first}-{second}"
        sources[name] = schema(record(wildcard(first), "Base")
                               + record('<xs:complexContent><xs:extension base="t:Base">' + wildcard(second)
                                        + '</xs:extension></xs:complexContent>'))
        expected[name] = valid
    for label, first, second in (("any", "##any", "##local"),
                                  ("other-set", "##other", "##targetNamespace ##local urn:foreign"),
                                  ("empty", "##local", "##targetNamespace"),
                                  ("same-other", "##other", "##other")):
        for qualified in (False, True):
            name = f"intersection-{label}-{qualified}"
            local_group = '<xs:attributeGroup name="G">' + wildcard(first) + '</xs:attributeGroup>'
            sources[name] = schema(local_group + derived('<xs:attributeGroup ref="t:G"/>' + wildcard(second),
                                                         attribute(qualified)))
            expected[name] = label == "any" and not qualified
    for first, second, allowed in (("skip", "strict", True), ("strict", "skip", False)):
        name = f"first-processing-{first}"
        groups = '<xs:attributeGroup name="A">' + wildcard("##local", first) + '</xs:attributeGroup>'
        groups += '<xs:attributeGroup name="B">' + wildcard("##local", second) + '</xs:attributeGroup>'
        sources[name] = schema(groups + derived('<xs:attributeGroup ref="t:A"/><xs:attributeGroup ref="t:B"/>',
                                                wildcard("##local", "lax")))
        expected[name] = allowed
    resources = {FOREIGN_URI: schema(record(wildcard("##other"), "Base")
                                     + '<xs:attributeGroup name="Other">' + wildcard("##other")
                                     + '</xs:attributeGroup>', FOREIGN, False)}
    imports = f'<xs:import namespace="{FOREIGN}" schemaLocation="{FOREIGN_URI}"/>'
    extension = record('<xs:complexContent><xs:extension base="f:Base">' + wildcard("##other")
                       + '</xs:extension></xs:complexContent>', "Base")
    for qualified in (False, True):
        name = "imported-union-" + str(qualified)
        sources[name], expected[name] = schema(imports + extension + restriction(attribute(qualified))), qualified
    sources["imported-intersection"] = schema(imports + record('<xs:attributeGroup ref="f:Other"/>' + wildcard("##other")))
    expected["imported-intersection"] = False
    sources["imported-subset-different"] = schema(imports + restriction(wildcard("##other"), "f:Base"))
    expected["imported-subset-different"] = False
    sources["subset-not-namespace-from-not-absent"] = schema(imports + extension + restriction(wildcard("##other")))
    expected["subset-not-namespace-from-not-absent"] = False
    bare_uri = BASE + "bare.xsd"
    resources[bare_uri] = f'<xs:schema xmlns:xs="{XSD}"><xs:attributeGroup name="Other">' + wildcard("##other") + '</xs:attributeGroup></xs:schema>'
    sources["intersection-not-absent"] = schema(f'<xs:import schemaLocation="{bare_uri}"/>'
                                               + derived('<xs:attributeGroup ref="Other"/>' + wildcard("##other"), attribute(True)))
    expected["intersection-not-absent"] = False
    return sources, expected, resources


class AttributeWildcardsTest(unittest.TestCase):
    def test_construction_matrix(self):
        sources, expected, resources = cases()
        jobs, worker_cases = [], []
        lxml_gaps = set()
        with tempfile.TemporaryDirectory(prefix="wsdl-attribute-wildcards-") as temporary:
            root = Path(temporary)
            for index, (name, source) in enumerate(sources.items()):
                uri = BASE + str(index) + '.xsd'
                try:
                    compile_schema(source, uri, resources)
                    valid = True
                except etree.XMLSchemaParseError:
                    valid = False
                if valid != expected[name]:
                    lxml_gaps.add(name)
                jobs.append(SchemaJob(name, uri, source.encode()))
                for version in ("11", "12"):
                    path = root / f"{index}-{version}.wsdl"
                    path.write_text(description(version, source))
                    worker_cases.append({"name": name + "/" + version, "wsdl": str(path), "base": BASE,
                                         "operation": "submit", "binding": "Soap" + version, "messages": []})
            rows = survey.run_worker(worker_cases, resources)
        self.assertEqual(82, len(sources))
        self.assertEqual(164, len(rows))
        # libxml2 wrongly admits no-namespace attributes into ##other and rejects
        # the empty set as a subset of ##other (cos-ns-subset.3.2.2).
        self.assertEqual({"subset-other-local", "subset-empty"}, lxml_gaps)
        self.assertEqual({c["name"] for c in worker_cases}, {r["case"] for r in rows})
        for row in rows:
            with self.subTest(case=row["case"]):
                self.assertEqual("parse", row["stage"])
                self.assertEqual(expected[row["case"].rsplit("/", 1)[0]], row["ok"], row)
                if not row["ok"]:
                    self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs, {uri: source.encode() for uri, source in resources.items()})
        self.assertEqual(set(sources), set(oracle["schemas"]))
        for name, result in oracle["schemas"].items():
            self.assertEqual(expected[name], result["ok"], (name, result))

    def test_restricted_attribute_values_and_consumers(self):
        jobs = []
        for simple in (False, True):
            for qualified in (False, True):
                source = schema(derived(wildcard("##any", "skip"), attribute(qualified), simple))
                compiled = etree.XMLSchema(etree.fromstring(source.encode()))
                worker_cases, documents, expected = [], {}, {}
                with tempfile.TemporaryDirectory(prefix="wsdl-wildcard-consumers-") as temporary:
                    root = Path(temporary)
                    for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                        path = root / f"{version}.wsdl"
                        path.write_text(description(version, source))
                        messages = []
                        for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                            for variant in ("valid", "namespace", "missing", "fixed"):
                                name = f"{simple}/{qualified}/{version}/{direction}/{variant}"
                                flag = ("t:" if qualified != (variant == "namespace") else "") + "flag"
                                attrs = '' if variant == 'missing' else f' {flag}="{str(variant == "fixed").lower()}"'
                                content = '0' if simple else ''
                                payload = f'<t:{wrapper} xmlns:t="{NS}"{attrs}>{content}</t:{wrapper}>'
                                documents[name], expected[name] = payload.encode(), variant == "valid"
                                self.assertEqual(expected[name], compiled.validate(etree.fromstring(documents[name])))
                                message = root / name.replace("/", "-")
                                message.write_text(f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{payload}'
                                                   '</s:Body></s:Envelope>')
                                messages.append({"file": name, "path": str(message), "direction": direction})
                        worker_cases.append({"name": version, "wsdl": str(path), "base": BASE,
                                             "operation": "submit", "binding": "Soap" + version, "messages": messages})
                        process = subprocess.run(["qore", "--enable-debug",
                                                  str(Path(__file__).with_name("attribute-wildcards.qr")), str(path),
                                                  "Soap" + version, str(simple).lower()], capture_output=True,
                                                 text=True, timeout=30)
                        self.assertEqual(0, process.returncode, process.stderr)
                        self.assertEqual("", process.stderr)
                        consumer_rows = [json.loads(line) for line in process.stdout.splitlines()]
                        self.assertEqual(4, len(consumer_rows))
                        for row in consumer_rows:
                            self.assertIs(False, row["value"]["^attributes^"]["flag"])
                            if simple:
                                self.assertIs(int, type(row["value"]["^value^"]))
                                if row["kind"] == "native":
                                    self.assertEqual(0, row["value"]["^value^"])
                            envelope = etree.fromstring(row["body"].encode())
                            self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                            payload = envelope.find("{*}Body")[0]
                            self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                            self.assertEqual({(f"{{{NS}}}" if qualified else "") + "flag": "false"}, dict(payload.attrib))
                            self.assertEqual(str(row["value"]["^value^"]) if simple else None, payload.text)
                            name = f"{simple}/{qualified}/{version}/{row['direction']}/{row['kind']}"
                            documents[name], expected[name] = etree.tostring(payload), True
                    rows = survey.run_worker(worker_cases, {})
                counts = survey.stage_accounting(worker_cases, rows)["counts"]
                self.assertEqual(4, counts["serialize"]["ok"], rows)
                self.assertEqual(12, counts["deserialize"]["failed"], rows)
                for row in rows:
                    if row["stage"] == "parse":
                        self.assertTrue(row["ok"], row)
                    elif not expected[row["file"]]:
                        self.assertFalse(row["ok"], row)
                        self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
                    elif row["stage"] == "deserialize":
                        self.assertTrue(row["ok"], row)
                    else:
                        self.assertTrue(row["ok"], row)
                        payload = etree.fromstring(row["body"].encode()).find("{*}Body")[0]
                        self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                        self.assertEqual({(f"{{{NS}}}" if qualified else "") + "flag": "false"}, dict(payload.attrib))
                        self.assertEqual('0' if simple else None, payload.text)
                        name = row["file"] + "/output"
                        documents[name], expected[name] = etree.tostring(payload), True
                self.assertEqual(28, len(documents))
                jobs.append((SchemaJob(f"{simple}-{qualified}", BASE + f"{simple}-{qualified}.xsd", source.encode(), documents), expected))
        oracle = run_independent([job for job, expected in jobs])
        expected = {name: value for job, expectation in jobs for name, value in expectation.items()}
        self.assertEqual(112, len(oracle["documents"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        for result in oracle["schemas"].values():
            self.assertTrue(result["ok"], result)
        for name, result in oracle["documents"].items():
            self.assertEqual(expected[name], result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
