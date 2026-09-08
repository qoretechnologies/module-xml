# Union provider validation and reference evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 uses the first matching union member in declaration order unless an
explicit dynamic type selects a member. Integer and decimal share a value space;
boolean and decimal do not. See the W3C requirements for
[unions](https://www.w3.org/TR/xmlschema-2/#union-datatypes) and
[equality](https://www.w3.org/TR/xmlschema-2/#equal).

The provider preflight showed that `UnionDataType.getValueType()` advertised
`AutoType`. An enclosing `ListDataType` therefore accepted arbitrary union items
without calling member validators. Inherited requiredness also advertised an
optional value without accepting omission. Broad exception catches hid cancellation
and unexpected errors. The implementation corrects these provider contracts and
preserves declaration order, metadata reconstruction and member restrictions.

The final corpus review caught two date/string union families that had depended
on swallowing raw `INVALID-DATE` exceptions. Builtin date conversions now translate
only date input rejection to the directional SOAP error; binary decoders similarly
translate `BASE64-PARSE-ERROR` and `PARSE-HEX-ERROR` to SOAP input rejection. Native
conversion diagnostics are retained, and cancellation/unexpected errors still
propagate. Focused tests cover original/reconstructed schemas, date/time rejection,
binary rejection and successful later string alternatives.

Audit reproductions exposed exponential repeated trials and metadata traversal
when two members referenced the same nested union. Per-call typed caches now
evaluate shared union nodes once for each operation/input. Cyclic metadata fails
explicitly. A 28-level shared graph checks terminal invocation counts, including
failed NaN trials in scalars/lists/hashes and metadata cleanup after cancellation.
Reentrant signed-zero, different-precision number and different-timezone date
inputs get independent contexts. No persistent
cache or timing-dependent test is used.

The independent matrix has six cases: boolean-first, integer-first, restricted
integer/boolean members, exact decimal/boolean, integer-list/boolean, and restricted
text/integer. Each runs as an atomic element, simple content with a required union
attribute, and repeated elements. Both actual SOAP bindings and both directions
are covered, with reconstructed contracts and detached element/message providers.
Primitive value identity, exact Decimal values, item order, repeated occurrence
counts, payload expanded names and envelope versions are checked separately from
schema validity.

The matrix checks 468 input documents, 288 emitted binding documents, 2784 consumer
rows and 1824 consumer/provider/example documents: 2580 independently validated
documents in total. The focused Qore suite also exercises malformed metadata,
legacy reconstruction, optional variants and directional schema error propagation.

## Existing libxml2 decimal precision limitation

The exact decimal `12345678901234567890.123456789` exceeds libxml2 2.12.10's
24-significant-digit decimal buffer. This is the same primitive limitation already
adjudicated in P1 and P3-04, now reached through a union member. The relevant
[libxml2 implementation](https://github.com/GNOME/libxml2/blob/v2.12.10/xmlschemastypes.c#L2360)
stops collecting significant digits at 24 and subsequently rejects remaining input.

Pinned Xerces 2.12.2 validates every document and rejects every invalid document,
without warnings. Libxml2 2.12.10 disagrees only for 24 binding documents and 64
consumer documents carrying that exact decimal. The test permits only that named
case, exact payload text and union datatype validation diagnostic; all other
libxml2 verdicts must agree. A newer validator may accept all cases. No Qore result,
precision assertion or primitive-family assertion is waived, and no upstream
fixture is edited.

## Remaining P3 union criteria

The independent preflight `/tmp/wsdl-p3-10-preflight.py` records separate schema
union defects that remain required implementation work. Integer/decimal enumeration
`01` incorrectly rejects equivalent `1` and `1.0`; boolean/integer enumeration `1`
incorrectly accepts decimal-family `01`. Union pattern `0` discards its accepted
lexical form, union whitespace is not always collapsed, and forbidden ordered
facets are accepted. The reproduction records 24 mismatched input verdicts,
eight invalid emitted documents and two accepted invalid SOAP contracts. Xerces
verifies the intended verdicts. These cases will become permanent regressions in
the next union increment; this provider increment does not claim full P3 acceptance.

The added date consumer investigation also reproduced existing P3 date defects.
`QoreDateDataTypeBase.acceptsValue()` delegates to `TimeZone::date(value, format)`.
Both the omitted-format call and the explicit single-string call turn malformed
text into an epoch date. The single-string `TimeZone::date()` overload constructs
`DateTimeNode` without an exception sink, suppressing invalid-date errors.
Valid date strings parse correctly in both calls, ruling out the initial suspicion
of numeric overload selection. Separately, prefixing a malformed time
with `1970-01-01T` can cause `date()` to accept an absent/invalid time as midnight.
`/tmp/wsdl-p3-10-date-preflight.qr` records both before the required P3 date work.
These are scalar parser/provider root causes, independent of union traversal.
Strict date lexical/value semantics and their core fixes remain mandatory; the
six-case independent provider matrix makes no date-provider conformance claim.
