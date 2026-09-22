# SOAP encoding

Copyright (C) 2026 Qore Technologies, s.r.o.

This document describes how the WSDL module decodes and encodes `use="encoded"` message parts. It covers the
SOAP 1.1 section 5 rules; SOAP 1.2 Encoding is added by later P8 increments.

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

Only a same-document fragment reference (`href="#id"`) names an independent element. Any other URI, such as a
`cid:` reference to a MIME part, is left to the value's own conversion; it is never resolved as a local id.

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
- SOAP 1.1 section 5.4.2 lets an array accessor name the generic `SOAP-ENC:Array` together with
  `SOAP-ENC:arrayType`, even where the schema declares a type derived from it. An explicit `SOAP-ENC:Array`
  keeps the declared array type. It cannot replace a type that is not an encoded array.

## Arrays

`XsdArrayType` parses both the declared `wsdl:arrayType` and each instance's `SOAP-ENC:arrayType` with one parser
that follows the SOAP 1.1 section 5.4.2 grammar: `atype = QName *(rank)` and `asize = "[" #length "]"`. A shape is
the item QName, the ranks of the nested array levels that `atype` names (innermost first), the array's own rank,
and its asserted lengths, which are either all present or all absent. `xsd:int[,]` is one rank-2 array;
`xsd:int[][]` is a rank-1 array whose members are `int[]` arrays. The public `dimensions` member is the nesting
depth of the decoded Qore list: 2 for both of those.

### Decoding

Each array level is decoded against the instance's own `arrayType`, or the declared one when absent:

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

## RPC parts

RPC accessors are matched by WSDL part name, as WSDL 1.1 section 3.5 requires for WSDL-described operations.
A WSDL-generated Apache Axis stub names the return accessor after its part, too.

Decoding returns a single part's value directly. Serialization accepts that bare value back: a scalar or list
since `138c803`, and a struct since P8-02. For a single type-based complex part, the type's declared fields are
taken from the flat hash in the same way as for an element-based part, so header message containers can travel
in the same hash. With several type-based parts a flat hash cannot say which part a field belongs to, so it is
rejected as unserialized input.
