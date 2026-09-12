# P5-16d native fixed and scalar value-space evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

Parent: `7927265`. This native prerequisite corrects fixed-value comparison,
clock comparison, unsigned lexical acceptance and allocation-error handling.
It does not close WSDL instance default/fixed or identity-constraint requirements.
The [implemented design](../../design/native-value-spaces.md),
[validation inventory](P5-16d-validation.json) and
[complete audit](audits/P5-16d-native-value-spaces.md) describe the exact change.

## Requirements and root causes

| Requirement | Root cause and correction | Regression |
| --- | --- | --- |
| XSD 1.0 Part 1 [cvc-elt 5.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt) | Simple fixed content compared lexical strings without computing the instance value. The validator computes it and compares typed values, propagating internal comparison errors. Empty lists now have symmetric equality. | Simple and complex simple content; integer/decimal precision, boolean, QName, binary, calendar, duration, string, lists; equal and unequal forms. |
| Selected-type value identity; Part 2 [value spaces](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#value-space) | Primitive families must remain distinct when xsi:type selects a union member. libxml2's anySimpleType string storage now compares consistently with selected strings. XSD 1.0 leaves the anySimpleType lexical/value mapping unspecified; this preserves the existing native string mapping. | Selected boolean/string/integer union members; decimal/integer overlap; string/token whitespace distinctions. |
| Part 2 [time](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#time) | Nonzero timezone normalization invented missing date fields while zero-offset values retained zero date fields. The comparator now uses normalized clock minutes and separate fractional seconds when timezone presence matches. | Fixed/enumeration matrix, day wrap, midnight, fractional seconds, timezone presence, four range facets. |
| Part 2 [unsignedLong](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#unsignedLong) and its unsigned restrictions | The integer branch accepted signs forbidden by the XSD 1.0 unsigned lexical spaces. It now rejects signs before value/range validation. | All four unsigned builtins, signed zero, leading zeroes, whitespace, declaration default/fixed values; nonNegativeInteger remains distinct. |
| Native allocation-error and ownership contracts | Integer allocation errors became datatype violations; NULL list tokens became empty lexicals; failed string copies published incomplete values; the legacy URI parser conflated invalid input and allocation failure. Error propagation, unpublished-value cleanup and xmlParseURISafe correct these paths. | 100 permanent injected failures, invalid input, arbitrary precision, computed scalar/list values, ID, output ownership, cleanup and reuse. |

No rounding heuristic is needed for these corrections. The time fix preserves
libxml2's fractional-second representation, and numeric comparisons retain its
arbitrary-precision integer/decimal values. No public representation changes or
mutable production globals are added. Allocator hooks are test/probe-only.

## Independent and native checks

The final source gate passes all **142 suites, 1,366 cases and 66,465 reported
assertions**, including affected SOAP clients/handlers, schema/provider consumers,
streaming/cancellation and previous native fixes. The existing soap comparator's
intentional assertion-failure self-checks are caught by its negative tests; all
22 cases succeed. No new warning, error, skip or fixture waiver is introduced.

The new Qore suite has four cases/419 assertions and passes in AST, IR and JIT.
The independent matrix covers **95 schemas/774 documents** through DOM, XmlReader
and XmlDoc, asserting rejection categories and original XML preservation where
those APIs return XML data. Pinned Xerces 2.12.2 agrees except for 14 exact
midnight defects, individually recorded in [xerces-time-midnight.json](xerces-time-midnight.json).
The pinned Xerces source demonstrates that its comparison retains an invented
day change for 24:00 with Z or an absent timezone. Every native expectation remains
enforced; classification does not skip validation or convert native failure to pass.

Both selected AOT consumers pass: generic values (10 cases/271 assertions) and
actual SOAP 1.1/1.2 HTTP (four cases/214 assertions). The 16 survey unit tests pass.
All **47 CMake provider tests** pass, including genuine fixed/backported system
libraries, defective-provider detection, missing/offline/cross builds, private
installation, distribution inputs and hash/idempotence checks.

Three affected Valgrind runs are clean:

| Run | Result |
| --- | --- |
| New Qore value-space suite | 4 cases/419 assertions; zero errors or lost blocks; 117,504 runtime bytes reachable |
| Native allocation executable | 100 injected failures; all 1,394 allocations freed; zero errors |
| Complete configure probe | Every behavior passes; all 230,965 allocations freed; zero errors |

Valgrind uses `qore -b --enable-debug` and `QORE_PCRE2_NO_JIT=1` only for the
instrumented Qore process. Ordinary functional checks retain PCRE2 JIT.
Documentation generation and the shipment-cutoff example pass without warnings.
The final native artifacts stayed unchanged throughout the full source gate and
both-version corpus run.

## Reproduction and artifacts

Commands run from the repository root with `build-debug` verified as Debug and
install prefix `/usr`:

```sh
cmake -S . -B build-debug -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build-debug -j4
qore -b --enable-debug test/xml-value-space.qtest
python3 test/wsdl-interop/test_native_value_spaces.py -v
python3 test/cmake/test_libxml2_provider.py -v
python3 test/wsdl-interop/test_survey.py -v
python3 test/wsdl-interop/survey.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 \
  --soap-version both --output /tmp/wsdl-p5-16d-values/final-values/final-survey.json
python3 test/wsdl-interop/coverage.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 \
  --strict --output /tmp/wsdl-p5-16d-values/final-values/final-coverage.json
```

Set `QORE_MODULE_DIR` to this repository's absolute `build-debug:qlib` paths.
Final tests use the byte-identical snapshot of deployed Qore revision
`d66e2cd7e53d7ebe1eb76d52cf1fa75c2061cabe` under
`/tmp/wsdl-p5-16d-values/confirmed/runtime`, with that directory in
`LD_LIBRARY_PATH`. A previous runtime pathname was replaced during Valgrind's
startup symbol reading; its failed run and the confirmed installation race are
retained in `/tmp/wsdl-qore-validation-install-race/README.md`. No main-Qore code
change or installation was needed.

All final logs, deterministic drivers and reports are under
`/tmp/wsdl-p5-16d-values/final-values/`. The provider suite's isolated artifacts are
`/tmp/qore-xml-libxml2-test-x6lwv8iv`; the Valgrind executables were built under
`/tmp/qore-xml-libxml2-test-pv7si_9h` from the identical final native sources and
current tests/probes. The inventory records generated source, runtime, authored
source, fixture and log hashes. Original failing experiments and intermediate
results remain in adjacent directories; they are not acceptance results.

## Remaining acceptance

The complete two-version corpus rows and coverage failures are identical to
P5-16c. All 144 selected WSDLs/1,388 directions pass. Eight valid-input directions
and 24 broad diagnostic failure records remain; these are not claimed as passes.
Original corpus files and historical findings remain unchanged.

[Canonical-default/identity semantics](default-identity-investigation.md) remain
an open P5 adjudication. WSDL instance defaults, fixed values and identity
constraints, the remaining P5 corpus failures and all P6-P9 criteria remain
required. The pre-existing QName AOT stack finding remains assigned to P9.
This increment introduces no workaround or scope reduction.
