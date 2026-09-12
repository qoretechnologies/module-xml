# P5-16f effective anyType inheritance

Copyright (C) 2026 Qore Technologies, s.r.o.

The native prerequisite is committed as `ad3d574`. WSDL had marked empty
extensions of `xs:anyType` as mixed but had never built the inherited wildcard
particle. Ordered decoding consequently rejected valid children. Its public
wildcard flag also described only directly parsed content, so providers could
miss active inherited and group wildcards.

WSDL now constructs the builtin sequence/lax wildcard as schema-owned metadata,
combines effective extension particles, and computes wildcard presence from the
completed graph. Zero-occurrence particles are absent from effective content;
empty compositor and named-group distinctions follow XSD 1.0. Invalid occurrence
ranges, mixed-content derivation and unique particle attribution still reject
during schema construction. The implementation and normative references are in
[the durable design](../../design/wsdl-anytype-inheritance.md).

No corpus fixture or adjudication changed. Complete keyed comparison with
P5-16e closes request and response for both versions of
`GlobalElementComplexTypeSequenceExtension`. All other coverage case objects are
identical. The diagnostic survey has two newly reachable successful serialization
rows; every previously successful stage remains successful. The selected scope
remains 144 WSDLs/1,388 directions, with no selected failures. Four valid-input
directions and twenty broader failures remain visible. Dynamic-type legacy
projection, instance default/fixed constraints, identities and P6-P9 acceptance
remain open; this increment is not complete protocol conformance.

The full regression gate exposed an older native-type receiver test whose
substitute schema was itself invalid: a nonempty element-only extension of
anyType. Pinned Xerces independently confirms its rejection. That exact source
remains an explicit WSDL/native schema-negative test. A valid unrelated empty
base now supplies the original receiver type-mismatch check, with every prior
assertion retained. The corrected suite passes 17 cases/488 assertions in source
and compiled-module modes. The original failed gate and targeted recheck are
both recorded; production source and all other suites were unchanged.

## Tests and reproduction

Final acceptance artifacts are under `/tmp/wsdl-p5-16f-inheritance/accepted/`.
Earlier interrupted runs under the parent and `final/` directories are retained
but superseded: tests were expanded to cover bounded provider samples and
zero-occurrence compositors before the final source was frozen. Only the final
unchanged-production-source gate and the targeted fixture repair below supply
accepted regression results.

```sh
export LD_LIBRARY_PATH=/tmp/wsdl-p5-16d-values/confirmed/runtime
export QORE_MODULE_DIR=/home/david/src/qore/git/module-xml/build-debug:/home/david/src/qore/git/module-xml/qlib
export PATH=/tmp/wsdl-p5-16d-values/accepted/bin:$PATH
qore -b --enable-debug test/wsdl-anytype-inheritance.qtest
qore -b --enable-debug test/wsdl-mixed-http.qtest
python3 test/wsdl-interop/test_anytype_inheritance.py -v
python3 test/wsdl-interop/test_mixed_values.py -v
python3 /tmp/wsdl-p5-16f-inheritance/accepted/gate.py
python3 /tmp/wsdl-p5-16f-inheritance/accepted/run-corpus-gate.py
python3 /tmp/wsdl-p5-16f-inheritance/accepted/run-supplement.py
```

The new Qore suite covers 19 valid schema forms, saved schemas/values, original
and native providers, soft/mandatory variants, active/zero group references,
bounded samples, mixed XML text/order/comments, namespace bindings and invalid
known children/attributes. All four cases/1,000 assertions pass in AST, IR and
JIT, and against the rebuilt compiled WSDL module. The HTTP suite's four
cases/298 assertions pass in source and compiled-module modes, including clients,
handlers and SoapDataProvider. A malformed request is rejected before its handler
callback, followed by successful reuse. The expected statuses follow
[SOAP 1.1 section 6.2](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383529)
and [SOAP 1.2 HTTP response status rules](https://www.w3.org/TR/soap12-part2/#tabresstatereccodes).

The independent matrix checks 17 schemas/119 documents/476 actual SOAP binding
directions and 1,020 outputs through pinned Xerces and the lxml peer. It compares
lexical wildcard values, expanded names, QName-like text bindings, comments and
order. Its AOT copy changes only module-loading paths; fixtures and comparisons
are identical. The shared mixed-value helper retains its original twelve-schema,
480-document, 1,920-direction and 852-output coverage. The prior 95-schema native
value matrix and mixed-base matrix also pass.

The final new Qore suite passes Valgrind with zero errors and zero lost blocks;
139,068 bytes in 119 blocks remain reachable at process shutdown. This optional
check uses `QORE_PCRE2_NO_JIT=1`; normal tests keep PCRE2 JIT enabled. There are no
C/C++ changes in this increment. WSDL qmod/Doxygen builds and the executed shipment
example are warning-free. Runtime, build, test and artifact hashes are retained
in [the inventory](P5-16f-validation.json); all 62 checks are recorded in
[the audit](audits/P5-16f-anytype-inheritance.md).

Remote was fetched with no incoming commit. No main-Qore mutation, installation
or push was made. Mandatory Python coverage and supported CI environments remain
assigned to P9.
