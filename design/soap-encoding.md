# SOAP encoding

Copyright (C) 2026 Qore Technologies, s.r.o.

This document describes how the WSDL module decodes and encodes `use="encoded"` message parts: the SOAP 1.1
section 5 rules and SOAP 1.2 Encoding (SOAP 1.2 Part 2 section 3).

## Encoding style

A part's `soap:body` or `soap:header` `encodingStyle` is a URI list whose most specific URI comes first. The
first of the SOAP 1.1 encoding (`http://schemas.xmlsoap.org/soap/encoding/`) and SOAP 1.2 Encoding
(`http://www.w3.org/2003/05/soap-encoding`) that the list names selects the rules. Without either, including
when no style is declared, SOAP 1.1 encoding applies as it always has. Encoded output writes the selected URI as
the wrapper's `encodingStyle`. Before P8-03 every encoded body was written with the SOAP 1.1 URI, even where a
SOAP 1.2 binding declared SOAP 1.2 Encoding.

## Structs

SOAP encoding distinguishes a struct's members by name alone (SOAP 1.1 section 5.4.1, SOAP 1.2 Part 2 section
2.3). An encoded struct whose distinct members arrive in another order than the schema's sequence is matched
after putting them in declared order. The W3C SOAP 1.2 test collection sends `varInt`, `varFloat`, `varString`
against the SOAPBuilders schema's `varString` first. Repeated member names are not a struct and keep their
order, and literal content keeps its declared order.

## Reference context

An encoded Body is decoded against a reference context built by `SoapBinding::processMultiRef()`:

- Every Body child that carries an unqualified `id` attribute is an independent element: a multi-reference value
  (SOAP 1.1 section 5.1, rule 2). The element name is not significant, so `multiRef`, `number` or any other name
  works. `parse_xml()` delivers consecutive same-named siblings as a list under one key, so each list member is
  examined individually.
- The `id` must be an XML `NCName`, and an id may be used only once.
- SOAP encoding metadata on an independent element is consumed before type conversion sees the value:
  `SOAP-ENC:root` must be `0` or `1`, and `SOAP-ENV:encodingStyle`, an ordered list of URIs, must include the
  SOAP 1.1 encoding URI. More specific URIs may precede it. Attributes are matched by expanded name in the
  element's namespace scope, so any prefix works. All other attributes remain instance data.
- The remaining Body children are the serialization roots, such as the RPC wrapper.
- An embedded accessor may carry the `id` itself: rule 8 of section 5.1 allows it for string and byte-array
  values, whose other accessors are then empty elements with `href`. Its `id` is consumed like an independent
  element's and shares the same id space. Values of other types that a sender serializes in place are accepted
  the same way, and the graph checks below cover them too.

Only a same-document fragment reference (`href="#id"`) names a value in the message. A multipart message replaces
`cid:` references to its MIME parts before conversion. Any other reference, such as the `http:` reference of the
Note's section 5.4.1 example, is outside the message and raises `SOAP-DESERIALIZATION-ERROR`. External values are
never retrieved.

## Graph checks

Before any value is converted, `SoapEncodedReferenceHelper::checkGraph()` collects every fragment reference in
the roots and in the independent elements:

- a reference that names no independent element raises `INVALID-REFERENCE`;
- a reference cycle raises `SOAP-DESERIALIZATION-ERROR`. The search is iterative, so deep graphs cannot exhaust
  the stack. Plain Qore values cannot represent a cyclic graph, so a cycle is rejected instead of looping.

Shared references, where several accessors name one independent element, are allowed. Each accessor decodes to
an equal copy of the value.

Accessors resolve references lazily through `XsdData::getValue()` at each conversion site, including array
members, which can themselves be accessors to independent elements.

## Type names

- SOAP 1.1 section 5.2.1 names every builtin simple type in the encoding namespace as well: `SOAP-ENC:int`,
  `SOAP-ENC:string` and so on only add the `id` and `href` reference attributes. An explicit `xsi:type` in the
  encoding namespace therefore selects the corresponding XML Schema builtin type.
- The same names are declared types: a part or element of type `SOAP-ENC:string` has the builtin `xsd:string`
  type. Section 5.2.3's `SOAP-ENC:base64` restricts `xsd:base64Binary`, as a declared type and as an explicit
  `xsi:type`.
- SOAP 1.1 section 5.4.2 lets an array accessor name the generic `SOAP-ENC:Array` together with
  `SOAP-ENC:arrayType`, even where the schema declares a type derived from it. An explicit `SOAP-ENC:Array`
  keeps the declared array type. It cannot replace a type that is not an encoded array.
- `SOAP-ENC:Array` as a declared type is the generic array (below). Other types of the encoding schema, such as
  `SOAP-ENC:Struct`, are not provided; a part that names one fails with `WSDL-ERROR`.

## Arrays

`XsdArrayType` parses both the declared `wsdl:arrayType` and each instance's `SOAP-ENC:arrayType` with one parser
that follows the SOAP 1.1 section 5.4.2 grammar: `atype = QName *(rank)` and `asize = "[" #length "]"`. A shape is
the item QName, the ranks of the nested array levels that `atype` names (innermost first), the array's own rank,
and its asserted lengths, which are either all present or all absent. `xsd:int[,]` is one rank-2 array;
`xsd:int[][]` is a rank-1 array whose members are `int[]` arrays. The public `dimensions` member is the nesting
depth of the decoded Qore list: 2 for both of those.

A declared `SOAP-ENC:Array` is the generic array. It has no declared item type or shape: each instance's
`SOAP-ENC:arrayType` supplies both and is therefore required.

### Decoding

Each array level is decoded against the instance's own `arrayType`, or the declared one when absent:

- The instance's item QName is resolved in the instance's namespace scope: an XML Schema or encoding-namespace
  builtin, a nested `SOAP-ENC:Array`, or a schema type. It must be the declared item type or a type that can
  substitute for it; a nested level is checked against the item type of the level that contains it. A
  generic array accepts any known type. An unknown type or an incompatible one is an error.
- Members are the element children in document order. Their names are not significant, so the result keeps the
  qorelanguage/qore#2899 representation: when every member shares one element name, the value is
  `{local name: list}`; otherwise it is a plain list. Prefixes and the `{uri}` form of expanded literal
  documents are both reduced to the local name.
- A rank-n level with asserted lengths holds its members in row-major order and is reshaped into nested lists.
  Without lengths, members are nested rows, the form this module produced before P8.
- `SOAP-ENC:offset` (section 5.4.2.1) places the first transmitted member. `SOAP-ENC:position` (section 5.4.2.2)
  places an individual member, and is read from the member accessor even when that accessor refers to an
  independent element. Untransmitted members and `xsi:nil` members are `NOTHING`. A position outside the asserted
  size, a position used twice or more members than the size are errors. A single bare index, such as
  `offset="0"`, is accepted for rank 1.
- Asserted sizes can exceed the transmitted members, so the member slots a level allocates are bounded by
  `XsdEncodedArrayHelper::MaxSlots` (1,048,576). P8-06 makes limits explicit and configurable.
- Java peers such as Apache Axis send a rank-n declaration (`string[,]`) as a jagged array of arrays
  (`xsd:string[][2]`). That form is accepted when the decoded value is rectangular. Any other mismatch between
  the instance and the declared shape is an error.
- In an array of `xsd:anyType`, such as the Note's `xsd:ur-type[4]`, a member without `xsi:type` whose element
  name is a type of the encoding schema has that type (section 5.1 rule 3(c)): the encoding schema declares an
  element for each of its types for this purpose. `<SOAP-ENC:int>12345</SOAP-ENC:int>` decodes as an int. An
  explicit `xsi:type` takes precedence. RPC array parts therefore keep their members' prefixes for the array
  decoder; other parts' child names are still reduced to local names.
- With `preserve_types`, a member whose type differs from the declared item type, whether the instance
  `arrayType` or an element name selected it, is retained as a `^type^`/`^val^` wrapper, like an `xsi:type`
  selection. Encoding writes the wrapper's type as the member's `xsi:type`. Without it, a generic array's struct
  members, whose type only the instance named, re-encode as `xsd:anyType` content.

### Encoding

- A rank-1 level keeps `atype[]` (no asserted quantity, which section 5.4.2 permits).
- A rank-n level requires a rectangular nested list. It is written as row-major members with the lengths
  asserted, such as `xsd:int[2,3]`. A ragged value is rejected with a pointer to jagged types.
- Members of a jagged level are arrays with their own `SOAP-ENC:arrayType` and `xsi:type="SOAP-ENC:Array"`.
- `NOTHING` members are written as `xsi:nil="true"`.
- A `{name: list}` value names its members `SOAP-ENC:name`, as since #2899; a plain list names them `item`. A
  single RPC array part whose members carry the part's own name (Axis's convention) decodes to a
  `{part name: list}` value that serialization reads as the part map, so those members are renamed `item` on
  re-encoding. Member names are not significant, and the data is unchanged.
- An element whose type is an encoded array takes a list as its one value (`hasNativeListValue()`), not as
  repeated occurrences.
- The generic array infers the shape from the native value, whose nested lists are arrays. A rectangular
  nesting without empty dimensions is a rank-n array, such as `xsd:anyType[2,3]`. Otherwise every list member
  is an array of one common shape, and the level is jagged, such as `xsd:anyType[][]`, with absent members
  written as nil. Scalar and list members cannot be mixed, and jagged members of different shapes are rejected.
  Members are `xsd:anyType` values with their own `xsi:type`.

## Type annotations

An encoded value carries `xsi:type`. A named simple type that restricts another writes its own name there, such
as `xsi:type="ns1:Color"` for an enumeration of strings. Before P8-02d it wrote the base type's name, which is not
a valid annotation: `xsi:type` must name the declared type or one derived from it. A receiver, including this
module, rejected such parts and array members. A union, and a restriction of one, keeps naming the member type
that holds the value, because a member type counts as derived from the union (XML Schema 1.0 section 3.14.6,
clause 2.2.4). A list writes no `xsi:type`. Element declarations continue to write their declared type
themselves.

## SOAP 1.1 Note examples

`test/soap11-note-examples.qtest` runs the 27 instance examples of the SOAP 1.1 Note's section 5
(`test/wsdl-interop/encoded-corpus/soap11-note.json`) through the rpc/encoded operations of
`encoded-corpus/soap11-note.wsdl`. 24 decode to the values the Note describes. Three are rejected: example 21
refers outside the message; example 28's `array-1` asserts two members and transmits three; and example 34's
`arrayType="Order[2]"` has no prefix while no default namespace is in scope. Examples 17 and 37 are not
well-formed as published.

## SOAP 1.2 Encoding

### Reference graph

SOAP 1.2 has no independent elements. A multi-reference value appears once where it occurs, with `enc:id`, and
other edges to it are empty elements with `enc:ref` (section 3.1.5). Identifiers are envelope-wide: the W3C
collection's T57 refers from the Body to a value in a header block. `SoapEncodedReferenceHelper::collect12()`
therefore walks the Header and Body before either is converted:

- Only elements in the scope of an `encodingStyle` that names SOAP 1.2 Encoding carry encoding metadata. An
  `enc:id` elsewhere is not an identifier, so a reference to it is missing (section 3.1.1).
- `enc:id` must be an `NCName` and unique; a repeated id raises `enc:DuplicateID`. Each identified element is
  registered where it appears. `enc:ref` becomes an internal marker that `XsdData::getValue()` resolves at each
  conversion site, as SOAP 1.1 `href` references are resolved. A reference to no id raises `enc:MissingID`.
- An element must not carry both `enc:id` and `enc:ref` (section 3.1.5.3). A reference element with content of
  its own is rejected, since its edge ends at the referenced node. Reference cycles are rejected as for SOAP 1.1,
  because plain Qore values cannot represent them.
- `enc:nodeType` must be `simple`, `struct` or `array` (section 3.1.7) and must fit its element: a simple value
  has no child elements, and a struct's members have distinct names.
- SOAP 1.2 `encodingStyle` attributes are consumed as metadata. A Body element scoped with an encoding that is
  neither SOAP 1.2 or SOAP 1.1 encoding nor `http://www.w3.org/2003/05/soap-envelope/encoding/none` raises
  `env:DataEncodingUnknown` (SOAP 1.2 Part 1 section 5.4.6, the collection's XMLP-9).

### Arrays

The rules selected for a part are kept in a thread-local scope (`EncodingRules`) while its value is converted,
so `XsdArrayType` reads and writes the matching array form. Outside SOAP messages, such as a literal element of
an encoded array type, the SOAP 1.1 form is kept. Array types are still declared the WSDL 1.1 way, as
`SOAP-ENC:Array` restrictions with `wsdl:arrayType`.

- **Decoding** (sections 3.1.3, 3.1.4 and 3.1.6):
  - `enc:itemType` names the members' type unless a member has `xsi:type`. It is resolved and checked against
    the declared item type like a SOAP 1.1 item QName. Without it the declared item type applies, or
    `xsd:anyType` for the generic array.
  - `enc:arraySize` is `("*" | n) (whitespace n)*`, and `*` is its default. The number of extents must equal
    the declared rank. Only the first extent may be `*`, which the member count then determines; members that
    do not fill whole rows are an error (the collection's T61 puts `*` second).
  - Members are in row-major order. SOAP 1.2 has no partial or sparse arrays, so omitted trailing members are
    `NOTHING`, and more members than the extents allow is an error. `xsi:nil` members are `NOTHING`.
  - A jagged level's members are arrays with their own attributes.
- **Encoding**: `enc:arraySize` lists every extent, such as `"2 3"`, and `enc:itemType` names the declared item
  type; a jagged level names none. Member names are unqualified: `item`, or the #2899 key. The envelope
  declares the `enc` prefix.

### Faults

These errors are `SOAP-DESERIALIZATION-ERROR` exceptions whose argument is a `hash<SoapFaultOptions>` naming the
SOAP 1.2 code or subcodes. `SoapHandler` answers with `env:Sender` and the subcode (HTTP 400), or with
`env:DataEncodingUnknown` (HTTP 500). SOAP 1.1 has no subcodes and keeps its Client code.

## SOAP 1.2 RPC Representation

SOAP 1.2 Part 2 section 4 applies to SOAP 1.2 RPC-style bindings whose parts use SOAP 1.2 Encoding
(`SoapBinding::usesSoap12RpcRepresentation()`). The representation is defined over the SOAP Data Model, which
SOAP 1.2 Encoding serializes. SOAP 1.2 rpc/literal bindings are unchanged: peers such as CXF expect only the
WSDL's parts.

- **Return value.** `WSOperation::getReturnPartName()` names the output part that holds the return value. With
  WSDL 1.1's `parameterOrder`, which operations now retain, it is the output part the list omits (section
  2.4.6), and several omitted parts leave it undetermined. Without one, it is the part named `return`, or else a
  single output part. An operation whose output parts are all out parameters, like the collection's
  `echoStructAsSimpleTypes`, is void.
- **`rpc:result`** (section 4.2.2). A non-void response written by this module names the return accessor in
  `rpc:result`, as its first member. A void response, or one without the return value, has none. When
  decoding, `rpc:result` names the edge that holds the return value, whatever its name: that edge becomes the
  return part. A name that is no edge, a void operation, a second `rpc:result`, or a named edge beside the return
  part's own accessor is an error. A response without `rpc:result` is read by part names.
- **One child** (section 4.2.3). With SOAP Encoding the RPC struct is the Body's only child.
- **Faults** (section 4.4). Argument conversion errors carry `env:Sender` with `rpc:BadArguments`, unless a
  more specific encoding subcode such as `enc:MissingID` applies. `SoapHandler` answers an unknown procedure
  with `rpc:ProcedureNotPresent` when it serves operations that use the representation.

## Missing parameters

An encoded RPC parameter that is absent, or present with `xsi:nil`, is an edge without a node (SOAP 1.2 Part 2
section 3.1.3) and decodes as `NOTHING` in either SOAP version. An explicit `NOTHING` is written as a nil
accessor. Before P8-04 both were read and written as an empty value, so `NOTHING` and `""` could not be told
apart. The collection's `isNil` test (T77) relies on this.

## Appendix B names

`WSDLLib::toXmlName()` maps an application-defined name to an XML name by the rules of SOAP 1.2 Part 2
Appendix B.1:
- `_x` becomes `_x005F_x`;
- a leading `xml` in any capitalization has its first letter escaped;
- every character that XML names cannot hold becomes `_xHHHH_`, with six hex digits beyond the Basic
  Multilingual Plane.

Character classes are those of Namespaces in XML 1.0 (XML 1.0 Second Edition), as the appendix's examples require
(Tagalog and Cherokee letters are escaped). `WSDLLib::fromXmlName()` reverses the mapping. WSDL-described
operations and parts already have XML names, so the module applies it nowhere implicitly; applications that
derive method or parameter names from program identifiers use it.

## W3C SOAP 1.2 test collection

`test/soap12-collection.qtest` sends each Node A request of the collection's encoding and RPC tests to a
`SoapHandler` echo service for `encoded-corpus/w3c-soap12.wsdl`, and compares the reply with Node C:

- **Faults:** the same code, and the collection's subcodes where it lists any. Where it lists none,
  `rpc:BadArguments` is also accepted, since section 4.4 requires it for argument errors that the collection's
  samples show as a bare `env:Sender`.
- **Values:** equal after decoding, with white space collapsed and decimals compared as numbers, because the
  samples are pretty-printed.

Eleven tests are outside this scope, and the test names them. Two echo header blocks, one retrieves a resource
with HTTP GET, one reports received type names, and seven test intermediaries.

The collection publishes several defective Node C messages, which the test asserts as errata:
- T46's and the SOAPBuilders nested-array reply's `<return>` tag closes before its namespace declaration.
- The SOAPBuilders 2-D reply's `rpc:result` names an absent edge.
- T27, T28 and T58 put text in `env:Detail`, and T59 writes `env:detail` in lower case.
- T76 and XMLP-9 are not well-formed.
- XMLP-1's fault uses an unbound prefix.

## Array text

A whitespace-preserving parse, which `SoapHandler` uses, numbers the text between elements (`^value1^` and so
on). Whitespace text between array members is ignored under any key; other text is rejected. Before P8-03 the
numbered text was taken for members, so a pretty-printed array reached callbacks as a list of whitespace and
values.

## RPC parts

RPC accessors are matched by WSDL part name, as WSDL 1.1 section 3.5 requires for WSDL-described operations.
A WSDL-generated Apache Axis stub names the return accessor after its part, too.

Decoding returns a single part's value directly. Serialization accepts that bare value back: a scalar or list
since `138c803`, and a struct since P8-02. For a single type-based complex part, the type's declared fields are
taken from the flat hash in the same way as for an element-based part, so header message containers can travel
in the same hash. With several type-based parts a flat hash cannot say which part a field belongs to, so it is
rejected as unserialized input.
