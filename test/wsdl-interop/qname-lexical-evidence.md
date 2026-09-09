# QName lexical evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

Before P3-29, `XsdBaseType` treated QName as an ordinary string in serialization,
decoding and provider construction. The reduction in
`/tmp/wsdl-p3-29-name-preflight.qr` accepted empty text, `a:b:c`, `0name` and an
unbound prefix. The first three are lexical errors. Prefix binding is a separate
remaining context requirement. `WSMessageHelper` also lacked a QName sample
category, and the generic simple-type sample path could return text that failed
the base grammar or truncate it according to a deprecated length facet.

[XSD 1.0 Part 2 §3.2.18](https://www.w3.org/TR/xmlschema-2/#QName) defines the
QName grammar and namespace/local value space. Its normative namespace reference
is the [1999 recommendation](https://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-QName).
Both QName components use NCName productions. The character ranges therefore
come from the same pinned XML 1.0 Second Edition tables used by the existing
name datatype tests, rather than the newer element-name grammar in XML parsers.
[Length §4.3.1.3](https://www.w3.org/TR/xmlschema-2/#rf-length) treats QName length
constraints as always satisfied.

`test_qname_lexical.py` checks:

- 4,036 unprefixed and implicit-`xml` character-boundary inputs against the
  independent range table, libxml2 2.12.10 and Xerces-J 2.12.2. Qore serialization,
  decoding and reconstructed providers must match all expected verdicts and text.
- Seven schema declarations through both actual binding versions, including
  malformed enumeration spellings and equivalent aliases declared locally on
  parent and child enumeration facets. Lexical validation must not introduce
  string comparison of these aliases during schema construction.
- Seven value definitions across atomic, attributed simple-content and repeated
  models: 42 SOAP contracts and 612 input messages. All 216 accepted messages
  produce independently valid output with the checked namespace/local identity.
  Detached element/message providers, reconstruction and generated examples use
  the same matrix. There are no new oracle disagreements.

The Qore suites cover both QName components, non-XML whitespace, omitted versus
empty values, malformed metadata, inherited patterns, ignored length facets,
list item validation, union fallback, cancellation and subsequent recovery.
Local HTTP tests use queues and 30-second deadlines with deterministic teardown.
Original W3C fixtures and classifications remain unchanged.

The audit corrected an initial enum check that called the existing base value
comparison: that would reject namespace-equivalent aliases before their context
implementation is complete. The final construction check validates grammar only.
The initial sample helper also appended absent candidates to a narrowed typed
list; explicit candidate insertion and presence checks corrected that defect.
Both have executable regressions. An overlapping development test read a file
during a save; the final gate freezes source and test hashes before rerunning.

The standalone QName matrix, execution modes, compiled modules, disabled-PCRE2-JIT
character check, broad regressions and both-version reports are recorded in
[EXECUTION.md](EXECUTION.md). Scope remains the complete P1–P9 plan. This lexical
increment does not close QName context/enumeration or ENTITY/ENTITIES constraints.

The ENTITY reduction accepts `lt` or `logo` without an unparsed-entity declaration.
[XSD §3.3.11](https://www.w3.org/TR/xmlschema-2/#ENTITY) requires that declaration
in the particular instance's DTD. Both [SOAP 1.1 §3](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383494)
and [SOAP 1.2 §5](https://www.w3.org/TR/soap12-part1/#soapenv) prohibit DTDs.
The remaining implementation must distinguish document validation from detached
scalar/provider conversion; it must not enable prohibited SOAP constructs.
