# SOAP extension grammar evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The 303 documents in `regressions/wsdl-soap-grammar/cases.json` cover both SOAP
binding namespaces and seven declaration contexts. They test required, unknown,
same-namespace and foreign attributes; character and child content; whitespace;
XML booleans; xsi types/hints; URI and name lexical values; prefix aliases; and a
default binding namespace. Multi-headerfault rows exercise list normalization with
independent message/part references. Valid contracts run through source and both saved forms,
detached operations, native providers/examples, requests/responses, declared body
faults and headerfaults. Original WSDL text remains exact.

The root causes were unvalidated extension attributes/content and passing original
XML token spellings to component lookup. The stream checker validates before
grouping; the compilation projection normalizes recognized attributes only.
Normalization fixes legal surrounding whitespace in transport URIs, fault names
and header part references without changing the saved source text.

## Independent schema inputs

The manifest pins unchanged original bytes, license notices and SHA-256 values for:

- [SOAP 1.1 corrected schema](https://schemas.xmlsoap.org/wsdl/soap/2004-08-24.xsd).
- [SOAP 1.2 binding schema](https://schemas.xmlsoap.org/wsdl/soap12/wsdl11soap12.xsd).

The wrapper imports the already pinned corrected core WSDL schema first, then the
selected SOAP schema. All resources are supplied offline. The schemas' locationless
WSDL imports resolve the previously loaded core grammar; no upstream file is edited.

Xerces assesses every document. Expected module acceptance and schema validity are
separate fields, with exactly sixteen documented differences:

- Two SOAP 1.2 fault rows contain foreign attributes. Section 3.4 of the
  [SOAP 1.2 WSDL binding specification](https://www.w3.org/submissions/wsdl11soap12/)
  explicitly permits those attributes. Its published tFault restriction omits the
  wildcard, so the schema rejects them; module-xml follows the specification.
- Fourteen rows contain incomplete xsi:schemaLocation pairs. The hint syntax in
  [XSD 1.0 Structures section 4.3.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#schema-loc)
  consists of namespace/location URI pairs. Module-xml rejects an incomplete pair;
  the validator accepts these ignored hints. This semantic rejection is not
  represented as a schema-invalid document.

Whitespace in an empty-content declaration is invalid. Header alone has an
element-only model permitting whitespace between headerfault children. The oracle
and module agree on this distinction. All disagreement identities, directions and
counts are asserted; no failed assessment is omitted from the inventory.

## Reproduction and scope

```sh
QORE_MODULE_DIR=build-debug:qlib:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-soap-grammar.qtest
python3 -B test/wsdl-interop/test_wsdl_soap_grammar.py -v
```

See [the implemented design](../../design/wsdl-soap-extension-grammar.md).
This increment does not close remaining top-level WSDL constraints, HTTP/MIME
grammar, binding semantics, attachment interoperability or P7–P9 acceptance.

The published SOAP `tFault` type derives from `tBody`. Eight additional rows
check legal body declarations using that derived type and reject its missing name,
prohibited parts attribute and abstract intermediate type in both SOAP versions.
Selecting the derived schema type does not turn a body declaration into a fault.
