#!/usr/bin/env python3
"""Survey an extracted W3C Databinding corpus with local Qore and libxml2.

Copyright (C) 2026 Qore Technologies, s.r.o.
Requires Python 3.10+, lxml, qore, and the Qore xml/json modules. No network I/O.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import unquote, urlparse

from lxml import etree


SOURCE = "http://www.w3.org/2002/ws/databinding/examples/6/09/"
SOAP_NAMESPACES = (
    "http://schemas.xmlsoap.org/soap/envelope/",
    "http://www.w3.org/2003/05/soap-envelope",
)


def inventory(corpus, version):
    """Include every echo WSDL 1.1; never silently drop a case that fails to parse."""
    cases = []
    for directory in sorted(corpus.iterdir()):
        wsdl = directory / f"echo{directory.name}.wsdl"
        if not directory.is_dir() or not wsdl.is_file():
            continue
        messages = []
        for path in sorted(directory.glob("*-soap*.xml")):
            if version != "both" and not path.name.endswith(f"-soap{version}.xml"):
                continue
            messages.append({"file": path.relative_to(corpus).as_posix(), "path": str(path)})
        cases.append({"name": directory.name, "wsdl": str(wsdl),
                      "base": SOURCE + directory.name + "/", "messages": messages})
    if not cases:
        raise ValueError(f"no echo WSDL 1.1 fixtures found in {corpus}")
    return cases


class CorpusResolver(etree.Resolver):
    """Resolve corpus URLs locally; reject all other resources deterministically."""

    def __init__(self, corpus):
        super().__init__()
        self.corpus = corpus.resolve()

    def resolve(self, url, public_id, context):
        if url.startswith(SOURCE):
            path = self.corpus / unquote(url[len(SOURCE):])
        else:
            parsed = urlparse(url)
            if parsed.scheme not in ("", "file") or parsed.netloc:
                raise OSError(f"external resource unavailable offline: {url}")
            path = Path(unquote(parsed.path))
        path = path.resolve()
        if not path.is_relative_to(self.corpus) or not path.is_file():
            raise OSError(f"resource unavailable in corpus: {url}")
        return self.resolve_filename(str(path), context)


def parser(corpus):
    result = etree.XMLParser(no_network=True, resolve_entities=False)
    result.resolvers.add(CorpusResolver(corpus))
    return result


def payload(wire, xml_parser):
    envelope = etree.fromstring(wire, xml_parser)
    for ns in SOAP_NAMESPACES:
        if envelope.tag != f"{{{ns}}}Envelope":
            continue
        body = envelope.find(f"{{{ns}}}Body")
        children = [] if body is None else [node for node in body if isinstance(node.tag, str)]
        if len(children) != 1:
            raise ValueError("expected exactly one document-style SOAP body child")
        # This copies all in-scope declarations, including prefixes used only by QName values.
        return etree.fromstring(etree.tostring(children[0]), xml_parser)
    raise ValueError("not a SOAP 1.1 or SOAP 1.2 envelope")


def validate(schema, wire, xml_parser):
    try:
        schema.assertValid(payload(wire, xml_parser))
        return {"ok": True}
    except (etree.LxmlError, ValueError, OSError) as error:
        return {"ok": False, "desc": str(error)}


def examine(corpus, cases, rows):
    """Record input oracle disagreements separately from proven serialization failures."""
    xml_parser = parser(corpus)
    schema_cache = {}
    inputs = {}
    for case in cases:
        name = case["name"]
        try:
            path = corpus / name / f"echo{name}.xsd"
            schema_cache[name] = etree.XMLSchema(etree.parse(str(path), xml_parser))
        except (etree.LxmlError, OSError) as error:
            schema_cache[name] = str(error)
        for message in case["messages"]:
            schema = schema_cache[name]
            inputs[message["file"]] = (
                {"ok": None, "desc": schema} if isinstance(schema, str)
                else validate(schema, Path(message["path"]).read_bytes(), xml_parser)
            )
    for row in rows:
        if "file" in row:
            row["input_validation"] = inputs[row["file"]]
        if row["stage"] == "serialize" and row["ok"]:
            schema = schema_cache[row["case"]]
            wire = row.pop("body")
            row["output_validation"] = (
                {"ok": None, "desc": schema} if isinstance(schema, str)
                else validate(schema, wire.encode(), xml_parser)
            )
            if row["output_validation"]["ok"] is not True:
                row["body"] = wire
    counts = Counter(f"{r['stage']}_{'ok' if r['ok'] else 'failed'}" for r in rows)
    for row in rows:
        if "output_validation" in row:
            state = row["output_validation"]["ok"]
            counts["output_valid" if state is True else "output_rejected" if state is False
                   else "output_unassessed"] += 1
            if state is False and row["input_validation"]["ok"] is True:
                counts["valid_input_invalid_output"] += 1
    counts.update({"input_valid": sum(v["ok"] is True for v in inputs.values()),
                   "input_rejected": sum(v["ok"] is False for v in inputs.values()),
                   "input_unassessed": sum(v["ok"] is None for v in inputs.values())})
    return {"counts": dict(sorted(counts.items())), "rows": rows, "inputs": inputs}


def check_rows(cases, rows):
    """Require one complete, ordered worker result for every reachable manifest operation."""
    results = iter(rows)

    def take(name, stage, file=None):
        row = next(results, None)
        if (not isinstance(row, dict) or row.get("case") != name or row.get("stage") != stage
                or row.get("file") != file or type(row.get("ok")) is not bool):
            raise RuntimeError(f"incomplete or unexpected Qore result for {name}/{file}: {stage}")
        if row["ok"] and stage == "serialize" and not isinstance(row.get("body"), str):
            raise RuntimeError(f"missing serialized body for {name}/{file}")
        if not row["ok"] and any(not isinstance(row.get(key), str) for key in ("err", "desc")):
            raise RuntimeError(f"missing Qore error details for {name}/{file}: {stage}")
        return row["ok"]

    for case in cases:
        if not take(case["name"], "parse"):
            continue
        for message in case["messages"]:
            if take(case["name"], "deserialize", message["file"]):
                take(case["name"], "serialize", message["file"])
    end = object()
    if next(results, end) is not end:
        raise RuntimeError("unexpected trailing Qore survey results")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("corpus", type=Path, help="extracted databinding/examples/6/09 directory")
    cli.add_argument("--output", type=Path, required=True, help="write the complete JSON report here")
    cli.add_argument("--soap-version", choices=("11", "12", "both"), default="11")
    cli.add_argument("--qore", default="qore")
    args = cli.parse_args()
    corpus = args.corpus.resolve()
    cases = inventory(corpus, args.soap_version)
    # Share one cache across all cases instead of duplicating the entire corpus in every manifest entry.
    cache = {}
    for path in sorted(corpus.rglob("*.xsd")):
        cache[SOURCE + path.relative_to(corpus).as_posix()] = path.read_text()
    with tempfile.TemporaryDirectory(prefix="qore-wsdl-survey-") as temporary:
        manifest = Path(temporary) / "manifest.json"
        manifest.write_text(json.dumps({"cases": cases, "cache": cache}))
        run = subprocess.run([args.qore, "--enable-debug", str(Path(__file__).with_name("probe.qr")),
                              str(manifest)], text=True, capture_output=True, timeout=120, check=True)
    if run.stderr.strip():
        raise RuntimeError(f"Qore emitted diagnostics:\n{run.stderr}")
    rows = [json.loads(line) for line in run.stdout.splitlines()]
    check_rows(cases, rows)
    result = examine(corpus, cases, rows)
    sources = sorted({Path(c["wsdl"]) for c in cases}
                     | {Path(m["path"]) for c in cases for m in c["messages"]}
                     | set(corpus.rglob("*.xsd")))
    result["source_sha256"] = {p.relative_to(corpus).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sources}
    result["versions"] = {"lxml": list(etree.LXML_VERSION), "libxml2": list(etree.LIBXML_VERSION),
                          "qore": subprocess.run([args.qore, "--version"], text=True, capture_output=True,
                                                 timeout=10, check=True).stdout,
                          "wsdl_module_sha256": hashlib.sha256(
                              Path(__file__).resolve().parents[2].joinpath("qlib/WSDL.qm").read_bytes()).hexdigest()}
    result["scope"] = {"wsdls": len(cases), "messages": sum(len(c["messages"]) for c in cases),
                       "soap_version": args.soap_version, "network": False,
                       "checks": "WSDL 1.1 parse; request decode/encode; independent payload XSD validation"}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"scope": result["scope"], "counts": result["counts"]}, indent=2))
    # A diagnostic survey is intentionally not a green conformance test: all failures stay in the report.


if __name__ == "__main__":
    main()
