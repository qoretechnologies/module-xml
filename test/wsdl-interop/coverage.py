#!/usr/bin/env python3
"""Adjudicated Qore request/response coverage and an explicitly selected strict gate.

Copyright (C) 2026 Qore Technologies, s.r.o.
Full diagnostic coverage preserves failures assigned to later implementation phases.
The selected gate never accepts expected implementation failures as passing tests.
"""

import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import subprocess

from lxml import etree

import adjudicate
import contract
import corpus
import calendar_reference
import duration_reference
import binary_reference
from independent import SchemaJob, run as run_independent
import normative
import survey


ROOT = Path(__file__).resolve().parent
DIRECTIONS = ("request", "response")


def prepare(root: Path, source: dict) -> tuple[list[dict], dict]:
    """Bind every original to its adjudicated schema, actual port, binding and message parts."""
    cases = survey.inventory(root, "both")
    records = {record["case"]: record for record in source["cases"]}
    if len(records) != len(source["cases"]) or set(records) != {c["name"] for c in cases}:
        raise ValueError("source adjudication case inventory mismatch")
    for case in cases:
        record = records[case["name"]]
        if (type(record["source_decision"]["valid"]) is not bool or
                any(type(m["decision"]["valid"]) is not bool for m in record["messages"].values())):
            raise ValueError("source adjudication has a provisional classification")
        corpus.check_digest(Path(case["wsdl"]).read_bytes(), record["wsdl_sha256"], case["name"])
        identity = contract.describe(etree.parse(case["wsdl"], survey.parser(root)).getroot())
        if identity != record["contract"]:
            raise ValueError("source adjudication component identity changed")
        if len(identity["ports"]) != 1:
            raise ValueError("W3C echo fixture must identify one actual port")
        port = identity["ports"][0]
        binding = identity["bindings"][port["binding"]]
        operations = identity["port_types"][binding["port_type"]]["operations"]
        if len(operations) != 1 or binding["soap_version"] not in ("11", "12"):
            raise ValueError("W3C echo fixture must identify one SOAP operation")
        operation = operations[0]
        case["binding"] = etree.QName(port["binding"]).localname
        case["operation"] = operation["name"]
        case["identity"] = {"port": port, "binding": port["binding"], "operation": operation["name"],
                            "soap_version": binding["soap_version"], "directions": {}}
        for direction, io in (("request", "input"), ("response", "output")):
            message = operation[io]["message"]
            case["identity"]["directions"][direction] = {
                "message": message, "parts": identity["messages"][message]["parts"],
                "inline_schema_sha256": record["schemas"]["inline"]["sha256"]}
        if set(record["messages"]) != {m["file"] for m in case["messages"]}:
            raise ValueError("source adjudication message inventory mismatch")
        for message in case["messages"]:
            corpus.check_digest(Path(message["path"]).read_bytes(), record["messages"][message["file"]]["sha256"],
                                message["file"])
        case["messages"] = [dict(m, direction=d) for m in case["messages"] for d in DIRECTIONS]
    survey.validate_cases(cases)
    return cases, records


def value_checks(expected: etree._Element, actual: etree._Element, assertions: list[dict]) -> dict:
    """Check declared scalar values independently, using expanded paths and exact arithmetic."""
    if not assertions:
        return {"ok": None, "status": "unassessed", "reason": "typed/infoset preservation coverage pending"}
    results = []
    for assertion in assertions:
        try:
            before = normative.select_value(expected, assertion)
            after = normative.select_value(actual, assertion)
            datatype = assertion["datatype"]
            if datatype == "boolean":
                values = {"true": True, "1": True, "false": False, "0": False}
                before, after = before.strip(" \t\r\n"), after.strip(" \t\r\n")
                valid = before in values and after in values and values[before] == values[after]
            elif datatype == "duration":
                valid = duration_reference.compare(before, after) == 0
            elif datatype in {"hexBinary", "base64Binary"}:
                valid = binary_reference.value(datatype, before) == binary_reference.value(datatype, after)
            elif datatype in calendar_reference.FORMATS:
                valid = calendar_reference.value(datatype, before) == calendar_reference.value(datatype, after)
            elif datatype == "list":
                left, right = re.findall(r"[^ \t\r\n]+", before), re.findall(r"[^ \t\r\n]+", after)
                item_type = assertion["item_datatype"]
                valid = len(left) == len(right)
                if valid:
                    if item_type in {"string", "normalizedString", "token"}:
                        valid = left == right
                    elif item_type == "boolean":
                        booleans = {"true": True, "1": True, "false": False, "0": False}
                        valid = all(a in booleans and b in booleans and booleans[a] == booleans[b]
                                    for a, b in zip(left, right))
                    elif item_type == "duration":
                        valid = all(duration_reference.compare(a, b) == 0 for a, b in zip(left, right))
                    elif item_type in {"hexBinary", "base64Binary"}:
                        valid = all(binary_reference.value(item_type, a) == binary_reference.value(item_type, b)
                                    for a, b in zip(left, right))
                    elif item_type in calendar_reference.FORMATS:
                        valid = all(calendar_reference.value(item_type, a) == calendar_reference.value(item_type, b)
                                    for a, b in zip(left, right))
                    else:
                        valid = all(normative.same_number(item_type, a, b) for a, b in zip(left, right))
            elif datatype == "string":
                valid = before == after
            elif datatype in ("normalizedString", "token"):
                # Only XML whitespace is replaced/collapsed; NBSP and other Unicode spaces retain their values.
                before = before.translate(str.maketrans({"\t": " ", "\r": " ", "\n": " "}))
                after = after.translate(str.maketrans({"\t": " ", "\r": " ", "\n": " "}))
                if datatype == "token":
                    before = " ".join(part for part in before.split(" ") if part)
                    after = " ".join(part for part in after.split(" ") if part)
                valid = before == after
            else:
                valid = normative.same_number(datatype, before, after)
            results.append({"datatype": datatype, "expected": before, "actual": after, "ok": valid})
        except (ValueError, etree.LxmlError) as error:
            results.append({"ok": False, "reason": str(error)})
    return {"ok": all(r["ok"] for r in results), "status": "assessed", "assertions": results}


def validate_selection(selection: dict, records: dict) -> None:
    """Reject stale/empty/duplicate selections and undocumented expectations before testing."""
    if (not isinstance(selection, dict) or type(selection.get("format")) is not int or selection["format"] != 1
            or not isinstance(selection.get("cases"), dict) or not selection["cases"]):
        raise ValueError("invalid strict selection")
    for name, entry in selection["cases"].items():
        if name not in records or not isinstance(entry, dict):
            raise ValueError("strict selection names an absent case")
        record = records[name]
        if record["source_decision"]["valid"] is False:
            if entry != {"parse_error": "PARSE-XML-EXCEPTION" if "XML10-empty-document" in
                          record["source_decision"]["requirements"] else "WSDL-ERROR"}:
                raise ValueError("invalid schema rejection expectation")
            continue
        if set(entry) != {"messages"} or not isinstance(entry["messages"], dict) or not entry["messages"]:
            raise ValueError("strict selection needs explicit messages")
        for file, assertions in entry["messages"].items():
            if file not in record["messages"] or not isinstance(assertions, list):
                raise ValueError("strict selection names an absent message or malformed assertions")
            decision = record["messages"][file]["decision"]
            if decision["valid"] is True and not assertions:
                raise ValueError("strict valid messages require independent value assertions")
            if decision["valid"] is False and assertions:
                raise ValueError("invalid source message cannot expect successful serialization")
            for assertion in assertions:
                if (not isinstance(assertion, dict) or not isinstance(assertion.get("elements"), list)
                        or not assertion["elements"] or any(not isinstance(s, str) for s in assertion["elements"])
                        or assertion.get("datatype") not in {"list", "boolean", "string", "normalizedString", "token", "decimal", "float", "double", "duration", "hexBinary", "base64Binary",
                            *calendar_reference.FORMATS, *normative.UNSIGNED_MAX, *normative.INTEGER_BOUNDS}
                        or ("attribute" in assertion and not isinstance(assertion["attribute"], str))):
                    raise ValueError("malformed strict value assertion")
                if assertion["datatype"] == "list" and assertion.get("item_datatype") not in {
                        "boolean", "string", "normalizedString", "token", "decimal", "float", "double", "duration", "hexBinary", "base64Binary",
                        *calendar_reference.FORMATS, *normative.UNSIGNED_MAX, *normative.INTEGER_BOUNDS}:
                    raise ValueError("malformed strict list item assertion")


def assess(root: Path, source: dict, selection: dict, catalog: corpus.Catalog, qore: str = "qore") -> dict:
    """Run all cases and both directions; strict selection is a gate over the complete report."""
    cases, records = prepare(root, source)
    validate_selection(selection, records)
    resources = {survey.SOURCE + p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*.xsd")}
    for uri, data in catalog.resources.items():
        if uri in resources and resources[uri] != data:
            raise ValueError("conflicting corpus resource")
        resources[uri] = data
    rows = survey.run_worker(cases, {uri: data.decode("utf-8") for uri, data in resources.items()}, qore)
    accounting = survey.stage_accounting(cases, rows)
    indexed = {(r["case"], r.get("file"), r.get("direction"), r["stage"]): r for r in rows}
    jobs, schemas = [], {}
    for case in cases:
        name = case["name"]
        document = etree.parse(case["wsdl"], survey.parser(root, catalog))
        schema = document.find(f"{{{contract.WSDL}}}types/{{{contract.XSD}}}schema")
        data = etree.tostring(schema)
        corpus.check_digest(data, records[name]["schemas"]["inline"]["sha256"], name + "/inline")
        uri = survey.SOURCE + name + f"/echo{name}.wsdl"
        documents = {}
        for message in case["messages"]:
            row = indexed.get((name, message["file"], message["direction"], "serialize"))
            if row and row["ok"]:
                key = message["file"] + "/" + message["direction"]
                try:
                    documents[key] = etree.tostring(survey.payload(row["body"].encode(), survey.parser(root, catalog)))
                except (etree.LxmlError, ValueError, OSError) as error:
                    row["output_document_error"] = str(error)
        jobs.append(SchemaJob(name, uri, data, documents))
        try:
            schemas[name] = etree.XMLSchema(etree.fromstring(data, survey.parser(root, catalog), base_url=uri))
        except (etree.LxmlError, OSError) as error:
            schemas[name] = str(error)
    oracle = run_independent(jobs, resources)
    outcomes, failures, selected_failures = [], [], []
    totals = Counter()
    for case in cases:
        name = case["name"]
        record = records[name]
        parsed = indexed[name, None, None, "parse"]
        selected = selection["cases"].get(name, {})
        valid_schema = record["source_decision"]["valid"]
        expected_error = "PARSE-XML-EXCEPTION" if "XML10-empty-document" in record["source_decision"]["requirements"] else "WSDL-ERROR"
        parse_ok = parsed["ok"] if valid_schema else not parsed["ok"] and parsed["err"] == expected_error
        item = {"case": name, "implementation_phase": record["implementation_phase"], "identity": case["identity"],
                "source_valid": valid_schema, "parse": parsed, "schema_xerces": oracle["schemas"][name],
                "expected_parse": "success" if valid_schema else expected_error,
                "parse_requirement_passed": parse_ok, "messages": []}
        if not parse_ok:
            failure = {"case": name, "stage": "parse", "phase": record["implementation_phase"]}
            failures.append(failure)
            if selected:
                selected_failures.append(failure)
        for message in case["messages"]:
            file, direction = message["file"], message["direction"]
            decision = record["messages"][file]["decision"]
            decode = indexed.get((name, file, direction, "deserialize"))
            encode = indexed.get((name, file, direction, "serialize"))
            result = {"file": file, "direction": direction, "source_valid": decision["valid"],
                      "requirements": decision["requirements"], "expected_deserialize": "success" if
                      decision["valid"] else "SOAP-DESERIALIZATION-ERROR", "failures": [],
                      "deserialize": decode, "serialize": encode}
            if not valid_schema:
                result["status"] = "invalid_source"
                result["rejection_passed"] = parse_ok
            elif decode is None:
                result["status"] = "unreachable"
                result["failures"].append("parse")
            elif not decision["valid"]:
                result["status"] = "invalid_source"
                result["rejection_passed"] = not decode["ok"] and decode["err"] == "SOAP-DESERIALIZATION-ERROR"
                if not result["rejection_passed"]:
                    result["failures"].append("invalid_input_accepted" if decode["ok"] else "wrong_error_category")
            elif not decode["ok"]:
                result["status"] = "valid_input_requiring_fix"
                result["failures"].append("deserialize")
            elif not encode["ok"]:
                result["status"] = "valid_input_requiring_fix"
                result["failures"].append("serialize")
            else:
                result["status"] = "valid_input_assessed"
            if encode and encode["ok"]:
                key = file + "/" + direction
                schema = schemas[name]
                result["output_xerces"] = oracle["documents"].get(key)
                result["output_lxml"] = ({"ok": None, "desc": schema} if isinstance(schema, str) else
                    survey.validate(schema, encode["body"].encode(), survey.parser(root, catalog)))
                if decision["valid"] and (encode.get("output_document_error") or
                        result["output_xerces"] is None or result["output_xerces"]["ok"] is not True):
                    result["failures"].append("output_schema")
                assertions = selected.get("messages", {}).get(file)
                if assertions is None:
                    assertions = [a for a in decision.get("assertions", []) if a["valid"] and a["datatype"] != "gMonth"]
                expected = actual = None
                try:
                    expected = survey.payload(Path(message["path"]).read_bytes(), survey.parser(root, catalog))
                    actual = survey.payload(encode["body"].encode(), survey.parser(root, catalog))
                    result["values"] = value_checks(expected, actual, assertions)
                    envelope = etree.fromstring(encode["body"].encode(), survey.parser(root, catalog))
                    result["binding_version_passed"] = envelope.tag == "{" + survey.SOAP_NAMESPACES[
                        0 if case["identity"]["soap_version"] == "11" else 1] + "}Envelope"
                except (etree.LxmlError, ValueError, OSError) as error:
                    result["values"] = {"ok": False, "reason": str(error)}
                    result["binding_version_passed"] = False
                if decision["valid"] and result["values"]["ok"] is False:
                    result["failures"].append("value_preservation")
                if (result["output_xerces"] is not None and result["output_lxml"]["ok"] is not
                        result["output_xerces"]["ok"]):
                    # Only the explicitly adjudicated numeric precision limitation
                    # can be settled here. Every new disagreement stays a failure.
                    known_precision = (decision["valid"] and result["output_xerces"]["ok"] is True
                        and result["values"]["ok"] is True and "XSD10-arbitrary-number" in decision["requirements"])
                    unchanged_invalid_idrefs = (not decision["valid"] and result["output_lxml"]["ok"] is True
                        and result["output_xerces"]["ok"] is False and "XSD10-IDREF" in decision["requirements"]
                        and "cvc-id.1" in result["output_xerces"]["desc"]
                        and expected is not None and actual is not None
                        and normative.same_token_content(expected, actual))
                    result["output_oracle_disagreement"] = {
                        "adjudicated": known_precision or unchanged_invalid_idrefs,
                        "requirements": decision["requirements"]}
                    if not known_precision and not unchanged_invalid_idrefs:
                        result["failures"].append("output_oracle_disagreement")
                if decision["valid"] and not result["binding_version_passed"]:
                    result["failures"].append("binding_version")
            if result["failures"]:
                if decision["valid"]:
                    result["status"] = "valid_input_requiring_fix"
                failure = {"case": name, "file": file, "direction": direction,
                           "stages": result["failures"], "phase": record["implementation_phase"]}
                failures.append(failure)
                if file in selected.get("messages", {}):
                    selected_failures.append(failure)
            for stage, field in (("output_lxml", "output_lxml"), ("output_xerces", "output_xerces"),
                                  ("values", "values")):
                counts = accounting["counts"].setdefault(stage, {state: 0 for state in
                    ("ok", "failed", "unreachable", "unassessed", "missing", "skipped")})
                check = result.get(field)
                state = ("unreachable" if not encode or not encode["ok"] else "unassessed" if
                         check is None or check["ok"] is None else "ok" if check["ok"] else "failed")
                counts[state] += 1
            totals[result["status"]] += 1
            item["messages"].append(result)
        outcomes.append(item)
    version = subprocess.run([qore, "--version"], text=True, capture_output=True, check=True, timeout=10)
    if version.stderr or not version.stdout:
        raise RuntimeError("missing Qore version or unexpected version diagnostics")
    return {"format": 1, "scope": {"wsdls": len(cases), "input_files": sum(len(c["messages"]) for c in cases) // 2,
                "directions": list(DIRECTIONS), "input_soap_versions": ["11", "12"], "network": False,
                "not_assessed": ["full typed/infoset preservation outside explicit assertions", "HTTP", "SOAP processing",
                                 "actual SOAP 1.2 binding interoperability in the W3C echo set"]},
            "source_report_sha256": hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest(),
            "selection_sha256": hashlib.sha256(json.dumps(selection, sort_keys=True).encode()).hexdigest(),
            "versions": {**oracle["versions"], "qore": version.stdout, "lxml": list(etree.LXML_VERSION),
                         "libxml2": list(etree.LIBXML_VERSION), "wsdl_module_sha256": hashlib.sha256(
                             (ROOT.parents[1] / "qlib/WSDL.qm").read_bytes()).hexdigest()},
            "catalog_sha256": dict(catalog.sha256),
            "stage_accounting": accounting, "counts": dict(sorted(totals.items())),
            "selected_scope": {"wsdls": len(selection["cases"]), "message_directions":
                               2 * sum(len(e.get("messages", {})) for e in selection["cases"].values())},
            "failures": failures, "selected_failures": selected_failures, "cases": outcomes}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("corpus", type=Path)
    cli.add_argument("--source-report", type=Path, default=ROOT / "adjudication-report.json")
    cli.add_argument("--selection", type=Path, default=ROOT / "strict-selection.json")
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--strict", action="store_true", help="require every selected Qore requirement to pass")
    args = cli.parse_args()
    root = args.corpus.resolve()
    adjudicate.verify_original_corpus(root)
    source = corpus.read_manifest(args.source_report)
    if source["unclassified"]:
        raise ValueError("source report contains unclassified disagreements")
    result = assess(root, source, corpus.read_manifest(args.selection), corpus.Catalog())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": result["counts"], "stages": result["stage_accounting"]["counts"],
                      "failures": len(result["failures"]), "selected_failures": result["selected_failures"]}, indent=2))
    if args.strict and result["selected_failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
