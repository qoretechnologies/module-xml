#!/usr/bin/env python3
"""Generated WSDL SOAP bindings produce and accept the messages WSDL 1.1 section 3.5 describes.

Copyright (C) 2026 Qore Technologies, s.r.o.

A seeded generator writes WSDL documents with SOAP 1.1 and 1.2 bindings in the document/literal, RPC/literal and
RPC/encoded styles, the style declared on the binding or on the operation, soap:body namespaces, body parts selected
with the parts attribute, header parts, SOAP actions, and element or type parts with simple and complex types. For
each, the module serializes a request and a response, which must have the structure WSDL 1.1 section 3.5 and the SOAP
encoding define, derived independently here from the generated description: document parts as the Body's children in
part order; an RPC wrapper named by the operation (and "Response") in the soap:body namespace, holding one unqualified
accessor per part in part order; encoded messages with the encodingStyle and each accessor's xsi:type; header parts in
the Header; and the content type and action of each SOAP version. A request built here with other prefixes must decode
to the generated values, and its mutations (a wrong wrapper name or namespace, a missing, extra or qualified accessor,
a missing or unknown document part) must be rejected. The seed and a digest of the generated cases are pinned.
"""
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

from lxml import etree

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SEED = 20260928
COUNT = 120
XSD = "http://www.w3.org/2001/XMLSchema"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
TYPES_NS = "urn:gen:xsd"
ENVELOPES = {"11": "http://schemas.xmlsoap.org/soap/envelope/", "12": "http://www.w3.org/2003/05/soap-envelope"}
ENCODINGS = {"11": "http://schemas.xmlsoap.org/soap/encoding/", "12": "http://www.w3.org/2003/05/soap-encoding"}
BINDING_NS = {"11": "http://schemas.xmlsoap.org/wsdl/soap/", "12": "http://schemas.xmlsoap.org/wsdl/soap12/"}
SIMPLE = ("string", "int", "boolean", "decimal", "date")
OPERATIONS = ("submit", "getQuote", "Update_Item", "cancel2")
PART_NAMES = ("amount", "customerName", "a1", "flag", "when", "note")
MUTATIONS = {
    "rpc": {
        "wrapper-name": "WSDL 1.1 section 3.5: the RPC wrapper is named after the operation",
        "wrapper-namespace": "WSDL 1.1 section 3.5: the RPC wrapper is in the soap:body namespace",
        "missing-accessor": "an omitted accessor is an absent value (SOAP 1.1 section 5.1, SOAP 1.2 Part 2 section "
                            "3.1.3; for literal messages decided 2026-09-25); tested separately",
        "extra-accessor": "WS-I BP R2735 (literal) and the operation signature: no undeclared accessors",
        "qualified-accessor": "WS-I BP R2735: a literal type part's accessor has no namespace; encoded accessors may "
                              "be qualified (SOAP 1.1 section 7.1, SOAP 1.2 Primer)",
    },
    "document": {
        "missing-part": "WSDL 1.1 section 3.5: each body part appears as its element",
        "unknown-part": "WS-I BP R2712: the Body carries only the described part elements",
    },
}
# the SHA-256 of the generated cases; see test_generator_is_pinned
CASES_SHA256 = "69f622f7d4f7a4269a547e1d985854a60bcb7baf0c4a553f14e60a13d3839ccf"


def lexical(rng, datatype):
    if datatype == "string":
        return "".join(rng.choice("abcdefgh XYZ-") for _ in range(rng.randrange(1, 12))).strip() or "s"
    if datatype == "int":
        return str(rng.randrange(-100000, 100000))
    if datatype == "boolean":
        return rng.choice(("true", "false"))
    if datatype == "decimal":
        return f"{rng.randrange(-9999, 9999)}.{rng.randrange(1, 99):02d}".rstrip("0")
    return f"{rng.randrange(2000, 2031)}-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}"


def same(datatype, expected, actual):
    """Compares lexical values by their value (XSD 1.0 Part 2)."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(expected) == set(actual) and \
            all(same(datatype[name], expected[name], actual[name]) for name in expected)
    if actual is None:
        return False
    if datatype == "decimal":
        return Decimal(expected) == Decimal(actual)
    if datatype == "int":
        return int(expected) == int(actual)
    if datatype == "date":
        return actual.startswith(expected)
    return expected == actual


class Description:
    """One generated WSDL with one binding and operation."""

    def __init__(self, rng, index):
        self.rng, self.index = rng, index
        self.version = rng.choice(("11", "12"))
        self.style = rng.choice(("document", "rpc", "rpc"))
        self.use = "encoded" if self.style == "rpc" and rng.random() < 0.4 else "literal"
        self.style_on_operation = rng.random() < 0.5
        self.operation = rng.choice(OPERATIONS)
        self.action = rng.choice(("", f"urn:gen:action:{index}"))
        self.rpc_ns = f"urn:gen:rpc:{index}"
        self.complex_fields = {"code": rng.choice(SIMPLE), "count": "int"}
        names = rng.sample(PART_NAMES, rng.choice((1, 2, 3)))
        # document parts are elements; RPC parts are types (WS-I BP R2203, R2204)
        self.parts = {"input": [], "output": []}
        for direction in ("input", "output"):
            for name in (names if direction == "input" else rng.sample(PART_NAMES, rng.choice((1, 2)))):
                datatype = rng.choice(SIMPLE + ("complex",))
                self.parts[direction].append({"name": name, "type": datatype,
                                              "element": f"{name}E{index}{direction[0]}"})
        self.header = {"name": "hdr", "element": f"Hdr{index}", "type": "string"} if rng.random() < 0.3 else None

    def values(self, rng, direction):
        values = {}
        for part in self.parts[direction]:
            if part["type"] == "complex":
                values[part["name"]] = {field: lexical(rng, datatype) for field, datatype in self.complex_fields.items()}
            else:
                values[part["name"]] = lexical(rng, part["type"])
        return values

    def types(self, direction):
        return {part["name"]: (self.complex_fields if part["type"] == "complex" else part["type"])
                for part in self.parts[direction]}

    def wsdl(self):
        v = self.version
        elements = ""
        for direction in ("input", "output"):
            for part in self.parts[direction]:
                elements += f'<xsd:element name="{part["element"]}" type="{self.xsd_type(part["type"])}"/>'
        if self.header:
            elements += f'<xsd:element name="{self.header["element"]}" type="xsd:string"/>'
        complex_type = ('<xsd:complexType name="Rec"><xsd:sequence>'
                        + "".join(f'<xsd:element name="{field}" type="xsd:{datatype}"/>'
                                  for field, datatype in self.complex_fields.items())
                        + '</xsd:sequence></xsd:complexType>')
        messages = ""
        for direction, message in (("input", "In"), ("output", "Out")):
            parts = ""
            for part in self.parts[direction]:
                if self.style == "document":
                    parts += f'<part name="{part["name"]}" element="x:{part["element"]}"/>'
                else:
                    parts += f'<part name="{part["name"]}" type="{self.xsd_type(part["type"])}"/>'
            if self.header and direction == "input":
                parts += f'<part name="hdr" element="x:{self.header["element"]}"/>'
            messages += f'<message name="{message}">{parts}</message>'
        body_attributes = f'use="{self.use}"'
        if self.style == "rpc":
            body_attributes += f' namespace="{self.rpc_ns}"'
        if self.use == "encoded":
            body_attributes += f' encodingStyle="{ENCODINGS[v]}"'
        input_body = f'<soap:body {body_attributes}'
        header = ""
        if self.header:
            input_body += ' parts="' + " ".join(part["name"] for part in self.parts["input"]) + '"'
            header = '<soap:header message="t:In" part="hdr" use="literal"/>'
        style_binding = "" if self.style_on_operation else f' style="{self.style}"'
        style_operation = f' style="{self.style}"' if self.style_on_operation else ""
        return (f'<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:soap="{BINDING_NS[v]}" '
                f'xmlns:xsd="{XSD}" xmlns:x="{TYPES_NS}" xmlns:t="urn:gen" targetNamespace="urn:gen">'
                f'<types><xsd:schema targetNamespace="{TYPES_NS}" elementFormDefault="qualified">{complex_type}'
                f'{elements}</xsd:schema></types>{messages}'
                f'<portType name="P"><operation name="{self.operation}"><input message="t:In"/>'
                f'<output message="t:Out"/></operation></portType>'
                f'<binding name="B" type="t:P"><soap:binding{style_binding} '
                f'transport="http://schemas.xmlsoap.org/soap/http"/><operation name="{self.operation}">'
                f'<soap:operation soapAction="{self.action}"{style_operation}/>'
                f'<input>{input_body}/>{header}</input><output><soap:body {body_attributes}/></output>'
                f'</operation></binding><service name="S"><port name="p" binding="t:B">'
                f'<soap:address location="http://localhost/gen{self.index}"/></port></service></definitions>')

    @staticmethod
    def xsd_type(datatype):
        return "x:Rec" if datatype == "complex" else f"xsd:{datatype}"

    def request(self, values, header_value, mutation=None):
        """Builds a request envelope from the WSDL 1.1 section 3.5 rules, with prefixes the module does not use."""
        v = self.version
        env = f'e{self.index % 7}'
        body = ""
        parts = list(self.parts["input"])
        if mutation == "missing-part" or mutation == "missing-accessor":
            parts = parts[:-1]
        for part in parts:
            value = values[part["name"]]
            if self.style == "document":
                content = self.content(part, value, "y")
                body += f'<y:{part["element"]}>{content}</y:{part["element"]}>'
            else:
                name = part["name"]
                qualified = mutation == "qualified-accessor" and part is parts[0]
                tag = f"w:{name}" if qualified else name
                type_attribute = ""
                if self.use == "encoded":
                    type_attribute = f' i:type="{"y:Rec" if part["type"] == "complex" else "d:" + part["type"]}"'
                body += f"<{tag}{type_attribute}>{self.content(part, value, 'y')}</{tag}>"
        if mutation == "extra-accessor":
            body += "<undeclared>1</undeclared>"
        if mutation == "unknown-part":
            body += f"<y:unknownPart{self.index}>1</y:unknownPart{self.index}>"
        if self.style == "rpc":
            local = self.operation + ("X" if mutation == "wrapper-name" else "")
            namespace = "urn:gen:other" if mutation == "wrapper-namespace" else self.rpc_ns
            encoding = f' {env}:encodingStyle="{ENCODINGS[v]}"' if self.use == "encoded" else ""
            body = f'<w:{local} xmlns:w="{namespace}"{encoding}>{body}</w:{local}>'
        header = ""
        if self.header:
            header = f'<{env}:Header><y:{self.header["element"]}>{header_value}</y:{self.header["element"]}></{env}:Header>'
        return (f'<{env}:Envelope xmlns:{env}="{ENVELOPES[v]}" xmlns:y="{TYPES_NS}" xmlns:d="{XSD}" '
                f'xmlns:i="{XSI}">{header}<{env}:Body>{body}</{env}:Body></{env}:Envelope>')

    def content(self, part, value, prefix):
        if part["type"] != "complex":
            return value
        return "".join(f"<{prefix}:{field}>{value[field]}</{prefix}:{field}>" for field in self.complex_fields)


def generate():
    rng = random.Random(SEED)
    cases = []
    for index in range(COUNT):
        description = Description(rng, index)
        values = {"input": description.values(rng, "input"), "output": description.values(rng, "output")}
        header_value = f"h{index}" if description.header else None
        incoming = [description.request(values["input"], header_value)]
        mutations = list(MUTATIONS[description.style])
        if description.style == "document" and len(description.parts["input"]) < 2:
            mutations.remove("missing-part")
        if description.style == "rpc" and len(description.parts["input"]) < 2:
            mutations.remove("missing-accessor")
        incoming += [description.request(values["input"], header_value, mutation) for mutation in mutations]
        input_values = dict(values["input"])
        if description.header:
            input_values["hdr"] = header_value
        cases.append({"id": f"binding-{index}", "version": description.version, "style": description.style,
                      "use": description.use, "operation": description.operation, "action": description.action,
                      "rpc_ns": description.rpc_ns, "wsdl": description.wsdl(), "binding": "B",
                      "input": input_values, "output": values["output"],
                      "input_types": description.types("input"), "output_types": description.types("output"),
                      "input_parts": [(p["name"], p["element"], p["type"]) for p in description.parts["input"]],
                      "output_parts": [(p["name"], p["element"], p["type"]) for p in description.parts["output"]],
                      "header": description.header, "incoming": incoming, "mutations": mutations})
    return cases


def run_module(cases):
    with tempfile.TemporaryDirectory(prefix="binding-generation-") as temp:
        path = Path(temp) / "cases.json"
        path.write_text(json.dumps([{key: case[key] for key in ("id", "wsdl", "binding", "operation", "input",
                                                                "output", "incoming")} | {"operation":
                                                                case["operation"]} for case in cases]))
        env = dict(os.environ, QORE_MODULE_DIR=os.pathsep.join(
            (str(REPO / "build-debug"), str(REPO / "qlib"), os.environ.get("QORE_MODULE_DIR", ""))))
        result = subprocess.run([os.environ.get("QORE", "qore"), "-b", "--enable-debug",
                                 str(HERE / "binding-messages.qr"), str(path)],
                                capture_output=True, text=True, env=env, timeout=600)
    if result.returncode or result.stderr:
        raise AssertionError(f"worker exit {result.returncode}: {result.stderr}")
    return [json.loads(line) for line in result.stdout.splitlines()]


class BindingGenerationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = generate()
        cls.results = run_module(cls.cases)

    def test_generator_is_pinned(self):
        digest = hashlib.sha256(json.dumps(self.cases, sort_keys=True).encode()).hexdigest()
        self.assertEqual(CASES_SHA256, digest)
        self.assertEqual(COUNT, len(self.cases))
        self.assertEqual([case["id"] for case in self.cases], [result["id"] for result in self.results])

    def test_generated_bindings_cover_the_styles(self):
        combinations = {(case["version"], case["style"], case["use"]) for case in self.cases}
        self.assertEqual({(version, style, use) for version in ("11", "12")
                          for style, use in (("document", "literal"), ("rpc", "literal"), ("rpc", "encoded"))},
                         combinations)
        self.assertTrue(any(case["header"] for case in self.cases))
        self.assertTrue(any(part[2] == "complex" for case in self.cases for part in case["input_parts"]))
        self.assertTrue(any(not case["action"] for case in self.cases))

    def check_body(self, case, envelope, direction):
        """Checks a serialized envelope against the WSDL 1.1 section 3.5 structure of the generated binding."""
        v = case["version"]
        root = etree.fromstring(envelope.encode())
        self.assertEqual(f"{{{ENVELOPES[v]}}}Envelope", root.tag)
        body = root.find(f"{{{ENVELOPES[v]}}}Body")
        parts = case[f"{direction}_parts"]
        values = case[direction] if direction == "output" else \
            {name: value for name, value in case["input"].items() if name != "hdr"}
        types = case[f"{direction}_types"]
        if case["style"] == "document":
            children = list(body)
            self.assertEqual([f"{{{TYPES_NS}}}{element}" for _, element, _ in parts], [c.tag for c in children])
            accessors = dict(zip([name for name, _, _ in parts], children))
        else:
            self.assertEqual(1, len(body))
            wrapper = body[0]
            name = case["operation"] + ("Response" if direction == "output" else "")
            self.assertEqual(f"{{{case['rpc_ns']}}}{name}", wrapper.tag)
            children = list(wrapper)
            # without a parameterOrder, the return value is the part named "return" or a single output part
            # (WSOperation::getReturnPartName()); SOAP 1.2 Part 2 section 4.2.3 names it in rpc:result
            if case["use"] == "encoded" and v == "12" and direction == "output" and len(parts) == 1:
                result = children.pop(0)
                self.assertEqual("{http://www.w3.org/2003/05/soap-rpc}result", result.tag)
                # an unprefixed QName in no namespace names the unqualified accessor
                prefix, local = result.text.split(":", 1) if ":" in result.text else (None, result.text)
                self.assertEqual((None, parts[0][0]), (result.nsmap.get(prefix) if prefix else None, local))
            # accessors are unqualified and in part order (WS-I BP R2735, SOAP 1.1 section 7.1)
            self.assertEqual([name for name, _, _ in parts], [child.tag for child in children])
            accessors = {child.tag: child for child in children}
            if case["use"] == "encoded":
                self.assertEqual(ENCODINGS[v], wrapper.get(f"{{{ENVELOPES[v]}}}encodingStyle"))
                for part_name, _, datatype in parts:
                    prefix, _, local = accessors[part_name].get(f"{{{XSI}}}type").partition(":")
                    self.assertEqual((TYPES_NS, "Rec") if datatype == "complex" else (XSD, datatype),
                                     (accessors[part_name].nsmap[prefix], local))
        for part_name, value in values.items():
            element = accessors[part_name]
            if isinstance(value, dict):
                actual = {etree.QName(child).localname: child.text for child in element}
            else:
                actual = element.text
            self.assertTrue(same(types[part_name], value, actual), (part_name, value, actual))
        if direction == "input" and case["header"]:
            header = root.find(f"{{{ENVELOPES[v]}}}Header")
            self.assertEqual(case["input"]["hdr"], header.findtext(f"{{{TYPES_NS}}}{case['header']['element']}"))

    def test_serialized_messages_have_the_binding_structure(self):
        for case, result in zip(self.cases, self.results):
            with self.subTest(case=case["id"], style=(case["version"], case["style"], case["use"])):
                self.assertNotIn("error", result, result)
                self.check_body(case, result["request"], "input")
                self.check_body(case, result["response"], "output")
                media = result["content_type"].split(";")[0]
                if case["version"] == "11":
                    self.assertEqual("text/xml", media)
                    self.assertEqual(f'"{case["action"]}"', result["soapaction"])
                else:
                    self.assertEqual("application/soap+xml", media)
                    if case["action"]:
                        self.assertIn(f'action="{case["action"]}"', result["content_type"])

    def check_decoded(self, case, decoded):
        # WSOperation::deserializeRequest() returns header parts keyed by their message name and a single body part's
        # value by itself
        types = case["input_types"]
        body = {name: value for name, value in case["input"].items() if name != "hdr"}
        if case["header"]:
            self.assertEqual({"hdr": case["input"]["hdr"]}, decoded.pop("In"), decoded)
        if len(body) == 1 and not isinstance(decoded, dict) or len(body) == 1 and set(decoded) != set(body):
            decoded = {next(iter(body)): decoded}
        self.assertEqual(set(body), set(decoded), decoded)
        for name, value in body.items():
            self.assertTrue(same(types[name], value, decoded[name]), (name, value, decoded[name]))

    def test_requests_decode_to_the_generated_values(self):
        for case, result in zip(self.cases, self.results):
            with self.subTest(case=case["id"]):
                self.check_decoded(case, result["decoded"])
                # the independently built request, with other prefixes
                self.assertNotIn("error", result["incoming"][0], (case["incoming"][0], result["incoming"][0]))
                self.check_decoded(case, result["incoming"][0]["values"])

    def test_omitted_accessors_are_absent(self):
        # an omitted accessor is an absent value in literal and encoded messages
        count = 0
        for case, result in zip(self.cases, self.results):
            if "missing-accessor" not in case["mutations"]:
                continue
            count += 1
            outcome = result["incoming"][1 + case["mutations"].index("missing-accessor")]
            with self.subTest(case=case["id"]):
                self.assertNotIn("error", outcome, outcome)
                omitted = case["input_parts"][-1][0]
                self.assertIsNone(outcome["values"].get(omitted, "absent key"), outcome)
        self.assertGreater(count, 40)

    def test_mutated_requests_are_rejected(self):
        count = 0
        for case, result in zip(self.cases, self.results):
            for mutation, outcome, envelope in zip(case["mutations"], result["incoming"][1:], case["incoming"][1:]):
                if mutation == "missing-accessor":
                    continue
                # encoded accessors may be qualified (decided 2026-09-25)
                if mutation == "qualified-accessor" and case["use"] == "encoded":
                    self.assertNotIn("error", outcome, (envelope, outcome))
                    continue
                count += 1
                with self.subTest(case=case["id"], mutation=mutation, rule=MUTATIONS[case["style"]][mutation]):
                    self.assertEqual("SOAP-DESERIALIZATION-ERROR", outcome.get("error"), (envelope, outcome))
        self.assertGreater(count, 300)


if __name__ == "__main__":
    unittest.main()
