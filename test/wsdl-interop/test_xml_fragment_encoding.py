#!/usr/bin/env python3
"""Validate generated XML bytes independently, including wide output encodings.

Copyright (C) 2026 Qore Technologies, s.r.o.
QORE selects the executable; QORE_MODULE_DIR selects the local native module.
"""
import base64
import os
from pathlib import Path
import subprocess
import unittest
from xml.etree import ElementTree

from lxml import etree


class FragmentEncodingTest(unittest.TestCase):
    def test_generated_bytes_and_preserved_content(self):
        script = Path(__file__).with_name("xml-fragment-encoding.qr")
        for encoding in ("UTF-8", "ISO-8859-1", "UTF-16LE", "UTF-16BE"):
            with self.subTest(encoding=encoding):
                result = subprocess.run([os.environ.get("QORE", "qore"), "--enable-debug", str(script), encoding],
                                        capture_output=True, check=True, timeout=30)
                self.assertEqual(b"", result.stderr)
                documents = result.stdout.splitlines()
                self.assertEqual(10, len(documents))
                for index, encoded in enumerate(documents):
                    with self.subTest(api=index):
                        data = base64.b64decode(encoded, validate=True)
                        source = data.decode(encoding)
                        self.assertIn("<![CDATA[café]]>", source)
                        self.assertIn("<!--note-->", source)
                        self.assertIn("&#9;", source)
                        self.assertIn("&#10;", source)
                        self.assertIn("&#13;", source)
                        if index < 7:
                            self.assertIn(f'encoding="{encoding}"', source)
                        else:
                            self.assertNotIn("<?xml", source)
                        independent_root = ElementTree.fromstring(data, parser=ElementTree.XMLParser(encoding=encoding if index >= 7 else None))
                        self.assertEqual("root", independent_root.tag)
                        self.assertEqual("a\tb\nc\rd", independent_root.get("label"))
                        self.assertEqual("beforecafé", independent_root.find("value").text)
                        self.assertEqual("after", independent_root.find("value/item").tail)
                        root = etree.fromstring(data, etree.XMLParser(encoding=encoding if index >= 7 else None, no_network=True))
                        self.assertEqual("root", root.tag)
                        self.assertEqual("a\tb\nc\rd", root.get("label"))
                        value = root.find("value")
                        self.assertIsNotNone(value)
                        self.assertEqual("beforecafé", value.text)
                        self.assertEqual("after", value.find("item").tail)
                        self.assertEqual(["note"], [node.text for node in value.xpath("comment()")])


if __name__ == "__main__":
    unittest.main()
