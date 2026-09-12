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


class SourceDistributionTest(unittest.TestCase):
    def test_native_dependency_inputs_are_distributed(self):
        makefile = (REPO / "Makefile.am").read_text().replace("\\\n", " ")
        declarations = [line.partition("=")[2] for line in makefile.splitlines()
                        if line.startswith("EXTRA_DIST =")]
        self.assertEqual(1, len(declarations))
        distributed = set(declarations[0].split())
        inputs = {str(path.relative_to(REPO)) for path in (REPO / "cmake").rglob("*")
                  if path.is_file() and path.suffix in (".cmake", ".c", ".h", ".inc", ".txt")}
        self.assertTrue(inputs)
        self.assertEqual(set(), inputs - distributed, "CMake dependency input missing from source archive")


class LibXml2ProviderTest(unittest.TestCase):
    @classmethod
    def run_command(cls, args, *, success=True, input=None):
        result = subprocess.run([str(arg) for arg in args], text=True, capture_output=True, timeout=180, input=input)
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
add_executable(entity-allocation "{REPO}/test/cmake/libxml2_entity_allocation.c")
target_link_libraries(entity-allocation PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
add_executable(particle-allocation "{REPO}/test/cmake/libxml2_particle_identity_allocation.c")
target_link_libraries(particle-allocation PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
add_executable(counter-values "{REPO}/test/cmake/libxml2_particle_counter_values.c")
target_link_libraries(counter-values PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
add_executable(particle-execution-allocation "{REPO}/test/cmake/libxml2_particle_execution_allocation.c")
target_link_libraries(particle-execution-allocation PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
foreach(part attribution-allocation attribution-math attribution-summary)
    string(REPLACE "attribution-" "" suffix "${{part}}")
    add_executable(${{part}} "{REPO}/test/cmake/libxml2_particle_attribution_${{suffix}}.c")
    target_link_libraries(${{part}} PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
endforeach()
if(TARGET LibXml2)
    get_target_property(native_sources LibXml2 SOURCES)
    foreach(native_source IN LISTS native_sources)
        get_filename_component(native_name "${{native_source}}" NAME)
        if(native_name STREQUAL "xmlschemas.c")
            set(schema_source "${{native_source}}")
        elseif(native_name STREQUAL "xmlregexp.c")
            set(regexp_source "${{native_source}}")
        endif()
    endforeach()
    get_target_property(native_includes LibXml2 INCLUDE_DIRECTORIES)
    get_target_property(native_options LibXml2 COMPILE_OPTIONS)
    foreach(part attribution-schema-allocation counter-schema-allocation counter-execution edc-schema-allocation wildcard-id-allocation wildcard-type-allocation)
        string(REPLACE "-" "_" suffix "${{part}}")
        if(part STREQUAL "wildcard-id-allocation")
            add_executable(${{part}} "{REPO}/test/cmake/libxml2_wildcard_id_allocation.c")
        elseif(part STREQUAL "wildcard-type-allocation")
            add_executable(${{part}} "{REPO}/test/cmake/libxml2_wildcard_type_allocation.c")
        else()
            add_executable(${{part}} "{REPO}/test/cmake/libxml2_particle_${{suffix}}.c")
        endif()
        target_compile_definitions(${{part}} PRIVATE QORE_XML_SCHEMA_SOURCE="${{schema_source}}"
                                                   QORE_REGEXP_SOURCE="${{regexp_source}}")
        target_include_directories(${{part}} PRIVATE ${{native_includes}})
        if(native_options)
            target_compile_options(${{part}} PRIVATE ${{native_options}})
        endif()
        target_link_libraries(${{part}} PRIVATE ${{QORE_XML_LIBXML2_TARGET}})
    endforeach()
endif()
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
include("{REPO}/cmake/QoreXmlLibXml2UriFix.cmake")
qore_xml_fix_libxml2_uris("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2EntityFix.cmake")
qore_xml_fix_libxml2_entities("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2OccursFix.cmake")
qore_xml_fix_libxml2_occurs("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2ParticleIdentityFix.cmake")
qore_xml_fix_libxml2_particle_identity("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2ParticleAttributionFix.cmake")
qore_xml_fix_libxml2_particle_attribution("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2ParticleCounterFix.cmake")
qore_xml_fix_libxml2_particle_counters("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2ParticleRangeFix.cmake")
qore_xml_fix_libxml2_particle_ranges("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2TypeFinalFix.cmake")
qore_xml_fix_libxml2_type_finals("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2ElementSubstitutionFix.cmake")
qore_xml_fix_libxml2_element_substitution("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2ElementConsistencyFix.cmake")
qore_xml_fix_libxml2_element_consistency("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2WildcardIdFix.cmake")
qore_xml_fix_libxml2_wildcard_ids("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2WildcardTypeFix.cmake")
qore_xml_fix_libxml2_wildcard_types("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2SchemaWhitespaceFix.cmake")
qore_xml_fix_libxml2_schema_whitespace("{cls.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
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
        self.assertIn("qname_unions=PASS", output)
        self.assertIn("uri_identity=PASS", output)
        self.assertIn("entity_values=PASS", output)
        self.assertIn("occurs_values=PASS", output)
        self.assertIn("particle_identity=PASS", output)
        self.assertIn("particle_attribution=PASS", output)
        self.assertIn("particle_ranges=PASS", output)
        self.assertIn("element_substitution=PASS", output)
        self.assertIn("element_consistency=PASS", output)
        self.assertIn("wildcard_ids=PASS", output)
        self.assertIn("wildcard_types=PASS", output)
        self.assertIn("schema_whitespace=PASS", output)
        stage = self.root / "stage"
        self.run_command(["cmake", "--install", self.root / "bundled", "--prefix", stage])
        self.assertEqual(["bin/probe", "share/licenses/qore-xml/libxml2-NOTICES.txt"],
                         sorted(str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file()))
        notice = (stage / "share/licenses/qore-xml/libxml2-NOTICES.txt").read_text()
        self.assertIn((self.source / "Copyright").read_text(), notice)
        for name in ("dict.c", "list.c"):
            body = (self.source / name).read_text()
            self.assertIn(body[:body.index("*/") + 2], notice)

    def test_qname_fixed_library_with_broken_uris_uses_fallback(self):
        project = self.root / "uri-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(f'''cmake_minimum_required(VERSION 3.18...3.31)
project(uri_broken_fixture C)
add_subdirectory("{self.source}" libxml)
include("{REPO}/cmake/QoreXmlLibXml2QNameFix.cmake")
qore_xml_fix_libxml2_qnames("{self.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
''')
        build = self.root / "uri-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        self.configure("uri-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        probe = (self.root / "uri-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("qname_values=PASS", probe)
        self.assertIn("qname_unions=PASS", probe)
        self.assertIn("uri_identity=FAIL", probe)
        self.configure("uri-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)

    def test_unexpected_uri_sources_are_rejected(self):
        import shutil
        for filename in ("uri.c", "tree.c"):
            with self.subTest(filename=filename):
                source = self.root / ("changed-uri-source-" + filename)
                shutil.copytree(self.source, source)
                path = source / filename
                path.write_bytes(path.read_bytes() + b"\n/* Unrecognized URI source modification. */\n")
                output = self.configure("changed-uri-" + filename, "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                                        f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={source}", success=False)
                self.assertIn(f"Unexpected libxml2 {filename}; cannot apply URI fixes", output)

    def test_qname_uri_backport_without_entity_fix_is_rejected(self):
        project = self.root / "entity-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(f'''cmake_minimum_required(VERSION 3.18...3.31)
project(entity_broken_fixture C)
add_subdirectory("{self.source}" libxml)
include("{REPO}/cmake/QoreXmlLibXml2QNameFix.cmake")
qore_xml_fix_libxml2_qnames("{self.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
include("{REPO}/cmake/QoreXmlLibXml2UriFix.cmake")
qore_xml_fix_libxml2_uris("{self.source}" "${{CMAKE_CURRENT_BINARY_DIR}}/libxml")
''')
        build = self.root / "entity-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("entity-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "entity-broken-auto/system-libxml2/namespace-probe.log").read_text()
        for label in ("qname_values", "qname_unions", "uri_identity"):
            self.assertIn(label + "=PASS", probe)
        self.assertIn("entity_values=FAIL", probe)
        self.configure("entity-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)

    def test_count_backport_detection_and_reconfigure(self):
        project = self.root / "occurs-broken/source"
        project.mkdir(parents=True)
        fixed = self.previous_fix_fixture()
        for module, function in (("ParticleAttribution", "particle_attribution"), ("ParticleCounter", "particle_counters"),
                                 ("ParticleRange", "particle_ranges")):
            fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2{module}Fix.cmake")\n', "")
            fixed = fixed.replace(f'qore_xml_fix_libxml2_{function}("{self.source}" '
                                  '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2ParticleIdentityFix.cmake")\n', "")
        fixed = fixed.replace(f'qore_xml_fix_libxml2_particle_identity("{self.source}" '
                              '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2OccursFix.cmake")\n', "")
        fixed = fixed.replace(f'qore_xml_fix_libxml2_occurs("{self.source}" '
                              '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        (project / "CMakeLists.txt").write_text(fixed)
        build = self.root / "occurs-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("occurs-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "occurs-broken-auto/system-libxml2/namespace-probe.log").read_text()
        for label in ("qname_values", "qname_unions", "uri_identity", "entity_values"):
            self.assertIn(label + "=PASS", probe)
        self.assertIn("occurs_values=FAIL", probe)
        self.configure("occurs-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        replacement = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-occurs-fix/xmlschemas.c"
        stamp = replacement.stat().st_mtime_ns
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertEqual(stamp, replacement.stat().st_mtime_ns)

    def test_particle_identity_backport_and_cleanup(self):
        import hashlib
        project = self.root / "particle-broken/source"
        project.mkdir(parents=True)
        fixed = self.previous_fix_fixture()
        for module, function in (("ParticleAttribution", "particle_attribution"), ("ParticleCounter", "particle_counters"),
                                 ("ParticleRange", "particle_ranges")):
            fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2{module}Fix.cmake")\n', "")
            fixed = fixed.replace(f'qore_xml_fix_libxml2_{function}("{self.source}" '
                                  '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2ParticleIdentityFix.cmake")\n', "")
        fixed = fixed.replace(f'qore_xml_fix_libxml2_particle_identity("{self.source}" '
                              '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        (project / "CMakeLists.txt").write_text(fixed)
        build = self.root / "particle-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("particle-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "particle-broken-auto/system-libxml2/namespace-probe.log").read_text()
        for label in ("qname_values", "qname_unions", "uri_identity", "entity_values", "occurs_values"):
            self.assertIn(label + "=PASS", probe)
        self.assertIn("particle_identity=FAIL", probe)
        self.configure("particle-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        replacements = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-particle-identity-fix"
        stamps = {name: (replacements / name).stat().st_mtime_ns for name in ("xmlschemas.c", "xmlregexp.c")}
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        for name, stamp in stamps.items():
            self.assertEqual(stamp, (replacements / name).stat().st_mtime_ns)
        self.assertEqual("3b2ba46567d52d898864b9c3b7478066c25720cbb9ad69f5961f6b329cd64aaf",
                         hashlib.sha256((self.source / "xmlregexp.c").read_bytes()).hexdigest())
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "particle-allocation", "-j4"])
        self.assertIn("Particle identity allocation cleanup: PASS",
                      self.run_command([self.root / "bundled/particle-allocation"]))

    def test_particle_exact_arithmetic_and_cleanup(self):
        from fractions import Fraction
        import itertools
        import random
        targets = ("attribution-math", "attribution-summary", "attribution-allocation",
                   "attribution-schema-allocation", "particle-execution-allocation")
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", *targets, "-j4"])
        executable = self.root / "bundled/attribution-math"
        rng = random.Random(4105)
        boundaries = (0, 1, 2, 999999999, 1000000000, 1000000001, 10**80 - 1, 10**80)
        pairs = list(itertools.product(boundaries, repeat=2))
        pairs += [(rng.randrange(10**rng.randint(1, 349)), rng.randrange(10**rng.randint(1, 349)))
                  for _ in range(300)]
        checks = 0
        for left, right in pairs:
            self.assertEqual(str(left * right), self.run_command([executable, "multiply", left, right]).strip())
            self.assertEqual(str((left > right) - (left < right)),
                             self.run_command([executable, "compare", left, right]).strip())
            self.assertEqual(str(abs(left - right)),
                             self.run_command([executable, "subtract", max(left, right), min(left, right)]).strip())
            checks += 3
        for _ in range(300):
            args = [rng.randrange(1, 10**rng.randint(1, 200)) for _ in range(4)]
            left, right = Fraction(*args[:2]), Fraction(*args[2:])
            self.assertEqual(str((left > right) - (left < right)),
                             self.run_command([executable, "ratio", *args]).strip())
            checks += 1
        for args in (("subtract", "1", "2"), ("multiply", "x", "2"), ("multiply", "", "1"),
                     ("ratio", "1", "0", "2", "1"), ("unknown", "1", "1"),
                     ("ratio", "1", "2"), ("multiply", "1", "2", "3", "4")):
            self.assertEqual("", self.run_command([executable, *args], success=False))
            checks += 1
        self.assertEqual(1399, checks)
        for executable, label in (("attribution-allocation", "Native UPA arithmetic/sets: PASS"),
                                  ("attribution-schema-allocation", "Native particle attribution cleanup: PASS"),
                                  ("particle-execution-allocation", "Native particle execution cleanup: PASS")):
            self.assertIn(label, self.run_command([self.root / "bundled" / executable]))

    def test_particle_counter_value_boundaries(self):
        import random
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "counter-values", "-j4"])
        executable = self.root / "bundled/counter-values"
        rng = random.Random(4106)
        values = (0, 1, 2, 3, 999999998, 999999999, 1000000000, 1000000001,
                  1073741823, 1073741824, 1073741825, 2147483646, 2147483647, 2147483648,
                  2**64 - 1, 2**64, 10**80 - 1, 10**80)
        cases = []
        for low in values:
            for high in (low, low + 1, None):
                for emitted in (0, 1):
                    if high == 0 and emitted:
                        continue  # An absent particle never emits a first occurrence.
                    for nullable in (0, 1):
                        minimum = max(0, (0 if nullable else low) - emitted)
                        maximum = None if high is None else high - emitted
                        for current in sorted({0, max(0, minimum - 1), minimum,
                                               maximum if maximum is not None else minimum + 10}):
                            if maximum is None or current <= maximum:
                                cases.append((low, high, emitted, nullable, current, 3))
        for _ in range(300):
            low = rng.randrange(10**rng.randint(1, 180))
            high = low + rng.randrange(100)
            current = rng.choice((0, max(0, low - 2), low, high))
            cases.append((low, high, 0, 0, current, rng.randrange(6)))
        self.assertEqual(881, len(cases))
        for low, high, emitted, nullable, current, steps in cases:
            minimum = max(0, (0 if nullable else low) - emitted)
            maximum = None if high is None else high - emitted
            advanced = steps if maximum is None else min(steps, maximum - current)
            result = min(current + advanced, minimum) if maximum is None else current + advanced
            expected = [minimum, "u" if maximum is None else maximum, result, advanced,
                        int(maximum is None or result < maximum),
                        int(result >= minimum and (maximum is None or result <= maximum)),
                        minimum if minimum <= 2147483647 else "wide",
                        maximum if maximum is not None and maximum <= 2147483647 else "wide"]
            args = [low, "unbounded" if high is None else high, emitted, nullable, current, steps]
            self.assertEqual(" ".join(map(str, expected)), self.run_command([executable, *args]).strip())
        for low, high in (("  +0002\t", " +0003\n"), ("-000", " unbounded\r\n")):
            canonical = [int(low), "unbounded" if "unbounded" in high else int(high)]
            self.assertEqual(self.run_command([executable, *canonical, 0, 0, 0, 3]),
                             self.run_command([executable, low, high, 0, 0, 0, 3]))
        for invalid in ("", " ", "+", "-", "-1", "1.0", "1e2", "1x", "1 2", "++1", "NaN"):
            for position in (0, 1, 4):
                args = ["0", "3", "0", "0", "0", "3"]
                args[position] = invalid
                self.assertEqual("", self.run_command([executable, *args], success=False))
        for args in (("4", "3", 0, 0, 0, 1), ("4", "3", 0, 1, 0, 1),
                     ("0", "0", 1, 0, 0, 1), ("0", "3", 0, 0, 4, 1),
                     ("unbounded", "unbounded", 0, 0, 0, 1)):
            self.assertEqual("", self.run_command([executable, *args], success=False))

    def test_particle_counter_execution_and_cleanup(self):
        targets = ("counter-execution", "counter-schema-allocation")
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", *targets, "-j4"])
        for executable, label in (("counter-execution", "Exact native counter execution and rollback: PASS"),
                                  ("counter-schema-allocation", "Exact native schema counter cleanup: PASS")):
            self.assertIn(label, self.run_command([self.root / "bundled" / executable]))

    def test_particle_summary_boundaries_and_present_components(self):
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "attribution-summary", "-j4"])
        a, b = ("a",), ("b",)
        def repeat(child, low, high):
            return ("r", child, str(low), str(high))
        def nested(outer, low=2, high=3):
            return ("s", repeat(("s", repeat(b, 0, 1), repeat(a, low, high)), outer, outer), b)
        low, high = 10**80 - 1, 10**80
        fixtures = [(("c", a, a), 0), (repeat(("c", a, a), 0, 0), 1),
                    (("s", ("e",), ("c", a, a)), 0), (("s", repeat(a, 2, 2), a), 1),
                    (("s", repeat(a, 2, 3), a), 0), (nested(2), 1), (nested(3), 0),
                    (nested(low, low, high), 1), (nested(high, low, high), 0),
                    (("s", repeat(a, 0, "u"), b), 1), (("s", repeat(a, 0, "u"), a), 0)]
        def encode(expression, rows):
            kind = expression[0]
            if kind in ("a", "b", "e", "0"):
                row = (kind, 0, 0, 1, 1)
            elif kind == "r":
                row = (kind, encode(expression[1], rows), 0, expression[2], expression[3])
            else:
                row = (kind, encode(expression[1], rows), encode(expression[2], rows), 1, 1)
            rows.append(row)
            return len(rows) - 1
        inputs = []
        for expression, _ in fixtures:
            rows = []
            encode(expression, rows)
            inputs.append(str(len(rows)) + "\n" + "\n".join(" ".join(map(str, row)) for row in rows))
        source = "\n".join(inputs) + "\n"
        (self.root / "summary-input.txt").write_text(source)
        executable = self.root / "bundled/attribution-summary"
        output = self.run_command([executable], input=source)
        self.assertEqual([expected for _, expected in fixtures], [int(value) for value in output.splitlines()])
        for malformed in ("x\n", "1\ns 0 0 1 1\n", "1\nr 0 0 1 1\n", "2\na 0 0 1 1\nr 0 0 2 1\n"):
            self.assertEqual("", self.run_command([executable], input=malformed, success=False))

    def test_attribution_backport_detection(self):
        project = self.root / "attribution-broken/source"
        project.mkdir(parents=True)
        fixed = self.previous_fix_fixture()
        for module, function in (("ParticleAttribution", "particle_attribution"), ("ParticleCounter", "particle_counters"),
                                 ("ParticleRange", "particle_ranges")):
            fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2{module}Fix.cmake")\n', "")
            fixed = fixed.replace(f'qore_xml_fix_libxml2_{function}("{self.source}" '
                                  '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        (project / "CMakeLists.txt").write_text(fixed)
        build = self.root / "attribution-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        self.configure("attribution-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        probe = (self.root / "attribution-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("particle_identity=PASS", probe)
        self.assertIn("particle_attribution=FAIL", probe)
        self.configure("attribution-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)

    def test_counter_backport_detection_and_source_idempotence(self):
        import hashlib
        project = self.root / "counter-broken/source"
        project.mkdir(parents=True)
        fixed = self.previous_fix_fixture()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2ParticleRangeFix.cmake")\n', "")
        fixed = fixed.replace(f'qore_xml_fix_libxml2_particle_ranges("{self.source}" '
                              '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2ParticleCounterFix.cmake")\n', "")
        fixed = fixed.replace(f'qore_xml_fix_libxml2_particle_counters("{self.source}" '
                              '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        (project / "CMakeLists.txt").write_text(fixed)
        build = self.root / "counter-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        self.configure("counter-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        probe = (self.root / "counter-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("particle_identity=PASS", probe)
        self.assertIn("particle_attribution=FAIL", probe)
        self.configure("counter-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        directory = self.root / "bundled/_deps/qore_xml_libxml2-build"
        paths = [directory / "qore-particle-attribution-fix/xmlschemas.c",
                 directory / "qore-particle-counters-fix/xmlregexp.c"]
        stamps = {path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths}
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        for path, expected in stamps.items():
            self.assertEqual(expected, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def test_range_backport_detection_and_source_idempotence(self):
        import hashlib
        project = self.root / "range-broken/source"
        project.mkdir(parents=True)
        fixed = self.previous_fix_fixture()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2ParticleRangeFix.cmake")\n', "")
        fixed = fixed.replace(f'qore_xml_fix_libxml2_particle_ranges("{self.source}" '
                              '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")
        (project / "CMakeLists.txt").write_text(fixed)
        build = self.root / "range-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("range-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "range-broken-auto/system-libxml2/namespace-probe.log").read_text()
        for label in ("qname_values", "qname_unions", "uri_identity", "entity_values", "occurs_values",
                      "particle_identity", "particle_attribution"):
            self.assertIn(label + "=PASS", probe)
        self.assertIn("particle_ranges=FAIL", probe)
        self.configure("range-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        directory = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-particle-ranges-fix"
        stamps = {path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
                  for path in (directory / "xmlschemas.c", directory / "xmlregexp.c")}
        self.assertEqual(2, len(stamps))
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        for path, expected in stamps.items():
            self.assertEqual(expected, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def previous_fix_fixture(self):
        """Keep fixtures for earlier fixes independent of the final-default correction."""
        fixed = self.previous_substitution_fixture()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2TypeFinalFix.cmake")\n', "")
        return fixed.replace(f'qore_xml_fix_libxml2_type_finals("{self.source}" '
                             '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")

    def previous_substitution_fixture(self):
        """Build the verified dependency with only the substitution correction omitted."""
        fixed = self.previous_consistency_fixture()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2ElementSubstitutionFix.cmake")\n', "")
        return fixed.replace(f'qore_xml_fix_libxml2_element_substitution("{self.source}" '
                             '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")

    def test_element_consistency_allocation_cleanup(self):
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "edc-schema-allocation", "-j4"])
        self.assertIn("Native element consistency cleanup: PASS",
                      self.run_command([self.root / "bundled/edc-schema-allocation"]))

    def previous_schema_whitespace_fixture(self):
        """Build all earlier corrections without declaration whitespace cleanup."""
        fixed = (self.root / "fixed/source/CMakeLists.txt").read_text()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2SchemaWhitespaceFix.cmake")\n', "")
        return fixed.replace(f'qore_xml_fix_libxml2_schema_whitespace("{self.source}" '
                             '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")

    def test_schema_whitespace_backport_detection_and_idempotence(self):
        import hashlib
        project = self.root / "schema-whitespace-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(self.previous_schema_whitespace_fixture())
        build = self.root / "schema-whitespace-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("schema-whitespace-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "schema-whitespace-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("wildcard_types=PASS", probe)
        self.assertIn("schema_whitespace=FAIL", probe)
        self.configure("schema-whitespace-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        path = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-schema-whitespace-fix/xmlschemas.c"
        stamp = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual("a3db543b225021533cf966759c304f7a955ef85b1b645c1828334413b61b7004", stamp[1])
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertEqual(stamp, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def previous_wildcard_type_fixture(self):
        """Build every earlier correction while omitting strict xsi:type assessment."""
        fixed = self.previous_schema_whitespace_fixture()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2WildcardTypeFix.cmake")\n', "")
        return fixed.replace(f'qore_xml_fix_libxml2_wildcard_types("{self.source}" '
                             '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")

    def test_wildcard_type_allocation_cleanup(self):
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "wildcard-type-allocation", "-j4"])
        self.assertIn("Native wildcard instance-type phase cleanup: PASS",
                      self.run_command([self.root / "bundled/wildcard-type-allocation"]))

    def test_wildcard_type_backport_detection_and_idempotence(self):
        import hashlib
        project = self.root / "wildcard-type-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(self.previous_wildcard_type_fixture())
        build = self.root / "wildcard-type-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("wildcard-type-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "wildcard-type-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("wildcard_ids=PASS", probe)
        self.assertIn("wildcard_types=FAIL", probe)
        self.configure("wildcard-type-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        path = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-wildcard-type-fix/xmlschemas.c"
        stamp = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual("75e468136eaa0dbf8c95071194d41937d6da6f188ee799a47cf50902a98ad65b", stamp[1])
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertEqual(stamp, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def previous_wildcard_id_fixture(self):
        """Build every earlier correction while omitting wildcard ID reporting."""
        fixed = self.previous_wildcard_type_fixture()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2WildcardIdFix.cmake")\n', "")
        return fixed.replace(f'qore_xml_fix_libxml2_wildcard_ids("{self.source}" '
                             '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")

    def test_wildcard_id_constraint_allocation_cleanup(self):
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "wildcard-id-allocation", "-j4"])
        self.assertIn("Native attribute use constraints: PASS",
                      self.run_command([self.root / "bundled/wildcard-id-allocation"]))

    def test_wildcard_id_backport_detection_and_idempotence(self):
        import hashlib
        project = self.root / "wildcard-id-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(self.previous_wildcard_id_fixture())
        build = self.root / "wildcard-id-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("wildcard-id-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "wildcard-id-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("element_consistency=PASS", probe)
        self.assertIn("wildcard_ids=FAIL", probe)
        self.configure("wildcard-id-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        path = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-wildcard-id-fix/xmlschemas.c"
        stamp = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual("3a78da4283035b2691688766e2bd6dda205a14cf36ce8430af3ec03677d2e80f", stamp[1])
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertEqual(stamp, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def previous_consistency_fixture(self):
        """Build the verified dependency with only declaration consistency omitted."""
        fixed = self.previous_wildcard_id_fixture()
        fixed = fixed.replace(f'include("{REPO}/cmake/QoreXmlLibXml2ElementConsistencyFix.cmake")\n', "")
        return fixed.replace(f'qore_xml_fix_libxml2_element_consistency("{self.source}" '
                             '"${CMAKE_CURRENT_BINARY_DIR}/libxml")\n', "")

    def test_consistency_backport_detection_and_idempotence(self):
        import hashlib
        project = self.root / "consistency-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(self.previous_consistency_fixture())
        build = self.root / "consistency-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("consistency-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "consistency-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("element_substitution=PASS", probe)
        self.assertIn("element_consistency=FAIL", probe)
        self.configure("consistency-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        path = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-element-consistency-fix/xmlschemas.c"
        stamp = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual("a918602d87b2ed7a35f0d7d26189e9190365123966feb8525a9aba2344711d67", stamp[1])
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertEqual(stamp, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def test_consistency_system_diagnostics_are_independent(self):
        project = self.root / "consistency-alternative/source"
        project.mkdir(parents=True)
        text = (self.root / "fixed/source/CMakeLists.txt").read_text()
        text += r'''
get_target_property(edc_sources LibXml2 SOURCES)
foreach(edc_entry IN LISTS edc_sources)
    get_filename_component(edc_name "${edc_entry}" NAME)
    if(edc_name STREQUAL "xmlschemas.c")
        file(READ "${edc_entry}" edc_text)
        string(REPLACE "xmlSchemaPCustomErr(scope->parser, XML_SCHEMAP_FAILED_PARSE,"
            "xmlSchemaPCustomErr(scope->parser, XML_SCHEMAP_MG_PROPS_CORRECT_1," edc_text "${edc_text}")
        string(REPLACE "cos-element-consistent: declarations with the same expanded name have inconsistent type definitions"
            "Conflicting declarations in this model" edc_text "${edc_text}")
        set(edc_replacement "${CMAKE_CURRENT_BINARY_DIR}/alternative-schema.c")
        file(WRITE "${edc_replacement}" "${edc_text}")
        list(REMOVE_ITEM edc_sources "${edc_entry}")
        list(APPEND edc_sources "${edc_replacement}")
        break()
    endif()
endforeach()
set_property(TARGET LibXml2 PROPERTY SOURCES "${edc_sources}")
'''
        (project / "CMakeLists.txt").write_text(text)
        build = self.root / "consistency-alternative/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        output = self.configure("consistency-alternative-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM",
            f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}")
        self.assertIn("passes namespace identity probe", output)
        log = (self.root / "consistency-alternative-system/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("element_consistency=PASS", log)
        self.assertFalse((self.root / "consistency-alternative-system/_deps").exists())

    def test_substitution_backport_detection_and_idempotence(self):
        import hashlib
        project = self.root / "substitution-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(self.previous_substitution_fixture())
        build = self.root / "substitution-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("substitution-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "substitution-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("type_final_defaults=PASS", probe)
        self.assertIn("element_substitution=FAIL", probe)
        self.configure("substitution-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        path = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-element-substitution-fix/xmlschemas.c"
        stamp = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual("3c2709538ea99bd15fe64b61a30c96cfcab57153a074167bf23b89e32391674c", stamp[1])
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertEqual(stamp, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def test_final_default_backport_detection_and_idempotence(self):
        import hashlib
        project = self.root / "final-broken/source"
        project.mkdir(parents=True)
        (project / "CMakeLists.txt").write_text(self.previous_fix_fixture())
        build = self.root / "final-broken/build-debug"
        self.run_command(["cmake", "-S", project, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        libraries = list((build / "libxml").glob("libxml2.so")) + list((build / "libxml").glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={self.fixed_include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("final-broken-auto", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "final-broken-auto/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("particle_ranges=PASS", probe)
        self.assertIn("type_final_defaults=FAIL", probe)
        self.configure("final-broken-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)
        path = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-type-final-fix/xmlschemas.c"
        stamp = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        self.assertEqual(stamp, (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()))

    def test_unknown_regexp_source_is_rejected(self):
        override = self.qname_source_override("changed-regexp-source", "xmlregexp.c", fixed=False)
        output = self.configure("changed-regexp-build", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                                f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={override}", success=False)
        self.assertIn("Unexpected libxml2 xmlregexp.c; cannot apply particle identity fix", " ".join(output.split()))

    def test_entity_fixes_preserve_sources_and_reconfigure(self):
        import hashlib
        hashes = {"xmlschemas.c": "bed8bfbfd61a2025b67b7a0e4d05ce50093e7a6bb5e43a3ebac343b8df4329a7",
                  "xmlschemastypes.c": "08cac7d1dbdb617688ac5b36ab6fee75f634e5bf0372aa0e6569a0bebe3b0c8f"}
        replacements = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-entity-fix"
        times = {name: (replacements / name).stat().st_mtime_ns for name in hashes}
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        for name, expected in hashes.items():
            self.assertEqual(expected, hashlib.sha256((self.source / name).read_bytes()).hexdigest())
            self.assertEqual(times[name], (replacements / name).stat().st_mtime_ns)
        self.run_command(["cmake", "--build", self.root / "bundled", "--target", "entity-allocation", "-j4"])
        self.assertIn("ENTITY allocation and cancellation cleanup: PASS",
                      self.run_command([self.root / "bundled/entity-allocation"]))

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
        uri_hashes = {"uri.c": "16cc4794868487cb3dac76faffef603163f8d8472508735df7b5a4cf0a4c4e44",
                      "tree.c": "2045cf4d1a93bd5d2e9b2781ed92a748e146e30c2919f59fb3ea1845f5795dea",
                      "xmlschemas.c": hashes["xmlschemas.c"]}
        uri_replacements = self.root / "bundled/_deps/qore_xml_libxml2-build/qore-uri-fix"
        uri_times = {name: (uri_replacements / name).stat().st_mtime_ns for name in uri_hashes}
        self.configure("bundled", "-DQORE_XML_LIBXML2_PROVIDER=BUNDLED",
                       f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}")
        for name, expected in hashes.items():
            self.assertEqual(expected, hashlib.sha256((self.source / name).read_bytes()).hexdigest())
            self.assertEqual(times[name], (replacements / name).stat().st_mtime_ns)
        for name, expected in uri_hashes.items():
            self.assertEqual(expected, hashlib.sha256((self.source / name).read_bytes()).hexdigest())
            self.assertEqual(uri_times[name], (uri_replacements / name).stat().st_mtime_ns)
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

    def test_qname_identity_backport_without_union_fix_is_rejected(self):
        # Model a distribution that backported only the previous QName fixes.
        # A new regression must invalidate its otherwise passing probe result.
        import shutil
        partial = self.root / "partial/source"
        partial.mkdir(parents=True)
        for entry in self.source.iterdir():
            if entry.name not in ("xmlschemas.c", "xmlschemastypes.c"):
                (partial / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        original = (self.source / "xmlschemas.c").read_text()
        old = "{\n    if (vctxt->sax != NULL) {\n"
        self.assertEqual(1, original.count(old))
        (partial / "xmlschemas.c").write_text(original.replace(old,
            "{\n    /* The xml prefix is bound even without a namespace declaration. */\n"
            '    if (xmlStrEqual(prefix, BAD_CAST "xml")) {\n'
            "        return (XML_XML_NAMESPACE);\n    }\n    if (vctxt->sax != NULL) {\n"))
        import hashlib
        self.assertEqual("e7910a943964ce25bac32479fec4b244e1b0080abd6ae7146210d88ca3877098",
                         hashlib.sha256((partial / "xmlschemas.c").read_bytes()).hexdigest())
        shutil.copyfile(self.root / "bundled/_deps/qore_xml_libxml2-build/qore-qname-fix/xmlschemastypes.c",
                        partial / "xmlschemastypes.c")
        build = self.root / "partial/build-debug"
        self.run_command(["cmake", "-S", partial, "-B", build, "-DCMAKE_BUILD_TYPE=Debug",
                          "-DBUILD_SHARED_LIBS=ON", "-DLIBXML2_WITH_PROGRAMS=OFF",
                          "-DLIBXML2_WITH_TESTS=OFF", "-DLIBXML2_WITH_PYTHON=OFF"])
        self.run_command(["cmake", "--build", build, "--target", "LibXml2", "-j4"])
        include = self.root / "partial/include"
        shutil.copytree(self.source / "include/libxml", include / "libxml")
        shutil.copyfile(build / "libxml/xmlversion.h", include / "libxml/xmlversion.h")
        libraries = list(build.glob("libxml2.so")) + list(build.glob("libxml2.dylib"))
        self.assertEqual(1, len(libraries))
        options = [f"-DLIBXML2_LIBRARY={libraries[0]}", f"-DLIBXML2_INCLUDE_DIR={include}",
                   f"-DFETCHCONTENT_SOURCE_DIR_QORE_XML_LIBXML2={self.source}"]
        output = self.configure("partial-system", "-DQORE_XML_LIBXML2_PROVIDER=AUTO", *options)
        self.assertIn("using private static libxml2 2.15.4", output)
        probe = (self.root / "partial-system/system-libxml2/namespace-probe.log").read_text()
        self.assertIn("qname_values=PASS", probe)
        self.assertIn("qname_unions=FAIL", probe)
        self.configure("partial-system", "-DQORE_XML_LIBXML2_PROVIDER=SYSTEM", *options, success=False)

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
