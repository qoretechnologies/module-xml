# P6-45 Declaring-document service port addresses

Copyright (C) 2026 Qore Technologies, s.r.o.

The reduced baseline kept `../api/` as the selected port address even when the containing document URI was known; constructing SoapClient then left its native URL unset. An imported service also lost the URI of its own declaring document because service parsing only received component and namespace context. The new regression failed both source/saved address assertions and live handler registration before this fix.

WSDL 1.1 [appendix A.1.2](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_relativeURIs) defines relative references against the containing document. Service parsing now receives that document URI explicitly and calls Qore `resolve_url()` with `RESOLVE_URL_ENCODE`. There is no temporary global context mutation or separate URI implementation. Original source bytes remain unchanged; document catalog contexts carry the same resolution through saved services. Inline sources without a document URI remain lexical, and explicit client URLs still override deployment addresses.

Tests cover HTTP, SOAP 1.1 and SOAP 1.2; root/relative/network/absolute references; query-only, explicitly empty, fragment and empty references; Unicode, spaces and existing escapes; imported services; synchronous/asynchronous/client loading through redirected root and imported documents; source/saved/data providers and handlers; and offline restoration after the peer stops. Python urllib supplies an independent resolver for actual HTTP request-line and origin assertions. Existing invalid URI/grammar and unsupported-port gates remain green.

All 203 phase-boundary Qore suites pass: **3,257 cases / 136,416 assertions**. All 18 independent Python gates and 16 corpus commands meet their expected outcomes. The new port-address suite passes 4 cases / 519 assertions in both source and compiled WSDL; its loopback loaders cover 63 HTTP exchanges, while the independent Python peer covers another 28. Six corpus reports match P6-44 except for the WSDL source hash. Documentation and three-file astparser checks pass without warnings/errors.

The broad gate includes every previously recorded P6 Qore suite and affected schema/provider regressions. The P5 legacy projection diagnostic still returns its expected failure status: these accepted projection losses are reported separately from explicit native capture and retained XML, and are not reclassified as passes.

Validation: [P6-45-validation.json](P6-45-validation.json). Audit: [P6-45-port-locations.md](audits/P6-45-port-locations.md). Acceptance: [P6-acceptance.md](P6-acceptance.md). Durable design: [location resolution](../../design/wsdl-location-resolution.md). Logs, reduced baseline and compiled artifacts: `/tmp/xml-wsdl-port-address/`.
