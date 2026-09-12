# P5-16g receiving-element fixed values

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL previously validated an occurrence's datatype without comparing its value
with the receiving element's fixed constraint. This admitted explicit different
values and confused distinct primitive values selected by `xsi:type`. Ordinary
providers likewise accepted values that failed the receiving declaration.

WSDL now captures the original conversion's XSD identity and compares explicit
nonempty content with the resolved declaration identity. Unions retain the chosen
member, lists retain item order, and QName equality uses expanded names. Mixed
fixed content rejects children. Generic XML output returns its actual selected
identity from the existing validation call. Custom converters run once per
conversion. The [implemented design](../../design/element-fixed-values.md)
includes normative references and an executed invoice example.

The ordinary provider adapter retains primitive/list/record shape, base category,
requiredness, tags and soft conversion. Mandatory examples use the fixed value
with required attributes. Native providers enforce the same receiving declaration.
The audit caught and fixed metadata that had reported a primitive as `all` and
an existing native XSD list provider that did not report list behavior. It also
caught premature foreign-member inspection during saved-provider restoration;
provider-first indexed data now restores and validates after reconstruction.

Old providers retain declaration lexical data but lack computed identity metadata.
The [frozen fixture](fixtures/fixed-legacy/README.md) was produced by unmodified
`46f73cd` WSDL. Its first use resolves missing identity under a declaration lock;
successful results cache, cancellation releases the lock and permits retry.
The exact old bytes, a second save/restore, custom counters and concurrent first
use are covered. Schema serialization still rebuilds from saved source documents.

An early transient initializer referencing another member independently crashed
Qore during restore. A standalone reproducer, stack and core root cause are in
`/tmp/wsdl-transient-member-restore/README.md` for the separate Qore task. WSDL uses
the documented custom restoration protocol to initialize its local cache lock;
no core patch or installed-runtime workaround is included. The same writeup
records a separate typed-hash forward-index ordering question, with an isolated
core reproducer; the original serializer's ordering works and stays unchanged.

## Validation and reproduction

Final artifacts are in `/tmp/wsdl-p5-16g-fixed/final/`. Earlier parent and
`accepted/` runs are retained as superseded evidence: migration and metadata
coverage changed after those runs began. Only `final/` supplies acceptance.
The [inventory](P5-16g-validation.json) contains exact hashes and all commands;
the [audit](audits/P5-16g-fixed-values.md) covers all 62 checks.

```sh
export LD_LIBRARY_PATH=/tmp/wsdl-p5-16d-values/confirmed/runtime
export QORE_MODULE_DIR=/home/david/src/qore/git/module-xml/build-debug:/home/david/src/qore/git/module-xml/qlib
export PATH=/tmp/wsdl-p5-16d-values/accepted/bin:$PATH
qore -b --enable-debug test/wsdl-fixed-values.qtest
qore -b --enable-debug test/wsdl-fixed-http.qtest
python3 test/wsdl-interop/test_fixed_values.py -v
python3 /tmp/wsdl-p5-16g-fixed/final/gate.py
python3 /tmp/wsdl-p5-16g-fixed/final/run-corpus.py
python3 /tmp/wsdl-p5-16g-fixed/final/supplement.py
```

The Qore suite has 11 cases/174 assertions and the actual HTTP suite has one
case/28 assertions. Both pass in AST, IR, JIT and with the rebuilt compiled WSDL
module. HTTP tests exercise SoapClient, SoapHandler and SoapDataProvider with
real SOAP 1.1/1.2 bindings, including malformed request rejection before callbacks
and subsequent valid reuse. Expected statuses follow
[SOAP 1.1 section 6.2](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383529)
and [SOAP 1.2 HTTP response rules](https://www.w3.org/TR/soap12-part2/#tabresstatereccodes).

The Python matrix derives separately named service schemas from the unchanged
native fixed-value models. Pinned Xerces 2.12.2 checks 53 schemas, 172 documents
and 1,257 outputs through 688 actual SOAP request/response directions. Independent
Python comparisons check exact numeric values, primitive identity, ordered lists,
expanded QNames, dates/durations, binary octets and required attributes. The
source and AOT matrices use identical fixtures and comparisons. Sixteen survey
unit tests, the 95-schema/774-document native matrix and union identity tests pass.

The final source gate passes 146 suites, 1,387 cases and 67,922 reported assertions.
The optional final Valgrind run reports zero errors/lost blocks; 138,428 bytes in
103 blocks remain reachable. Only Valgrind disables PCRE2 JIT. The compiled WSDL,
Doxygen build and executed invoice example are warning-free. There are no C++
changes in this increment.

All 2,461 diagnostic survey rows and all 293 coverage case objects are identical
to P5-16f. No case was dropped or newly skipped; original fixtures and catalogs
are unchanged. Selected coverage remains 144 WSDLs/1,388 passing directions.
Four valid-input directions and twenty broader failure records remain visible.
Empty-element/default PSVI semantics, IDs/keys/references, the legacy dynamic-type
projection decision and P6-P9 remain open. This increment does not claim phase or
protocol conformance completion. Remote was fetched with no incoming commit;
no main-Qore mutation, installation or push was made.
