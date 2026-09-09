# QName union validation in the native dependency

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 [section 2.5.1.3](https://www.w3.org/TR/xmlschema-2/#union-datatypes)
requires ordered member matching. An unbound `p:Name` fails the QName member
but matches a later string member. A restriction enumerating that unbound
literal has a string value: an instance that binds `p` instead selects QName
and does not equal it. QName [namespace identity](https://www.w3.org/TR/xmlschema-2/#QName)
and [enumeration](https://www.w3.org/TR/xmlschema-2/#rf-enumeration) remain exact.

In libxml2 2.15.4, `xmlSchemaVCheckCVCSimpleType()` recursively tries union
members with `fireErrors=0`. `xmlSchemaValidateQName()` did not receive the
flag, so its unbound-prefix diagnostic called `xmlSchemaCustomErr()` anyway.
The callback and accumulated error count rejected a document even when the
union subsequently found a valid member. The fix passes the flag through and
guards only this candidate diagnostic. Return codes, failed-union diagnostics,
internal errors, namespace resolution and temporary-name cleanup remain intact.
This corrects the dependency at its error-reporting boundary; supplied XML,
member order and validation requirements do not change.

The configure probe retains its 48 QName/NOTATION pairs and adds 100 union
pairs. Both DOM and streaming validation must agree with the declared verdict;
valid documents must produce no error or warning callbacks. DOM contexts also
validate a known-invalid document and then the original document again.
The exact pre-fix dependency rejected seven valid pairs:

| Type | Unbound lexical values |
| --- | --- |
| QName followed by string | `p:Name` |
| String enumeration on that union | `p:Name` |
| Nested QName/integer union followed by string | `p:Name` |
| QName list followed by string | `p:Name`, `p:Name 17` |
| List of QName/string union items | `p:Name`, `p:Name 17` |

Other cases test bound/implicit prefixes, a different namespace, invalid QName
syntax, QName-only and all-members-failed rejection, empty values, list integer
items, reversed member order, and QName enumeration aliases. The full source
archive stays unchanged. Original `xmlschemas.c` SHA-256 is
`bed8bfbfd61a2025b67b7a0e4d05ce50093e7a6bb5e43a3ebac343b8df4329a7`;
the build-tree source, including the previous implicit-xml correction, is
`99eeb19c5c78c3407af28efc22752ae8c5e581ef74a5c09807ab3fcf37277650`.

The independent Python matrix expands these models to content-only,
attribute-only and combined cases: **30 schemas / 300 documents**. Pinned
Xerces-J 2.12.2 and the corrected native module agree on every verdict. Qore's
`parse_xml_with_schema()` and `XmlReader` both validate all rows and preserve
accepted XML text and attributes; invalid rows raise `PARSE-XML-EXCEPTION`.
The separate Python libxml2 2.12.10 rejects exactly the seven cases above in
all three shapes, **21 false negatives**. Each must report the exact datatype
error, once per affected content/attribute. A future fixed Python validator
may agree on all rows; arbitrary subsets or other discrepancies fail the test.
No native Qore discrepancy is waived.

The complete authored fixtures have SHA-256
`4504254bd15b7e1ce2e33ca48893d6bb1a48fc994994d2ad5dfdbdeec13d46ad`.
Inputs, original verdicts and native results are retained in
`/tmp/xml-qname-union-validator-bhanf7v2/{fixtures,results}.json`.
`test_qname_union_validator.py` deterministically rebuilds them and preserves
new run artifacts. No upstream corpus file or historical finding was edited.

`test/xml-qname-unions.qtest` adds **5 cases / 351 assertions**, including
separate invalid content/attribute paths, later successful calls and interruption.
The complete suite passes AST/IR/JIT/tiered in both UTC and Europe/Prague.
The CMake provider suite passes all **18 tests**, including a library containing
only the earlier QName identity fixes: it passes `qname_values` and fails
`qname_unions`, so AUTO falls back and SYSTEM rejects it. Complete backports,
source checksums, unchanged reconfiguration timestamps, offline/cross builds
and notice installation remain tested.

Both the complete native probe and Qore suite pass Valgrind with zero errors
and zero definite/indirect/possible loss. Native compilation with
`-Wall -Wextra -Werror`, Debug module/docs builds and the documented example
also pass. Qore Valgrind uses `-b --enable-debug --exec-mode=jit` with the
authorized `QORE_PCRE2_NO_JIT=1`; the previously tracked core DWARF-reader
warning remains a P9 environment finding, without suppression.

## Separate native reader findings

The new direct reader checks exposed two independent, pre-existing API defects:

- `XmlReader::toQore()` and `toQoreData()` call the hash-only `parseXmlData()`
  helper, despite documenting a string return for scalar content. Reading
  `<value>text</value>`, advancing to the element and calling `toQore()` aborts
  in Debug at the `NT_HASH` assertion. No QName or schema is needed.
- `XmlReader::schemaValidate()` documents an XSD string but passes it to
  libxml2's schema-location API. A valid schema string fails before any read
  with `XMLREADER-XSD-ERROR`; the constructor's `xsd` option works.

These are assigned to the next independent P3 native-reader increment, before
returning to the WSDL QName integration. They are not passing tests or changes
introduced by union error isolation. Minimal programs and exact outcomes are
`/tmp/wsdl-p3-35-reader-{scalar,schema}-baseline.qr` and
`/tmp/wsdl-p3-35-reader-baseline.json`; the first API's stack is retained in
`/tmp/wsdl-p3-34-assert-gdb.log`. The union tests use the separately verified
public schema-parsing and cursor APIs. General WSDL QName conversion remains
open and is excluded from this dependency increment.
