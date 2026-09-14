# Native identity-constraint XPath grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

Native XSD validation requires a nonempty path on each side of a selector or
field union separator. For example, `row|other` is valid and `row|` is invalid.
Selectors cannot select attributes; fields can end in an attribute step such
as `row/@id`. Namespace prefixes must resolve in the declaration context.
The grammar permits XML whitespace around tokens and equivalent explicit
`child::` and `attribute::` axes.

The private libxml2 pattern compiler rejects empty input and a terminal union
separator. The separator check precedes temporary allocation, so it cannot
overwrite an allocation failure with a syntax error. It uses the existing error
path to free parser state and previously compiled alternatives and clear the
output pointer. No extra traversal, allocation, shared state or public ABI is
introduced. Empty input returns syntax status rather than success with no result.

CMake tests selector and field behavior before selecting a system library.
AUTO chooses the pinned private dependency when the probe fails; SYSTEM reports
the failure. The private correction verifies input and output SHA-256 values,
writes only the build tree and preserves timestamps on unchanged reconfiguration.

`test/xml-identity-paths.qtest` checks the reader, schema-aware parser and DOM
validator against `test/wsdl-interop/fixtures/identity-paths.json`. The direct
C test covers every pattern mode with and without a dictionary, invalid input,
union cleanup and subsequent successful compilation. Provider tests verify
behavioral selection and idempotence against a real shared library retaining
only the original pattern compiler defect.

Normative source: [XSD 1.0 Part 1 §3.11.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#coss-identity-constraint).
