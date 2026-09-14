# Approved nil identity interpretation

Copyright (C) 2026 Qore Technologies, s.r.o.

On 2026-09-14 the user approved the proposal, then explicitly directed:
“count it as missing”. The interpretation question is resolved.

A nil element contributes no identity value. A unique/keyref tuple containing
such a field does not participate in uniqueness or reference comparison. The
node still counts for field cardinality: selecting two nodes remains invalid,
even if either is nil. Empty strings remain values. Fields must still have a
simple type or complex type with simple content; nil does not excuse an invalid
field type or invalid element content. The XSD 1.0 prohibition on key fields
assessed by nillable element declarations is retained.

This applies the nil-as-missing resolution from
[WG issue2219](https://www.w3.org/Bugs/Public/show_bug.cgi?id=2219#c1), explicitly
reflected in [XSD1.1 Structures3.11.4](https://www.w3.org/TR/xmlschema11-1/#cvc-identity-constraint).
The project still targets XSD1.0; this specific interpretation was approved,
without importing other XSD1.1 changes such as skipped-subtree semantics. It
does not remove or rewrite XML nodes, change value carriers or relax cardinality.

## Correction to the preliminary historical evidence

The archived W3C `msData/identityConstraint/idF018.xsd` omits the `uid` type,
so the second nil element has `anyType`, which is not an admissible field type.
The original fixture therefore remains invalid under this interpretation.
Its historical invalid expectation is not evidence of a duplicate-nil rule.
The preliminary proposal overstated what that fixture established.

The schema quoted in WG2219 explicitly uses `anySimpleType`. Our separately
identified derivative adds only `type="xsd:anySimpleType"` to the original uid
declaration, matching that issue's example; the instance bytes remain unchanged.
The derivative is valid. Original schema and instance bytes, including line
endings, are retained in the matrix and compared against the pinned W3C sources.
Both original and derivative remain executable tests.

## Independent implementation differences

The148-case matrix contains96 valid and52 invalid instances. Pinned Xerces2.12.2
agrees on119 cases. Its27 nil-keyref rejections are retained as explicit
`nil-keyref-stored-as-null` differences. `Field.Matcher.matched()` passes the
null actual value to `ValueStoreBase.addValue()`, which increments its field
count and stores the null tuple entry. Keyref lookup later searches for that
entry and reports a missing `null` or `A,null` key. This differs from the
approved exclusion of tuples with missing values. Unique comparison happens to
skip null comparisons, so its matching results do not establish a consistent
missing-value implementation.

Two additional cases expose a separate Xerces XPath union defect: field
`. | .` selects one node, whether nil or non-nil. `XPathMatcher.endElement()`
clears the first branch's matched flag before processing the next branch, so
its duplicate-branch guard fails and it reports the same node twice. Those
cases are explicitly classified as `union-counts-same-node-twice`, with both
nil and non-nil regressions. Native node-set matching correctly counts one.

Source evidence is from the already pinned Xerces2.12.2 source archive,
SHA256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
The exact archive hash is verified in the validation inventory; implementation
files and diagnostics are retained in `/tmp/wsdl-p5-20e-nil-identities/`.
Expected module behavior and observed oracle behavior occupy separate fields;
no original fixture, failed module result or oracle disagreement is hidden.
