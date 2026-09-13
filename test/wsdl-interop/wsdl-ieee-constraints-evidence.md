# WSDL canonical IEEE declarations (P5-18f)

Copyright (C) 2026 Qore Technologies, s.r.o.

The parent `976fd28` implements native IEEE conversion and canonical constraint
checks. WSDL still captured the original float/double lexical form for its second
declaration assessment. The frozen parent WSDL accepted all 144 invalid schemas
in the 300-declaration IEEE fixture. Baseline source and all verdicts are retained
under `/tmp/wsdl-p5-18f-wsdl-ieee/baseline/` and `baseline.jsonl`.

The new `canonical_xsd_float()` API validates a complete lexical string and
formats its selected binary32/binary64 value through the corrected native APIs.
UTF-8 conversion, embedded-NUL rejection, RAII ownership, categorized errors and
cooperative cancellation protect the public boundary. WSDL canonical capture
uses the original selected identity, including list/union members. The second
assessment cannot replace the published default/fixed value or its lexical
carrier, even when the canonical text selects another union member.

The normative declaration rules are XSD 1.0
[e-props-correct.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct)
and [a-props-correct.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#a-props-correct).
The formatter follows the
[float canonical syntax](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#float-canonical-representation)
with the explicit shortest-round-trip precision policy described in the
[native evidence](native-ieee-constraints-evidence.md). No decimal rounding
heuristic changes the selected value.

`test/wsdl-ieee-constraints.qtest` checks 300 declarations: 156 valid and 144
invalid, across elements, local elements, simple content, attributes, global
attributes and references, including defaults/fixed values and list/union
members. It also checks saved schemas/providers, selected-member retention and
scope recovery after conversion failure or interruption. The HTTP suite checks
both actual SOAP bindings through SoapClient, SoapHandler and SoapDataProvider,
including omitted default attributes, invalid requests/responses and recovery.

The independent WSDL matrix has 2,148 records: 900 construction checks and
1,248 serialized SOAP payloads. It independently compares exact IEEE values,
selected strings and expanded QName list members. The original Xerces jobs
retain 300 schemas and 1,548 documents. All 48 documented schema differences
remain explicit, along with the unreachable instance verdicts: 24 zero-spelling
defects and 24 smallest-subnormal precision choices. A separate set of 48
derivatives removes exactly one default/fixed attribute from each corresponding
schema and checks 432 explicit instances under the retained type restrictions.
The original bytes and declaration verdicts are never replaced.

`test/xsd-float-canonical.qtest` checks formatting, precise rounding, special
values, invalid input, embedded NULs, UTF-16 conversion, long inputs, interruption
and concurrent ownership. `test_ieee_canonical.py` checks 1,314 exact
integer-rational reference cases. The older `xsd-float.qtest` long-input fixtures
now use `strmul()`; Qore's string multiplication expression had performed numeric
multiplication, so those fixtures had not exercised their intended lengths.

Reproduction uses the local Debug XML module and repository qlib:

```sh
export QORE_MODULE_DIR="$PWD/build-debug:$PWD/qlib"
qore -b --enable-debug test/xsd-float-canonical.qtest
qore -b --enable-debug test/wsdl-ieee-constraints.qtest
qore -b --enable-debug test/wsdl-ieee-constraints-http.qtest
python3 -B test/wsdl-interop/test_ieee_canonical.py -v
python3 -B test/wsdl-interop/test_wsdl_ieee_constraints.py -v
```

The installed Qore executable/library match the verified runtime `8c0c22c15`
with scope-cleanup fix `c203380c4`. The acceptance run uses its frozen ELF/library
under `/tmp/wsdl-p5-17b-identities/final/runtime`. PCRE2 JIT remains enabled for
normal runs and is disabled programmatically through `QORE_PCRE2_NO_JIT=1` only
for Valgrind. Main Qore development is read-only in this increment.

These declaration checks leave calendar canonical forms, instance-default PSVI,
key/unique/keyref, complete typed-preservation accounting and P6–P9 requirements
open. The default remains `preserve_types=False`; both corpus modes are assessed
separately and tracked failures remain visible.

## Final acceptance

The unchanged-source gate passes all 159 Qore suites and 22 supplements. The
new API suite has four cases/602 assertions, the WSDL unit suite four cases/1,272
assertions, and HTTP one case/88 assertions. AST/IR/JIT/tiered runs pass with
immediate compilation; both WSDL suites and the independent WSDL worker also
pass with the compiled WSDL module. Both native API suites and both new WSDL
consumer suites pass Valgrind with zero errors and no lost memory. The WSDL
consumer memory runs force AST with a 1,200-second deadline; the initial default
execution run exceeded 600 seconds and is excluded from acceptance. The unchanged
private dependency retains P5-18e's allocation-failure evidence.

Both complete corpus modes match P5-18e at every case, stage, count and scope
record. WSDL AOT and native/WSDL API documentation build without warnings.
The full audit has 22 Pass, 40 N/A and zero Fail. Exact source/runtime/test hashes,
commands, summaries and parent comparisons are in [P5-18f-validation.json](P5-18f-validation.json).
Artifacts are under `/tmp/wsdl-p5-18f-wsdl-ieee/final/`; earlier diagnostic logs
are excluded from final acceptance. Remote fetch found no incoming XML commits.
No main-Qore source change, installation or push was performed.
