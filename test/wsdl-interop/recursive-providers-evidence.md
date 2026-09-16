# Ordinary recursive provider acceptance (P5-20i)

Copyright (C) 2026 Qore Technologies, s.r.o.

Recursive edges previously copied an unfinished field map, so later fields were
missing at nested occurrences. Completed definition references now preserve
conversion and metadata through self/mutual recursion, occurrence copies and
serialization. Validating records expose outer optionality independently of
their deliberately absent single reflected value type. See the
[implemented design and example](../../design/wsdl-recursive-providers.md).

## Verified dependency

Installed Qore `16ae86ca790ae1eaf7135b49af375b1b0813e871` fixes shared-graph
soft conversion. Both blocking core/XML regressions pass. The original core
probe now performs one leaf conversion at each depth 4, 8 and 12, instead of
16, 256 and 4096. Qore's own graph suite passes 11 cases / 80 assertions.
Main Qore was only read. Its source modules and installed ELF/library/reflection
were copied into a new frozen runtime; source hashes were unchanged throughout
the copy. The preceding runtime and historical failure logs are preserved.

## Results

- 186 affected Qore suites: 91,480 assertions, no warnings or errors.
  The documentation target relinked XML after detecting updated Qore tools during
  the initial run. All Qore source/test inputs stayed unchanged. The 37 suites
  that could overlap the relink were rerun against a frozen final XML binary;
  the other 149 already ran after the relink. The final 37-suite recheck, corpus,
  example, documentation, survey tests and Valgrind use that frozen binary.
  `final-check/relink-recheck.json` records the selection and binary hash.
- Recursive providers: 11 cases / 207 assertions, including saved graphs,
  nested soft fields, mandatory NULL rejection, acceptance/return metadata,
  sibling occurrence independence, failed construction/completion, actual
  program interruption, concurrent consumers and WSDL message containment.
- Validating-record optionality: 3 cases / 168 assertions.
- Ordinary/wildcard graph-size bounds: 2 cases / 18 assertions.
- Recursive-provider Valgrind: zero errors and zero definitely/indirectly/possibly
  lost bytes; 125,353 bytes remain reachable in the runtime. Run uses the direct
  frozen ELF, `-b --enable-debug` and `QORE_PCRE2_NO_JIT=1`.
- 17 Python survey tests, WSDL documentation and the shipment example pass.
- Four legacy/native survey/strict-coverage reports differ from P5-20h only at
  `/versions/qore` and `/versions/wsdl_module_sha256`. Historical diagnostic
  failures remain visible; these are not claims of completed P5/P9 conformance.
- Full audit: 22 Pass / 40 N/A / zero Fail across all 62 skill checks.

## Reproduction

The frozen runtime is
`/tmp/wsdl-p5-20i-recursive-providers/fixed-core/runtime/`. Set `LD_LIBRARY_PATH`
to that directory, and `QORE_MODULE_DIR` to the runtime directory, this
repository's `build-debug` and `qlib`, and the runtime's `qlib`, in that order.
Run its `qore -b --enable-debug` with:

```text
test/wsdl-provider-optionality.qtest
test/wsdl-recursive-providers.qtest
test/wsdl-provider-graph-size.qtest
```

The full driver and per-suite logs are under
`/tmp/wsdl-p5-20i-recursive-providers/fixed-core/`; `gate.py`, `run-corpus.py`,
`runtime-provenance.json`, `gate.json` and `corpus-differences.json` retain exact
commands, input hashes and comparisons. The [inventory](P5-20i-validation.json)
records final source/log hashes and the [audit](audits/P5-20i-recursive-providers.md)
classifies every check. C++ is unchanged from `1760935`.

Scoped identity tuples, their complete typed accounting and remaining P5–P9
acceptance remain separate work. No install, push or CI execution occurred.
