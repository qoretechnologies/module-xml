# ENTITY values in WSDL document conversion

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL element, attribute and message-part conversion checks the document requirement
of the **selected** ENTITY value after its datatype conversion succeeds. The
native representations remain strings for ENTITY/ENTITIES and lists for custom
list types. No new public value carrier is needed.

[XSD 1.0 Part 2 §3.3.11](https://www.w3.org/TR/xmlschema-2/#ENTITY) distinguishes
ENTITY's NCName spelling from the requirement for an unparsed-entity declaration.
ENTITIES applies the requirement to each name and has a minimum length of one.
A custom list of ENTITY can be empty unless its facets forbid that value.
[SOAP 1.1 §3](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383494)
prohibits a DTD. [SOAP 1.2 §5](https://www.w3.org/TR/soap12-part1/#soapenv)
requires empty unparsed-entity and notation properties and prohibits a document
type declaration. Consequently, a selected nonempty ENTITY value cannot appear
in a valid SOAP message.

## Conversion and union selection

`XsdUnionValueIdentity` retains selected entity names separately from primitive
family/value identity. Enumeration equality and `valueKey()` still compare
ENTITY's string value. Builtin ENTITIES, atomic lists and captured union-valued
items propagate the selected names in order. Shared union trial results carry
the same metadata without repeating a member callback.

`XsdDocumentValueCapture` observes the existing target-specific schema captures.
The surrounding element/attribute/part operation finishes its datatype and
facet checks before checking document requirements. Its lifetime restores the
caller's thread-local captures on success, exceptions and cancellation. Nested
operations receive their own captures. Primitive metadata is inspected only
when no union/list selection capture is required.

For `ENTITY | string`, `photo` selects ENTITY and fails document conversion;
that failure cannot cause selection of `string`. For `string | ENTITY`, `photo`
selects string and remains valid. A restricted ENTITY member that fails its own
enumeration or pattern permits the next datatype alternative. The same ordering
applies to each list item and to a list member of a union.

The checks apply to element occurrences, simple content, attributes, defaulted
attributes, typed WSDL parts and encoded array items. Both SOAP directions and
complete retained XML validation use these paths. The existing retained XML APIs
do not accept a DTD. Standalone native XML validation with legitimate declarations
is described in [the native ENTITY design](xml-entity-validation.md).

## Detached values, defaults and examples

Detached simple-type conversion, simple-type provider acceptance, schema facet
compilation and finite-value comparison remain datatype operations. Complete
message providers additionally check the supplied parts through their schema
instance conversion; see [message provider validation](wsdl-message-providers.md).
`XsdXmlValueDataType` checks the complete retained element through that conversion.

`XsdAttribute::getDefaultValue()` returns the compiled schema value.
`getInstanceDefaultValue()` additionally checks that value's document requirements.
It uses the compiled value, retaining declaration QName identity even when an
instance rebinds the same prefix. Output validation uses a private namespace
registry. Nilled standalone elements register the instance namespace before
writing the nil attribute; omitted/nilled ENTITY values have no selected name.

Generated native values pass the same instance checks before returning from
normal `WSMessageHelper::getMessage()` calls. A candidate requiring an unavailable
declaration raises `XSD-SAMPLE-ERROR`; retained XML generation can report this
before constructing XML. See [sample validation](wsdl-sample-instances.md) for
bounded generation and the existing explanatory choices option.
Datatype-only sample generation does not invent declarations.

For example, a legacy contract might accept an unparsed image name or an integer
catalog reference. The integer alternative can be used in SOAP:

```qore
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:t="urn:catalog" targetNamespace="urn:catalog">
    <xs:simpleType name="Reference"><xs:union memberTypes="xs:ENTITY xs:int"/></xs:simpleType>
    <xs:element name="item" type="t:Reference"/></xs:schema>', {"async_only": True});
XsdXmlValue item = schema.serializeXmlValue("urn:catalog", "item", 17);
printf("%s\n", item.getXml());
# Supplying "photo" instead raises SOAP-SERIALIZATION-ERROR.
```

## Verification

`test/wsdl-entity-values.qtest` checks ordered selection, lists, declaration-only
operations, defaults, omitted/nilled values, retained XML, reconstruction,
reentrant callbacks, cancellation and concurrent reuse. `wsdl-entity-consumers.qtest`
checks local SoapClient/SoapHandler traffic and RPC type-based parts in both actual
SOAP bindings. `test/wsdl-interop/test_entity_wsdl.py` validates authored inputs and
all emitted payloads independently with pinned Xerces, checking completeness and
preserved values through reconstructed providers and retained XML consumers.
