# Explicit XML values

Copyright (C) 2026 Qore Technologies, s.r.o.

`WSDL::XsdXmlValue` retains a complete XML element document as a Qore string.
It is an explicit value API; ordinary WSDL scalars and records use their documented
native conversion contracts, including lossless string alternatives for decimal
and [calendar values](wsdl-calendar-values.md). Construction checks XML well-formedness, independently of XSD
validation. The carrier is useful when callers need lexical spellings, namespace
bindings or content that a scalar or flat record cannot represent.

The existing `^type^`/`^val^` representation selects an `XsdAbstractType` and a
native value for serialization. It does not retain the source lexical spelling,
QName namespace scope, mixed text, comments or ordered repeated particles.
`XsdXmlValue` preserves that information without changing this existing API.

## Authoritative data and views

`getXml()` returns the original string. `getReader()` creates an independent
`XmlReader`; it retains element and attribute expanded names, descendant namespace
rebinding, whitespace, processing instructions, CDATA and comments. `resolveQName()`
resolves a lexical QName using the document element's scope, including the
implicit `xml` prefix. Descendant QName values use their reader's namespace scope.

`getExpandedName()` reports the root as `{namespace-uri}local-name`, including
`{}local-name`. `getXmlDataView()` returns a copy-on-write hash produced with
`XPF_PRESERVE_ORDER | XPF_ADD_COMMENTS | XPF_PRESERVE_WHITESPACE`; `getElementData()` returns its root value.
These hash views retain lexical scalar strings, attributes and ordered mixed
content keys, including whitespace-only fragments between children. Whitespace
separates repeated children into ordered suffixed keys (for example `entry^1`),
while immediately adjacent equal names can share a list. Processing instructions
remain available through the authoritative XML string and reader.

The source XML and inherited XML attributes are serialized by `Serializable`.
Reconstruction validates both and rebuilds all transient views and names; earlier
XML-only state is still accepted. A malformed XML string or a
missing/non-string serialized source fails explicitly. Instances expose no
mutator; returned strings and hashes use Qore's copy-on-write semantics. The class
is final so subclasses cannot replace the XML independently of its validated
root identity and views.

`getInheritedXmlAttributes()` returns the parent's effective `xml:lang`,
`xml:space` and `xml:base` attributes. The constructor accepts this optional map
when an element comes from another document. Unknown attributes, non-string
serialized values, invalid XML characters and invalid `xml:space` values reject.
`getXmlContext()` applies the root's overrides, including empty language resets,
and resolves relative bases with Qore `resolve_url()` and
`RESOLVE_URL_RELATIVE_BASE`. Without a nonempty inherited base, the authored
reference is retained until a base is available. XML Base permits unescaped extended IRIs, so Unicode characters and
spaces remain intact; existing percent escapes are neither decoded nor encoded
again. Unresolved leading parent segments are retained for relative bases whose
document URI is unknown. The authored `xml:base` value
remains unchanged in the XML. Context maps are separate from authored attributes;
`getXml()` and `getReader()` still expose standalone XML. Missing context keys
remain absent, and all maps use copy-on-write semantics.

## XML generation

`getXmlSerializationData()` returns a mutable `hash<auto>` using the XML module's
`^xml^` marker. For example:

```qore
%modern
%requires xml
%requires WSDL

XsdXmlValue quantity("<quantity unit='kg'>009.00</quantity>");
hash<auto> shipment = quantity.getXmlSerializationData();
shipment."^attributes^" += {"xmlns": "urn:shipments"};
string xml = make_xml({"shipment": shipment});
```

The generated quantity stays in the empty namespace, even though its shipment
parent has a default namespace. Its spelling `009.00` stays intact. Fragment
keys can have suffixes to preserve insertion order among multiple fragments.

The generator hash also carries inherited XML attributes on its containing
element. Preserve these when adding other parent attributes. This placement
retains contextual meaning without adding attributes to schema-controlled roots:

```qore
XsdXmlValue order("<o:Order xmlns:o='urn:orders'><quantity>009</quantity></o:Order>", {
    "xml:lang": "cs", "xml:space": "preserve", "xml:base": "https://example.org/orders/",
});
string xml = make_xml({"batch": order.getXmlSerializationData()});
```

The batch has the XML attributes; Order inherits them. Native attribute encoding
uses character references for tabs, line feeds and carriage returns, so XML
attribute normalization does not change those characters during reconstruction.

The native generator parses the entire fragment with a private libxml2 reader,
preserves its root document during iteration, then serializes that element.
Reader and document lifetimes are separate and exception-safe; the reader is
destroyed before its retained document. Cancellation is checked during root
validation, hash traversal, parsing and namespace traversal. Default libxml2
parser limits apply, external DTD loading is not enabled, and DOCTYPEs are rejected.

The XML declaration and nodes outside the document element are not embedded.
Element content is retained in its original order, subject to XML's normal
attribute, character-reference and line-ending normalization. Formatting does
not change whitespace within a fragment. Numeric-reference formatting does not
rewrite retained fragment content. Output encoding conversion reports errors
for unrepresentable characters.

The parser receives the actual UTF-8 encoding and input length after the Qore
string has been converted. The original declaration cannot decode these bytes
a second time, and embedded NULs cannot truncate input silently.

## Schema and SOAP consumers

`XsdSchema.getXmlValue(xml)` constructs a carrier for a declared global element.
`validateXmlValue(value)` returns the carrier after validation; the opt-in
`getXmlDataProviderType(namespace_uri, local_name)` returns an `XsdXmlValueDataType`.
Native provider field types remain unchanged. The XML provider retains its schema
owner and serializes that source-backed schema, rebuilding transient declaration,
namespace and type references during reconstruction. Optional/mandatory copies
retain their XML validator; optional providers accept an omitted value. Validation
and XML example generation allocate output prefixes in a private registry copy.

Element validation checks the exact expanded root name and applies both existing
native decoding and serialization constraints. Comments are excluded from the
validation projection, as they do not participate in XSD content models. The
retained XML and public ordered view still contain them. These checks use the
same scalar, particle and dynamic-type rules as native values.

Element-based literal SOAP parts accept `XsdXmlValue` objects keyed by WSDL part
name. A bare carrier is accepted when exactly one document part is selected.
Each fragment marker includes a length-prefixed WSDL message name and the part
name so independently serialized headers cannot overwrite each other.
SOAP values reject DTDs and processing instructions, as required for senders by
SOAP 1.1 section 3 and SOAP 1.2 section 5. Pure XML carriers retain processing
instructions for other XML uses.

`WSMessageHelper.getXmlMessage(message)` converts existing native examples into
XML carriers, keyed by WSDL part name, and applies the same validation paths.
Example generation therefore has the same content-model capabilities as the
native helper. Independently validated example coverage is tracked alongside the
interoperability plan.

`WSOperation.deserializeXmlRequest(xml, binding)` and `deserializeXmlResponse()`
return `hash<SoapXmlMessageInfo>`:

- `body` maps WSDL part names to carriers.
- `headers` maps WSDL message names, then part names, to carriers.
- `unbound_headers` retains other header elements in their original order.
- `extensions` retains SOAP 1.1 extension elements following the body.

Parts are matched by expanded XML name. Duplicate or missing body parts and
ambiguous bound header identities fail explicitly. The original envelope is
used for existing schema and fault handling, while carriers are extracted from
its XML. Default native decoding APIs retain their existing return shapes.

`XsdXmlValue.getChildValues()` extracts immediate element children in document
order. It materializes inherited namespace declarations, including bindings
used only in QName text; local declarations and default-namespace resets win.
The root tag is generated to escape attributes, then combined with the reader's
original inner XML. Child content retains CDATA, comments, whitespace and order.
Each child also retains the parent's effective XML attributes separately. Local
language/space overrides and relative/absolute/empty bases survive repeated child
extraction and Serializable reconstruction.

SOAP serialization places inherited XML attributes on the Body or Header
container. Retained siblings in one container must have the same inherited
context, including its absence; conflicting requirements raise
`SOAP-SERIALIZATION-ERROR`. Body and Header contexts are independent. Native
values do not declare retained ambient context, and native headers cannot erase
the context retained by XML headers. This contract avoids silently changing
context or adding schema-invalid attributes to payload roots.

`SoapClient.callOperation()` accepts the explicit `xml_values: True` option to
return `SoapXmlMessageInfo` for operations with output messages. One-way calls
return `NOTHING`. `SoapHandler.addMethod()` accepts an optional final
`xml_values` boolean to pass that type to the callback. A callback can return
carriers in its ordinary part-name response hash and `^header^` message/part hash.
For example:

```qore
hash<SoapXmlMessageInfo> response = client.callOperation("submit", {
    "body": new XsdXmlValue("<o:Order xmlns:o='urn:orders'><quantity>009</quantity></o:Order>"),
}, {"xml_values": True});
string original_response = response.body.body.getXml();
```

## Verification and scope

`test/wsdl-xml-value.qtest` checks the public API, reconstruction, invalid state
and XML generation. `test/xml-literal.qtest` checks native fragments, encoding,
namespace isolation, complete-input rejection, ordered nodes and cancellation.
`test/wsdl-interop/test_xml_values.py` independently checks emitted lexical
values, QName context and mixed content; libxml2 and pinned Xerces-J validate
both positive and negative XSD examples.

`test/wsdl-xml-consumers.qtest` covers schema/provider reconstruction, declared
parts and headers, exact lexical text, negative validation and real local HTTP
calls with the client and handler options independently enabled. The Python
`test_xml_consumers.py` checks input/output values and examples with libxml2 and
pinned Xerces-J. Open validation and dependency findings remain failures in the
execution record; this document does not claim complete schema or SOAP conformance.

`test/wsdl-xml-context.qtest` covers inherited language/space/base state, local
overrides, malformed state, backward reconstruction, attribute whitespace and
copy isolation. `test_xml_context.py` checks 80 payloads with libxml2 and Xerces,
comparing authored attributes and effective ancestor context through both SOAP
versions/directions, schema/provider reconstruction and direct XML generation.
The consumer qtest also checks context over actual HTTP and sibling conflicts.

Namespace isolation follows [Namespaces in XML 1.0, section 6.2](https://www.w3.org/TR/REC-xml-names/#defaulting).
The retained document's lifetime follows the [libxml2 reader contract](https://gnome.pages.gitlab.gnome.org/libxml2/html/xmlreader_8h.html).
Context follows [XML Base](https://www.w3.org/TR/xmlbase/#resolution) and
[XML language/space inheritance](https://www.w3.org/TR/REC-xml/#sec-lang-tag).
Attribute escaping follows [XML attribute normalization](https://www.w3.org/TR/REC-xml/#AVNormalize).

SOAP processing-instruction and DTD rules follow [SOAP 1.1 section 3](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383494)
and [SOAP 1.2 section 5](https://www.w3.org/TR/soap12-part1/#soapenv).
