#!/usr/bin/env python3
"""Generated SOAP 1.1 and 1.2 faults are read as independently parsed, and invalid faults are rejected.

Copyright (C) 2026 Qore Technologies, s.r.o.

SOAP clients read fault responses with WSDLLib::getSOAPFaultInfo(). A seeded generator writes SOAP 1.2 faults with
the standard codes under changing prefixes, subcode chains whose QNames are declared at different ancestors, reasons
in several languages, nodes, roles, details and header blocks, and SOAP 1.1 faults with standard and qualified
dotted fault codes, fault actors and details. Every generated fault is valid under the pinned W3C envelope schema,
and the expected codes, reasons and properties come from lxml's resolution of each QName in its element's scope.
Mutations break one rule of the fault grammar each (SOAP 1.2 Part 1 section 5.4, SOAP 1.1 section 4.4); the pinned
schema must reject them, and the module must reject them with SOAP-DESERIALIZATION-ERROR. The seed and a digest of the
generated cases are pinned.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

from lxml import etree

from test_soap_envelope import PEER as SCHEMA_PEER, LocalSchemas, URI

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SEED = 20260926
COUNT = 150
XML_NS = "http://www.w3.org/XML/1998/namespace"
CODES12 = ("Sender", "Receiver", "MustUnderstand", "VersionMismatch", "DataEncodingUnknown")
CODES11 = ("Client", "Server", "MustUnderstand", "VersionMismatch")
ENV_PREFIXES = ("s", "env", "soap", "e2")
PREFIXES = ("app", "q", "err", "x1")
URIS = ("urn:billing", "urn:orders", "urn:errors", "urn:x")
LANGUAGES = ("en", "de", "cs", "fr-CA", "en-US")
MUTATIONS = {
    "12": {
        "nonstandard-code": "5.4.6: the top-level Code Value is a standard fault code",
        "text-without-language": "5.4.2.1: every Reason Text has an xml:lang attribute",
        "missing-reason": "5.4: a Fault has a Reason",
        "subcode-without-value": "5.4.1.3: a Subcode has a Value",
        "unbound-subcode-prefix": "5.4.1.3: a Subcode Value is a QName",
        "duplicate-detail": "5.4: a Fault has at most one Detail",
        "reason-before-code": "5.4: Code precedes Reason",
    },
    "11": {
        "missing-faultcode": "4.4: a Fault has a faultcode",
        "missing-faultstring": "4.4: a Fault has a faultstring",
        "unbound-faultcode-prefix": "4.4.1: the faultcode is a qualified name",
        "faultcode-not-qname": "4.4.1: the faultcode is a qualified name",
        "duplicate-detail": "4.4: a Fault has at most one detail",
    },
}
# mutations the pinned schema rejects although the protocol permits them, as adjudicated in P7-05: SOAP 1.1 section
# 4.4 names the Fault's fields without an order, and the receiver recognizes them by name
SCHEMA_ONLY = {"11": {"faultstring-before-faultcode": "SOAP 1.1 section 4.4 does not order the Fault's fields"}}
SUBCODE_MUTATIONS = ("subcode-without-value", "unbound-subcode-prefix")
# the SHA-256 of the generated cases; see test_generator_is_pinned
CASES_SHA256 = "ba8f4673713a2e3196aab44c3ff7d1f0d6794a06ab94f889e9b220feb760f8e1"


def declarations(names):
    return "".join(f' xmlns:{prefix}="{uri}"' for prefix, uri in names)


class Fault:
    """One generated fault; rendered as text after any mutation."""

    def __init__(self, rng, version, index):
        self.rng, self.version, self.index = rng, version, index
        self.env = rng.choice(ENV_PREFIXES)
        # a second prefix bound to the envelope namespace, declared on the Fault, spells the code in its scope
        self.code_env = rng.choice([self.env, "f" + self.env])
        self.levels = {"Envelope": [], "Fault": [], "Code": []}
        if self.code_env != self.env:
            self.levels["Fault"].append((self.code_env, URI[version]))
        self.detail = [] if rng.random() < 0.4 else [self.detail_element() for _ in range(rng.choice((1, 2)))]
        self.headers = [self.header_block(i) for i in range(rng.choice((0, 0, 1, 2)))]
        if version == "12":
            self.code = rng.choice(CODES12)
            self.subcodes = []
            placed = {}
            for level in range(rng.choice((0, 1, 1, 2, 3))):
                prefix, uri = rng.choice(PREFIXES), rng.choice(URIS)
                where = rng.choice(("Envelope", "Fault", "Code", "Value"))
                # one declaration of a prefix per element: a conflicting binding is declared on the Value itself
                if where != "Value" and placed.get((where, prefix), uri) != uri:
                    where = "Value"
                if where != "Value":
                    placed[(where, prefix)] = uri
                self.subcodes.append({"prefix": prefix, "uri": uri, "local": f"e{index}x{level}", "where": where})
            self.reasons = [(f"reason {index} {language}", language)
                            for language in rng.sample(LANGUAGES, rng.choice((1, 1, 2, 3)))]
            self.node = f"urn:node:{index}" if rng.random() < 0.3 else None
            self.role = f"urn:role:{index}" if rng.random() < 0.3 else None
        else:
            if rng.random() < 0.5:
                self.faultcode = (self.code_env, URI[version], rng.choice(CODES11)
                                  + ("." + rng.choice(("Auth", "Quota")) if rng.random() < 0.3 else ""))
            else:
                prefix, uri = rng.choice(PREFIXES), rng.choice(URIS)
                self.faultcode = (prefix, uri, "Billing.Denied" if rng.random() < 0.5 else "Denied")
                self.levels[rng.choice(("Envelope", "Fault"))].append((prefix, uri))
            self.faultstring = f"fault {index}"
            self.actor = f"urn:actor:{index}" if rng.random() < 0.4 else None
        self.mutation = None

    def detail_element(self):
        prefix, uri = self.rng.choice(PREFIXES), self.rng.choice(URIS)
        return (f'<{prefix}:info xmlns:{prefix}="{uri}" {prefix}:ref="r{self.index}">'
                f'<{prefix}:line>{self.rng.randrange(1000)}</{prefix}:line></{prefix}:info>')

    def header_block(self, position):
        uri = self.rng.choice(URIS)
        return f'<h{position}:trace xmlns:h{position}="{uri}">t{self.index}</h{position}:trace>'

    def render(self):
        env, m = self.env, self.mutation
        body = self.render12() if self.version == "12" else self.render11()
        header = f"<{env}:Header>{''.join(self.headers)}</{env}:Header>" if self.headers else ""
        outer = self.levels["Envelope"] + [(item["prefix"], item["uri"]) for item in getattr(self, "subcodes", ())
                                           if item["where"] == "Envelope"]
        return (f'<{env}:Envelope xmlns:{env}="{URI[self.version]}"{declarations(self.dedupe(outer))}>'
                f'{header}<{env}:Body>{body}</{env}:Body></{env}:Envelope>')

    def render12(self):
        env, m, c = self.env, self.mutation, self.code_env
        levels = {level: list(names) for level, names in self.levels.items()}
        subcode = ""
        for item in reversed(self.subcodes):
            if item["where"] in ("Fault", "Code"):
                levels[item["where"]].append((item["prefix"], item["uri"]))
        for position, item in reversed(list(enumerate(self.subcodes))):
            local_declaration = declarations([(item["prefix"], item["uri"])]) if item["where"] == "Value" else ""
            prefix = "unbound9" if m == "unbound-subcode-prefix" and position == 0 else item["prefix"]
            value = "" if m == "subcode-without-value" and position == 0 else \
                f'<{env}:Value{local_declaration}>{prefix}:{item["local"]}</{env}:Value>'
            subcode = f"<{env}:Subcode>{value}{subcode}</{env}:Subcode>"
        code_value = "Unlisted" if m == "nonstandard-code" else self.code
        code = (f'<{env}:Code{declarations(self.dedupe(levels["Code"]))}><{env}:Value>{c}:{code_value}</{env}:Value>'
                f'{subcode}</{env}:Code>')
        texts = "".join((f'<{env}:Text>{text}</{env}:Text>' if m == "text-without-language" and i == 0
                         else f'<{env}:Text xml:lang="{language}">{text}</{env}:Text>')
                        for i, (text, language) in enumerate(self.reasons))
        reason = "" if m == "missing-reason" else f"<{env}:Reason>{texts}</{env}:Reason>"
        parts = [code, reason] if m != "reason-before-code" else [reason, code]
        if self.node:
            parts.append(f"<{env}:Node>{self.node}</{env}:Node>")
        if self.role:
            parts.append(f"<{env}:Role>{self.role}</{env}:Role>")
        details = 2 if m == "duplicate-detail" else (1 if self.detail else 0)
        parts += [f"<{env}:Detail>{''.join(self.detail)}</{env}:Detail>"] * details
        return f'<{env}:Fault{declarations(self.dedupe(levels["Fault"]))}>{"".join(parts)}</{env}:Fault>'

    def render11(self):
        env, m = self.env, self.mutation
        prefix, uri, local = self.faultcode
        if m == "unbound-faultcode-prefix":
            prefix = "unbound9"
        faultcode = "" if m == "missing-faultcode" else \
            f"<faultcode>{'not a qname' if m == 'faultcode-not-qname' else prefix + ':' + local}</faultcode>"
        faultstring = "" if m == "missing-faultstring" else f"<faultstring>{self.faultstring}</faultstring>"
        parts = [faultcode, faultstring] if m != "faultstring-before-faultcode" else [faultstring, faultcode]
        if self.actor:
            parts.append(f"<faultactor>{self.actor}</faultactor>")
        details = 2 if m == "duplicate-detail" else (1 if self.detail else 0)
        parts += [f"<detail>{''.join(self.detail)}</detail>"] * details
        return f'<{env}:Fault{declarations(self.dedupe(self.levels["Fault"]))}>{"".join(parts)}</{env}:Fault>'

    @staticmethod
    def dedupe(names):
        seen, result = {}, []
        for prefix, uri in names:
            if prefix not in seen:
                seen[prefix] = uri
                result.append((prefix, uri))
        return result


def generate():
    rng = random.Random(SEED)
    cases = []
    for version in ("12", "11"):
        faults = [Fault(rng, version, index) for index in range(COUNT)]
        for fault in faults:
            cases.append({"id": f"{version}-valid-{fault.index}", "version": version, "kind": "valid",
                          "xml": fault.render()})
        for kind in list(MUTATIONS[version]) + list(SCHEMA_ONLY.get(version, {})):
            eligible = [fault for fault in faults if fault.subcodes] if kind in SUBCODE_MUTATIONS else faults
            for fault in eligible[:15]:
                fault.mutation = kind
                cases.append({"id": f"{version}-{kind}-{fault.index}", "version": version, "kind": kind,
                              "xml": fault.render()})
                fault.mutation = None
    return cases


def expected(case):
    """Returns the fault's properties as lxml resolves them."""
    root = etree.fromstring(case["xml"].encode())
    env = URI[case["version"]]
    fault = root.find(f"{{{env}}}Body/{{{env}}}Fault")
    header = root.find(f"{{{env}}}Header")

    def qname(element):
        prefix, _, local = element.text.partition(":")
        return f"{{{element.nsmap[prefix]}}}{local}"
    if case["version"] == "12":
        codes = [qname(fault.find(f"{{{env}}}Code/{{{env}}}Value"))]
        subcode = fault.find(f"{{{env}}}Code/{{{env}}}Subcode")
        while subcode is not None:
            codes.append(qname(subcode.find(f"{{{env}}}Value")))
            subcode = subcode.find(f"{{{env}}}Subcode")
        reasons = [{"text": text.text, "language": text.get(f"{{{XML_NS}}}lang")}
                   for text in fault.findall(f"{{{env}}}Reason/{{{env}}}Text")]
        node, role = fault.findtext(f"{{{env}}}Node"), fault.findtext(f"{{{env}}}Role")
        actor, detail = None, fault.find(f"{{{env}}}Detail") is not None
    else:
        codes = [qname(fault.find("faultcode"))]
        reasons = [{"text": fault.findtext("faultstring"), "language": None}]
        node = role = None
        actor, detail = fault.findtext("faultactor"), fault.find("detail") is not None
    return {"soap12": case["version"] == "12", "codes": codes, "reasons": reasons, "actor": actor, "node": node,
            "role": role, "detail": detail, "headers": 0 if header is None else len(header)}


def run_module(cases):
    with tempfile.TemporaryDirectory(prefix="fault-generation-") as temp:
        path = Path(temp) / "cases.json"
        path.write_text(json.dumps([{"id": case["id"], "xml": case["xml"]} for case in cases]))
        env = dict(os.environ, QORE_MODULE_DIR=os.pathsep.join(
            (str(REPO / "build-debug"), str(REPO / "qlib"), os.environ.get("QORE_MODULE_DIR", ""))))
        result = subprocess.run([os.environ.get("QORE", "qore"), "-b", "--enable-debug",
                                 str(HERE / "fault-info.qr"), str(path)],
                                capture_output=True, text=True, env=env, timeout=300)
    if result.returncode or result.stderr:
        raise AssertionError(f"worker exit {result.returncode}: {result.stderr}")
    return [json.loads(line) for line in result.stdout.splitlines()]


class SoapFaultGenerationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        cls.schemas = {version: etree.XMLSchema(etree.fromstring((SCHEMA_PEER / f"soap{version}.xsd").read_bytes(),
                                                                 parser))
                       for version in ("11", "12")}
        cls.cases = generate()
        cls.results = run_module(cls.cases)

    def test_generator_is_pinned(self):
        digest = hashlib.sha256(json.dumps(self.cases, sort_keys=True).encode()).hexdigest()
        self.assertEqual(CASES_SHA256, digest)
        self.assertEqual(2 * COUNT + 15 * (sum(len(kinds) for kinds in MUTATIONS.values())
                                           + sum(len(kinds) for kinds in SCHEMA_ONLY.values())), len(self.cases))
        self.assertEqual(len(self.cases), len({case["id"] for case in self.cases}))
        self.assertEqual([case["id"] for case in self.cases], [result["id"] for result in self.results])

    def test_generated_faults_cover_the_constructs(self):
        valid = [expected(case) for case in self.cases if case["kind"] == "valid"]
        self.assertTrue(any(len(fault["codes"]) == 4 for fault in valid))
        self.assertTrue(any(len(fault["reasons"]) == 3 for fault in valid))
        for key in ("node", "role", "actor"):
            self.assertTrue(any(fault[key] for fault in valid), key)
        self.assertTrue(any(fault["headers"] == 2 for fault in valid))
        self.assertTrue(any(not code.startswith("{http") for fault in valid if not fault["soap12"]
                            for code in fault["codes"]))

    def test_valid_faults_are_schema_valid_and_read_as_parsed(self):
        for case, result in zip(self.cases, self.results):
            if case["kind"] != "valid":
                continue
            with self.subTest(case=case["id"]):
                schema = self.schemas[case["version"]]
                self.assertTrue(schema.validate(etree.fromstring(case["xml"].encode())), str(schema.error_log))
                self.assertNotIn("error", result, (case["xml"], result))
                self.assertEqual(expected(case), {key: value for key, value in result.items() if key != "id"},
                                 case["xml"])

    def test_schema_only_differences_are_read(self):
        cases = [(case, result) for case, result in zip(self.cases, self.results)
                 if case["kind"] in SCHEMA_ONLY.get(case["version"], {})]
        self.assertEqual(15, len(cases))
        for case, result in cases:
            with self.subTest(case=case["id"], reason=SCHEMA_ONLY[case["version"]][case["kind"]]):
                self.assertFalse(self.schemas[case["version"]].validate(etree.fromstring(case["xml"].encode())))
                self.assertEqual(expected(case), {key: value for key, value in result.items() if key != "id"},
                                 case["xml"])

    def test_invalid_faults_are_rejected(self):
        for case, result in zip(self.cases, self.results):
            if case["kind"] not in MUTATIONS[case["version"]]:
                continue
            with self.subTest(case=case["id"], rule=MUTATIONS[case["version"]][case["kind"]]):
                self.assertFalse(self.schemas[case["version"]].validate(etree.fromstring(case["xml"].encode())),
                                 case["xml"])
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", result.get("error"), (case["xml"], result))


if __name__ == "__main__":
    unittest.main()
