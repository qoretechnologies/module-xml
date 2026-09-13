# P5-18a: native canonical numeric declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

Based on `ace866d`, the native schema compiler now checks the canonical spelling
of selected integer, decimal and boolean default/fixed values against the
receiving simple type. The root cause was omission of the second assessment;
the attribute checker explicitly assumed the XSD 1.1 rule instead of the targeted
XSD 1.0 requirement. The correction covers element, simple-content, attribute and
attribute-use paths without replacing declaration values or changing instance PSVI.
See [implemented design](../../design/native-numeric-defaults.md).

The committed `fixtures/numeric-defaults.json` contains 396 schemas: 202 valid and
194 invalid. Its generator and pinned Xerces 2.12.2 agree on every schema and all
reachable documents. Native conversion, DOM and reader APIs pass 987 assertions.
Invalid declarations consistently raise `XSD-SYNTAX-ERROR`. Tests include all
integer families, exact large values, signed decimal zero, both booleans,
singleton/empty lists, mixed numeric/QName lists and string-first union controls.

All 2,394 permanent allocation failures across the three checker entry points
release their owned values. The C test checks exact temporary canonical text and
buffer growth, then repeats successful calls after faults. If an already invalid
canonical pattern runs out of memory while formatting its diagnostic, the native
function retains its positive rejection code and `XML_ERR_NO_MEMORY` context;
otherwise-valid constraints return an internal failure. No failed allocation is
accepted as a valid constraint. Valgrind reports zero errors and zero live native
allocations at exit. The Qore suite also has zero errors and zero definitely,
indirectly or possibly lost bytes under direct-executable Valgrind with `-b` and
`QORE_PCRE2_NO_JIT=1`.

The final gate contains 150 passing Qore suites and 53 passing dependency-provider
checks. The provider matrix verifies real AUTO fallback, SYSTEM rejection,
already-fixed provider acceptance, source preservation and configuration
idempotence. Both complete corpus surveys and both strict coverage runs match the
parent's case, stage, failure and count records exactly. Native mode retains
2,096 valid serialized directions; legacy mode retains its four known dynamic-type
serialization failures. Typed-preservation and later-phase gaps remain visible.
The selected strict scope is still 144 WSDLs and 1,388 directions.

The initial broad run exhausted the `/tmp` quota: two provider checks were
interrupted and 22 Qore suites lost complete output. Superseded build artifacts
were removed; every affected check was rerun successfully. The inventory merges
only complete passing results and retains the failed-environment logs. This was
an environment retry, with no production change or test exclusion.

The build, affected Doxygen targets, independent fixture test and 17 survey
Python tests pass without warnings. Source and runtime hashes stayed unchanged
through the final acceptance run. Installed Qore `8c0c22c15`, including scope fix
`c203380c4`, was used from the verified frozen runtime. No Qore source was changed.

Evidence: `/tmp/wsdl-p5-18-defaults/`, [inventory](P5-18a-validation.json), and
[full audit](audits/P5-18a-native-numeric-defaults.md): 18 Pass, 44 N/A, zero Fail.
WSDL declaration-level canonical checks, instance defaults and key/unique/keyref
remain required P5 work. Float/calendar/binary canonical constraints are not
claimed by this numeric/boolean increment.
