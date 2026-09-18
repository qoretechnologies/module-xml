# MIME multipart declaration grammar and nested SOAP metadata

Copyright (C) 2026 Qore Technologies, s.r.o.

`WsdlMimeMultipartGrammar` validates multipart extension payloads in the original
XML reader stream. It owns depth-indexed container frames and delegates each SOAP
body/header or MIME content/XML leaf to its existing extension grammar. Nested
containers preserve this ownership. QName attributes require bound prefixes.
Character data, invalid attributes, unqualified/foreign part declarations and
mismatched SOAP versions fail before binding publication.

The multipart container accepts qualified `mime:part` children. The part container
accepts concrete format extensions; unknown optional vendor payloads remain
opaque, while unknown required extensions reject. The source projection walks
these containers with their actual namespace scopes and isolates vendor payloads
before local-name grouping. Leaf normalization applies the existing QName,
NMTOKEN, URI and body-parts rules. Schema-instance hints are validated without
retrieving resources.

Container grammar uses the published MIME schema dated 2004-08-24, which corrects
the older unqualified-part declaration. The optional part `name` attribute is
lexically checked and retained in source; it does not identify an abstract message
part. This general WSDL grammar is not a claim to enforce every WS-I Attachments
Profile restriction. In particular, the profile forbids that optional name and
requires explicit `mime:content/@part`; the general single-part default is a
separate binding rule.

A SOAP multipart binding requires one part containing its SOAP body. Nested SOAP
headers belong to that part. Compilation establishes multipart, part and header
namespace scopes before resolving header message QNames. It uses the same owned
header/headerfault descriptions as direct SOAP bindings and preserves literal body
namespace/encoding hints. Headers in a non-root part reject. Source, imported and
saved services reconstruct these descriptions; detached operations retain them.

Multipart content metadata uses internal message argument keys. Every alternative
resolves the same public WSDL part name through `WSMessage::pmap`. For example,
parts `invoice` and `copy` can reference one global `Document` element while each
retains its own alternatives. Use `description.parts{message.pmap.invoice}` to
inspect the alternatives for `invoice`.

A root MIME declaration can contain a SOAP body and a session header:

```xml
<mime:multipartRelated>
  <mime:part xmlns:session="urn:session">
    <soap:body use="literal" parts="order"/>
    <soap:header message="session:Session" part="token" use="literal"/>
  </mime:part>
</mime:multipartRelated>
```

The header uses the same native message/part map as a directly bound header.
With no attachment values, the existing transport can send an ordinary SOAP
message; WS-I Attachments Profile R2917 permits this for SOAP 1.1. Declaring MIME
metadata does not itself create an attachment value or replace wire validation.

MIME content uses the same declaration media parser in direct and multipart
bindings. Omitting `part` selects the sole abstract message part; omission with
multiple parts and references to unknown parts fail. Omitting `type` accepts every
MIME type and is represented by `*/*` in the multipart map. An explicitly empty
`type` fails. All alternatives undergo parameter and wildcard validation before
publication; original supplied media strings remain in multipart metadata.

An empty `<mime:content/>` is a present declaration. A single-part HTTP upload
can use it to accept arbitrary content; callers supply a concrete media type in
the existing `^attributes^.^content-type^` value metadata. For example,
`{"payload":{"^value^":"invoice text", "^attributes^":{"^content-type^":"text/plain;charset=UTF-8"}}}`
selects UTF-8 text without relaxing the payload's declared schema type.

These defaults follow general WSDL 1.1 section 5.3. The published 2004 MIME schema
requires an explicit content part for WS-I; the general single-part default is
checked separately and does not imply WS-I Attachments Profile conformance.
