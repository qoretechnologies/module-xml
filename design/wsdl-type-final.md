# XSD type construction and final exclusions

Copyright (C) 2026 Qore Technologies, s.r.o.

Schema construction records each type's effective `final` set before its source
namespace scope exits. `Namespaces::schema_final_default` holds the currently
parsed schema's default, with restoration on both successful and failed exits.
Imported, included, chameleon and multiple inline schemas therefore keep their
own defaults. Canonical builtin definitions keep their intrinsic empty set.
Explicit empty `final` overrides the default. Simple types retain restriction,
list and union; complex types retain extension and restriction. Unknown tokens,
non-XML whitespace, mixed `#all` lists and `final` on anonymous declarations fail
with `WSDL-ERROR`. Anonymous types still inherit applicable schema defaults.

`XsdDerivationMethod`, `XsdAbstractType::isFinal()` and
`getFinalDerivations()` expose the retained exclusions. The set is immutable
after construction, returned by value, and preserved by `Serializable`. Legacy
encoded array adapters carry the enclosing declaration's set. Previously
serialized schemas that discarded these attributes must be reparsed to acquire
the information; it cannot be reconstructed from the lost attributes.

Simple resolution checks a restriction's resolved base, a list's item type and
a union's actual atomic/list member definitions. XSD 1.0 union composition
replaces nested union definitions with their members, including restricted
unions. The replaced union's own final set does not become a property of its
members. Existing shared union graphs avoid materializing repeated paths;
resolved union nodes have already validated their actual members. A union used
as a list item retains its own list exclusion, because that operation does not
replace the item definition. Complex resolution checks the selected derivation
method against the resolved base before inheriting content. Synthesized
simple-content facet restrictions have their own empty final set and still
check their actual base's restriction exclusion.

For example, an invoice contract can prevent downstream restrictions on its
validated amount while allowing direct use of that type:

```qore
XsdSchema invoice("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:simpleType name='Amount' final='restriction'>"
    "<xs:restriction base='xs:decimal'><xs:minInclusive value='0'/>"
    "</xs:restriction></xs:simpleType>"
    "<xs:element name='amount' type='Amount'/></xs:schema>");
@assert(invoice.findType("Amount").isFinal(XsdDerivationMethod::Restriction));
XsdXmlValue output = invoice.serializeXmlValue("", "amount", "12345678901234567890.25");
```

The authoritative component mapping is
[XSD 1.0 Datatypes 4.1.2](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/),
including its explicit filtering of irrelevant `finalDefault` values.
The Structures document labels its duplicated simple-type mapping in 3.14.2
non-normative; its inclusion of extension does not override that mapping.
[Structures 3.14.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-restricts)
applies constraints to the composed member definitions, and
[3.4.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-ct-extends)
constrains complex derivations. The
[second-edition errata](https://www.w3.org/2004/03/xmlschema-errata)
do not amend these rules.

The private libxml2 correction applies anonymous simple-type defaults at the
missing construction branch. It sets the same three flags as the named-type
branch, without additional allocation or traversal. The source archive remains
unchanged; CMake verifies the input and output hashes of the generated source.
The configure probe tests all three methods with matching, unrelated and absent
defaults, so AUTO selects a corrected dependency by behavior. SYSTEM rejects a
dependency that fails this check. DOM validation, stream validation and failed
schema replacement use the corrected component construction.

The unit suites are `test/wsdl-type-final.qtest` and
`test/xml-type-final.qtest`. `test/wsdl-interop/test_type_final.py` checks exact
construction errors and preserved values in both actual SOAP bindings,
directions and serialized copies. Validator disagreements and reference schema
derivatives are recorded alongside the interoperability plan. This design
covers construction-time type exclusions; instance `block` handling and element
substitution exclusions have separate P5 ownership.
