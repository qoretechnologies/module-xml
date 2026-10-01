#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise the pinned occurrence-flow patch against the preceding build-stage source."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(sys.argv.pop(1)).resolve()
ROOT = Path(__file__).resolve().parents[2]


class OccurrenceFlowTests(unittest.TestCase):
    def configure(self, directory, mode):
        root = Path(directory)
        source = root / 'source with spaces'; source.mkdir()
        content = SOURCE.read_bytes()
        if mode == 'changed':
            content += b'\n/* unexpected source */\n'
        (source / 'xmlschemas.c').write_bytes(content)
        (source / 'dummy.c').write_text('int unused;\n')
        c_file = 'dummy.c' if mode == 'missing' else 'xmlschemas.c'
        (source / 'CMakeLists.txt').write_text(f'''cmake_minimum_required(VERSION 3.18...3.31)
project(OccurrenceFlow C)
include("{ROOT}/cmake/QoreXmlLibXml2OccurrenceFlowFix.cmake")
add_library(LibXml2 STATIC {c_file})
qore_xml_fix_libxml2_occurrence_flow("${{CMAKE_CURRENT_SOURCE_DIR}}" "${{CMAKE_CURRENT_BINARY_DIR}}")
qore_xml_fix_libxml2_occurrence_flow("${{CMAKE_CURRENT_SOURCE_DIR}}" "${{CMAKE_CURRENT_BINARY_DIR}}")
get_target_property(actual LibXml2 SOURCES)
file(WRITE "${{CMAKE_CURRENT_BINARY_DIR}}/sources.txt" "${{actual}}")
''')
        build = root / 'build'
        result = subprocess.run(['cmake','-S',str(source),'-B',str(build)], capture_output=True, text=True)
        self.assertEqual(content, (source / 'xmlschemas.c').read_bytes())
        return build, result

    def test_actual_patch_is_idempotent_and_preserves_pinned_input(self):
        with tempfile.TemporaryDirectory() as directory:
            build, result = self.configure(directory, 'normal')
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertNotIn('warning', result.stderr.lower())
            target = Path((build / 'sources.txt').read_text())
            self.assertEqual('qore-occurrence-flow-fix', target.parent.name)
            content = target.read_text()
            self.assertEqual('c8a1eae8ea68df0bba7bad29e6aa5870346f2f117aaffddca5a0a0131c47bfe9',
                             hashlib.sha256(content.encode()).hexdigest())
            self.assertIn('if ((particle->minOccurs == 0) && (particle->maxOccurs == 0))', content)

    def test_unexpected_source_is_rejected_without_patch_output(self):
        with tempfile.TemporaryDirectory() as directory:
            build, result = self.configure(directory, 'changed')
            self.assertNotEqual(0, result.returncode)
            self.assertIn('Unexpected libxml2 xmlschemas.c', result.stderr)
            self.assertFalse((build / 'qore-occurrence-flow-fix').exists())

    def test_missing_target_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            build, result = self.configure(directory, 'missing')
            self.assertNotEqual(0, result.returncode)
            self.assertIn('Cannot locate libxml2 xmlschemas.c', result.stderr)
            self.assertFalse((build / 'qore-occurrence-flow-fix').exists())


if __name__ == '__main__':
    unittest.main()
