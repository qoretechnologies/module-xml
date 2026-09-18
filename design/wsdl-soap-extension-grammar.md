# SOAP binding extension declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

`WsdlSoapExtensionGrammar` checks direct SOAP 1.1 and SOAP 1.2 extension declarations
while `WsdlStructureGrammar` reads the WSDL document. It handles binding, operation,
body, fault, header and address declarations under their recognized core parents,
including a header's nested headerfault declarations. Schema/message processing
and HTTP/MIME payload handling have separate owners.

The checker keeps construction-local element frames and the selected extension
namespace. Only headers have element children, which must be headerfaults in the
same SOAP binding namespace. Header content permits XML whitespace between those
children. The other declaration types have empty content: even character
whitespace is invalid, while XML comments and processing instructions are not
character content.

## Attributes and normalized values

The declared attributes have their schema lexical types. Required transport,
address location, fault name and header message/part/use attributes are checked
before compilation. `style` and `use` retain the whitespace-sensitive enumeration
rules of their string-based types. URI values, names, QNames and part lists use the
shared XSD lexical helpers. SOAP 1.1 encodingStyle is a URI list; SOAP 1.2 has a
single URI value. Both `wsdl:required` and SOAP 1.2 `soapActionRequired` use XML
boolean syntax.

SOAP 1.1 has closed attribute sets, with `wsdl:required` on extensibility elements
but not on headerfault. SOAP 1.2 permits foreign attributes, including on faults
and headerfaults, and adds operation-level `soapActionRequired`. Attributes in the
element's own namespace do not satisfy its foreign-attribute wildcard.

The four defined schema-instance attributes have separate handling. Declarations
are not nillable; an explicit xsi:type must name the matching published SOAP
declaration type. Location hints must contain lexical URIs and complete
namespace/location pairs, but never trigger schema retrieval. Other foreign
schema-instance names follow the applicable attribute wildcard.

After the stream validates a declaration, `WsdlSourceProjection` normalizes its
known URI and token attributes in the grouped compilation data. It also normalizes
nested headerfault attributes, including repeated declarations grouped in a list.
This separates the original source text from
component identity: `part=" token "` resolves the declared `token` part, while the
source returned by the service retains the authored whitespace. Foreign attribute
values remain metadata and are not rewritten as known binding attributes.

For example, both of these references select the same authentication part:

```xml
<soap:header message="tns:Credentials" part="token" use="literal"/>
<soap:header message=" tns:Credentials " part=" token " use="literal"/>
```

## Specification ownership

The SOAP 1.1 and SOAP 1.2 schemas are pinned test inputs. The
[SOAP 1.2 binding specification, section 3.4](https://www.w3.org/submissions/wsdl11soap12/)
expressly permits foreign attributes on faults; that rule is used even though the
published schema's restriction omits the attribute wildcard. Location-pair syntax
comes from
[XSD 1.0 Structures, section 4.3.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#schema-loc),
independently of whether a validator chooses to use a hint.

`test/wsdl-soap-grammar.qtest` exercises source, serialized and data-serialized
services, detached operations, provider samples, requests/responses and body/header
fault values. Its companion Python suite assesses the same documents with pinned
Xerces and records the two specification/schema differences explicitly. Prefix
aliases and a default SOAP binding namespace do not change component selection.
