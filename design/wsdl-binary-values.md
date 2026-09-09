# WSDL binary lexical values

Copyright (C) 2026 Qore Technologies, s.r.o.

`xs:hexBinary` and `xs:base64Binary` represent octets. WSDL decoding returns a
native `binary`, including an empty binary for present empty XML content.
The conversion validates the complete XSD 1.0 lexical grammar before calling
Qore's native decoder. Invalid XML values raise `SOAP-DESERIALIZATION-ERROR`.

Hex accepts pairs of ASCII hexadecimal digits in either case. Leading and trailing
XML whitespace is collapsed; whitespace within a pair or between pairs rejects.
Base64 accepts XML whitespace between any encoding characters, including `=`.
After removing that whitespace, its length must be divisible by four, padding
must occur only at the end, and unused bits must be zero. Non-XML whitespace,
nonalphabet characters, URL-base64 substitutions and trailing garbage reject.
Encoded text is interpreted as characters even when its Qore string uses UTF-16.
There is no MIME line-length restriction or fixed lexical size limit.

Serialization preserves the existing input contract: native binary values are
octets, and strings are **raw bytes to encode**. String whitespace is part of those
bytes; the string's encoding is not changed before encoding. A UTF-8 and a UTF-16
string containing the same characters therefore produce different binary values.
Output uses lowercase hex or compact padded base64. Lowercase hex is valid XSD
text; this API does not promise XSD's uppercase canonical hex spelling.
Unrelated native categories reject with `SOAP-SERIALIZATION-ERROR`.

`XsdBinaryDataType("hexBinary")` and `XsdBinaryDataType("base64Binary")` accept
native binary or **encoded XML text**, validate it, and return exact octets.
This differs intentionally from the existing serializer's raw-string convention.
Use the provider to decode authored XML text before passing it to serialization:

```qore
%requires WSDL
XsdBinaryDataType encoded("base64Binary");
binary attachment = encoded.acceptsValue(" A A = = ");
@assert(attachment == <00>);
XsdBaseType base = new Namespaces({}).getBaseType("base64Binary");
@assert(base.serializeValue(new Namespaces({}), attachment, True) == "AA==");
@assert(base.serializeValue(new Namespaces({}), " a\tb ", True) == "IGEJYiA=");
AbstractDataProviderType optional = Serializable::deserialize(encoded.getOrNothingType().serialize());
@assert(optional.acceptsValue(NOTHING) == NOTHING);
@assert(optional.acceptsValue("") == binary());
```

Required providers distinguish omission (`MISSING-VALUE-ERROR`) from empty encoded
text (empty binary). Malformed encoded text and unrelated native categories raise
`RUNTIME-TYPE-ERROR`. Optional copies and serialized providers retain the encoding
and requiredness. Reconstruction rejects unknown encodings and nonboolean
optionality before changing state. Enclosing lists cannot bypass validation via
direct native type assignment. Interruption retains its category and a subsequent
conversion can reuse the provider.

The helpers keep no mutable shared state. Validation uses a fixed number of
linear character scans, without a backtracking expression over base64 quartets.
This avoids adding regex stack limits to large attachments. Local HTTP tests use
bounded request/response queues and exception-safe server teardown.

The executable checks are `test/wsdl-binary-values.qtest`,
`test/wsdl-binary-consumers.qtest` and `test/wsdl-interop/test_binary_values.py`.
The independent reference compares exact octets using Python decoding plus
canonical re-encoding to detect nonzero padding bits. Both SOAP binding versions
and directions, simple content, attributes, repeated elements, detached providers,
reconstruction and examples are covered. See
[validator evidence](../test/wsdl-interop/binary-values-evidence.md) for precisely
recorded libxml2 disagreements.
