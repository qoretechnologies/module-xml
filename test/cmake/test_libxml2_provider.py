#!/usr/bin/env python3
"""Integration tests for real libxml2 provider selection and offline builds.

Copyright (C) 2026 Qore Technologies, s.r.o.
Run with python3 test/cmake/test_libxml2_provider.py -v. XML_LIBXML2_SOURCE
may name an unpacked pinned archive for offline execution. Logs and build
artifacts are retained in the printed temporary directory for diagnosis.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]


class LibXml2ProviderTest(unittest.TestCase):
    @classmethod
    def run_command(cls, args, *, success=True):
        result = subprocess.run([str(arg) for arg in args], text=True, capture_output=True, timeout=180)
        with (cls.root / "commands.log").open("a") as log:
            log.write(repr(args) + "\n" + result.stdout + result.stderr + "\n")
        if (result.returncode == 0) != success:
            raise AssertionError(f"Unexpected status {result.returncode}: {args}\n"
                                 + result.stdout + result.stderr)
        return result.stdout + result.stderr

    @classmethod
    def configure(cls, name, *options, success=True):
        return cls.run_command(["cmake", "-S", cls.project, "-B", cls.root / name,
                                "-DCMAKE_BUILD_TYPE=Debug", *options], success=success)

    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="qore-xml-libxml2-test-"))
        print(f"libxml2 provider test artifacts: {cls.root}", flush=True)
        cls.project = cls.root / "project"
        cls.project.mkdir()
        (cls.project / "CMakeLists.txt").write_text(f'''cmake_minimum_required(VERSION 3.18...3.31)
project(libxml2_provider_test C)
set(BUILD_SHARED_LIBS ON CACHE BOOL "Parent option must survive")
include("{REPO}/cmake/QoreXmlLibXml2.cmake")
if(NOT BUILD_SHARED_LIBS)
    message(FATAL_ERROR "Dependency changed parent BUILD_SHARED_LIBS")
endif()
add_executable(probe "{REPO}/cmake/libxml2-namespace-probe.c")
target_link_libraries(probe PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
add_executable(catalog-cleanup "{REPO}/test/cmake/libxml2_catalog_cleanup.c")
target_link_libraries(catalog-cleanup PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
install(TARGETS probe RUNTIME DESTINATION bin)
''')
        source = os.environ.get("XML_LIBXML2_SOURCE")
        if not source:
            local = REPO / "build-debug/_deps/qore_xml_libxml2-src"
            if local.is_dir():
                source = str(local)
        source_option = ([f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={source}"] if source else [])
        cls.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED", *source_option)
        cls.run_command(["cmake", "--build", cls.root / "bundled", "--target", "probe", "-j4"])
        cls.source = Path(source) if source else cls.root / "bundled/_deps/qore_xml_libxml2-src"
        # Build a real fixed shared dependency to exercise the SYSTEM branch.
        fixed_project = cls.root / "fixed/source"
        fixed_project.mkdir(parents=True)
        (fixed_project / "CMakeLists.txt").write_text(f'''cmake_minimum_required(VERSION 3.18...3.31)
project(libxml2_backport_fixture C)
add_subdirectory("{cls.source}" libxml)
include("{REPO}/cmake/QoreXmlLibXml2QNameFix.cmake")
qore_xml_fix_libxml2_qnames("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
''')
        cls.fixed = cls.root / "fixed/build-debug"
        cls.run_command(["cmake", "-S", fixed_project, "-B", cls.fixed, "-DCMAKE_BUILD_TYPE=Debug",
                         "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                         "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        cls.run_command(["cmake", "--build", cls.fixed, "--target", "LibXml2", "-j4"])
        cls.fixed_include = cls.root / "fixed/include"
        cls.fixed_include.mkdir(parents=True)
        # A merged include tree matches a normal installation. Give the fixture an
        # older version string to model a distribution backport: selection must
        # follow the run result, not the advertised release number.
        import shutil
        shutil.copytree(cls.source / "include/libxml", cls.fixed_include / "libxml")
        header = (cls.fixed / "libxml/libxml/xmlversion.h").read_text()
        (cls.fixed_include / "libxml/xmlversion.h").write_text(
            header.replace('#define LIBXML_DOTTED_VERSION "2.15.4"',
                           '#define LIBXML_DOTTED_VERSION "2.12.10"'))
        libraries = list((cls.fixed / "libxml").glob("libxml2.so")) + list((cls.fixed / "libxml").glob("libxml2.dylib"))
        if len(libraries) != 1:
            raise AssertionError(f"Expected one fixed shared library: {libraries}")
        cls.fixed_options = [f"-DLIBXML2_LIBRARY={libraries[0]}",
                             f"-DLIBXML2_INCLUDE_DIR={cls.fixed_include}"]

    def test_bundled_behavior_and_install(self):
        output = self.run_command([self.root / "bundled/probe"])
        self.assertIn("namespace_identity=PASS", output)
        self.assertIn("runtime=21504", output)
        stage = self.root / "stage"
        self.run_command(["cmake", "--install", self.root / "bundled", "--prefix", stage])
        self.assertEqual(["bin/probe", "share/licenses/qore-xml/libxml2-NOTICES.txt"],
                         sorted(str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file()))
        notice = (stage / "share/licenses/qore-xml/libxml2-NOTICES.txt").read_text()
        self.assertIn((self.source / "Copyright").read_text(), notice)
        for name in ("dict.c", "list.c"):
            body = (self.source / name).read_text()
            self.assertIn(body[:body.index("*/") + 2], notice)

    def test_catalog_error_cleanup(self):
        import hashlib
        original = (self.source / "parserInternals.c").read_bytes()
        self.assertEqual("62b005e11c8d9af96ee49bb4e9e5cc3f02dd3378d7d4cfb775a253dce43fe56b",
                         hashlib.sha256(original).hexdigest())
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "catalog-cleanup", "-j4"])
        self.assertIn("catalog cleanup: PASS", self.run_command([self.root / "bundled/catalog-cleanup"]))
        self.assertEqual(original, (self.source / "parserInternals.c").read_bytes())

    def qname_source_override(self, name, filename, *, fixed):
        override = self.root / name
        override.mkdir()
        for entry in self.source.iterdir():
            if entry.name != filename:
                (override / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        source = ((self.root / "bundled/_deps/qore_xml_libxml2-build/qore-qname-fix" / filename).read_bytes()
                  if fixed else (self.source / filename).read_bytes() + b"\n/* Unexpected source modification. */\n")
        (override / filename).write_bytes(source)
        return override

    def test_qname_fixes_preserve_sources_and_reconfigure(self):
        import hashlib
        hashes = {"xmlschemas.c": "bed8bfbfd61a2025b67b7a0e4d05ce50093e7a6bb5e43a3ebac343b8df4329a7",
                  "xmlschemastypes.c": "08cac7d1dbdb617688ac5b36ab6fee75f634e5bf0372aa0e6569a0bebe3b0c8f"}
        replacements = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-qname-fix"
        times = {name: (replacements / name).stat().st_mtime_ns for name in hashes}
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        for name, expected in hashes.items():
            self.assertEqual(expected, hashlib.sha256((self.source / name).read_bytes()).hexdigest())
            self.assertEqual(times[name], (replacements / name).stat().st_mtime_ns)
        self.assertIn("qname_values=PASS", self.run_command([self.root / "bundled/probe"]))

    def test_unexpected_qname_sources_are_rejected(self):
        for filename in ("xmlschemas.c", "xmlschemastypes.c"):
            with self.subTest(filename=filename):
                name = "changed-" + filename
                override = self.qname_source_override(name, filename, fixed=False)
                output = self.configure(name + "-build", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                                        f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={override}", success=False)
                self.assertIn(f"Unexpected libxml2 {filename}; cannot apply the QName identity fix",
                              " ".join(output.split()))

    def test_unfixed_current_release_uses_qname_fallback(self):
        raw = self.root / "unfixed/build-debug"
        self.run_command(["cmake", "-S", self.source, "-B", raw, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", raw, "--target", "LibXml2", "-j4"])
        import shutil
        includes = self.root / "unfixed/include"
        shutil.copytree(self.source / "include/libxml", includes / "libxml")
        shutil.copyfile(raw / "libxml/xmlversion.h", includes / "libxml/xmlversion.h")
        libraries = list(raw.glob("libxml2.so")) + list(raw.glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={includes}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("unfixed-system", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("2.15.4 failed namespace identity probe", output)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe_log = (self.root / "unfixed-system/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("qname_values=FAIL", probe_log)
        self.run_command(["cmake", "--build", self.root / "unfixed-system", "--target", "probe", "-j4"])
        self.assertIn("qname_values=PASS", self.run_command([self.root / "unfixed-system/probe"]))
        self.configure("unfixed-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)

    def test_already_fixed_qname_sources_are_accepted(self):
        for filename in ("xmlschemas.c", "xmlschemastypes.c"):
            with self.subTest(filename=filename):
                name = "fixed-" + filename
                override = self.qname_source_override(name, filename, fixed=True)
                output = self.configure(name + "-build", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                                        f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={override}")
                self.assertNotIn(f"applied libxml2 QName identity fix to {filename}", output)
                self.run_command(["cmake", "--build", self.root / (name + "-build"), "--target", "probe", "-j4"])
                self.assertIn("qname_values=PASS", self.run_command([self.root / (name + "-build") / "probe"]))

    def catalog_source_override(self, name, *, fixed):
        override = self.root / name
        override.mkdir()
        for entry in self.source.iterdir():
            if entry.name != "parserInternals.c":
                (override / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        source = (self.source / "parserInternals.c").read_text()
        if fixed:
            source = source.replace("\n    *lastError = oldError;\n\n    return(code);\n",
                                    "\n    xmlResetError(lastError);\n    *lastError = oldError;\n\n    return(code);\n")
        else:
            source += "\n/* Unexpected dependency modification. */\n"
        (override / "parserInternals.c").write_text(source)
        return override

    def test_unexpected_catalog_source_is_rejected(self):
        override = self.catalog_source_override("changed-parser", fixed=False)
        output = self.configure("changed-parser-build", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                                f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={override}", success=False)
        self.assertIn("cannot apply the catalog error ownership fix", " ".join(output.split()))

    def test_already_fixed_catalog_source_is_accepted(self):
        override = self.catalog_source_override("fixed-parser", fixed=True)
        output = self.configure("fixed-parser-build", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                                f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={override}")
        self.assertNotIn("applied libxml2 catalog error ownership fix", output)
        self.run_command(["cmake", "--build", self.root / "fixed-parser-build", "--target", "catalog-cleanup", "-j4"])
        self.assertIn("catalog cleanup: PASS", self.run_command([self.root / "fixed-parser-build/catalog-cleanup"]))

    def test_fixed_backport_stays_system(self):
        output = self.configure("fixed-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *self.fixed_options)
        self.assertIn("2.12.10 passes namespace identity probe", output)
        self.assertNotIn("FetchContent)", output)
        self.run_command(["cmake", "--build", self.root / "fixed-system", "--target", "probe", "-j4"])
        self.assertIn("namespace_identity=PASS", self.run_command([self.root / "fixed-system/probe"]))

    def test_missing_system_uses_offline_fallback(self):
        output = self.configure("missing", "-DCMAKE_DISABLE_FIND_PACKAGE_LibXml2=TRUE",
                                f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}",
                                "-DFETCHCONTENT_FULLY_DISCONNECTED=ON")
        self.assertIn("using private static libxml2 2.15.4", output)

    def test_missing_system_is_rejected_when_required(self):
        output = self.configure("missing-required", "-DCMAKE_DISABLE_FIND_PACKAGE_LibXml2=TRUE",
                                "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", success=False)
        self.assertIn("System libxml2 is missing, unusable, or failed", output)

    def test_switch_providers_in_existing_build(self):
        offline = f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"
        output = self.configure("switch", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *self.fixed_options)
        self.assertIn("passes namespace identity probe", output)
        output = self.configure("switch", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED", offline)
        self.assertIn("using private static libxml2 2.15.4", output)
        output = self.configure("switch", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *self.fixed_options)
        self.assertIn("passes namespace identity probe", output)
        self.assertNotIn("FetchContent)", output)

    def test_cross_build_requires_verification_or_fallback(self):
        output = self.configure("cross", "-DCMAKE_SYSTEM_NAME=Linux", "-DCMAKE_CROSSCOMPILING_EMULATOR=",
                                f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertIn("without a cross-compiling emulator", output)
        self.assertIn("using private static libxml2 2.15.4", output)
        output = self.configure("cross", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", success=False)
        self.assertIn("Cross builds need CMAKE_CROSSCOMPILING_EMULATOR", " ".join(output.split()))

    def test_installed_library_behavior_controls_selection(self):
        output = self.configure("installed", f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        if "passes namespace identity probe" in output:
            self.assertNotIn("FetchContent)", output)
        else:
            self.assertIn("using private static libxml2 2.15.4", output)
            output = self.configure("installed", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", success=False)
            self.assertIn("System libxml2 is missing, unusable, or failed", " ".join(output.split()))

    def test_invalid_provider_is_rejected(self):
        output = self.configure("invalid", "-DQORE_XML_LIBXML2_PROVIDER=system", success=False)
        self.assertIn("must be AUTO, SYSTEM, or BUNDLED", output)

    def test_wrong_offline_source_version_is_rejected(self):
        override = self.root / "wrong-source"
        override.mkdir()
        for entry in self.source.iterdir():
            if entry.name != "VERSION":
                (override / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        (override / "VERSION").write_text("2.15.3\n")
        output = self.configure("wrong-source-build", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                                f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={override}", success=False)
        self.assertIn("source override must provide pinned version 2.15.4", " ".join(output.split()))

    def test_cross_build_with_emulator_verifies_system(self):
        output = self.configure("cross-emulated", "-DCMAKE_SYSTEM_NAME=Linux",
                                "-DCMAKE_CROSSCOMPILING_EMULATOR=/usr/bin/env",
                                "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *self.fixed_options)
        self.assertIn("passes namespace identity probe", output)


if __name__ == "__main__":
    unittest.main()
