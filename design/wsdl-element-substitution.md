# XSD element substitution declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdElement` captures global `substitutionGroup` QNames in their declaration's
namespace context and retains effective `final` exclusions. Element final allows
extension and restriction. Source `finalDefault` is filtered to those methods;
an explicit empty value overrides the default. Invalid lexical forms, local
affiliations and local final attributes fail during construction.

After all schema documents contribute their declarations, `XsdSchema` resolves
affiliations by expanded name. An iterative dependency traversal rejects missing
heads and circular affiliations, including declarations with explicit types.
It resolves heads before members and assigns the head's exact type component
when a member omits its type. This defaulting does not inherit nillability,
abstractness, value constraints or element blocks. Anonymous types retain their
identity. References subsequently assimilate the resolved global declaration.

After complex/simple finalization and value-constraint checks, every immediate
affiliation must satisfy Type Derivation OK under its head's final exclusions.
An abstract member type is permitted in a declaration graph: instance validation
separately requires a concrete selected type. Identity remains a valid type
relationship even under `final="#all"`.

The schema computes concrete membership by following each nonabstract element's
affiliation chain. A head's `block="substitution"` prevents alternate element
names. Extension/restriction blocks are applied to the complete type derivation,
combined with the head type's block and every intermediate complex type's block.
The selected type's own block does not prevent its selection. A blocked
intermediate element can still affiliate a member to a more distant head;
the receiving head supplies the element block. Abstract declarations stay in
the affiliation graph but are absent from actual member sets. Nonabstract heads
belong to their own sets. Local declarations have no substitution group.

The public inspection APIs are:

| Method | Result |
| --- | --- |
| `getSubstitutionGroupExclusions()` | Effective element final method-name set |
| `getSubstitutionGroupName()` | Captured immediate head QName, or NOTHING |
| `getSubstitutionGroupAffiliation()` | Resolved immediate head declaration, or NOTHING |
| `getSubstitutionGroup()` | Concrete members keyed by expanded element name |
| `getInstanceDeclarations()` | Concrete occurrence declarations, including self for a local element |
| `getInstanceDeclaration(name)` | Permitted declaration for an expanded instance name |
| `getDeclaration()` | Canonical global declaration behind a reference, otherwise self |

For example, a member can inherit an integer head's type:

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='item' type='xs:int' abstract='true'/>"
    "<xs:element name='quantity' substitutionGroup='item'/>"
    "</xs:schema>");
XsdElement quantity = schema.getElement("", "quantity");
@assert(quantity.type === schema.getElement("", "item").type);
@assert(keys schema.getElement("", "item").getSubstitutionGroup() == ("{}quantity",));
```

Global references retain a strong link to their declaration for membership
inspection while keeping their own occurrence limits. Returned maps are copies.
Schema serialization reconstructs affiliations and members from retained source
documents. Successful incremental additions extend existing heads' sets; failed
additions restore previously published sets as well as the component registry.
Membership is computed before publication, with restoration if publication is
interrupted. Per-call traversal state never resides in published declarations.

The affiliation traversal visits each declaration once; membership storage is
bounded by the potential member/head pairs in the input graph. Type checks use
the existing bounded derivation worklist. Qore loops retain runtime cancellation.
Construction and concurrent inspection tests cover forward/imported/chameleon
declarations, restoration, exact component identity and deep affiliation chains.

The native libxml2 validator applies the same method-set rule. The verified
build-tree correction in `QoreXmlLibXml2ElementSubstitutionFix.cmake` treats every
simple type step as restriction, including builtins whose declaration flags do
not encode that method. Extension accumulation is independent of previously
seen restrictions. The correction adds no allocation or traversal, preserves
upstream sources and is guarded by both input and output hashes. The configure
probe checks 45 schemas, each with head and member instances through DOM and
streaming validation. Passing distribution backports remain eligible for the
system provider regardless of version string.

These rules implement XSD 1.0 Structures §3.3.2, Element Declaration Properties
Correct §3.3.6(4,6), Substitution Group OK (Transitive) §3.3.6 and Type Derivation
OK §3.4.6/§3.14.6. See the [normative specification](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/)
and the separate [validator adjudication and tests](../test/wsdl-interop/element-substitution-evidence.md).

The [child-particle design](wsdl-substitution-particles.md) explains matching,
attribution, conversion, provider fields, samples and post-membership component checks.
