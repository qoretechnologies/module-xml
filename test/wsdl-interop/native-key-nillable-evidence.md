# P5-20d native key nillable evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

## Requirement and root cause

[XSD 1.0 Structures 3.11.4 clause 4.2.3](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-identity-constraint)
forbids key element fields assessed against nillable declarations, including
non-nil values. The pinned private libxml2 field matcher checked simple content
and tuple membership but omitted the declaration's nillable flag. Its previous
build accepted a key field declared `nillable=true` with value `1`, both without
`xsi:nil` and with `xsi:nil=false`. Pinned Xerces rejects both correctly.

The correction checks the effective declaration only for matched element key
fields, then reports the existing identity-constraint error and follows normal
state deregistration. The value remains available to other matching constraints.
It adds no allocation or mutable shared state; diagnostic allocation failures
retain rejection and cleanup. See [implemented design](../../design/native-key-nillable.md).

## Independent matrix and native consumers

The authored `fixtures/key-nillable.json` has 63 valid schemas and one instance
per schema: 33 valid and 30 invalid documents. It covers simple/complex simple
content, nillable/ordinary declarations, absent/false/true nil markers, missing
and multiple fields, attributes on nillable owners, unselected nodes, duplicate
keys, element references, substitution members, strict wildcards, dynamic types,
and key/unique constraints sharing a field in either declaration order.

All cases agree with pinned Xerces 2.12.2 using the existing independently pinned
harness. `test/xml-key-nillable.qtest` passes 220 assertions through XmlReader,
parse_xml_with_schema and XmlDoc validation, including error categories and
unchanged DOM content. Nil unique/keyref tuple qualification is explicitly
outside this correction; its interpretation decision remains pending.

## Configuration and cleanup

The configure probe runs ten cases through DOM and reader validation, including
reuse after rejection. A real shared library with every prior correction but
this one fails `key_nillable`; AUTO selects the private static dependency and
SYSTEM reports the failed probe. A fully fixed shared library remains usable.
Repeated configuration preserves generated source timestamps. The new inputs
are in the source distribution. All 72 provider tests pass.

A direct native harness isolates the new rejection branch and tests all six
diagnostic allocation positions with both one-shot and persistent failures.
Every trial preserves rejection, deregisters the matched state and returns to
the allocation baseline; a successful recovery follows each failure. Direct
Valgrind records 508 allocations, 508 frees, zero live bytes and zero errors.
The Qore matrix under Valgrind, with signals and PCRE2 JIT disabled, has zero
errors/lost bytes; 117,480 bytes remain reachable from runtime globals.

## Final validation and scope

The working tree passes 54 affected Qore suites (24,657 assertions), including
the pending component suite. To validate the native commit independently, an
isolated source snapshot overlays only this correction on committed `0dd3110`;
its 53 affected suites pass. Both snapshots run all four corpus commands
(legacy/native decoding, diagnostic/strict reporting, both SOAP versions), and
each report is exactly unchanged from its corresponding baseline. No diagnostic
failure is relabeled as conformance. The existing NOTATION typed-accounting
failures remain visible and assigned to remaining P5 work.

The native module builds in the existing Debug `/usr` configuration, without
installation. Native documentation builds without warnings/errors. Survey unit
tests and the full 62-item audit pass. Source/runtime/fixture hashes, exact test
results and guide hashes are in [P5-20d-validation.json](P5-20d-validation.json);
see [full audit](audits/P5-20d-native-key-nillable.md).
Reproducible commands and logs are in
`/tmp/wsdl-p5-20d-identity-fields/final/`, with committed-source evidence under
`committed-wsdl/` and its isolated input under `native-snapshot/`.

This is a native-only prerequisite, independent of the uncommitted P5-20c
WSDL components. The Qore serialization source-lifetime blocker is still
`/tmp/wsdl-identity-serialization-lifetime/README.md`; the installed library
has not changed. No Qore source was modified or installed here. Scoped WSDL
instance tuples, the nil interpretation decision, complete typed accounting
and P6-P9 remain outstanding.
