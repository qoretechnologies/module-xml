#!/usr/bin/env python3
"""Java oracles and peers run without ambient JVM options.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import os
import subprocess
import unittest
from unittest import mock

import jvm

OPTIONS = {"JAVA_TOOL_OPTIONS": "-Dfile.encoding=UTF8", "JDK_JAVA_OPTIONS": "-Xmx64m", "_JAVA_OPTIONS": "-Xss1m"}


class JvmEnvironmentTest(unittest.TestCase):
    def test_removes_only_the_ambient_options(self):
        base = {"PATH": "/usr/bin", "JAVA_HOME": "/usr/lib/jvm/default-jvm", "QORE_MODULE_DIR": "a:b", **OPTIONS}
        self.assertEqual({"PATH": "/usr/bin", "JAVA_HOME": "/usr/lib/jvm/default-jvm", "QORE_MODULE_DIR": "a:b"},
                         jvm.environment(base))
        # the argument is copied, not changed
        self.assertEqual(6, len(base))
        self.assertEqual({}, jvm.environment({}))

    def test_process_environment(self):
        with mock.patch.dict(os.environ, OPTIONS):
            environment = jvm.environment()
        self.assertFalse(set(OPTIONS) & set(environment))
        self.assertEqual(os.environ.get("PATH"), environment.get("PATH"))

    def test_launchers_report_no_ambient_options(self):
        # with the options, each launcher prints a notice on stderr, which the oracles treat as a diagnostic
        with mock.patch.dict(os.environ, OPTIONS):
            for command in (["java", "-version"], ["javac", "-version"]):
                ambient = subprocess.run(command, capture_output=True, text=True, timeout=60)
                self.assertEqual(0, ambient.returncode, command)
                self.assertIn("Picked up JAVA_TOOL_OPTIONS", ambient.stderr, command)
                clean = subprocess.run(command, capture_output=True, text=True, timeout=60, env=jvm.environment())
                self.assertEqual(0, clean.returncode, command)
                self.assertNotIn("Picked up", clean.stdout + clean.stderr, command)


if __name__ == "__main__":
    unittest.main()
