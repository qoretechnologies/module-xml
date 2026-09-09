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
unchanged. P3-27 established the lexical/native/provider conversion boundary.

## P3-28 binary facets and collections

XSD [length §4.3.1](https://www.w3.org/TR/xmlschema-2/#rf-length) counts binary
octets, [pattern §4.3.4](https://www.w3.org/TR/xmlschema-2/#rf-pattern) constrains
lexical text, and [enumeration §4.3.5](https://www.w3.org/TR/xmlschema-2/#rf-enumeration)
compares values. Enumeration literals must belong to the base type; they need not
use the spelling required by a pattern introduced in the same restriction.
For example, hex enumeration `ff` with own pattern `FF` accepts `FF`.

The previous generic facet path compared decoded binary to authored strings and
called unsupported `string(binary)` for patterns. The two hex reductions also
reproduce at `6218d07`, before P3-27. Spaced base64 previously stopped earlier in
the decoder; fixing that decoder exposed the same pattern-conversion defect.
Binary restrictions now validate encoded text and octet values separately.
An immutable `XsdBinaryValue` retains the spelling needed by a pattern, while
ordinary values remain native bytes. Detached providers enforce the same chain.
Fields and fixed attributes compare octets; lists preserve item order, and unions
retain distinct hex/base64 primitive identities.

The first independent facet matrix exposed an example generator returning the
one-character pattern sample `A` for `[A-F]+`, which is incomplete hex. Binary
sample construction now considers complete encoding units and validates every
candidate. The union matrix then exposed generic example selection replacing a
decoded binary carrier with an enumeration string. Serializing that string as raw
bytes changed the selected value. Union examples now decode candidate text before
checking serialization.

A further independent reduction rejected the initial outer-whitespace carrier
behavior. XSD [whiteSpace §4.3.6](https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace)
delegates normalization to the selected member. Both validators correctly reject
binary union pattern ` FF ` even for input ` FF `, since the selected binary
member collapses the input to `FF`. The union trial now propagates the selected
leaf's normalization through nested unions before applying union-owned facets.
This also fixes normalizedString, token, numeric and list member patterns. The
two older Qore-only union/list tests that expected a double-space pattern to accept
were incorrect; they now require rejection and `XSD-SAMPLE-ERROR` for that empty
lexical intersection. New positive tests check all three whitespace modes and
continued conversion after rejection. Binary carriers retain normalized text.

Audit traced an implicit binary union serialization boundary: atomic binary
serializers interpret strings as raw bytes, while union strings retain XML lexical
values to preserve member selection. Applying the raw-string convention to unions
broke the existing HTTP round-trip of string alternative `AB==`. The final change
explicitly validates union text as encoded binary before invoking that member's
serializer. Malformed binary text can then select a later string member, and
valid `41` selects hex octet 65 without an intermediate double encoding. Native
binary remains the unambiguous byte input. Original/reconstructed schemas test both
encodings, restrictions and fallback; the HTTP regression keeps `AB==` as a string.

`test_binary_facets.py` compares exact Python bytes and primitive identities
through both actual bindings and directions, content/attribute/repeated models,
original/reconstructed element and message providers, and generated examples.
Its atomic/list/union facet matrices require agreement from both pinned validators;
the MIME-tolerance exceptions above apply only to the separate lexical matrix.
`coverage.py` independently checks binary octets, including lists, and negative
unit cases prove that changed bytes, invalid padding and ignored punctuation fail.
The four original W3C binary element/attribute families add 28 message directions
to the strict selection without changing original sources or their adjudication.
