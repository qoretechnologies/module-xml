# P5-22b typed corpus accounting

Copyright (C) 2026 Qore Technologies, s.r.o.

`coverage.py` now requires independent typed observations for every serialized
valid input, in addition to output-schema validation and existing normative
assertions. Source and output are assessed by the same compiled inline schema,
with the pinned offline import catalog. Every direction has a `typed_values`
stage; unavailable reference assessments remain explicit failures. Malformed
observations fail the harness instead of becoming production-document verdicts.
The report stores input/output observation hashes and comparator/observer source
hashes so results identify the exact comparison implementation.

The default element-only order is the established `per-name` native-record
contract. Mixed/generic characters and child order, and repeated equal-name
occurrence order, always remain exact. A strict assertion can require the stronger
complete-payload contract:

```json
{"datatype": "typed", "order": "exact"}
```

Only `exact` and `per-name` are accepted; unknown fields and duplicate typed
assertions fail selection validation. Existing scalar/particle assertions remain
mandatory alongside the complete typed comparison. This retains the normative
adjudication of reference defects and stricter particle-specific order checks.
Raw namespace-prefix spelling, unused namespace declarations and equivalent
schema-default materialization do not introduce false value differences.
See [the observer contract](typed-observer-evidence.md) for value representations,
namespace dependencies, supported tree bounds and XML-carrier responsibilities.

`p5-selection.json` preserves every prior strict assertion and adds exact typed
checks for all assigned P5 families plus 13 supporting default/fixed, nil, mixed,
wildcard and abstract-type families. It covers 172 WSDLs / 1,564 directions; the
34 P5 requirement families include expected invalid-source/IDREF rejections.
Historical corpus phase assignments and original source files remain unchanged.
The authored JSON selection is Copyright (C) 2026 Qore Technologies, s.r.o.

Run the native gate against the verified extraction:

```sh
python3 -B test/wsdl-interop/test_typed_coverage.py -v
python3 -B test/wsdl-interop/coverage.py /tmp/wsdl-corpus/databinding/examples/6/09 \
  --preserve-types --selection test/wsdl-interop/p5-selection.json --strict \
  --output /tmp/wsdl-p5-native-coverage.json
```

Run the same selection without `--preserve-types` to report the established legacy
projection losses; that strict run must fail. Keep both reports. Ordinary decoding
still projects an attribute-free nil to `NOTHING`, omits optional `NOTHING`, and
may infer a scalar anyType annotation. Explicit native capture retains presence
and selected type. The compatibility policy is documented in
[nil values](../../design/wsdl-element-nil.md),
[generic values](../../design/wsdl-generic-values.md) and
[type projection](type-projection-evidence.md). The legacy report must not count
schema-valid loss as preserved data or change decoding defaults to hide it.

The integration regression mutates generic text and a scalar boolean while
keeping output schema-valid, removes input/output observations, supplies malformed
observations, checks exact versus per-name order and keeps legacy failures visible.
It also verifies complete selection membership, original assertion retention and
all stage totals. Full reports distinguish native success from compatibility
projection loss. This payload gate does not establish SOAP/HTTP protocol coverage,
complete XML-carrier lexical preservation, attachment/reference behavior or CI
acceptance; those remain governed by their existing tests and P6–P9 requirements.

Final acceptance: native accounting passes all 2,096 valid directions with no
unassessed/missing/skipped typed stage; 176 invalid-source directions reject.
The expanded native strict gate passes and the legacy strict gate exits one with
all twelve expected loss records. Both survey reports are unchanged. Seven new
integration tests and eight affected Qore suites pass; the existing two P6
binding subtests remain failures. Exact commands, source/runtime hashes, report
hashes and diagnostics are in [validation](P5-22b-validation.json); the
[62-check audit](audits/P5-22b-typed-coverage.md) has 11 Pass / 51 N/A / zero Fail.
