#!/usr/bin/env python3
"""Ordered particle languages, with complete native and independent outcomes.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS
from test_particle_model import schema


def element(name, counts=""):
    return f'<xs:element name="{name}" type="xs:string" {counts}/>'


def samples(valid, alphabet="abcd"):
    words = {"", *valid}
    for word in valid:
        for index in range(len(word) + 1):
            for char in alphabet:
                words.add(word[:index] + char + word[index:])
            if index < len(word):
                words.add(word[:index] + word[index + 1:])
    return sorted(words)


class ParticleMatchingTest(unittest.TestCase):
    def test_ordered_languages_in_both_bound_parts(self):
        ab = element("a") + element("b")
        all_words = ["ab", "ba", *("".join(p) for p in itertools.permutations("abc"))]
        cases = {
            "whole-sequence": (schema(f'<xs:sequence minOccurs="0" maxOccurs="2">{ab}</xs:sequence>'),
                               r'(?:ab){0,2}', samples(["ab", "abab"])),
            "alternating-choice": (schema('<xs:choice minOccurs="2" maxOccurs="3">' + ab + '</xs:choice>'),
                                   r'[ab]{2,3}', ["".join(p) for n in range(5) for p in itertools.product("ab", repeat=n)]),
            "nested-optional": (schema('<xs:sequence>' + element("a") + '<xs:sequence minOccurs="0">'
                + element("b") + element("c") + '</xs:sequence>' + element("d") + '</xs:sequence>'),
                r'a(?:bc)?d', samples(["ad", "abcd"])),
            "finite-gaps": (schema('<xs:sequence minOccurs="2" maxOccurs="3">'
                + element("a", 'minOccurs="2" maxOccurs="2"') + '</xs:sequence>'),
                r'(?:aa){2,3}', ["a" * n for n in range(9)] + ["aaaab"]),
            "nullable-counts": (schema('<xs:sequence minOccurs="3" maxOccurs="4">'
                + element("a", 'minOccurs="0"') + '</xs:sequence>'),
                r'a{0,4}', ["a" * n for n in range(7)] + ["aab"]),
            "shared-group": (schema('<xs:sequence><xs:group ref="t:Fields" minOccurs="1" maxOccurs="2"/>'
                + element("c") + '<xs:group ref="t:Fields"/></xs:sequence>',
                '<xs:group name="Fields"><xs:sequence>' + ab + '</xs:sequence></xs:group>'),
                r'(?:ab){1,2}cab', samples(["abcab", "ababcab"])),
            "all-permutations": (schema('<xs:all minOccurs="0">' + ab + element("c", 'minOccurs="0"')
                + element("d", 'minOccurs="0" maxOccurs="0"') + '</xs:all>'),
                '(?:' + '|'.join(["", *all_words]) + ')', samples(all_words)),
            "zero-choice-member": (schema('<xs:choice>' + element("a", 'minOccurs="0" maxOccurs="0"')
                + element("b") + '</xs:choice>'), r'b', ["", "a", "b", "ab", "ba", "aa", "bb"]),
            "empty-choice": (schema('<xs:choice/>'), r'(?!)', ["", "a"]),
            "optional-empty-choice": (schema('<xs:choice minOccurs="0"/>'), r'', ["", "a"]),
            "epsilon-choice": (schema('<xs:choice><xs:sequence/>' + element("a") + '</xs:choice>'),
                               r'a?', ["", "a", "aa", "b"]),
        }
        self.assertEqual(11, len(cases))
        jobs, workers, expected = [], [], {}
        libxml_disagreements = []
        for case, (source, pattern, words) in cases.items():
            self.assertEqual(len(words), len(set(words)))
            compiled = etree.XMLSchema(etree.fromstring(source.encode()))
            documents, names = {}, {}
            for index, word in enumerate(words):
                name = f"{case}/{index}"
                document = f'<t:Submit xmlns:t="{NS}">' + ''.join(f'<{char}>value</{char}>' for char in word) + '</t:Submit>'
                documents[name] = document.encode()
                names[name] = ["{}" + char for char in word]
                expected[name] = re.fullmatch(pattern, word) is not None
                actual = compiled.validate(etree.fromstring(document.encode()))
                if actual != expected[name]:
                    libxml_disagreements.append((case, word, actual, expected[name]))
            jobs.append(SchemaJob(case, f'http://example.invalid/{case}.xsd', source.encode(), documents))
            for version in ("11", "12"):
                workers.append({"name": case + "/" + version, "wsdl": description(version, source),
                                "binding": "Soap" + version, "documents": names})
        self.assertEqual(270, len(expected), "document coverage changed")
        self.assertEqual(22, len(workers), "binding coverage changed")
        oracle = run_independent(jobs)
        self.assertEqual(set(cases), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        for name, result in oracle["schemas"].items():
            self.assertTrue(result["ok"], (name, result))
            self.assertEqual([], result["warnings"])
        xerces_disagreements = []
        for name, result in oracle["documents"].items():
            self.assertEqual([], result["warnings"])
            if result["ok"] != expected[name]:
                xerces_disagreements.append((name, result["ok"], expected[name]))
        # The recorded zero-count libxml2 bug retains this local declaration as a
        # choice alternative. It incorrectly permits both epsilon and a consuming
        # transition; XSD 1.0 3.3.2 requires no component at this position.
        self.assertEqual([("zero-choice-member", "", True, False),
                          ("zero-choice-member", "a", True, False)], libxml_disagreements)
        # CMBuilder substitutes its empty content model when an empty choice
        # produces no syntax-tree node. Section 3.8.4 explicitly makes the
        # required empty choice's language empty, including the empty document.
        self.assertEqual([("empty-choice/0", True, False)], xerces_disagreements)
        mode = os.environ.get("QORE_EXEC_MODE", "jit")
        self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
        with tempfile.TemporaryDirectory(prefix="wsdl-particle-matching-") as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text(json.dumps(workers), encoding="utf-8")
            process = subprocess.run(["qore", "-b", "--enable-debug", "--exec-mode=" + mode,
                str(Path(__file__).with_name("particle-matching.qr")), str(path)],
                capture_output=True, text=True, timeout=90)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual("", process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        for worker in workers:
            for copy in (False, True):
                for direction in ("request", "response"):
                    for name in worker["documents"]:
                        self.assertEqual({"case": worker["name"], "copy": copy, "direction": direction,
                                          "root": "{" + NS + "}" + ("Submit" if direction == "request" else "Reply"),
                                          "document": name, "ok": expected[name]}, next(rows))
        self.assertIsNone(next(rows, None), "extra particle matching result")


if __name__ == '__main__':
    unittest.main()
