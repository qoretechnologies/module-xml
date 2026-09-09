# P3-40: native ENTITY/ENTITIES evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment repairs native XSD validation and XML reader error ownership.
WSDL's separate ENTITY document-context integration remains the next P3 task.
No SOAP document restriction is relaxed.

## Requirements and root causes

XSD 1.0 Part 2 section 3.3.11 defines ENTITY names by the containing document's
unparsed entities. Part 1 section 3.14.4 applies the document constraint after
datatype/facet validation; Part 2 section 2.5.1.3 selects the first matching union
member. XML 1.0 section 4.2 preserves the first general-entity declaration.
Parameter entities have a separate name space. SOAP 1.1 section 3 and SOAP 1.2
section 5 prohibit document type declarations.

Pinned libxml2 2.15.4 had four relevant gaps: element validation passed no DOM
node to ENTITY conversion; SAX split callbacks forwarded declarations without
retaining document context; computed ENTITY values were unimplemented; and the
built-in lists' minimum-length facets were absent from the effective facet set
and bypassed during instance validation. The checked build-tree corrections
record first bindings per context, construct typed ENTITY strings, defer document
checks until after datatype/facet selection, and restore inherited list facets.

The restriction matrix additionally found that `xmlSchemaDeriveAndValidateFacets`
never compared the effective minimum and maximum length. The correction compares
local or inherited facets as required by [Part 2 section 4.3.2.4](https://www.w3.org/TR/xmlschema-2/#minLength).
It rejects contradictory schemas and preserves equal boundaries. All corrections
apply to general schema types, without fixture-name branches.

A schema callback can raise a Qore exception while libxml2 still returns a node
or ordinary EOF. `read(xsink)` previously passed that status through, and
`getXmlData()` could replace an error with a successful lower-depth boundary.
The conversion could then release a partial hash together with the exception.
The reader now returns failure for callback exceptions and only treats an actual
node as an element boundary; `xml_stack` retains and releases partial values.

## Independent evidence and exact-value coverage

The context matrix has 91 schemas, including six invalid default/fixed schemas,
and 5,679 documents under valid schemas: 1,743 valid and 3,936 invalid. Every
such document has seven native verdicts (39,753 total): whole-document parsing,
XmlDoc validation, reader consumption, cursor conversion, grouped conversion,
text-schema attachment and file-schema attachment. Expected errors, complete
consumption, source text/attributes and raw XML projection are checked. The 54
documents belonging to invalid schemas are explicitly unreachable at schema
construction, rather than skipped or counted as document successes.

A second matrix checks 432 schema constructions across eight types, six bound
pairs, both inheritance orders and three inheritance depths. Nine invalid rows
expose a pinned Xerces defect: `XSSimpleTypeDecl.applyFacets()` uses an `else if`
for an inherited minimum after checking an inherited maximum. Thus lowering a
built-in list's minimum from one to zero is incorrectly accepted when a base type
also supplies maximum one. The test asserts those nine exact false acceptances,
while requiring native rejection and the normative minimum restriction. All
remaining Xerces schema/document verdicts agree with the specified expectations.

Xerces-J 2.12.2 JAR SHA-256:
`6fc991829af1708d15aea50c66f0beadcd2cfeb6968e0b2f55c1b0909883fe16`.
The corresponding source archive SHA-256 is
`3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`;
`XSSimpleTypeDecl.java` SHA-256 is
`1f81a456d6b9dcbde0627fbeb51beb1381f2e166230a4530f2711c20c227d9f4`.

The standalone oracle uses Xerces DOM because its JAXP SAX ValidatorHandler only
records unparsed declarations, losing an earlier parsed binding. DOM preserves
that first binding. Readable-file controls verify that external general entities,
parameter entities and DTD subsets cannot supply data or declarations. Schema
DTDs and ordinary SOAP DOCTYPEs remain rejected. No oracle dependency or upstream
fixture was modified.

The generated fixture inventory is `/tmp/wsdl-p3-40-final-fixtures.json`, SHA-256
`7ea2cfba6ff302d0bd98da0cebc0c13a1fde684ee7e79e8d4a3dc036ab40a383`.
The committed test sources deterministically reconstruct those fixtures.

## Build and memory evidence

Both builds use `/usr`, matching `/usr/bin/qore`, with Debug in `build-debug/`
and Release in `build/`. They load locally without installation. Private libxml2
source files remain immutable, including offline overrides. The final generated
`xmlschemas.c` SHA-256 is
`955e8848f6446219f5b1546993ab55b27ed2512828c0cea5d6e30b6da1f3a105`;
`xmlschemastypes.c` is
`6c8d53841944eff6e81c63dbd3059a0f27abb3bdd114e4aa04f56e1b69f6d2bd`.

Final Debug XML module SHA-256:
`95ed6b98adc9c3171883c2c5d8e848431d1bf1720961faca8502ca54466e5824`.
Final Release XML module SHA-256:
`90abd462eb4c3e4ee6cc3c12bf38c527c1bf2a41852e8f610f189edcda656a9a`.
The isolated Debug core artifact remains
`40c2824efa1fdd66cd20c50ad767dd18614c6f6f2842d9a5fd4e94311e89802e`.

The original six-case Valgrind run exposed 336 leaked bytes. Isolated cases alone
were clean; GDB on the complete suite identified the partial return for `<value/>`
and 32 repeated `<root><image/></root>` conversions with rejected ENTITY defaults.
The expanded pre-fix run leaked 21,840 bytes. The final eight-case run has zero
Valgrind errors and zero definitely, indirectly or possibly lost bytes. Its source
snapshot is byte-identical to the committed qtest. The native allocation test
covers 78 failure sites, callback forwarding, context reuse, early unplug and
computed-value ownership; all heap blocks are freed with zero Valgrind errors.

Valgrind used `QORE_PCRE2_NO_JIT=1`, `qore -b --enable-debug --exec-mode=jit`, and a
bounded 300-second deadline. The existing isolated core artifact still produces
`zero subprog, missing DW_AT_abstract_origin in DW_TAG_inlined_subroutine` while
Valgrind reads debug information. This is the already tracked P9 debug-artifact
issue, not a clean-diagnostics claim; no suppression was added.

## Final gates

- Native ENTITY suite: eight cases / 753 assertions, Debug and Release; all four
  AST, IR, JIT and tiered modes pass on Debug.
- Independent ENTITY matrices and oracle policy: four Python methods pass on
  both builds, including all native verdicts and 432 schema constructions.
- Full XML gate: 90 suites / 937 cases / 35,897 reported assertions; no test-case
  failure or warning. The aggregate uses QUnit's reported assertion counts.
- CMake provider suite: 22 methods, including a QName/URI-fixed but ENTITY-broken
  system library, corrected backports, AUTO/SYSTEM behavior, immutable sources,
  no-op reconfigure timestamps and installation isolation.
- Survey tests: 15 methods; independent oracle protocol: seven methods;
  resource/URI/oracle integration: seven, six and five methods respectively.
- Both native probes and allocation targets pass; the documented example executes;
  Debug/Release builds and Doxygen produce no warning/error diagnostics.
- The complete both-version diagnostic report is exactly equal to the prior
  `current-report.json`, including original hashes, values and failure counts.
  It retains 102 decode failures, two serialization failures, 42 invalid outputs
  and four valid-input invalid outputs assigned to the remaining implementation.

Logs are `/tmp/wsdl-p3-40-*-final.log`, the full gate manifest is
`/tmp/wsdl-p3-40-final-xml-gate.json`, and the exact report comparison is
`/tmp/wsdl-p3-40-report-comparison-final.json`. Source/artifact/log hashes are
recorded in `/tmp/wsdl-p3-40-final-manifest.json`.
The [full audit](audits/P3-40-entity-native.md) resolves all 62 items:
21 Pass / 41 N/A / 0 Fail. P3 remains active; P4–P9 acceptance is still outstanding.
