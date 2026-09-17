# SOAP header/body merge evidence (P6-13)

Copyright (C) 2026 Qore Technologies, s.r.o.

Issue [5453](https://github.com/qoretechnologies/qore/issues/5453) was reproduced
by the 2.x regression added to `soap.qtest`: a body part named after its message
was overwritten by that message's header values. Independent focused cases also
reproduced flattened-key conflicts, scalar header loss, wrapper loss and RPC
scalar header loss. Seven of eight original focused cases failed before the fix;
the nil case already passed. The subsequent HTTP case tests both public consumers.
An existing component-reference HTTP test had relied on discarded RPC headers;
its callback now reads the body part and explicitly checks the retained header.
No production changes were needed after the initial merge repair.

The port checks flattened value keys, preserves scalar part keys, groups
colliding parts inside their message, and keeps selected type/element wrappers
intact. [Durable rules](../../design/wsdl-soap-header-values.md) describe the
result shape, including the nested wrapper case unique to develop.

The earlier fixes for issues 5405, 5410, 5411 and 5452 remain ancestors of HEAD;
their fixture files and SOAP cases are retained. XSD patterns compile at schema
construction and reuse compiled constraints during value checks, covering the
2.x caching improvement without adding a second cache.

Validation:

- Focused suite: 9 cases / 480 assertions. Independently authored XML, both SOAP
  versions and directions, source/saved services, missing headers, nil/empty/scalar
  values, collisions, selected wrappers, invalid extra body content and real
  SoapClient/SoapHandler exchanges all pass.
- Every `test/wsdl-*.qtest` plus SOAP/client/handler suites: 160 suites,
  1,612 cases / 81,391 reported assertions. All cases pass without
  warnings or unhandled errors. `soap.qtest` intentionally catches seven failed
  comparator assertions in its negative comparator tests.
- WSDL/SoapClient documentation generation and WSDL astparser validation pass.
- No C++ changed; Valgrind is not required.
- Full audit: 62 checks, 18 Pass / 44 N/A / zero Fail.

Exact commands, source fingerprints and log hashes are in
[P6-13-validation.json](P6-13-validation.json); audit findings are in
[audits/P6-13-header-merge.md](audits/P6-13-header-merge.md).
The customer archive is not available locally; the ported fixtures reproduce
its message/part collision without containing customer data.

The P6 overload/default-name work and P7–P9 remain open.
