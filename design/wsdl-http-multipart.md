# HTTP MIME entity trees

Copyright (C) 2026 Qore Technologies, s.r.o.

HTTP WSDL MIME representations retain a recursive declaration graph. Each `mime:part` describes one entity; its MIME declarations are alternatives. Multipart alternatives have local selectors `multipart:0`, `multipart:1`, and so on. Content and schema XML retain `content:partName` and `xml:partName`. Selection never enumerates combinations of child alternatives.

`BindingMessageDescription::getMimeFormats()` returns representation metadata. Calling `getMimeDescription(selector).getMimeParts()` exposes a multipart representation's child descriptions in WSDL declaration order. Graph validation rejects empty entity descriptions, contradictory metadata and cycles, including restored Serializable graphs. Shared acyclic descriptions are allowed.

A native multipart message has exactly one top-level key, `^mime^`, containing a `WsdlMimeEntityInfo` tree:

- A multipart node contains `parts`; its `root` is the root entity's WSDL declaration index, defaulting to zero.
- A leaf contains `value` and its selected `format`. Type-based `mime:content` leaves carry raw string/binary media; element-based content and `mime:mimeXml` use the shared XML part codec. Form values contain the complete abstract message map.
- A child may set `part` to its declaration index. During encoding, an omitted index uses the child list position. Decoded lists are normalized to declaration order.
- `content_type` carries the media type and parameters. `content_id` identifies a nested entity without angle brackets. Serialization generates missing child IDs and rejects duplicates within a multipart body.

Each declared entity receives exactly one value. Repeated uses of an abstract message part remain distinct tree nodes. Returned trees can be serialized again without flattening values or losing binary bytes. The writer emits the chosen root first and generates the related `boundary`, `start` and `type` parameters. Other parameters, including `start-info`, are retained. Stale framing parameters from a decoded value cannot override the current tree.

`WsdlMimeSelection` accepts a legacy format string or a `WsdlMimeSelectionInfo` tree. Child selections are keyed by declaration index, using list position unless `part` is explicit. `format` chooses a representation; `content_id` identifies a received entity. An explicit `wire_index` can identify an entity when a caller knows its peer's order and IDs are unavailable. This last selector is valid only for decoding. No default identity rule relies on received wire order.

The decoder builds candidate edges from identity, media and explicit selections before interpreting schema values. Candidate indexing uses selected IDs/positions, public WSDL part IDs and media components. Forced unique assignments are resolved across the bipartite entity/declaration graph. Incompatible, incomplete and ambiguous assignments fail. A schema failure never triggers a retry with a different representation.

Qore Mime provides multipart framing, transfer decoding and related-message output. XML validates entity headers and related root semantics through `WsdlMultipartHelper`. HTTP transport paths preserve the complete raw MIME body until the selected binding decodes it. SOAP attachment normalization uses the same reader but retains its separate SOAP value contract.

SoapClient call options and SoapHandler registrations carry recursive request/response choices. Choices are local to a call or registration and are never transmitted as private HTTP headers. The operation's scope restores thread-local selection state on success or failure.

`WsdlHttpMimeDataType` and SoapRequestDataProvider describe the concrete binding, validate complete values by serialization without I/O, and generate complete examples. Saved, soft and optional providers retain the same validator. Ordinary part fields remain available when the selected binding also offers direct representations. Abstract WSMessage provider types continue to describe the abstract message.

The Qore entity-tree suite covers source/saved/detached operations, schemas, binary and character values, media alternatives, repeated parts, invalid metadata, concurrent calls and provider consumers. The independent Python MIME peer verifies wire structure, transfer encodings, both HTTP directions and rejection/recovery behavior.
