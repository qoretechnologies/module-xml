# P6-04 document-local component references

Copyright (C) 2026 Qore Technologies, s.r.o.

The old parser discarded QName prefixes before choosing messages, port types and
bindings. A reference to another namespace could therefore select a same-local-name
component. Empty bindings could retain an undefined port type because validation
only ran while iterating operations. Valid references with surrounding whitespace
or locally declared header prefixes failed for separate normalization/scope reasons.

The reader now collects typed reference records and resolves them against complete
expanded-name component tables before construction. Input/output/fault messages,
binding port types, service port bindings and direct SOAP header/headerfault
messages use their own lexical namespace context. The grouped view retains
normalized QName/name attributes; root targetNamespace whitespace is normalized
in both the declaration table and constructed namespace container. Binding
construction enters operation, input/output and header namespace scopes and
restores each enclosing scope on exit.

The requirements are the component symbol spaces and QName references in
[WSDL 1.1 sections 2.1–2.7 and 3.7](https://www.w3.org/TR/wsdl.html), with QName/anyURI
whitespace rules from its published schema. The shared 21-document fixture matrix
records schema validity separately from component-reference validity. Pinned
Xerces 2.12.2 validates lexical/schema expectations, and the independent lxml
contract inventory resolves expanded component references. Schema validation
alone does not detect an undefined message or binding target.

Run with the established local Qore/XML paths:

```sh
qore -b --enable-debug test/wsdl-component-references.qtest
python3 -B test/wsdl-interop/test_wsdl_component_references.py -v
python3 -B test/wsdl-interop/test_contract.py -v
```

The focused Qore suite passes 8 cases / 103 assertions. It checks namespace
mismatches, malformed/unbound QNames, missing attributes and empty-binding targets,
forward references, default/no namespace, scoped aliases, whitespace, independent
symbol spaces and headerfault references. Positive fixture rows run through source
and saved services. Real HTTP exchanges use both actual SOAP bindings, declared
headers, bounded client/queue deadlines and deterministic listener cleanup.
Headerfault reference checks do not claim complete headerfault wire processing.

The complete enterprise/partner description suite also passes all 5 cases / 85
assertions without warnings/errors in 693.688 seconds on the frozen runtime.
The separately documented native collector cost remains a P9 investigation;
this successful bounded run is not a verified Release benchmark.

All 32 affected suites pass 428 cases / 6,862 reported assertions, including the
seven intentional caught comparator assertions in soap.qtest. The full native
and legacy surveys and both default/P5 typed coverage reports differ from P6-03
only in version metadata. Native coverage retains 2,096 successful valid directions
and 176 required invalid-source rejections. Legacy retains 2,084 successes and
twelve reported projection losses; strict P5 legacy exits one as expected.
All 16 coverage and 17 survey tests pass. Seven contract tests and the shared
21-case independent reference matrix pass. WSDL documentation builds without
warnings or errors. Source hashes remain unchanged during the final runs.

Initial reference tests reproduced four distinct failures. Review then exposed
raw targetNamespace whitespace in the new declaration table and independent
inventory; both were corrected and retested before acceptance. Test-development
API/signature mistakes are retained in the local diagnostic logs and are not
counted as successful runs. The final verification is in `verified/` under
`/tmp/wsdl-p6-04-component-references/`.

The separately discovered existing WSDLLib URI-base/path resolution issue is
assigned to the next P6 import increment, before import-catalog integration.
Root cause, examples and RFC 3986 requirements are written up in
`/tmp/wsdl-p6-05-import-catalog/location-finding.md`. An isolated catalog prototype
passes its initial cycle/diamond/mismatch/retry checks; it is not integrated or
counted as completed import functionality.

See [validation](P6-04-validation.json), [all 62 audit checks](audits/P6-04-component-references.md)
and [implemented design](../../design/wsdl-component-references.md). No C++ change,
installation or main-Qore mutation. WSDL import graphs, full grammar, operation
signatures, parts/header/fault behavior and HTTP/MIME remain P6 work; P7–P9 remain open.
