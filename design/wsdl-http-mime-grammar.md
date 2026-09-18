# HTTP and MIME declaration grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

`WsdlHttpMimeExtensionGrammar` validates the HTTP binding, operation, address,
urlEncoded and urlReplacement declarations, and MIME content and mimeXml
declarations recognized directly beneath their core WSDL parents. It shares the
existing declaration reader pass. Multipart structure and binding combinations
have separate validation owners.

These declarations have empty content. Comments and processing instructions are
allowed; text, character whitespace and element children are rejected. HTTP verb,
operation location and address location are required. Known attributes use their
published schema types: URI values, NMTOKEN names and MIME type strings. Attribute
sets are closed. `wsdl:required` is an XML boolean on the named extensibility types;
the two anonymous URL-encoding declaration types have no attribute wildcard.

`WsdlExtensionLexicalGrammar` centralizes URI validation, XML booleans and the four
defined schema-instance attributes for core WSDL and binding declarations. Core,
SOAP and HTTP/MIME callers supply their declaration namespace and schema type.
Each caller supplies the applicable published type, including SOAP body's tFault
derivation. An explicit xsi:type must match that type; anonymous declaration types
cannot be named this way. Declarations are not nillable. Location hints
require lexical URI references and complete namespace/location pairs, and never
cause retrieval. Unknown schema-instance names follow the caller's attribute rules.

After validation, `WsdlSourceProjection` normalizes known HTTP URI/token attributes
and MIME part names in the compilation graph. Original source text and foreign
metadata remain unchanged. For example, `verb=" POST "` selects POST, and
`<mime:mimeXml part=" result "/>` selects the message's `result` part.

The independent matrix uses unmodified, digest-pinned HTTP and MIME schemas and
the corrected core WSDL schema. Source and both saved forms, detached operations,
provider examples, both message directions and real HTTP consumers share these
normalized component values. Prefix aliases and default extension namespaces are
semantically equivalent.
