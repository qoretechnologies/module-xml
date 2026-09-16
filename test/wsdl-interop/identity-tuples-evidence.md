# Scoped WSDL identity tuple acceptance (P5-20j)

Copyright (C) 2026 Qore Technologies, s.r.o.

Element key, unique and keyref constraints now assess selected typed values in
instance-local scopes through XML, saved schemas, ordinary/native/saved/soft
providers and real SOAP1.1/1.2 HTTP request/response consumers. The previous
component representation alone did not enforce instance tuples. This increment
integrates the P5-20f prototype and its separately accepted native/provider
prerequisites. See the [implemented design and example](../../design/wsdl-identity-tuples.md).

## Semantics and independent evidence

The 165 tuple models cover101 valid and64 invalid inputs: XPath unions and
expanded names, duplicate/missing/multiple fields, nil and nillable declarations,
exact scalar/list/union identities, wildcard assessment and skipped subtrees,
recursive/inherited key tables, sibling ordering, conflicts and local precedence.
The 36 builtin-instance-attribute models add16 valid and20 invalid inputs.
Their expected WSDL/native/Xerces outcomes remain separate. Pinned Xerces-J2.12.2
rechecks all 201 schemas/documents without warnings. Union deduplication and
scoped-table disagreements retain the previously documented
[nil/union](native-nil-identities-evidence.md) and [table](native-identity-tables-evidence.md)
root causes. Unassessed attribute comparisons use the documented XSD1.0
anySimpleType processor choice, rather than treating oracle agreement as normative.

Native preservation retains empty records as{} and untyped anyType text as
existing XML-data hashes. The latter preserves absence of xsi:type. A probe
against committed47122aa demonstrated invalid serialized output when inferred
string types created duplicates in a unique constraint selecting that attribute.
The correction retains source type absence; explicitly constructed scalar inputs
still request inference. Legacy projection rejections remain explicit: one
anySimpleType value-space case and two anyType attribute-presence cases. None is
counted as lossless forwarding. XML carriers preserve the original documents.
See [compatibility policy](legacy-identity-projection.md) and
[scoped accounting](identity-tuples-accounting.json), which explicitly does not
claim complete P5 typed/infoset coverage.

## Final validation

- 191 affected suites, 95,421 assertions; all final source/runtime/test hashes
 remain stable. No unexpected errors or warnings. The soap suite's seven
 deliberately caught comparator assertion failures match its accepted baseline.
- Scoped tuples:165 cases/2671 assertions. Builtin instance attributes:72/512,
 including serialization validity, native attribute presence and provider output.
- Lossless selected integer/string forwarding:1/191; actual SOAP HTTP:1/60;
 lifecycle/conversion/interruption/concurrent saved-schema tests:4/45.
- Structural memory checks retain16/32/64/128 entries for those node counts.
 Unchanged inherited tables incur zero tuple-loop visits. The test fails both
 earlier implementations at the relevant ownership/traversal assertions.
- Lifecycle Valgrind:zero errors/lost bytes,128889 reachable bytes. Final instance
 Valgrind:zero errors/lost bytes,127401 reachable bytes. Signals and PCRE2 JIT are
 disabled and the direct frozen ELF is used.
- All17 survey tests, the pinned reference test, resource test, catalog example,
 qdx/Doxygen/postprocessing and the actual docs-WSDL CMake target pass.
- Four corpus command results retain all preceding verdicts and completeness.
 Three reports change only the WSDL source hash. Native strict coverage also
 changes four GlobalElementAbstract bodies: they no longer invent xsi:type and
 retain original namespace bindings. Independent assertions compare each changed
 leaf's expanded name, text, attributes and bindings to the original source.
 Existing diagnostic failures and unassessed typed stages remain visible.
- Full 62-check audit:22 Pass/40 N/A/zero Fail.

The first 191-suite run found a regression in established empty-list record
serialization plus two tests still expecting native empty records as NOTHING.
The regression now normalizes accepted empty element-only lists before ordinary
validation; the tests assert preserved{}. All failures and intermediate logs
remain available, separate from the final acceptance run.

## Documentation dependency and reproduction

Qdx exposed a Qore astparser defect for valid unqualified select() calls.
The isolated fix under `/tmp/wsdl-astparser-select-call/` adds the callable alias
and required grammar conflicts. Its3 new cases/40 assertions and existing
111/893+4/215 suites pass; all three Valgrinds report zero errors/lost bytes.
`qore-select-call.patch` passes git apply --check against Qore develop. The patch
and reproducer are ready for separate Qore integration; this task did not edit,
build, install or commit in main Qore. XML documentation is tested with the fixed
isolated parser, without rewriting WSDL to evade the parser defect.

Use `/tmp/wsdl-p5-20i-recursive-providers/fixed-core/runtime/qore` with
`-b --enable-debug`. Set LD_LIBRARY_PATH to that frozen runtime and QORE_MODULE_DIR
to the runtime, this repository's qlib and the runtime's qlib. The runtime includes
the frozen final XML binary. Documentation additionally prepends the isolated
astparser build-debug directory. The local CMake cache uses that same context.

Exact drivers, commands, hashes and logs are under
`/tmp/wsdl-p5-20j-identity-memory/integrated/final/`. Earlier lifecycle evidence
is in its parent; the original generic-provenance reproduction is under
`/tmp/wsdl-p5-20k-generic-provenance/`. See [inventory](P5-20j-validation.json)
and [full audit](audits/P5-20j-identity-tuples.md).

Complete P5 typed/infoset accounting and P6–P9 binding/protocol/attachment/CI
acceptance remain open. No CI execution, installation or push is claimed.
