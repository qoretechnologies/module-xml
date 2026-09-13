# P5 WSDL annotation and declaration ID grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

Reproduced on `6dfcc3b`, using the fixed Qore runtime `8c0c22c15` and local Debug
XML. WSDL accepts annotation element children, unknown or schema-qualified
attributes, malformed/duplicate annotation IDs, duplicate declaration IDs,
malformed `xml:lang`, and malformed `source` URIs. Non-whitespace annotation text
already rejects. It correctly treats arbitrary appinfo/documentation payloads
as data, including nested XSD names.

Root cause: `validateSchemaGrammar()` checks direct notation shape and facet
ordering, but lacks annotation attribute/content and document ID assessment;
`XsdFacetGrammarHelper` deliberately skips annotation payloads. Annotation fields
are then discarded during component construction, so later checks cannot recover
the original ordered representation.

The same probes independently found native libxml2 rejecting foreign `lang` and
accepting malformed documentation `source`. P5-19e corrects those native checks.
The WSDL counterpart is implemented in P5-19f, with ordered grammar, ID scope,
saved-schema, native URI and SOAP contract tests. The separate regrouping defect
for mixed empty/nonempty documentation is also fixed. Complex types no longer
pass empty, attributed or repeated documentation directly to trim(); ordered
plain-text extraction accepts these valid forms. See
[implemented design](../../design/wsdl-schema-annotations.md).

Original probe inputs and independent diagnostics:
`/tmp/wsdl-p5-19e-schema-annotations/models.json` and `xerces.json`.
The scratch native/WSDL output was overwritten during the next prototype run;
`/tmp/wsdl-p5-19f-wsdl-annotations/baseline/native-wsdl.jsonl` reproducibly records
WSDL `9ed2230` against the now-corrected native validator, with the original input
bytes. It distinguishes the still-broken WSDL grammar from the accepted native fix.
Requirements: [XSD 1.0 annotations](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cAnnotations)
and [validation-root ID uniqueness](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-id).
