# Native schema particle positions

Copyright (C) 2026 Qore Technologies, s.r.o.

The private libxml2 provider preserves a schema particle's position when lowering
its content model to automaton transitions. Two local declarations, two global
element references, or two uses of a shared named group have distinct positions.
The same position can emit multiple transitions for repetition, wildcard namespace
alternatives or substitution members. Callback data still identifies the selected
element declaration or wildcard and retains its existing validation semantics.

The compiler assigns a numeric identity to the pair `(parent use, particle address)`.
A context-owned hash map reuses that identity when libxml2 emits the same counted
source position again. Entering and leaving a component saves/restores the current
parent without allocating a traversal stack. All-group members use the same bridge
because their transitions are built directly by the all compositor. Atoms retain
the numeric identity, including atom copies. Equality requires both the existing
atom equality and equal positions, so transition coalescing cannot erase competing
uses. Generic regex and Relax NG callers leave the position zero and retain their
existing equality behavior.

The map exists only during compilation, uses expected constant-time lookups and
linear storage in emitted component uses, and is freed on success or failure.
Allocation failures preserve the current parent and report a parser error.
No public libxml2 headers, callback payloads or installed symbols are added.
CMake verifies input and output source hashes, compiles build-tree copies, and
probes local/global references, shared groups, all members, wildcards and repeated
emission before selecting a system backport. Downloaded sources remain unchanged.

For example, this valid shared-group sequence retains both element values:

```qore
%requires xml
string xsd = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:group name='Pair'><xs:sequence><xs:element name='a' type='xs:int'/></xs:sequence></xs:group>"
    "<xs:element name='r'><xs:complexType><xs:sequence><xs:group ref='Pair'/>"
    "<xs:group ref='Pair'/></xs:sequence></xs:complexType></xs:element></xs:schema>";
@assert(parse_xml_with_schema("<r><a>7</a><a>11</a></r>", xsd).r.a == ("7", "11"));
```

Replacing the containing sequence with a choice makes the two uses ambiguous and
raises `XSD-SYNTAX-ERROR` during schema construction. The
[native tests](../test/xml-particle-identity.qtest) check DOM and streaming paths,
substitution collisions, typed-content rejection, repeated compilation, interruption
and subsequent reuse. The allocation fixture checks every allocation fault point
in the identity map, including growth and reuse without new allocations.

The [component attribution checker](xml-particle-attribution.md) uses these
positions with exact count-context analysis before automaton reduction.
The normative rule is [XSD 1.0 unique particle attribution](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-nonambig).
