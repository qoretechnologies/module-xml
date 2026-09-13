# WSDL canonical numeric constraint declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL schema construction checks integer, decimal and boolean default/fixed values
in both their source and canonical spellings. It follows the native compiler's
[declaration rules](native-numeric-defaults.md). Element constraints use their
simple content type; attribute declarations and constraints on attribute
references use the resolved attribute type. Validation occurs after type
finalization, so forward references and inherited facets are available.

Canonical text comes from the actual chosen atomic/list/union members. Existing
exact decimal identity strings provide every digit; integer spellings omit the
fraction and decimal spellings require it. Boolean text is `true` or `false`.
Other atomic members keep their lexical context. Lists assemble selected item
spellings in order, including empty and singleton lists. A string-first union
does not acquire numeric semantics merely because another member is numeric.

The temporary `XsdUnionValueIdentity.constraint_lexical` field is populated only
inside a declaration's `XsdConstraintLexicalScope`. The scope restores its
thread-local predecessor on success, exception and cancellation. The field is
excluded from value equality. Ordinary value conversion does not compute these
canonical spellings; unrelated documents do not share capture state.

Canonical assessment can select a different union member. For example, consider
a union of a boolean restriction with pattern `1`, followed by string, with
`fixed="1"`. Its original value selects boolean, while canonical text `true`
selects string. The declaration is valid, but its stored constraint still comes
from the first assessment. Explicit instance text `true` therefore fails that
fixed constraint. The declaration retains its original spelling and selected
identity through reconstruction and repeated resolution.

Neither an attribute nor an element publishes a new constraint value until both
assessments succeed. The second conversion's value is discarded. This keeps
default metadata, fixed comparisons and QName declaration bindings independent
of the canonical validation trial. Namespace context remains active throughout
both assessments and is restored afterward.

`test/wsdl-numeric-constraints.qtest` covers the 396-schema independent matrix,
saved schemas/providers, changed union selection and failure during the second
assessment. The HTTP suite checks both actual SOAP bindings, client/server
directions, omitted attributes and invalid fixed values. The Python matrix
validates output payloads with pinned Xerces and compares numeric values and
expanded QName identities independently.

These declaration checks are separate from empty-element default projection.
They do not resolve instance PSVI interpretation under E1-56, add float/calendar/
binary canonicalization, or change the default `preserve_types=False` policy.
