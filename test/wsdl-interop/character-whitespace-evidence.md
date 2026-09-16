# Character whitespace preservation (P5-21)

Copyright (C) 2026 Qore Technologies, s.r.o.

Whitespace between children of mixed or generic XML is character data. XML 1.0
[section 2.10](https://www.w3.org/TR/REC-xml/#sec-white-space) distinguishes the
application's whitespace handling from XML parsing; XSD 1.0 defines
[anyType as mixed content](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#ur-type-itself).
The schema-free data parser previously discarded those characters when no other
text or CDATA appeared at the same parent. Schema validation accepted the changed
output, so the missing typed/infoset comparison exposed this defect.

`XPF_PRESERVE_WHITESPACE` retains whitespace entries through node finalization,
including inherited/local `xml:space` resets. Combine it with
`XPF_PRESERVE_ORDER` for character positions among repeated children. Existing
unflagged parsing retains its data-grouping behavior. WSDL instance parsing and
XML-value views use the new flag; schema-aware conversion still discards allowed
indentation in element-only models. Declaration parsing retains its existing
source grammar path. Direct hash-input callers must request both flags.

## Verification

- `xml-preserve-whitespace.qtest`: 5 cases / 2,152 assertions, including all
  XML data readers, schema validation, default resets, 1/32/1024 repeated children,
  malformed XML and actual interruption/retry. Existing whitespace suite: 7/1,863.
- `wsdl-character-whitespace.qtest`: 2/114; mixed/generic schemas, saved values
  and providers, complete carriers, nested content and element-only rejection.
- Extended `wsdl-generic-http.qtest`: 5/270, actual SOAP1.1/1.2 client/server and
  SoapDataProvider request/response character preservation.
- `test_character_whitespace.py`: 288 conversions across both actual bindings,
  both directions, saved contracts/providers and both projection modes. Exact
  expanded names, attributes, characters and child order are checked. Pinned
  Xerces validates all 18 sources and 288 outputs under three schemas. The
  comparator's negative test detects schema-valid whitespace deletion/movement.
  The same integration matrix fails all 288 conversions against a snapshot of
  parent commit `9b8276d` using the identical new native binary: WSDL must request
  preservation at its instance boundary.
  The existing legacy generic scalar policy is explicit: 40 rows add 56 checked
  `xs:string` annotations; native mode retains annotation absence.
- Final **193 suites / 97,747 assertions**, stable source/runtime hashes,
  no unexpected warnings/errors. Seven deliberately caught comparator assertion
  failures in `soap.qtest` remain its accepted negative self-tests. The first
  broad run caught an overbroad source-parser flag change and an obsolete XML-view
  grouping expectation; the final full run follows both corrections.
- Four affected Valgrinds: **zero errors, zero lost bytes**, direct frozen Qore
  ELF with signals and PCRE2 JIT disabled. Exit reachable bytes: xml-preserve-whitespace 114,812, xml-whitespace 114,876, wsdl-character-whitespace 125,098, wsdl-generic-http 127,857.
- Both native and WSDL documentation targets, the executable public example,
  and 17 survey tests pass. Debug
  build, `/usr` prefix, frozen new XML qmod and Qore `16ae86ca7`; no install/push.

## Corpus and remaining accounting

All four legacy/native survey/strict-coverage commands pass, with unchanged
verdicts/counts and all previously recorded failures/unassessed stages visible.
Only WSDL source metadata and eight output bodies in each coverage mode change.
Every changed row now matches the original generic subtree's characters, names,
attributes and child order; the parent commit's output fails that same comparison.
Affected families: `AnyTypeElement` and
`GlobalElementComplexTypeSequenceExtension`, both directions and input versions.

The exploratory Xerces PSVI comparison assesses 2,096 before/after pairs with no
validation failures. Exact order differs in 20 rows of four previously documented
flat-record/all families; comparing per-name order only in element-only nodes
finds no other difference. This remains a prototype: comprehensive datatype and
namespace-context comparison tests are required before complete P5 accounting.
The prototype is under `/tmp/wsdl-p5-typed-accounting/after-whitespace/`; it is not
a substitute for the mandatory corpus gate or complete SOAP conformance.

Artifacts, original failure logs, corpus diffs and source-character proof:
`/tmp/wsdl-p5-21-whitespace/`. See [inventory](P5-21-validation.json) and
[all 62 audit checks](audits/P5-21-character-whitespace.md). P5 remains in progress;
P6–P9 remain required, with no outstanding user decision.
