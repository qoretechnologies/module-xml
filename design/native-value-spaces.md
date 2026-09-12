# Native XSD 1.0 fixed values and time comparison

Copyright (C) 2026 Qore Technologies, s.r.o.

Native validation compares a present simple-content element's fixed constraint
in its value space. Equivalent XML spellings remain unchanged in the returned
XML representation. For example, an element fixed to `+0017` accepts `17`, and
an element fixed to QName `p:Part` accepts `q:Part` when both prefixes identify
the same namespace. It rejects an unequal value even when that value is otherwise
valid for the declared type. An empty list equals another empty list and differs
from any nonempty list. A selected `xsi:type` retains its own primitive value
identity: string `1` differs from boolean `true`, while integer `17` equals
decimal `17.0`. libxml2's string-valued `anySimpleType` constraints compare with
selected string types without converting either value or changing its declaration.
XSD 1.0 leaves the `anySimpleType` lexical-to-value mapping unspecified; this
comparison follows libxml2's existing string mapping consistently.

The shared libxml2 element validator now computes the instance value whenever a
fixed declaration needs it. The existing typed equality routine compares this
value with the declaration's computed constraint. Negative comparison results
propagate through internal-error cleanup before any inequality is reported.
This applies to simple types and complex types with simple content. Mixed-content
character comparison retains its separate string semantics.

`xs:time` has no date. When both operands have the same timezone presence, the
comparator normalizes clock minutes modulo 1,440 and compares fractional seconds
separately. It does not add a calendar date to a nonzero-offset operand. Thus
`12:00:00Z` equals `14:00:00+02:00`, and `24:00:00` equals `00:00:00`.
The existing partial-order path handles comparisons between zoned and unzoned
values. This correction introduces no rounding heuristic or numeric conversion.

XSD 1.0's `unsignedLong`, `unsignedInt`, `unsignedShort` and `unsignedByte` have
unsigned decimal lexical forms. Their parser rejects a leading `+` or `-` before
applying numeric range or schema constraints. The distinct `nonNegativeInteger`
type still permits signed zero. Whitespace normalization and leading zeroes
remain supported.

## Ownership and failures

Computed values belong to the active validation context and follow its existing
cleanup and identity-constraint transfer paths. The schema's constraint is never
modified. No shared cache or mutable production state is introduced. Clock
comparison and the unsigned lexical guard take constant time and allocate nothing.

The arbitrary-precision integer parser already distinguishes allocation failure
from invalid lexical input. Its caller now preserves that distinction: allocation
failure returns the native internal-error result after cleanup; invalid input
returns the ordinary datatype violation. Failed list-token copies enter internal-error
cleanup before token validation; a NULL token must never be interpreted as an empty
lexical value. Failed string-value copies release their unpublished value before
returning an internal error. URI parsing uses the error-reporting parser API to
distinguish allocation failure from an invalid URI. The standalone allocation test installs
tracked allocator hooks before initialization, refuses each allocation permanently
in turn, and checks cleanup and successful reuse with and without computed values.
Allocator hooks are confined to test/probe executables, never installed by xml.

## Dependency selection and tests

CMake measures fixed-value, clock, unsigned lexical and allocation-error behavior
through the installed library's public APIs. `AUTO` selects the private pinned
library when a behavior fails; `SYSTEM` rejects it; a correctly backported library
remains usable. Build-tree transformations verify both input and output hashes
and leave downloaded source files unchanged. Reconfiguration preserves generated
source timestamps. Static private dependency symbols and install isolation follow
the existing dependency contract.

`test/xml-value-space.qtest` exercises positive, negative, precision, empty-list,
timezone and unsigned-declaration cases through DOM, XmlReader and XmlDoc.
`test/wsdl-interop/test_native_value_spaces.py` supplies an independent fixed-value
and time matrix with original XML preservation and error-category assertions.
The matrix records exact Xerces 2.12.2 midnight disagreements in
`xerces-time-midnight.json`, including its source root cause; those do not waive
any native requirement. The provider-selection suite covers detection, a genuine
backport, missing/offline/cross providers, source integrity and installation.

For a recurring shipment cutoff expressed in local time:

```qore
string xsd = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='cutoff' type='xs:time' fixed='12:00:00Z'/></xs:schema>";
hash<auto> payload = parse_xml_with_schema("<cutoff>14:00:00+02:00</cutoff>", xsd);
@assert(payload.cutoff == "14:00:00+02:00");
```

The normative requirements are XSD 1.0 Part 1
[cvc-elt 5.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt),
Part 2 [time](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#time)
and [unsignedLong](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#unsignedLong)
(and its three unsigned restrictions). No public API or schema data representation
changes are required by these corrections.
