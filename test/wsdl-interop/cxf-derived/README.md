# Corrected CXF document-header contract

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
