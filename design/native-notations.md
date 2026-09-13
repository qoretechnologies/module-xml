# Native XSD 1.0 NOTATION assessment

Copyright (C) 2026 Qore Technologies, s.r.o.

The XML dependency validates notation declaration attributes before publishing a
component. `name` is an NCName with collapsed whitespace; `id` is an ID; `public`
is a token and `system` is an anyURI. At least one identifier must be present.
An empty identifier is present and valid. Foreign namespace attributes are
allowed; unknown unqualified and XML Schema namespace attributes are rejected.
The declaration permits one optional annotation.

These requirements follow [XSD 1.0 Part 1 §3.12](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cNotation_Declarations).
The XML Schema representation of `public` uses the token lexical space; the
parser does not impose the different DTD `PubidLiteral` character grammar on it.

[Part 2 §3.2.19](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#NOTATION)
requires an enumeration-derived NOTATION type when a schema uses the datatype.
The final component pass checks element and attribute declaration types,
including simple content, and the item/member types used by list/union
components. It permits unused intermediate atomic restrictions: a later
restriction can introduce the required enumeration. An unused intermediate
complex type can likewise receive its enumeration through a later simple-content
restriction. List or union construction already uses its item/member types and
cannot supply a missing atomic NOTATION enumeration through a later collection
facet.

The pass walks component uses iteratively. A visited table avoids repeated list
and union expansion. A separate status cache resolves atomic restriction ancestry
once, retaining whether the primitive is NOTATION and whether an enumeration was
introduced. Intermediate cached restrictions are assessed when actually used;
caching an unrestricted base does not reject its valid enumerated derivative.
Both tables and worklists are local to schema compilation and own no components.
The pass requires space and time proportional to the visited graph and facets.
Builtin base types terminate the walk, including libxml2's self-referencing
`anyType`. Existing schema cycle checks run before this pass.

The enumeration requirement is a schema-component constraint. It does not turn
the builtin's lexical space into an empty set. A document selecting an otherwise
unused type through `xsi:type` is checked against the schema's declared notation
QNames and ordinary derivation/facet rules. The compatibility advice concerning
attributes and no-target-namespace schemas is a recommendation, not a prohibition
on notation elements in namespaced schemas.

Notation value identity uses namespace URI and local name. Equal public/system
identifiers do not make differently named declarations equal. Prefix aliases
are equal; QName and NOTATION remain distinct primitive value families. Existing
native value/default ownership retains declaration namespace scope independently
of instance prefixes. Validation preserves the original instance XML.

For example, a document can refer to an allowed image format with a prefix
chosen independently of the schema:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:f="urn:formats" targetNamespace="urn:formats">
  <xs:notation name="jpeg" public="image/jpeg"/>
  <xs:simpleType name="Format">
    <xs:restriction base="xs:NOTATION">
      <xs:enumeration value="f:jpeg"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="format" type="f:Format"/>
</xs:schema>
```

The instance `<a:format xmlns:a="urn:formats">a:jpeg</a:format>` is valid. An
unbound prefix or a QName outside the enumeration is rejected.

Allocation failures in schema attribute extraction are distinct from a missing
optional attribute. The shared reader returns the empty lexical value for an
absent node, while failures extracting or interning a present value set the
parser error. ID normalization trims an already validated, owned NCName buffer
in place, avoiding the nullable public whitespace allocator. Component allocation,
worklist growth and hash insertion are checked and cleaned up on every exit.

CMake's behavioral probe includes both valid and invalid notation schemas. AUTO
falls back when a system library fails; SYSTEM fails configuration; the bundled
provider applies an input/output-hash-guarded correction to the pinned source in
the build tree. No public libxml2 ABI or installed dependency is replaced.

Tests are `test/xml-notations.qtest`, the pinned-Xerces matrix
`test/wsdl-interop/test_notations.py`, and the native allocation/provider suite.
See [acceptance evidence](../test/wsdl-interop/native-notations-evidence.md).
WSDL notation declaration storage and conversion are a separate P5 increment;
this native change does not claim that the WSDL conversion gap is closed.
