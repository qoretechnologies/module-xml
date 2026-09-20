# P7-02 SOAP header boolean attribute lexical spaces

Copyright (C) 2026 Qore Technologies, s.r.o.

The P7-01 structural validator checked header names but did not check SOAP's boolean processing attributes. A reduced source/saved/retained test demonstrated that SOAP 1.1 accepted `mustUnderstand="true"` and SOAP 1.2 accepted malformed `mustUnderstand`/`relay` values. The new baseline fails for the expected missing rejection.

`SoapEnvelopeHelper` now resolves each header-block attribute in the block's namespace context. It validates SOAP 1.1 `mustUnderstand` against `0`/`1`, and SOAP 1.2 `mustUnderstand`/`relay` against the XSD boolean lexical space after XML whitespace collapse. It reuses the established XSD boolean validator. Serialization checks the actual attribute string conversion, so a native float `1.0` cannot pass a value-space check and then generate an invalid boolean spelling. Qualified raw compatibility fragments use the same checks.

Unqualified, foreign-namespace, other-version and descendant attributes do not acquire these protocol semantics. SOAP 1.1 has no `relay` attribute semantics. This is lexical validation only; explicit node capabilities, targeting, mandatory-header handling and relay execution remain the next P7 increment.

The normative sources are [SOAP 1.1 section 4.2.3](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/) and [SOAP 1.2 sections 5.2.3–5.2.4](https://www.w3.org/TR/soap12-part1/). The independent Python matrix imports the exact pinned W3C attribute declarations and assesses every positive/negative spelling through lxml, without consulting the Qore validator. HTTP fixtures address their optional/mandatory headers to another node; they do not assume an implicit capability to process an unknown mandatory targeted header.

The [W3C assertion collection](https://www.w3.org/TR/soap12-testcollection/) rows `x1-soapmu-prop`, `x1-soapmu-acceptfalse`, `x1-soapmu-allrep`, `x1-soapmu-ignore`, `x1-soaprelay-prop`, `x1-soaprelay-acceptfalse`, `x1-soaprelay-allrep` and `x1-soaprelay-ignore` map to the lexical matrix and scope cases in the new Qore/Python suites. This increment does not claim the omitted/default-value processing or node-role assertions.

The Qore suite covers source, serialized and data-restored graphs; native requests/responses; retained XML; output; raw fragments; namespace aliases; whitespace and NBSP; case errors, empty and extra tokens; native boolean/integer/float representations; input immutability; and recovery. The Python peer makes 225 sender/handler exchanges and 36 persistent-client/receiver exchanges (261 total), including failed requests excluded from callbacks and valid responses after failures.

All 21 affected Qore suites pass: **359 cases / 10,957 assertions**. Four independent Python gates pass, including 261 new HTTP exchanges and the pinned W3C attribute-declaration matrix. The new suite passes **3 cases / 927 assertions** with both source and compiled WSDL. Documentation and two-file astparser checks pass without warnings/errors. All 16 corpus commands meet their expected outcomes; six semantic reports match P7-01 apart from the WSDL source hash.

The full audit is recorded in [P7-02 audit](audits/P7-02-soap-processing-attributes.md), with exact commands in [P7-02 validation](P7-02-validation.json). Implemented behavior is in [SOAP envelope processing](../../design/soap-envelope-processing.md). Baseline, logs and compiled artifacts are in `/tmp/xml-soap-header-processing/`.

No C++ changes, Qore changes, installation or push. P7 node processing, faults and HTTP rules remain open; P8–P9 remain open.
