#!/usr/bin/env python3
"""Verify and extract the pinned W3C corpus, and load offline schema catalogs.

Copyright (C) 2026 Qore Technologies, s.r.o.
This module never downloads resources or modifies upstream documents.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlparse
import zipfile


ROOT = Path(__file__).resolve().parent / "corpus"
INVENTORY = ROOT / "inventory.json"
CATALOG = ROOT / "catalog.json"
EXAMPLES = Path("databinding/examples/6/09")
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 128 * 1024 * 1024
MAX_FILES = 10000


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_manifest(path: Path) -> dict[str, Any]:
    """Read a versioned JSON object, rejecting duplicate keys and unknown versions."""
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or type(value.get("format")) is not int or value["format"] != 1:
        raise ValueError(f"invalid manifest format: {path}")
    return value


def relative_path(name: str) -> PurePosixPath:
    """Require a normalized relative file name without traversal or platform aliases."""
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name or "\x00" in name
            or any(part in ("", ".", "..") for part in name.split("/"))):
        raise ValueError(f"invalid relative resource path: {name!r}")
    return PurePosixPath(name)


def local_path(root: Path, name: str) -> Path:
    path = (root / relative_path(name)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"resource escapes root: {name}")
    return path


def check_digest(data: bytes, digest: str, name: str) -> None:
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError(f"invalid SHA-256: {name}")
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"SHA-256 mismatch: {name}")


def load_inventory(path: Path = INVENTORY) -> dict[str, Any]:
    """Validate the archive inventory before opening or writing any member files."""
    manifest = read_manifest(path)
    archive, files = manifest.get("archive"), manifest.get("files")
    if not isinstance(archive, dict) or not isinstance(files, dict) or not 0 < len(files) <= MAX_FILES:
        raise ValueError("invalid archive inventory")
    relative_path(archive.get("path"))
    for name, item in [(archive["path"], archive), *files.items()]:
        relative_path(name)
        if (not isinstance(item, dict) or type(item.get("size")) is not int or item["size"] < 0
                or not isinstance(item.get("sha256"), str)
                or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None):
            raise ValueError(f"invalid inventory entry: {name}")
    if archive["size"] > MAX_ARCHIVE_BYTES or sum(i["size"] for i in files.values()) > MAX_EXPANDED_BYTES:
        raise ValueError("archive exceeds corpus resource limits")
    return manifest


def verify_archive(path: Path = INVENTORY) -> dict[str, Any]:
    """Check archive bytes, member set, paths, types, sizes, CRCs and SHA-256 hashes."""
    manifest = load_inventory(path)
    archive = local_path(path.parent, manifest["archive"]["path"])
    if archive.stat().st_size != manifest["archive"]["size"]:
        raise ValueError("archive size mismatch")
    check_digest(archive.read_bytes(), manifest["archive"]["sha256"], archive.name)
    with zipfile.ZipFile(archive) as stream:
        seen = set()
        for member in stream.infolist():
            relative_path(member.filename.rstrip("/") if member.is_dir() else member.filename)
            if member.filename in seen:
                raise ValueError(f"duplicate archive member: {member.filename}")
            seen.add(member.filename)
            mode = stat.S_IFMT(member.external_attr >> 16)
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR) or member.flag_bits & 1:
                raise ValueError(f"unsupported archive member: {member.filename}")
            if member.is_dir():
                continue
            expected = manifest["files"].get(member.filename)
            if expected is None or member.file_size != expected["size"]:
                raise ValueError(f"unexpected archive member or size: {member.filename}")
            check_digest(stream.read(member), expected["sha256"], member.filename)
        if set(manifest["files"]) != {m.filename for m in stream.infolist() if not m.is_dir()}:
            raise ValueError("missing archive members")
    return manifest


def verify_extraction(directory: Path, path: Path = INVENTORY) -> dict[str, Any]:
    """Account for every original file, including non-SOAP and WSDL 2.0 source artifacts."""
    manifest = load_inventory(path)
    for name, expected in manifest["files"].items():
        source = local_path(directory, name)
        if not source.is_file() or source.stat().st_size != expected["size"]:
            raise ValueError(f"missing corpus file or size mismatch: {name}")
        check_digest(source.read_bytes(), expected["sha256"], name)
    return manifest


def extract(directory: Path, path: Path = INVENTORY) -> Path:
    """Extract verified bytes to a new directory; leave it absent if extraction fails.

    The caller owns the destination and must not create it concurrently. Existing
    destinations are refused, including empty directories and symbolic links.
    """
    if directory.exists() or directory.is_symlink():
        raise FileExistsError(f"extraction destination already exists: {directory}")
    manifest = verify_archive(path)
    with tempfile.TemporaryDirectory(prefix=".wsdl-corpus-", dir=directory.parent) as temporary:
        staged = Path(temporary) / "corpus"
        staged.mkdir()
        with zipfile.ZipFile(local_path(path.parent, manifest["archive"]["path"])) as stream:
            for name in manifest["files"]:
                target = local_path(staged, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(stream.read(name))
        verify_extraction(staged, path)
        if directory.exists() or directory.is_symlink():
            raise FileExistsError(f"extraction destination already exists: {directory}")
        staged.rename(directory)
    return directory / EXAMPLES


class Catalog:
    """Immutable, checksum-verified URI-to-bytes catalog shared by all validators.

    Empty or malformed upstream XML is preserved, so parsers can report the actual
    source defect. Catalog lookup must never manufacture a replacement schema.
    """

    def __init__(self, path: Path = CATALOG):
        manifest = read_manifest(path)
        resources = manifest.get("resources")
        if not isinstance(resources, list) or len(resources) > MAX_FILES:
            raise ValueError("catalog resources must be a bounded list")
        data, digests = {}, {}
        total_size = 0
        for item in resources:
            if not isinstance(item, dict) or not isinstance(item.get("uri"), str):
                raise ValueError("invalid catalog entry")
            uri = item["uri"]
            parsed = urlparse(uri)
            if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.fragment:
                raise ValueError(f"invalid catalog URI: {uri}")
            if uri in data:
                raise ValueError(f"duplicate catalog URI: {uri}")
            resource = local_path(path.parent, item.get("path"))
            size = resource.stat().st_size
            total_size += size
            if size > MAX_ARCHIVE_BYTES or total_size > MAX_EXPANDED_BYTES:
                raise ValueError(f"catalog resource exceeds size limit: {uri}")
            content = resource.read_bytes()
            check_digest(content, item.get("sha256"), uri)
            data[uri] = content
            digests[uri] = item["sha256"]
        self.resources: Mapping[str, bytes] = MappingProxyType(data)
        self.sha256: Mapping[str, str] = MappingProxyType(digests)

    def qore_cache(self) -> dict[str, str]:
        """Return UTF-8 schema bytes as Qore's async import cache values."""
        return {uri: content.decode("utf-8") for uri, content in self.resources.items()}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    action = cli.add_mutually_exclusive_group(required=True)
    action.add_argument("--extract", type=Path, help="extract into a new directory")
    action.add_argument("--verify", type=Path, help="verify an existing archive extraction")
    args = cli.parse_args()
    if args.extract:
        print(extract(args.extract))
    else:
        verify_archive()
        manifest = verify_extraction(args.verify)
        print(f"Verified all {len(manifest['files'])} original archive files")


if __name__ == "__main__":
    main()
