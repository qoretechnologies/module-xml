# WSDL calendar canonical constraints (P5-18g)

Copyright (C) 2026 Qore Technologies, s.r.o.

Parent `6bcb9f5` captures canonical IEEE declarations. Calendar declarations
still reused their source lexical forms for canonical assessment. The parent
WSDL accepts all 144 invalid declarations in the 306-schema calendar matrix;
its exact module source and verdicts are under
`/tmp/wsdl-p5-18g-calendar-constraints/baseline/` and `baseline.jsonl`.

WSDL now derives canonical dateTime/time/date text through its existing exact
calendar parser, integer-minute normalization and renderer. Fractions remain
decimal strings, midnight and timezone carries use Gregorian calendar arithmetic,
and extended years retain every digit. Dates keep their recoverable offset.
The selected default/fixed value, original lexical form and declaration scope
remain unchanged after canonical assessment, including list/union reselection.
Duration and partial calendar members retain their XSD 1.0 lexical context.

The normative requirements are XSD 1.0 Part 2
[dateTime](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#dateTime),
[time](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#time) and
[date](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#date), plus Part 1
[e-props-correct.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct)
and [a-props-correct.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#a-props-correct).
The [implemented design](../../design/wsdl-canonical-constraints.md) gives examples.
No rounding heuristic or native floating-point date arithmetic participates.

The matrix covers 162 valid and 144 invalid declarations through all six
element/attribute/reference/simple-content paths, both default/fixed constraints,
lists/unions and duration/partial-calendar controls. The unit suite also checks
saved schemas/providers, selected-member retention and interrupted scope cleanup.
Eighteen additional boundaries cover Gregorian leap centuries, year-zero
crossings, timezone extrema, zero offsets, leap seconds, long fractions and
1,000-digit year carries. Independent ordinal-day and rational-second arithmetic
checks the expected canonical value of every boundary. These are WSDL checks;
they do not imply native extended-year conformance.

The HTTP suite exercises both real SOAP bindings through SoapClient, SoapHandler
and SoapDataProvider, with saved types, both preservation policies, omitted
default attributes, invalid requests/responses and recovery. The independent
WSDL matrix contains 2,214 records: 918 construction checks and 1,296 payloads.
It compares exact calendar/clock values, duration values, selected strings and
expanded QName list members independently of Qore conversion.

Pinned Xerces retains the following explicitly classified differences:

| Stage | Count | Root cause and evidence |
| --- | --- | --- |
| Schema declaration | 24 | Canonical fractional seconds are rounded to binary64, dropping decimal digits. |
| Schema declaration | 24 | Date canonicalization drops the recoverable timezone, changing the interval. |
| Fixed-value instance | 25 | Midnight `24:00:00` retains a next-day anchor while the canonical fixed `00:00:00` uses the original anchor; see the earlier [midnight evidence](native-value-spaces-evidence.md). |
| Fixed-value instance | 5 | Partial-calendar fixed values lose their interval identity during declaration canonicalization: for example `2000+01:00` becomes `1999Z`. The original instance is identical to the declared lexical value and must satisfy its own fixed constraint. |

The original oracle run keeps 306 schemas and 1,602 documents, including all
unreachable and invalid verdicts. Separately identified derivatives remove
exactly one default/fixed attribute from each of 78 affected schemas and validate
702 explicit instances under the retained type restrictions. Independent value
comparisons still require the original selected value; derivative validity
cannot excuse data loss or replace the original declaration/instance verdict.

The native counterpart is a required [outstanding P5 finding](p5-native-calendar-constraints-finding.md).
Its 432 invalid schema acceptances across conversion, DOM and reader stages
remain failures. Native formatting changes fractional seconds, mishandles
midnight/year padding and drops date offsets. This WSDL increment uses exact
existing arithmetic independently and does not suppress those native results.

Reproduction uses the local Debug XML module and repository qlib:

```sh
export QORE_MODULE_DIR="$PWD/build-debug:$PWD/qlib"
qore -b --enable-debug test/wsdl-calendar-constraints.qtest
qore -b --enable-debug test/wsdl-calendar-constraints-http.qtest
python3 -B test/wsdl-interop/test_calendar_constraints.py -v
python3 -B test/wsdl-interop/test_wsdl_calendar_constraints.py -v
```

The default preservation policy remains `False`. Native calendar enforcement,
instance-default PSVI, key/unique/keyref, complete typed-preservation accounting
and P6–P9 acceptance remain active requirements.

## Final acceptance

All 161 Qore suites and 20 supplements pass on unchanged source. The new unit
suite passes five cases/1,477 assertions; HTTP passes one case/88 assertions.
Forced AST/IR/JIT/tiered runs use immediate compilation. Both suites and the
independent WSDL worker also pass using the compiled WSDL module. Both complete
corpus modes match P5-18f at every case, stage, count and scope record. WSDL AOT
and affected API documentation build without warnings. The initial supplemental
calendar run exceeded its 600-second process deadline; its partial log is
retained separately and excluded. The complete unchanged suite was rerun with
a 1,800-second deadline. No C++ change requires
additional Valgrind; the unchanged native dependency retains its prior evidence.

The full audit has 15 Pass, 47 N/A and zero Fail. Source/runtime/test hashes,
commands, summaries and exact comparisons are in [P5-18g-validation.json](P5-18g-validation.json).
Final artifacts are under `/tmp/wsdl-p5-18g-calendar-constraints/final/`;
earlier diagnostic logs are excluded from acceptance. Installed Qore still
matches the verified fixed runtime. No main-Qore mutation, install or push.
