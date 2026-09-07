# WSDL/SOAP implementation execution record

Copyright (C) 2026 Qore Technologies, s.r.o.

Execution started 2026-09-07 on `develop` at `c81b2db`, with a clean working tree.
The authoritative scope and acceptance criteria remain in [PLAN.md](PLAN.md).
P1 corpus/adjudication acceptance is complete; P2 is next. No scope reductions or workarounds are approved.

## P1: corpus provenance and adjudication (complete)

- Read the execution prompt, plan, README, historical findings, survey worker/driver,
  regression tests, and applicable instructions. The required audit skill is
  `/home/david/.codex/skills/audit-changes/SKILL.md`.
- Verified archive SHA-256
  `510b1528e5bdaee527c416524e6462c73f5e82b5237af4a4f7fef65904b90aca`.
  The extraction at `/tmp/module-xml-wsdl-survey/` contains all 4,191 archive files;
  all 416 file hashes retained in `findings.json` match the extraction.
- Baseline tests: `qore --enable-debug test/wsdl-interop.qtest` passed 10 cases /
  230 assertions; `python3 test/wsdl-interop/test_survey.py -v` passed 9 tests.
- Both-version baseline: `/tmp/wsdl-survey-baseline-both.json`, 293 WSDLs and
  1,136 messages. Parse: 271 pass / 22 fail; decode: 986 pass / 116 fail;
  serialize: 984 pass / 2 fail; output oracle: 930 valid / 48 rejected /
  6 unassessed; input oracle: 1,020 valid / 104 rejected / 12 unassessed.
  These are diagnostic stage counts, not conformance results.
- Confirmed the old oracle uses separate echo schemas rather than WSDL inline
  schemas. Imported resources must be recovered before drawing conclusions from
  schema-construction errors (the shared parser also retains previous resolver
  errors in later diagnostics).
- Implemented the pinned archive inventory, verified extraction, and immutable
  import catalog (`corpus.py`, `corpus/`). Four dependencies contain valid XML;
  authoritative `Imported.xsd` is zero bytes (HTTP metadata retained in catalog).
  Source adjudication confirms this resource is not a well-formed XML document.
  Original bytes are never replaced or corrected in place.
- Fixed parser exception contamination with a regression that fails on `c81b2db`:
  after a missing import, an unrelated schema's undefined type was reported as
  the earlier import failure. `test_schema_failure_isolation` asserts the actual
  error independently. Each schema/payload now uses a separate parser.
- New tests: 14 passing Python corpus tests; the 9 existing survey tests and all
  10 Qore interoperability cases pass. All seven required SOAP/XSD/client/handler
  suites pass, 199 cases total. `soap.qtest` intentionally catches three failed
  assertions in its comparator negative tests (lines 1448, 1461, 1466); all 20
  cases pass and there are no warnings. Logs: `/tmp/wsdl-p1-tests/`.
- Compared every previously successful worker stage against both new surveys:
  no regression. Without catalog, module stage counts are identical to baseline;
  fixing parser contamination reassesses six `ChoiceChoice` messages as valid
  and two `SchemaVersion` messages as invalid source payloads. With catalog:
  274 parsed / 19 failed WSDLs; 988 decoded / 116 failed; 986 serialized / 2 failed;
  938 oracle-valid outputs / 48 rejected. All 1,136 inputs receive an oracle result
  (1,028 accepted / 108 rejected). This does not establish value preservation or
  resolve the source disagreements. Full current evidence: [current-report.json](current-report.json).

- P1-02 adds the pinned Apache Xerces-J 2.12.2 oracle, eight CXF contracts plus the
  complete schema import graph, component identity inventory, specification
  adjudications and exact numeric/lexical predicates. All 293 echo WSDLs and
  1,136 inputs are assessed against both inline and echo schemas; no source
  disagreement in that set remains unclassified. Findings: 14 invalid generated
  descriptions, 88 invalid source payloads, 1,048 valid payloads. All three retained
  unassessed outputs validate. Full evidence: [adjudication-report.json](adjudication-report.json).
- Newly identified independent findings: dangling IDREF/IDREFS in four fixture
  families, assigned explicitly to P5; obsolete `gMonth` and signed unsigned forms
  accepted by Xerces but rejected by the selected XSD 1.0 rules. Standalone normative
  assertions distinguish these from valid large numbers rejected by libxml2.
- Exploratory xmlschema 4.2.0 (elementpath 5.0.4) additionally accepted undeclared
  ENTITY and signed unsigned values and rejected `ElementTypeDefaultNamespace`
  and `GlobalElementComplexTypeSequenceExtension`. Its element parser uses
  `self.schema.resolve_qname(type_name)` (validators/elements.py:273), losing local
  QName context; its extension handling compares mixedness even for an explicit
  empty sequence (validators/complex_types.py:480). Xerces and libxml2 accept those
  two schemas, consistent with their local namespace and empty-extension rules.
  Exploratory evidence: `/tmp/wsdl-p1-oracles.json`. The committed independent
  oracle uses pinned Xerces and separate normative assertions for its limitations.
- Additional original aggregate-source defect: `examples.xsd` and `examples.wsdl`
  resolve `../static/RelativeIncluded.xsd` to `examples/6/static/RelativeIncluded.xsd`,
  which returns HTTP 404. This is outside the 293 echo contracts and is adjudicated
  in P1-04 as an invalid source location; no original file was changed or URI remapped.

- P1-03 implements `coverage.py` and `strict-selection.json`: all 293 echo WSDLs,
  1,136 originals and 2,272 independent request/response executions. Each direction
  records its inline schema, message/parts, service/port and explicitly selected binding.
  The report retains every serialized body, error category, stage failure and phase owner.
  The 23-description / 68-message-direction strict selection passes, including all 14
  invalid descriptions and selected negative payloads. Missing/duplicate results fail.
- Complete stage counts: parse 274 pass / 19 fail; decode 1,976 pass / 232 fail /
  64 unreachable; encode 1,972 pass / 4 fail / 296 unreachable. Each output oracle
  accepts 1,876 and rejects 96 (different sets); 300 outputs are unreachable. Explicit
  values: 72 pass / 40 fail / 300 unreachable / 1,860 unassessed. Zero missing/skipped.
  The 449 failed requirements remain diagnostic failures, assigned to their phases.
- Exact value checks expose P3 large-integer derivative clamping to signed 64-bit limits
  and decimal exponent output. Schema-valid clamped values are not counted as preserved.
  A regression mutates a boolean to a different schema-valid value and proves the strict
  gate fails it. No production runtime behavior was changed by this test infrastructure.
- Real worker cancellation uses a readiness event and checks that the child is terminated
  and reaped and its manifest removed. Unit tests cover failure/deadline cleanup, malformed
  manifests, stale source hashes and complete stage accounting. A pinned CXF SOAP 1.2
  binding passes separate request/response checks with distinct body QNames and response text.

- P1-04 accounts for all 4,191 archive artifacts and all 48 import edges. The 293
  duplicate standalone schemas are byte-identical; all 568 bare echo payloads and 568
  raw fragments match their corresponding SOAP source content. Unknown dependencies,
  stale evidence, extra files and duplicate IDs are fatal. Full report: `archive-report.json`.
- All 18 additional historical/aggregate XSD/WSDL artifacts receive independent schema
  and Qore parse diagnostics. Four are invalid sources because imports follow declarations;
  the aggregate pair also embeds foreign schema content and references the empty import
  and unavailable relative URL. These are explicit source defects, not missing test setup.
- All 1,136 aggregate SOAP entries contain unqualified wrappers, independently checked
  against their required expanded message-part roots and linked to the original echo files.
  Nine additional valid historical contracts reproduce local default-XSD-namespace loss:
  `Namespaces::doType()` uses shared `default_ns`, then `resolveType()` falls back to an
  unqualified custom `string` lookup (WSDL.qm:7952 and :8595). They are assigned to P2.
- Invalid historical descriptions rejected because of that namespace defect do not gain
  credit for import-order validation. Production grammar rejection remains unassessed in P6.
  Empty-import rejections are recorded as `PARSE-XML-EXCEPTION`; invalid grammar has the
  expected `WSDL-ERROR` category. Full errors and requirement expectations remain visible.
- The 32 output-oracle disagreements are now adjudicated: 16 exact large integers beyond
  libxml2's precision and 16 unchanged invalid IDREF/IDREFS payloads. The latter retain their
  input-rejection failures in P5. This adds no production acceptance or validation exceptions.

### P1 acceptance evidence

| Criterion | Evidence |
| --- | --- |
| Every original file and both SOAP versions accounted for | `corpus/inventory.json`, `archive-report.json`; original hashes unchanged |
| Offline imports, all transitive edges, no unclassified dependencies | `corpus/catalog.json`, `corpus/source-defects.json`, 48 edges in `archive-report.json`; malformed upstream resources classified without substitution |
| Actual inline schemas, wrappers, parts and both direction identities | `adjudication-report.json`, `coverage-report.json`, `contract.py` and tests |
| Historical 52 rejected / 6 unassessed inputs and 3 unassessed outputs adjudicated | `adjudications.json`; pinned Xerces, libxml2 and specification assertions; zero unclassified source disagreements |
| Valid failures remain failures with phase and reproducer | All 449 echo failures belong to P2–P5 (57/208/76/108); nine historical namespace failures belong to P2; file IDs, full bodies/errors and commands retained |
| Source-invalid and oracle-defect coverage | Explicit negative selection with error categories; exact numeric and unchanged-IDREF predicates; aggregate source grammar and QName regressions |
| Strict selected Qore gate plus complete broad diagnostics | 23 descriptions / 68 message-direction combinations pass; all 2,272 combinations retained, missing/skipped zero, unassessed values explicit |
| Worker failure/cancellation and deterministic cleanup | Unit failure/deadline tests plus real readiness-event cancellation/reaping test; no sleeps/polling |
| Pinned CXF contracts and imports; actual SOAP 1.2 operation check | `cxf/catalog.json`; all eight contracts/import graph verified; distinct request/response body and text assertions |
| Tests and commit audit | 58 Python tests; 209 Qore cases; both-version diagnostic surveys unchanged; complete 62-item `audits/P1-04.md` |

P2–P9 have not started. Later-phase failures remain recorded in the historical
findings and current diagnostic reports.

## Commit and audit record

- `8914353` — P1-01, `pin W3C corpus and isolate offline schema diagnostics`: verified archive,
  catalog, extraction and resolver-isolation regression. Full 62-item audit:
  [audits/P1-01.md](audits/P1-01.md). All applicable checks pass; language/provider
  checks outside this diff are individually N/A. Committed after tests and the full audit; no push performed.

- `7a9692e` — P1-02, independent source adjudication and pinned CXF contracts: 44 Python tests,
  10 Qore interoperability cases and 199 affected Qore cases pass. Both-version
  catalog survey is exactly unchanged from P1-01. Full 62-item audit:
  [audits/P1-02.md](audits/P1-02.md); all applicable checks pass.

- `150dc80` — P1-03, strict Qore selection, independent directions and complete reporting:
  54 Python tests and 209 Qore cases pass. Both original/catalog request surveys
  are exactly unchanged from P1-02. Full 62-item audit:
  [audits/P1-03.md](audits/P1-03.md); all applicable checks pass.

- P1-04 — whole-archive accounting, supplemental source/parse evidence and P1
  acceptance: 58 Python tests and 209 Qore cases pass; original/catalog surveys
  unchanged. Full 62-item audit [audits/P1-04.md](audits/P1-04.md); all applicable checks pass.
