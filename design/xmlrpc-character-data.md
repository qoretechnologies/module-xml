# XML-RPC character data

Copyright (C) 2026 Qore Technologies, s.r.o.

XML-RPC strings and struct names preserve XML 1.0 character data. Serialization
escapes markup and writes carriage returns as `&#13;`, because literal carriage
returns are normalized by an XML parser. An empty struct name remains empty and
is distinct from the ordinary key `!!empty-hash-key!!`. Input collects adjacent
text and CDATA nodes, ignores comments and processing instructions, and rejects
nested elements in a scalar string or member name.

Untyped values containing character data are strings, including whitespace-only
values. Whitespace before a typed child is formatting only if every character is
XML whitespace. The complete `<value>` reader is shared by arrays, structs,
parameters and responses so empty values cannot consume a following sibling.
The historical empty-value representation remains `NOTHING` for both `<value/>`
and `<value></value>`; explicitly typed empty strings remain strings. Duplicate
struct keys retain the last value and release the replaced value. Qore hash keys
are NUL-terminated; arbitrary byte keys are outside that hash representation.

Document conversion checks trailing input before returning a value. Malformed XML
raises `PARSE-XML-EXCEPTION`; invalid XML-RPC structure raises `PARSE-XMLRPC-ERROR`.
Characters excluded by XML 1.0 raise `XMLRPC-SERIALIZATION-ERROR` during generation,
including when numeric references are requested. Encoding conversion retains its
own error category. Arbitrary bytes use XML-RPC base64 through Qore binary values.

ASCII-incompatible output encodings are assembled as UTF-8 and converted once
into the requested encoding. The XML declaration names the final encoding.
String, member-name, method-name and fault-string output use the same character
validation and escaping helper. Cancellation is checked during character scans,
collection traversal and reader advances; scoped holders release partial results.

The full signed 32-bit range, including `-2147483648`, uses the integer wire type.
Larger integers retain the existing string serialization policy. This change does
not redefine the module's existing numeric/date extensions as strict XML-RPC
conformance. Legacy encoding wrappers use the same output path and retain all
arguments after their encoding parameter.

```qore
%modern
%requires xml
hash<auto> customer = {"": "unnamed", "address": "First line\r\nSecond line"};
string request = make_xmlrpc_call("customer.update", (customer,), 0, "UTF-16LE");
@assert(parse_xmlrpc_call(request).params[0] == customer);
```

`test/xmlrpc-text.qtest` covers character data, encodings, negative cases,
collection boundaries, replacement ownership, cancellation and recovery.
`test/wsdl-interop/test_xmlrpc_text.py` uses independent Expat/XML-RPC decoding
and actual HTTP client/server exchanges. The CPython marshaller's literal-CR
loss has a separate reduction; authored incoming fixtures preserve CR explicitly.

References: [XML-RPC specification](https://xmlrpc.com/spec.md),
[XML 1.0 line-end normalization](https://www.w3.org/TR/REC-xml/#sec-line-ends),
[XML character production](https://www.w3.org/TR/REC-xml/#charsets).
