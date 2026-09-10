#!/usr/bin/env python3
"""Complete finite marked languages verify declaration selection for each token.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import time
import unittest

from test_particle_ambiguity import generated, source, valid_components, words
from test_particle_model import schema


class ParticleValueAttributionTest(unittest.TestCase):
    def test_complete_marked_languages_and_mutations(self):
        rng = random.Random(4103)
        expressions = [generated(rng, 4) for _ in range(300)] + [generated(rng, 5) for _ in range(700)]
        inputs, expected = [], []
        for index, expression in enumerate(expressions):
            name = f"finite-{index:04}"
            valid = valid_components(expression)
            expected.append({"case": name, "error": "" if valid else "WSDL-ERROR"})
            candidates, marked = set(), {}
            if valid:
                for word in words(expression):
                    text = "".join(name for name, _ in word)
                    positions = ["".join("/" + str(index) for index in position) for _, position in word]
                    if text in marked:
                        self.assertEqual(marked[text], positions, "accepted grammar has ambiguous attribution")
                    marked[text] = positions
                candidates = set(marked) | {"", "a", "b", "aa", "ab", "ba", "bb", "c"}
                for word in marked:
                    candidates |= {word[:n] + word[n + 1:] for n in range(len(word))}
                    candidates |= {word[:n] + char + word[n + 1:] for n in range(len(word)) for char in "abc"}
                    candidates |= {char + word for char in "abc"} | {word + char for char in "abc"}
                for copy in (False, True):
                    for word in sorted(candidates):
                        expected.append({"case": name, "copy": copy, "word": word, "positions": marked.get(word)})
            inputs.append({"name": name, "schema": schema("<xs:sequence>" + source(expression) + "</xs:sequence>"),
                           "words": sorted(candidates)})
        self.assertEqual(42630, len(expected))
        mode = os.environ.get("QORE_EXEC_MODE", "jit")
        self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
        actual = []
        # Bound one worker independently of the total oracle size. AST executes
        # each schema and reconstruction in the interpreter; a 1,000-model
        # process exceeded the earlier aggregate 180-second deadline. Four
        # deterministic batches retain every case and the complete global order.
        with tempfile.TemporaryDirectory(prefix="particle-value-attribution-") as temporary:
            for first in range(0, len(inputs), 250):
                path = Path(temporary) / f"cases-{first:04}.json"
                batch = inputs[first:first + 250]
                path.write_text(json.dumps(batch), encoding="utf-8")
                started = time.monotonic()
                try:
                    process = subprocess.run(["qore", "-b", "--enable-debug", "--exec-mode=" + mode,
                        str(Path(__file__).with_name("particle-value-attribution.qr")), str(path)],
                        capture_output=True, text=True, timeout=180)
                except subprocess.TimeoutExpired as error:
                    self.fail(f"attribution batch {first} exceeded 180s; last output: "
                              f"{error.stdout[-2000:] if error.stdout else ''}; stderr: {error.stderr}")
                self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
                self.assertEqual("", process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                actual.extend(rows)
                print(f"{mode}: models {first}-{first + len(batch) - 1}: {len(rows)} rows "
                      f"in {time.monotonic() - started:.3f}s", flush=True)
        self.assertEqual(len(expected), len(actual), "missing or extra attribution rows")
        for want, got in zip(expected, actual):
            self.assertEqual(want, got)


if __name__ == "__main__":
    unittest.main()
