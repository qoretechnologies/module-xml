# P4 particle construction and occurrence evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 Part 1 sections 3.8 and 3.9 define ordered model groups and whole-particle
occurrence constraints. Section 3.3.2 states that an element declaration with
both occurrence attributes zero contributes no component to its parent content
model. Part 2 section 3.3.20.1 permits a single optional plus sign for
nonNegativeInteger, and a minus sign only for zero; section 4.3.6 defines XML
whitespace collapse. The XSD schema for schemas applies integer value constraints
to all-group counts, including the value-equivalent signed spellings.

- [XSD 1.0 Part 1, Second Edition](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/)
- [XSD 1.0 nonNegativeInteger](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#nonNegativeInteger)
- [XSD 1.0 whitespace](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#rf-whiteSpace)

`test_particle_counts.py` generates 26 valid original schemas and 26 separately
named canonical lexical derivatives. Each has six documents: zero through four
element occurrences plus an unknown child. The independent validators assess all
52 schemas and 312 documents. Another 128 original invalid schemas cover four
particle kinds, both attributes and 16 invalid spellings, each with an empty
document. The native worker accounts for every result through two APIs: 880 rows,
with exact schema-versus-document exception categories and no extra or missing rows.

The local libxml2 fallback is 2.15.4. Independent lxml 6.1.1 uses libxml2 2.12.10;
Xerces-J is the pinned 2.12.2 JAR, SHA-256
`6fc991829af1708d15aea50c66f0beadcd2cfeb6968e0b2f55c1b0909883fe16`.
The JAR fingerprint is verified by the independent harness. Four disagreements
have separate assertions:

| Validator | Root cause | Required result and evidence |
| --- | --- | --- |
| libxml2 | Digit-only min/max scanners and an unbounded comparison before whitespace collapse | Accept valid signed/whitespace originals. Their separately identified canonical derivatives also run; originals are never replaced. |
| libxml2 | Local zero-count declaration reaches the content-model compiler and creates a consuming transition | Reject positive occurrences of the zero-count local element. Both fixed native APIs and Xerces reject; the empty document remains valid. |
| Xerces-J | XSAttributeChecker removes a leading plus before Integer.parseInt, which accepts the following minus | Reject `+-0`. The eight min/max schemas are invalid; the exact Xerces false acceptances remain visible and Qore must reject with XSD-SYNTAX-ERROR. |
| Xerces-J | XSAttributeChecker compares all-group count enumerations to literal strings 0 and 1 | Accept the two valid original all schemas with signed counts. Xerces reports cvc-enumeration-valid, making 12 document stages unreachable there; the native APIs assert the normative results on those original documents. Canonical derivatives compile independently. |

The checked fallback patch corrects the two libxml2 causes. It does not patch the
independent validators. Their discrepancies require the named schema, diagnostic
and document outcomes; an unexpected disagreement fails the test. Empty documents
under invalid schemas are recorded as unreachable, except the explicitly recorded
Xerces false acceptances. Original corpus files and historical findings are untouched.

`test_particle_model.py` separately checks ten valid schema families (including a
named lexical derivative), six invalid schemas, 32 actual SOAP binding contracts,
and original/reconstructed schemas. Its 80 model rows retain declaration order,
exact counts, element identity and shared group definitions; 12 construction
errors have their expected categories. These are construction assertions on actual
bound parts, not claims of completed ordered message conversion.

Native tests cover 597 assertions through streaming and hash conversion. The model
suite covers 1,854 assertions, including 1,000 sibling positions, 80 nested groups,
81-digit compositor counts, chameleon imports, reconstructed detached types,
malformed Serializable state and interruption/recovery. Native schema ownership
is checked with Valgrind, including the zero-count declaration arena and repeated
validation contexts. Full final run counts and hashes are recorded in
[the execution record](EXECUTION.md) and the P4-01 audit.

The remaining P4 criteria include runtime ordered matching/serialization, complete
group counts, ambiguity detection, field requiredness and sample generation. The
76 existing P4 corpus failure records remain failures until those criteria pass.
