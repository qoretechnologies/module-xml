#!/usr/bin/env python3
"""Compare inline and echo schemas with independent oracles and record adjudications.

Copyright (C) 2026 Qore Technologies, s.r.o.
Produces diagnostic evidence; --strict requires every disagreement to be adjudicated.
It does not certify Qore's values, WSDL grammar, HTTP behavior or SOAP processing.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from lxml import etree

import contract
import corpus as corpus_tools
from independent import SchemaJob, run as run_independent
from normative import check_assertions
import survey


ROOT = Path(__file__).resolve().parent


def verify_original_corpus(root: Path) -> None:
    """Verify every archive file and forbid extra files in the surveyed source tree."""
    manifest = corpus_tools.verify_extraction(root.parents[3])
    prefix = corpus_tools.EXAMPLES.as_posix() + "/"
    expected = {name.removeprefix(prefix) for name in manifest["files"] if name.startswith(prefix)}
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if expected != actual:
        raise ValueError(f"survey source tree differs from pinned inventory: "
                         f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")


def validate_decisions(decisions: dict) -> None:
    """Reject malformed, provisional, or undocumented adjudication entries."""
    if not isinstance(decisions, dict) or type(decisions.get("format")) is not int or decisions["format"] != 1:
        raise ValueError("invalid adjudication format")
    for section in ("schemas", "messages", "historical_outputs", "requirements", "ownership"):
        if not isinstance(decisions.get(section), dict):
            raise ValueError(f"invalid adjudication section: {section}")
    for required in ("XSD10-schema", "XSD10-payload"):
        if required not in decisions["requirements"]:
            raise ValueError(f"missing requirement: {required}")
    for key, requirement in decisions["requirements"].items():
        if (not isinstance(requirement, dict) or not isinstance(requirement.get("url"), str)
                or not requirement["url"].startswith("https://") or not isinstance(requirement.get("reason"), str)
                or not requirement["reason"].strip()):
            raise ValueError(f"undocumented adjudication requirement: {key}")
    for key, phase in decisions["ownership"].items():
        if phase not in {f"P{i}" for i in range(1, 10)}:
            raise ValueError(f"invalid implementation phase: {key}")
    for section in ("schemas", "messages", "historical_outputs"):
        for key, decision in decisions[section].items():
            if (not isinstance(decision, dict) or type(decision.get("valid")) is not bool
                    or not isinstance(decision.get("requirements"), list) or not decision["requirements"]):
                raise ValueError(f"invalid adjudication decision: {key}")
            for requirement in decision["requirements"]:
                if not isinstance(requirement, str) or requirement not in decisions["requirements"]:
                    raise ValueError(f"unknown adjudication requirement: {requirement}")


def assess(root: Path, cases: list[dict], catalog: corpus_tools.Catalog, decisions: dict,
           historical: dict) -> dict:
    """Assess each original payload and retained unassessed output against both schema sources.

    Explicit specification decisions override oracle agreement; no fixture bytes
    or oracle results are rewritten. An unclassified disagreement stays visible.
    """
    validate_decisions(decisions)
    case_ids, message_ids = set(), set()
    for case in cases:
        if case["name"] in case_ids:
            raise ValueError(f"duplicate case: {case['name']}")
        case_ids.add(case["name"])
        for message in case["messages"]:
            if message["file"] in message_ids:
                raise ValueError(f"duplicate message: {message['file']}")
            message_ids.add(message["file"])
    schemas, jobs, records = {}, [], []
    resources = dict(catalog.resources)
    for path in root.rglob("*.xsd"):
        uri = survey.SOURCE + path.relative_to(root).as_posix()
        data = path.read_bytes()
        if uri in resources and resources[uri] != data:
            raise ValueError(f"catalog conflicts with corpus: {uri}")
        resources[uri] = data
    retained = {}
    for row in historical.get("rows", []):
        if row.get("output_validation", {}).get("ok", True) is None:
            retained.setdefault(row["case"], {})[row["file"]] = row["body"].encode()
    for case in cases:
        name = case["name"]
        document = etree.parse(case["wsdl"], survey.parser(root, catalog))
        inline = document.findall(f"{{{contract.WSDL}}}types/{{{contract.XSD}}}schema")
        if len(inline) != 1:
            raise ValueError(f"expected one inline schema in W3C echo contract: {name}")
        record = {"case": name, "wsdl_sha256": hashlib.sha256(Path(case["wsdl"]).read_bytes()).hexdigest(),
                  "contract": contract.describe(document.getroot()), "schemas": {}, "messages": {},
                  "historical_outputs": {}}
        for source, data in (("inline", etree.tostring(inline[0])),
                             ("echo", (root / name / f"echo{name}.xsd").read_bytes())):
            key = name + "/" + source
            uri = survey.SOURCE + name + f"/echo{name}.xsd"
            documents = {}
            for message in case["messages"]:
                documents[message["file"] + "/" + source] = etree.tostring(survey.payload(
                    Path(message["path"]).read_bytes(), survey.parser(root, catalog)))
            for file, wire in retained.get(name, {}).items():
                documents["historical-output/" + file + "/" + source] = etree.tostring(
                    survey.payload(wire, survey.parser(root, catalog)))
            jobs.append(SchemaJob(key, uri, data, documents))
            try:
                schema = etree.XMLSchema(etree.fromstring(data, survey.parser(root, catalog), base_url=uri))
                schemas[key] = schema
                outcome = {"ok": True, "desc": ""}
            except (etree.LxmlError, OSError) as error:
                outcome = {"ok": False, "desc": str(error)}
            record["schemas"][source] = {"sha256": hashlib.sha256(data).hexdigest(), "lxml": outcome}
            for identity, payload in documents.items():
                schema = schemas.get(key)
                if schema is None:
                    value = {"ok": None, "desc": "schema compilation failed: " + key}
                else:
                    node = etree.fromstring(payload, survey.parser(root, catalog))
                    valid = schema.validate(node)
                    value = {"ok": valid, "desc": "" if valid else str(schema.error_log.last_error)}
                source_file = identity.removesuffix("/" + source)
                target = record["messages"]
                if source_file.startswith("historical-output/"):
                    source_file = source_file.removeprefix("historical-output/")
                    target = record["historical_outputs"]
                target.setdefault(source_file, {}).setdefault(source, {})["lxml"] = value
        records.append(record)
    independent = run_independent(jobs, resources)
    unclassified = []
    for record in records:
        name = record["case"]
        source_decision = decisions.get("schemas", {}).get(name)
        schema_valid = True
        for source, value in record["schemas"].items():
            value["xerces"] = independent["schemas"][name + "/" + source]
            schema_valid = schema_valid and value["lxml"]["ok"] and value["xerces"]["ok"]
        source_errors = record["contract"]["errors"] or record["contract"]["imports"]
        if source_decision:
            record["source_decision"] = source_decision
        elif schema_valid and not source_errors:
            record["source_decision"] = {"valid": True, "requirements": ["XSD10-schema"]}
        else:
            record["source_decision"] = {"valid": None, "requirements": []}
            unclassified.append(name + "/schema")
        for kind in ("messages", "historical_outputs"):
            for file, checks in record[kind].items():
                oracle_key = ("historical-output/" if kind == "historical_outputs" else "") + file
                for source, outcome in checks.items():
                    outcome["xerces"] = independent["documents"][oracle_key + "/" + source]
                decision = decisions.get(kind, {}).get(file)
                valid = all(outcome[validator]["ok"] is True for outcome in checks.values()
                            for validator in ("lxml", "xerces"))
                if decision is None and valid:
                    decision = {"valid": True, "requirements": ["XSD10-payload"]}
                if decision is None:
                    unclassified.append(oracle_key)
                    decision = {"valid": None, "requirements": []}
                checks["decision"] = decision
                wire = (root / file).read_bytes() if kind == "messages" else retained[name][file]
                checks["sha256"] = hashlib.sha256(wire).hexdigest()
                if "assertions" in decision:
                    checks["normative_assertions"] = check_assertions(
                        survey.payload(wire, survey.parser(root, catalog)), decision["assertions"])
        # Record future implementation ownership even where an invalid source is
        # rejected already. A source defect never closes that feature's test coverage.
        record["implementation_phase"] = decisions.get("ownership", {}).get(name, "P9")
    known_cases = {record["case"] for record in records}
    known_messages = {file for record in records for file in record["messages"]}
    known_outputs = {file for record in records for file in record["historical_outputs"]}
    for section, known in (("schemas", known_cases), ("messages", known_messages),
                            ("historical_outputs", known_outputs)):
        for key, decision in decisions.get(section, {}).items():
            if key not in known:
                raise ValueError(f"adjudication names an absent {section} case: {key}")
    counts = Counter()
    for record in records:
        counts["wsdl_valid" if record["source_decision"]["valid"] is True else
               "wsdl_invalid_source" if record["source_decision"]["valid"] is False else "wsdl_unclassified"] += 1
        for kind in ("messages", "historical_outputs"):
            for value in record[kind].values():
                status = value["decision"]["valid"]
                counts[kind + ("_valid" if status is True else "_invalid_source" if status is False
                               else "_unclassified")] += 1
    return {"format": 1, "scope": {"schema": "XSD 1.0 Second Edition with errata", "soap_versions": ["11", "12"],
                "network": False, "checks": ["inline schema", "echo schema", "payload schema validity",
                    "WSDL component identity", "retained historical unassessed outputs"],
                "not_assessed": ["complete WSDL grammar", "Qore typed values", "SOAP processing", "HTTP",
                                 "binding interoperability"]},
            "versions": {**independent["versions"], "lxml": list(etree.LXML_VERSION),
                         "libxml2": list(etree.LIBXML_VERSION)}, "catalog_sha256": dict(catalog.sha256),
            "counts": dict(sorted(counts.items())), "unclassified": unclassified, "cases": records}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("corpus", type=Path)
    cli.add_argument("--decisions", type=Path, default=ROOT / "adjudications.json")
    cli.add_argument("--catalog", type=Path, default=corpus_tools.CATALOG)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--strict", action="store_true", help="fail if any source disagreement is unclassified")
    args = cli.parse_args()
    root = args.corpus.resolve()
    verify_original_corpus(root)
    cases = survey.inventory(root, "both")
    decisions = corpus_tools.read_manifest(args.decisions)
    report = assess(root, cases, corpus_tools.Catalog(args.catalog), decisions,
                    json.loads((ROOT / "findings.json").read_text()))
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"counts": report["counts"], "unclassified": report["unclassified"]}, indent=2))
    if args.strict and report["unclassified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
