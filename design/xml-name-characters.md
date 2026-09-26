# XSD name characters in the libxml2 dependency

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 Part 2 defines `Name`, `NCName`, `QName` and `NMTOKEN`, and the types derived from them (`ID`, `IDREF`,
`IDREFS`, `ENTITY`, `ENTITIES`, `NMTOKENS`), with the name productions of XML 1.0 Second Edition: letters, digits,
combining characters and extenders of its Appendix B. The XSD errata do not replace that reference with the XML 1.0
Fifth Edition grammar; only XSD 1.1 lets a processor choose the Fifth Edition characters. This applies to every
SOAP version, since SOAP 1.1 and SOAP 1.2 both use XSD 1.0 datatypes (decided 2026-09-26, with no per-version or
optional Fifth Edition mode). The WSDL module's own lexical checks follow the same rule
(`test/wsdl-interop/builtin-list-values-evidence.md`).

libxml2 2.15 validates these datatypes with `xmlValidateName()`, `xmlValidateNCName()`, `xmlValidateQName()` and
`xmlValidateNMToken()`, which since 2.15 scan with the Fifth Edition characters (`xmlScanName()` without
`XML_SCAN_OLD10`). Schema validation therefore accepted values such as `Ͱa` (U+0370), `⁰a` (U+2070) or `𐀀a`
(U+10000), which Xerces and libxml2 before 2.15 reject. Before 2.15, those functions used the Appendix B tables.

`cmake/QoreXmlLibXml2NameEditionFix.cmake`, applied after every other fix of the two files, gives the schema
processor its own validators, `xmlSchemaValidateName10()` and its NCName, QName and NMTOKEN variants, in
`xmlschemastypes.c`. They are the upstream functions scanning with `XML_SCAN_OLD10`, the Appendix B tables that the
parser keeps for its `XML_PARSE_OLD10` option. Every name check of `xmlschemastypes.c` (instance values of the
Name-derived types and their lists) and `xmlschemas.c` (QName attributes and `id` attributes of schema documents,
QName resolution and `ENTITY` values) uses them.

XML names are unchanged. Element, attribute, entity and notation names in documents, DTD validation and the public
`xmlValidate*()` functions keep the Fifth Edition characters, so a document may use an element name that an
`xs:QName` value cannot name.

CMake uses a system libxml2 only when the runtime probe passes; `cmake/libxml2-name-edition-probe.h` checks Second
Edition letters, combining characters and extenders, characters that may only continue a name, and Fifth Edition
only characters, for the four types through `xmlSchemaValidatePredefinedType()` and document validation, and for
component names and ids in schema documents. `test/xml-name-edition.qtest` checks the native validators
(`XmlDoc::validateSchema()`, `parse_xml_with_schema()` and `XmlReader`), including `ID`, `IDREF`, `IDREFS`,
`ENTITY` and `NMTOKENS`, and that XML names keep the Fifth Edition characters.
