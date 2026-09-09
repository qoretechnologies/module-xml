# Native XSD ENTITY validation

Copyright (C) 2026 Qore Technologies, s.r.o.

`XmlDoc::validateSchema()`, `parse_xml_with_schema()` and schema-enabled
`XmlReader` operations validate ENTITY names against the containing XML
document's unparsed-entity declarations. NCName spelling alone is insufficient.
Parsed entities, predefined XML entities such as `lt`, parameter entities and
undeclared names do not satisfy an ENTITY value.

## Value and document checks

Datatype validation normalizes ENTITY whitespace, validates the NCName and
constructs a typed string value. Schema facets and defaults can be compiled
without an instance DTD. During instance validation, document checks run after
datatype and facet validation. This retains the first matching union member:
`ENTITY | string` rejects undeclared `photo`, while `string | ENTITY` accepts it
as a string. A lexical mismatch such as `p:photo` can reach a later string member.
Lists check each selected ENTITY item; an explicitly defined list can be empty.
The built-in ENTITIES, IDREFS and NMTOKENS types have `minLength=1`, which also
constrains their restrictions. Schema construction checks `minLength <= maxLength`
on the effective facets, including inherited bounds. A restriction cannot permit
zero items by setting `length`, `minLength` or `maxLength` to zero.

DOM validation uses the document's entity table. SAX validation records the
first general-entity binding per name in a context-owned hash table. Parsed and
unparsed declarations share that name space; parameter entities remain separate.
Callbacks supplied by an application are still forwarded. Declaration tracking
also works when the application has no SAX declaration handlers.

Unplugging, clearing or freeing the validation context releases the table.
Allocation failures mark validation as failed. Computed values and built-in
facet links use libxml2 ownership and cleanup, including failure paths. No
entity content is loaded to validate an unparsed-entity name.

The reader normalizes a schema callback exception to a failed read even when
libxml2 reports a node or ordinary EOF. Conversion never changes that failure
into a successful element boundary or releases a partial result. This closes a
Qore hash leak exposed by a rejected ENTITY default on an empty element.

## Example

```qore
%modern
%requires xml
string schema = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="image" type="xs:ENTITY"/></xs:schema>';
string document = '<!DOCTYPE image [<!NOTATION gif SYSTEM "image/gif">'
    '<!ENTITY product_photo SYSTEM "product.gif" NDATA gif>]>'
    '<image>product_photo</image>';
XmlDoc doc(document);
doc.validateSchema(schema);
@assert(parse_xml_with_schema(document, schema).image == "product_photo");
```

This is standalone XML. SOAP 1.1 and SOAP 1.2 prohibit document type declarations;
their document context therefore cannot supply an unparsed-entity declaration.

## Dependency selection and verification

CMake checks the installed library's behavior, including ENTITY values, through
DOM, reader and SAX validation. A passing backport remains eligible regardless
of its version string. `AUTO` falls back on failure; `SYSTEM` reports failure.
The pinned 2.15.4 fallback compiles checksum-verified build-tree copies of
`xmlschemas.c` and `xmlschemastypes.c` after the QName and URI corrections.
Downloaded and offline source trees remain unchanged.

`test/xml-entities.qtest` checks the public native APIs, Unicode, rejection
categories, defaults, nil, early close and deterministic cancellation.
`test/wsdl-interop/test_entity_context.py` compares seven native APIs with
checksum-pinned Xerces-J 2.12.2 and separately specified expected values. Its
schema matrix also checks 432 combinations of local and inherited length bounds.
`qore-xml-entity-allocation` injects failures during SAX declaration recording
and datatype validation and checks complete cleanup.

The standalone oracle uses DOM so first parsed declarations remain visible.
Xerces's JAXP SAX ValidatorHandler records only unparsed declarations and can
incorrectly accept a later unparsed declaration after an earlier parsed binding.
The ordinary SOAP oracle continues to reject all DOCTYPE declarations. Both
oracles disable external entity access; schema documents also prohibit DTDs.
Tests use readable external files to verify that external general entities,
parameter entities and DTD subsets cannot supply content or declarations.

Nine schema-matrix rows expose a separate Xerces defect: when a base type has
both length bounds, its `applyFacets()` checks the inherited maximum in an `if`
branch and the inherited minimum in an `else if` branch. It therefore accepts
lowering the minimum of ENTITIES, IDREFS and NMTOKENS from one to zero when an
intermediate type supplies a maximum of one. The test records those exact
false acceptances and still requires the native schema parser to reject all
nine cases. XSD 1.0 Part 2 section 4.3.2.4 prohibits lowering an inherited minimum.

Normative references: [XSD 1.0 Part 2, ENTITY and ordered unions](https://www.w3.org/TR/xmlschema-2/),
[XSD 1.0 Part 1, String Valid](https://www.w3.org/TR/xmlschema-1/#cvc-simple-type),
[XML 1.0, entity declarations](https://www.w3.org/TR/REC-xml/#sec-entity-decl),
[SOAP 1.1 section 3](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/),
and [SOAP 1.2 section 5](https://www.w3.org/TR/soap12-part1/).
