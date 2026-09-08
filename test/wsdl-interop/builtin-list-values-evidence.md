# Builtin names, name lists and union values

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment implements datatype lexical and value rules. Document-level ID,
IDREF/key constraints and unparsed-entity declarations remain assigned to P5,
with SOAP DTD restrictions assigned to P7. Accepting an ENTITY token in a scalar
API does not establish that it names a declared unparsed entity in a document.

## Normative requirements and reproduced roots

XSD 1.0 Second Edition defines [NMTOKEN](https://www.w3.org/TR/xmlschema-2/#NMTOKEN),
[Name](https://www.w3.org/TR/xmlschema-2/#Name),
[NCName](https://www.w3.org/TR/xmlschema-2/#NCName) and their derivations using the
XML 1.0 Second Edition name productions. Its explicit normative reference is
[XML 1.0 Second Edition](https://www.w3.org/TR/2000/REC-xml-20001006), including
productions 4, 5 and 7 and Appendix B productions 85–89. The
[XSD errata](https://www.w3.org/2004/03/xmlschema-errata.html) do not replace that
reference with the broader XML Fifth Edition grammar. XML component/parser names
and XSD datatype values are separate constraints.

`Αλφα`, `中文`, a name followed by U+0301 and names containing U+00B7 are valid.
U+0370 and U+10000 are outside these datatype productions. Colon is allowed in
Name/NMTOKEN; NCName and its ID/IDREF/ENTITY derivatives exclude it. NMTOKEN can
start with a digit or combining character. No Unicode normalization is applied.

[NMTOKENS](https://www.w3.org/TR/xmlschema-2/#NMTOKENS),
[IDREFS](https://www.w3.org/TR/xmlschema-2/#IDREFS) and
[ENTITIES](https://www.w3.org/TR/xmlschema-2/#ENTITIES) are lists with collapsed
XML whitespace and inherited minimum length one. Items satisfy the corresponding
NMTOKEN/IDREF/ENTITY grammar. [Enumeration](https://www.w3.org/TR/xmlschema-2/#rf-enumeration)
compares ordered item values, while [pattern](https://www.w3.org/TR/xmlschema-2/#rf-pattern)
constrains lexical forms at the appropriate derivation step. The same XML name
classes define regex `\i` and `\c` in [Appendix F](https://www.w3.org/TR/xmlschema-2/#regexs).

On committed P3-16, all four initial regression cases fail: builtin list unions
compare enumeration by raw text, own list enumeration is not normalized, detached
providers omit list patterns/enumeration, and name/list-item grammar is not checked.
Regex name classes were limited to ASCII. The implementation now retains ordered
string-item identity for builtin lists, validates tokens, normalizes enumeration
through the base and preserves these rules in provider metadata and examples.
A corruption regression also rejects a builtin list substituted for an atomic
item descriptor; old compiled metadata accepted it. Public builtin lists remain
strings, and native user-defined lists retain their existing representation.

## Range provenance and independent boundaries

`xml10-second-name-ranges.json` is a numeric transcription of the five Appendix B
productions: BaseChar (202 ranges/singletons), Ideographic (3), CombiningChar (95),
Digit (15) and Extender (11), totaling 326. The downloaded normative source SHA-256
is `e5350fb462ada6babfc43d72263a955bddf78605180457c6e006886f60a89b67`.
The transcription selects each production's own table row using its `NT-` anchor;
it does not concatenate adjacent productions. Runtime tests are offline.

The boundary test independently constructs expected membership from that fixture.
The union of every range start/end and adjacent code point contains 1,009 distinct
non-whitespace code points. Bare and `A`-prefixed values for Name, NCName and
NMTOKEN give 6,054 documents. Every document is checked by libxml2 2.12.10 and
Xerces-J 2.12.2, plus schema serialization, schema deserialization and detached
provider conversion. Values and exact error categories are asserted. Additional
unit/binding cases cover XML whitespace, NUL, supplementary characters, colons,
repeated values, attributes, regular-expression escapes and generated examples.

## libxml2 builtin-list empty-value false positives

Both libxml2 2.12.10 (lxml 6.1.1) and private 2.15.4 accept `<value/>` against
an element of type NMTOKENS, IDREFS or ENTITIES, including a restriction of that
type. Qore's WSDL conversion and Xerces reject the empty list as required.
The private native reproducer uses `XmlDoc::validateSchema()`; logs are retained
in `/tmp/wsdl-p3-17-empty-builtin-private-final.log` with its `.qr` source.
The earlier deprecated-API probe remains separate historical evidence.

The root is visible in the pinned libxml2 2.15.4 source:

- `xmlschemastypes.c:850–874` constructs the three builtin lists and sets item
  types without an explicit minimum-length facet.
- `xmlschemas.c:24230–24320` validates list tokens with `len` initialized to zero;
  empty input exits the item loop and checks only available facets.
- `xmlschemas.c:23771–23776` notes that derived builtin types have no explicit
  facets; the general facet validator returns success for BASIC types.
- The separate NMTOKENS branch in `xmlschemastypes.c:2968` requires a positive
  item count, but the schema-validation list path above does not call it.

Source: [libxml2 v2.15.4 xmlschemas.c](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemas.c)
and [xmlschemastypes.c](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemastypes.c).
This is separate from the previously adjudicated empty-list enumeration compiler
error and from IDREF document-context differences.

The new binding matrix records exactly 24 libxml2 false positives: empty input
for `builtin-count` and `name-NMTOKENS`, three content models, two actual SOAP
bindings and two directions. The override requires those exact schema families,
empty text/attributes, an otherwise successful libxml2 verdict and no libxml2
diagnostics. Xerces must reject every one; Qore must reject with the expected
SOAP error. No output or consumer verdict is waived, and unexpected disagreements
or missing/duplicate cases fail. Upstream corpus files and pinned validator
artifacts are unchanged.

## Verification matrix

`test_builtin_list_values.py` contains 15 binding definitions: 45 schemas and
90 actual SOAP 1.1/1.2 contracts, 1,584 input and 828 emitted binding documents,
9,168 consumer results and 5,136 emitted/provider/example documents. All 7,548
binding/consumer documents plus the 6,054 boundary documents are assessed by
Xerces. libxml2 agrees except for the 24 precisely identified false positives.
Primitive family, ordered values and expanded names are checked in addition to
schema validity. ID/IDREF/ENTITY lexical-only unit coverage is not counted as
independently valid SOAP document coverage.

The Qore regression covers original/reconstructed schemas/providers, inherited
facets, optionality, examples, invalid declarations, metadata corruption, finite
choices, member reordering, native user-defined list equivalence and invalid
native scalar containers. Full test/build/audit evidence is recorded in
[EXECUTION.md](EXECUTION.md) and the P3-17 audit. P3 remains in progress.
