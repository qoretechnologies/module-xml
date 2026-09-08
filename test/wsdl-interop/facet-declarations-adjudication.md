# Numeric facet declaration adjudication

Copyright (C) 2026 Qore Technologies, s.r.o.

`test_facet_declarations.py` defines authored schema cases for XSD 1.0 Second
Edition, separately from the unchanged W3C corpus. Each case is compiled as an
atomic and a simple-content restriction. Qore parses actual SOAP 1.1 and 1.2
contracts, and successful cases with nonempty value spaces process both request
and response payloads. Exact Python Decimal values and expanded XML names are
mandatory independently of schema-compiler acceptance.

The normative baseline is [XSD 1.0 Part 2](https://www.w3.org/TR/xmlschema-2/),
with the [Second Edition errata](https://www.w3.org/2004/03/xmlschema-errata.html).
The errata contain no Part 2 correction changing these rules. Xerces-J 2.12.2 is
checksum-pinned in `oracle/manifest.json`; the observed lxml libxml2 is 2.12.10.
The test's `ORACLE_DEFECTS` sets identify every permitted disagreement by name.
They never change expected Qore schema validity. Unexpected disagreements fail,
and the pinned versions must reproduce the complete observed sets.

| Cases | Normative result and basis | Observed compiler disagreement |
| --- | --- | --- |
| `bounds-minExclusive-minExclusive-1`, `bounds-maxExclusive-maxExclusive-1` | Valid: sections 4.3.8–9 explicitly permit repetition of the base's same exclusive endpoint. | libxml2 rejects the endpoint as an instance value. Xerces accepts. |
| `exclusive-enum`, `exclusive-digits`, `exclusive-pattern-valid` | Valid: the repeated endpoint need not belong to the base value space, but its spelling must map through the base lexical space. | libxml2 rejects the repeated endpoint. Xerces accepts. `exclusive-pattern-invalid` separately checks an invalid base lexical spelling; both reject. |
| `bounds-minInclusive-maxExclusive-1`, `bounds-maxInclusive-minExclusive-1`, `builtin-upper-empty`, `builtin-lower-empty` | Invalid: section 4.1.2.1 merges inherited facets; 4.3.9.4 and 4.3.10.4 require strict ordering of opposite mixed inclusive/exclusive endpoints. Builtin byte endpoints participate in that inheritance. | Xerces accepts all four. libxml2 accepts all except the inherited minimum-inclusive/maximum-exclusive case. These schema acceptance results do not override the explicit component constraints. |
| `integer-fraction` | Invalid: integer fixes fractionDigits to zero (3.3.13). | libxml2 accepts one; Xerces rejects. |
| `duplicate-bound` | Invalid: Single Facet Value (4.1.3); only pattern/enumeration permit repetition. | libxml2 accepts duplicate bounds; Xerces rejects. |
| `whitespace-weakened` | Invalid: numeric types fix whiteSpace to collapse (4.3.6). | libxml2 accepts replace; Xerces rejects. |
| `whitespace-token` | Valid: the facet value has NMTOKEN type and its whitespace is collapsed (4.3.6.2 and Appendix A). | libxml2 compares the unnormalized token and rejects; Xerces accepts. |
| `inherited-digits` | Invalid: inherited fractionDigits=4 remains a facet under 4.1.2.1 when totalDigits=2 is introduced; 4.3.12.4 requires fractionDigits <= totalDigits. | Xerces accepts; libxml2 rejects. |
| `large-count-2147483648`, `large-count-9223372036854775808`, `large-count-narrowed` | Valid: totalDigits is positiveInteger and fractionDigits is nonNegativeInteger (4.3.11–12), without a signed machine-width limit. | Xerces rejects counts above its signed 32-bit counter range. libxml2 accepts; Qore retains exact string metadata. The inverse `large-count-widened` restriction is invalid and both reject. |
| `unknown-attribute`, `schema-attribute`, `invalid-fixed`, `pattern-fixed` | Invalid: Appendix A and facet XML representation summaries constrain unqualified attributes, allow only non-schema namespaced extension attributes, require boolean fixed values, and prohibit fixed on pattern. | libxml2's compiler does not enforce these representation constraints; Xerces rejects. |

`equal-exclusive-empty` is valid under 4.3.8.4 even though its value space is
empty. `own-enum-digits-empty` is also a valid declaration with an empty
intersection. Both compilers agree; there is no fabricated valid instance for
either case. `different-fixed-kind` is valid because a fixed facet prevents a
different value for that same facet; it does not prohibit adding a different
facet that further narrows the value space. Both compilers agree.

For valid schemas rejected by Xerces's count limit, document validation is
explicitly reported unreachable. libxml2 instance validation, exact Decimal
comparisons, Qore count metadata, provider reconstruction and sample tests retain
the applicable coverage. Rejected repeated-endpoint schemas similarly retain
Xerces document validation. No fixture bytes or schema bounds are rewritten to
make an oracle accept them.
