# Exact native occurrence ranges

Copyright (C) 2026 Qore Technologies, s.r.o.

The private libxml2 provider preserves the exact values of XSD 1.0 occurrence
attributes during schema construction and DOM/reader validation.
[Particle properties](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Particle_details)
use nonnegative integers for minima and finite maxima, with `unbounded` as a
separate maximum value. The
[nonNegativeInteger value space](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#nonNegativeInteger)
has no machine-integer ceiling. Numeric comparison is exact; rounding would
change the accepted language.

The lexical scanner validates every character and retains a small control value
for the existing parser branches. Original attributes remain authoritative for
large bounds. A borrowed, normalized decimal view compares minima and maxima
before zero-count components are removed, so an invalid range inside an absent
parent still raises a schema error. Constraints that restrict `all` particles to
zero or one remain enforced. A private `maxFinite` flag distinguishes a numeric
maximum from libxml2's `1 << 30` unbounded sentinel. Synthetic inherited particles
use the original count source retained by the attribution checker.

The schema compiler attaches exact bounds to counted automaton transitions.
It subtracts the first occurrence already represented by a token transition and
uses an effective minimum of zero for nullable terms, after checking the source
range. Small finite adjusted bounds use the existing integer fields. Other bounds
use immutable base-1e9 limb arrays owned by the automaton and transferred to the
compiled regular expression. Failure frees every attached descriptor.

Each executor owns its counter values, progress marks and diagnostic snapshots.
Finite counters retain their exact value and check their maximum before every
increment. For an unbounded maximum, all counts at or above the minimum admit the
same future input; execution therefore saturates exactly at the minimum. This
avoids overflow on arbitrarily long streams. Separate counter offsets prevent
aliasing, resets affect only the selected counter, and rollback restores both
exact values and nullable-progress marks. Diagnostic snapshots retain their own
values when execution rolls back or resets.

Storage and comparison cost grow with the number of decimal digits in the bounds,
not their numeric value. Allocation sizes and sums are checked. Compilation does
not expand occurrence counts, and nullable execution does not enumerate empty
iterations. Generic character regular expressions and Relax NG automata retain
the existing integer representation. These private fields and helper functions
do not change the public libxml2 ABI.

For example, a batch schema may declare a large finite capacity while accepting
a small batch:

```qore
%modern
%requires xml
string xsd = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='batch'><xs:complexType><xs:sequence>"
    "<xs:element name='item' type='xs:string' maxOccurs='18446744073709551616'/>"
    "</xs:sequence></xs:complexType></xs:element></xs:schema>";
@assert(parse_xml_with_schema("<batch><item>invoice</item><item>receipt</item></batch>", xsd).batch.item
    == ("invoice", "receipt"));
```

The [range suite](../test/xml-particle-ranges.qtest) checks exact schema admission,
whole-group execution, nullable and inherited bounds, substitution members,
wildcards, invalid ranges and typed values in DOM and streaming readers. Native
fixtures seed counters near large boundaries to test actual execution without
constructing impossibly large documents. Python integer comparisons, allocation
faults and Valgrind cover arithmetic, ownership and recovery. CMake tests range
behavior before selecting a system backport; its fallback uses checked copies
of the pinned dependency sources. The
[attribution design](xml-particle-attribution.md) describes the accompanying exact
schema-component analysis.
