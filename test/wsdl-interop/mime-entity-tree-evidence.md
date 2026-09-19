# P6-43 HTTP MIME entity trees

Copyright (C) 2026 Qore Technologies, s.r.o.

The implementation retains recursive HTTP MIME declarations, independent entity values, explicit ambiguous-format selections, related root identities and concrete provider types. Source, saved and detached operations use the same contract.

Installed Qore `e8768a8a0` resolves both ordinary-literal conversion failures. The independent core reproducer passes 5 cases / 5 assertions. XML's focused tree and literal suites pass 15 cases / 676 assertions in both source and compiled-module checks. No XML coercion workaround is present.

All 43 affected Qore suites pass: **1,684 cases / 55,397 assertions**. All 16 independent Python gates pass, including five MIME peer tests with 32 external decoding variants, four live HTTP exchanges and 32 malformed-input/recovery pairs. All 16 corpus commands meet their expected outcomes; six semantic reports match P6-42 apart from runtime version metadata. Documentation, eight-file astparser checks and all four compiled QMODs pass without warnings/errors.

The full audit reports **28 Pass / 34 N/A / zero Fail**. All work targets `develop` in the main checkout. No C++ change, Qore source change, installation or push was made. Request-local HTTP URL support and its XML integration remain required P6 work; P7–P9 remain incomplete.

Validation: [P6-43-validation.json](P6-43-validation.json). Audit: [P6-43-mime-entity-trees.md](audits/P6-43-mime-entity-trees.md). Durable implementation: [wsdl-http-multipart.md](../../design/wsdl-http-multipart.md).

Logs are in `/tmp/xml-mime-layouts-next/gates-installed-fix/` and `installed-fix-*.log`. The fixed core conversion handoff is `/tmp/qore-mime-tree-hashdecl-coercion/README.md`; the outstanding request-local URL handoff is `/tmp/xml-http-base-resolution/QORE-REQUEST-URL.md`. The final documentation-only delta changes nine Doxygen language tags, with no executable-code change.
