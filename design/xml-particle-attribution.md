# Native counted particle attribution

Copyright (C) 2026 Qore Technologies, s.r.o.

The private libxml2 provider checks schema component attribution before reducing
content models to automata. Each present model group must satisfy
[XSD 1.0 unique particle attribution](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-nonambig),
including unused named groups and groups inside an empty surrounding language.
A zero-count particle contributes no component. Matching names are expanded names;
wildcards compare their namespace constraints. Abstract declarations contribute
no directly matching name, while usable substitution members retain the position
of the referring particle.

An iterative postorder walk caches intrinsic summaries by resolved component
identity. Each summary retains emptiness, nullability, FIRST predicates, sparse
FOLLOW thresholds, a flexibility ratio, and unconditional/continuing-context
ambiguity thresholds. A repeated use scales thresholds by its count; a required
following component can end an inherited counting context. The calculation follows
the weak-determinism/FOLLOW analysis of
[Chen and Lu](https://lcs.ios.ac.cn/~chm/papers/dlt2012.pdf) and the intrinsic
threshold construction in [Groz et al., section 3.4](https://www.pure.ed.ac.uk/ws/portalfiles/portal/32885322/jcss2017_3.pdf).
It checks source positions, so different iteration boundaries at one position do
not by themselves make a model ambiguous.

All threshold calculations use nonnegative integer limbs and exact rational
comparisons. They do not use floating point, rounding, or expansion of occurrence
counts. QName predicates use hash lookups; wildcard entries have a separate list
so a wildcard does not force every pair of ordinary names to be compared.
Summaries published to the component cache are immutable; combining parents own
their mutable sets. Arithmetic and graph storage belong to one compiler context.
Temporary cross-products are freed immediately, and all remaining allocations are
released on success or error. Source attributes distinguish finite values from
the native unbounded sentinel. Synthetic extension particles retain a borrowed
pointer to their original count source.

The automaton retains [particle-use identities](xml-particle-identity.md) and its
computed execution flags. Schema acceptance uses the component analysis instead
of the older counter-insensitive determinism test. Abstract-only transitions lead
to disconnected states; substitution transitions omit abstract declarations.
Thus the callback selects the same declaration whose name was admitted by the
attribution analysis.

Schema count increments remain explicit epsilon operations. Epsilon reduction
cannot overwrite an outer increment with an inner increment, and every increment
checks its upper bound. A nullable term has an effective execution minimum of
zero, without changing its source occurrence fields. Per-counter progress marks
prevent a second empty iteration without intervening input. The marks survive
counter resets, clear when an input token is consumed, and are saved/restored with
rollback counts. This avoids enumerating a large number of empty iterations.
The existing native execution/state allocation limits remain active.
These counter changes apply to schema automata; generic regular-expression and
Relax NG automata retain their existing counter behavior. An all group with a
required member whose language is empty also has an empty language; optional
members and an optional whole group retain their separate occurrence semantics.

For example, a fixed boundary permits the following two declarations of `item`:

```qore
%modern
%requires xml
string xsd = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='r'><xs:complexType><xs:sequence>"
    "<xs:element name='item' type='xs:string' minOccurs='2' maxOccurs='2' fixed='line'/>"
    "<xs:element name='item' type='xs:string' fixed='total'/>"
    "</xs:sequence></xs:complexType></xs:element></xs:schema>";
@assert(parse_xml_with_schema("<r><item>line</item><item>line</item><item>total</item></r>", xsd).r.item
    == ("line", "line", "total"));
```

Changing the first maximum to `3` makes the boundary ambiguous and raises
`XSD-SYNTAX-ERROR`. Invalid instance values still raise `PARSE-XML-EXCEPTION`.
The [native suite](../test/xml-particle-attribution.qtest) checks these distinctions,
nested bounds, abstract callbacks, empty components and large nullable repetition.
The finite-language oracle checks schema acceptance and DOM/reader documents;
separate allocation fixtures exhaust measured failures in arithmetic, compilation
and execution. CMake probes these behaviors before choosing a system backport and
otherwise compiles hash-checked copies of the pinned dependency sources.
