# Native type projection policy and corpus evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The approved default remains `preserve_types=False`. Applications explicitly
choose `True` for native selected-type/value retention; complete XML infoset
preservation uses `XsdXmlValue`. See the [API contract](../../design/wsdl-native-type-values.md).
This increment changes the test harness, reporting and documentation only.

`survey.py` and `coverage.py` accept `--preserve-types`. Each report records
`scope.preserve_types`; absence of the option selects the existing projection.
The internal worker checks the boolean and forwards it to both operation decode
methods. The strict selection and all source/adjudication files are unchanged.

Final evidence is in `/tmp/wsdl-p5-16h-type-projection/`; the committed
[inventory](P5-16h-validation.json) records commands, source and artifact hashes,
test counts and the full [62-check audit](audits/P5-16h-type-projection.md).
Tests use the frozen d66e2 Qore runtime, `-b --enable-debug`, local WSDL and
`build-debug` xml. No native changes, installation or Valgrind run were needed.

| Adjudicated coverage | Legacy default | Preserve types |
| --- | ---: | ---: |
| WSDLs / input message directions | 293 / 2,272 | 293 / 2,272 |
| Invalid-source directions | 176 | 176 |
| Valid inputs assessed | 2,092 | 2,096 |
| Valid inputs requiring fixes | 4 | 0 |
| Broader failure records | 20 | 16 |
| Selected WSDLs / directions passing | 144 / 1,388 | 144 / 1,388 |

Every legacy survey row and every adjudicated case object is identical to
P5-16g; source hashes, catalog and strict selection match between modes. The
four legacy failures are the request/response directions of the original
`TypeSubstitutionUsingXsiType` SOAP 1.1/1.2 inputs. They still fail serialization
with `SOAP-SERIALIZATION-ERROR`. Capturing types lets all four serialize and
validate independently. The 16 broader failures in type-preserving mode are
invalid IDREF/IDREFS inputs still accepted; these remain P5 work.

The corpus reports still explicitly mark typed/infoset comparisons without
assertions as unassessed. Zero valid-input failures in one report does not close
P5 or the overall plan. `test_type_projection.py` separately verifies the original
fixture's two ordered parts, exact number/description fields and expanded
`Part2` type QName in all four output directions. Its eight input/output payloads
validate with pinned Xerces and lxml. The original W3C contract has a SOAP 1.1
binding; its SOAP 1.2 input variant is not claimed as a real SOAP 1.2 binding test.

`test_survey.py` has 17 passing methods. Its new generated contract covers actual
SOAP 1.1 and 1.2 bindings, both directions, omitted/false/true settings, invalid
types/facets and malformed option values. `test_native_type_values.py` and
`test_native_type_providers.py` pass their independent matrices, including saved
values, receiver validation, unchanged default native shapes and selected names.
The 11 affected Qore suites pass 250 cases / 2,686 reported assertions, including
native provider HTTP exchanges, SoapClient and SoapHandler. The legacy SOAP
suite retains its intentional caught comparator-negative assertions.

The full `test_coverage.py` run has 15 passing methods and one method retaining
two previously assigned P6-selected-binding-version failures: a dual-binding
simple-content contract emits SOAP 1.2 for the selected SOAP 1.1 request and
response. The root cause and original reproduction are recorded in the P2
execution entries. These assertions remain failing; no skip or expected-failure
marker was introduced. This is an incremental P5 gate, not phase acceptance.
