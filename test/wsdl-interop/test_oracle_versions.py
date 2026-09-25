#!/usr/bin/env python3
"""The suite runs with the pinned lxml validator.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import re
from pathlib import Path
import unittest
from unittest import mock

from lxml import etree

import oracle_versions

HERE = Path(__file__).resolve().parent


class OracleVersionsTest(unittest.TestCase):
    def test_pinned_lxml_and_libxml2(self):
        self.assertEqual([], oracle_versions.problems())
        oracle_versions.check()

    def test_other_versions_are_rejected(self):
        pinned = {"LXML_VERSION": oracle_versions.LXML, "LIBXML_VERSION": oracle_versions.LIBXML2,
                  "LIBXML_COMPILED_VERSION": oracle_versions.LIBXML2}
        for name, value in (("LXML_VERSION", (5, 3, 2, 0)), ("LIBXML_VERSION", (2, 15, 2)),
                            ("LIBXML_COMPILED_VERSION", (2, 13, 9))):
            with mock.patch.multiple(etree, **dict(pinned, **{name: value})):
                self.assertEqual(1, len(oracle_versions.problems()), name)
                with self.assertRaisesRegex(RuntimeError, "requires the pinned lxml validator"):
                    oracle_versions.check()

    def test_requirements_pin_the_same_version(self):
        text = (HERE / "requirements.txt").read_text()
        pins = re.findall(r"(?m)^(\S+)==(\S+) \\$", text)
        self.assertEqual([("lxml", ".".join(map(str, oracle_versions.LXML[:3])))], pins)
        hashes = re.findall(r"--hash=sha256:([0-9a-f]+)", text)
        self.assertTrue(hashes)
        self.assertEqual(len(hashes), len(set(hashes)))
        self.assertTrue(all(len(value) == 64 for value in hashes))


if __name__ == "__main__":
    unittest.main()
