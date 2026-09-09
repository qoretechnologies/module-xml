# QName identity in the libxml2 dependency

Copyright (C) 2026 Qore Technologies, s.r.o.

CMake selects a system libxml2 only when the runtime namespace probe succeeds.
The probe checks namespace declaration escaping and 48 QName/NOTATION schema/document
pairs using DOM and streaming validation. It covers implicit and explicit `xml`
bindings, prefix aliases, wrong and missing bindings, malformed names, and
enumeration identity across absent and explicitly empty default namespaces.
A package version string does not establish correctness; a distribution
backport passing the probe remains eligible.

Unpatched libxml2 2.15.4 has two QName defects. Its streaming namespace lookup
searches only declared bindings and misses the predefined `xml` binding. Its
QName comparison distinguishes a null namespace pointer from an empty URI,
although both denote no namespace. The fixes supply the implicit binding at
`xmlSchemaLookupNamespace()` and compare null/empty namespace strings equally
at the QName/NOTATION value comparison boundary. Neither fix allocates memory
or changes supplied XML. Other namespace and local-name comparisons remain exact.

`QoreXmlLibXml2QNameFix.cmake` compiles corrected build-tree copies of
`xmlschemas.c` and `xmlschemastypes.c` for the private static fallback. The
downloaded/offline source tree remains byte-identical. Exact original and
corrected SHA-256 values are checked before selecting the compile inputs.
Already corrected source overrides are accepted by their complete file hashes;
other modified files fail configuration. Reconfiguration preserves unchanged
compile-input timestamps. The existing pinned URL, archive hash, hidden symbols,
catalog ownership correction and notice installation still apply.

`AUTO` falls back when a system candidate fails; `SYSTEM` fails configuration.
Cross builds require an emulator to establish system eligibility; without one,
`AUTO` uses the private fallback. No system library is installed or replaced.
Autotools continues to use its explicitly selected system dependency.

`test/cmake/test_libxml2_provider.py` exercises an unpatched current release,
a fixed shared backport with an older advertised version, offline sources,
provider switching, source integrity, reconfiguration, installation and cross
build selection. `qore-xml-namespace-probe` provides the runtime check and a
standalone Valgrind target. The QName value matrix also exercises the selected
dependency through `XmlReader` against all 1,008 generated schema/document pairs.

Normative references: [QName identity](https://www.w3.org/TR/xmlschema-2/#QName)
and [the implicit XML namespace and default scope](https://www.w3.org/TR/REC-xml-names/#ns-decl).
Upstream implementation: [namespace lookup](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemas.c)
and [value comparison](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemastypes.c).
