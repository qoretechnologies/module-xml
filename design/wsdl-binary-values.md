# WSDL binary lexical values

Copyright (C) 2026 Qore Technologies, s.r.o.

`xs:hexBinary` and `xs:base64Binary` represent octets. WSDL decoding returns a
native `binary`, including an empty binary for present empty XML content.
Patterned restrictions can return an `XsdBinaryValue` carrier to preserve the
required spelling. Callers must handle that object alternative instead of assuming
every restricted binary result is native bytes; `getBinaryValue()` returns its bytes.
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

Atomic binary serialization preserves the existing input contract: native binary values are
octets, and strings are **raw bytes to encode**. String whitespace is part of those
bytes; the string's encoding is not changed before encoding. A UTF-8 and a UTF-16
string containing the same characters therefore produce different binary values.
Output for raw bytes uses lowercase hex or compact padded base64. Lowercase hex is valid XSD
text; this API does not promise XSD's uppercase canonical hex spelling.
Unrelated native categories reject with `SOAP-SERIALIZATION-ERROR`.

`XsdBinaryDataType("hexBinary")` and `XsdBinaryDataType("base64Binary")` accept
native binary, **encoded XML text** or an `XsdBinaryValue`, validate it, and return exact octets.
This differs intentionally from the existing serializer's raw-string convention.
Union string inputs also represent encoded XML text so that decoded string
alternatives retain their selected identity on serialization. The union validates
text before invoking a binary member and uses an explicit carrier at that boundary.
Pass native binary to a union for byte content. For atomic binary serialization,
use the provider to decode authored XML text first:

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
XsdBinaryValue retained("base64Binary", "A A = =");
@assert(base.serializeValue(new Namespaces({}), retained, True) == "A A = =");
@assert(Serializable::deserialize(retained.serialize()).getBinaryValue() == <00>);
```

Required providers distinguish omission (`MISSING-VALUE-ERROR`) from empty encoded
text (empty binary). Malformed encoded text and unrelated native categories raise
`RUNTIME-TYPE-ERROR`. Optional copies and serialized providers retain the encoding
and requiredness. Reconstruction rejects unknown encodings and nonboolean
optionality before changing state. Enclosing lists cannot bypass validation via
direct native type assignment. Interruption retains its category and a subsequent
conversion can reuse the provider.

`XsdBinaryValue` stores an explicit encoding, normalized lexical text and decoded
octets. Construction validates the text after the builtin's whitespace processing;
that spelling remains available through `getLexicalValue()`. It has no mutator,
and returned text/bytes use Qore's copy-on-write semantics. Reconstruction validates
the encoding and text and derives the byte cache again. A mismatched primitive
encoding rejects. Union patterns apply after the selected leaf member's whitespace
processing, including through nested unions. Binary members collapse XML whitespace;
internal base64 spaces and hex case remain available to lexical patterns.

Binary restrictions apply lexical patterns at every derivation step. Length,
minimum length and maximum length count decoded octets. Enumeration and fixed
values compare octets: `FF` and `ff` are equal hex values, and `AA==` and `A A = =`
are equal base64 values. Binary families remain distinct primitive identities in
unions. Lists compare ordered item values and reject empty or whitespace-containing
item spellings that cannot represent one XML list item.

`XsdBinaryFacetInfo` describes the builtin, local patterns, enumeration and octet
counts. `XsdBinaryRestrictionDataType` validates these facets and its inherited
base. It returns native bytes unless its own or inherited pattern requires a
carrier; its category metadata exposes that object alternative. Optional and
reconstructed providers retain the same checks. `XsdBinaryDataField` uses octet
keys for scalar and repeated finite choices and constructs complete replacements
before changing state. Native byte display uses hex; carriers display their
retained spelling. Every underlying restriction still applies to creatable fields.

Samples are checked against the entire restriction chain. Binary construction
tries the default, enumeration spellings, bounded pattern repetition minima and
bounded zero-byte candidates. Pattern repetition minima include complete encoding
units, so `[A-F]+` can yield `AA` instead of an invalid single hex digit. The
existing generated-example size limit applies before allocating bytes. Union
sample construction decodes enumeration and pattern text before retrying
serialization, preserving the selected primitive family and any binary carrier.
When no candidate satisfies all constraints, generation raises `XSD-SAMPLE-ERROR`.

The helpers keep no mutable shared state. Validation uses a fixed number of
linear character scans, without a backtracking expression over base64 quartets.
This avoids adding regex stack limits to large attachments. Local HTTP tests use
bounded request/response queues and exception-safe server teardown.

The executable checks are `test/wsdl-binary-values.qtest`,
`test/wsdl-binary-facets.qtest`, `test/wsdl-binary-consumers.qtest`,
`test/wsdl-interop/test_binary_values.py` and `test/wsdl-interop/test_binary_facets.py`.
The independent reference compares exact octets using Python decoding plus
canonical re-encoding to detect nonzero padding bits. Both SOAP binding versions
and directions, simple content, attributes, repeated elements, detached providers,
reconstruction and examples are covered. See
[validator evidence](../test/wsdl-interop/binary-values-evidence.md) for precisely
recorded libxml2 disagreements.
