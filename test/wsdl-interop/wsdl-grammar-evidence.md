# P6 core grammar evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The 312 authored documents in `regressions/wsdl-grammar/cases.json` exercise
core child/attribute contexts, documentation and text, operation ordering,
namespace collisions, extension requirements, parameter ordering and schema
instance attributes. Every row records module acceptance separately from schema
validity. The valid rows exercise original, serialized and data-serialized graphs,
component inventories, native providers and samples, and SOAP requests/responses.
Separate regressions check recovery, prefix aliases and retained unsupported
binding/port metadata with locally rebound namespaces.

## Requirements and independent checks

The [WSDL 1.1 note](https://www.w3.org/TR/2001/NOTE-wsdl-20010315) defines the
component model and extensibility. The corrected core grammar is pinned from
[WS-I's 2004-08-24 schema](https://ws-i.org/profiles/basic/1.1/wsdl-2004-08-24.xsd).
Its original bytes, CRLF, license and whitespace are preserved. The manifest pins
its SHA-256 and source URL; the oracle verifies the hash before compilation.

[Basic Profile 1.2, sections 4.2.8 and 5.1.1](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/csd01/BasicProfile-v1.2-csd01.html)
clarifies extensibility and identifies the corrected schema (R2028). It permits
foreign attributes/elements in core component types that older schema revisions
omitted. The corrected schema places service extensions before ports, despite
the different sketch in WSDL 1.1 section 2.1; the grammar follows the corrected
formal schema. This does not claim conformance to the whole Basic Profile:
legacy XSD imports, deduplicated import resources and advertised encoded bindings
remain supported separately.

Xerces 2.12.2 assesses each row against that unmodified schema. A supplemental
libxml2 check reports the already documented empty-`NMTOKENS` discrepancy, if
present, rather than changing the expected rejection. No live schema retrieval
occurs during these checks. Schema-location hints in fixture documents are
non-authoritative and are not fetched by module-xml.

Twenty-two rows are schema valid but deliberately reject in module-xml because
they require an unknown extension (`wsdl:required="true"` or `"1"`). R2027 requires
that failure; the oracle asserts this separate capability classification. The
remaining rows require agreement between core schema validity and acceptance.
Unknown attributes in the schema-instance namespace follow the foreign wildcard;
the four defined schema-instance attributes still have their own checks.

The existing header-metadata suite now treats an optional foreign `header` as
metadata in both SOAP versions, including saved services and wire decoding.
Its negative checks separately cover an unknown required extension and a header
using the other SOAP version. A local-name collision is not a SOAP declaration.

## Reproduction

```sh
QORE_MODULE_DIR=build-debug:qlib:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-grammar.qtest
python3 -B test/wsdl-interop/test_wsdl_grammar.py -v
```

The durable implementation is described in
[the core grammar design](../../design/wsdl-core-grammar.md). Deeper extension
grammar and remaining binding/attachment interoperability are separate P6 work;
these checks do not establish P6 or P7–P9 completion.
