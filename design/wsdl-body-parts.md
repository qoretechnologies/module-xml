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

Document request routing includes the wire names of selected type-based parts as
well as admitted element declarations. For example, an `orderId` part declared
with `type="xs:string"` can dispatch from its `orderId` body element when the SOAP
action is omitted. Explicit body selection excludes unselected type-part names
from registration. Source/saved services and detached operations derive these
names from their binding descriptions; normal body validation still applies.

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

Serialization accepts, for a single *selected* part, the bare value that decoding
returns for it. Decoding already returns a single body part's value directly, and
that documented shape is unchanged; what was missing was the matching acceptance on
the way back out. The count that matters is the number of selected parts, not the
number of message parts: a message can carry more parts than its body selects, such
as a header-bound part, and a binding with `parts="body"` over a two-part message
previously sent the bare value past the legacy single-argument branch and into part
matching, which rejected it.

`serializeDocument()` therefore wraps a bare scalar as the one selected part, as it
already did for a bare retained XML value, and `serializeRpc()` does the same for a
single RPC parameter instead of failing with `RUNTIME-TYPE-ERROR` inside part
conversion. `serializeRpc()` rejects a bare value when more than one part is selected,
since it cannot know which part the value belongs to. Together these make a decoded
message re-encodable through the operation that produced it.

## RPC part accessors

A received RPC message has one accessor per selected part inside its operation wrapper:

- **Qualification:** the accessor of a type part in a literal message has no namespace (WS-I Basic Profile R2735);
  one qualified by a prefix or by a default namespace declaration raises `SOAP-DESERIALIZATION-ERROR`. An element
  part's accessor is its element, with the element's own namespace. The SOAP encodings leave the qualification of
  accessors open (SOAP 1.1 section 7.1; the SOAP 1.2 Primer qualifies them), so encoded accessors may be qualified.
- **Omitted accessors:** an omitted type-part accessor is an absent value (`NOTHING`) whatever its type. SOAP 1.1 section
  5.1 and SOAP 1.2 Part 2 section 3.1.3 define this for encoded messages; literal messages follow the same rule
  (decided 2026-09-25), which accepts services that leave out optional parameters.
- **Empty accessors:** an empty accessor is an empty value, so `<name/>` is an empty string and an empty `xsd:int`
  accessor is rejected.

The qualification check uses the expanded names of the wrapper's children, before prefixes are removed for part
matching.
