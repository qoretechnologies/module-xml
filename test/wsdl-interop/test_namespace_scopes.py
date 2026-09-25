#!/usr/bin/env python3
"""Generated namespace scopes resolve as an independent XML parser resolves them.

Copyright (C) 2026 Qore Technologies, s.r.o.

SOAP decoding resolves every element and attribute name to its expanded name (XsdBase::expandElementNamespaces()).
A seeded generator writes documents with nested prefix declarations, rebinding, default namespaces and their
undeclaration, prefixed, unprefixed and xml: attributes, and repeated names in changing scopes. The expected names
come from Python's expat parser (xml.etree.ElementTree), which is independent of libxml2 and of the module. Mutations
of the valid documents break one Namespaces in XML 1.0 constraint each; expat and the module must both reject them.
The seed and a digest of the generated cases are pinned, so a change of the generator is visible.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SEED = 20260925
VALID = 300
XML_NS = "http://www.w3.org/XML/1998/namespace"
XMLNS_NS = "http://www.w3.org/2000/xmlns/"
PREFIXES = ("p", "q", "r", "ns1", "a")
URIS = ("urn:a", "urn:b", "urn:c", "urn:d")
LOCALS = ("a", "b", "c", "item")
ATTRIBUTES = ("id", "kind", "a")
# the constraint each invalid mutation breaks (Namespaces in XML 1.0, third edition)
MUTATIONS = {
    "unbound-element-prefix": "NSC: Prefix Declared (element name)",
    "unbound-attribute-prefix": "NSC: Prefix Declared (attribute name)",
    "duplicate-expanded-attribute": "NSC: Attributes Unique",
    "undeclared-prefix": "NSC: No Prefix Undeclaring",
    "rebound-xml-prefix": "NSC: Reserved Prefixes and Namespace Names (xml)",
    "bound-xmlns-prefix": "NSC: Reserved Prefixes and Namespace Names (xmlns)",
    "xmlns-namespace-name": "NSC: Reserved Prefixes and Namespace Names (xmlns namespace name)",
}
# the SHA-256 of the generated cases; see test_generator_is_pinned
CASES_SHA256 = "925b5c3b0e818d523cfb4295d4055b08d3986bb6da034c0280104cc51aeb675f"


class Generator:
    """Writes one document; each element records its declarations, name and attributes in its scope."""

    def __init__(self, rng):
        self.rng = rng
        self.counter = 0

    def document(self):
        return self.element({"xml": XML_NS}, None, 0)

    def element(self, inherited, default, depth):
        rng = self.rng
        scope = dict(inherited)
        declarations = []
        for _ in range(rng.choice((0, 0, 1, 1, 2))):
            prefix, uri = rng.choice(PREFIXES), rng.choice(URIS)
            if any(declared == prefix for declared, _ in declarations):
                continue
            declarations.append((prefix, uri))
            scope[prefix] = uri
        choice = rng.random()
        if choice < 0.2:
            default = rng.choice(URIS)
            declarations.append(("", default))
        elif choice < 0.3 and default is not None:
            # undeclaring the default namespace is permitted
            default = None
            declarations.append(("", ""))
        bound = sorted(prefix for prefix in scope if prefix != "xml")
        prefix = rng.choice(bound) if bound and rng.random() < 0.6 else None
        name = (prefix + ":" if prefix else "") + rng.choice(LOCALS)
        attributes, identities = [], set()
        for _ in range(rng.choice((0, 0, 1, 2))):
            kind = rng.random()
            if kind < 0.15:
                attribute, identity = "xml:lang", (XML_NS, "lang")
            elif kind < 0.55 and bound:
                attribute_prefix = rng.choice(bound)
                local = rng.choice(ATTRIBUTES)
                attribute, identity = f"{attribute_prefix}:{local}", (scope[attribute_prefix], local)
            else:
                local = rng.choice(ATTRIBUTES)
                attribute, identity = local, ("", local)
            if identity in identities or any(existing == attribute for existing, _ in attributes):
                continue
            identities.add(identity)
            self.counter += 1
            attributes.append((attribute, f"v{self.counter}"))
        children = []
        if depth < 4:
            for _ in range(self.rng.choice((0, 1, 2, 3))):
                children.append(self.element(scope, default, depth + 1))
        self.counter += 1
        return {"name": name, "declarations": declarations, "attributes": attributes, "children": children,
                "text": None if children else f"t{self.counter}", "scope": scope}


def render(node):
    parts = [node["name"]]
    for prefix, uri in node["declarations"]:
        parts.append(f'xmlns{":" + prefix if prefix else ""}="{uri}"')
    parts += [f'{name}="{value}"' for name, value in node["attributes"]]
    inner = "".join(render(child) for child in node["children"]) if node["children"] else node["text"]
    return f"<{' '.join(parts)}>{inner}</{node['name']}>"


def mutate(rng, node, kind):
    """Returns an invalid variant of a document, as text and as parsed data, breaking the named constraint on one
    element."""
    elements = []

    def collect(item):
        elements.append(item)
        for child in item["children"]:
            collect(child)
    collect(node)
    target = rng.choice(elements)
    original = dict(target)
    if kind == "unbound-element-prefix":
        target["name"] = "zz:" + target["name"].split(":")[-1]
    elif kind == "unbound-attribute-prefix":
        target["attributes"] = target["attributes"] + [("zz:extra", "x")]
    elif kind == "duplicate-expanded-attribute":
        target["declarations"] = target["declarations"] + [("dup1", "urn:dup"), ("dup2", "urn:dup")]
        target["attributes"] = target["attributes"] + [("dup1:x", "1"), ("dup2:x", "2")]
    elif kind == "undeclared-prefix":
        target["declarations"] = [(prefix, uri) for prefix, uri in target["declarations"] if prefix != "gone"] \
            + [("gone", "")]
    elif kind == "rebound-xml-prefix":
        target["declarations"] = target["declarations"] + [("xml", "urn:other")]
    elif kind == "bound-xmlns-prefix":
        target["declarations"] = target["declarations"] + [("xmlns", "urn:other")]
    elif kind == "xmlns-namespace-name":
        target["declarations"] = target["declarations"] + [("ns9", XMLNS_NS)]
    text, data = render(node), parsed(node)
    target.clear()
    target.update(original)
    return text, data


def parsed(node):
    """Returns a document as parse_xml() with preserved order represents it.

    Adjacent repetitions of a name form a list; a later, non-adjacent repetition gets an occurrence suffix.
    """
    def content(item):
        attributes = {("xmlns:" + prefix if prefix else "xmlns"): uri for prefix, uri in item["declarations"]}
        attributes.update(dict(item["attributes"]))
        if not item["children"]:
            return {"^attributes^": attributes, "^value^": item["text"]} if attributes else item["text"]
        result = {"^attributes^": attributes} if attributes else {}
        counts, last = {}, None
        for child in item["children"]:
            name = child["name"]
            value = content(child)
            if name == last:
                key = name if counts[name] == 0 else f"{name}^{counts[name]}"
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
                continue
            if name in counts:
                counts[name] += 1
                result[f"{name}^{counts[name]}"] = value
            else:
                counts[name] = 0
                result[name] = value
            last = name
        return result
    return {node["name"]: content(node)}


def generate():
    """Returns the valid and invalid cases: [{"id", "xml", "valid", "kind"}]."""
    rng = random.Random(SEED)
    generator = Generator(rng)
    cases, trees = [], []
    for index in range(VALID):
        tree = generator.document()
        trees.append(tree)
        cases.append({"id": f"valid-{index}", "xml": render(tree), "data": parsed(tree), "valid": True,
                      "kind": "valid"})
    for kind in MUTATIONS:
        for index in range(20):
            text, data = mutate(rng, trees[index], kind)
            cases.append({"id": f"{kind}-{index}", "xml": text, "data": data, "valid": False, "kind": kind})
    return cases


def expat_names(text):
    """Returns the expanded element and attribute names in document order, as expat resolves them."""
    def expanded(name):
        return name if name.startswith("{") else "{}" + name
    return [{"name": expanded(element.tag), "attributes": sorted(expanded(name) for name in element.attrib)}
            for element in ET.fromstring(text).iter()]


def run_module(cases, form):
    """Runs the module on each case's text (form "xml") or parsed data (form "data")."""
    with tempfile.TemporaryDirectory(prefix="namespace-scopes-") as temp:
        path = Path(temp) / "cases.json"
        path.write_text(json.dumps([{"id": case["id"], form: case[form]} for case in cases]))
        env = dict(os.environ, QORE_MODULE_DIR=os.pathsep.join(
            (str(REPO / "build-debug"), str(REPO / "qlib"), os.environ.get("QORE_MODULE_DIR", ""))))
        result = subprocess.run([os.environ.get("QORE", "qore"), "-b", "--enable-debug",
                                 str(HERE / "namespace-scopes.qr"), str(path)],
                                capture_output=True, text=True, env=env, timeout=300)
    if result.returncode or result.stderr:
        raise AssertionError(f"worker exit {result.returncode}: {result.stderr}")
    return [json.loads(line) for line in result.stdout.splitlines()]


class NamespaceScopesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = generate()
        cls.results = run_module(cls.cases, "xml")
        cls.data_results = run_module(cls.cases, "data")

    def test_generator_is_pinned(self):
        digest = hashlib.sha256(json.dumps(self.cases, sort_keys=True).encode()).hexdigest()
        self.assertEqual(CASES_SHA256, digest)
        self.assertEqual(VALID + 20 * len(MUTATIONS), len(self.cases))
        self.assertEqual(len(self.cases), len({case["id"] for case in self.cases}))

    def test_generated_scopes_cover_the_constructs(self):
        documents = [case["xml"] for case in self.cases if case["valid"]]
        for construct in ('xmlns="urn:', 'xmlns=""', "xml:lang=", ' xmlns:p="', "<p:", " p:"):
            self.assertTrue(any(construct in text for text in documents), construct)
        # a prefix rebound to another namespace inside the scope of its first binding
        self.assertTrue(any(self.rebinds(case["xml"]) for case in self.cases if case["valid"]))

    @staticmethod
    def rebinds(text):
        scopes = [{}]
        for element in ET.iterparse(__import__("io").StringIO(text), events=("start-ns",)):
            prefix, uri = element[1]
            if prefix in scopes[-1] and scopes[-1][prefix] != uri:
                return True
            scopes[-1][prefix] = uri
        return False

    def test_results_account_for_every_case(self):
        for results in (self.results, self.data_results):
            self.assertEqual([case["id"] for case in self.cases], [result["id"] for result in results])

    def test_valid_scopes_resolve_as_expat_resolves_them(self):
        for case, result in zip(self.cases, self.results):
            if not case["valid"]:
                continue
            with self.subTest(case=case["id"]):
                self.assertNotIn("error", result, case["xml"])
                self.assertEqual(expat_names(case["xml"]), result["elements"], case["xml"])

    def test_parsed_data_resolves_as_expat_resolves_the_text(self):
        for case, result in zip(self.cases, self.data_results):
            if not case["valid"]:
                continue
            with self.subTest(case=case["id"]):
                self.assertNotIn("error", result, case["xml"])
                self.assertEqual(expat_names(case["xml"]), result["elements"], case["xml"])

    def test_invalid_parsed_data_is_rejected_by_the_module(self):
        # libxml2 rejects the invalid texts before the module sees them; parsed data reaches the module's own checks
        for case, result in zip(self.cases, self.data_results):
            if case["valid"]:
                continue
            with self.subTest(case=case["id"], constraint=MUTATIONS[case["kind"]]):
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", result.get("error"), (case["data"], result))

    def test_invalid_scopes_are_rejected(self):
        for case, result in zip(self.cases, self.results):
            if case["valid"]:
                continue
            with self.subTest(case=case["id"], constraint=MUTATIONS[case["kind"]]):
                with self.assertRaises(ET.ParseError, msg=case["xml"]):
                    ET.fromstring(case["xml"])
                self.assertIn("error", result, case["xml"])


if __name__ == "__main__":
    unittest.main()
