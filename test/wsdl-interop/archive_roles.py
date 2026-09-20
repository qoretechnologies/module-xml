#!/usr/bin/env python3
"""Account for every original archive artifact, aggregate source and import edge.

Copyright (C) 2026 Qore Technologies, s.r.o.
Historical toolkit programs are inventoried as data and never executed.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urljoin

from lxml import etree

import contract
import corpus
from independent import SchemaJob, run as run_independent
import survey


ROOT = Path(__file__).resolve().parent
BASE = "http://www.w3.org/2002/ws/"
PREFIX = corpus.EXAMPLES.as_posix() + "/"
XS = "{" + contract.XSD + "}"
WS = "{" + contract.WSDL + "}"


def signature(node: etree._Element) -> tuple:
    """Compare source copies by expanded names, text, attributes and used QName context.

    Only whitespace between element children is treated as source formatting.
    Scalar whitespace and QName prefix bindings remain significant.
    """
    children = [c for c in node if isinstance(c.tag, str)]
    text = node.text or ""
    if children and not text.strip():
        text = ""
    bindings = {}
    for value in [text, *node.attrib.values()]:
        for prefix in re.findall(r"(?<![\w.-])([A-Za-z_][\w.-]*):[A-Za-z_]", value):
            bindings[prefix] = node.nsmap.get(prefix)
    return (node.tag, tuple(sorted(node.attrib.items())), text, tuple(sorted(bindings.items())),
            tuple((signature(child), child.tail if (child.tail or "").strip() else "") for child in children))


def schema_grammar_errors(schema: etree._Element) -> list[dict]:
    """Apply the specific normative schema grammar rules violated by aggregate generators."""
    declared = False
    errors = []
    declarations = {XS + name for name in ("simpleType", "complexType", "group", "attributeGroup", "element",
                                           "attribute", "notation")}
    for child in schema:
        if not isinstance(child.tag, str):
            continue
        if child.tag in (XS + "include", XS + "import", XS + "redefine") and declared:
            errors.append({"requirement": "XSD10-schema-import-order", "line": child.sourceline,
                           "element": child.tag})
        elif child.tag not in declarations | {XS + n for n in ("annotation", "include", "import", "redefine")}:
            errors.append({"requirement": "XSD10-schema-content", "line": child.sourceline,
                           "element": child.tag})
        declared = declared or child.tag in declarations
    return errors


def assess(root: Path, *, worker_timeout=60) -> dict:
    """Verify the complete archive, classify every file role and close source dependency evidence."""
    survey.validate_worker_timeout(worker_timeout)
    inventory = corpus.verify_extraction(root)
    expected = set(inventory["files"])
    actual = {p.relative_to(root).as_posix() for p in (root / "databinding").rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("archive role inventory has missing or extra files")
    catalog = corpus.Catalog()
    defects = corpus.read_manifest(ROOT / "corpus/source-defects.json")
    missing = {d["uri"]: d for d in defects["resources"]}
    if len(missing) != len(defects["resources"]) or any(d["http_status"] != 404 for d in missing.values()):
        raise ValueError("invalid missing-location evidence")
    source = corpus.read_manifest(ROOT / "adjudication-report.json")
    by_case = {c["case"]: c for c in source["cases"]}
    if len(by_case) != len(source["cases"]) or set(by_case) != {
            p.parent.name for p in (root / corpus.EXAMPLES).glob("*/echo*.wsdl")
            if not p.name.endswith("-wsdl20.wsdl")}:
        raise ValueError("source adjudication case inventory mismatch")
    roles, imports, extras, jobs = {}, [], [], []
    resources = dict(catalog.resources)
    for name in expected:
        if name.endswith(".xsd"):
            resources[BASE + name] = (root / name).read_bytes()
    for name in sorted(expected):
        path = root / name
        item = {**inventory["files"][name]}
        if name.startswith(PREFIX) and len(path.relative_to(root / corpus.EXAMPLES).parts) == 2:
            relative = name.removeprefix(PREFIX)
            case = path.parent.name
            item["case"] = case
            if path.name.endswith("-wsdl20.wsdl"):
                item.update(role="wsdl2-description", status="outside-plan-WSDL2")
            elif path.suffix == ".wsdl":
                item.update(role="echo-wsdl1", source_valid=by_case[case]["source_decision"]["valid"])
            elif path.suffix == ".xsd":
                echo = root / corpus.EXAMPLES / case / f"echo{case}.xsd"
                if path.read_bytes() != echo.read_bytes():
                    raise ValueError(f"standalone/echo schema evidence differs: {name}")
                item.update(role="echo-schema" if path.name.startswith("echo") else "duplicate-echo-schema",
                            assessed_by="adjudication-report.json", wsdl_source_valid=by_case[case]["source_decision"]["valid"],
                            schema_oracles={oracle: by_case[case]["schemas"]["echo"][oracle]["ok"]
                                            for oracle in ("lxml", "xerces")})
            elif relative in by_case[case]["messages"]:
                item.update(role="soap-message", source_valid=by_case[case]["messages"][relative]["decision"]["valid"])
            elif path.suffix == ".xml" and not path.name.endswith("-patterns.xml"):
                echo_name = path.name if path.name.startswith("echo") else "echo" + path.name
                echo = path.with_name(echo_name)
                echo_node = etree.parse(str(echo), survey.parser(root / corpus.EXAMPLES)).getroot()
                if path.name.startswith("echo"):
                    soap = path.with_name(path.stem + "-soap11.xml")
                    counterpart = survey.payload(soap.read_bytes(), survey.parser(root / corpus.EXAMPLES))
                    original = echo_node
                    item["role"] = "bare-echo-payload"
                else:
                    elements = [c for c in echo_node if isinstance(c.tag, str)]
                    if len(elements) != 1:
                        raise ValueError("raw fragment must have one corresponding echo child")
                    counterpart = elements[0]
                    original = etree.parse(str(path), survey.parser(root / corpus.EXAMPLES)).getroot()
                    item["role"] = "raw-payload-fragment"
                if signature(original) != signature(counterpart):
                    raise ValueError(f"source payload copy differs: {name}")
                item.update(assessed_by="adjudication-report.json", corresponding_soap_file=
                            (echo.with_name(echo.stem + "-soap11.xml")).relative_to(root).as_posix())
            else:
                item["role"] = "pattern-metadata" if path.name.endswith("-patterns.xml") else "documentation"
        elif name.startswith("databinding/edcopy/toolkits/"):
            item["role"] = "historical-toolkit-contract" if path.suffix in (".wsdl", ".xsd") else "historical-toolkit-data"
        else:
            item["role"] = "aggregate-source" if path.suffix in (".wsdl", ".xsd") else "aggregate-metadata"
        roles[name] = item
        if path.suffix not in (".wsdl", ".xsd"):
            continue
        document = etree.fromstring(path.read_bytes(), etree.XMLParser(no_network=True, resolve_entities=False),
                                    base_url=BASE + name)
        for node in document.iter():
            if node.tag not in (XS + "import", XS + "include", XS + "redefine", WS + "import"):
                continue
            location = node.get("schemaLocation") or node.get("location")
            edge = {"source": name, "element": node.tag, "line": node.sourceline,
                    "namespace": node.get("namespace"), "location": location}
            if location is None:
                edge["status"] = "no-location-hint"
            else:
                uri = urljoin(node.base, location)
                edge["uri"] = uri
                if uri in resources:
                    data = resources[uri]
                    edge.update(status="pinned-resource" if data else "invalid-empty-source",
                                sha256=hashlib.sha256(data).hexdigest())
                elif uri in missing and name in missing[uri]["references"]:
                    edge.update(status="invalid-source-location", evidence=missing[uri])
                else:
                    raise ValueError(f"unclassified dependency: {name}: {uri}")
            imports.append(edge)
        if item["role"] not in ("aggregate-source", "historical-toolkit-contract"):
            continue
        schemas = [document] if document.tag == XS + "schema" else document.findall(WS + "types/" + XS + "schema")
        context_evidence = [{"name": n.get("name"), "line": n.sourceline, "type": n.get("type"),
                             "expanded_type": contract.qname(n, n.get("type"))}
                            for n in document.iter() if n.get("type") == "string"
                            and n.nsmap.get(None) == contract.XSD]
        record = {"file": name, "phase": "P2" if context_evidence else "P6", "schemas": [],
                  "default_namespace_type_evidence": context_evidence}
        if context_evidence:
            record["namespace_finding"] = {
                "requirement": "https://www.w3.org/TR/xmlschema-1/#src-resolve",
                "reproducer": "archive_roles.py EXTRACTION --output REPORT.json",
                "cause": "Namespaces::doType() uses the shared default_ns; the declaration's local default "
                         "namespace is not active. resolveType() then looks for an unqualified custom string type.",
                "implementation": "qlib/WSDL.qm:7952; qlib/WSDL.qm:8595"}
        if document.tag == WS + "definitions":
            record["contract"] = contract.describe(document)
        for index, schema in enumerate(schemas):
            key = name + "/schema-" + str(index)
            data = etree.tostring(schema)
            grammar = schema_grammar_errors(schema)
            try:
                etree.XMLSchema(etree.fromstring(data, survey.parser(root / corpus.EXAMPLES, catalog),
                                                base_url=BASE + name))
                result = {"ok": True, "desc": ""}
            except (etree.LxmlError, OSError) as error:
                result = {"ok": False, "desc": str(error)}
            record["schemas"].append({"id": key, "sha256": hashlib.sha256(data).hexdigest(),
                                      "lxml": result, "normative_errors": grammar})
            jobs.append(SchemaJob(key, BASE + name, data))
        extras.append(record)
    independent = run_independent(jobs, resources)
    if set(missing) != {e["uri"] for e in imports if e["status"] == "invalid-source-location"}:
        raise ValueError("unused missing-location evidence")
    for record in extras:
        for schema in record["schemas"]:
            schema["xerces"] = independent["schemas"][schema["id"]]
            if schema["normative_errors"]:
                schema["source_valid"] = False
            elif schema["lxml"]["ok"] and schema["xerces"]["ok"]:
                schema["source_valid"] = True
            else:
                raise ValueError(f"unclassified aggregate schema: {schema['id']}")
        record["source_valid"] = all(s["source_valid"] for s in record["schemas"])
        if record.get("contract", {}).get("errors"):
            raise ValueError(f"unclassified historical WSDL component error: {record['file']}")
    qore_cases = [{"name": c["file"], "wsdl": str(root / c["file"]),
                   "base": BASE + c["file"].rsplit("/", 1)[0] + "/", "messages": [],
                   "schema_only": c["file"].endswith(".xsd"), "parse_only": True} for c in extras]
    parsed = survey.run_worker(qore_cases, {uri: data.decode("utf-8") for uri, data in resources.items()},
                               worker_timeout=worker_timeout)
    for record, row in zip(extras, parsed):
        record["qore"] = row
        empty_import = any(e["source"] == record["file"] and e["status"] == "invalid-empty-source" for e in imports)
        expected_errors = ["WSDL-ERROR", "PARSE-XML-EXCEPTION"] if empty_import else ["WSDL-ERROR"]
        record["expected_parse"] = "success" if record["source_valid"] else expected_errors
        record["parse_requirement_passed"] = row["ok"] if record["source_valid"] else (
            not row["ok"] and row["err"] in expected_errors)
        if not record["source_valid"]:
            # Credit the ordered schema check only for its own diagnostic and a
            # corresponding independently established source violation.
            requirement = ("XSD10-schema-import-order" if "must precede component declarations" in row.get("desc", "")
                           else "XSD10-schema-content")
            violations = {e["requirement"] for schema in record["schemas"] for e in schema["normative_errors"]}
            if (not row["ok"] and row["err"] == "WSDL-ERROR" and row["desc"].startswith("schema grammar:")
                    and requirement in violations):
                record["grammar_rejection"] = {"status": "passed", "phase": "P2", "requirement": requirement}
            else:
                record["grammar_rejection"] = {"status": "unassessed", "phase": "P6",
                    "reason": "earlier namespace/import failure does not establish schema grammar validation"}
    # The aggregate message lists contain unqualified echo wrappers. Link each
    # original entry to the separately supplied, correctly qualified echo file.
    message_files = {}
    for case, record in by_case.items():
        for file in record["messages"]:
            stem = Path(file).name.removeprefix("echo" + case + "-")
            key = stem.removesuffix(".xml")
            if key in message_files:
                raise ValueError("duplicate aggregate-to-echo message identity")
            message_files[key] = file
    aggregate_messages = []
    for version in ("11", "12"):
        name = PREFIX + f"examples-soap{version}.xml"
        document = etree.parse(str(root / name)).getroot()
        seen = set()
        for message in document:
            identity = message.get("{http://www.w3.org/XML/1998/namespace}id")
            if not identity or identity in seen:
                raise ValueError("missing/duplicate aggregate message identity")
            seen.add(identity)
            file = message_files[identity + "-soap" + version]
            envelope = next(c for c in message if isinstance(c.tag, str))
            value = survey.payload(etree.tostring(envelope), survey.parser(root / corpus.EXAMPLES))
            expected_root = "{" + survey.SOURCE + "}echo" + file.split("/")[0]
            if value.tag != etree.QName(expected_root).localname:
                raise ValueError("aggregate wrapper namespace evidence changed")
            aggregate_messages.append({"source": name, "id": identity, "echo_file": file,
                "actual_root": value.tag, "expected_root": expected_root, "source_valid": False,
                "requirement": "XSD10-global-element-namespace", "phase": "P2"})
        if len(seen) != sum(f.endswith("-soap" + version + ".xml") for c in by_case.values() for f in c["messages"]):
            raise ValueError("aggregate message inventory incomplete")
    version = subprocess.run(["qore", "--version"], capture_output=True, text=True, check=True, timeout=10)
    if version.stderr or not version.stdout:
        raise RuntimeError("missing Qore version or unexpected diagnostics")
    return {"format": 1, "archive_sha256": inventory["archive"]["sha256"], "files": roles,
            "role_counts": dict(sorted(Counter(v["role"] for v in roles.values()).items())),
            "imports": imports, "additional_contracts": extras, "aggregate_messages": aggregate_messages,
            "unclassified": [], "versions": {**independent["versions"], "qore": version.stdout,
                "wsdl_module_sha256": hashlib.sha256((ROOT.parents[1] / "qlib/WSDL.qm").read_bytes()).hexdigest()},
            "requirements": {
                "XSD10-schema-import-order": "https://www.w3.org/TR/xmlschema-1/#element-schema",
                "XSD10-schema-content": "https://www.w3.org/TR/xmlschema-1/#element-schema",
                "XSD10-global-element-namespace": "https://www.w3.org/TR/xmlschema-1/#cvc-elt"}}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("extraction", type=Path, help="directory containing databinding/")
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--worker-timeout", type=survey.parse_worker_timeout, default=60,
                     help="bounded Qore worker timeout in seconds (1–3600; default: 60)")
    args = cli.parse_args()
    report = assess(args.extraction.resolve(), worker_timeout=args.worker_timeout)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"roles": report["role_counts"], "import_edges": len(report["imports"]),
                      "additional_contracts": len(report["additional_contracts"]),
                      "aggregate_messages": len(report["aggregate_messages"])}, indent=2))


if __name__ == "__main__":
    main()
