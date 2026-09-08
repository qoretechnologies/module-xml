# List value and oracle diagnostic adjudication

Copyright (C) 2026 Qore Technologies, s.r.o.

The list matrices use XSD 1.0, Xerces-J 2.12.2 and libxml2 2.12.10.
[List datatypes](https://www.w3.org/TR/xmlschema-2/#list-datatypes) have ordered
atomic item values, fixed XML whitespace collapse, and patterns over the whole
list lexical form. SPACE, TAB, CR and LF delimit items; NBSP does not. Empty lists
are valid unless restricted. Native empty or whitespace-containing items cannot
be emitted as single items without changing the value.

[Enumeration](https://www.w3.org/TR/xmlschema-2/#rf-enumeration) literals map
through the base type. The current step's pattern need not match that spelling:
`01 +2` can enumerate the value serialized as `001 002`. Item order and exact
integer/decimal values remain significant. Same-step facets can have an empty
intersection: `enumeration="1 2"` with `length="1"` admits no instance.
The schema remains constructible; example generation reports `XSD-SAMPLE-ERROR`.

Two oracle issues are explicitly assessed:

- Xerces emits `FacetsContradict` as a **warning** for the empty intersection.
  Its `XSDAbstractTraverser.checkEnumerationAndLengthInconsistency()` also compares
  Java string length to the length facet for a list. Thus the valid two-item
  enumeration `1 2` with `length=2` produces the same warning. The
  [upstream implementation](https://github.com/apache/xerces2-j/blob/trunk/src/org/apache/xerces/impl/xs/traversers/XSDAbstractTraverser.java)
  calls `reportSchemaWarning`; the pinned JAR's `javap -p -c` output confirms it
  (`/tmp/wsdl-p3-08-xerces-abstract-traverser.txt`). The oracle harness previously
  threw warnings as errors and incorrectly reported these schemas invalid.
  Diagnostics now retain a separate ordered warning list on every schema/document
  result. Both schemas compile; document validation still rejects errors. Tests
  require these exact diagnostic categories and no document warnings.
- libxml2 rejects a valid empty-list enumeration with an internal error because
  its empty list has no allocated value. In
  [v2.12.10 xmlschemas.c](https://github.com/GNOME/libxml2/blob/v2.12.10/xmlschemas.c),
  `xmlSchemaCheckFacet()` treats null `facet->val` after successful base validation
  as a missing computed value (lines 17861–17864). `empty-enum` retains this exact
  compiler diagnostic, and Xerces checks every original and emitted document.
  Exact empty-list assertions remain mandatory. Other libxml2 compiler failures
  are test failures; no production verdict is waived.

The same libxml2 defect occurs when the empty list belongs to a union member.
P3-14 reproduces it with both lxml's libxml2 2.12.10 and the private libxml2 2.15.4.
In the latter, `xmlSchemaVCheckCVCSimpleType()` leaves its computed value null for
zero items (`xmlschemas.c`, list branch starting at line 24230), and
`xmlSchemaCheckFacet()` reports that successful empty value as uncomputed at
lines 18337–18340. `test_union_list_identity.py` requires the two precise
`SCHEMAP_INTERNAL` compiler diagnostics for this named case and reports the three
affected schemas and their unassessed document counts. It still requires every
Xerces schema/document verdict and every ordered primitive-value assertion.
No source schema is rewritten. All other libxml2 errors fail the matrix.

P3-14 also exposes libxml2's base64 lexical false positives: both 2.12.10 and
2.15.4 accept `!? ???` as a list of `base64Binary` values. The
[2.15.4 implementation](https://github.com/GNOME/libxml2/blob/v2.15.4/xmlschemastypes.c)
explicitly follows MIME decoding's tolerance for stray characters: both scanning
loops in the `XML_SCHEMAS_BASE64BINARY` branch ignore negative results from
`_xmlSchemaBase64Decode()`, and allocation copies only alphabet/padding characters.
The punctuation therefore becomes empty data. XSD 1.0
[base64Binary lexical rules](https://www.w3.org/TR/xmlschema-2/#base64Binary)
permit alphabet/padding characters and XML whitespace, excluding that punctuation.
Qore and Xerces reject the input. The matrix retains exactly 12 libxml2 false
positives across three content models, two bindings and two directions, verifies
the exact offending text/attribute, and independently rejects its tokens with
Python's strict base64 decoder. Consumer/output cases have no such disagreement.
Other mismatches still fail; these false positives are explicitly counted and
never used to relax Qore validation.

P3-15 exposes a Xerces-J 2.12.2 false negative when an enclosing union compares
a list of union-valued items to an atomic-item list. The item union is boolean/int;
`01 2` selects two decimal-derived values, as does `1.0 2.00` through the decimal
list alternative. XSD 1.0 [list values](https://www.w3.org/TR/xmlschema-2/#dt-list)
are ordered sequences of atomic values; integer and decimal share their primitive
value space. The two lists are therefore equal for enumeration. The single-item
case `01` versus `1.0` has the same issue. `1` selects a boolean and remains distinct.

The unmodified [2.12.2 source artifact](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar)
has SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`
(2,150,056 bytes). In `XSSimpleTypeDecl.java`, lines 1675–1708 require matching
primitive kinds before testing enumeration values. Lines 1882–1909 assign distinct
`LISTOFUNION_DT` and `LIST_DT` kinds, and `convertToPrimitiveKind()` at lines
3463–3479 leaves those kinds distinct. Even merging the kinds would leave another
representation issue: the type list contains one type per union item but only one
type for a homogeneous atomic-item list. Neither storage detail changes the XSD
list value space. `ValidatedInfo.isComparable()` contains the same distinction.

The new matrix records exactly 48 binding-document and 128 consumer/output false
negatives, all with `cvc-enumeration-valid` for the two exact lexical forms above.
libxml2 accepts these documents, and separate Python primitive-family/Decimal
assertions verify equal ordered values. All other Xerces verdicts remain mandatory,
including boolean distinctions, changed item order/value and malformed items.
The existing libxml2 empty-list compiler defect remains separately counted, with
Xerces and exact empty-value checks for those documents. No schema, pinned JAR or
production validation result is changed to accommodate either oracle defect.

The matrices retain original and reconstructed schemas/providers, atomic elements,
attributed simple content, attributes, repeated elements and generated examples.
They use actual SOAP 1.1/1.2 bindings and both request/response directions. Separate
Python comparisons verify ordered values independently of schema acceptance.
Original W3C files and the historical findings/adjudication report are unchanged.

Separating warning severity also exposes two existing namespace-oracle cases:
`declared-target-empty` and `declared-target-whitespace`. Xerces issues exactly one
`EmptyTargetNamespace` warning and constructs a schema, while Qore rejects both
with `WSDL-ERROR` as required by the nonempty target namespace rule. The reference
permission matrix now records that exact diagnostic without changing Qore's
expected rejection. Neither namespace acceptance nor warning suppression is added
to production. The other 27 reference cases retain their prior oracle verdicts;
`/tmp/wsdl-p3-08-reference-diagnostics.json` records the complete comparison.
