#!/usr/bin/env python3
"""Diagnostic, not a conformance pass: retain P4's native finite-count failures.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from test_particle_model import schema


def cases():
    low, high = "9" * 80, "1" + "0" * 80
    def counted(outer):
        return ('<xs:sequence>' + f'<xs:sequence minOccurs="{outer}" maxOccurs="{outer}">'
                + '<xs:element name="b" minOccurs="0"/>'
                + f'<xs:element name="a" minOccurs="{low}" maxOccurs="{high}"/>'
                + '</xs:sequence><xs:element name="b"/></xs:sequence>')
    result = [("nested-adjacent-valid", schema(counted(low)), True),
              ("nested-adjacent-ambiguous", schema(counted(high)), False)]
    for value in ("2", "1073741825", "2147483647", "2147483648", high):
        result.append(("fixed-" + value, schema('<xs:sequence>'
                       + f'<xs:element name="a" minOccurs="{value}" maxOccurs="{value}"/>'
                       + '<xs:element name="a"/></xs:sequence>'), True))
    declarations = '<xs:complexType name="Base">' + f'<xs:sequence minOccurs="{high}" maxOccurs="{high}">'
    declarations += '<xs:element name="a"/></xs:sequence></xs:complexType>'
    result.append(("inherited-finite", schema('<xs:complexContent><xs:extension base="t:Base">'
                   + '<xs:sequence><xs:element name="a"/></xs:sequence></xs:extension></xs:complexContent>',
                   declarations), True))
    return [{"name": name, "schema": text, "schema_sha256": hashlib.sha256(text.encode()).hexdigest(),
             "expected_schema_ok": expected} for name, text, expected in result]


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = cases()
    with tempfile.TemporaryDirectory(prefix="native-particle-ranges-") as directory:
        path = Path(directory) / "cases.json"
        path.write_text(json.dumps(inputs), encoding="utf-8")
        result = subprocess.run(["qore", "-b", "--enable-debug",
                                 str(Path(__file__).with_name("native-particle-ranges.qr")), str(path)],
                                text=True, capture_output=True, timeout=30, check=True)
    if result.stderr:
        raise RuntimeError(result.stderr)
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    expected_keys = [(item["name"], stream) for item in inputs for stream in (False, True)]
    if [(row["case"], row["stream"]) for row in rows] != expected_keys:
        raise ValueError("missing, duplicated, or reordered native diagnostic row")
    by_name = {item["name"]: item for item in inputs}
    for row in rows:
        row["expected_schema_ok"] = by_name[row["case"]]["expected_schema_ok"]
        row["matches_expectation"] = row["schema_ok"] == row["expected_schema_ok"]
        if not row["expected_schema_ok"]:
            # Reject the ambiguous component for attribution, not lexical count truncation.
            row["matches_expectation"] &= "attribution" in row.get("description", "").lower()
    report = {"copyright": "Copyright (C) 2026 Qore Technologies, s.r.o.", "owner": "P4",
              "requirement": "XSD 1.0 nonNegativeInteger occurrence counts and cos-nonambig",
              "status": "diagnostic", "cases": inputs, "rows": rows,
              "failures": sum(not row["matches_expectation"] for row in rows),
              "root_cause": "The native lexical scanner saturates at INT_MAX, then rejects finite maxima "
                            "above the UNBOUNDED sentinel (1 << 30), before exact attribution runs."}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{len(inputs)} schemas / {len(rows)} DOM-reader rows: {report['failures']} failing P4 diagnostics")


if __name__ == "__main__":
    run()
