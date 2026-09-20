# Corrected CXF contracts

Copyright (C) 2026 Qore Technologies, s.r.o.

`header_doc_lit_corrected_parts.wsdl` is a separately named derivative of
`../cxf/header_doc_lit.wsdl`, pinned to Apache CXF 4.1.3 commit
`5b660b5f9d26ae1e606c6291e8beb61ef0d7fcc8`. The original and its catalog hash remain
unchanged and its invalid body references remain an expected rejection.

The corrections are limited to the `headerTesterSOAPBinding` operation
`inoutHeader`: input `soap:body/@parts="in"` and output `parts="out"` both become
`parts="inout"`, matching the actual abstract message parts. WSDL4J independently
observes the original undefined references in `test_wsdl_cxf_bindings.py`.

The import URI becomes `../cxf/header.xsd` to preserve the same pinned dependency
from this new directory, and a modification copyright comment is added. No other
binding, service, port, schema or operation changes. The independent peer test
reconstructs these exact edits and compares the entire derivative byte for byte.
The original Apache license and notice apply, as retained in `../cxf/`.

## SOAP 1.2 action

`hello_world_soap12_absolute_action.wsdl` is an explicit derivative of the pinned
`../cxf/hello_world_soap12.wsdl`. The original `sayHi` binding has the relative action
`sayHiAction`; the unchanged historical CXF capture also sends that value.
[SOAP 1.2 Part 2 section 6.5.3](https://www.w3.org/TR/soap12-part2/#soapfeatureaction)
requires a nonempty absolute action URI. The original WSDL remains parseable, but
request serialization and HTTP reception reject that invalid protocol value.

The derivative replaces only that action with `urn:cxf:sayHiAction` and adds a 2026
modification notice. `soap12-action.json` records both hashes and the exact edits;
the independent peer gate reconstructs the derivative byte for byte. Schema,
operation, service and port identities remain unchanged. The original Apache
license and notices apply.

Native/retained replay, coverage and live Qore/CXF SOAP 1.2 checks explicitly select
the derivative. Java bindings are generated from it, and captured requests use the
same absolute action for positive live exchanges. Original source and captured
relative-action headers remain mandatory negative controls, including HTTP rejection
without application dispatch followed by successful calls on the same handler.
Historical golden files and their hashes are not rewritten.
