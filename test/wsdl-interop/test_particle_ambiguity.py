#!/usr/bin/env python3
"""Exact particle attribution, including exhaustive finite marked-word oracles.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS
from test_particle_model import schema


def words(expression, position=()):
    """Enumerate complete marked words; repeats reuse positions, siblings do not."""
    kind = expression[0]
    if kind == "empty":
        return set()
    if kind == "epsilon":
        return {()}
    if kind == "element":
        return {((expression[1], position),)}
    if kind == "repeat":
        child = words(expression[1], position + (0,))
        result, current = set(), {()}
        for count in range(expression[3] + 1):
            if count >= expression[2]:
                result |= current
            current = {left + right for left in current for right in child}
        return result
    left = words(expression[1], position + (0,))
    right = words(expression[2], position + (1,))
    return left | right if kind == "choice" else {a + b for a in left for b in right}


def unique_prefixes(expression):
    seen = {}
    for word in sorted(words(expression)):
        prefix = ()
        for name, position in word:
            prefix += (name,)
            if prefix in seen and seen[prefix] != position:
                return False
            seen[prefix] = position
    return True


def valid_components(expression):
    # Section 3.8.6 applies to every present model group, including a group
    # contained in a surrounding empty language. A zero-count term is absent.
    if expression[0] == "repeat" and expression[3] == 0:
        return True
    return unique_prefixes(expression) and all(valid_components(item)
        for item in expression[1:] if isinstance(item, tuple))


def source(expression):
    kind = expression[0]
    if kind == "empty":
        return '<xs:choice/>'
    if kind == "epsilon":
        return '<xs:sequence/>'
    if kind == "element":
        return f'<xs:element name="{expression[1]}" type="xs:string"/>'
    if kind == "repeat":
        return (f'<xs:sequence minOccurs="{expression[2]}" maxOccurs="{expression[3]}">'
                + source(expression[1]) + '</xs:sequence>')
    tag = "choice" if kind == "choice" else "sequence"
    return f'<xs:{tag}>' + source(expression[1]) + source(expression[2]) + f'</xs:{tag}>'


def limits(expression):
    """Conservative generation budget; every generated case is tested completely."""
    kind = expression[0]
    if kind in ("empty", "epsilon", "element"):
        return (int(kind != "empty"), int(kind == "element"))
    count, length = limits(expression[1])
    if kind == "repeat":
        return sum(count ** n for n in range(expression[2], expression[3] + 1)), length * expression[3]
    other_count, other_length = limits(expression[2])
    return ((count + other_count, max(length, other_length)) if kind == "choice"
            else (count * other_count, length + other_length))


def generated(rng, depth):
    if not depth or rng.random() < .25:
        return rng.choice([("empty",), ("epsilon",), ("element", "a"), ("element", "b")])
    if rng.random() < .45:
        maximum = rng.randint(1, 3)
        result = ("repeat", generated(rng, depth - 1), rng.randint(0, maximum), maximum)
    else:
        result = (rng.choice(["sequence", "choice"]), generated(rng, depth - 1), generated(rng, depth - 1))
    count, length = limits(result)
    # Bound the finite language while constructing the test expression, before
    # it becomes a test case. No emitted case is skipped or partially enumerated.
    return result if count <= 1024 and length <= 12 else ("element", rng.choice("ab"))


class ParticleAmbiguityTest(unittest.TestCase):
    def run_workers(self, cases):
        workers = [{"name": name + "/" + version, "wsdl": description(version, text), "binding": "Soap" + version}
                   for name, (text, _) in cases.items() for version in ("11", "12")]
        expected = []
        for name, (_, valid) in cases.items():
            for version in ("11", "12"):
                row = {"case": name + "/" + version, "stage": "construction", "ok": valid}
                if not valid:
                    row["err"] = "WSDL-ERROR"
                expected.append(row)
                if valid:
                    for copy, direction in itertools.product((False, True), ("request", "response")):
                        expected.append({"case": name + "/" + version, "stage": "bound-part", "copy": copy,
                            "direction": direction, "root": "{" + NS + "}" + ("Submit" if direction == "request"
                            else "Reply"), "ok": True})
        mode = os.environ.get("QORE_EXEC_MODE", "jit")
        self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
        with tempfile.TemporaryDirectory(prefix="wsdl-particle-attribution-") as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text(json.dumps(workers), encoding="utf-8")
            result = subprocess.run(["qore", "-b", "--enable-debug", "--exec-mode=" + mode,
                str(Path(__file__).with_name("particle-ambiguity.qr")), str(path)],
                capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual("", result.stderr)
        actual = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(expected), len(actual), "missing/extra construction or bound-part row")
        for wanted, received in zip(expected, actual):
            self.assertEqual(wanted, received)

    def test_complete_finite_prefix_oracle(self):
        rng = random.Random(4103)
        cases = {}
        for index in range(300):
            expression = generated(rng, 4)
            name = f"finite-{index:03}"
            cases[name] = (schema('<xs:sequence>' + source(expression) + '</xs:sequence>'),
                           valid_components(expression))
        self.assertEqual(300, len(cases))
        self.assertEqual(242, sum(value[1] for value in cases.values()))
        self.assertEqual(58, sum(not value[1] for value in cases.values()))
        self.run_workers(cases)

    def test_pinned_schema_oracles(self):
        element = lambda name, counts="": f'<xs:element name="{name}" type="xs:string" {counts}/>'
        cases = {
            "exact-boundary": (schema('<xs:sequence>' + element("a", 'minOccurs="2" maxOccurs="2"')
                + element("a") + '</xs:sequence>'), True),
            "variable-boundary": (schema('<xs:sequence>' + element("a", 'minOccurs="2" maxOccurs="3"')
                + element("a") + '</xs:sequence>'), False),
            "choice-duplicate": (schema('<xs:choice>' + element("a") + element("a") + '</xs:choice>'), False),
            "choice-distinct": (schema('<xs:choice>' + element("a") + element("b") + '</xs:choice>'), True),
            "optional-boundary": (schema('<xs:sequence>' + element("a", 'minOccurs="0"') + element("a")
                + '</xs:sequence>'), False),
            "weak-boundaries": (schema('<xs:sequence minOccurs="1" maxOccurs="2">'
                + element("a", 'minOccurs="1" maxOccurs="2"') + '</xs:sequence>'), True),
            "wildcard-disjoint": (schema('<xs:choice>' + element("a") + '<xs:any namespace="##other"/>'
                + '</xs:choice>'), True),
            "wildcard-overlap": (schema('<xs:choice>' + element("a") + '<xs:any namespace="##local"/>'
                + '</xs:choice>'), False),
            "empty-choice": (schema('<xs:choice/>'), True),
            "empty-language-component": (schema('<xs:sequence><xs:choice/><xs:choice>' + element("a")
                + element("a") + '</xs:choice></xs:sequence>'), False),
        }
        for count in (2, 3):
            cases[f"nested-count-{count}"] = (schema('<xs:sequence>'
                + f'<xs:sequence minOccurs="{count}" maxOccurs="{count}">'
                + element("b", 'minOccurs="0"') + element("a", 'minOccurs="2" maxOccurs="3"')
                + '</xs:sequence>' + element("b") + '</xs:sequence>'), count == 2)
        self.assertEqual(12, len(cases))
        libxml_disagreements = []
        for name, (text, valid) in cases.items():
            try:
                etree.XMLSchema(etree.fromstring(text.encode()))
                accepted = True
            except etree.XMLSchemaParseError:
                accepted = False
            if accepted != valid:
                libxml_disagreements.append((name, accepted, valid))
        oracle = run_independent([SchemaJob(name, f'http://example.invalid/{name}.xsd', text.encode(), {})
                                  for name, (text, _) in cases.items()])
        self.assertEqual(set(cases), set(oracle["schemas"]))
        self.assertEqual({}, oracle["documents"])
        xerces_disagreements = []
        for name, result in oracle["schemas"].items():
            self.assertEqual([], result["warnings"])
            if result["ok"] != cases[name][1]:
                xerces_disagreements.append((name, result["ok"], cases[name][1]))
        # libxml2's automaton check ignores counter feasibility and coalesces
        # equal transitions from distinct declaration positions. Xerces reduces
        # the inner range 2..3 to 1..2 for UPA, introducing a conflict absent from
        # the original two-iteration language. The exact defects are recorded in
        # particle-ambiguity-evidence.md; native libxml2 repairs remain P4 work.
        self.assertEqual([("exact-boundary", False, True), ("choice-duplicate", True, False),
                          ("empty-language-component", True, False),
                          ("nested-count-2", False, True)], libxml_disagreements)
        self.assertEqual([("nested-count-2", False, True)], xerces_disagreements)
        self.run_workers(cases)


if __name__ == '__main__':
    unittest.main()
