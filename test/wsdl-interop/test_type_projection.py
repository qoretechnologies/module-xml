#!/usr/bin/env python3
"""Original W3C dynamic-type fixture in both native projection modes.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from pathlib import Path
import tempfile
import unittest

from lxml import etree

import corpus
import survey
from independent import SchemaJob, run as run_independent
from test_type_identity import expanded_type


class TypeProjectionTest(unittest.TestCase):
    def test_original_dynamic_type_in_both_directions(self):
        name = "TypeSubstitutionUsingXsiType"
        namespace = survey.SOURCE
        with tempfile.TemporaryDirectory(prefix="wsdl-type-projection-") as temporary:
            root = corpus.extract(Path(temporary) / "corpus")
            case = next(case for case in survey.inventory(root, "both") if case["name"] == name)
            case["binding"] = "SoapBinding"
            case["messages"] = [dict(message, direction=direction) for message in case["messages"]
                                for direction in ("request", "response")]
            self.assertEqual(4, len(case["messages"]))
            schema = (root / name / f"echo{name}.xsd").read_bytes()
            compiled = etree.XMLSchema(etree.fromstring(schema))
            documents = {}
            for message in case["messages"]:
                node = survey.payload(Path(message["path"]).read_bytes(), survey.parser(root))
                compiled.assertValid(node)
                documents[message["file"] + "/" + message["direction"] + "/input"] = etree.tostring(node)
            legacy = survey.run_worker([case], {})
            self.assertEqual(legacy, survey.run_worker([case], {}, preserve_types=False))
            counts = survey.stage_accounting([case], legacy)["counts"]
            self.assertEqual(4, counts["deserialize"]["ok"])
            self.assertEqual(4, counts["serialize"]["failed"])
            for row in legacy:
                if row["stage"] == "serialize":
                    self.assertEqual("SOAP-SERIALIZATION-ERROR", row["err"], row)
            typed = survey.run_worker([case], {}, preserve_types=True)
            self.assertEqual(4, survey.stage_accounting([case], typed)["counts"]["serialize"]["ok"])
            for row in typed:
                self.assertTrue(row["ok"], row)
                if row["stage"] != "serialize":
                    continue
                node = survey.payload(row["body"].encode(), survey.parser(root))
                compiled.assertValid(node)
                parts = node.findall(f"{{{namespace}}}assembly/{{{namespace}}}part")
                self.assertEqual(2, len(parts))
                self.assertIsNone(expanded_type(parts[0]))
                self.assertEqual((namespace, "Part2"), expanded_type(parts[1]))
                self.assertEqual([(f"{{{namespace}}}number", "p1")],
                                 [(child.tag, child.text) for child in parts[0]])
                self.assertEqual([(f"{{{namespace}}}number", "p2"),
                                  (f"{{{namespace}}}description", "extended part")],
                                 [(child.tag, child.text) for child in parts[1]])
                documents[row["file"] + "/" + row["direction"] + "/output"] = etree.tostring(node)
            oracle = run_independent([SchemaJob(name, survey.SOURCE + name + "/schema.xsd", schema, documents)])
            self.assertEqual(8, len(oracle["documents"]))
            self.assertTrue(oracle["schemas"][name]["ok"], oracle)
            self.assertEqual([], oracle["schemas"][name]["warnings"])
            for verdict in oracle["documents"].values():
                self.assertTrue(verdict["ok"], verdict)
                self.assertEqual([], verdict["warnings"])


if __name__ == "__main__":
    unittest.main()
