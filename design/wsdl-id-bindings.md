# WSDL document ID bindings

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL validates selected ID, IDREF and IDREFS values when an assessed XML root
closes. Lexical validation alone cannot detect an unresolved reference or two
owners of the same identifier. The binding rule and parent ownership follow
[XSD 1.0 cvc-id and section 3.15.5](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-id):
an ID attribute identifies its element, while an ID-valued child identifies its
parent. A token must identify exactly one element in the validation root.
Forward references are accepted. Repeated bindings to the same owner are valid;
different owners are invalid. An ID value on a root with no corresponding
in-scope owner is invalid, as confirmed by the
[Working Group's issue 9922](https://www.w3.org/Bugs/Public/show_bug.cgi?id=9922).

`XsdUnionValueIdentity` retains selected identity tokens separately from value
space equality. Successful atomic conversions and actual list/union selections
contribute tokens after lexical and facet validation. A union selecting string
does not acquire the obligations of an unselected IDREF member. Nilled values
contribute only assessed attributes; skipped wildcards contribute no values.
Defaulted IDREF attributes participate. Element default expansion is a separate
operation and is not implemented by this registry.

Each actual element occurrence has a frame with its owner and parent numbers.
Frames share a hash table within the root and retain no input tree. Missing
bindings have owner zero; conflicting owners have a negative marker. Assigning
owner numbers checks overflow. Root closure scans the table once. Thread-local
frames are restored by lexical scope destruction on success, errors and
cancellation. The thread local holds a frame, not its restoring scope, so it
cannot keep that scope alive. Public schema and operation calls establish
independent document boundaries even when called from another conversion.

Standalone simple-type conversion remains datatype-only. Complete element
providers assess their element as the validation root. WSDL parts are assessed
as XML roots; sibling parts and SOAP headers do not donate bindings to a part.
This is payload schema assessment, not validation of the SOAP envelope against
a combined schema. SOAP encoding references are a distinct protocol mechanism.

Providers first perform field conversions, then validate the completed value.
Preparatory nested provider passes suspend identity collection: an IDREF field
cannot be closed before its sibling ID field is converted. Retained-XML checks
and wildcard output checks avoid counting an internal second traversal as new
owners. The final selected values contribute their obligations without invoking
custom scalar converters again to discover their selected type.

`XsdIdentityDataType` wraps ordinary element providers whose reachable schema
can contain identity values, retaining field, list, optionality and soft-type
metadata. Native and retained-XML providers use the same root checks. Saved
providers retain their declaration and underlying conversion provider; restored
members are checked before use. A previously saved bare native hash provider
without a schema declaration cannot gain requirements absent from its metadata.
Legacy values also cannot reconstruct dynamic types discarded during decoding;
use `preserve_types=True` and native providers when selected types must survive.

For a schema with repeated `ref` elements of type IDREF and repeated `item`
elements carrying an ID attribute, this value contains forward references:

```qore
hash<auto> value = {
    "ref": ("shipment17", "shipment18"),
    "item": ({"^attributes^": {"id": "shipment17"}},
             {"^attributes^": {"id": "shipment18"}}),
};
XsdXmlValue xml = schema.serializeXmlValue("", "value", value);
auto checked = schema.getNativeDataProviderType("", "value").acceptsValue(value);
```

Removing the second item rejects the value with `SOAP-SERIALIZATION-ERROR` or
`RUNTIME-TYPE-ERROR`, respectively. Receiving the corresponding invalid SOAP
payload raises `SOAP-DESERIALIZATION-ERROR` before handler dispatch. Repeated
optional record fields use their base type code to preserve occurrence lists;
Qore output-type compatibility alone does not establish that a provider is a
list provider.

See the [unit and independent regressions](../test/wsdl-interop/id-bindings-evidence.md).
