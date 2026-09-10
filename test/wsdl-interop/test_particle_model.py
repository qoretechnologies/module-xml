#!/usr/bin/env python3
"""Schema particle positions in actual SOAP bindings, independently checked XSDs.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD


def term(kind, *children, minimum="1", maximum="1", **properties):
    return {"kind": kind, "min": minimum, "max": maximum, "children": list(children), **properties}


def element(name, datatype="int", **counts):
    return term("element", name="{}" + name, type=datatype, **counts)


def schema(model, declarations=""):
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
      {declarations}<xs:complexType name="Record">{model}</xs:complexType>
      <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
    </xs:schema>'''


class ParticleModelTest(unittest.TestCase):
    def test_particle_order_counts_and_references_in_both_bindings(self):
        models = {
            "sequence-choice": (schema('''<xs:sequence><xs:choice><xs:element name="a" type="xs:int"/>
                <xs:element name="b" type="xs:int"/></xs:choice><xs:element name="c" type="xs:int"/>
                </xs:sequence>'''), term("sequence", term("choice", element("a"), element("b")), element("c"))),
            "nested-counts": (schema('''<xs:sequence minOccurs="0" maxOccurs="3"><xs:element name="a" type="xs:int"/>
                <xs:sequence minOccurs="2" maxOccurs="4"><xs:element name="b" type="xs:int"/>
                <xs:element name="c" type="xs:int"/></xs:sequence><xs:choice maxOccurs="unbounded">
                <xs:element name="d" type="xs:int"/><xs:element name="e" type="xs:int"/>
                </xs:choice></xs:sequence>'''), term("sequence", element("a"),
                    term("sequence", element("b"), element("c"), minimum="2", maximum="4"),
                    term("choice", element("d"), element("e"), maximum=None), minimum="0", maximum="3")),
            "all": (schema('''<xs:all minOccurs="0"><xs:element name="b" type="xs:int"/>
                <xs:element name="a" type="xs:int" minOccurs="0"/></xs:all>'''),
                term("all", element("b"), element("a", minimum="0"), minimum="0")),
            "empty-positions": (schema('''<xs:sequence><xs:sequence/><xs:sequence/>
                <xs:element name="a" type="xs:int"/><xs:sequence/></xs:sequence>'''),
                term("sequence", term("sequence"), term("sequence"), element("a"), term("sequence"))),
            "count-lexical": (schema('''<xs:sequence minOccurs=" -000 " maxOccurs=" unbounded ">
                <xs:element name="a" type="xs:int" minOccurs=" +000 " maxOccurs=" unbounded "/>
                </xs:sequence>'''), term("sequence", element("a", minimum="0", maximum=None),
                    minimum="0", maximum=None)),
            "reference": (schema('''<xs:sequence><xs:element name="a" type="xs:int"/>
                <xs:group ref="t:Fields" minOccurs="0" maxOccurs="2"/><xs:element name="d" type="xs:int"/>
                </xs:sequence>''', '''<xs:group name="Fields"><xs:sequence>
                <xs:element name="b" type="xs:int"/><xs:element name="c" type="xs:int"/></xs:sequence></xs:group>'''),
                term("sequence", element("a"), term("group", minimum="0", maximum="2", ref=f"{{{NS}}}Fields",
                    definition=term("sequence", element("b"), element("c"))), element("d"))),
            "extension": (schema('''<xs:complexContent><xs:extension base="t:Base"><xs:sequence>
                <xs:element name="c" type="xs:int"/></xs:sequence></xs:extension></xs:complexContent>''',
                '''<xs:complexType name="Base"><xs:sequence><xs:element name="a" type="xs:int"/>
                <xs:element name="b" type="xs:int"/></xs:sequence></xs:complexType>'''),
                term("sequence", term("sequence", element("a"), element("b")), term("sequence", element("c")))),
        }
        for prefix, namespace in (("alias", f'xmlns:alias="{XSD}"'), ("", f'xmlns="{XSD}"')):
            tag = prefix + ":" if prefix else ""
            models["alias-" + prefix] = (schema(f'''<xs:sequence {namespace}>
                <xs:element name="a" type="xs:int"/><xs:choice><xs:element name="b" type="xs:int"/>
                <xs:element name="c" type="xs:int"/></xs:choice><{tag}element name="d" type="xs:int"/>
                </xs:sequence>'''), term("sequence", element("a"), term("choice", element("b"), element("c")), element("d")))
        # Preserve the original signed-count source. libxml2's schema attribute
        # scanner rejects its valid nonNegativeInteger signs; this separately
        # identified derivative changes only equivalent occurrence spellings.
        original, expected = models["count-lexical"]
        canonical = original.replace(' -000 ', '0').replace(' +000 ', '0').replace(' unbounded ', 'unbounded')
        self.assertNotEqual(original, canonical)
        models["count-lexical-canonical"] = canonical, expected
        self.assertEqual(10, len(models))
        self.check_models(models)

    def test_invalid_particle_declarations_fail_before_binding_use(self):
        models = {name: (schema(body), "WSDL-ERROR") for name, body in {
            "reversed-range": '<xs:sequence minOccurs="2" maxOccurs="1"/>',
            "negative-count": '<xs:choice minOccurs="-1"><xs:element name="a"/></xs:choice>',
            "fractional-count": '<xs:sequence maxOccurs="1.5"/>',
            "absent-ref": '<xs:sequence><xs:group/></xs:sequence>',
            "unknown-ref": '<xs:sequence><xs:group ref="t:Missing"/></xs:sequence>',
            "absent-name": '<xs:sequence><xs:element/></xs:sequence>',
        }.items()}
        self.assertEqual(6, len(models))
        self.check_models(models)

    def check_models(self, models):
        jobs, cases, expected = [], [], {}
        for name, (source, result) in models.items():
            valid = isinstance(result, dict)
            if valid:
                try:
                    etree.XMLSchema(etree.fromstring(source.encode()))
                except etree.XMLSchemaParseError as error:
                    # XSD 1.0 Part 2 3.3.20.1 explicitly permits signs on zero.
                    # Xerces and the Qore worker still receive the original bytes.
                    self.assertEqual("count-lexical", name, str(error))
                    self.assertIn("attribute 'minOccurs'", str(error))
                    self.assertIn("Expected is 'xs:nonNegativeInteger'", str(error))
            else:
                with self.assertRaises(etree.XMLSchemaParseError, msg=name):
                    etree.XMLSchema(etree.fromstring(source.encode()))
            jobs.append(SchemaJob(name, f"http://example.invalid/{name}.xsd", source.encode()))
            for version in ("11", "12"):
                key = name + "/" + version
                cases.append({"name": key, "wsdl": description(version, source), "binding": "Soap" + version})
                expected[key] = result
        oracle = run_independent(jobs)
        self.assertEqual(set(models), set(oracle["schemas"]))
        self.assertEqual({}, oracle["documents"])
        for name, result in oracle["schemas"].items():
            self.assertEqual(isinstance(models[name][1], dict), result["ok"], (name, result))
            self.assertEqual([], result["warnings"], (name, result))
        mode = os.environ.get("QORE_EXEC_MODE", "jit")
        self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
        with tempfile.TemporaryDirectory(prefix="wsdl-particle-model-") as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text(json.dumps(cases), encoding="utf-8")
            process = subprocess.run(["qore", "-b", "--enable-debug", "--exec-mode=" + mode,
                                      str(Path(__file__).with_name("particle-model.qr")), str(path)],
                                     capture_output=True, text=True, timeout=60)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual("", process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        for case in cases:
            key = case["name"]
            result = expected[key]
            if isinstance(result, str):
                row = next(rows)
                self.assertEqual(key, row["name"])
                self.assertEqual(result, row["err"], row)
                self.assertTrue(row["desc"])
                continue
            for copy in (False, True):
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    row = next(rows)
                    self.assertEqual({"name": key, "copy": copy, "direction": direction,
                                      "root": f"{{{NS}}}{wrapper}", "particle": result}, row)
        self.assertIsNone(next(rows, None), "unexpected extra worker record")


if __name__ == "__main__":
    unittest.main()
