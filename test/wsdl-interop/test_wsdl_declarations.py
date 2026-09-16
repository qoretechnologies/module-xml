#!/usr/bin/env python3
"""Independent WSDL declaration identity checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run


class WsdlDeclarationsTest(unittest.TestCase):
    def test_pinned_wsdl_schema(self):
        root = Path(__file__).parent / "regressions/wsdl-declarations"
        data = json.loads((root / "oracle-cases.json").read_text())
        schema = (root / data["schema_file"]).read_bytes()
        self.assertEqual(data["schema_sha256"], hashlib.sha256(schema).hexdigest())
        self.assertEqual(25, len(data["cases"]))
        report = run([SchemaJob("wsdl-1.1", data["schema_url"], schema,
            {name: row["xml"].encode() for name, row in data["cases"].items()})])
        self.assertTrue(report["schemas"]["wsdl-1.1"]["ok"], report)
        self.assertEqual([], report["schemas"]["wsdl-1.1"]["warnings"])
        for name, row in data["cases"].items():
            with self.subTest(name=name):
                result = report["documents"][name]
                self.assertEqual(row["valid"], result["ok"], result)
                self.assertEqual([], result["warnings"])


if __name__ == "__main__":
    unittest.main()
