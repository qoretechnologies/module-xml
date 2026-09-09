# XSD 1.0 union composition

Copyright (C) 2026 Qore Technologies, s.r.o.

An explicit union member contributes its member definitions in order. Restrictions
on that union do not become restrictions on the composed union. This follows
[XSD 1.0 Part 2 section 4.1.2.3](https://www.w3.org/TR/xmlschema-2/#derivation-by-union).
The named restricted union continues to enforce its own facets when used directly
or as a list item. Atomic and list members also retain their restrictions.

For example, `Restricted` below accepts the spelling `01`. `Outer` accepts `2` as
an integer and `true` as a boolean because its effective members are `xs:int` and
`xs:boolean`:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="Base">
    <xs:union memberTypes="xs:int xs:boolean"/>
  </xs:simpleType>
  <xs:simpleType name="Restricted">
    <xs:restriction base="Base">
      <xs:pattern value="0[0-9]+"/>
      <xs:enumeration value="01"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="Outer">
    <xs:union memberTypes="Restricted"/>
  </xs:simpleType>
</xs:schema>
```

Schema resolution first resolves and validates each complete explicit dependency,
including restrictions that composition will subsequently remove. Its temporary
`union_definitions` map identifies the original union definition behind each
resolved union restriction. A composed member references that definition. Atomic
and list members keep their original objects. Inline and named members follow
the same rule. Direct uses of the restricted type are unchanged.

The implementation retains shared union nodes instead of copying a potentially
exponential sequence of leaf members. Existing ordered traversal and per-call
caches provide the same member selection on this compact graph. A chain with
two references to the previous union at each level therefore grows with the
declared graph, rather than the number of paths through it. Both schema and
provider reconstruction preserve those references. The temporary resolution map
is cleared on success or failure along with the existing dependency state.

`test/wsdl-union-composition.qtest` covers exact primitive selection, retained
restrictions, reconstruction, a shared 32-level graph, invalid dependencies and
recovery. `test/wsdl-interop/test_union_composition.py` checks named/inline members,
outer and list restrictions against Xerces and independent libxml2, then exercises
both SOAP bindings, request/response processing and detached provider consumers.
