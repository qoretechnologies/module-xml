# SOAP body-part selection

Copyright (C) 2026 Qore Technologies, s.r.o.

`BindingMessageBodyDescription::parts` is an optional list of part-name strings.
An omitted `soap:body parts` attribute remains `NOTHING`, while an explicitly
empty or XML-whitespace-only attribute becomes an empty list. XML whitespace is
collapsed before splitting names; character-reference TAB, CR and LF have the
same separator meaning as SPACE. Selection order is retained. Repeated names
raise `WSDL-ERROR`, and binding construction rejects names absent from the
selected abstract input/output message. Names refer to message parts, not their
referenced XML element names.

The omitted attribute selects **all** message parts, including those also bound
to a header, as required by WSDL 1.1 section 3.5. Only an explicit list partitions
parts between the Body and Header. `getBodyPartNames()` returns `NOTHING` for
this all-parts default.
`getBodyPartNames()` returns an empty list for an empty explicit selection.
Document and RPC serialization consume only selected parts. Document decoding,
retained XML decoding and RPC decoding use that selection and reject unselected
body values. A document body with no selected parts contains no body elements;
an RPC body retains its operation wrapper without accessors. Single-argument
inference applies only when selection is omitted. Explicitly selecting no parts
does not infer the message's sole argument.

For example, a binding can put a token in the Header and no parts in the Body:

```xml
<wsdl:input>
  <soap:body use="literal" parts=""/>
  <soap:header message="partner:Session" part="token" use="literal"/>
</wsdl:input>
```

Declared fault detail belongs to the fault's message. The normal output body's
part selection does not filter that detail.

`WSMessage::deserializeRpc()` accepts a string or list of selected part names.
Its optional `ignore_unknown` argument defaults to accepting unselected fields
only when an explicit selection is supplied, retaining the public partial-value
conversion behavior. SOAP binding decoding passes `False` so extra accessors
cannot disappear silently. The returned hash is keyed by WSDL part names.

Saved services reconstruct selections from retained WSDL. Standalone descriptions
retain the distinction between empty lists and omitted selections. Older saved
standalone descriptions that already discarded an empty attribute cannot recover
it from `NOTHING`; reconstruct from the original WSDL to restore that distinction.

The empty-body behavior follows WS-I Basic Profile R2213/R2214, and the part list
uses XML Schema list whitespace semantics. The pinned WSDL4J oracle distinguishes
omitted, empty and nonempty space-separated lists. Its SPACE-only tokenizer does
not normalize character-reference TAB/CR/LF, so those cases are verified separately
with the pinned XML Schema validator and normative list rules.

Literal, non-multipart serialization checks that every selected body part was
emitted. Missing required parts reject with `SOAP-SERIALIZATION-ERROR`; partial
header conversion still uses its explicit part projection.

When native decoding finds the same message part in both Body and Header, it
returns exactly `{"^body^": <part map>, "^headers^": <message/part map>}`.
This decision precedes flattening: even distinct flat keys can otherwise cause
message-container lookup to substitute the header value when reserializing the
body. Scalars, nil/empty records and selected wrappers retain their part keys.

SOAP serialization accepts both maps together, validates their hash types and
rejects extra top-level keys. Nonempty headers in both the map and the separate
header argument reject instead of silently choosing one source. Both directions,
SOAP versions, document/RPC styles and client/handler calls use the same path.
Messages without overlapping parts retain the documented legacy merge shape.

`SoapRequestDataProvider::getRequestTypeWithData()` describes explicit maps when
present. Its body uses the existing schema-checked message type. The header map
uses the same transport-level contract as the `soap_header` request option;
selected header parts are schema-checked during SOAP serialization, before I/O.
The static request/response types still describe the abstract message part map.
For example, send `{"^body^": {"order": order, "token": "body-token"},
"^headers^": {"OrderMessage": {"token": "header-token"}}}` or supply the body
part map with the separate `soap_header` request option.

Source and saved services apply the same standard default. WSDLs relying on
implicit removal of header-bound parts must add explicit body `parts` lists.
This follows [WSDL 1.1 section 3.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body).
