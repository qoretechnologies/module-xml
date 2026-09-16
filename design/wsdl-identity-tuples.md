# Scoped WSDL identity tuples

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL validates element `key`, `unique` and `keyref` constraints during conversion
of complete XML values and SOAP message elements. Saved schemas and ordinary,
native, saved and soft providers retain the same constraints. Definition grammar,
expanded paths and reference resolution are described in
[identity components](wsdl-identity-components.md).

## Capture and scope

Each participating element has a transient node with its expanded name, assessed
simple type, selected value identity, declaration nillability, attributes and
children. Capture starts at a constraint owner and continues through its assessed
subtree. It uses values already produced by the converter: identity checking does
not re-run user conversions. Native field providers retain their existing field
validation before enclosing-element serialization.

The capture retains atomic/list/union selection and exact numeric, calendar,
binary, QName and NOTATION identities. Defaulted values participate. Builtin
`xsi:type`, `xsi:nil`, `xsi:schemaLocation` and `xsi:noNamespaceSchemaLocation`
participate only when actually present in input or emitted output. A selected
type or nil state alone does not invent an attribute. Native empty complex records
remain present as `{}`, allowing a missing required field to be distinguished
from an existing empty element during subsequent serialization. Untyped `anyType`
text uses the existing XML-data hash in native preservation mode, retaining the
absence of `xsi:type`; scalar values supplied by an application still request
the existing type inference. Empty list inputs accepted as empty element-only
records are normalized before ordinary record validation.

Compiled XPath alternatives select actual node identities; overlapping paths
select one node once. Fields may select at most one simple-typed node. A missing
or nil field makes a unique/keyref tuple incomplete; a key requires every field
and also rejects fields assessed against nillable element declarations. Tuple
components use length-framed typed keys, preserving field boundaries and value
families. See the approved [nil rule](../test/wsdl-interop/nil-identity-interpretation.md)
and [skipped-element rule](../test/wsdl-interop/skipped-subtree-interpretation.md).

The child scope validates first. Its tables then move to the parent, while its
nodes remain available for ancestor selectors. Conflicts between inherited
entries for distinct nodes disappear at their receiving scope; local entries
have precedence. Keyrefs use that completed scope's table. This follows
[XSD 1.0 Structures §3.11.4–5](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-identity-constraint).

## Unassessed attribute values

An attribute accepted by a lax or skip wildcard on an assessed element still
participates. WSDL compares its initial normalized string, so `1` and `01` are
distinct and identical strings compare equal. This is an explicit processor
choice: XSD 1.0 leaves the lexical-to-value mapping of `anySimpleType` unspecified,
including its identity comparisons. See
[Structures §2.2.1.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Simple_Type_Definition)
and [§3.2.5](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Attribute_Declaration_details).

Native libxml2 and pinned Xerces observations differ for some such attributes.
Fixtures record each expected outcome separately; those differences do not
change WSDL's string policy or exclude the attributes. Declared wildcard
attributes instead use their declared selected types. The approved exclusion
of skipped element subtrees does not exclude attribute wildcards on an assessed
owner.

Legacy `preserve_types=False` keeps its existing scalar mapping. When this
projection removes a type distinction needed by a constraint, serialization
rejects the resulting duplicate. Use `preserve_types=True` or complete XML
carriers for lossless forwarding; see the
[approved compatibility policy](../test/wsdl-interop/legacy-identity-projection.md).

## Lifetime and resource behavior

Tuple state is thread-local and document-scoped. Destructors restore the enclosing
scope on success, rejection or interruption; only successful child conversions
are attached to a parent. Nested document validation saves and restores its
caller's state. Shared schema declarations contain no mutable instance tables.
Concurrent documents can therefore use the same keys independently.

Completed child tables transfer ownership instead of leaving a retained copy at
every ancestor. Conflict cleanup revisits only actual collisions. A sole-child
chain with no local constraints transfers tables without scanning their entries.
XPath traversal uses iterative worklists and node deduplication. Work remains
proportional to the actual selectors, fields and merging required by the schema;
no global linear-time claim is made for arbitrary overlapping selectors.

`test_identity_tuple_resources.py` instruments a temporary copy of the actual
private implementation. It counts retained entries at 16/32/64/128 nodes and
checks that unchanged inherited tables incur zero tuple-loop visits. There is
no production inspection API. Lifecycle tests cover rejection/retry, actual
program interruption, custom converter counts, concurrent documents and flat
128/1024-value tables.

## Catalog example

The catalog's references must name one of its distinct product codes:

```qore
%modern
%requires WSDL
string xsd = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='catalog'><xs:complexType><xs:sequence>"
    "<xs:element name='product' type='xs:string' maxOccurs='unbounded'/>"
    "<xs:element name='ref' type='xs:string' maxOccurs='unbounded'/>"
    "</xs:sequence></xs:complexType>"
    "<xs:key name='products'><xs:selector xpath='product'/><xs:field xpath='.'/></xs:key>"
    "<xs:keyref name='references' refer='products'><xs:selector xpath='ref'/>"
    "<xs:field xpath='.'/></xs:keyref></xs:element></xs:schema>";
XsdSchema schema(xsd, {"async_only":True});
hash<auto> catalog = {"product":("SKU-100", "SKU-200"), "ref":("SKU-200",)};
XsdXmlValue wire = schema.serializeXmlValue("", "catalog", catalog);
printf("%s\n", wire.getXml());
# A ref of SKU-300 raises SOAP-SERIALIZATION-ERROR.
```
