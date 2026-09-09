"""Pinned Apache Xerces-J validation, independent of the module's libxml2.

Copyright (C) 2026 Qore Technologies, s.r.o.
Requires a JDK (java and javac); all dependencies are pinned offline.
"""

import base64
from dataclasses import dataclass, field
import os
from pathlib import Path
import subprocess
import tempfile

from corpus import check_digest, local_path, read_manifest


ROOT = Path(__file__).resolve().parent / "oracle"


@dataclass
class SchemaJob:
    """A schema at its original URI and explicitly identified standalone XML payloads."""

    name: str
    uri: str
    schema: bytes
    documents: dict[str, bytes] = field(default_factory=dict)


def _field(value: str) -> str:
    if (not isinstance(value, str) or not value or len(value) > 4096
            or any(c in value for c in "\t\r\n\x00")):
        raise ValueError(f"invalid oracle identifier: {value!r}")
    return value


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _decode(value: str) -> str:
    try:
        return base64.b64decode(value, validate=True).decode("utf-8")
    except (ValueError, UnicodeError) as error:
        raise RuntimeError("malformed oracle diagnostic encoding") from error


def check_results(jobs: list[SchemaJob], output: str) -> dict:
    """Reject lost, duplicate, reordered or malformed worker results, including skipped stages."""
    lines = iter(output.splitlines())
    version = next(lines, "").split("\t")
    if len(version) != 3 or version[0] != "version":
        raise RuntimeError("missing oracle implementation version")
    report = {"versions": {"xerces": _decode(version[1]), "java": _decode(version[2])},
              "schemas": {}, "documents": {}}
    if report["versions"]["xerces"] != "Xerces-J 2.12.2" or not report["versions"]["java"]:
        raise RuntimeError("unexpected oracle implementation version")

    def take(stage: str, name: str, schema_ok: bool = True) -> dict:
        row = next(lines, "").split("\t")
        if (len(row) != 5 or row[:2] != [stage, name]
                or row[2] not in ("valid", "invalid", "unreachable")
                or (row[2] == "unreachable") != (not schema_ok)):
            raise RuntimeError(f"incomplete or unexpected oracle result: {stage}/{name}")
        desc = _decode(row[3])
        if (row[2] == "valid") != (desc == ""):
            raise RuntimeError(f"inconsistent oracle diagnostic: {stage}/{name}")
        warnings = [_decode(item) for item in row[4].split(",")] if row[4] else []
        if any(not warning for warning in warnings) or (row[2] == "unreachable" and warnings):
            raise RuntimeError(f"inconsistent oracle warnings: {stage}/{name}")
        return {"ok": True if row[2] == "valid" else False if row[2] == "invalid" else None,
                "status": row[2], "desc": desc, "warnings": warnings}

    for job in jobs:
        schema = report["schemas"][job.name] = take("S", job.name)
        for name in job.documents:
            report["documents"][name] = take("V", name, schema["ok"])
    if next(lines, None) is not None:
        raise RuntimeError("unexpected trailing oracle results")
    return report


def run(jobs: list[SchemaJob], resources: dict[str, bytes] | None = None) -> dict:
    """Compile and run the checksum-pinned oracle within bounded subprocess deadlines.

    All resources are supplied as bytes. Unknown external resources and DTDs are
    rejected; input schemas/documents are never rewritten. Worker stderr is fatal.
    Compilation uses all javac lint checks with warnings treated as errors.
    """
    return _run(jobs, resources, "XsdOracle")


def run_entity_documents(jobs: list[SchemaJob]) -> dict:
    """Validate standalone ENTITY documents through the pinned DOM oracle.

    Internal DTD declarations populate document context. External entities and
    external DTD loading remain disabled; schema documents still prohibit DTDs.
    This entry point does not change the SOAP oracle's DOCTYPE policy.
    """
    return _run(jobs, None, "XsdEntityOracle")


def _run(jobs: list[SchemaJob], resources: dict[str, bytes] | None, worker: str) -> dict:
    if not jobs:
        raise ValueError("no independent oracle jobs")
    resources = resources or {}
    blobs = [*resources.values(), *(job.schema for job in jobs),
             *(data for job in jobs for data in job.documents.values())]
    if (len(blobs) > 10000 or any(not isinstance(data, bytes) for data in blobs)
            or sum(len(data) for data in blobs) > 64 * 1024 * 1024):
        raise ValueError("oracle inputs exceed limits or contain non-byte data")
    manifest = read_manifest(ROOT / "manifest.json")
    artifacts = []
    for item in manifest["artifacts"]:
        path = local_path(ROOT, item["path"])
        data = path.read_bytes()
        check_digest(data, item["sha256"], item["path"])
        if len(data) != item["size"]:
            raise ValueError(f"oracle artifact size mismatch: {item['path']}")
        artifacts.append(str(path))
    lines = [f"R\t{_field(uri)}\t{_encode(data)}" for uri, data in resources.items()]
    names, documents = set(), set()
    for job in jobs:
        if job.name in names:
            raise ValueError(f"duplicate oracle schema: {job.name}")
        names.add(job.name)
        lines.append(f"S\t{_field(job.name)}\t{_field(job.uri)}\t{_encode(job.schema)}")
        for name, data in job.documents.items():
            if name in documents:
                raise ValueError(f"duplicate oracle document: {name}")
            documents.add(name)
            lines.append(f"V\t{job.name}\t{_field(name)}\t{_encode(data)}")
    with tempfile.TemporaryDirectory(prefix="wsdl-xerces-") as temporary:
        path = Path(temporary)
        input_file = path / "manifest.tsv"
        input_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        classpath = os.pathsep.join(artifacts + [temporary])
        compile_result = subprocess.run(["javac", "-Xlint:all", "-Werror", "-cp", classpath,
                                         "-d", temporary, str(ROOT / "XsdOracle.java"),
                                         str(ROOT / "XsdEntityOracle.java")],
                                        capture_output=True, text=True, check=True, timeout=30)
        if compile_result.stdout or compile_result.stderr:
            raise RuntimeError(f"oracle compilation diagnostics: {compile_result.stdout}{compile_result.stderr}")
        # XSD 1.0 length counts Unicode characters, not Java UTF-16 storage units.
        # Xerces exposes the conforming count as a JVM property read during type initialization.
        process = subprocess.run(["java", "-Xmx256m",
                                 "-Dorg.apache.xerces.impl.dv.xs.useCodePointCountForStringLength=true",
                                 "-cp", classpath, worker, str(input_file)],
                                 capture_output=True, text=True, check=True, timeout=60)
        if process.stderr:
            raise RuntimeError(f"oracle worker diagnostics: {process.stderr}")
    return check_results(jobs, process.stdout)
