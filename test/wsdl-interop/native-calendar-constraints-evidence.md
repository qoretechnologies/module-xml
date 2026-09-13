# Native calendar values and constraints (P5-18h)

Copyright (C) 2026 Qore Technologies, s.r.o.

The predecessor `454486b` fixes WSDL calendar declarations and retains the
[native finding](p5-native-calendar-constraints-finding.md). Native conversion,
DOM and reader validation previously accepted all 144 invalid calendar schemas:
432 invalid acceptances across the 306-schema, 918-stage matrix. Canonical
formatting also changed fractional values, retained hour 24, padded negative
years incorrectly and discarded recoverable date offsets.

The root cause is the native date representation (`long` year and `double`
seconds), coupled to floating-point date addition and fixed-size formatting.
Rounding cannot recover lost fractional digits or repair a changed date interval.
The [implemented design](../../design/native-calendar-constraints.md) replaces
those paths with owned exact year/fraction strings and integer calendar fields.
Copy, cleanup and allocation failures are handled throughout the value lifetime.
Duration operations remain independent and retain their existing representation.

Normative requirements are XSD 1.0 Part 2
[dateTime](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#dateTime),
[time](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#time),
[date](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#date),
[uncertainty ordering](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#dateTime-order)
and Part 1's element/attribute constraint-validity requirements. Leap seconds
follow the value interpretation explicitly approved on 2026-09-10; the published
Appendix E contradiction and preserved value model remain documented in
[temporal evidence](temporal-values-evidence.md).

The expanded seeded comparison matrix identified an additional error in the
independent temporal reference. Comparing unzoned `09:39:60.22` with
`09:39:60.22-14:00` must be indeterminate: the zoned value is the unknown-zone
interval's upper endpoint. The old reference added 840 minutes but retained
second 60, comparing `(23:39, 60.22)` below normalized `(23:40, 0.22)`. The
reference now attaches and normalizes each assumed timezone using independent
ordinal/Fraction arithmetic. Daily endpoints retain their common-date carry.
Explicit reversed endpoint tests cover time and quarter-end dateTime values.
Production WSDL already handled these endpoints correctly.

Historical `temporal-validator-defects.json` remains byte-for-byte intact.
The four native precision reductions now require the normative rejection instead
of the former private-libxml2 false positive. External lxml and pinned Xerces
results remain separately asserted under their unchanged historical records.

The native unit suite covers 306 declarations, 18 exact boundaries, precision
facets, timezone uncertainty, malformed lexicals and recovery across conversion,
DOM and reader paths. Its DOM checks preserve the original document after both
successful and failed validation. Direct native tests copy values, destroy the
original owner, and then format/compare them against 9,807 independent cases
(8,000 valid), with years up to 1,001 digits and exact fractional seconds.

Provider tests check AUTO fallback, SYSTEM rejection, acceptance of corrected
providers, pinned source hashes and idempotence. A deliberately incomplete
provider with exact calendar values but missing declaration enforcement must
still fail. Allocation sweeps exercise value parsing/copy/canonical/comparison
and element/attribute/reference canonical-declaration paths, with recovery and
unchanged original values. The shared numeric declaration sweep now includes
calendar lists, QName unions, selected-member changes and partial-calendar controls.

Reproduction uses the repository Debug XML module and Qore with debugging:

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/xml-calendar-constraints.qtest
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-calendar-constraints.qtest
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-calendar-constraints-http.qtest
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_temporal_values.py -v
python3 -B test/cmake/test_libxml2_provider.py -v
```

Prototype and final artifacts are separated under `/tmp/wsdl-p5-18h-native-calendar/`.
The earlier 10,216-row prototype retains all four initial reference discrepancies;
the committed generator uses only standard-library references and has a distinct
9,807-row matrix. Earlier failed prototype builds and malformed test-data attempts
are not acceptance evidence. Remaining default PSVI, identity constraints, typed
accounting and all P6–P9 criteria stay in scope.

## Final acceptance

All 162 Qore suites, 16 supplements and 61 provider checks pass on frozen source.
The new native suite passes two cases/1,083 assertions in default, AST, IR, JIT
and tiered execution. Compiled WSDL consumers and the independent calendar
matrices pass; WSDL unit and HTTP tests retain 1,477 and 88 assertions.
The direct native reference verifies 9,807 records, including 8,000 valid values.
Six Valgrind runs report zero errors and no lost memory: the native calendar
and value-space suites, AST WSDL HTTP consumer, direct calendar values, and the
105-fault value/3,273-fault declaration allocation sweeps.

Both complete corpus modes match P5-18g at every case, stage, count and scope.
The initial native strict-coverage worker exceeded its 60-second deadline during
concurrent acceptance testing. Its traceback remains retained; the unchanged
command passed when rerun after provider/Valgrind completion, with its original
deadline. Neither a missing report nor the initial failed run counts as acceptance.
WSDL AOT and affected API documentation build without warnings. The full audit
has 19 Pass, 43 N/A and zero Fail.

Source/runtime/generated-source hashes, commands, summaries and exact comparisons
are in [P5-18h-validation.json](P5-18h-validation.json). Final artifacts are under
`/tmp/wsdl-p5-18h-native-calendar/final/`. Installed Qore matches the verified
fixed runtime; no main-Qore mutation, installation or push was performed.
Default PSVI, key/unique/keyref, complete typed accounting and P6–P9 remain active.
