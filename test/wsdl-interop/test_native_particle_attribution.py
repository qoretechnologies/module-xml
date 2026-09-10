#!/usr/bin/env python3
"""Native counted attribution and documents against complete finite languages.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

from test_particle_ambiguity import generated, source, valid_components, words
from test_particle_model import NS, schema


class NativeParticleAttributionTest(unittest.TestCase):
    def test_complete_finite_languages_and_mutations(self):
        rng = random.Random(4103)
        expressions = [generated(rng, 4) for _ in range(300)] + [generated(rng, 5) for _ in range(700)]
        cases, expected = [], []
        accepted = 0
        for index, expression in enumerate(expressions):
            name = f"finite-{index:04}"
            valid = valid_components(expression)
            accepted += valid
            documents = []
            for stream in (False, True):
                expected.append({"case": name, "stage": "schema", "stream": stream,
                                 "error": "" if valid else "XSD-SYNTAX-ERROR"})
            if valid:
                # Enumerate the entire marked language, then test every distinct
                # unmarked word and every specified single mutation against it.
                language = {"".join(name for name, _ in word) for word in words(expression)}
                candidates = language | {"", "a", "b", "aa", "ab", "ba", "bb", "c"}
                for word in language:
                    candidates |= {word[:n] + word[n + 1:] for n in range(len(word))}
                    candidates |= {word[:n] + char + word[n + 1:] for n in range(len(word)) for char in "abc"}
                    candidates |= {char + word for char in "abc"} | {word + char for char in "abc"}
                for word in sorted(candidates):
                    document = f'<t:Submit xmlns:t="{NS}">' + "".join(
                        f"<{name}>value</{name}>" for name in word) + "</t:Submit>"
                    documents.append({"word": word, "xml": document})
                    for stream in (False, True):
                        expected.append({"case": name, "stage": "document", "word": word, "stream": stream,
                                         "error": "" if word in language else "PARSE-XML-EXCEPTION",
                                         # Invalid readers can stop at any rejected child.
                                         "childCount": len(word) if stream and word in language else None})
            cases.append({"name": name, "schema": schema("<xs:sequence>" + source(expression) + "</xs:sequence>"),
                          "documents": documents})
        self.assertEqual(765, accepted)
        self.assertEqual(43630, len(expected))
        mode = os.environ.get("QORE_EXEC_MODE", "jit")
        self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
        with tempfile.TemporaryDirectory(prefix="native-particle-attribution-") as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps(cases), encoding="utf-8")
            result = subprocess.run(["qore", "-b", "--enable-debug", "--exec-mode=" + mode,
                                     str(Path(__file__).with_name("native-particle-attribution.qr")), str(path)],
                                    capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual("", result.stderr)
        actual = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(expected), len(actual), "missing/extra schema or document rows")
        for wanted, received in zip(expected, actual):
            if wanted.get("childCount", -1) is None:
                count = received.pop("childCount")
                self.assertGreaterEqual(count, 0)
                self.assertLessEqual(count, len(wanted["word"]))
                if not wanted["stream"]:
                    self.assertEqual(0, count)
                wanted = {key: value for key, value in wanted.items() if key != "childCount"}
            self.assertEqual(wanted, received)


if __name__ == "__main__":
    unittest.main()
