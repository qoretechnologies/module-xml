# WSDL/SOAP implementation execution record

Copyright (C) 2026 Qore Technologies, s.r.o.

Execution started 2026-09-07 on `develop` at `c81b2db`, with a clean working tree.
The authoritative scope and acceptance criteria remain in [PLAN.md](PLAN.md).
P1 corpus/adjudication acceptance is complete; P2 namespace/type work is in progress. No scope reductions or workarounds are approved.

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

## P2: namespace, type and attribute resolution (in progress)

- `test/wsdl-namespace-context.qtest` first reproduces declaration-local default
  namespace loss, stale XSD-prefix shadowing, same-local-name type collisions,
  wrong-namespace fallback and lost global-element nillable metadata. Baseline on
  `1854be2`: 8 cases, 2 pass / 6 errors. The implemented increment expands this to
  19 cases covering namespace syntax, scope, reconstruction, rollback and grammar.
- Additional P2 regression: Serializable reconstruction of bare XsdSchema loses all
  element/type maps. These maps are transient and no original XSD sources or rebuild
  hook are retained. WebService has its own deserializeMembers() rebuild path, while
  XsdSchema previously had none. Source retention and reconstruction now pass for
  empty, standalone, multi-namespace and callback-imported schemas and WebService.
- Root code: parseTypes() reconstructs global typed elements with only name/type,
  discarding declaration namespace attributes and nillability; doType()/resolveType()
  use shared prefix/default state and local-name fallback; NamespacePrefixHelper saves
  overridden prefixes only, does not scope new prefixes, cannot reset the default
  namespace to empty, and leaves stale xsd_schema entries when prefixes are rebound.

- P2-01 resolves element/simple-type QNames in declaration-local contexts, retains
  URI identity (including a distinct `{}name` internal key), preserves global element
  attributes and restores complete input namespace maps. QName lexical checks use
  XML 1.0 name ranges, permitting Unicode and rejecting malformed names/colon forms.
- Successful source/dependency retention reconstructs transient XsdSchema registries;
  old standalone serialized data lacking sources now fails descriptively. Failed
  schema additions restore component/import/source state, and retries work on the
  same schema. Provider type metadata and WebService reconstruction are tested, including the
  inherited-options/base-path bug exposed by relative imports during reconstruction.
- Fixing namespace lookup exposed acceptance of two invalid historical descriptions
  whose errors were previously masked. Ordered XSD child/import-position validation
  now rejects all four grammar-invalid archive schemas for the normative reason.
  This necessary regression fix covers XSD construction; complete WSDL grammar stays P6.
- The original `ElementTypeDefaultNamespace` fixture passes both directions, both
  output validators and exact string preservation. Strict selection: 24 descriptions,
  76 message-direction combinations. Current broad echo failures: 440, with phase
  ownership P2=48, P3=208, P4=76, P5=108; no missing/skipped stages.
- Six additional valid historical descriptions now parse; the remaining three
  (`dotnet_cs_2.0.50727.42`, `wcf_cs_3.0`, `zsi_python_2.0`) reach the known P2 builtin
  base defect: complexType finalization strips the namespace and looks up `anyType`
  in the named-type registry. This is the next derivation-resolution increment.
- Additional independent P3 finding: `xs:int` accepts `not-an-integer` as zero through
  permissive `int(val)` conversion in XsdBaseType::deserializeValue(). The P2 collision
  regression uses a valid integer outside the int range to verify correct type selection;
  strict lexical rejection remains an explicit P3 requirement, not a passing test.
- P2 remains incomplete: builtin/complex derivations, remaining QName/ref contexts,
  implicit-prefix handling, import/include/chameleon identity/cycles, attribute
  references/types/use/form/default/fixed, and the additive lossless payload contract.
  Current changes do not alter the public scalar/hash payload representation.

P3–P9 have not started. Later-phase failures remain recorded in the historical
findings and current diagnostic reports.

### P2-02: complex-content derivation

- Seven reduced derivation tests initially all failed on `1a62154`, reproducing
  builtin `anyType` lookup, wrong namespace selection, lost inherited attributes,
  restricted particles incorrectly merged with removed base fields, custom `Array`
  mistaken for SOAP encoding, invalid bases and cyclic derivation.
- Complex-content bases now retain declaration-local URI identity and resolve
  builtin types separately. Empty extensions inherit content/attributes and provider
  field reporting; restrictions retain their declared particle. Finalization marks
  completion only on success and detects cycles before publishing base links.
- All 279 valid echo WSDLs and all 14 valid supplemental contracts now parse. The
  14 invalid echo WSDLs and four grammar-invalid supplemental sources still reject.
  `ComplexTypeAttributeExtension` now retains the inherited `name` element. Its
  original payload is source-invalid: `gender` is on the child instead of the parent.
  Unknown-attribute rejection remains a P2 failure; schema-valid output that drops
  the misplaced attribute is not a passing interoperability result.
- Separate attribute-owner derivatives retain both original/derived hashes and exact
  byte substitutions in `derivatives/manifest.json`. Their original source bytes are
  checked from the archive, never replaced; libxml2/Xerces validate the corrected
  payload and four output directions, with exact `Mary`/`female` ownership assertions.
- Newly reachable independent runtime failures are explicitly assigned to P5:
  `GlobalElementComplexTypeSequenceExtension` needs generic `anyType` content
  handling (valid `data` child rejected), and `MixedComplexContent` needs ordered
  mixed text (valid `^value^` content rejected). Their parse/base resolution is fixed;
  their eight direction failures remain in the report under the original primary P2
  case ownership. No runtime passing claim or skip is added for those messages.
- Simple-content derivation, full particle restriction validation (P4), dynamic type
  identity (P5), and the other listed P2 acceptance work remain outstanding.
- Empty extension/restriction declarations now check key presence even when parsed as
  NOTHING, so missing bases consistently reject with WSDL-ERROR. Invalid SOAP array
  occurrence declarations use the same schema error category.
- Final checks: 235 Qore cases (seven new / 32 assertions) and 59 Python tests pass.
  Strict selection passes all 26 descriptions / 84 directions. Full report: 428
  failures, P2=36, P3=208, P4=76, P5=108; no missing/skipped stages. Every previously
  successful valid stage/output is preserved. Catalog request counts: parse 279/14,
  decode 996/120, encode 994/2, output 948/46; newly reachable failures stay visible.

### P2-03: attribute declaration construction

- The reduced baseline on `592a649` fails all nine original attribute cases. Attribute
  references and anonymous/default declarations leave `type` unset, schema-global
  attributes have no registry, and use validation only runs for explicitly typed
  attributes. Runtime required checks depend on a truthy attribute hash, and the
  prohibited check reads the incoming hash rather than the declaration.
- Global attributes now resolve by captured expanded name, anonymous types use normal
  late resolution, and default types are `xs:anySimpleType`. Contradictory declarations
  and complex/unresolved attribute types fail during schema construction. Global
  registries roll back and reconstruct from original sources, including imported data.
- Declaration form metadata honors local overrides and scoped schema defaults. Runtime
  use checks cover absent attributes and empty values. Scalar anySimpleType handling
  preserves lexical strings and rejects child structures rather than dropping them.
- Strict selection adds AnySimpleTypeAttribute, AnySimpleTypeElement,
  ExtendedSimpleContent and LocalAttributeSimpleType with text and attribute comparisons.
  This fixes the default/anonymous attribute cause in ExtendedSimpleContent; full
  simple-content base/attribute inheritance remains a separate P2 requirement.
- P2 remains incomplete: qualified attribute instance processing (currently local-name
  lookup can drop qualified data), defaults/fixed values, complete attribute groups and
  collisions, builtin/declaration validation, remaining QName/ref contexts,
  import/include/chameleon semantics, and the additive lossless value contract.
- Final verification: 246 Qore cases (11 new / 70 assertions), 59 Python tests,
  strict 30-description / 108-direction gate pass. All previous successful stages
  and wire bodies are unchanged. Full failures: 404 (P2=28, P3=208, P4=76, P5=92).
  Both-version catalog survey: parse 279/14, decode 1014/102, encode 1012/2,
  output 960/52. Newly reachable invalid qualified-attribute outputs remain failures.

### P2-04: simple-content derivation (uncommitted)

- Baseline `4809f18` fails all seven reduced simple-content cases: local base prefix
  loss, complex-base content passed to a scalar decoder without inherited attributes,
  unparsed restrictions, unfinalized anonymous types, inconsistent false/zero/empty
  return shapes, missing-base errors and accepted cycles.
- Current implementation retains expanded bases, finalizes inherited simple content,
  applies restrictions to the effective scalar type, supports inline restriction types
  including the anyType ur-type, and finalizes nested anonymous declarations.
  Eight Qore cases / 43 assertions pass. Broader tests still need final execution/audit.
- The authored `regressions/simple-content` fixture has distinct request/response
  wrappers, inherited required/boolean attributes and 1..3 scalar restrictions, with
  actual SOAP 1.1 and SOAP 1.2 bindings. It exposed a P2 consumer bug: the bare-message
  extractor only inspected complex element members, leaving ^value^/^attributes^
  unconsumed. The extractor now consumes that existing representation explicitly.
- A separate P6 defect remains a failing check in the new Python integration test:
  WSOperation::serializeRequest/Response/Fault use nsc.hasSoap12(), which reflects
  namespace declarations anywhere in the WSDL, instead of the selected binding.
  Selecting Soap11 from this dual-binding contract therefore emits a SOAP 1.2 envelope.
  An asynchronous user question requests permission to fix this bounded prerequisite
  before its scheduled P6 phase. No binding-version implementation was changed while
  that ordering decision is pending. This test is not counted as passing.
- Additional construction work remains for simpleContent restrictions of named
  mixed-content bases with emptiable particles; this needs the P2 schema-content
  predicate coordinated with P4 particle validation. Generic mixed runtime behavior
  remains P5. Full restriction/facet consistency remains part of P3/P4 validation.
- While the bounded P6 ordering decision is pending, local element form/reference
  work continues independently. `wsdl-element-form.qtest` reproduces four failures
  out of five cases. The serializer uses the containing type's form flag instead of
  the element's; refs fall back from absent namespace to the target namespace.
  Declaration-local QName refs and local form overrides now pass five cases / 27
  assertions. ElementFormUnqualified is promoted to the strict selection with exact
  values, and the diagnostic failure count is 400 before final audit/verification.
  Incoming element namespace validation remains a separate P2 requirement.


### Additional P2 work while the binding-order decision is pending (uncommitted)

- Removed the invented input `xsd` prefix while retaining canonical builtin output
  prefixes. Recognized XSD builtin names and declaration NCNames are validated.
  Namespace-context coverage now passes 22 cases / 152 assertions. The legacy
  `binary` HTTP/MIME extension remains recognized and is explicitly distinguished
  from XSD 1.0 builtins.
- Schema composition uses a shared deferred-resolution queue for the complete
  dependency graph, namespace-specific component deduplication, byte caching and
  active source/base identities for root cycles. Chameleon references adopt the
  including namespace. Imports require matching target namespaces; includes allow
  matching or absent target namespaces. Standalone roots must be XSD schema
  elements. Inline schemas no longer inherit the WSDL target namespace.
  `wsdl-schema-composition.qtest` passes 11 cases / 40 assertions, including cycles,
  two-namespace reuse, wrong reference kinds, root validation and rollback/retry.
- The original issue-4449 fixture contains incorrect import namespaces. It is now
  explicitly rejected. `derivatives/Issue4449/manifest.json` preserves original and
  derived hashes and all exact substitutions. The corrected include graph retains
  the duplicate-dependency regression in both soap.qtest and SoapClient.qtest.
  Both independent validators compile the corrected schemas and validate the
  expected payload. Originals remain unchanged.
- `test_composition.py` passes two tests covering eight independent schema graphs,
  positive/negative documents and derivative provenance. libxml2 2.12.10 accepts
  two fetched, unused mismatched imports; Xerces 2.12.2 rejects them with
  src-import.3.1. The normative invalid-source decision and executable oracle
  exception are recorded in regressions/schema-composition/validator-notes.md.
- Simple types now resolve dependency graphs before constructing provider metadata.
  Cycles and complex dependencies fail as WSDL-ERROR; lists require atomic items or
  unions of atomic items. Forward union members retain declared order without
  duplicate resolution, including XML whitespace in memberTypes. Inline restriction
  types are supported; contradictory forms and empty declarations fail explicitly.
  `wsdl-simple-resolution.qtest` failed all six initial cases before the change and
  now passes seven cases / 34 assertions. P3 lexical/value semantics remain separate.
- Latest diagnostic files are /tmp/wsdl-coverage-p2-simple-resolution.json and
  /tmp/wsdl-survey-p2-simple-resolution.json. Coverage retains 400 failures and no
  selected failures (31 selected descriptions / 112 directions); request survey
  parses 279 descriptions and rejects 14 invalid sources, with 1014 decode successes,
  1012 encode successes, 962 independently valid outputs and 50 rejected outputs.
  No phase completion is claimed. Reports still need final regeneration and audit.
- The affected existing Qore suites passed after switching the second issue-4449
  consumer to the provenance-checked derivative. Final full tests, exact-diff audit,
  documentation and commits remain outstanding for these increments. The new
  dual-binding Python test still exposes the independently tracked P6 version bug;
  no binding-version implementation change has been made without the ordering decision.


- Group construction now captures declaration/compositor/reference namespace scopes,
  uses expanded keys without local-name fallback, and rejects missing or cyclic
  definitions even when unused. Nested groups resolve before complex consumers;
  no-namespace public registry aliases remain available. Group-context coverage
  reproduced five failing cases and now passes seven cases / 27 assertions.
  Existing group occurrence/order flattening remains an explicit P4 requirement.
- `test_composition.py` now passes four independent tests: eight composition graphs,
  eight simple dependency graphs, six group graphs, and derivative provenance.
  Xerces 2.12.2 also accepts an invalid list whose item is xs:anySimpleType with
  absent variety; libxml2 and Qore reject it. The explicit normative adjudication
  is recorded beside the earlier libxml2 import limitation.
- Most recent group diagnostic reports: /tmp/wsdl-coverage-p2-groups.json and
  /tmp/wsdl-survey-p2-groups.json; 400 retained coverage failures and zero selected
  failures. Full Python run before the two latest matrix additions ran 62 tests:
  61 passed, the dual-binding P6 test failed. Log: /tmp/wsdl-p2-resolution-python.log.
  It is not a green full-suite result. The full affected Qore run after initial
  group fixes passed; latest small group guards/tests still need final full audit
  checks. No commit or push has been made for this outstanding work.


- Audit preparation reread the full audit-changes skill. Review found that expanded
  attribute/element refs normalized their QName identity but retained whitespace in
  the public field name. A new failing namespace regression proved the mismatch;
  names now use the captured local QName. Namespace suite: 23 cases / 156 assertions.
  Release notes and implemented design now describe the outstanding changes.
  Audit checklist reporting and final tests are not yet complete; no commit gate
  has been claimed to pass.


- Latest full run before attribute-value changes: all 288 affected Qore cases
  passed (logs /tmp/wsdl-p2-review-*.log). Python ran 64 tests with 63 passes and
  the same pending P6 dual-binding failure (/tmp/wsdl-p2-review-python.log).
- Attribute default/fixed work now has six initial cases / 22 passing assertions
  in wsdl-attribute-values.qtest; all six initially failed (one original expectation
  was corrected to inspect the attribute hash, preserving the existing empty-value
  XML representation). Constraints retain their lexical forms, resolve typed values
  after simple-type finalization, inherit through refs, reject inconsistent fixed
  overrides, and populate absent optional attributes. Required fixed attributes
  still require explicit values; serialization/deserialization check supplied fixed
  values. New methods are XsdAttribute::resolveConstraints(), hasValueConstraint()
  and getDefaultValue(). Broader and independent value-constraint verification,
  qualified-attribute integration, documentation and final audit remain outstanding.
  Current runs: /tmp/wsdl-p2-values-*.log; reports
  /tmp/wsdl-coverage-p2-attribute-values.json and /tmp/wsdl-survey-p2-attribute-values.json.


- Independent attribute-value testing uncovered another P2 bare-message extractor
  defect: attributed complex values were left unserialized because the extractor
  consumed only element members and returned NULL for empty content models. It now
  consumes the existing attribute hash for complex messages, including empty models.
  `test_attribute_values.py` validates eight outputs in separate actual SOAP 1.1
  and SOAP 1.2 contracts, both directions, with exact default/explicit/fixed values.
  Twenty documents are checked with pinned Xerces and libxml2; four wrong-fixed
  inputs fail Qore deserialization. This does not alter the pending dual-binding
  P6 test or its failing envelope assertion.
- Three malformed attribute constraints are checked against Qore and Xerces. The
  local-fixed-over-global-fixed mismatch exposes a libxml2 2.12.10 false acceptance,
  adjudicated by au-props-correct.2; see
  regressions/attribute-values/validator-notes.md. Two independent tests pass in
  /tmp/wsdl-p2-values-independent5.log after that explicit oracle adjudication.
- Full Qore tests and both-version diagnostics passed/completed before the final
  attributed-message extractor change; the current exact diff still needs final
  test execution, report regeneration and full audit. Nothing was committed or pushed.


- Qualified-attribute baseline reproduced all five failing cases. Current code
  propagates inherited prefix declarations to attributed SOAP descendants before
  namespace stripping, resolves attribute QNames against the actual input context,
  and matches declarations by expanded identity. Serialized attributes allocate
  prefixes from declaration URIs; local form overrides work independently. Unknown
  attributes on complex/simple values are rejected, except existing schema-instance,
  SOAP encoding and internal transport metadata. No-namespace unqualified attribute
  names never inherit the default namespace. The new suite passes five cases / 13
  assertions before broader verification (/tmp/wsdl-p2-qualified-*.log).
- This namespace increment is still under implementation: same-local-name attribute
  collisions, scalar synthetic/legacy input regressions, broader corpus checks and
  independent qualified-attribute tests require follow-up. Attribute maps still use
  local field names internally, so collision handling has not been claimed fixed.
  The new helper methods are XsdBase::getAttributeNamespaces(), inheritAttributeNamespaces(),
  getExpandedAttributes(), isInstanceAttribute() and validateSimpleAttributes(), plus
  XsdAttribute::getXmlName(). Nothing in binding-version selection was changed.

### P2-04 final incremental audit and verification

- Qualified attributes now preserve namespace identity through SOAP input/output,
  including inherited/rebound prefixes, local form overrides and duplicate local
  names. Unique names keep their existing keys; collisions use expanded keys in
  public attribute maps and `^attributes^`. Reconstruction and both directions
  pass. Eleven initial cases grew to twelve / 189 assertions after prohibition
  checks. The scope/depth tests verify caller immutability, recovery and only the
  required prefix declarations at 128 nested scopes.
- Prohibitions contribute no attribute-use component. Local attribute groups
  resolve before base inheritance; prohibitions cannot remove required base uses
  without a required replacement. The independent composition matrix now includes
  ten group graphs, including live duplicates, repeated prohibitions and invalid
  required-base removal. All four independent composition tests pass.
- Audit found and fixed empty base/itemType exclusivity checks and exponential
  list-item validity traversal on shared union graphs. The twenty-level diamond
  exceeded a ten-second deadline before per-type memoization and now completes
  within the focused suite in under a second. Simple-resolution coverage is eight
  cases / 38 assertions. Attribute maps merge in batches; identical schema references
  reuse successful validation while differing include/import modes are checked.
- The synthetic SOAP response's missing enc declaration remains a negative test;
  its positive copy restores the declaration from the original XML comment. Array
  fragment tests supply their enclosing namespace context. All existing SOAP tests pass.
- Final Qore run: 307 cases pass in 18 suites, with debugging enabled and no warnings
  or unhandled errors (`/tmp/wsdl-p2-audited-*.log`). Python runs 67 tests: 66 pass;
  the dual-binding simple-content test reports two P6 subtest failures for SOAP 1.1
  request/response envelope selection. All its P2 payload checks and 28 independent
  document validations execute before those assertions. This is not a green full
  Python suite. No skip or expected-failure marker was added.
- The P6 finding is independent of these P2 changes: default envelope selection uses
  namespace availability rather than the selected binding. It remains a real failure
  under the execution prompt's explicit routing rule for later phases. The earlier
  phase-order question is unanswered; no P6 code or ordering exception was applied.
- The separate attribute-value and qualified-collision tests use actual individual
  SOAP 1.1/1.2 bindings, both directions, and exact values/expanded names. All three
  Python tests pass, with twenty default/fixed documents and sixteen qualified
  attribute documents checked by pinned Xerces and libxml2.
- Strict coverage grows to 38 descriptions / 140 directions: three positive qualified
  attribute families have exact attribute/child assertions and four invalid families
  must reject. Zero selected failures; 384 broad failures remain: P2=8, P3=208,
  P4=76, P5=92. No new requirement failures or missing/skipped stages relative to
  4809f18. Twenty wire bodies change for defaults/correct qualification; sixteen
  previously serialized source-invalid directions now reject correctly.
- Current reports were regenerated with both versions. Catalog survey: 279/14 parse,
  1006/110 decode, 1004/2 serialize, 960/44 output validation. Stage completion does
  not imply conformance; all original source/historical hashes remain unchanged.
- Full 62-item incremental audit: [audits/P2-04.md](audits/P2-04.md). All applicable
  P2 increment checks pass. This does not close the phase boundary or full-suite gate.

### P2-05 file-relative source bases

- Three new file/directory scenarios reproduced incorrect reuse of the first root's
  directory and failure to restore the initial default on errors. Each file now
  resolves against its own containing directory; successful first additions retain
  the legacy default, and subsequent additions restore the configured default.
  Failed file/directory calls restore the previous default. Successfully added
  files retain their own bases through Serializable reconstruction.
- Composition suite: 14 cases / 66 assertions pass, including missing files, invalid
  roots, exact int/boolean values, directory additions, reconstruction and recovery.
  The source-bases fixture manifest records all five authored files and hashes.
  Five independent composition tests pass; the new case checks both schema graphs
  and four positive/negative oracle payloads.
- Full affected Qore run: 310 cases pass in 18 suites (`/tmp/wsdl-p2-05-<suite>.log`).
  Python: 68 tests, 67 pass and the existing test retains its two P6 version subtest
  failures. The full Python suite is not green. Both-version survey and strict gate
  results are unchanged except the module digest: 38 descriptions / 140 directions
  selected with no failures; 384 complete diagnostic failures remain.
- Complete 62-item audit: [audits/P2-05.md](audits/P2-05.md). No C++ change, push,
  P6 implementation or phase-order exception.

### P2-06 attribute consumer fields and examples

- Provider construction omitted declared attributes on element/empty complex content;
  WSMessageHelper generated scalar placeholders before considering constraints. Seven
  initial consumer cases failed. Attribute fields now expose the existing `^attributes^`
  shape, namespace collision keys, use requiredness, typed defaults/fixed choices and
  typed enumerations. Generated samples use resolved constraints, including false,
  zero and empty strings, on simple/element/empty content.
- Requiredness cannot be inferred from `anySimpleType`/union scalar providers: their
  `auto` type accepts omitted values. `XsdAttributeDataType` enforces attribute presence
  separately, retains scalar/list conversion and makes optional/mandatory variants
  without mutating the source type. Required fixed uses have examples but no default.
- Normative basis: XSD 1.0 Structures sections 3.2 and 3.5, Attribute Locally Valid
  and Attribute Use Properties Correct (https://www.w3.org/TR/xmlschema-1/#cvc-attribute
  and https://www.w3.org/TR/xmlschema-1/#au-props-correct). P3 still owns complete scalar
  value-space semantics. Simple-content provider representation remains open in P2;
  this increment changes only its attribute example generation.
- Focused Qore coverage: 8 cases / 93 assertions, including typed choices, missing and
  invalid values, unknown fields, immutability, namespace collisions and reconstruction.
  All 318 Qore cases pass in 19 suites with debugging enabled, without warnings or
  unhandled errors (`/tmp/wsdl-p2-06-<suite>.log`).
- Four independent attribute tests pass (`/tmp/wsdl-p2-06-independent-final.log`). The
  new worker checks 12 generated payloads from separate actual SOAP 1.1/1.2 bindings,
  both directions; eight also serialize provider-defaulted values. libxml2 and pinned
  Xerces validate all outputs, with exact typed values and qualified names asserted.
- Full Python run: 69 tests, 68 pass, with the same two P6-selected-binding-version
  subtest failures in the remaining test (`/tmp/wsdl-p2-06-python.log`). Final worker
  and exact-type assertion refinements were rerun in the four independent tests.
- Both corpus reports are exactly unchanged from 2387dd0 except the module digest.
  Strict selection remains 38 descriptions / 140 directions with no selected failures;
  384 complete diagnostic failures remain. No phase-boundary or full-suite pass claimed.
- Full 62-item audit: [audits/P2-06.md](audits/P2-06.md). No C++ change or push.

### P2-07 simple-content provider representations

- Attributed simple content now exposes the existing structured `^value^` and
  `^attributes^` representation through XsdSimpleContentDataType. Scalar input stays
  scalar when all attributes are optional; a required attribute requires a hash.
  Optional variants accept an omitted complete value without weakening requirements
  of a supplied hash. Invalid hashes never fall back to scalar conversion.
- Scalar enum choices belong to `^value^`, including in nested elements and message
  parts. The additive getDataProviderAllowedValues() API reports complete-value
  choices; the existing scalar getAllowedValues() API is preserved. Metadata exposes
  a hash for required-attribute types and scalar/hash alternatives otherwise. The
  existing SOAP provider assertion was updated because its fixture requires `info`;
  it now checks the required attribute, scalar field type/choices, exact accepted
  structure and missing-attribute rejection.
- Four new scenarios failed before the change. The consumer suite now passes
  12 cases / 137 assertions, including scalar false/zero/empty values, required and
  optional copies, unknown/wrong fields, nested choices, WebService reconstruction
  and direct Serializable provider reconstruction.
- Qore core prerequisite: `5c8899669`, `fix: retain required hash fields when adding
  defaults`, committed separately on Qore develop. postProcessAddedField forgot a
  required field added before an optional default. The source fix records it in
  either order. Four new core cases / 21 assertions and 45 existing core cases pass.
  Full 62-item core audit: Qore repository
  `examples/test/qlib/DataProvider/HashDataTypeRequiredFields.audit.md`.
- Core AGENTS.md was read and DataProvider-qmod rebuilt with the existing /usr prefix
  and release build. The first attempt detected source changes during compilation;
  the retry succeeded. Optional quictls/LibreSSL CMake messages were recorded; test
  runs have no warnings/errors. No C++ source changed or installation performed.
- All WSDL tests use `QORE_MODULE_DIR=/home/david/src/qore/git/qore/qlib` to load that
  local core fix. Without it, the installed DataProvider still shows the requiredness
  regression. All 322 affected Qore cases pass in 19 suites. Logs:
  `/tmp/wsdl-p2-07-<suite>.log` and `/tmp/wsdl-p2-07-core-*.log`.
- Four independent attribute tests pass, with all 12 new generated payloads now
  passing through provider conversion, including simple content, before serialization
  in both directions of separate actual SOAP 1.1/1.2 contracts. Both validators and
  exact typed/expanded-name assertions pass (`/tmp/wsdl-p2-07-independent-final.log`).
- Full Python run: 69 tests, 68 pass; the remaining test retains the same two P6
  selected-binding-version subtest failures (`/tmp/wsdl-p2-07-python.log`). Final
  metadata refinements were rerun in the affected consumer/SOAP/independent tests.
  Both-version survey and strict coverage are unchanged except the module digest:
  38 descriptions / 140 directions pass; all 384 diagnostic failures remain visible.
- Complete incremental audit: [audits/P2-07.md](audits/P2-07.md). P2 acceptance stays
  open; broader lexical/QName/dynamic/ordered/mixed/wildcard representations and
  remaining namespace/schema checks are still required. No push performed.

### P2-08 compositor namespace scopes

- Tracing incoming element identity exposed an earlier declaration-context defect:
  `parseModelGroup()`, `getChoiceAlternatives()` and `flattenModelGroup()` ignored
  namespace declarations on their compositor. Children with locally introduced
  prefixes failed; rebound prefixes could incorrectly resolve an enclosing type.
  The legacy array element-sequence path had the same omission.
- These four paths now enter the existing exception-safe `NamespacePrefixHelper`
  before constructing children. XML Namespaces 1.0 sections 6.1/6.2 and XSD 1.0
  QName interpretation require the in-scope bindings, including default resets:
  https://www.w3.org/TR/xml-names/#scoping and
  https://www.w3.org/TR/xmlschema-1/#src-qname. No particle algorithm or public
  data representation changes in this increment.
- `test/wsdl-compositor-context.qtest`: the original seven cases all failed before
  the fix. The final eight cases / 55 assertions pass, covering sequence/choice/all,
  nested alternatives, sibling restoration, default/no namespace, deferred type
  and element refs, invalid/unbound namespaces, failed-addition reuse, provider
  metadata, Serializable reconstruction and legacy array element scope.
- `test_compositor_context.py` verifies actual SOAP 1.1/1.2 contracts in both
  directions. Sixteen input/output pairs preserve exact child names and false/zero
  values; all 32 documents pass libxml2 and pinned Xerces. Separate negative checks
  establish that both validators reject all four mixed-alternative payloads.
- The negative experiment independently exposed `P4-nested-choice-exclusivity`:
  `getChoiceAlternatives()` calls `flattenModelGroup()` for a nested choice and
  collapses its mutually exclusive alternatives into one member map. This behavior
  predates the scope guards and is assigned to P4's particle-model replacement.
  `test_nested_choice_exclusivity_requirement_p4` retains four actual failing
  request/response subtests in the normal Python discovery run. No skips, expected
  failures or validator relaxations were added.
- All 330 Qore cases in 20 suites pass with debugging enabled and the local core
  module path (logs `/tmp/wsdl-p2-08-<suite>.log`). Full Python run: 71 tests,
  69 pass; two tests retain six failing subtests (four P4 and the two existing P6
  binding-version failures). No new namespace failures or warnings remain.
- Both corpus reports are identical to P2-07 except the production module digest:
  `0410a173e1a77c795b866e18ce04b1d4e062bf043f38a4ab918af99c1e7dcf4f`.
  Strict gate: 38 descriptions / 140 directions, zero selected failures. Broad
  coverage retains 384 failures, zero missing/skipped cases. Exact recursive JSON
  comparisons checked every report row before replacing the current reports.
- Full 62-item incremental audit: [audits/P2-08.md](audits/P2-08.md). P2 remains
  active; this is not a green full Python run or phase-boundary acceptance.

### P2-09 array item identity and output prefix reservation

- Array construction read `wsdl:arrayType` after stripping attribute prefixes but
  never entered that attribute's declaration scope. Locally introduced/default
  prefixes failed; a rebound prefix could select the wrong same-local-name type.
  Array finalization also repeated a bare local-name lookup after the item object
  was already resolved, making the optional public alias necessary internally.
- The array annotation now has its own namespace guard. Finalization uses the
  resolved item or its canonical expanded registry key and restores its completion
  flag on failure. The named array uses the declaring target namespace rather than
  the SOAP encoding namespace of its base. WSDL 1.1 section 2.2 / array examples
  and SOAP 1.1 section 5 describe the QName-based item annotation and derived array
  types: https://www.w3.org/TR/wsdl.html#_types and
  https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383512.
- The collision regression exposed a second construction error: independent child
  namespace containers allocated prefixes already used by the enclosing registry.
  `merge()` later renamed prefixes after types had cached them. New contexts now
  reserve enclosing output maps through copy-on-write assignment before allocating
  their own prefixes, and reuse the existing target URI's prefix. Added schemas
  and nested imports therefore retain captured output names. Input scopes remain
  local; no global mutable registry was introduced.
- `test/wsdl-array-context.qtest`: five of six initial cases failed before the fix.
  Final nine cases / 46 assertions pass: attribute/default scopes, same-local-name
  and no-namespace items, canonical registries, failed-addition recovery, typed
  values, provider metadata, Serializable reconstruction, and nested output-prefix
  collisions. No array wire algorithm, rank, sparse/reference or SOAP-version
  encoding behavior is claimed here; those remain P8 requirements.
- A concurrent core build redirected `qlib/DataProvider/DataProvider.qmod` to the
  Debug artifact dated September 3, which lacks core fix `5c8899669`. This caused
  one required-field regression with the former source-directory-only module path.
  The source still contains the fix; no core source or symlink was changed here.
  Tests now explicitly prepend `../qore/build/qlib-qmod/DataProvider` before core
  `qlib`, selecting the verified Release artifact, SHA-256
  `6c833e067863e19a1fd2b38761d937c3b5657b890a622f2ecfb67caa215f22c1`.
  README commands use this reproducible dependency selection.
- All 339 Qore cases in 21 suites pass with debugging enabled and the pinned core
  module path. Full Python: 71 tests / 69 passing tests; the same six P4/P6 subtest
  failures remain, with no errors or warnings. Final namespace/composition/array/
  SOAP and four independent attribute tests rerun after copy-on-write refinement.
  Logs: `/tmp/wsdl-p2-09-final-<suite>.log` and
  `/tmp/wsdl-p2-09-independent-final.log`.
- Both final corpus reports retain every previous result, differing only in
  module SHA-256 `b2e2479cb824702e82b6f1321dfc1240ebe7b16c91aa2c4b3c751d3e56c38ca3`.
  Strict gate: 38 descriptions / 140 directions with zero selected failures;
  broad coverage: 384 failures, zero missing/skipped cases. Full incremental audit:
  [audits/P2-09.md](audits/P2-09.md). P2 acceptance remains open.

### Remaining P2 acceptance work

- Incoming element namespace identity and same-local-name element collisions; the
  current element-prefix removal is still lossy. The remaining broad P2 decode
  failures are GlobalElementComplexTypeSequenceExtension and MixedComplexContent
  (four directions each); mixed runtime behavior is coordinated with P5.
- Complete and test the additive public lossless contract beyond attribute keys:
  lexical forms, QName values, selected dynamic types, ordered particles, mixed
  text and wildcard nodes, including client/handler/provider/example consumers.
- Remaining inherited constraint/derivation checks, named mixed emptiable simple-content restrictions,
  and imported-reference permissions.
- P2 phase-boundary acceptance must pass before P3 starts. P3–P9 remain unstarted;
  no push or external publication is authorized or performed.

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

- `1854be2` — P1-04, whole-archive accounting, supplemental source/parse evidence and P1
  acceptance: 58 Python tests and 209 Qore cases pass; original/catalog surveys
  unchanged. Full 62-item audit [audits/P1-04.md](audits/P1-04.md); all applicable checks pass.

- `1a62154` — P2-01 — declaration namespace identity, schema reconstruction,
  rollback and ordered schema construction: 58 Python tests and 228 Qore cases
  pass; 19 new cases / 112 assertions. Every previously successful wire output is
  byte-identical; the fixed W3C fixture adds eight request/response outputs. Full
  62-item audit [audits/P2-01.md](audits/P2-01.md); all applicable checks pass.

- `592a649` — P2-02 — complex-content base identity, inheritance and cycle
  checks: 59 Python tests and 235 Qore cases pass. Complete 62-item audit
  [audits/P2-02.md](audits/P2-02.md); all applicable checks pass. P2 remains in progress.

- `4809f18` — P2-03 — global/anonymous/default attribute type construction,
  declaration form metadata and unconditional use validation: 59 Python tests and
  246 Qore cases pass. Complete 62-item audit [audits/P2-03.md](audits/P2-03.md);
  all applicable checks pass. P2 remains in progress.

- `505a38b` — P2-04 — schema dependency graphs, simple content, group context,
  attribute values and expanded names: 307 Qore cases pass; strict 38-description/
  140-direction gate passes. Full Python run: 66 of 67 tests pass, with the remaining
  test reporting the two explicitly routed P6 binding-version failures. Full 62-item
  incremental audit [audits/P2-04.md](audits/P2-04.md); P2 remains in progress.

- `2387dd0` — P2-05 — per-file schema dependency bases and exception-safe default
  restoration: 310 Qore cases pass; 67 of 68 Python tests pass with the existing
  two P6 subtest failures. Corpus reports unchanged except module digest. Full
  62-item incremental audit [audits/P2-05.md](audits/P2-05.md).

- `6e93367` — P2-06 — complex attribute provider fields and constrained examples:
  318 Qore cases pass; 68/69 Python tests pass with the recorded P6 failures. Full
  62-item audit [audits/P2-06.md](audits/P2-06.md). No push.
- Qore `5c8899669` — P2-07 prerequisite — required hash field tracking independent
  of default insertion order; 49 core cases pass. Full audit in the Qore repository
  at `examples/test/qlib/DataProvider/HashDataTypeRequiredFields.audit.md`.
- `4ae38d1` — P2-07 — attributed simple-content provider fields, scalar compatibility
  and complete-value choices; 322 Qore cases pass, with the two recorded P6 subtest
  failures. Full 62-item audit [audits/P2-07.md](audits/P2-07.md). No push.
- `b67d61c` — P2-08 — compositor namespace scopes; 330 Qore cases pass, with six
  routed P4/P6 subtest failures. Full audit [audits/P2-08.md](audits/P2-08.md). No push.


## P2-24 committed provider prerequisite (2026-09-08)

Core external native worker cleanup is committed to develop as `1e52a0a44`;
its full audit and native barrier/failure tests are in the core ThreadPool test
directory. ThreadPool/async/HTTP regressions pass 78 cases / 555 assertions and
normal native/HTTP/SOAP memory checks have zero errors/lost allocations. The
independent HTTP quoted-boundary fixture correction is commit `4f43e60f7`.
Nothing was pushed and concurrent AOT/Jina/astparser work was excluded.

The XML provider increment is independently validated on parent `4879ed6`:
AUTO probes actual installed namespace identity and falls back to a pinned,
private static libxml2 2.15.4. SYSTEM/BUNDLED, backports, offline/cross builds,
install isolation and source immutability are tested. Its full 62-item final
review is [audits/P2-24-provider.md](audits/P2-24-provider.md), superseding the
provider and callback gates in earlier provisional audits.

The new callback negative tests exposed a libxml2 catalog error ownership leak:
xmlResolveFromCatalog overwrote temporary error strings while restoring a saved
error. Standalone C/GDB reproductions identify the exact overwrite without Qore.
A checksum-verified build-tree copy adds the missing xmlResetError; supplied
source trees remain unchanged and unsupported source changes fail configure.
The C allocation regression fails against pristine upstream (three retained
allocations) and passes against the correction, including prior-error state.
Valgrind reports zero errors/loss (873 allocations/frees). The Qore schema
callback suite also has zero errors/loss and retains original exception kinds.

All 13 CMake integration tests and 238 isolated Qore cases pass. The isolated
both-version corpus is recursively identical to its committed parent apart from
version metadata. All 482 working P2 XML/SOAP cases pass after the final native
change; the native documentation target has no warnings/errors. The wider P2
implementation still has uncommitted increments; P2 acceptance and P3-P9 remain
open. Existing later-phase corpus/Python failures remain visible.

Independent P9 environment findings remain explicit: host glibc 2.43-8.fc44 leaks
TLS storage on actual pthread_create kernel failure (standalone C reproduces it;
Qore rollback checks pass), and Valgrind 3.27.1 emits existing DWARF/fstat tool
warnings. These do not recur as memory errors in the repaired normal native,
HTTP, SOAP or catalog paths. No diagnostic suppression or host library change
was applied. System-provider catalog cleanup needs supported-environment checks.


## P2-25 native XML fragment acceptance (2026-09-08)

The independently validated native increment builds on provider commit `5477680`.
It supports validated ^xml^ element fragments with namespace isolation, retained
lexical text and ordered content; attribute tab/LF/CR preservation; explicit UTF-8
reader byte lengths; exception-safe cleanup and cooperative cancellation. Final
review found and fixed wide output encoding: markup must be generated in an
ASCII-compatible buffer before converting the complete result to UTF-16. Modern
and deprecated XML document/fragment APIs share this behavior. Native helper
symbols have internal linkage through an anonymous namespace.

An isolated checkout on `5477680` passes 249 affected Qore cases. The native suite
passes 11 cases / 256 assertions, including cancellation/recovery and all ten
output variants. Expat and lxml independently validate 40 raw output byte sequences
across four encodings, with exact attributes, lexical text, comments and order.
The final native suite under Valgrind has zero errors or lost allocations, with
existing tool diagnostics retained. The isolated both-version corpus exactly
matches its parent except version metadata. All 483 working P2 XML/SOAP cases
pass; the separate callback suite adds four cases. Native documentation generation
passes with no warnings/errors. No install or push.

Full final 62-item audit: [audits/P2-25-native.md](audits/P2-25-native.md).
Durable implementation contract: [../../design/xml-element-fragments.md](../../design/xml-element-fragments.md).
P2 WSDL/value/consumer increments and documentation build hygiene remain
uncommitted; phase acceptance and P3-P9 remain open.
