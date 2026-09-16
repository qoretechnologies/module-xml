# Approved skipped-subtree identity interpretation

Copyright (C) 2026 Qore Technologies, s.r.o.

On 2026-09-14, after the skipped-subtree decision and recommendation were
explained, the user approved: “proceed as proposed”. This decision is resolved
and is separate from the earlier nil-as-missing approval.

For key, unique and keyref evaluation, an element matched by a wildcard with
`processContents="skip"`, together with its descendants and attributes, is
excluded from selector and field results. The original XML is preserved.
Declarations whose names happen to match elements inside the skipped subtree
do not make those elements participate in identity checking.

A declared row outside that subtree still participates. If its required key
field points only into the skipped subtree, the key fails because the field is
missing. Unique/keyref tuples with missing fields do not participate in value
comparison. Unions deduplicate the remaining actual nodes and retain the normal
single-field cardinality rule. Strict and lax element wildcards retain their
existing assessment rules. This decision does not exclude an attribute wildcard
on an otherwise assessed element.

This adopts the specific resolution of
[W3C issue 1937](https://www.w3.org/Bugs/Public/show_bug.cgi?id=1937), reflected in
[XSD 1.1 Structures §3.11.4](https://www.w3.org/TR/xmlschema11-1/structures.html#cvc-identity-constraint).
The project still targets XSD 1.0; no other XSD 1.1 changes are implied.
The previous nil interpretation's statement that skipped-subtree semantics were
not included describes the scope of that earlier approval, not a remaining
restriction after this decision.

The repository tuple matrix `test/wsdl-identity-tuples.qtest` checks this rule
for keys, unique constraints and keyrefs, including matching declarations,
unknown elements, nested skipped subtrees, outside declarations and path unions.
Scoped tuples are integrated in WSDL and acceptance is tracked as P5-20j; this
policy does not by itself close the remaining P5 acceptance criteria. Historical
prototype evidence remains in `/tmp/wsdl-p5-20f-identity-tuples/`.
