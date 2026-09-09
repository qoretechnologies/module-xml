# Binary lexical conversion evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The normative requirements are XSD 1.0 Second Edition
[hexBinary §3.2.15](https://www.w3.org/TR/xmlschema-2/#hexBinary),
[base64Binary §3.2.16](https://www.w3.org/TR/xmlschema-2/#base64Binary) and the fixed
`whiteSpace=collapse` facet. Binary values are octet sequences. Hex requires digit
pairs. Base64 permits XML whitespace between characters, requires complete
four-character groups after whitespace removal, and constrains the final data
character to `[AQgw]` before `==` or `[AEIMQUYcgkosw048]` before `=`. Arbitrary
MIME punctuation tolerance is not part of this grammar.

The previous WSDL path delegated to Qore's general decoder. In `lib/QoreLib.cpp`,
`parse_base64_intern()` stops when it first encounters padding and does not check
the remaining padding or unused bits. `get_base64_value()` handles CR/LF but not
SPACE/TAB. Consequently `AB==`, `AAB=` and `AA===` were accepted, while valid
`A A = =` rejected. WSDL now validates and compacts XSD lexical text before native
decoding. This is an XML datatype fix; the general Qore decoder is unchanged.

Separately, WSDL applied XML whitespace collapse to serializer strings before
encoding their raw bytes. `" a\tb "` became `"a b"`; the output changed from the
required hex `2061096220` / base64 `IGEJYiA=` to `612062` / `YSBi`. Builtin and
derived binary serialization now preserve original string bytes. Provider input
strings continue to mean encoded XML text. Unrelated native categories no longer
become empty octets merely because their generic `.empty()` predicate is true.

The independent Python reference validates hex digit pairs. For base64 it uses
strict Python decoding and requires independent canonical re-encoding to equal
the whitespace-free input, detecting unused-bit aliases. The matrix covers every
last-data-character alternative before one and two padding characters,
empty/whitespace input, malformed padding/alphabet, all 256 octets, actual SOAP
1.1/1.2 contracts in both directions, simple content and attributes, repeated
elements, detached/reconstructed providers and generated examples. Qore tests
also cover 64 KiB values, NUL and non-XML controls, UTF-8/UTF-16/ISO-8859-1 strings,
native category rejection, list/union conversion and cancellation/recovery.

`binary-validator-defects.json` records exactly three normative/oracle triples.
Both libxml2 2.12.10 and private 2.15.4 accept invalid `AA==!`, `!? ???` and
`AA==` followed by NBSP; Xerces-J 2.12.2 and Qore reject them. These are additional
reductions of the already adjudicated MIME-tolerance root cause described in
[list adjudication](list-values-adjudication.md), not a new allowed lexical form.
In both libxml2 sources, `XML_SCHEMAS_BASE64BINARY` in `xmlschemastypes.c` ignores
characters whose `_xmlSchemaBase64Decode()` result is negative. The surrounding
comment explicitly cites RFC 2045's permissive MIME decoding. Padding positions
and bits are checked correctly in these libxml2 versions.

The binding test requires exactly 36 libxml2 false positives across the three
authored values, three content models, two versions and two directions. Xerces has
zero disagreements. All generated/reconstructed outputs validate in both oracles;
every Qore rejection and exact-byte assertion remains mandatory. Native private
libxml2 reproductions can be run separately:

```sh
qore -b --enable-debug test/wsdl-interop/calendar-validator.qr \
  test/wsdl-interop/binary-validator-defects.json
```

This generic scalar diagnostic reports three `valid: true` results with empty
stderr; its successful exit means execution completed, not that these inputs are
normatively valid. Original W3C fixtures, hashes and historical findings are
unchanged. Full binary facet/choice/collection identity acceptance remains in P3;
this increment establishes the lexical/native/provider conversion boundary.
