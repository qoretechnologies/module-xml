# P5-11 native wildcard ID evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The two omitted reports in `xmlSchemaVAttributesComplex()` allowed multiple
assessed wildcard IDs and wildcard IDs alongside a declared ID use. Reporting
alone still accepted ID restrictions because `xmlSchemaIsDerivedFromBuiltInType()`
followed `subtypes` rather than `baseType`. The schema matrix then exposed the
inverted `defVal` guard in `xmlSchemaCheckAttrUsePropsCorrect()`, which skipped
referenced constraints before computing them. All three causes are corrected.

The [implemented design](../../design/native-wildcard-ids.md) cites XSD 1.0
Structures 3.4.4/5.1-5.2, the type hierarchy and base property mapping. The
private correction is applied only to checked build-tree source. The final
`xmlschemas.c` SHA-256 is
`3a78da4283035b2691688766e2bd6dda205a14cf36ce8430af3ec03677d2e80f`.
The original libxml2 archive and source remain unchanged.

`test/xml-wildcard-ids.qtest` passes 4 cases/627 assertions in AST, IR, JIT and
tiered modes. It tests DOM/readers, qualified/unqualified names, both attribute
orders, direct/restricted ID types, present/absent declared uses, strict/lax/skip,
schema constraints, recovery, interruption and concurrent readers. The independent
matrix passes 24 schemas/180 documents/360 native paths with 160 required
rejections, plus 100 ID ancestry schema cases with 30 construction rejections.
Both methods pass in all four execution modes.

Xerces-J 2.12.2 agrees with all 180 wildcard document outcomes. Its 100-schema
results differ in six simple-content ID constraints and 48 list/union ancestry
cases, documented in the design and asserted explicitly by the matrix. Pinned
lxml/libxml2 2.12.10 accepts all 80 invalid wildcard documents. These supporting
validator results never replace the native normative expectations.

The behavioral configure probe includes the same boundaries and validates
context reuse and diagnostic presence. All 40 distinct provider tests pass:
the complete 39-test gate plus the added allocation-cleanup test. They cover
broken/fixed system libraries, backports advertising an older version, AUTO and
SYSTEM, offline sources, idempotence, distribution inputs and cross compilation.
The new allocation test injects every one of 30 allocation failures across a
valid integer default, invalid integer default and prohibited ID default.

The new native unit, complete probe and allocation test have zero Valgrind
errors and no lost blocks. The additional wildcard WSDL consumer Valgrind run
exposed an independent failed-deserialization cycle in Qore core. This remains
an explicit failing result, reproduced without XML and assigned to the next
prerequisite in [its finding](p5-deserialization-cycle-finding.md).

The existing 127-suite regression gate passes 1,274 cases/63,311 assertions
without warnings or errors. All 19 AOT/consumer/previous-matrix/harness supplements
pass. Native documentation builds cleanly and the shipment ID example executes.
Both-version corpus reports are byte-for-byte unchanged: 2,455 survey rows,
144 strict-selected WSDLs/1,388 directions, no selected failures, and 60 broader
failures still assigned to remaining phases. There are no new value, missing or
skipped failures. This is P5 progress; remaining P5-P9 acceptance is required.

See [P5-11-validation.json](P5-11-validation.json) for commands, logs, exact
fixtures, runtime hashes and the complete 62-item audit.
