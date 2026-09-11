# Native element declaration consistency

Copyright (C) 2026 Qore Technologies, s.r.o.

Native XSD construction enforces XSD 1.0
[Element Declarations Consistent](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-element-consistent)
after substitution membership and component resolution. This supplements the
separate counted unique-attribution check. A required sequence can be
unambiguous while still containing conflicting declarations of the same name.

For each complex type and named group, an iterative walk indexes explicit
child declarations and admitted concrete substitution members by expanded name.
Distinct declarations must share the same named type component. Repeated uses
of the same declaration remain valid, including global references with anonymous
types. Explicit abstract heads participate in consistency; abstract or blocked
implicit members do not. Wildcards do not add element declarations.

The walk follows model groups and particles but stops at element declarations:
an element's own complex type forms a separate scope. The existing resolved
component list supplies those anonymous and imported type roots independently.
Shared components are visited once per model, occurrence counts are never
expanded, and zero-maximum particles add no declarations. Named groups are
checked even when unused. Extended content includes inherited particles.

Each invocation owns its traversal state, declaration hash and arena allocations.
Every failure releases them without changing the resolved components. There is
no mutable process-global checker state. Native schema replacement retains its
existing transactional ownership, so rejected replacements leave the reader's
prior schema usable. Qore's entry and resource-callback cancellation checks
remain in force; this private C checker adds no I/O or Qore runtime dependency.

libxml2 does not define a dedicated consistency error code. The checker reports
`XML_SCHEMAP_FAILED_PARSE` with a `cos-element-consistent` diagnostic. Both Qore
DOM and stream schema construction report `XSD-SYNTAX-ERROR`. Allocation failures
reject construction, with exhaustive fault-injection tests covering successful
and conflicting declaration paths.

The correction lives in a hash-guarded build copy of pinned libxml2 2.15.4;
upstream source files are unchanged. The 34-schema configure probe includes
positive and negative declaration scopes, blocking, namespace distinctions,
anonymous types and zero particles. `AUTO` falls back to the private provider
when the installed dependency fails; `SYSTEM` rejects it. A corrected system
backport continues to use the system provider.

For example, an order can accept a concrete integer quantity through a decimal
substitution head and then require another quantity of the same named type:

```qore
string schema = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="item" type="xs:decimal" abstract="true"/>'
    '<xs:element name="quantity" type="xs:int" substitutionGroup="item"/>'
    '<xs:element name="order"><xs:complexType><xs:sequence><xs:element ref="item"/>'
    '<xs:element name="quantity" type="xs:int"/></xs:sequence></xs:complexType></xs:element></xs:schema>';
hash<auto> order = parse_xml_with_schema('<order><quantity>17</quantity><quantity>18</quantity></order>', schema);
@assert(order.order.quantity == ("17", "18"));
```

Changing the local `quantity` declaration to `xs:string` causes schema
construction to fail, even when both lexical values would be accepted as strings.
See the [root cause and evidence](../test/wsdl-interop/p5-native-element-consistency-finding.md).
