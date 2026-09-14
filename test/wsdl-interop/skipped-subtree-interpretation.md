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

Implementation is part of the ongoing P5-20f scoped-tuple work. Approval of the
interpretation does not mark that implementation or its acceptance gates complete.
The prototype and executable boundary evidence are retained under
`/tmp/wsdl-p5-20f-identity-tuples/` until the implementation is ready for its full
review and commit.
