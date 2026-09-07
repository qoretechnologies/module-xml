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
  Historical recovery/source adjudication is still open. Original bytes are never
  replaced or corrected in place.
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

Outstanding P1 criteria: complete offline inventory/catalog and transitive imports;
pin CXF contracts; validate inline schemas and component references; independently
adjudicate every source disagreement; distinguish requests/responses and actual
bindings; implement strict selected-corpus reporting, error expectations, complete
stage accounting, and worker cancellation tests; run phase checks and full audit.

P2–P9 have not started. Later-phase failures remain recorded in the historical
findings and current diagnostic reports.

## Commit and audit record

- P1-01, `pin W3C corpus and isolate offline schema diagnostics`: verified archive,
  catalog, extraction and resolver-isolation regression. Full 62-item audit:
  [audits/P1-01.md](audits/P1-01.md). All applicable checks pass; language/provider
  checks outside this diff are individually N/A. The commit ID is recorded in
  the following execution update after committing.
