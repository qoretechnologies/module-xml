# WSDL canonical constraint declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL schema construction checks integer, decimal, boolean, binary, IEEE and complete calendar default/fixed values
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

Binary members use their already selected octets: hexadecimal text is uppercase,
and Base64 has no whitespace or line wrapping. Canonicalization never treats a
raw string as encoded input or changes a retained `XsdBinaryValue` carrier. A
binary-pattern/string union can select a different member for its canonical
trial, just as the boolean example below does; its stored fixed identity still
comes from the original binary conversion. Empty and large binary values retain
their complete octet sequence through saved providers and both SOAP bindings.

IEEE members pass their already selected round-trip identity text to
`canonical_xsd_float(lexical, double_precision=False)`. That API validates a
complete XML lexical string and reuses the native datatype/canonical APIs with
RAII ownership. It rejects embedded NULs before calling the terminated-string
API, converts encoding to UTF-8 and checks cooperative cancellation. Its native
formatter preserves locale and the caller's floating-point environment.

For example, `canonical_xsd_float("16777217")` returns `1.6777216E7`, the exact
binary32 result, while passing `True` returns binary64 text `1.6777217E7`.
Finite values use shortest round-trip scientific text; special values use
`INF`, `-INF` and `NaN`. XSD 1.0's single zero is `0.0E0`. This policy never
rounds a selected value for decimal appearance. See the
[native IEEE contract](native-ieee-constraints.md) for the precision policy.

The complete calendar families `dateTime`, `time` and `date` use WSDL's exact
calendar parser and renderer. Fractions remain decimal strings; timezone
normalization changes only integer minutes and calendar fields. dateTime/time
offsets become UTC, while an absent offset remains absent. Midnight carries
the date where applicable, and fractional trailing zeros disappear. Calendar
carries retain extended years and skip year zero without native integer limits.

Dates retain the recoverable timezone of their one-day interval. An offset above
`+12:00` moves the date back one day and subtracts 24 hours from the offset. An
offset at or below `-12:00` moves it forward one day and adds 24 hours. Thus
`2002-10-10+13:00` becomes `2002-10-09-11:00`, preserving the same interval.
Zero offsets render `Z`. XSD 1.0 does not specify canonical representations for
duration or the partial `g*` calendar families; these retain their lexical context.

For example, `2000-01-01T00:00:00.100+01:00` is assessed as
`1999-12-31T23:00:00.1Z` for canonical validity. The declaration still retains
its original lexical form and selected value. No native floating-point date
arithmetic or rounding heuristic participates in this transformation.

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

The corresponding `test/wsdl-binary-constraints.qtest` and HTTP suite exercise
binary declarations, canonical member reselection, cancellation and large
values. `test/wsdl-interop/test_wsdl_binary_constraints.py` compares decoded
octets independently across original/saved services and both SOAP bindings.

The IEEE unit/HTTP suites cover 300 declarations and preserved provider values.
`test_wsdl_ieee_constraints.py` compares exact IEEE values, selected string
values and expanded QName list members for 1,248 SOAP payloads. It retains all
48 pinned Xerces schema differences and their unreachable document results.
Separately identified derivatives remove only the default/fixed attribute to
check explicit instance validity with the original type restrictions. These
derivatives never replace the original declaration verdicts or fixture bytes.
`test_ieee_canonical.py` checks the public API against 1,314 exact rational
conversion/formatting expectations, including invalid and boundary inputs.

The calendar suites cover 306 declarations, 18 exact calendar boundaries,
saved schemas/providers and both SOAP HTTP directions. The independent matrix
compares ordinal days and rational seconds for 1,296 SOAP payloads. All 48
Xerces declaration disagreements and 30 fixed-value instance disagreements
remain explicit. Separately identified derivatives remove only the declaration
constraint to validate instances, while independent comparisons still require
the original value. Native calendar formatting and declaration enforcement
remain a separately recorded [P5 finding](../test/wsdl-interop/p5-native-calendar-constraints-finding.md).

These declaration checks are separate from empty-element default projection.
They do not resolve instance PSVI interpretation under E1-56 or change the
default `preserve_types=False` policy.
