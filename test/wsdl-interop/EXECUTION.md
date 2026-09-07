# WSDL/SOAP implementation execution record

Copyright (C) 2026 Qore Technologies, s.r.o.

Execution started 2026-09-07 on `develop` at `c81b2db`, with a clean working tree.
The authoritative scope and acceptance criteria remain in [PLAN.md](PLAN.md).
No phase is complete yet. No scope reductions or workarounds are approved.

## P1: corpus provenance and adjudication (in progress)

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
  which returns HTTP 404. This is outside the 293 echo contracts and remains an
  explicit P1 aggregate-source adjudication item; no original file was changed.

Outstanding P1 criteria: finish aggregate-source/import accounting; tie current
module failures and expected exception categories to the adjudicated ledger;
implement strict selected-corpus Qore reporting, complete missing/unreachable
stage counts and independent request/response runs with actual binding identity;
complete worker cancellation tests, phase checks and the full commit audits.

P2–P9 have not started. Later-phase failures remain recorded in the historical
findings and current diagnostic reports.

## Commit and audit record

- `8914353` — P1-01, `pin W3C corpus and isolate offline schema diagnostics`: verified archive,
  catalog, extraction and resolver-isolation regression. Full 62-item audit:
  [audits/P1-01.md](audits/P1-01.md). All applicable checks pass; language/provider
  checks outside this diff are individually N/A. Committed after tests and the full audit; no push performed.

- P1-02 — independent source adjudication and pinned CXF contracts: 44 Python tests,
  10 Qore interoperability cases and 199 affected Qore cases pass. Both-version
  catalog survey is exactly unchanged from P1-01. Full 62-item audit:
  [audits/P1-02.md](audits/P1-02.md); all applicable checks pass.
