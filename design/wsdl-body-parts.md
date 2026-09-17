# Explicit SOAP body-part selection

Copyright (C) 2026 Qore Technologies, s.r.o.

`BindingMessageBodyDescription::parts` is an optional list of part-name strings.
An omitted `soap:body parts` attribute remains `NOTHING`, while an explicitly
empty or XML-whitespace-only attribute becomes an empty list. XML whitespace is
collapsed before splitting names; character-reference TAB, CR and LF have the
same separator meaning as SPACE. Selection order is retained. Repeated names
raise `WSDL-ERROR`, and binding construction rejects names absent from the
selected abstract input/output message. Names refer to message parts, not their
referenced XML element names.

An explicit list takes precedence over default body/header partitioning.
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
