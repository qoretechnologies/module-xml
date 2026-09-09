# QName identity in the libxml2 dependency

Copyright (C) 2026 Qore Technologies, s.r.o.

CMake selects a system libxml2 only when the runtime namespace probe succeeds.
The probe checks namespace declaration escaping, 48 QName/NOTATION schema/document
pairs and 100 QName union pairs using DOM and streaming validation. Valid
documents must produce no error or warning callbacks; invalid documents must
produce a rejection diagnostic. DOM contexts are reused after a known-invalid
document to verify recovery. It covers implicit and explicit `xml`
bindings, prefix aliases, wrong and missing bindings, malformed names, and
enumeration identity across absent and explicitly empty default namespaces.
A package version string does not establish correctness; a distribution
backport passing the probe remains eligible.
The probe also checks [schema URI identity and XML Base](xml-schema-uris.md);
a library with only the QName fixes is not sufficient.

Unpatched libxml2 2.15.4 has three QName defects. Its streaming namespace lookup
searches only declared bindings and misses the predefined `xml` binding. Its
QName comparison distinguishes a null namespace pointer from an empty URI,
although both denote no namespace. The fixes supply the implicit binding at
`xmlSchemaLookupNamespace()` and compare null/empty namespace strings equally
at the QName/NOTATION value comparison boundary.

During ordered union matching, an unbound QName candidate previously called
`xmlSchemaCustomErr()` even when `xmlSchemaVCheckCVCSimpleType()` passed
`fireErrors=0`. That call incremented the validator's error state and invoked
application callbacks although a later string member accepted the value.
`xmlSchemaValidateQName()` now receives `fireErrors` and guards that diagnostic.
The candidate still returns its datatype error and releases its temporary name;
a standalone QName or a union with no matching member still rejects normally.
An allocation/internal error retains its existing error reporting. No fix
allocates additional memory or changes supplied XML. Other namespace and local-name comparisons remain exact.

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
a fixed shared backport with an older advertised version, a partial backport
missing union error isolation, offline sources,
provider switching, source integrity, reconfiguration, installation and cross
build selection. `qore-xml-namespace-probe` provides the runtime check and a
standalone Valgrind target. The QName value matrix also exercises the selected
dependency through `XmlReader` against all 1,008 generated schema/document pairs.

Normative references: [QName identity](https://www.w3.org/TR/xmlschema-2/#QName)
and [the implicit XML namespace and default scope](https://www.w3.org/TR/REC-xml-names/#ns-decl).
Upstream implementation: [namespace lookup](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemas.c)
and [value comparison](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemastypes.c).

The union matrix covers QName/string member order, namespace-sensitive string
and QName enumerations, nested unions, lists as union members, union-valued
list items, empty values and invalid lexical forms. A string enumeration such
as unbound `p:Name` accepts that string. Binding `p` in the instance instead
selects the earlier QName member and must fail that string enumeration.
`test/xml-qname-unions.qtest` exercises public schema parsing and streaming,
retained XML values, exact exception categories and cancellation. The independent
`test/wsdl-interop/test_qname_union_validator.py` checks 300 documents across
content-only, attribute-only and combined models against pinned Xerces. Its
Python libxml2 verdicts retain the precise unpatched-library disagreements;
the native dependency must agree with every normative verdict.

Example using a string fallback for a catalog label whose prefix is unbound:

```qore
%modern
%requires xml
string schema = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="label"><xs:simpleType><xs:union memberTypes="xs:QName xs:string"/>'
    '</xs:simpleType></xs:element></xs:schema>';
@assert(parse_xml_with_schema('<label>catalog:Product</label>', schema).label == "catalog:Product");
```

The applicable requirements are XSD 1.0 [ordered union matching](https://www.w3.org/TR/xmlschema-2/#union-datatypes)
and [datatype validity](https://www.w3.org/TR/xmlschema-2/#cvc-datatype-valid).
See [regression evidence](../test/wsdl-interop/qname-union-validator-evidence.md).
