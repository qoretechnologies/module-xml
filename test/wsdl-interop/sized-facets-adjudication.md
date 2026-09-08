# String and length facet adjudication

Copyright (C) 2026 Qore Technologies, s.r.o.

`test_sized_facets.py` requires Qore's declared schema/input verdicts and exact
output values independently of both validators. It checks atomic and simple-content
types through actual SOAP 1.1/1.2 request and response bindings. Named oracle
disagreements never change Qore's expected results. The pinned Xerces version is
2.12.2; the local lxml library uses libxml2 2.12.10.

The following schema disagreements follow
[XSD 1.0 length constraints](https://www.w3.org/TR/xmlschema-2/#rf-length),
[minLength constraints](https://www.w3.org/TR/xmlschema-2/#rf-minLength), and
[whitespace constraints](https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace):

- `base-min-repeat-own-length` is valid: its minimum repeats an ancestor without
  an exact length. Libxml2 rejects it.
- `base-length-own-min` lacks that ancestor and is invalid. Libxml2 accepts it.
- `contradictory-length` has minimum three and maximum two. Libxml2 accepts it.
- `weakened-whitespace` and `list-whitespace` illegally weaken inherited or fixed
  collapse behavior. Libxml2 accepts them.
- `builtin-list-zero-*` contradict the builtin NMTOKENS minimum of one item.
  Libxml2 accepts these schemas and also accepts the invalid whitespace-only
  `builtin-list-empty` document. See [NMTOKENS](https://www.w3.org/TR/xmlschema-2/#NMTOKENS).

Xerces rejects valid counters above signed 32-bit range and accepts Arabic-Indic
digits in `invalid-*-١`. Length counters have the nonNegativeInteger value space;
[integer lexical syntax](https://www.w3.org/TR/xmlschema-2/#integer) permits ASCII
digits and has no machine-word limit. Its
[attribute checker](https://github.com/apache/xerces2-j/blob/trunk/src/org/apache/xerces/impl/xs/traversers/XSAttributeChecker.java)
uses `Integer.parseInt` for these counters. The pinned JAR's `javap -p -c` output
confirms those calls at bytecode offsets 212 and 316 in `validate`.

Xerces also defaults to counting Java UTF-16 units for string length. Its
[TypeValidator](https://github.com/apache/xerces2-j/blob/trunk/src/org/apache/xerces/impl/dv/xs/TypeValidator.java)
provides `org.apache.xerces.impl.dv.xs.useCodePointCountForStringLength`. The worker
now sets this property before datatype initialization, selecting XSD's character
count. The supplementary-character and combining-character regressions check the
configured behavior; no Unicode-length verdict is waived.

Local reproduction logs: `/tmp/wsdl-p3-07-independent-builtin.log`,
`/tmp/wsdl-p3-07-independent-codepoints.log`,
`/tmp/wsdl-p3-07-xerces-count-bytecode.txt`, and
`/tmp/wsdl-p3-07-xerces-string-length-bytecode.txt`.

The string `pattern-final-newline` regression follows XSD's whole-lexical-value
matching rule. PCRE's `$` can match before a final newline; its absolute `\A` and
`\z` assertions enforce the required boundaries, as documented in
[PCRE2 pattern syntax](https://www.pcre.org/current/doc/html/pcre2pattern.html).
Both independent validators reject `A` followed by LF for the XSD pattern `A`.
Production pattern compilation and sample verification now use absolute anchors.
