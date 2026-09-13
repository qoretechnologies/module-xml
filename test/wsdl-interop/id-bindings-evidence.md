# WSDL ID bindings acceptance (P5-17b)

Copyright (C) 2026 Qore Technologies, s.r.o.

The Qore scope-cleanup prerequisite is resolved by `c203380c4`, verified in the
installed `8c0c22c150c6e51ed09976ca99d74041ec074620` build. All 15 original
scope cases/modes pass with immediate synchronous compilation. The XML code
uses the corrected runtime without a workaround.

WSDL previously validated the lexical spaces of ID, IDREF and IDREFS without
checking the containing document's bindings. P5-17b records successfully selected
identity values and checks their owners when the assessed XML root closes. It
builds on native prerequisite `e1c58e8`; no C++ or private libxml2 change is made.
See the [implemented design and example](../../design/wsdl-id-bindings.md).

The requirement is [XSD 1.0 cvc-id / 3.15.5](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-id).
The 21-schema, 68-document [normative fixture](fixtures/id-bindings.json) includes
42 valid and 26 invalid documents. Its ten differences from pinned Xerces 2.12.2
remain explicitly adjudicated in [native evidence](native-id-bindings-evidence.md).
New [native inputs](fixtures/id-binding-native-values.json) pin the fixture hash
and preserve the source tokens and selected dynamic types. Original corpus files
and classifications are unchanged.

## Verification

`test/wsdl-id-bindings.qtest` passes seven cases and 1,211 assertions. It checks
all fixtures through decoding, serialization, retained XML and saved ordinary,
native and XML providers; 272 SOAP 1.1/1.2 request/response directions; nil;
converter invocation counts; simulated cancellation/recovery; reentrant complete
schema calls; and concurrent saved providers. Normalized value assertions retain
token values/order and expanded selected type names, while ignoring incidental
namespace allocation and native empty-value wrappers. Repeated optional record
metadata is explicitly tested as a list of records, including two supplied IDs.
The root cause was using output-type compatibility (`isList()`) to decide whether
an optional record was already an occurrence list; the check now uses its base
kind (`NT_LIST`).

`test/wsdl-id-bindings-http.qtest` passes one case and 56 assertions. Saved input
and output providers, SoapClient, SoapHandler and SoapDataProvider exchange valid
forward references over loopback HTTP for both bindings. Invalid native requests
fail before transmission, malformed requests fail before callback dispatch,
subsequent valid requests recover, and a separate peer serving a malformed SOAP
response is rejected in both preservation modes. Server cleanup uses lexical
exit handlers; queue completion and network calls have bounded deadlines.

`test_id_bindings.py` checks 340 serialization rows: 68 standalone values and
272 actual SOAP directions. All 130 invalid rows fail with the expected category
and cvc-id diagnostic. Its pinned independent validator assesses 21 schemas and
278 documents: the 68 inputs and 210 emitted valid payloads. Exact expected
Xerces differences are ten inputs and 25 outputs corresponding to five valid
fixture cases; no new disagreement is accepted.

The final 149-suite regression gate passed without test warnings or failures,
with unchanged source and runtime hashes. Both new suites pass in AST, IR, JIT,
tiered and compiled WSDL (AOT) runs. Supplements force synchronous compilation
with `QORE_IR_THRESHOLD=1`, `QORE_JIT_THRESHOLD=1`, `QORE_JIT_SYNC_COMPILE=1`;
the source/AOT independent harness, survey unit tests and affected native-value
and union-identity Python tests also pass. The earlier failed JIT run is retained
under the parent evidence directory and is excluded from acceptance.
The documented example executes successfully.
WSDL AOT and affected WSDL/native API documentation builds are warning-free.
An earlier whole-repository documentation build exposed 22 warnings in seven
unchanged modules; exact diagnostics are retained separately for P9 documentation
integration. They are not described as a warning-free whole-repository build.
No Valgrind run is required for this Qore-only increment.

## Corpus accounting

Both legacy and `preserve_types=True` surveys contain 2,453 rows, eight fewer
than the previous 2,461: eight newly rejected invalid request inputs no longer
reach serialization. Both strict reports account for all 293 cases, both input
SOAP versions and both directions, with no missing/skipped stages. The selected
144 WSDL / 1,388-direction scope remains clean.

All 16 invalid IDREF/IDREFS directions previously accepted by WSDL are now
rejected. No new failure appears. Native preservation mode serializes all 2,096
valid directions and all pass pinned Xerces; legacy mode retains its four
previously documented TypeSubstitutionUsingXsiType serialization failures.
The 56 lxml output disagreements remain accounted for separately. Explicit
value checks cover 1,272 directions, with 824 native / 820 legacy directions
still unassessed for full typed preservation. Passing validity is not proof of
preservation for those directions.

## Reproduction and scope

Acceptance uses the frozen deployed Qore 3.0/API 2.0 runtime `8c0c22c15`, the local
Debug XML module and local qlib. Commands require the pinned corpus and validator
cache described in the main README:

```bash
export PATH=/tmp/wsdl-p5-17b-identities/final/bin:/usr/bin:/usr/local/bin:/bin
export LD_LIBRARY_PATH=/tmp/wsdl-p5-17b-identities/final/runtime
export QORE_MODULE_DIR="$PWD/build-debug:$PWD/qlib"
export QORE_IR_THRESHOLD=1 QORE_JIT_THRESHOLD=1 QORE_JIT_SYNC_COMPILE=1
qore -b --enable-debug test/wsdl-id-bindings.qtest
qore -b --enable-debug test/wsdl-id-bindings-http.qtest
python3 test/wsdl-interop/test_id_bindings.py -v
python3 test/wsdl-interop/test_survey.py -v
python3 test/wsdl-interop/survey.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 --soap-version both --output /tmp/wsdl-id-survey.json
python3 test/wsdl-interop/coverage.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 --strict --preserve-types --output /tmp/wsdl-id-coverage.json
```

Final logs and exact hashes are in `/tmp/wsdl-p5-17b-identities/final/` and
[P5-17b-validation.json](P5-17b-validation.json); the
[full 62-check audit](audits/P5-17b-id-bindings.md) has 15 Pass, 47 N/A and
zero failures.
P5 remains open for empty-element defaults, key/unique/keyref constraints and
complete value-preservation accounting. P6 binding selection failures and P7–P9
requirements remain visible. The approved legacy default is unchanged. No main
Qore change, installation or push is part of this increment.
