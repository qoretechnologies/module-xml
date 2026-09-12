# WSDL/SOAP implementation execution record

Copyright (C) 2026 Qore Technologies, s.r.o.

Execution started 2026-09-07 on `develop` at `c81b2db`, with a clean working tree.
The authoritative scope and acceptance criteria remain in [PLAN.md](PLAN.md).
P1 corpus/adjudication, P2 schema/representation, P3 scalar and P4 particle acceptance are complete; P5 content and substitution work is in progress. No scope reductions or workarounds are approved.

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

The P2-10 through P2-23 entries below are historical intermediate states. Their
open-gate language is retained as evidence; P2-24 through P2-31 record the fixes
and committed acceptance that supersede them.

### P2-10 — explicit XML values and native element fragments (uncommitted)

- Added `XsdXmlValue`: authoritative XML string, immutable ordered data/reader
  views, root expanded name and scoped QName resolution. Serializable stores
  only XML and revalidates/rebuilds transient views. `getXmlSerializationData()`
  supplies validated native `^xml^` element fragments. Existing SOAP/provider
  values are unchanged; their consumer integration remains required P2 work.
- Native XML generation parses each fragment to EOF, retains and owns its
  element document, isolates default namespace scopes, preserves node order and
  lexical text, rejects malformed values/DOCTYPEs/NULs and supports cancellation.
  XML generation and root checks now preserve the first exception and stop work.
- Root-caused and fixed string-reader encoding corruption: Qore converts strings
  to UTF-8 but libxml2 decoded them again from their original declaration.
  Readers now receive explicit UTF-8 and byte length. UTF-8, Latin-1 and both
  UTF-16 byte orders, NUL truncation and recovery are regression-tested.
- Native Debug configuration uses `/usr` (installed qore `/usr/bin/qore`), CMake
  4.3.0, normal libxml2 parser limits and no installation. CMake policies through
  3.31 remove configuration warnings; build-debug is ignored. An import callback
  exception no longer emits a misleading secondary skipped-import warning.
- Latest focused tests: `xml-literal` 8/44, `wsdl-xml-value` 10/59, XML 25/189,
  stream SAX 5/15, all passing without warnings. The 21 prior WSDL/SOAP suites
  also pass. `test_xml_values.py` checks six original/reconstructed XML outputs
  with exact names, lexical values, QName scope, mixed text, PI/comment/CDATA;
  libxml2 and pinned Xerces agree on all four valid and two invalid XSD cases.
- Full Python: 72 tests, retaining only the six routed P4/P6 subtest failures in
  two tests. Corpus surveys currently retain 384 broad diagnostic failures,
  zero strict selection failures and no missing/skipped cases. Final reports
  were regenerated after the final WSDL documentation edits: only the WSDL
  module digest changes in a recursive comparison of every report field.
- Valgrind found no leaks but reports an uninitialized conditional in PCRE2 JIT
  used by QUnit's call-stack regex. A standalone C reproduction linked only to
  PCRE2 10.47 reproduces it (51 contexts, zero leaks), independently of Qore/XML.
  `--expensive-definedness-checks=yes` does not remove it. See the Valgrind FAQ
  section 5.4: https://valgrind.org/docs/manual/faq.html . Logs and C reproduction:
  `/tmp/wsdl-p2-10-pcre-repro.c`, `...-pcre-repro.log`,
  `/tmp/wsdl-p2-10-literal-valgrind.log`. The required memory-check gate is not
  claimed passing. An asynchronous request asks approval to use a local same-
  version PCRE2 build without JIT solely for valgrind; **no reply yet** and no
  workaround/configuration has been applied.
- Documentation validation exposed an astparser grammar gap: valid Qore brace
  regex operations could not be parsed by Qdx. The bounded core prerequisite now
  uses a stateless C external scanner, compiles/installs it with the generated
  grammar, and preserves existing syntax-node kinds. Node 24/tree-sitter 0.26.8
  regeneration and direct CLI parsing of the complete WSDL source pass. Full
  astparser tests pass 111 cases / 893 assertions; brace/boundary tests pass
  four cases / 101 assertions, including invalid modifiers, form-feed/vertical-
  tab separators, 1,024 nested braces and a 64 KiB replacement body. The initial grammar-only approach accepted inter-part
  comments and shifted unrelated token ranges; the scanner fixes both causes.
  No unrelated core work, source module symlink or installation was changed.
- The astparser valgrind run passed its four cases / 101 assertions with zero
  definitely, indirectly or possibly lost bytes, but the same PCRE2 JIT issue
  reported two contexts. The native memory-check gate remains open.
- XML/WSDL/WebContentUtil documentation now builds without warnings, including
  the final pass with all cross-reference tags. CMake uses explicit public QPP
  declarations and the actual docs/ asset path, preserves caller-supplied core
  tags and builds user-module tags before the final native documentation pass.
  XML generation options were moved from an unexported implementation comment
  to a public page. Stale parameter/link markup, duplicated language flag anchors
  and WebService's detached class comment were corrected. WebContentUtil edits
  affect documentation only; its 85 cases / 346 assertions pass.
- Core documentation's Java-wrapper step exposed a separate JNI exception bug:
  `JniCallStack` passed Java's native-frame line `-2` to Qore, which permits only
  `-1` as an unknown location. GDB identifies `defs.cpp` via the installed JNI
  module; a focused System.arraycopy(null,...) regression aborts before the fix.
  The local module-jni prerequisite normalizes lines below -1, preserving positive
  lines, Java exception identity and frame type. New tests pass 2 cases / 20
  assertions; eight selected existing exception/stack/callback/lifecycle cases
  pass 58 assertions (49 unrelated cases excluded by the explicit filter).
  The complete astparser docs commands, including Qjar, pass without warnings
  with this local JNI module prepended. No installation or core build-file change
  was needed. JNI valgrind completes all 20 assertions, but reports 54,041
  definitely lost bytes plus JVM stack-probing/GC diagnostics. Standalone
  OpenJDK 25.0.4.1 `java -version` reproduces JVM stack diagnostics (109 contexts)
  and its own shutdown allocations. Those are separate from a real JNI leak:
  64-byte Class wrappers allocated by findCreateQoreClass are not owned on early
  duplicate/recursive returns from createClassInNamespace. A SimpleRefHolder now
  guards the wrapper until setManagedUserData takes it. An import-only variant
  with test execution commented out isolates this leak from exception handling;
  the import-only baseline reproduces exactly the same 843 leaked wrappers /
  53,952 bytes as the complete test, proving the leak occurs before either test
  case runs. The final Debug rebuild and tests pass: 2 new cases / 20 assertions,
  plus 10 selected existing cases / 62 assertions including recursive code
  generation (47 unrelated cases explicitly excluded). Final valgrind eliminates
  all 843 leaked wrappers. Its remaining direct losses are 33 bytes in JVM
  PerfMemory initialization and 56 bytes in WatcherThread startup; 3,795 bytes
  are indirectly lost and 611,384 possibly lost. All remaining loss allocation
  stacks originate in JVM allocation or JVM-created thread TLS. An independent
  C JNI invocation/lifecycle reproduction links only libjvm and reproduces the
  identical 33-byte PerfMemory, 56-byte WatcherThread and 3,795-byte indirect
  losses after DestroyJavaVM. Its smaller workload reports 215,712 possibly
  lost bytes and 211 contexts; the larger module workload is not claimed
  byte-identical. Source and log: `/tmp/wsdl-p2-10-jvm-invocation.c` and
  `/tmp/wsdl-p2-10-jvm-invocation-valgrind.log`; hashes are recorded in the JNI
  audit. No leak suppression or JVM configuration workaround has been applied.
- User handoff: the user is taking the astparser audit/commit in parallel. Its
  implementation is stable (115 cases / 994 assertions, warning-free docs using
  local JNI). modules/astparser/ and design/astparser-brace-regex.md are frozen
  for that review, including the existing 62-item audit with its open PCRE2 gate.
  This task continues XML/JNI work and will not stage or commit astparser paths
  while the user owns that review.
- Logs: `/tmp/wsdl-p2-10-final-<suite>.log`, `...-python.log`,
  `...-independent.log`, `...-cmake.log`, `...-build.log`, `...-docs.log`.
  API/release documentation and durable `design/wsdl-xml-values.md` are drafted.
  Full final-diff audit and a commit remain pending the required checks.
  Current source SHA-256 is `15eb3f9f0fcd5f3bc0335efbd51ae4914d098c14f7ed08bb30ae470467534bbc`;
  native Debug artifact is `dc1fadc47062c8d809cd8e04ffb8611edd2ffe03baf08b26f284b5cedbd98372`.
  `get_module_hash().xml.filename` confirms the local build-debug binary is loaded.
  Final reports were compared recursively and copied to current-report.json and
  coverage-report.json: only the WSDL digest changes. All 387 Qore cases in 25
  suites pass; the added negative native assertions do not change the case count.
- Final affected XML memory runs pass all 48 cases / 307 assertions with zero
  definitely, indirectly or possibly lost allocations in every suite. Memcheck
  still reports conditional branches on uninitialized values in generated code:
  xml-literal 1 context, xml 137, InputStreamSaxIterator 128, wsdl-xml-value 120.
  These remain visible pending PCRE2 diagnostic adjudication; no suppression or
  disabled JIT has been applied. Logs: `/tmp/wsdl-p2-10-valgrind-<suite>.log`.

### P2-11 — incoming element namespace identity (in progress, uncommitted)

- Document body and header elements are matched by expanded name before schema
  decoding. Local qualification defaults/overrides, default namespace resets,
  aliases and per-element rebinding are checked in their actual XML scope.
  Malformed names, unbound prefixes, invalid bindings and duplicate expanded
  attributes fail with `SOAP-DESERIALIZATION-ERROR`; caller data is unchanged.
- The generic `expandElementNamespaces()` helper retains distinct namespace
  identities, occurrence order and false/zero/empty values. Scope restoration
  uses one traversal map rather than copying ancestor bindings to descendants.
  Review found growing repeated-list copies; accumulation now promotes once
  and appends in place. A 4,096-value alias regression checks exact order/content.
- `restoreElementNamespaces()` prepares expanded wildcard names for XML output,
  reserving retained namespace prefixes and lexical `qorexmlN:` references so
  allocation cannot overwrite or accidentally create a QName binding. Empty
  namespaces explicitly reset defaults; the XML namespace uses `xml`.
- SoapHandler now inspects a copy for operation routing. Its former namespace
  removal injected a synthetic `ns` member into the message passed to decoding.
  A real HTTP SOAP 1.2 test rejects a wrong payload namespace and then accepts a
  valid request on the same server; 17 cases / 106 assertions pass.
- Latest full Python run: 74 tests, with only the six already-routed P4/P6
  subtest failures. New independent element tests assess 56 documents using
  lxml and pinned Xerces, checking exact expanded names, lexical values, order
  and QName bindings in requests/responses through actual SOAP 1.1/1.2 bindings.
- Latest diagnostic reports: `/tmp/wsdl-survey-p2-11-restored.json` and
  `/tmp/wsdl-coverage-p2-11-restored.json`. Request survey: 293 descriptions,
  1,136 messages, 279/14 description parses, 1,006/110 decodes, 1,004/2
  serializations, 972/32 output verdicts; valid-input/invalid-output decreases
  from 20 to 8. Full broad failures decrease from 384 to 360; strict selection
  still has zero failures. No new corpus failures; repository reports remain
  at P2-10 pending final review. Earlier transient Clark-name XML generation
  failures were root-caused and fixed by the inverse namespace conversion.
- Still open: schema maps overwrite same-local-name declarations from different
  namespaces; this increment does not yet repair declaration indexing. A
  wildcard-only top-level type is treated as empty by the existing unwrapped
  argument inference; explicit root wrappers work and are exercised here.
  Track and fix bare wildcard consumption in the remaining P2 consumer work.
  Full wildcard validation/mixed-content semantics remain assigned to P5.
- Final affected run passes 361 cases across 23 Qore suites, including 11
  namespace cases / 271 assertions. Final survey/coverage results differ from
  the previous improved run only in the WSDL digest and have been copied to
  the repository. WSDL SHA-256:
  `d49373f3a9d3414f88a857ff825f147debb83c1528140d7c390bb6d61cbb866d`.
  WSDL and SoapHandler API docs pass without warnings after correcting the
  latter's logging parameter markup. Full 62-item incremental review:
  [audits/P2-11.md](audits/P2-11.md). No C++ edits in this increment.
  The separate P2-10 PCRE2
  memory-check decision remains open; no workaround has been applied. Astparser
  paths remain owned by the user's parallel audit and have not been touched.

### P2-12 — colliding element declaration fields (in progress, uncommitted)

- Five initial regressions fail before the fix because parseElements and group
  maps overwrite same-local-name fields. Internal construction now retains
  expanded identities, including deferred imported/no-namespace references.
  Final field mapping considers the whole type and its choices: unique local
  names remain compatible, while colliding names use expanded keys.
- Base and group maps are reindexed during composition without renaming their
  source fields. All complex types enter the finalization queue, including
  nested anonymous types that were previously omitted. The resolver only
  attempts simple-type resolution when that metadata exists.
- XML serialization uses declaration names separately from public field keys.
  Provider fields already consume the finalized maps; WSMessageHelper now uses
  those field keys when assembling nested/choice examples. The first example
  regression failed from the previous local-name overwrite before its fix.
- New Qore suite currently passes six cases / 76 assertions. The first 24-suite
  affected run passed with no warnings; a final rerun is pending the example
  change. Independent tests pass two cases covering 136 documents against both
  lxml and pinned Xerces: 124 original/emitted namespace/content variants plus
  12 generated/provider/reconstructed examples, actual SOAP 1.1/1.2 bindings and
  both directions. Exact XML names/order/text and boolean/integer types are
  checked, as are SOAP-DESERIALIZATION-ERROR rejections.
- Normative basis: XSD 1.0 element declaration target namespace/form and
  declaration validity; distinct namespace/local pairs identify distinct
  declarations. This increment does not implement P4's repeated-particle model,
  or resolve the remaining same-local-name multipart WSDL message restriction.
- Logs: `/tmp/wsdl-p2-12-collisions-red.log`, `...-examples-red.log`,
  `...-collisions.log`, `...-independent.log`, `...-affected.log`.
  Final 24-suite affected run passes 367 cases, including the six new cases /
  76 assertions. Full Python discovery runs 76 tests with only the same six
  P4/P6 subtest failures. WSDL docs build without warnings. Final corpus reports
  are recursively identical to P2-11 apart from the WSDL source digest and have
  been copied to the repository. Source SHA-256:
  `1cb087938843d8b6909e8f6382e45b1ae428a2740edbcf2c42606680e2a80995`.
  Full 62-item incremental audit: [audits/P2-12.md](audits/P2-12.md).
  P2-10's native memory decision remains open; no native changes, astparser
  edits, installation, commits or push have been performed in this increment.

### P2-13 — WSDL message part identities (in progress, uncommitted)

- Four initial message regressions fail with WSDL-ERROR for ambiguous local
  element name `item`, despite three distinct namespaces. WSMessage now resolves
  parts in their message/part XML scope, counts local aliases after resolution,
  and uses expanded argument keys where element names collide. Distinct part
  names remain the provider/message data keys.
- An unprefixed `part.element` formerly used the WSDL target namespace through
  getNamespaceUri(); it now resolves the actual XML default namespace, including
  explicit resets. Malformed/unbound QNames and wrong referenced identities
  reject; scoped rebinding restores the outer namespace context.
- Element wire names are independent of internal argument keys, including
  no-namespace document roots. WSMessageHelper generates all parts for messages
  with multiple parts while retaining its existing single-part return shape.
- New Qore suite currently passes four cases / 65 assertions, covering actual
  SOAP 1.1/1.2 body/header parts, both directions, ambiguous/wrong inputs,
  providers, generated samples and Serializable reconstruction. Logs:
  `/tmp/wsdl-p2-13-message-red.log`, `...-message.log`, `...-affected.log`.
- Remaining duplicate references to the identical expanded element and complete
  RPC part/protocol semantics are still tracked under P6. This increment fixes
  distinct element identities; it does not claim the existing identical-element
  restriction is required by WSDL. Normative reference is the pinned WSDL 1.1
  Note, sections 2.3, 3.5 and 3.7:
  https://www.w3.org/TR/2001/NOTE-wsdl-20010315 (the generic /TR/wsdl URL now
  redirects to WSDL 2.0, which is outside this plan).
- The independent multipart matrix additionally exposes P3 integer lexical
  rejection: `xs:int` text `invalid` becomes integer zero through the existing
  scalar conversion. Eight explicit failing subtests (body/header placement,
  requests/responses, both SOAP versions) retain the required
  SOAP-DESERIALIZATION-ERROR assertion under `P3-integer-lexical-rejection`.
  This is a separately routed scalar defect, not a passing namespace test.
- Final focused suite passes five cases / 80 assertions, adding message-level
  scope and type/element part alias collisions. All 24 other affected suites
  pass (372 combined Qore cases). The independent test completes all 160
  element-document checks with both validators and exact values/types/placement;
  only its eight explicitly routed P3 subtests fail. Full discovery runs 77
  tests with 14 subtest failures: eight P3, four existing P4 and two existing P6.
  WSDL docs build without warnings. Survey and coverage compare recursively
  identical to P2-12 except source digest and have been copied to the repository.
  WSDL SHA-256:
  `11c598aec866cbcf6d31babc80f84961f668cd7cb8a80635e7f37b718e235252`.
  Full 62-item incremental audit: [audits/P2-13.md](audits/P2-13.md).
  No native or astparser edits; P2-10's memory-check decision remains open.

### P2-14 — inherited attribute constraints (implemented, uncommitted)

- Root cause: complex-type finalization replaced inherited attributes without
  checking requiredness, fixed constraints or simple-type ancestry. The same
  override merge also hid duplicate extension uses. Inline simple-content types
  were accepted without checking their relation to the effective base content.
- Restriction replacements now use expanded attribute identities and preserve
  required/fixed constraints. Type ancestry follows declared/builtin restriction
  links and list/union rules, with a per-check type-pair memo. Extensions reject
  duplicate expanded uses; omitted restriction attributes remain inherited per
  the XSD 1.0 complex-type property mapping. Base fields remain unchanged.
- New `test/wsdl-attribute-derivation.qtest`: seven cases / 69 assertions,
  including negative declarations, builtin/named/list/union ancestry, qualified
  collisions, inline content, provider values, Serializable restoration and
  failed-addition recovery. Six cases failed before the fix for missing WSDL-ERROR.
- New `test_attribute_derivation.py`: 44 schemas through 88 actual SOAP binding
  parses and 40 independent request/response payload checks with exact zero/false
  values. Both tests pass with lxml and pinned Xerces. Six fixed-constraint cases
  explicitly record libxml2's erroneous acceptance; Xerces and Qore reject in
  accordance with derivation-ok-restriction.2.1.3. No skipped disagreement.
- All 25 other affected suites pass (379 combined Qore cases). Full Python runs
  79 tests with only the 14 already tracked P3/P4/P6 subtest failures. WSDL docs
  build warning-free. Logs `/tmp/wsdl-p2-14-{focused,affected,independent,python,docs}.log`.
  Both-version survey and coverage are recursively unchanged apart from the
  verified source digest: `f8e6bbc1158b4cbd57a00e07da79a5b5f060a3948cb4c474d6970a3e906d7c78`.
  Current reports refreshed; strict failures zero, broad failures 360.
- References: https://www.w3.org/TR/xmlschema-1/#derivation-ok-restriction,
  #cos-st-derived-ok, #ct-props-correct and complex-type property mapping;
  second-edition errata checked. Full 62-item audit [audits/P2-14.md](audits/P2-14.md).
  Native P2-10 gate remains open; no astparser changes or commit.
- Remaining constraints: attribute wildcard composition/admission for newly
  introduced restriction uses, named mixed emptiable simple-content bases,
  contradictory element declarations and import-reference permissions. Scalar
  facet/value validation stays in P3; full final/block behavior in P5.

### P2-15 — named mixed emptiable bases (implemented, uncommitted)

- Root cause: simple-content finalization rejected every named base without
  simple content; construction had discarded effective mixed flags and nested
  emptiability information. Named groups also resolved only direct references,
  leaving missing/cyclic references inside compositors unchecked.
- Retains an internal typed tree for the XSD Particle Emptiable predicate, with
  captured expanded group identities and per-group result caches. Every nested
  reference is checked, including optional branches. Mixed flags follow
  complexContent/complexType precedence; genuinely empty effective content in an
  extension inherits the base's properties, including the anyType ur-type.
  Empty effective content is distinct from a nonempty but emptiable particle.
- Named mixed emptiable bases now allow simple-content restriction with an
  inline simple type, outer facets and inherited attribute constraints. Existing
  scalar/hash return shapes are preserved. Full ordered instance matching and
  general mixed-content preservation retain P4/P5 ownership.
- New `test/wsdl-mixed-base.qtest`: final six cases / 61 assertions, including
  provider/native values, group scope/cycles, required/optional particles,
  declaration flags, failed-addition recovery and a shared 32-level group graph
  before/after reconstruction. Four of the five initial cases failed before the
  fix. All 26 other affected suites pass: 385 combined Qore cases.
- New `test_mixed_base.py` and `mixed-base.qr`: 35 independent schemas and 28
  SOAP documents, actual 1.1/1.2 bindings, both directions, reconstructed
  WebService providers/examples and exact integer zero/attribute/name checks.
  Both Python tests pass. lxml's dropped outer facets (four negative documents)
  and incorrect mixed=false/0 override (two invalid schemas) are explicitly
  recorded oracle defects; Xerces and Qore enforce the XSD 1.0 mappings.
- Full final Python run: 81 tests with only 14 tracked P3/P4/P6 subtest failures,
  no new failures/skips. WSDL docs are warning-free. Logs:
  `/tmp/wsdl-p2-15-{focused,affected,independent,python-final,docs}.log`.
  Both-version request survey/full coverage compare unchanged except digest;
  current reports refreshed, strict failures zero, broad failures 360.
  WSDL SHA-256:
  `dfe994b06eaaee51bbf9576ed038c2bb951ccc69b74ce7bae70540b5128acaf9`.
- Full 62-item audit [audits/P2-15.md](audits/P2-15.md); references are XSD 1.0
  complex-type property mapping, src-ct, cos-group-emptiable and
  derivation-ok-restriction. Snapshot `/tmp/wsdl-p2-15-pre-reference-permissions-WSDL.qm`.
  P2-10 native decision remains open; no astparser changes or commit.

### P2-16 — source-local reference permissions (implemented, uncommitted)

- References now require imports in the referencing schema document, even when
  another source already loaded the components. Construction scopes restore the
  permission map on every exit; includes/imports receive their own scopes.
- Import checks and reference cache keys distinguish absent namespace attributes
  from explicit empty values. Empty/whitespace targetNamespace declarations fail
  with WSDL-ERROR; malformed/unbound QNames retain WSDL-NAMESPACE-ERROR.
- New `wsdl-reference-permissions.qtest` passes five cases / 53 assertions,
  covering nine reference kinds, transitive/include scopes, cached imports,
  reconstruction and recovery after failure. The corrected baseline reproducer
  fails four of five cases for missing WSDL-ERROR. All 28 affected suites pass:
  390 Qore cases (`/tmp/wsdl-p2-16-affected.log`).
- Independent tests pass 29 schema graphs and 24 SOAP documents through actual
  1.1/1.2 bindings in both directions, with provider/example/reconstructed-service
  consumers and exact expanded names, integer zero and boolean false values.
  Seven libxml2 and two Xerces schema verdict discrepancies are separately
  asserted against the normative src-resolve/src-import rules; no skipped cases.
- Three Qore-authored SOAP fixtures add their missing encoding namespace imports.
  Pinned upstream files are unchanged. Full Python: 83 tests, only 14 tracked
  P3/P4/P6 subtest failures. WSDL docs build without warnings/errors. Logs:
  `/tmp/wsdl-p2-16-{independent,python,docs}.log`.
- Survey/coverage retain all counters, stages and classifications: zero strict
  failures, 360 broad failures. The already-invalid SOAPEncodedArray source now
  fails earlier on an unimported WSDL-namespace QName, still WSDL-ERROR. Reports
  record the externally changed installed Qore revision `0817c849f2db`; this
  execution did not modify or install Qore. Local Debug XML artifact is unchanged.
  WSDL SHA-256:
  `4faccd75b554d33c005383726a86ab072aabc2e6f91fa29e3749c8da38aa5e80`.
- Full 62-item audit: [audits/P2-16.md](audits/P2-16.md). P2-10's native memory
  verification decision remains open. No astparser edits, commit or push.

### P2-17 — element declaration consistency (implemented, uncommitted)

- Root cause: field maps overwrote same-name declarations before their type
  identities could be compared. Named groups omitted nested compositors.
  Construction now retains declarations, resolves their types and checks expanded
  element identities before field/occurrence merges. Nested group fields reach
  existing provider/example consumers.
- Distinct declarations with one expanded name require the same named type.
  Repeated references to one declaration retain its anonymous type identity;
  separate but textually identical anonymous declarations conflict. Extensions
  combine base declarations; restrictions use replacement content. Ordinary
  optional particles contribute declarations; zero/zero particles do not.
- New `wsdl-element-consistency.qtest`: seven cases / 49 assertions pass, including
  nested/unused groups, namespace/scope separation, forward references, inherited
  content, failed-addition state restoration and a shared 32-level group graph
  before/after reconstruction. Isolated P2-16 baseline fails five of seven cases.
- New `test_element_consistency.py`: 30 schema graphs through 60 actual 1.1/1.2
  binding parses and 20 SOAP documents in both directions, with exact names,
  order, integer zero/boolean false and reconstructed provider/example consumers.
  Both tests pass. libxml2's 13 accepted conflicts and two rejected valid +00
  occurrence spellings, and Xerces's two unchecked unused groups, are recorded
  explicitly against XSD 1.0 cos-element-consistent/property mappings.
- All 29 affected Qore suites pass: 397 cases. Full Python: 85 tests with only
  14 already tracked P3/P4/P6 subtest failures, no new failure/skip. WSDL docs build
  without warnings/errors. Logs `/tmp/wsdl-p2-17-{affected,independent,python,docs}.log`.
  Both corpus reports are recursively unchanged except module digest, with zero
  strict failures and 360 broad failures. Current reports refreshed.
- WSDL SHA-256:
  `ed4e9532cfa12e67c8a1798a48a2c49bdec8e7288217e6aad0c18fe458bffe26`.
  Full 62-item audit: [audits/P2-17.md](audits/P2-17.md). P4 ordered matching and
  P5 substitution-group implicit declarations retain their phase ownership.
  P2-10 native memory decision remains open. No astparser edits or commit.

### P2-18 — attribute wildcard construction (implemented, uncommitted)

- Root cause: wildcard namespace/processing constraints were discarded; the
  anyAttribute boolean also represented element wildcards. Restrictions could
  introduce attributes without base namespace permission and accept invalid
  wildcard changes. Typed metadata now preserves source-local namespace tests,
  group intersections, extension unions and restriction subsets/strength.
- New public enums/hashdecl and group/type metadata getters retain native field
  shapes and copy-on-write views. Empty sets differ from absent wildcards;
  non-expressible XSD 1.0 combinations reject. xs:anyType's ur-type processing
  exception is retained. Runtime wildcard value behavior remains P5 work.
- New `wsdl-attribute-wildcards.qtest`: final eight cases / 67 assertions pass.
  Initial baseline failed all six original cases. Coverage includes imported and
  no-target namespaces, nested groups, processing precedence, immutable views,
  reconstruction, failed-addition recovery and native/provider consumers.
- New `test_attribute_wildcards.py` and `attribute-wildcards.qr`: 82 schema graphs
  through 164 actual 1.1/1.2 binding parses and 112 original/emitted documents,
  simple/complex content, qualified/unqualified attributes, both directions,
  providers, generated examples and reconstructed services. Both tests pass.
  Xerces matches all normative verdicts; libxml2's ##other/##local and empty-set
  subset disagreements are explicit assertions against cos-ns-subset.3.2.2.
- All 30 affected Qore suites pass: 405 cases. Full Python: 87 tests with only
  14 tracked P3/P4/P6 subtest failures, no new failure/skip. WSDL docs build without
  warnings/errors. Logs `/tmp/wsdl-p2-18-{affected,independent,python,docs}.log`.
  Both corpus reports are recursively unchanged except module digest: zero strict
  failures, 360 broad failures, no missing/skipped stages. Reports refreshed.
- WSDL SHA-256:
  `bb4758d5edf341accd03814fd4d077c886713f097e5470e96706a8e9ac36d08c`.
  Full 62-item audit: [audits/P2-18.md](audits/P2-18.md).
  Baseline `/tmp/wsdl-p2-17-pre-attribute-wildcards-WSDL.qm`.
  P2-10 native memory decision remains open. No native/astparser edits or commit.

### P2-19 — declaration constraints (implemented, uncommitted)

- Root cause: element constructors selected one of contradictory type declarations
  and did not distinguish local/global/reference properties. ID-derived value
  constraints and merged ID attribute-use limits were not checked after resolution.
- Construction now rejects contradictory declarations, invalid context properties,
  named/duplicate inline types and empty declarations in nested compositors/groups.
  Empty QName attributes report namespace errors. Legal boolean spellings retain
  correct nillability metadata.
- ID-derived attribute/element value constraints are checked after simple/complex
  type resolution. Combined local/group/inherited attributes allow at most one ID
  use. Prohibition removes a use; IDREF remains distinct. A new detached-schema
  regression fixes an expired borrowed namespace reference found in the first full
  Python run; ID checks now use only the resolved type chain.
- Focused test: eight cases / 97 assertions. All 31 affected Qore suites pass:
  413 cases, no warnings. Independent tests: 94 schemas / 188 actual 1.1/1.2 binding
  parses and 24 documents, both directions, reconstructed providers/examples and
  exact typed zero/false. Fourteen libxml2 and two Xerces disagreements are
  explicit assertions against the XSD 1.0 requirements.
- Documentation builds without warnings/errors. Both reports retain identical
  results (zero strict failures, 360 broad failures, no missing/skipped stages),
  differing only by WSDL digest and externally updated Qore revision
  b46682ff4d02341350b02cd55621a0a540c032a4. Local Debug XML is unchanged.
- WSDL SHA-256: `42512cfc525dd1bf506f228a9d3d1b4e3e104cc53065744be9810b11fdea9fba`.
  Baseline `/tmp/wsdl-p2-18-pre-declaration-constraints-WSDL.qm`.
  Logs `/tmp/wsdl-p2-19-{affected,reference-recheck,python-final,docs}.log`.
  Full 62-item audit: [audits/P2-19.md](audits/P2-19.md). Final Python: 89 tests
  in 110.904s with only the 14 tracked P3/P4/P6 subtest failures; no new error/skip.
  P2-10 native memory decision remains open; no new native/astparser edits or commit.

### P2-20 — unwrapped document values (implemented, uncommitted)

- Root cause: unwrapped selection inspected only the flat element map and treated
  wildcard-only/nested-choice-only content as empty. Selection now includes
  explicit element wildcard and choice fields for one selected part, preserving
  other part/header wrappers and WSDL message-name containers.
- Attribute wildcards and absent zero/zero particles do not claim child values.
  Multiple selected document parts require explicit wrappers. This closes the
  direct bare wildcard consumer finding from P2-11; full group/mixed/wildcard
  runtime semantics retain P4/P5 ownership.
- New qtest: six cases / 116 assertions. Independent test and worker validate
  60 emitted payload/header documents across four schemas, eight actual SOAP
  bindings, both directions, reconstructed services and bare/part/message forms.
  Exact names, zero/false/empty values, order and header ownership are asserted.
- All 32 affected Qore suites pass: 419 cases, no warnings. Full Python:
  Ran 90 tests in 118.806s; only the 14 tracked P3/P4/P6 subtest failures, no new error/skip.
  Docs build without warnings/errors. Both reports are recursively unchanged
  except WSDL digest: zero strict failures, 360 broad failures, no missing/skips.
- WSDL SHA-256: `cb7c2e6a3471a6c78f237fa9c8ffca5bb4d5540b9333d2767318674d6d40ba11`.
  Baseline `/tmp/wsdl-p2-19-pre-bare-values-WSDL.qm`. Full 62-item audit:
  [audits/P2-20.md](audits/P2-20.md). Logs:
  `/tmp/wsdl-p2-20-{affected-final,independent,python,docs}.log`.
  P2-10 native memory decision remains open; no new native/astparser edits or commit.

### P2-21 — retained XML consumers (in progress, commit gate not clear)

- Baseline `/tmp/wsdl-p2-20-pre-xml-consumers-WSDL.qm`; reviewed incremental diff
  `/tmp/wsdl-p2-21-WSDL.diff`. WSDL SHA-256:
  `2db90a28aee577555fb7a514d621a34fbe198eef6de3642298b0bff62955e2cb`.
- XsdXmlValue is final, keeping its XML source and cached identities/views
  consistent. New root URI/local getters and getChildValues() retain immediate
  children, namespace declarations (including QName-only bindings), local/default
  rebinding, lexical text, whitespace, CDATA and comments. Source between-child
  nodes stay accessible on the parent. Extraction handles 4,096 siblings and depth
  128, and interrupted extraction permits subsequent use.
- XsdElement.validateXmlValue checks exact root and DTDs and applies both existing
  decode and encode validation. Comments are absent from the validation projection
  because they do not participate in XSD content models; the authoritative XML
  retains them. Namespace allocation uses a private registry copy. Both validation
  wrappers rethrow PROGRAM-INTERRUPTED and THREAD-CANCELLED unchanged; an injected
  copy interruption checks sender/provider and receiver error paths.
- Literal document parts accept carriers keyed by part/element name, or bare when
  one part is selected. Fragment keys contain length-prefixed message identity and
  part name to prevent merged header fragments overwriting each other.
- XsdSchema.getXmlValue/validateXmlValue/getXmlDataProviderType expose explicit XML
  validation and providers. The provider keeps its source-backed schema owner;
  component/type/namespace state is transient. Direct graph serialization failed
  on internal XsdEmptiabilityInfo and was replaced by reconstruction from sources.
  Optional/mandatory copies now honor base type conversion while retaining the XML
  validator. Wrong serialized state, root and native input types reject explicitly.
  Providers remain usable after explicit deletion of the original schema.
- WSMessageHelper.getXmlMessage produces per-part XML examples using the native
  example helper, checks them with existing validators, and preserves namespace
  allocation state. Its inherited required-wildcard example defect is recorded
  below as a failing P5 diagnostic, not an accepted output.
- WSOperation.deserializeXmlRequest/Response return SoapXmlMessageInfo with `body`
  part-name maps, `headers` message/part maps, ordered `unbound_headers`, and SOAP
  1.1 `extensions` after Body. Root/container order, duplicate/missing/unknown body
  parts, duplicate declared headers, and unqualified header blocks reject. Existing
  schema and fault handling runs before results are published.
- SoapClient.callOperation(..., {"xml_values": True}) opts into this return type;
  SoapHandler.addMethod(..., xml_values) has an optional final bool selecting this
  callback argument type. Native defaults stay available. Real HTTP tests cover
  both versions, native/XML callbacks and results, body/header ownership, lexical
  009/007 and boolean 0/1, invalid option types and one-way operations.
- One-way coverage exposed a native decoder requirement for an absent output
  BindingMessageDescription. Making that reference optional and guarding header
  access fixes native and XML-mode one-way calls. Explicit XML response decoding
  for an operation without output rejects SOAP-DESERIALIZATION-ERROR.
- SOAP positive fixtures now use comments/CDATA, not processing instructions.
  SOAP 1.1 section 3 and SOAP 1.2 section 5 prohibit initial senders from emitting
  PIs. Retained SOAP sends and receives reject them and DTDs; pure XML carriers
  still retain PIs. This is required integration validation, not a full P7 claim.
- Focused consumer suite: 13 cases / 319 assertions pass. Carrier suite: 14 cases,
  13 pass / 211 assertions reached, with the namespace dependency error below.
  Initial checkpoints and current logs are `/tmp/wsdl-p2-21-{before,receive-before,
  http-before,optional-before,one-way-before,cancel-before,focused-final,children-final}.log`.
- `test_xml_consumers.py` and `xml-consumers.qr` check 192 documents across two
  schemas, actual 1.1/1.2 bindings, both directions, body/header part placement,
  source-backed service/provider reconstruction and generated examples. Exact
  expanded names, QName scope, lexical text, mixed text/tails, comments, CDATA and
  child order are checked independently of prefix choice.
- **Open dependency decision (P2):** libxml2 2.12.10 returns namespace URI
  `urn:quoted&#38;more` for source `xmlns:p="urn:quoted&amp;more"`, so namespace
  reconstruction escapes it again. The carrier regression remains failing.
  A standalone C reproducer `/tmp/wsdl-p2-21-libxml-namespace.c` confirms the root
  independently of Qore; its diagnostic comparison with XML_PARSE_NOENT returns
  the correct URI. Production parsing flags are unchanged. The C reproduction's
  valgrind log has zero errors/leaks (`/tmp/wsdl-p2-21-libxml-namespace.log`).
  Upstream parser.c adds namespace-specific entity expansion between v2.12.10
  and v2.13.9. An async question requests approval for a compatibility adaptation
  on older libxml2, or a required fixed dependency version. No answer or workaround
  has been applied; the user instruction forbids unapproved workarounds.
- **Additional native helper finding (P5):** WSMessageHelper.getTypeInfo(XsdComplexType)
  exposes a record only when elementmap is nonempty, and getMessage has no wildcard
  example generation. A required `xs:any` therefore gets an empty example. Both
  libxml2 and pinned Xerces reject 16 of the 192 documents (required-wildcard
  example payloads only); all retained values, emitted original payloads/headers,
  record examples and header examples validate. The Python test completes both
  validator passes and then fails with both exact rejection lists. Fix alongside
  complete wildcard content/example generation, not by making the fixture optional
  or calling empty invalid examples passing.
- Inherited xml:lang/xml:space/xml:base semantics still need consumer integration;
  child extraction currently copies namespace declarations only. The distinction
  is explicit in the design. The probe `/tmp/wsdl-p2-21-context-probe.qr` shows
  inherited language and effective relative/absolute base URIs available from the
  native reader. Preserve this context without injecting new schema-invalid
  attributes into payload roots. This criterion remains open under P2/P5.
- Final verification: 33 affected Qore suites / 436 cases, 435 pass with only the
  namespace dependency error; no warnings. Full Python: 91 tests in 119.848s,
  15 failures (14 existing P3/P4/P6 subtests plus the P5 wildcard example test),
  no error/skip. All three module docs targets build without warnings/errors.
  Both-version survey and strict coverage are recursively unchanged except the
  final WSDL digest: zero strict failures, 360 broad failures, no missing/skips.
  Current reports are refreshed from that digest. Final logs use the `-final`
  suffix in `/tmp/wsdl-p2-21-{affected,python,docs,survey,coverage}-final.log`.
  Full 62-item audit has explicit error-handling/correctness failures and does not
  clear the commit gate; no passing conformance claim is made.
- Release notes/design now describe the implemented APIs. SoapClient is 1.0.4 and
  its Version/User-Agent are synchronized; SoapHandler's Version now matches 0.3.4.
  Its new docs build exposed and fixed duplicate SoapClient release anchors,
  incorrect Xml namespace/constructor references and an obsolete method reference.
  The existing ConnectionProvider tag file is now supplied in the local docs cache.
- No new C++/astparser/JNI edit, build, installation, commit or push. Docs use the
  existing astparser artifact. Debug XML SHA remains
  `dc1fadc47062c8d809cd8e04ffb8611edd2ffe03baf08b26f284b5cedbd98372`.
  P2-10's earlier PCRE2 JIT/valgrind decision still blocks the native commit gate.
  Full audit status is recorded in [audits/P2-21.md](audits/P2-21.md).

### P2-22 — inherited XML context (implemented, uncommitted; gates open)

- WSDL baseline `/tmp/wsdl-p2-21-pre-xml-context-WSDL.qm`; final SHA
  `8a929d64f4e58443e0164e944a3f568d4ddc75a360c9d4c0629d7a13caae657e`. Full 62-item audit: [audits/P2-22.md](audits/P2-22.md), with explicit
  memory/error-handling/correctness failures; no commit or phase-boundary pass.
- Carriers serialize parent xml:lang/xml:space/xml:base separately from authored
  root attributes. getInheritedXmlAttributes()/getXmlContext(), child extraction,
  old/new Serializable state, direct generation and SOAP consumers preserve it.
  Body/Header contexts are independent; incompatible retained siblings and
  compatibility-header overrides reject without mutating caller values.
- XML Base resolves LEIRIs by component merging and linear dot-segment removal.
  The initial native reader choice lost Unicode bases (`rosé`); final code
  preserves Unicode, spaces, percent escapes and unresolved relative parents.
  Native XmlReader.baseUri() still has the dependency limitation; the carrier's
  explicit context API does not depend on it.
- A native generator root cause was fixed: literal attribute whitespace was
  normalized to spaces on parsing. concat_attribute_value emits character
  references, handles source/output encodings, checks cancellation every 100
  bytes and propagates conversion/interruption errors. Debug XML only rebuilt
  with verified prefix `/usr`; artifact SHA
  `bcf5425bd6b86cdb3b678fbde39687e2ca3968079c723c204b91b4dba1a1441d`. No core/JNI/astparser edit or build,
  installation, commit or push.
- Focused tests: context **9/167**, consumers **15/479**, native **10/122** pass.
  All **36 Qore suites / 482 cases: 481 pass**, only namespace dependency error,
  no warnings. New independent **80 documents / two schemas** pass both validators
  with exact authored attributes/whitespace/context across both bindings/directions,
  reconstructed schemas/providers and direct XML generation. RFC resolution cases
  and Unicode bases have separate normative/independent assertions.
- Full Python **92 tests, 15 failures, no errors/skips** (135.165s), same explicitly
  tracked P3/P4/P6 failures and P5 required-wildcard example failure. Final focused
  URI boundary checks also pass. Survey/coverage unchanged except WSDL digest:
  zero strict failures, 360 broad failures, no missing/skipped stages. Reports
  refreshed. Logs `/tmp/wsdl-p2-22-{affected,python,docs,survey,coverage}-final.log`.
- Affected native/WSDL/client/handler docs build without warnings. Broader docs
  exposed 38 independent P9 packaging/reference warnings; installed QoreMacros
  mistakenly includes SVG `.dox.h` inputs, and other modules have missing tags,
  obsolete/private-class refs and a missing WebDAV parameter description.
  Exact list: `/tmp/wsdl-p2-22-broad-doc-warnings.log`.
- Valgrind does **not** pass: conditional reads remain (context 175 contexts;
  consumer 7766 errors/7736 contexts), and the HTTP consumer run reports 384 bytes
  possibly lost in glibc TLS from core AsyncIoController's thread pool. Definite/
  indirect loss is zero; non-HTTP context/native runs also have zero possible loss.
  A bounded 30-second test I/O deadline fixes instrumentation-only timeout; all
  consumer functional cases now finish under valgrind. Final logs retain all
  reports with --error-limit=no. Minimal async-task and async-XML runs are clean.
  A plain-HTTP reproduction without XML/WSDL also reports 352 bytes possibly lost
  from the same core pool TLS allocation, with zero valgrind errors; see
  `/tmp/wsdl-p2-22-http-pool-repro.{qr,log}`. The pool's stopped notification precedes
  final native-thread cleanup; completion versus glibc TLS-cache classification
  still needs adjudication. This is isolated to the core HTTP/runtime lifecycle,
  not proven to be leaked XML storage. Final literal valgrind: 10 cases/122
  assertions pass, one conditional-read context, no lost memory.
- Prior namespace-URI compatibility/fixed-version decision and PCRE2 JIT test
  configuration decision are still pending; no workaround is authorized/applied.
  Remaining P3–P9 functionality and P2 boundary gates are not declared complete.

### Remaining P2 acceptance work

- Namespace/part identity and lossless carrier consumers are implemented through
  P2-22, including source context and actual HTTP. Clear the namespace-URI
  dependency regression and required native memory gate, then complete P2's
  acceptance review against the declaration and consumer tests.
  The remaining broad P2 decode
  failures are GlobalElementComplexTypeSequenceExtension and MixedComplexContent
  (four directions each); mixed runtime behavior is coordinated with P5.
- Keep the public representation's lexical/QName/ordered/mixed/context guarantees
  distinct from later scalar, particle and dynamic validation. Implicit substitution
  declarations, complete runtime wildcard enforcement/preservation and required
  wildcard examples remain P5 work; encoded/type/attachment consumers remain P6/P8.
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
- `4879ed6` — P2-09 — array item identity and reserved schema output prefixes;
  339 Qore cases pass, with six routed P4/P6 subtest failures. Full audit
  [audits/P2-09.md](audits/P2-09.md). No push.


## P2-23: behavioral libxml2 selection and PCRE2 test switch (2026-09-08)

The user selected a programmatic PCRE2 JIT test control and CMake behavioral
libxml2 detection with FetchContent fallback. The earlier dependency approval
questions are superseded. Qore now supports `QORE_PCRE2_NO_JIT=1` using the
installed PCRE2 library; XML CMake probes the installed dependency and falls back
to pinned private static libxml2 2.15.4. Details and the full 62-item audit are in
[audits/P2-23.md](audits/P2-23.md).

All 482 affected XML/SOAP cases pass, including namespace ampersands. The 10
CMake integration tests and 137 regex cases pass; production JIT remains the
default. Final survey and strict coverage reports are exactly unchanged. The
full Python suite retains its same 15 later-phase failures. Final valgrind
runs for the switch, literal XML, retained values and XML context have zero
errors/lost allocations. HTTP passes all 15 cases/479 assertions with no regex
conditional-read reports, but retains one 384-byte possibly-lost glibc TLS
allocation from core AsyncIoController/ThreadPool (exit 99; no definite/indirect
loss). A valgrind Debug-info warning is also recorded. Qore switch/tests/docs
and its independent full audit are committed as `6efa18fc5` on develop at the
user's explicit request; no push. XML changes remain uncommitted; astparser
sources/tests remain untouched. P2 acceptance and P3-P9 remain open.

The minimal plain-HTTP reproduction still reports possible TLS loss with glibc
stack caching disabled (diagnostic only), so cache tuning is not a solution.
Core thread cleanup detaches threads and decrements tp_thread_counter before
pthread's final TLS destruction; actual native termination must be distinguished
from the counter notification. No thread-lifetime code change was made after
Qore commit `6efa18fc5`. The valgrind Debug-info warning also occurs for
`qore --version`, independently of XML/regex test execution.

## P2-24: native HTTP thread termination prerequisite (in progress)

The remaining HTTP TLS finding is now root-caused. A Valgrind/vgdb breakpoint
at the actual libc `exit` function shows the main thread exiting while a Qore
pool worker is still in `start_thread -> madvise`, after returning from
`q_run_thread`. The same run reports one 352-byte possibly-lost TLS allocation.
Logs: `/tmp/wsdl-p2-24-http-{gdb,vg-debug}.log`; reproducible debugger driver:
`/tmp/wsdl-p2-24-http-exit-debug.py`. The first diagnostic breakpoint matched a
C++ `exit` method and timed out; the corrected run uses `break *exit`.

A deterministic native regression in the core repository holds a pthread TLS
destructor at a condition-variable barrier. The existing runtime fails its
assertion that `tp_thread_counter` must remain nonzero while that destructor is
running. Core changes under review add one lazy native cleanup worker, an
allocation-free intrusive completion queue, and native joins before releasing
the external counter; runtime shutdown joins the cleanup worker before unloading
native modules. ThreadPool public stop/cancellation behavior is unchanged.
Tests cover concurrent creation, default/custom stack overloads, repeated native
TLS destructor passes, failed creation/recovery and empty shutdown. Build and
validation are in progress; no new commit or push yet.

P2-24 verification update: the native TLS barrier regression passes with the
join implementation, including simultaneous first creation, repeated destructor
passes, invalid stacks, and real pthread_create failures/retry. The ordinary
native test, ThreadPool qtest, plain HTTP reproduction, and XML SOAP consumer
suite all have **zero Valgrind errors and zero definite/indirect/possible loss**.
The SOAP consumer suite is **15 cases / 479 assertions**. All **482 XML/SOAP
functional cases** pass with the new Debug runtime. Core regressions total
**78 cases / 555 assertions** after correcting a pre-existing HTTP test fixture
that greedily included a MIME boundary parameter's closing quote. That isolated
fixture correction and its full audit are committed to core develop as
`4f43e60f7`; it passes all 63 HTTP cases on both installed and Debug Qore.

The P2-24 survey and strict coverage differ from the prior reports only in build
version metadata: all counts, per-case results, failure owners and strict gates
are unchanged. Full Python: **92 tests / the same 15 later-phase failures**,
150.477 seconds. Final native audit found helper symbols accidentally exported;
they are now marked DLLLOCAL and the affected final binary is being rebuilt.
Core source/flags/test/docs remain uncommitted pending that validation. Other
active core AOT namespace work is excluded from our changes and commits.

### P9 independent environment findings from P2-24

- Fedora glibc **2.43-8.fc44** leaks TLS storage on actual kernel pthread_create
  failure. Qore's explicit resource-failure test passes all behavior/counter
  checks but Valgrind reports **704 bytes / two possible-loss records** inside
  libc. A standalone C program with no Qore/XML/OpenSSL reproduces two losses
  (**544 bytes**), with every successful thread joined. A native, non-Valgrind
  allocator measurement over 1,000 failed creations retains **287,712 extra
  bytes**, both with the default stack cache and with caching disabled. This is
  independent of the fixed Qore termination race. Reproduction is preserved at
  `qore/examples/test/qore/classes/ThreadPool/pthread_creation_failure.c` and
  in its README. Logs `/tmp/wsdl-p2-24-pthread-failure*-vg.log`; Qore fault log
  `/tmp/wsdl-p2-24-native-vg.log`. P9 must verify/fix the supported libc failure
  path; no suppressions, cache workaround, host library replacement or external
  bug-report submission has been applied.
- Valgrind **3.27.1-1.fc44** still reports the independently reproduced Qore
  DWARF reader warning; HTTP runs also print `invalid file descriptor -1 in
  syscall fstat()` as a tool warning. Their memory-error summary is zero.
  Keep these diagnostics visible for P9 environment/tool adjudication. Do not
  describe the instrumented runs as warning-free.

An isolated libxml2-provider checkout under `/tmp/wsdl-libxml-provider-review`
is being built against the committed XML parent plus only the build-provider
change. This verifies that its FetchContent/probe commit can stand independently
of the remaining XML value implementation and documentation changes.


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

## P2-26 committed identity increment (2026-09-08)

The P2-11/P2-12/P2-13 namespace work is now isolated on parent 049cf0d and
ready as one complete identity increment. Element namespaces are resolved before
matching, colliding fields retain expanded keys, WSDL message/part scopes select
the correct declarations, and HTTP routing preserves the original parsed input.
Ordinary unambiguous native fields and single-part examples retain their shape.
The incomplete historical XML carrier is excluded; its complete implementation
and consumers remain a following P2 increment.

Validation: 24 affected Qore suites pass 362 cases with debugging enabled against
isolated candidate qlib and the committed native Debug XML module. Namespace
restoration tests use XmlReader directly, independently of the forthcoming carrier.
The three independent Python suites finish all 56 namespace, 136 collision and
160 message element documents with lxml and pinned Xerces. Eight invalid integer
subtests remain explicit P3 failures; all P2 identity assertions pass. Candidate
WSDL and SoapHandler docs generate without warnings/errors after correcting two
existing parameter comment tags included in this change. No C++ changes.

The both-version request survey and full strict coverage are recursively identical
to the P2-13 reports except version metadata. The request survey covers 293 WSDLs
and 1136 messages: 279 parse successes, 1006 decodes, 1004 serializations, 972 valid
outputs and 32 rejected outputs. Fourteen invalid source descriptions still fail.
Strict selected failures are zero. All 360 broad failures remain visible with
zero missing/skipped stages; P3/P4/P5 and the previously identified P2-to-P5 runtime
cases retain their ownership. No conformance completion is claimed.

Logs: /tmp/wsdl-p2-26-schema-tests.log, /tmp/wsdl-p2-26-independent.log,
/tmp/wsdl-p2-26-docs.log (WSDL succeeds; historical handler warning corrected),
/tmp/wsdl-p2-26-handler-docs.log, /tmp/wsdl-p2-26-{survey,coverage}.log.
Reports: /tmp/wsdl-survey-p2-26.json and /tmp/wsdl-coverage-p2-26.json.
The final full 62-item audit is [P2-26-identity](audits/P2-26-identity.md).
No installation, push or astparser changes.

## P2-27 inherited attribute and mixed base acceptance (2026-09-08)

The identity increment was committed as 9ae595e. Its subsequent full Python
run completed 77 tests with exactly 14 tracked subtest failures (eight P3 integer,
four P4 nested-choice, two P6 binding selection), no new failure or skip.

The P2-14/P2-15 construction increments are isolated together on that parent.
Inherited required/fixed/type constraints, duplicate extension uses and inline
simple-content ancestry now validate before attribute replacement. Mixed flags
and nested particle emptiability resolve legal named mixed bases, with complete
nested group graph validation and bounded shared-reference evaluation.

All 26 affected Qore suites pass 375 cases, including 13 new cases / 130 assertions.
Four independent Python tests pass 79 schemas and 68 request/response documents
across both actual SOAP bindings, exact values, reconstructed schemas, providers
and examples. Oracle disagreements remain explicit. Candidate WSDL documentation
passes without warnings/errors. The full both-version request survey is recursively
identical to 9ae595e except versions, with no missing case or regression.

Logs: /tmp/wsdl-p2-27-{affected,attributes,mixed,survey,docs}.log and
/tmp/wsdl-survey-p2-27.json. Full 62-item audit:
[audits/P2-27-constraints.md](audits/P2-27-constraints.md).
No native code, astparser change, installation or push.

## P2-28 schema validation acceptance (2026-09-08)

Inherited attribute and mixed-base construction was committed as 8b8c3d1.
The next isolated candidate combines P2-16 through P2-19: source-local import
permissions, expanded-name element declaration consistency, attribute wildcard
construction algebra, declaration exclusivity/context and resolved ID constraints.
Three Qore-authored SOAP fixtures now declare their encoding imports. Pinned
upstream fixtures and historical findings remain byte-identical.

30 affected Qore suites pass 403 cases, including 28 new cases / 266 assertions.
Eight independent tests pass 235 schema graphs through 470 actual SOAP 1.1/1.2
binding parses and 180 request/response documents with exact name/type/value,
provider/example/reconstruction checks. Oracle disagreements are explicit assertions
against the cited XSD requirements. WSDL documentation has no warnings/errors.

The both-version survey retains all counts and classifications. The already-invalid
SOAPEncodedArray fails earlier on an unimported WSDL-namespace QName, with the same
WSDL-ERROR category. Other rows are unchanged apart from versions; the full report
is recursively equal to historical P2-19 excluding versions. No missing cases,
regression skips or new passing claims for P3/P4/P5/P6 failures.

Logs: /tmp/wsdl-p2-28-{affected,references,elements,wildcards,declarations,survey,docs}.log.
Report: /tmp/wsdl-survey-p2-28.json. Full 62-item audit:
[audits/P2-28-validation.md](audits/P2-28-validation.md).
No native or astparser changes, installation or push.

## P2-29 bare document argument acceptance (2026-09-08)

Schema validation was committed as 7771dde. The isolated P2-20 increment
recognizes bare nested-choice and explicit element-wildcard records while keeping
other part/header wrappers intact. Multipart values require unambiguous wrappers;
attribute wildcards and absent particles do not claim child fields.

31 affected Qore suites pass 409 cases, including six new cases / 116 assertions.
The independent test validates 60 payload/header documents across actual SOAP
1.1/1.2 bindings and both directions, with reconstructed services and exact names,
order, false/zero/empty values and header ownership. Candidate docs are warning-free.
The both-version survey is recursively identical to 7771dde excluding versions;
no missing cases, regressions or concealed later-phase failures.

Logs: /tmp/wsdl-p2-29-{affected,independent,survey,docs}.log.
Report: /tmp/wsdl-survey-p2-29.json. Full 62-item audit:
[audits/P2-29-unwrapped.md](audits/P2-29-unwrapped.md).
No native or astparser changes, installation or push.

## P2-30 retained XML consumer acceptance (2026-09-08)

Bare argument ownership was committed as 9fb341c. The complete P2-10/P2-21/P2-22
XML carrier and consumer changes are now isolated on that parent. Native prerequisites
were committed separately: verified libxml2 and catalog ownership (5477680), XML
fragments/encoding (049cf0d), core PCRE2 test control (6efa18fc5) and native-thread
cleanup (1e52a0a44). Their recorded tests and memory gates clear the old dependency
and lifecycle findings; historical open-gate entries above describe earlier states.

The final immutable XsdXmlValue retains authoritative XML and inherited XML
language/space/base context. Serializable and XML providers reconstruct from sources;
SOAP parts/headers, examples, client and handler consume the explicit representation.
Native return types remain the default, and all validation paths retain cancellation.
The separate XML Base resolver preserves LEIRIs and unknown relative parent segments.

34 affected Qore suites pass 447 cases, including 38 carrier/context/consumer cases
with 862 assertions. Actual local HTTP tests exercise native/XML client and handler
options, both SOAP bindings/directions, one-way behavior and body/header contexts.
All three user-module docs generate without warnings/errors. The independent value
and context checks validate six and 80 documents; the existing encoding regression
checks another 40 raw outputs. The consumer oracle completes 192 documents and
retains the known P5 failure for 16 empty required-wildcard examples; all retained
payload/header infoset and value assertions complete successfully.

Full Python discovery: 93 tests in 133.537 seconds, 15 failures, no errors/skips.
These are exactly eight P3 integer lexical subtests, four P4 nested-choice subtests,
two P6 binding-version subtests and the P5 required-wildcard example test. The
execution prompt permits these explicitly routed independent findings to remain
failing; no passing conformance claim or reduced phase scope is introduced.

The both-version request survey is recursively identical to 9fb341c except
versions. Full strict coverage matches the earlier fully tested P2 working tree:
zero selected failures, 360 broad failures, zero missing/skipped stages. The P2
schema-construction acceptance review distinguishes adjudicated invalid source
ImportSchema (its pinned Imported.xsd dependency is empty) from valid schema graphs. Remaining original
P2-family runtime anyType/mixed-content failures retain their explicit P5 assignment.

Logs: /tmp/wsdl-p2-30-{affected,independent,python,survey,coverage,docs}.log.
Reports: /tmp/wsdl-survey-p2-30.json and /tmp/wsdl-coverage-p2-30.json.
Full 62-item audit: [audits/P2-30-xml-values.md](audits/P2-30-xml-values.md).
No native or astparser changes, installation or push in this increment.

## P2-31 documentation/build and phase acceptance (2026-09-08)

Retained XML consumers were committed as d5cfc96. This increment completes public
QPP documentation inputs, native/user tag dependencies, option documentation,
qualified references and literal WebContentUtil markup. The six WebContentUtil
comment fixes were originally recorded under P2-10 and contain no runtime edits.
P2-10 through P2-23 audits are preserved as explicitly historical evidence.

The final local core package exposed two build requirements:

- Core's two-pass docs helper used file(COPY_FILE), unavailable before CMake 3.21.
  The parent fails with that diagnostic on actual CMake 3.18.4; core f23e5307a
  uses configure_file(COPYONLY). Three tests pass on 3.18.4 and 4.3.0, covering
  literal bytes, reconfiguration, target dependencies, disabled docs and errors.
- Qore 3.0 public headers require C++17; XML's forced C++11 flag generated
  extension warnings. CMake now selects the required standard by Qore version,
  preserves higher caller-selected standards and keeps C++11 for older Qore.
  Final compilation uses -std=c++17 without warnings. The independent legacy
  Autotools path still forces C++11 and its old AX macro cannot select C++17;
  this build-environment finding is explicitly assigned to P9, before acceptance
  of supported build configurations. No runtime parsing behavior is relaxed.

All native/user documentation builds with final warnings enabled and no warnings
or errors, using Debug /usr, local Qore package, fixed JNI and existing astparser
artifacts. The installed JNI assertion is resolved by the previously tested local
source fix described under P2-10; committing that prerequisite and adjudicating
standalone JVM diagnostics remain part of P9. Nothing was installed or pushed.

Final checks: 34 affected SOAP/WSDL suites pass 447 cases; xml, xml-literal,
xml-schema-callbacks and WebContentUtil add 125 cases, for 572 cases total.
The focused five-suite run includes 135 cases / 1,031 assertions (its ten
wsdl-interop cases are also in the 447). Boundary test_survey.py passes 14 tests.
The required full Python discovery from P2-30 retains exactly 15 known failures
among 93 tests, no errors/skips: eight P3 integer lexical subtests, four P4 nested
choice subtests, two P6 binding-version subtests and one P5 wildcard-example test.
No runtime Python/Qore implementation changed in this increment.

The final C++17 request survey equals P2-30 recursively except versions:
293 descriptions / 1,136 messages; 279 parse / 14 invalid-source rejections,
1,006 decode / 110 failures, 1,004 serialize / two failures, 972 valid / 32 invalid
outputs, eight valid-input-invalid-output rows. Nothing is unassessed by the input
oracle. Full both-direction coverage retains 360 broad failures, zero selected
failures, no missing/skipped stages; strict selection covers 38 descriptions and
140 message/direction combinations. Diagnostic completion is not conformance.

The C++17 native literal memory check passes 11 cases / 256 assertions with zero
invalid accesses and no definitely, indirectly or possibly lost allocations.
The checked run uses errors-for-leak-kinds=definite,indirect,possible. An initial
run used all, which also counts 826 still-reachable records as errors; all its
records were reachable (mostly retained process/library caches), with zero lost
memory and no invalid accesses. That invocation and its log are retained. The
previously reproduced Valgrind DW_AT_abstract_origin warning remains assigned to
P9's tool/environment checks and is not suppressed.

### P2 acceptance matrix

| Criterion | Result and executable evidence |
| --- | --- |
| Declaration-local QName/type identity | Pass: namespace-context, compositor-context, array-context and message-identity suites cover rebinding/default/no namespace, actual SOAP bindings, reconstruction and recovery. |
| Imports/includes/chameleons/cycles | Pass: schema-composition, reference-permissions and independent composition/reference tests cover real WSDL imports, source-local permission and namespace-specific caches. The empty pinned Imported.xsd is an adjudicated invalid source. |
| Attributes, simple content and inheritance | Pass: attribute, attribute-derivation, attribute-wildcards and declaration-constraints suites cover refs, anonymous/default types, use/default/fixed, builtin/complex bases and contradictory declarations. |
| Element/attribute qualification and collisions | Pass: element-namespaces, element-collisions, element-consistency and local-form tests validate expanded output names, provider metadata, inherited declarations and precise errors. |
| Additive lossless public representation | Pass: xml-value, xml-context, xml-consumers and native xml-literal suites plus independent XML/encoding checks cover lexical/context/order retention, Serializable, providers, examples, client/handler and actual HTTP in both directions. |
| Failure isolation and cancellation | Pass: namespace rollback, malformed reconstruction, detached provider ownership, injected cancellation and native callback/literal cleanup tests; committed native/core fixes clear the earlier ownership gates. |

All P2 schema-construction and representation criteria are complete. The original
primary P2 family labels for GlobalElementComplexTypeSequenceExtension and
MixedComplexContent retain eight runtime anyType/mixed-content failures; those
were explicitly routed to P5 earlier and remain failures. This acceptance does
not claim P3 scalar, P4 particle, P5 content or P6-P8 binding/protocol behavior.
The next implementation phase is P3, with its full original scope unchanged.

Core prerequisite IDs after the parallel developer's history rewrite are
b75db5d82 (PCRE2 control; formerly 6efa18fc5), 4060414dc (quoted MIME test;
formerly 4f43e60f7), and 06eb33d38 (native joins; formerly 1e52a0a44).
Their scoped blobs match the tested originals. Core f23e5307a is the additional
CMake helper fix committed here. Core is clean; astparser is untouched.

Final logs: /tmp/wsdl-p2-31-{docs-final,affected,test-survey,final-survey}.log,
/tmp/wsdl-p2-31-final-{xml,xml-literal,xml-schema-callbacks,wsdl-interop,WebContentUtil}.log,
/tmp/wsdl-p2-31-final-literal-vg-checked.log. Reports:
/tmp/wsdl-survey-p2-31-final.json and /tmp/wsdl-coverage-p2-31.json.
Full 62-item audit: [audits/P2-31-docs.md](audits/P2-31-docs.md).

## P3-01: integer lexical validation (2026-09-08)

P2 was committed as 1fedcf5. This increment validates all thirteen integer XML
lexical spaces before the existing native numeric conversions. Empty text,
malformed signs, fractional/exponent/hex spellings, trailing text and non-ASCII
digits fail with the corresponding SOAP serialization/deserialization error.
XSD 1.0 unsigned builtins require digit strings without a sign. XML whitespace
normalization replaces/collapses only TAB, LF, CR and SPACE; Qore trim() also
removed vertical tabs, incorrectly turning malformed input into valid integers.
Normalized-string and token output now use the same XML whitespace rules.

The root cause of embedded-NUL acceptance was QoreRegexSubst's zero-terminated
unmatched-tail append: even a no-match substitution changed "1\x00trailing" to
"1". Core ea9ddfc51 fixes full-length pattern compilation, replacement-template
scanning, case-converted captures, callback copies and unmatched tails. It is
committed on core develop, without push or astparser changes. Its six new cases
fail on the parent and pass 89 assertions after the fix; 143 affected cases pass
across applicable PCRE2 JIT/interpreter runs. Native Valgrind reports zero errors
and zero definite/indirect/possible loss. The full 62-row core audit is committed
at examples/test/qore/classes/RegexSubst/audits/embedded-nul.md.

Final XML validation:

- test/wsdl-integer-lexical.qtest: 16 cases / 983 assertions, including every
  integer builtin, both conversion directions, invalid types, whitespace,
  attributes/simple content, reconstruction and list/union alternatives.
- test_integer_lexical.py: 26 actual SOAP 1.1/1.2 bindings, 728 request/response
  inputs and 208 outputs; all 936 documents independently validated by libxml2
  and Xerces, with exact integer values and expanded-name assertions.
- All 35 affected SOAP/WSDL Qore suites pass 463 cases, including actual HTTP
  client/server consumers. WSDL Qdx/Doxygen completes without warnings/errors.
- Full Python discovery: 94 tests, seven known later-phase failures, zero
  errors/skips. Four P4 nested-choice and two P6 binding-version subtests plus
  one P5 wildcard-example test remain failures. All eight integer lexical
  subtests that previously failed now pass. test_survey's fourteen tests pass;
  its small corpus now requires rejection of the exact sixteen signed unsigned
  inputs instead of expecting their successful conversion. An initial update
  listed the wrong fixture families; the final expected set matches the pinned
  Short/Int element/attribute subset and checks error and oracle categories.

Both-version survey: 293 descriptions / 1,136 messages, 279 parsed / 14 invalid
sources, 974 decoded / 142 failures, 972 serialized / two failures, 940 valid /
32 invalid outputs, eight valid-input-invalid-output rows. Input oracle counts
remain 1,028 valid / 108 invalid / zero unassessed. Compared row by row with P2,
only 32 already-adjudicated invalid signed unsigned inputs change: decoding now
rejects them and the corresponding serialization rows disappear. Every other
row is identical, including every valid-input result. Source and catalog hashes
and original findings are unchanged. Full both-direction coverage removes
exactly 64 invalid-input-accepted failures: 296 broad failures remain, selected
failures are empty, and no stage is missing/skipped. Strict coverage remains
38 descriptions and 140 message/direction combinations. Current reports retain
all remaining failures; diagnostic completion is not phase acceptance.

Additional P9 environment evidence: a full PCRE2-interpreter operator run timed
out at 240 seconds. A verbose reproduction locates the first 5.5 MB no-match
scan, after the 4.9 MB checks passed, before substitution is called. The existing
operator test and upstream pcre2_match.c document the REQ_CU_MAX * 1000 required-
code-unit optimization cutoff in the interpreter. Production JIT passes the
full suite. This forced-interpreter performance failure and the previously
reproduced Valgrind DW_AT_abstract_origin warning remain explicit P9 findings;
neither is suppressed or counted as passing. No scope change is implied.

Logs: /tmp/wsdl-p3-01-{affected,independent,python-final,docs,survey,coverage}.log,
/tmp/wsdl-p3-01-affected-wsdl-integer-lexical.log, and the core audit's native logs.
The two current reports carry the final WSDL source hash after its comment-only
release-note addition. Audit: [audits/P3-01-integer-lexical.md](audits/P3-01-integer-lexical.md).

Remaining P3 work includes exact integer bounds/large-value provider conversion,
decimal precision, lexical versus value facets/enumerations, binary/list/union
validation, IEEE semantics, dates/durations/partial dates and XSD regex semantics.
Existing native return types are preserved by this first lexical gate; it does
not claim that those remaining conversions, providers or generated examples are
correct. P3 remains active with its original scope unchanged.

## P3-02: exact integer ranges and provider values (2026-09-08)

P3-01 was committed as 16b3fe3. Native prerequisites are committed in Qore as
860603291 (develop, not pushed); its full audit is
examples/test/qore/vars/audits/exact-numeric-conversion.md. The regex NUL
prerequisite is ea9ddfc51. No astparser edits or installation were made.
Concurrent core CMake/Mistral/OpenApi3/RestSchema edits and the unrelated
release-note hunk were preserved outside our commit.

All thirteen integer builtins now compare canonical decimal strings by sign,
length and lexical order before bounded conversion. Values beyond signed 64-bit
range remain strings; xs:integer retains its existing noncanonical-string
behavior. Native finite integral float/number values produce exact integer text;
fractional/nonfinite values fail. XsdIntegerDataType validates before provider
conversion, including lists, optional/mandatory and Serializable copies. Its
absent native input type prevents ListDataType from coercing lexical strings
first. Bounded output retains NT_INT metadata; int/string output reports NT_ALL.
Negative/nonpositive generated examples now satisfy their builtin bounds.

The core fixes address three root causes. MPFR's automatic significant-digit
count only preserves source precision; raw integral output now requests enough
digits for the complete integer. Default/scientific/fractional formatting and
float-to-number precision policy are unchanged. The SOAP matrix then exposed
LValueRemoveHelper's incorrect assumption that generic assignInitial() cannot
return a redundant numeric box. Twelve paths now release that storage; the
parent explicit AST regression aborts. Valgrind subsequently found typed foreach
creating unowned integer/float boxes. Those instructions now use the existing
owned-slot setter and cleanup ledger; the parent leaks 264 bytes in 11 blocks.
Return/break/continue, exceptions, deterministic queue-event cancellation, empty
lists, 48/64-bit transitions and negative NaNs are tested.

The final Debug /usr native build passes 116 IR/AST cases / 1664 assertions.
All three new suites pass Valgrind (13 cases / 153 assertions): zero errors and
zero definite/indirect/possible loss, no suppressions. The independently
reproduced DW_AT_abstract_origin tool warning remains an explicit P9 finding.
An AOT constant retains exact raw digits; documentation templates regenerate.

XML verification against the final implementation:

- wsdl-integer-range.qtest passes 16 cases / 980 assertions. The initial parent
  failed seven of fourteen cases: long overflow, unsignedLong/unbounded clamping
  and invalid output for native integral floats. All 36 affected Qore suites
  pass 479 cases, with --enable-debug and explicit local module paths.
- Invalid serialized datatype/requiredness fields are rejected; a valid original
  reconstructs after those failures. The first test draft used binary serialize()
  where a SerializationInfo hash was required; serializeToData() fixes the test.
  Its final targeted rerun passes after the other 35 affected suites passed.
- Existing array/soap metadata keeps NT_INT for bounded output. Attribute list
  metadata becomes xsd:int and adds malformed item rejection; original strings
  reach validation before conversion. Optional/provider reconstruction is tested.
- test_integer_range.py passes two tests with 1200 documents: 576 inputs and
  416 outputs in 26 actual SOAP bindings, plus 208 provider/generated-example
  documents in both directions through original/reconstructed services. Exact
  Python integers and mandatory Xerces validation check every value. Ninety-six
  libxml2 rejections of valid large input integers are explicitly asserted as
  the retained P1 precision disagreement.
- Final Python discovery runs 96 tests with exactly seven existing later-phase
  failures (four P4 nested choices, two P6 binding selections, one P5 wildcard
  example matrix), zero errors and no skips. The initial run also used the old
  harness expectation that large integers lose values; test_coverage now
  requires preservation and records all 64 adjudicated output disagreements.
- WSDL Qdx/Doxygen and the documented provider .qr example pass without warnings
  or errors. The first inline example invocation used literal newline escapes;
  extracting and executing the actual documented script passes.

The both-version survey has 293 descriptions / 1136 messages, 279 parsed /
14 invalid sources, 974 decoded / 142 failures, 972 serialized / two failures,
and eight valid-input-invalid-output rows. Its libxml2-only output counts are
924 valid / 48 rejected. Exactly sixteen output verdicts change to the same
known precision rejection as the original input: the formerly clamped values
are now exact. Every other survey row is identical. Input counts remain
1028 valid / 108 rejected / zero unassessed. The adjudicated both-direction
report uses Xerces and exact values: 32 value-loss failures resolve, 264 broad
failures remain, and no new failure appears.

Strict selection includes all thirteen integer element/attribute families and
original invalid inputs: 60 descriptions / 536 message-direction combinations,
zero selected failures. Signed bounded fixtures use the exact integer comparator;
authored boundary tests enforce each builtin range. No stage is missing/skipped;
1492 broad infoset checks remain explicitly unassessed, and eight decimal value
checks remain failing. Original corpus/source hashes and historical findings
are unchanged. P3 remains active; this is not whole-phase acceptance.

Logs: /tmp/wsdl-p3-02-{affected-final-audit,python-final,docs,doc-example,survey,
coverage-final,independent-consumers}.log, /tmp/wsdl-p3-core-native-checks.log,
/tmp/wsdl-p3-core-valgrind-checks.log, /tmp/wsdl-p3-native-{ir,ast,valgrind}-*.log,
and /tmp/wsdl-p3-native-docs.log. The original assertion matrix/backtrace remain
under /tmp/wsdl-p3-02-crash and /tmp/wsdl-p3-02-crash-gdb.log.
Audit: [audits/P3-02-integer-range.md](audits/P3-02-integer-range.md).

Next P3 criteria: exact decimals and boolean/binary lexical spaces, IEEE32/64
semantics, lexical/value facets and enumerations, retained patterns, dates,
durations/partial dates, lists/unions and XSD regex validation/generation.

### Decimal conversion policy investigation (2026-09-08)

The user asked to consider `qore_number_private::applyRoundingHeuristic()` and
established standards/best practice. XSD 1.0 decimal has exact decimal values
and no exponent notation; JAXB maps it to BigDecimal. Java's preferred native
double-to-BigDecimal conversion uses Double.toString's short decimal that rounds
back to the supplied binary value. XPath 3.1 casts instead require the closest
representable decimal to the binary value; this is a separate casting contract,
not a requirement on a Qore SOAP binding's native input policy.

The recommended policy communicated to the user is to preserve exact incoming
XML decimal digits, and use round-trip-preserving decimal spelling for native
float/number inputs. A heuristic candidate is safe only if parsing at the source
number's precision reconstructs that value. Schema restrictions must not cause
additional rounding. Existing native 123.45/fractionDigits=2 behavior motivates
the short spelling; exact XML strings must retain meaningful trailing digits.

`/tmp/wsdl-decimal-heuristic.qr` verifies default Qore formatting changes native
`number("1.00000000000000000001")` to `"1"` and
`number("0.123450000000000000000006")` to `"0.12345"`, changing their values.
It preserves 123.45n and 0.1n. The heuristic alone is therefore insufficient for
lossless wire output. No global Qore rounding or float-to-number policy was changed
by this investigation. Decimal implementation is still pending.

Sources: [XSD decimal](https://www.w3.org/TR/xmlschema-2/#decimal),
[JAXB 4.0 mappings](https://jakarta.ee/specifications/xml-binding/4.0/jakarta-xml-binding-spec-4.0),
[BigDecimal.valueOf](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/math/BigDecimal.html#valueOf(double)),
[Double.toString](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/lang/Double.html#toString(double)),
[XPath 3.1 casts](https://www.w3.org/TR/xpath-functions-31/#casting-to-decimal).

## P3-03: boolean lexical space and list whitespace (2026-09-08)

Root causes: boolean serialization/provider conversion used permissive
`parse_boolean()`, decoding used case-insensitive substring matches and generic
truth conversion, and enclosing list providers converted strings through softbool
before the XML validator. Strict item validation also exposed list tokenization
splitting on SPACE before normalizing TAB/LF/CR.

The common boolean helper now accepts only the four XSD spellings after XML
whitespace collapse, native booleans, and numeric zero/one. Both wire directions
and providers use it; invalid input gets the corresponding SOAP or provider error.
The provider retains its native boolean output category and inherited Serializable
and optional/mandatory copying, but returns NOTHING for its conversion type so
list items reach validation first. Optional omission differs from null. List
decoding now applies its fixed collapse whitespace rule before finding items.

The first complete regression run exposed CDATA fragments reaching the scalar
validator as hashes; permissive boolean conversion previously hid this. Scalar
conversion now joins ordered text/CDATA fragments before lexical validation,
ignores comments, preserves a single native value wrapper, and rejects child
elements or invalid mixed native fragments. List decoding uses the same text
projection. Retained XML carriers still preserve their authored nodes. The
independent retained-context suite again passes its 80 document checks.

Normative requirements: XSD 1.0 part 2 sections
[3.2.2](https://www.w3.org/TR/xmlschema-2/#boolean) and
[2.5.1.2](https://www.w3.org/TR/xmlschema-2/#list-datatypes), including the four
boolean lexical forms and list whitespace fixed to collapse. Native numeric
zero/one acceptance is the binding's documented input policy, separate from
XPath's wider numeric truth casts.

Focused regression `test/wsdl-boolean-lexical.qtest` first failed three of four
cases against the parent implementation for invalid lexical acceptance,
provider preconversion and invalid attributes. The final version passes five
cases / 281 assertions, including all XML separators, empty lists, non-XML
separators, invalid types, optionality, reconstruction, unions and ordered scalar
text/CDATA. The independent
matrix adds 616 documents: 356 lexical inputs, 132 valid outputs, and 128 native
provider/example outputs. Alternating content cases use CDATA, including records
with attributes. Every document receives libxml2 and Xerces validation;
valid output also requires correct expanded names and boolean values. The first
test draft mistakenly classified a valid multi-boolean list as invalid; the
validator caught this, and the corrected malformed item is `false0`.

All 37 affected Qore suites pass (484 cases), including the seven required SOAP
consumers, with local development modules and --enable-debug. WSDL Qdx/Doxygen
passes without warnings/errors. No C++ code changed in this increment, so no new
Valgrind run is required. Both-version survey and complete adjudicated coverage
are byte-equivalent to P3-02 except runtime/source version metadata: 264 broad
failures, 60 descriptions / 536 selected directions, zero selected failures and
zero missing/skipped stages. Historical sources/findings remain unchanged.

Concurrent core DataProvider edits caused AOT source-hash warnings and then
qcc's input-changed error during a rebuild. Final checks use an immutable
DataProvider source export from core commit 860603291 at /tmp/wsdl-core-deps.
It was compiled with the existing qcc and tested Debug libqore, and its
Qore-Q-square.svg resource was copied beside the qmod. QORE_MODULE_DIR selects
/tmp/wsdl-core-deps/build/qlib-qmod/DataProvider. The main checkout's concurrent
source changes were not modified or committed. An initial CMake target attempt
was stopped while building libqore after its dependency graph was found to include
all binary modules; astparser was not rebuilt. Direct qcc compilation of the
snapshot avoids that unrelated dependency graph. The temporary test runner now
checks warnings case-insensitively, including AOT WARNING diagnostics.

Reproduce the dependency export with `git archive 860603291 qlib/DataProvider`
from the core repository, extract it under /tmp/wsdl-core-deps, compile it using
`qcc -m /tmp/wsdl-core-deps/qlib/DataProvider -o
/tmp/wsdl-core-deps/build/qlib-qmod/DataProvider/DataProvider.qmod`, and copy
Qore-Q-square.svg from that source directory beside the generated qmod.
The complete command/environment and qcc outcome are retained in the session
and /tmp/wsdl-p3-dataprovider-snapshot.log.

Final Python discovery runs 98 tests with exactly the seven tracked P4/P5/P6
failures, zero errors/skips and no warnings. The final focused rerun adds native
MPFR NaN/infinity/nonboolean number rejections and passes 5/281.

Logs: /tmp/wsdl-p3-03-boolean-before.log,
/tmp/wsdl-p3-03-boolean-final-reviewed.log,
/tmp/wsdl-p3-03-verified-wsdl-boolean-lexical.log,
/tmp/wsdl-p3-03-independent-cdata.log, /tmp/wsdl-p3-03-context.log,
/tmp/wsdl-p3-03-verified.log, /tmp/wsdl-p3-03-docs-verified.log,
/tmp/wsdl-p3-03-survey-verified.log, /tmp/wsdl-p3-03-coverage-verified.log and
/tmp/wsdl-p3-03-python-verified.log. Earlier python-final/complete logs retain
CDATA regression evidence; they do not describe the final implementation.
Audit: [audits/P3-03-boolean-lexical.md](audits/P3-03-boolean-lexical.md).

P3 remains active; decimal conversion, other scalar lexical/value facets and
enumerations, retained patterns, dates/durations, binary values and IEEE32/64
semantics still require implementation before the P4 boundary.


## P3-04 — Exact decimal lexical values and native round-trip formatting

The decimal binding now validates XSD syntax before numeric conversion. XML
text keeps every authored digit and normalized lexical spelling. Native finite
int/float/number input is supported; native float/number formatting uses the
explicit Qore 3.0 toStringRoundTrip() API. Compatible canonical inputs still
return floats when their round-trip spelling reproduces the input exactly;
other inputs return exact strings. XsdDecimalDataType validates before enclosing
provider/list conversion, supports optionality and survives Serializable
reconstruction. WSDL now requires Qore 3.0.

The root cause was two independent lossy conversions: blind float() on XML
input and general display formatting for native output. The existing MPFR
applyRoundingHeuristic() can remove meaningful zero/nine runs. The selected
binding uses exact source decimal strings and shortest source-precision binary
round-trip spelling instead. Its basis is XSD 1.0 decimal's exact i*10^-n value
space and non-exponent lexical space. Java BigDecimal.valueOf(double) supplies
a comparable canonical-spelling policy; this does not claim that MPFR is a
decimal storage type or that this is XPath's float-to-decimal cast contract.
See the implemented design in design/wsdl-scalar-values.md and the primary
references linked there.

Core dependency **20422dedf** adds Float/Number.toStringRoundTrip() and its C++
API without changing existing display/rounding/precision policy. The MPFR
formatter searches the minimum significand length, including directed decimal
neighbors around asymmetric binary rounding intervals. The native formatter
has an independent exact rational oracle (320 signed values at 128–8192 bits),
a Python binary64 oracle (1050 values), 84 IR/AST Qore cases / 1152 assertions,
and zero-error/zero-lost-memory Valgrind runs. Its full audit is in core
examples/test/qore/vars/audits/round-trip-formatting.md. The existing
DW_AT_abstract_origin reader warning remains the tracked P9 environment issue.
The tested binary's version banner retains its configure-time 9b3a235d7 hash;
the compiled formatter is the source subsequently committed as 20422dedf.

Focused XML tests pass **5 cases / 380 assertions**, including 2000-digit
strings, subnormal/overflow boundaries, nonfinite rejection, original decimal
spellings, list conversion, optionality, reconstruction and ordered CDATA.
The independent matrix validates **784 documents**: 432 lexical inputs, 160
serialized outputs and 192 provider/example outputs. Six actual SOAP 1.1/1.2
contracts and both request/response directions cover attributes, decimal simple
content, lists, decimal/boolean unions, expanded root names and exact Decimal
values. Every document is checked by Xerces. The old libxml2 2.12.10 decimal
pre-parser uses a 24-digit buffer before fractional trailing-zero trimming;
its 24 input, 24 output and 32 native-provider rejections are explicit oracle
disagreements, not accepted Qore errors. The tests also accept zero such
rejections on newer libxml2, while still checking every document and its exact
value. Source: GNOME/libxml2 v2.12.10 xmlschemastypes.c decimal parsing.

All **38 affected Qore suites / 489 cases** pass without warnings with local
Debug Qore and the committed DataProvider dependency export described above.
Qdx/Doxygen passes without warnings. The XML decimal suite also passes under
Valgrind with zero errors or definite/indirect/possible loss, using qore -b
--enable-debug; the already tracked P9 reader warning is not suppressed.

The both-version survey now has 279 parsed / 14 source-invalid descriptions,
976 successful / 140 failed deserializations, and 974 successful / 2 failed
serializations. Its unadjudicated libxml2 output-rejection metric remains 48;
8 valid-input/output-schema disagreements are old validator limitations,
not remaining decimal value losses. The adjudicated full coverage has
**252 failure rows**, down from 264, with no new failure rows. The resolved rows
are DecimalAttribute01 and DecimalElement05 output/value failures (eight), plus
DecimalSimpleTypePattern02 deserialization failures (four). Strict selection
adds all DecimalAttribute, DecimalElement and DecimalSimpleTypePattern messages:
**63 descriptions / 576 directions**, zero selected failures. Exact value
checks: 484 pass, zero fail, 324 unreachable, 1464 still unassessed. Source
fixtures, their hashes and the original findings/adjudication reports are
unchanged. Current reports identify the exact final WSDL source hash.

Full Python discovery runs 100 tests with exactly the seven retained P4/P5/P6
failures (four nested-choice checks, two binding-version checks, one wildcard
example check), zero errors/skips/warnings. These remain visible failures.

During this increment the user requested a core commit checkpoint. Existing
core foreign-key and REST routing fixes landed as a29e8a63e and eef86281d via
parallel work. Our expanded audit caught encoded Swagger path values and the
resource name "0" being treated as empty; **ed8e8b709** fixes those plus related
documentation findings, with 81 cases / 1246 assertions and a full 62-item audit.
No push was made. Active Fireworks work that appeared afterward remains with
its owner. The XML affected suites and corpus were rerun after this core work.

Final logs: /tmp/wsdl-p3-04-final-affected.log (and per-suite logs),
/tmp/wsdl-p3-04-final-docs.log, /tmp/wsdl-p3-04-final-survey.json/.log,
/tmp/wsdl-p3-04-final-coverage.json/.log, /tmp/wsdl-p3-04-independent.log,
/tmp/wsdl-p3-04-python-reviewed.log, /tmp/wsdl-p3-04-valgrind.log and
/tmp/wsdl-p3-04-valgrind-tests.log. Native logs and commands are recorded in
core's round-trip formatting audit. The full XML audit is
[audits/P3-04-decimal-lexical.md](audits/P3-04-decimal-lexical.md).

P3 remains active. Exact numeric bounds/digit facets and value enumerations,
non-decimal retained patterns, IEEE32/64, dates/durations/partial dates, binary
lexical validation and the remaining regex/list/union requirements must pass
before starting P4. This commit closes the base decimal conversion increment,
not the entire scalar phase or SOAP/WSDL compatibility plan.

## P3-05 — Exact numeric restriction values, providers and examples

Decimal/integer bounds, digit facets and enumeration now use exact XML numeric
values. The old bound validator cast strings to binary64, collapsing nearby
bounds and allowing values on the wrong side of them. Digit counts previously
used native display formatting, which could remove meaningful digits. Each
numeric restriction now validates XML lexical text and patterns before converting,
compares canonical decimal keys, and retains patterned integer lexical forms for
reserialization. Neither rounding nor a display heuristic changes a value to
satisfy its schema.

The digit rule was checked against XSD 1.0 Second Edition 4.3.11–12 and the
second-edition errata. Fractional leading zeros count because totalDigits bounds
both the coefficient and scale in i*10^-n; 0.0012 therefore requires four digits.
Integer leading zeros and fractional trailing zeros do not count. Enumeration
compares numeric values, so +001.2300 and 1.23 are equivalent and all decimal zero
spellings denote zero. Bounds remain exact for 2000-digit integers and decimals
below the native float range. References are in design/wsdl-scalar-values.md.

XsdNumericRestrictionDataType stores a typed scalar facet snapshot plus the base
provider, avoiding transient namespace/component ownership. Early reconstruction
checks exposed a weak Namespaces lifetime error in an initial schema-object-based
implementation; the final snapshot representation fixes that ownership problem.
The hashdecl is public so Serializable can reconstruct it in another Program.
Providers validate before list conversion and retain requiredness, inherited
patterns and exact output categories.

Consumer checks exposed generic field enumeration comparing raw string keys.
XsdNumericDataField retains declared AllowedValueInfo metadata while comparing
exact numeric keys, including fixed attributes and repeated-element choices.
Its setters publish only fully validated replacement maps; failed updates retain
the previous choices. Another consumer failure showed that list examples had no
value because WSMessageHelper had no list branch. List examples now use a valid
item example. Numeric examples use exact inherited bounds and digit grids and
validate every candidate. Empty integer grids or unsupported pattern/enumeration
intersections raise the precise XSD-SAMPLE-ERROR required by P3.

Focused Qore tests pass **10 cases / 413 assertions**, including nearby bounds,
negative/zero values, arbitrary precision, native values, equivalent enumeration,
pattern retention, inherited constraints, optionality, reconstruction, repeated
choices, fixed attributes and atomic field updates. All **39 affected Qore suites
/ 499 cases** pass without warnings (the final focused test extends the affected
runner's earlier nine-case numeric suite). The independent matrix checks **1,440
documents** with both libxml2 and Xerces: 560 lexical inputs, 304 successful
reserializations and 576 native/reconstructed provider/example outputs. There
are 432 separately asserted provider rejections. Real SOAP 1.1/1.2 bindings, both
directions, expanded names, exact Decimal values, attributes/simple content and
lists/unions are covered. No case or stage is skipped.

Both-version diagnostic survey: 279 parsed / 14 rejected descriptions;
992 successful / 124 failed decodes; 990 successful / 2 failed serializations;
1028 valid / 108 rejected inputs; 942 valid / 48 rejected outputs. The eight raw
valid-input/output disagreements remain adjudicated old-libxml2 limitations.
Adjudicated broad failures fall from **252 to 220**, with no new failure rows.
The 32 resolved rows are the second examples of Int, Long, Short, NonNegativeInteger,
PositiveInteger, UnsignedInt, UnsignedLong and UnsignedShort SimpleTypePattern,
in both versions/directions. All nine integer pattern families, also including
IntegerSimpleTypePattern, now have exact value assertions in strict selection:
**72 descriptions / 648 directions**, zero selected failures. Value stages:
556 pass, zero fail, 292 unreachable and 1424 unassessed. Original source bytes,
hashes, historical findings and source adjudication remain unchanged.

Qdx/Doxygen exposed a duplicate NAMED_ARGS anchor shared by the XML module and
Qore's code-flags documentation. The XML subsection now has the unique
xml_named_args identifier. Both native XML documentation and WSDL documentation
pass without warnings, with FAIL_ON_WARNINGS used for the native documentation
check. An initial manual Doxygen invocation used the repository root and emitted
tags there; these temporary tags were moved to /tmp and the check was rerun from
build-debug. The final checks use the normal Debug core tags, with no warning
suppression or substituted dependency documentation. No C++ changed, so this
increment does not require a new Valgrind run.

Current reports identify exact WSDL SHA-256
7c9596f35c2e17acdc37b9f81b34bb121c28eb7a78a0bfa07571684cb30e4c7a.
The concurrently rebuilt local Debug Qore reports core 7237f17a4, including the
committed numeric formatter. Tests continue to use the immutable DataProvider
export documented above. This increment makes no core or astparser changes.

Logs: /tmp/wsdl-p3-05-before.log, /tmp/wsdl-p3-05-sample-before.log,
/tmp/wsdl-p3-05-consumers-{second,third,fourth,fifth}.log retain root-cause
reproductions; /tmp/wsdl-p3-05-focused-final.log,
/tmp/wsdl-p3-05-final-affected.log and per-suite logs,
/tmp/wsdl-p3-05-independent-reviewed.log,
/tmp/wsdl-p3-05-final-{survey,coverage}.json/.log,
/tmp/wsdl-p3-05-xml-docs-final.log and /tmp/wsdl-p3-05-docs-clean.log are final
focused/corpus/doc evidence. Full Python final status is recorded in the audit.

P3 remains active. Next work includes schema facet declaration grammar and valid
restriction/fixed-facet rules (including arbitrary-size digit counts), general
value-space enumeration, IEEE float/double, date/duration/partial-date/binary
lexical semantics and the remaining regex/list/union criteria. This independently
tested increment closes numeric value facets, not the entire scalar phase.

Final audit: [audits/P3-05-numeric-facets.md](audits/P3-05-numeric-facets.md), all 62 items recorded with no failures.
Final Python discovery in /tmp/wsdl-p3-05-python-verified.log runs 102 tests with
exactly seven tracked P4/P5/P6 failures, zero errors/skips/warnings. The added
IntegerSimpleTypePattern assertion preserves its existing P9 coverage ownership;
its earlier mistaken P3 expectation was a test error. Final documentation wording
was rechecked in /tmp/wsdl-p3-05-docs-reviewed.log, and reports were rerun as
/tmp/wsdl-p3-05-reviewed-{survey,coverage}.json/.log to capture the final source hash.

## P3-06 — Numeric facet declarations

P3-05 was committed as e57a414 without pushing. The new declaration regressions
initially exposed missing/duplicate malformed facets, inapplicable numeric
facets, contradictory bounds, widening/fixed restrictions, invalid base-space
facet values and clamped digit counts. Namespace/order tests additionally proved
that grouping parsed children by local name accepted wrong-namespace facets and
misplaced annotations. Original failing reproductions are retained in
/tmp/wsdl-p3-06-{before,grammar-before,inherited-before,matrix-before}.log.

The implementation validates numeric declarations before schema publication,
checks inherited/builtin bounds and fixed constraints, and retains totalDigits
and fractionDigits as XsdFacetCount (int or exact decimal string). A streaming
stack in the existing schema grammar pass checks expanded names, derivation and
annotation order, facet attributes and content before grouped hashes lose that
information. Namespace scopes and XmlReader attribute position restore on error;
failed additions leave the original schema and its reconstructed copies usable.

The independent matrix has 86 authored cases, 172 atomic/simple-content schemas,
344 actual SOAP 1.1/1.2 contracts and 608 input/output documents in both directions.
Exact Decimal values and expanded names remain mandatory. Every known compiler
disagreement is named in
[facet-declarations-adjudication.md](facet-declarations-adjudication.md), using
XSD 1.0 Second Edition and its errata. This includes arbitrary-size counters,
repeated exclusive endpoints, inherited mixed bounds, and representation grammar.
Xerces and libxml2 disagreement never changes expected Qore schema validity.
Original W3C files, historical findings and earlier adjudications remain unchanged.

Focused Qore currently passes 10 cases/176 assertions; the numeric value suite
passes 10 cases/420 assertions with added malformed provider metadata coverage.
The first full affected run found one error-category regression: the streaming
simpleContent derivation check raised XSD-SIMPLETYPE-ERROR where existing complex
schema grammar raised WSDL-ERROR. The implementation now preserves WSDL-ERROR,
and the original simple-content suite passes 8 cases/43 assertions unchanged.
No production validation was weakened or negative expectation changed.

Final full Python discovery passes the new matrix and runs 103 tests, retaining
exactly seven tracked P4/P5/P6 failures (zero errors/skips/warnings). All 40 affected
Qore suites pass, totaling 509 cases without warnings. Final source checks pass in /tmp/wsdl-p3-06-python-reviewed.log,
/tmp/wsdl-p3-06-reviewed-affected.log, /tmp/wsdl-p3-06-docs-reviewed.log and
/tmp/wsdl-p3-06-{survey,coverage}-reviewed.json/.log. Final corpus counts, failure rows and stage accounting are identical to P3-05:
220 broad failures and zero selected failures; strict ownership remains 72
schema descriptions/648 directions. Both committed reports match final WSDL
SHA-256 028eb787df869635f643f65f75f31a5168b49b71dfc8a31f5320aec5673fbe2c.
Qdx/Doxygen also passes without warnings.

Tests use /tmp/wsdl-p3-06-env.sh. A concurrent core relink caused one early run's
loader to see a partial libqore file. The completed Debug executable/library were
copied into /tmp/wsdl-core-deps/runtime only after unchanged fstat metadata and ELF
checks; manifest.json records source paths and SHA-256. The immutable runtime
and committed DataProvider export avoid interference from other developers'
ongoing core changes. No core/astparser code, native XML code, installation or
push is part of this increment. The user's Qore checkpoint request found core
clean on develop at 79d06bece; later other-owner changes are still in progress.

The full audit is [audits/P3-06-facet-declarations.md](audits/P3-06-facet-declarations.md).
All 62 items are recorded as Pass or N/A with final validation evidence; no audit
failures remain.
P3 remains active for nonnumeric facets, IEEE float/double, dates/durations/partial
dates/binary lexical and value semantics, and remaining regex/list/union criteria.

## P3-07 — String and length facets

P3-06 was committed as 753f17b without pushing. This increment applies the
most-derived whitespace normalization before inherited string constraints,
interprets string enumeration in the base value space, and checks exact character,
octet and item counts. Length/whitespace declarations enforce applicability,
narrowing, fixed ancestors, consistent bounds and the XSD 1.0 exact-length
ancestor rules. QName/NOTATION length facets remain always satisfied.

XsdSizedRestrictionDataType retains scalar facet metadata, validates its base
category, and rebuilds its private string-membership map on reconstruction.
Optional and nested-list providers retain restrictions. String field choices
contain only values satisfying the complete restriction; empty intersections do
not prevent provider construction. String and length-based examples validate
complete restrictions or raise XSD-SAMPLE-ERROR with bounded generation.

List detection follows restrictions, unions and complex simple content. Repeated
list-valued elements keep an occurrence list around item lists, including a single
occurrence and empty item lists. Existing scalar singleton serialization counts
one item; NOTHING used as an empty list must satisfy zero-item constraints.
Builtin token-list strings keep their public representation and require at least
one item. Name/token examples use valid lexical seeds. XSD patterns now use
absolute PCRE anchors, so a trailing newline cannot escape the pattern check.

The repeated string-choice tests exposed a core DataProvider defect: the element
membership map used raw rather than resolved metadata, structural fallback
compared native values to metadata records, and replacements could retain stale
state or publish partial choices. Core commit cbb8aceb2 (originally 559317b00 before the concurrent session rebased
develop) fixes those paths. Eight
core suites passed 87 cases / 2432 assertions; focused tests also passed in AST
mode, Qdx passed, and all 62 audit items are recorded in
examples/test/qlib/DataProvider/ElementAllowedValues.audit.md. No push was made.

The Together/OpenAPI owner completed that change as bb64c1a98 and rebased both
local commits over the latest develop. The Qore checkout is now clean, develop is
ahead by two commits, and no push was made here. The DataProvider implementation,
regression suite and audit have identical content before and after that rebase.
The user's request to commit remaining core work is therefore complete.

Current XML verification uses /tmp/wsdl-p3-07-env.sh, the immutable runtime in
/tmp/wsdl-core-deps/runtime, and the DataProvider module snapshot with the same DataProvider code
in /tmp/wsdl-core-choices/build/qlib-qmod/DataProvider (manifest.json records hashes).
No native code changed, so this increment does not require a new Valgrind run.

The independent matrix covers 56 authored cases as 112 atomic/simple-content
schemas and 224 SOAP contracts, with 328 input and 176 serialized output documents.
A second matrix covers 17 consumer cases as 51 schemas and 102 contracts, checking
1464 original/reconstructed provider and example results with 896 emitted
documents. Together they independently assess 1400 input/output documents, exact
strings/integer-list values/binary octets, expanded names and actual SOAP 1.1/1.2
request/response bindings. Named libxml2/Xerces compiler disagreements are
adjudicated in sized-facets-adjudication.md. Xerces code-point counting is selected
before type initialization and verified by supplementary/combining-character cases.
No production verdict or independent Unicode-length check is waived.

Strict selection adds sixteen string/whitespace/enumeration/pattern/length families:
88 descriptions / 752 directions. Its value assertions distinguish preserve,
replace and collapse using XML whitespace only and independently detect value loss.
Historical findings and original corpus sources remain unchanged.

Final verification completed with the /tmp/wsdl-p3-07-completed-* log/report
prefix against WSDL SHA-256
47f82ce4865fb0861003b95c88b9144696ddb25e26023d89ed3c231eb374e456:

- All 41 affected Qore suites pass 521 cases without warnings; focused string and
  length tests pass 12 cases / 313 assertions.
- Full Python discovery runs 106 tests with exactly the seven tracked P4/P5/P6
  failures, zero new failures, errors, skips or warnings. The exact failure
  identities match the preceding complete run.
- The 1400-document independent string/length matrices pass their schema, value,
  rejection, reconstruction, provider and example expectations.
- WSDL Qdx/Doxygen completes without warnings. No new Valgrind run is required
  because this increment changes no C++.
- Both-version survey counts, every row, and original corpus source hashes are
  unchanged. Strict coverage passes 88 descriptions / 752 directions with zero
  selected failures; all 220 broad failure rows are unchanged. Value checks record
  660 assessed successes and no failures or missing stages. Both committed
  current reports identify the final source SHA-256 above.
- All 62 audit checklist items are Pass or N/A in
  audits/P3-07-string-length-facets.md; no audit failures remain.

Remaining P3 work includes list-item lexical validation (including empty or
whitespace-containing native items), list/union value enumeration and retained
patterns, IEEE binary32/binary64 semantics, dates/durations/partial dates, binary
lexical/value rules, names/entity context and remaining regex requirements.
Current list patterns still inspect a Qore list's formatted text rather than the
whole XML list lexical form; list enumeration still uses raw hash keys. These
are the next list/union implementation criteria, not completed by this length
increment. Native float/double parsing remains permissive and shares binary64;
parsing decimal as binary64 then narrowing to binary32 would double-round and
cannot implement correct target-format conversion. P3 remains active; P4–P9
are still required after its acceptance gate passes.

## P3-08 — List lexical forms and value equality (complete)

P3-07 is committed as 335672b without pushing. Initial preflight in
/tmp/wsdl-p3-08-preflight.py and /tmp/wsdl-p3-08-preflight.json uses three schemas
with real SOAP 1.1/1.2 requests and responses. Pinned Xerces accepts all schemas
and agrees with all 24 positive/negative document verdicts. Qore rejects all twelve
valid inputs: integer/boolean list enumerations compare native lists with raw
lexical hash keys, and whole-list patterns attempt string(list) and raise
RUNTIME-OVERLOAD-ERROR rather than checking the normalized XML list lexical form.

The next implementation builds on completed boolean, decimal/integer and string
scalar conversion. List-item lexical boundary validation must reject native
empty/whitespace-containing items that would silently change the list on output.
Whole-list patterns must retain each token's valid lexical spelling through
conversion/reconstruction and serialization. List choices must compare ordered
item values using their atomic value spaces, and providers must enforce the same
rules after detachment/reconstruction. Union, float/double, dates/partial dates,
binary and QName/entity families retain their complete P3 acceptance requirements;
this ordering of small commits does not remove any phase deliverable.

Implemented list conversion now keeps ordered atomic values separate from whole
list lexical tokens. String/boolean/decimal/integer list enumerations use exact,
unambiguous length-prefixed value keys, deduplicate equivalent declarations and
handle empty lists. Whole-list patterns retain accepted token spellings through
binding/provider reconstruction. Native empty or XML-whitespace-bearing items
are rejected before they can introduce value loss on serialization. Invalid
native list input reports the serialization/deserialization error category.

XsdListDataType and XsdListRestrictionDataType retain strong item providers,
validate metadata before reconstruction/publication and preserve constraints in
optional/nested providers. XsdListDataField uses ordered value equality for
whole/repeated choices; failed replacements leave prior metadata untouched.
Atomic/attribute/simple-content/choice/message field construction uses the right
field class while preserving public WSDL part names. Generated list examples
must satisfy all item and list facets or report XSD-SAMPLE-ERROR.

The independent matrices cover 18 authored cases as 54 schemas and 108 actual
SOAP contracts each. Binding tests assess 576 input and 276 emitted documents.
Consumer tests check 4176 results for original/reconstructed contracts and detached
element/message providers, with 2288 emitted/provider/example documents. Together
these are 3140 independently checked documents, including exact decimals/large
integers, boolean values, item order, XML-only whitespace and actual SOAP 1.1/1.2
request/response envelopes.

Oracle investigation found a harness root cause: its ErrorHandler promoted all
Xerces warnings to schema rejection. The protocol now retains ordered warnings
separately; actual error/fatal-error events still reject validation. The list
matrix checks the exact FacetsContradict warning for empty intersections and
Xerces's character-count warning on an otherwise valid two-item enumeration.
The reference-permission matrix explicitly retains Xerces's EmptyTargetNamespace
warnings and Qore's mandatory rejection. Libxml2's empty-list enumeration null
value defect is adjudicated; Xerces validates all documents for that case, and
no Qore verdict or exact-value assertion is waived. Details and primary source
references are in list-values-adjudication.md.

The W3C List family adds exact ordered string-list assertions to the strict gate:
89 descriptions / 756 message directions, 664 successful value checks, no failed
or missing value checks, and no selected failures. The broad failure list has
exactly the same 220 rows. Every original survey row, input result and corpus
source hash is unchanged. Both refreshed reports identify final WSDL SHA-256
4fb454d9a3b93d41b8a075667a6dca064ffa39974c668ab3dcfdbb04035b936e.

42 affected Qore suites pass 533 cases without warnings; the focused list suite
passes 12 cases / 165 assertions. Qdx/Doxygen is clean after adding the missing
lexical parameter documentation. No C++ changed, so no new Valgrind run applies.
The final Python rerun passes its expectations: 110 tests run with exactly the
seven previously tracked P4/P5/P6 failures, zero new failures, errors, skips or
warnings. Their exact failure identities match the prior P3-07 run. Logs are
/tmp/wsdl-p3-08-final-affected.log and /tmp/wsdl-p3-08-completed-*; the latter
reports/focused/docs/Python results include the final documentation correction.
Those seven later-phase failures remain required P4/P5/P6 implementation work.
The full 62-item audit is recorded in audits/P3-08-list-values.md.

The next P3 reproducer is /tmp/wsdl-p3-09-preflight.py with evidence in
/tmp/wsdl-p3-09-preflight.json. XSD 1.0 boolean permits only pattern and whiteSpace
facets; Qore currently accepts invalid enumeration/ordered-bound declarations.
A valid boolean input 1 constrained by pattern 1 is serialized as true, producing
invalid output. Pinned Xerces independently rejects both invalid schemas, accepts
all four original request/response inputs and rejects all four emitted outputs.
This is an existing scalar-restriction gap, separate from the completed whole-list
pattern/value increment. Boolean restrictions, union selection/value semantics,
IEEE binary32/binary64 conversion, dates/durations/partial dates, strict binary
rules, names/entity context and remaining regex requirements are still required
for P3 acceptance; P4–P9 remain in scope afterward.


## P3-09 — Boolean lexical restrictions (complete)

P3-08 is committed as 64e4d23 without pushing. Boolean restrictions now reject
facets that XSD 1.0 does not permit, apply patterns to normalized lexical spellings
before conversion, and retain accepted patterned strings through serialization and
provider reconstruction. Unpatterned boolean types retain their native boolean
representation. Native booleans/numeric zero-one use canonical true/false spellings
and must satisfy the same pattern checks.

XsdBooleanRestrictionDataType validates typed metadata and base-provider identity
before reconstruction; optional/repeated providers retain restrictions. The audit
found and fixed an inherited-default path that could return before checking the
restriction's patterns. XsdBooleanDataField and fixed attributes compare truth
values independently of lexical patterns, including global references and complex
type restrictions. Choice setters resolve complete replacement state before
publication. Examples exhaust the four legal spellings and report XSD-SAMPLE-ERROR
for an empty pattern intersection.

13 focused Qore cases pass 184 assertions. All 43 affected suites pass 546 cases
without warnings. The independent matrices assess 2320 documents and 3104 consumer
rows across atomic values, simple content/attributes, repeated values, fixed flags,
patterned list items, actual SOAP 1.1/1.2 bindings, both directions and reconstructed
contracts/providers. Twenty forbidden-facet schemas reject in libxml2/Xerces and
all 40 corresponding Qore SOAP contracts. No reference verdict is waived.

Full Python discovery runs 113 tests with exactly the same seven P4/P5/P6 failures,
zero new failures, errors, skips or warnings. Final affected/matrix/docs checks
include the default-path audit correction. Qdx/Doxygen is clean. No C++ changed.
Strict coverage remains 89 descriptions/756 directions, 664 successful value checks,
zero failed/missing value checks and no selected failures. Every previous survey
and coverage case record, source hash, count and all 220 broad failure rows are
unchanged. Final WSDL SHA-256 is
e04a9cc66988dce2898b29e020905075e4432c5f9c4f5f9710ec11d04b8d1427.
Logs: /tmp/wsdl-p3-09-final-python.log and /tmp/wsdl-p3-09-completed-*.
All 62 audit items are Pass/N/A in audits/P3-09-boolean-facets.md; normative and
matrix details are in boolean-facets-evidence.md.

P3 remains active: union member selection/value equality and retained patterns,
IEEE binary32/binary64 conversion, dates/durations/partial dates, strict binary
lexical/value rules, QName/entity context and remaining regex requirements are
still required before its acceptance gate. P4–P9 remain required afterward.
The concurrent Qore Groq/DataProvider checkout is still receiving its owner's
changes; no additional core edits or commits belong to P3-09. The earlier core
commit request was completed with cbb8aceb2, bb64c1a98 and f6373c759; the user has
been asked whether the newer active changes are ready for a commit handoff.


## P3-10 — Union provider validation and traversal (complete)

P3-09 is committed as 715ee2f without pushing. Union providers now preserve
explicit mandatory/optional behavior through reconstruction and require enclosing
occurrence lists to validate each item. Ordered member conversion and inherited
member constraints remain intact. Metadata reconstruction rejects empty/nonprovider
members and nonboolean optionality before publishing state; older metadata retains
mandatory semantics.

Shared provider graphs now use typed caches for each runtime/metadata call.
Object contexts avoid repeated copy-on-write map cloning. Active entries reject
cycles; on_exit clears/restores state after success, rejection and cancellation.
Reentrant inputs distinguish native types, signed zero, number precision and date
timezone representation; nested list/hash NaNs can reuse failed trials. A 28-level
shared graph verifies one terminal visit per operation and fresh state on retry.

Union schema trials propagate unexpected errors. The corpus review exposed two
date/string families that had relied on swallowing raw native date rejection.
Builtin date/binary converters now translate only input parse rejection to the
directional SOAP error, retaining the native diagnostic. Focused schema tests cover
date, dateTime, time, base64Binary and hexBinary fallback through reconstruction.
The initial eight date/string corpus regressions were fixed before this commit.

All 44 affected Qore suites pass 557 cases without warnings; the union suite passes
11 cases/197 assertions. Six independent cases cover 2580 validated documents and
2784 consumer rows through atomic elements, simple content/attributes, repeated
elements, reconstructed contracts/providers, examples and actual SOAP 1.1/1.2
bindings in both directions. Xerces checks all verdicts without warnings. Libxml2's
previously adjudicated 24-digit decimal limit is retained as a precisely checked
reference limitation; no Qore or exact-value assertion is waived.

Final Python discovery runs 115 tests with exactly the seven existing P4/P5/P6
failures, no new failures/errors/skips/warnings and identical failure identities.
Qdx/Doxygen is clean. Strict coverage remains 89 descriptions/756 directions,
664 successful value checks, zero failed/missing value checks and no selected
failures. All 220 broad failure rows, corpus verdicts, counts and source hashes
are unchanged. Eight diagnostic survey rows (and their corresponding directional
coverage entries) now use SOAP-DESERIALIZATION-ERROR for the existing five-digit
date failures, with their original descriptions retained. These remain P3 failures.
Final WSDL SHA-256: 42cac931187e15f537d92ecea08e9dd291ff13f6ff27a756d627088a63910967.
Logs: /tmp/wsdl-p3-10-audited-*. Full 62-item audit:
audits/P3-10-union-providers.md. No C++ or core Qore edit belongs to this increment.

Qore develop is clean at d70ed3718: its owner committed the concurrent Groq work.
The user's latest core commit request therefore has no remaining uncommitted work;
nothing was pushed. The immutable XML test runtime/provider snapshot is unchanged.

P3 remains active. Next union criteria are normalized lexical patterns, primitive
value identity and enumeration, declaration applicability, examples, lists of
unions and bounded schema graph processing. The independent preflight records
24 mismatched input verdicts, eight invalid outputs and two accepted invalid
contracts; union-providers-evidence.md retains the cases and normative references.

The separate date preflight additionally confirms that TimeZone's single-string
parser suppresses malformed input errors, allowing soft date providers to return
the epoch for arbitrary text. Valid date strings work with or without the optional
format argument, ruling out numeric overload selection. Prefixing malformed time
text can also admit midnight. These core/parser findings remain required P3 date
work, alongside five-digit/negative years, timezones and fractional precision.
IEEE conversion, durations/partial dates, strict binary semantics, QName/entity
context and remaining regex work also remain required. P4-P9 follow P3 acceptance.


## P3-11 — XML and union whitespace (complete)

Native text escapes CR, CDATA splits around CR references, and formatting avoids
adding character data around text/CDATA or preserved-space content. Parsing
retains scalar/mixed whitespace and inherited xml:space (including subtree readers),
then omits child-only indentation under the default policy. Per-name counters and
shared insertion logic preserve repeated-child grouping in expected linear time.
Cancellation and partial-tree cleanup are tested under Valgrind.

Union members retain their own whitespace semantics; ordered bounds are rejected
on union restrictions and scalar comment wrappers survive serialization. Temporary
element-only schema and SOAP container views accept XML formatting whitespace and
reject non-whitespace text without changing retained XML. The local authored i4452
fixture now declares mixed=true for its existing text/CDATA test data, with independent
old/new validation and source hashes in union-whitespace-evidence.md. The AOT build's
unreachable break after SOAP-SEARCH-ERROR is removed and its documented exception fixed. Provider documentation now describes operation children and the actual request/response APIs; its example passes against the local fixture. Core prerequisite afded8c83 excludes resource assets from generated documentation inputs; its five CMake tests pass on 3.18.4 and 4.3.0 and actual provider docs are clean.

Validation: 55 affected Qore suites / 653 cases pass; focused native 7 cases / 1863
assertions and union 5 cases / 145 assertions. Six final independent checks pass:
492 union binding documents, 1264 consumer documents, 120 pattern documents, 48
invalid union contracts, old/new mixed fixture validity, and document/multi-parameter
RPC whitespace boundaries. WSDL/native/provider documentation and affected native/AOT
builds are clean. Native/union/SOAP Valgrind logs have zero errors and zero definite,
indirect/possible loss; the final relinked artifact was separately rechecked.
The known core DWARF metadata warning remains visible; no memory suppression is used.
The offline Salesforce connection case additionally passes two assertions.

Full Python discovery ran 122 tests with 33 failures: the prior seven P4/P5/P6
failures and two newly exposed P6 requirement groups (26 subtest/accounting failures),
reproduced using the previous WSDL/native code. The subsequently added independent
fixture test also passes. Strict coverage remains 89 descriptions / 756 directions,
664 value checks and no selected failure. All 220 broad failures and source hashes
remain; two invalid LocalElementSimpleType messages now report non-whitespace
content directly. WSDL SHA-256: 774583b452ea79d27399426ee9f6fb4480dd6e6d69e543b7877df8d807d707b7. Final audit: audits/P3-11-union-whitespace.md.
Logs: /tmp/wsdl-p3-11-final-*; old/intermediate failures are retained separately.

The initial P3-10 preflight's 24 mismatched inputs included eight Xerces-only
union-pattern whitespace disagreements: XSD delegates whitespace to the member,
whereas Xerces 2.12.2 collapses a union's own pattern input. The precise 24-document
oracle discrepancy is pinned and tested, without waiving a Qore verdict. Sixteen
confirmed union input mismatches and eight invalid outputs remain required P3
value/enum/retained-pattern work; the two invalid ordered-bound declarations are fixed.

P6 now has explicit failures for selected single body-part round trips losing Body,
RPC headers being required again as body parameters, and scalar RPC results failing
the serializer's reference<hash<auto>> requirement. Their baseline rows and root
causes are in union-whitespace-evidence.md and test_soap_container_whitespace.py.
They remain failures until P6, not expected-success or skipped cases.

P3 continues with ordered union primitive-family/value identity, enumeration and
retained lexical restrictions through providers/lists/examples, followed by date,
IEEE, binary, QName/entity and remaining regex criteria. TimeZone's nonthrowing date
constructor remains a separate required core fix. The separate XML-RPC escaping
sites still need the same CR/scalar-whitespace boundary review in P3. P4-P9 follow
P3 acceptance; no phase scope is reduced. Core develop was clean when the user's
commit request was checked. The subsequently discovered CMake documentation fix was
tested, fully audited and committed there as afded8c83; nothing is pushed.


## P3-12 — bounded schema union traversal (complete)

P3-11 is committed as a28bfa6; core documentation prerequisite afded8c83 is on
core develop without pushing. Schema serialization/deserialization and native-list
shape queries now memoize shared members for one contextual operation. Active
entries reject cycles and on_exit restores caller state on completion, cancellation
or unexpected errors. Only ordinary SOAP rejection is cached. Nested diagnostics
summarize immediate failures without duplicating shared descendants; atomic causes
and the legacy "union types" wording remain.

The provider input comparator is shared unchanged. Serialization keys include
namespace context and type-attribute policy; deserialization keys include element
name, type and reference maps. Reference comparisons preserve signed zero, NaN and
number precision. The audit reproduced and fixed a false cycle when a reentrant
reference map changed -0.0 to 0.0. Per-call metadata caches also observe configuration
changes between queries. No data result or accepted member order is changed here.

Validation: 56 affected Qore suites / 658 cases pass. New
wsdl-union-schema-graphs.qtest passes 5 cases / 143 assertions; the existing provider
suite passes 11 cases / 197 assertions. A 7-level pre-fix graph made 256 terminal
calls; 32-level graphs now visit each terminal once per operation, with bounded
error messages. Tests cover success, typed/comment wrappers, metadata, cycles,
ordinary/unexpected failures, cleanup and all reentrant contexts. Independent
atomic/list graphs pass real SOAP 1.1/1.2 requests/responses, reconstructed contracts,
providers, attributes, repeated values and examples.

Full Python discovery: 125 tests, exactly the same 33 tracked P4/P5/P6 failures,
no new failure/error/skip. Both corpus reports are identical outside version
metadata: strict 89 descriptions / 756 directions, 664 value checks, no selected
failures, 220 broad failures. The initial survey omitted the pinned import catalog;
its missing-resource diagnostics are preserved separately, and final surveys use
the catalog. WSDL/SoapClient/SoapDataProvider AOT and WSDL Qdx/Doxygen builds are
clean. No C++ changes or Valgrind requirement for this increment. WSDL SHA-256:
6a7392fb7c50bfb65ea31f474dbef8e975c5ab9a55d5a8f105e75c84846e0c97. Full audit: audits/P3-12-union-schema-graphs.md.
Logs: /tmp/wsdl-p3-12-final-*, /tmp/wsdl-p3-12-reviewed-*; baseline and intermediate
failures are retained. Nothing is pushed.

Next P3: ordered union primitive-family/value identity, enumeration and retained
lexical restrictions through providers/lists/examples, then date, IEEE, binary,
QName/entity and remaining regex requirements. TimeZone's nonthrowing date constructor
and XML-RPC escaping/whitespace remain required boundary reviews. P4-P9 follow P3
acceptance; the authorized phase scope is unchanged.

## P3-13 — Union value identity and checked date prerequisite (in progress)

The independent core prerequisite is committed on Qore develop as 512b4e298 (originally 7f161ec1b before parallel history maintenance):
TimeZone::date(string) now passes both its zone and ExceptionSink to the existing
absolute-date parser through an additive DateTimeNode constructor. ReferenceHolder
retains the result until parsing succeeds; the QPP method now uses RET_VALUE_ONLY.
Malformed/calendar/time/offset input detected by the parser raises INVALID-DATE.
Unzoned values retain the object's zone and daylight saving rules; explicit ISO
offsets and HTTP/email date behavior remain intact. XSD lexical validation still
belongs to P3; this flexible core parser is not an XSD date validator.

Validation used the isolated /tmp/wsdl-core-date checkout and its build-debug
directory, Debug with /usr matching /usr/bin/qore. New regression: 5 cases / 59
assertions in all four execution modes under UTC and Europe/Prague. Sixteen core
runs report 66 cases / 1446 assertions; existing Windows-only checks remain
inapplicable on Linux. New and existing date suites pass Valgrind with no errors
or definite/indirect/possible leaks, using -b --enable-debug and PCRE2's supported
JIT opt-out. Focused native/QPP Doxygen and executed examples pass. All 62 audit
items are resolved in Qore's examples/test/qore/vars/audits/timezone-date-errors.md.

All 56 affected XML/SOAP suites pass with the final runtime: 658 cases without
runtime diagnostics. Both-version survey and strict coverage are identical to
P3-12 outside versions: 89 selected WSDLs / 756 directions, no selected failures.
Logs and JSON: /tmp/wsdl-core-date-final-*. Runtime SHA-256:
cd01f8657d66b37f858a86f492a861ef216e28006cfabb10dc94f920e6d42476.
For subsequent work, /tmp/wsdl-core-date-env.sh selects this runtime and the
matching isolated DataProvider AOT build. The initial downstream runs diagnosed
a stale DataProvider source hash after concurrent main-repository edits; rebuilding
the isolated module and its dependencies removed the diagnostic without suppression.
The main Qore checkout was clean after commit; this task did not push.

The fresh dependency build also exposes separate P9 compiler/tooling findings:
GCC 16.2.1 ngtcp2 -Winline under -Og; jsoncons bigint allocator-temporary
-Wmaybe-uninitialized; DataFrame's raw QoreValue bit copy -Wclass-memaccess and
unused qdfCallObjectMethod overload. Their exact locations and diagnostics are in
/tmp/wsdl-core-date-{build,aot-build}.log and the core audit. The existing Valgrind
DW_AT_abstract_origin reader warning remains open for P9. No warning-free whole
dependency build is claimed, and none of these diagnostics is hidden or counted
as a passing compatibility requirement.

Next: preserve ordered union primitive-family/value identity, then enforce union
enumeration and lexical restrictions through schema, providers, lists and examples.
The remaining P3 and P4-P9 scope recorded above is unchanged.


### P3-13 core error-cleanup prerequisite

Malformed union provider metadata exposed a core deserialization use-after-free:
indexed hash/list initialization helpers adopted the index owner's reference and
released it on member failure. Qore develop commit bac32354a acquires independent
helper references and owns the returned values in the indexed caller. The fix,
regression, release notes, ownership design and full 62-item audit are committed;
nothing was pushed. Parallel DeepSeek work was independently committed as
b93680164, and the main checkout is clean after this task's core commit.

The final isolated Debug runtime SHA-256 is
fc3a60454896701c17913c4ed768678959f9788c059be20c334d72a43ab2ac80.
The baseline core regression exits 139; the fixed new/existing Serializable suites
pass in AST, IR, JIT and tiered modes (48 cases / 596 assertions), and the existing
hashdecl suite passes 10 cases / 220 assertions. Both Serializable suites and the
expanded XML union suite pass Valgrind with no errors or definite/indirect/possible
loss. The previously recorded debug-information reader warning remains visible.
The core audit is examples/test/qore/classes/Serializable/audits/indexed-container-errors.md.

Before the subsequent enum-metadata audit refinement, all 57 affected XML suites
pass: 668 cases / 10983 assertions. The union regression passes 10 cases / 293
assertions; both independent union value matrices pass. SOAP 1.1/1.2 survey and
strict coverage are identical outside version metadata to the pre-core-fix P3-13
reports (89 selected WSDLs / 756 directions, zero selected failures, 220 broad
failures). Logs and JSON: /tmp/wsdl-indexed-errors-*.

The current union implementation covers exact decimal/integer, boolean, string
and distinct hex/base64 primitive identities, lexical retention on changed member
selection, union patterns/enumerations, detached providers and finite field choices.
Final XML audit/build/testing is still pending. Full list-valued union identities,
remaining primitive families and native-input ambiguity remain required P3 work,
alongside the date/IEEE/binary/QName/entity/regex and XML-RPC boundaries already
listed above. No P3 or final-acceptance claim is made for this increment.


The final P3-13 docs configuration must retain the previously verified JNI module
at /home/david/src/qore/git/module-jni/build-debug. The first isolated-runtime
configuration omitted that path and rediscovered the installed JNI native-frame
line -2 assertion already recorded in P2-10. GDB again identifies JniCallStack in
the installed module. Existing JNI develop commit 0576b97 contains the normalization;
qjar succeeds with that Debug module and matching isolated reflection/astparser
artifacts selected. QORE_MODULE_DIR_FOR_DOCS now records these paths explicitly.
No additional JNI or core code change is needed, and the failed diagnostics remain
in /tmp/wsdl-p3-13-{final-docs,final-docs-sequential,qjar-assert-gdb}.log.


### P3-13 final audit and verification

The final enumeration audit adds rejection of invalid restored enum values and
propagates unexpected conversion errors while reporting choices; both regressions
fail before their fixes. Final wsdl-union-value-identity.qtest passes 12 cases /
311 assertions from source and from the rebuilt AOT module. All 57 affected XML
suites pass, 670 cases / 11001 recorded assertions; 11 independent union methods
pass. Full Python discovery before the last error-reporting guard runs 127 tests
with exactly the same 33 tracked P4/P5/P6 failure signatures; the final guard is
then covered by the complete affected Qore and independent union suites.

Final SOAP 1.1/1.2 survey and strict coverage are unchanged outside versions:
89 selected WSDLs / 756 directions, zero selected failures, 220 broad failures.
WSDL/SoapClient/SoapDataProvider AOT and native/WSDL documentation including qjar
pass without warnings or errors with the fixed local JNI path. Post-relink
Valgrind for the then 11-case union suite passes 305 assertions, zero errors and
zero definite/indirect/possible loss; the known DWARF reader diagnostic remains.
No native XML source changed in this increment.

Final WSDL SHA-256: a481f15526cf54cf4b284679c6e41b57cba8500c1fc1088550475fbc0faff37c.
Native XML SHA-256: 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.
Evidence: /tmp/wsdl-p3-13-reviewed-*, final-python.log, final-valgrind.log, and
all baseline/fixed logs. A matrix stdout/per-suite filename collision is preserved
in reviewed-matrix-combined.log; xml.qtest was rerun separately and all 57 per-suite
summaries were verified in reviewed-checks.json. Full 62-item audit:
audits/P3-13-union-value-identity.md. Remaining P3 and all P4-P9 requirements above
are unchanged; the phase is still in progress.


### P3-14 atomic list values in unions

Atomic list members now carry ordered primitive item identities through schema
conversion and detached providers. Exact integer/decimal lists can compare equal;
boolean/string/binary families and single-item lists versus atomic values remain
distinct. XML list text is split before member conversion; native item boundaries
remain strict. Ambiguous conversions retain item spellings in native lists, and
whole-union patterns can retain complete lexical text. Enumeration and finite field
choices share these keys. Typed metadata follows member reordering/pruning and
validates item rules, provider identities, list shape and mandatory items.

The baseline converts boolean list 1 0 into string list true false, rejects
numeric-equivalent list enumerations, and directly casts native provider lists to
string. Six initial regressions fail; binary coverage separately exposes native
PARSE-HEX-ERROR escaping instead of trying the valid base64 list. The conversion,
identity and error-category fixes pass 10 cases / 214 assertions from source and
rebuilt AOT. All 58 affected XML suites pass: 680 cases / 12246 assertions. The
previous P3-13 aggregate omitted soap.qtest's 1031 assertion count; the original
57 passing logs contain 12032. No historical artifact is rewritten.

The independent matrix covers 24 schemas / 48 SOAP 1.1/1.2 contracts, 588 input
and 312 emitted binding documents, 3520 consumer results and 2048 emitted/provider/
example documents. Xerces assesses all 2948 documents with no warnings. The existing
libxml2 empty-list enumeration compiler defect also affects these unions: three
schemas and 72/176 documents in the respective matrices remain unassessed by
libxml2. Both system 2.12.10 and private 2.15.4 reproduce it. The new binary matrix
also exposes exactly 12 libxml2 false positives for !? ???, caused by its base64
parser following MIME's nonalphabet-character tolerance instead of XSD's grammar.
Qore, Xerces and strict Python base64 reject those inputs. Exact diagnostic/input
checks and counters preserve both oracle findings; no Qore verdict is waived.
See list-values-adjudication.md for root causes and normative references.

Full Python discovery runs 129 methods. Apart from those 12 newly adjudicated
oracle false positives, its 33 tracked P4/P5/P6 failure signatures are identical
to P3-13. The affected two-method independent matrix passes after the precise
adjudication; production code is unchanged after full discovery. Both-version
survey and strict coverage are identical to P3-13 outside versions: 89 selected
WSDLs / 756 directions, zero selected failures, 220 broad diagnostic failures.
AOT and WSDL/native docs including qjar pass without warnings/errors. No C++ source
changed; no additional Valgrind run is required for this Qore increment.

Final WSDL SHA-256: 01f96dbb5449251b09ddc3d2c9a4a739bdfba686ccc4ce6988a67dc25137f0b6.
Native XML SHA-256: 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.
Logs/reports: /tmp/wsdl-p3-14-*. Full 62-item audit:
audits/P3-14-union-list-values.md.

The user's Qore commit request is satisfied: another developer completed and
committed the remaining DeepSeek follow-up as 39c4da922; the main develop checkout
was then clean. Earlier XML prerequisites bac32354a and 512b4e298 remain committed.
This task made no additional main-Qore changes and did not push.

Next P3 increment: list members whose items are themselves atomic unions.
/tmp/wsdl-p3-15-union-items-{probe.qr,baseline.log} reproduces a list of boolean/int
union items followed by a decimal list, restricted by enumeration 01 2. Equivalent
1.0 2.00 is rejected and detached provider choice validation still casts that
unclassified native list to string. The root is missing per-item union identity
metadata; atomic-item lists are fixed here. This is retained as required P3-15
work, along with the remaining primitive families and native-input ambiguity.
All earlier remaining date/IEEE/binary/QName/entity/regex/XML-RPC requirements and
all P4-P9 requirements remain in scope. P3 acceptance is not yet complete.


### P3-15: union-valued list items

The implementation captures the primitive identity chosen during actual item
conversion, including restriction wrappers. List members retain ordered values
for enclosing union enumeration and finite field choices. Captures do not replay
custom validators, and thread-local scope/depth restores state after reentry,
second-item errors or cancellation. Detached metadata validates union item
providers and excludes simultaneous atomic descriptors; old atomic metadata remains
compatible. Tests cover mixed boolean/decimal identity, text/binary items, empty
and invalid native boundaries, patterns, restrictions, metadata corruption and
reorder/pruning, finite choices, shared diamonds, cycles, reentry and cleanup.

Eleven source and compiled AOT cases pass 251 assertions. All 59 affected suites
pass 691 cases / 12497 recorded assertions. Full Python discovery runs 131 methods
with exactly the same 33 tracked P4/P5/P6 failure signatures, including after the
final Qore runtime fix. Survey and strict coverage are unchanged outside versions:
89 selected WSDLs / 756 directions, zero selected failures, 220 broad failures.
The new independent matrix covers 18 schemas, 36 real SOAP contracts, 408 input
and 180 emitted binding documents, and 1248 consumer/output/example documents.
Xerces assesses all 1836 documents. Exactly 48 binding and 128 consumer verdicts
are the source-adjudicated LISTOFUNION_DT/LIST_DT enumeration false negative;
libxml2 and exact ordered primitive values validate those documents. The libxml2
empty-list enumeration compiler defect remains separately counted: three schemas,
72 binding and 176 consumer documents unassessed there, assessed by Xerces and
exact values. See list-values-adjudication.md; no production verdict is waived.

AOT integration exposed two Qore root causes: generic hash-field map specialization
built list<auto> without the AST's actual value type inference, and common-type
folding erased optional types when followed by either their non-optional type or
repeated NOTHING. IR now calls the same typed, cancellation-aware map helper as
JIT/AOT. The Qore fix is committed on develop as 3e2f47be0, with no push and a clean
main checkout afterward. Its regression passes three cases / 28 assertions across
AST/IR/JIT/source-stripped AOT, both append paths and deterministic native
cancellation. Eleven affected existing core suites pass. Core, cancellation and
compiled XML Valgrind runs report zero errors and zero definite/indirect/possible
loss, without suppressions. The known DWARF reader warning remains tracked for P9.

WSDL/SoapClient/SoapDataProvider AOT and WSDL docs/qjar builds pass without warnings
or errors. Final WSDL SHA-256 is
c0bc371468726c34941e844ba9e951848fbd469358e21ce7a851c7e40e53e581;
native XML remains 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.
Final runtime library SHA-256 is
67f2c22aaaac71cec3a75b19b5417e0231d6d999fca55125fe36c87bd29057df.
Full 62-item audits: audits/P3-15-union-list-items.md and
audits/P3-15-qore-map-types.md. Evidence is retained under /tmp/wsdl-p3-15-, with
final-core checks/survey/coverage, python-core-final and comparison reports,
source/AOT/native regression, build, docs and Valgrind logs identified in the audits.

The next required P3 increment is independently reproduced by
/tmp/wsdl-p3-16-list-own-facets-{probe.qr,baseline.log}: enumeration declared on a
list whose items are boolean/int unions rejects valid 01 2 in schema conversion
and accepts invalid 01 3 through a detached provider. Atomic-only list facet
metadata does not describe union-valued items. P3-15 handles enclosing union
facets; list-own enumeration/pattern/provider semantics remain required work.
All earlier remaining date/IEEE/binary/QName/entity/regex/XML-RPC requirements and
all P4-P9 requirements remain in scope. P3 acceptance is not yet complete.


### P3-16: list-owned union-item facets

P3-15 is committed as c4f3412. List item metadata now describes union-valued items
without an atomic builtin. Schema and provider restrictions capture selected
primitive identities from the actual base conversion, and share capture intervals
through inherited restrictions. Enumeration compares ordered primitive values;
patterns use collapsed original tokens, and count facets apply to item counts.
Generated examples, detached choices and optional providers retain those rules.
Field corruption testing also exposed missing XsdListDataField item metadata
validation on reconstruction; the new hook rejects an inconsistent descriptor.
No item conversion is replayed merely to infer an identity.

The initial six-case regression failed all six cases on the committed baseline.
Final source and compiled AOT regressions pass 10 cases / 245 assertions, including
nested enclosing unions, empty and invalid native boundaries, invalid declarations,
metadata corruption, atomic field updates, schema/provider error cleanup and
provider reentry. All 60 affected XML suites pass: the original final run records
700 cases / 12689 assertions, and the expanded final suite contributes one further
case and 53 assertions, for combined final evidence of 701 cases / 12742 assertions.
The original report remains unchanged; reviewed-checks.json records the update.
The soap suite intentionally exercises three failed assertions internally.

The nine-case independent matrix covers 27 schemas, 54 actual SOAP contracts,
516 input and 204 emitted binding documents, 3184 consumer results and 1520
emitted/example documents. Xerces checks all 2240 documents; libxml2 checks all
except its existing empty-list enumeration compiler defect. Exact selected
primitive families and Decimal values remain mandatory. No new oracle waiver or
upstream fixture change. Final full Python discovery runs 133 methods and records
exactly the same 33 tracked P4/P5/P6 failure signatures as P3-15. Both-version
survey/strict coverage are unchanged outside versions: 89 selected WSDLs / 756
directions, zero selected failures and 220 broad tracked failures.

WSDL/SoapClient/SoapDataProvider AOT and WSDL docs/qjar builds pass without warnings
or errors. No C++ changes and no new Valgrind run needed. Full 62-item audit is
in audits/P3-16-list-union-facets.md. Evidence under /tmp/wsdl-p3-16- includes
reviewed-unit, reviewed-aot-unit, final-checks plus reviewed-checks.json,
final-python plus python-comparison.json, independent-first, final-survey,
final-coverage, aot-final and docs logs/reports. WSDL SHA-256 is
3e3fc3b3c003502c5e8f81b59476360eed49e56283dcf2d17b6eb07ede248d0d;
native XML remains 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.

Next reproducer: /tmp/wsdl-p3-17-builtin-list-{probe.qr,baseline.log} shows that
unions using NMTOKENS/IDREFS/ENTITIES reject whitespace-equivalent enumeration
values A TAB B and SPACE A SPACE SPACE B SPACE while accepting A SPACE B. The
union helper does not describe builtin list identities. Builtin token validation
and their own restriction/provider semantics also need review against the XML
name rules. Remaining primitive/date/IEEE/binary/QName/entity/regex/XML-RPC work
and all P4-P9 requirements remain in scope. P3 acceptance is not complete.


### P3-17: builtin name grammar and list values

P3-16 is committed as 42893c8. Builtin NMTOKENS/IDREFS/ENTITIES now retain
ordered string-item identity in unions, including equivalent native user-defined
lists and distinct atomic strings. Own and inherited enumeration/pattern/count
facets survive provider reconstruction, optionality, field choices and bounded
example generation. Builtin name types and list items validate the XML 1.0
Second Edition productions explicitly referenced by XSD 1.0. The shared Unicode
classes also replace ASCII-only regex name escapes. Detached metadata rejects
contradictory name rules and a builtin list substituted for an atomic list item.

All four initial regression cases fail on P3-16. Final source and compiled AOT
pass nine cases / 765 assertions. All 61 affected XML suites pass 710 cases /
13507 assertions (the SOAP suite intentionally tests three failed assertions
inside passing cases). AOT and docs builds are clean. No C++ changes and no
additional Valgrind required. Main Qore develop remains clean at 3e2f47be0,
with no push, installation or rebuild there.

The independent matrix covers 45 schemas and 90 actual SOAP contracts, 1584
input and 828 emitted binding documents, 9168 consumer results and 5136
provider/example documents. Three further schemas assess 6054 name-character
boundary documents. All 13602 documents are checked by Xerces-J 2.12.2;
libxml2 agrees except for exactly 24 empty builtin-list false positives.
Both 2.12.10 and private 2.15.4 omit the builtin minimum-length constraint in
the schema-validation list path. Qore and Xerces must reject those inputs;
no production verdict is waived. Token grammar does not establish document-level
ID/reference/entity validity; that remains assigned to P5/P7. Numeric ranges,
source SHA and the oracle root cause are documented in
builtin-list-values-evidence.md.

A preliminary full Python run recorded the same 33 tracked failures plus a
worker exit 2 whose captured stderr was omitted from the exception rendering.
The standalone two-method list suite passes with diagnostic capture. The exact
reason for the earlier exit cannot be recovered from that log; it is not used
as final verification. WorkerProcessError now preserves CalledProcessError
compatibility and displays up to 4096 stderr characters, retaining full output
in the exception. A real child-process regression verifies exit status, diagnostic
text, truncation and manifest cleanup; timeout/cancellation behavior is unchanged.
The implementation and tests are kept unchanged during the final full rerun.

Final stable Python discovery runs 139 methods in 495.285 seconds with exactly
33 tracked P4/P5/P6 failure signatures, identical to P3-16, and no worker errors.
Both-version survey and strict coverage match P3-16 outside versions: 89 selected
WSDLs / 756 directions, zero selected failures and 220 broad tracked failures.
No implementation or test file changed during this final full run.

WSDL SHA-256: 6288ad0427058ef8c16776e78428408761caf9faba6edac973d749c9e5e3ec68.
Native XML remains 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.
The full 62-item audit is audits/P3-17-builtin-list-values.md. Evidence is retained
under /tmp/wsdl-p3-17-, including exact-checks, exact-survey/coverage, final-aot-unit,
aot-final, docs-final, independent-final, stable-python and worker-reporting logs.

The next P3 requirement is already reproduced by
/tmp/wsdl-p3-18-class-escapes-{probe.qr,baseline.log} and schema-probe/Xerces reports:
class-contained name/block complements fail compilation; class-contained digit
and word complements use PCRE's ASCII semantics; malformed classes and
non-XSD PCRE constructs are accepted. XSD Appendix F gives the required grammar
and set semantics. These existing regex gaps, remaining date/IEEE/binary/QName/
entity/XML-RPC work and all P4-P9 criteria remain in scope. P3 is not complete.

### P3-18: regex character sets, grammar and bounded samples

P3-17 is committed as aebf117. XSD patterns now use explicit syntax validation
and complete single-character terms for Unicode unions, complements and ranges.
Nested subtraction is parsed and assembled iteratively. Invalid PCRE extensions,
malformed classes and reversed quantifiers fail at schema construction; `.`
excludes CR and LF. Sample counts are bounded before native conversion,
empty atoms do not loop, and bounded character candidates are checked against
intersecting restrictions. The audit found and fixed a new no-pattern sample
regression; types without patterns retain their supplied examples.

The initial six regression cases fail on P3-17. Final source and AOT pass twelve
cases / 988 assertions, including cancellation/recovery and schema/provider
reconstruction. All 62 affected XML suites pass 722 cases / 14495 assertions.
The SOAP suite intentionally checks three failed assertions inside passing cases.
Final AOT and docs builds are clean. No C++ changed and no new Valgrind run is
required. Main Qore develop remains clean at 3e2f47be0; no push or install.

The independent matrix covers 26 definitions, 78 original schemas and 156 actual
SOAP contracts: 1872 input documents, 804 emitted binding documents, 11232
consumer results and 5440 consumer/example documents. Eighteen separately
identified equivalent schemas add 1788 document assessments. Original oracle
verdicts remain visible; 172 original hyphen-subtraction documents are explicitly
unreachable in Xerces, then mandatorily checked through their equivalent schema.
The 32 invalid-schema cases require the precise Qore exception. libxml2 and
Xerces grammar/set defects are source-adjudicated in regex-classes-evidence.md;
fixed libxml2 verdicts are accepted, and no production verdict is waived.

Both-version survey and strict coverage match P3-17 outside version fields:
89 selected WSDLs / 756 directions, zero selected failures and 220 broad tracked
failures. Two intermediate full Python runs were deliberately interrupted for
audit fixes and portable oracle assertions. Final frozen discovery runs 142
methods in 588.793 seconds with exactly the same 33 tracked P4/P5/P6 failure
signatures and no errors. All three new independent methods pass. Implementation
and test hashes remain unchanged throughout that run; the full 62-item audit
has no failed items.

WSDL SHA-256: d64c20533b0a156965bb3e9905f71462f4d00e1c07e6d6fcad40035f3c504fe2.
Native XML remains 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.
Full audit: audits/P3-18-regex-classes.md. Evidence is retained under
/tmp/wsdl-p3-18-, including final-unit-guarded, exact-checks, aot-final-unit,
docs-final, exact-survey/coverage, frozen-hashes and frozen-python.

The next backend-limit reproducer is /tmp/wsdl-p3-19-repetition-probe.qr with
repetition-baseline.log: `a{65536}` and a very large finite maximum fail
PCRE's count limit; `(ab){32768}` fails compiled bytecode size. These are valid
XSD expressions. [PCRE2 limits](https://www.pcre.org/current/doc/html/pcre2limits.html)
and [repetition behavior](https://www.pcre.org/current/doc/html/pcre2pattern.html#SEC17)
explain the backend limits. Grammar translation alone does not close them.
Remaining primitive/date/IEEE/binary/QName/entity/XML-RPC work and all P4-P9
criteria remain in scope; P3 is not complete.

### P3-19: structural repetition counts beyond PCRE compilation limits

P3-18 is committed as 9b7ebe4. The reduced large literal/group and arbitrary
finite-count cases fail on that baseline because of PCRE's count field and
compiled-size limits. WSDL now retains exact decimal bounds in immutable
structural patterns when PCRE compilation cannot represent valid XSD grammar.
Ordinary anchored PCRE strings remain accepted, including old provider metadata.
Source-only reconstruction validates and rebuilds transient nodes. Matching
uses per-call stacks/caches, input-derived width bounds, nullable padding and
explicit character-set operations. Long repeated literals compare bounded UTF-8
segments; grammar parsing indexes Unicode characters once.

The initial eight cases have six schema errors on P3-18. Final source and AOT
pass fourteen cases / 476 assertions. All 63 affected XML suites pass 736 cases
/ 14971 assertions; SOAP intentionally checks three failed assertions within
passing cases. AOT and documentation builds are clean. No C++ changed and no
additional Valgrind is required. Main Qore develop remains clean at 3e2f47be0;
there was nothing further to commit there and no push, installation or rebuild.

The independent matrix defines 48 actual SOAP contracts and 24 original
schemas, with 384 input and 168 emitted binding documents, 2432 consumer result
rows and 1136 accepted provider/example documents. Original overflowing-count
schema rejections remain visible for both validators; 1464 original Xerces
document outcomes are explicitly unreachable. Each receives an additional
mandatory check by both validators through a separately identified schema
with equivalent membership for the asserted domain of at most 16 characters.
The original large literal/group schemas validate normally. No payload bytes,
production outcomes or original fixtures are altered. The direct structural
matrix adds 16764 exhaustive small-language results against Python plus 292
Unicode/class results, covering original and reconstructed objects.

The complete normative argument, exact validator source paths/hashes, bounded
reference proof and preliminary diagnostics are in regex-counts-evidence.md.
The audit fixed trailing-empty split semantics for open counts, large-value
processing overhead, cancellation in the literal fast path and repeated Unicode
prefix scans. Existing 60/90-second SOAP worker deadlines remain unchanged.
The Unicode sample assertion was corrected to expect its valid Greek candidate.
The exploratory Xerces INT_MAX worker exhausted its heap before a verdict;
its exact stack/output is preserved and is not acceptance evidence.

Both-version survey and strict coverage match P3-18 outside version fields:
89 selected WSDLs / 756 directions, zero selected failures and 220 broad tracked
failures. Final frozen Python discovery runs 146 methods in 571.099 seconds
with exactly the same 33 tracked P4/P5/P6 failure signatures, no new failures
and no errors. All four new repetition methods pass. Code and test hashes
remain unchanged throughout the run; the full 62-item audit has no failed items.

WSDL SHA-256: 68535d23496662e516943d479686464b448afee2e3521aebc7df42bff6d24476.
Native XML remains 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.
Evidence prefix: /tmp/wsdl-p3-19-, including frozen-hashes, exact-checks,
aot-unit, aot-frozen, docs-frozen, exact-survey/coverage and frozen-python.
The full checklist is audits/P3-19-regex-counts.md.

A separate existing regex execution limitation is reduced in
/tmp/wsdl-p3-20-backtracking-probe.qr: `(a|aa)+|a+b` must accept 100 `a`
characters followed by `b`, but PCRE reaches its match limit before evaluating
the successful alternative. The other reduced nested-repeat/alternative cases
have the same cause. A copied, unmodified P3-18 module produces byte-identical
results in backtracking-baseline.log, so this is not a P3-19 regression.
This remaining execution-limit requirement is the next P3 increment; it is not
counted as fixed. Primitive/date/IEEE/binary/QName/entity/XML-RPC and all P4-P9
criteria remain in scope. P3 acceptance is not complete.

### P3-20: structural XSD execution without backend backtracking limits

P3-19 is committed as 549a0e3. The existing ordinary-pattern failure is now
fixed: new constraints always retain source and execute structurally. Zero/one
and unbounded closures use Thompson state sets with per-input transition caches.
General counted matching prunes dominated states after meeting the minimum;
count gaps remain preserved before it. Pure closure identities collapse nested
stars/pluses. No numeric bound is expanded into a compiled graph. Legacy
serialized PCRE strings remain readable with their existing backend behavior.

The source regression passes six cases / 348 assertions, including both
conversion directions, detached reconstructed providers, 10,000-character
inputs, invalid suffixes, count holes, cancellation/reuse and synchronized
concurrent calls. All 64 affected XML suites pass 742 cases / 15319 assertions;
SOAP intentionally checks three failed assertions inside passing test cases.
AOT and documentation builds are clean. This XML increment changes no C++.
The independent Qore prerequisite described below has its own Valgrind and
62-item audit. No push, installation or main-checkout build was performed.

The independent execution matrix covers 30 schemas / 60 actual SOAP contracts,
540 binding input and 264 emitted documents, plus 3360 consumer result rows and
1888 accepted provider/example documents. Two exhaustive language methods add
15240 original/reconstructed verdicts against Python over all binary strings
of length zero through six. All four final independent methods pass in 72.313
seconds. The existing four repetition methods pass as well.

libxml2 reports its internal backtracking limit on 48 invalid original binding
documents. The direct private-2.15.4 probe returns the named -6 limit code;
2.12.10 and 2.15.4 share the 10-million saved-state guard. These are unassessed
original libxml2 results. Original Xerces results remain mandatory, and 668
separately identified globally equivalent schema/document jobs must agree in
both validators. No original payload, fixture, validator or limit is modified.
The proof, exact accounting, source hashes and probe are documented in
regex-execution-evidence.md.

P3-19's narrative document counts were corrected after instrumenting actual
jobs: 384 binding inputs, 168 outputs and 1464 bounded-reference documents,
not 512, 224 and 1616. Repeated payload values had been incorrectly counted
as documents. Tests already checked exact job identities; their outcomes and
completeness did not change. The two existing binding/provider methods were
rerun successfully, and the correction is explicit in regex-counts-evidence.md.

Both-version survey and strict coverage match P3-19 outside version fields:
89 selected WSDLs / 756 directions, zero selected failures and 220 broad tracked
failures. Final frozen Python discovery completes 150 methods in 686.339 seconds
with the same 33 tracked P4/P5/P6 failure signatures, zero errors and unchanged
source/test hashes. AOT execution passes the three regex suites (32 cases / 1812
assertions); four direct language methods check 32296 original/reconstructed
verdicts. The full 62-item audit has no failed items and is recorded in
audits/P3-20-regex-execution.md. WSDL SHA-256 is
767dc84affb55d4800155e443d927a078e7dac3ec7269faf64e497b40ec69274.
Native XML remains 8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12.
Evidence prefix: /tmp/wsdl-p3-20-. Primitive/date/IEEE/binary/QName/entity/XML-RPC
work and all P4-P9 criteria remain open; P3 acceptance is not complete.

The IEEE preflight found a separate existing core defect: `q_strtod()` returned
an uninitialized double when its stream sentry reached EOF on empty/whitespace
input. Valgrind traces the undefined read to that local variable. Qore develop
commit **9dab82749** initializes the result to zero and adds a three-case / 322-
assertion regression. Five suites pass across AST/IR/JIT/tiered (116 cases / 3628
assertions); affected Valgrind runs have zero errors and no lost allocations
using the previously authorized PCRE2 interpreter test switch. Its full 62-item
audit is examples/test/qore/vars/audits/empty-float-conversion.md in Qore.
Main Qore is clean after this commit and was not pushed or rebuilt. The isolated
Debug runtime used for final XML verification now has SHA-256
c8b0739f796b93c0f056cbf2a37050d6902de45c3e9361ed3565754ac5549afb.
The existing Valgrind DWARF reader warning remains tracked for P9. This core
prerequisite does not implement XSD float/double lexical or binary32 semantics.

### P3-21: native IEEE conversion prerequisite

P3-20 is committed as c15ff25. The new binary-module convert_xsd_float API
validates complete XSD lexical input and rounds directly to binary32 or binary64.
Its native result is a Qore float, carrying binary32 values exactly. The native
helper is independently testable; WSDL scalar/provider/facet integration is the
next increment and is not counted as fixed by this prerequisite.

The preflight in /tmp/wsdl-p3-21-float-preflight.qr reduces the existing WSDL
errors: float 16777217 remains 16777217, binary32 midpoints are first rounded
to binary64, 1e-50 stays nonzero, 3.5e38 stays finite, and malformed/empty text
reaches permissive Qore conversion. The separate empty-input core defect was
already fixed in 9dab82749; no further Qore changes were needed here.

Finite text uses direct target-precision classic-locale stream extraction under
a saved/restored nearest-rounding environment. Native binary32 conversion uses
at most 31 exact midpoint comparisons against the original value, including
arbitrary-precision numbers and integers above binary64's exact integer range.
It never applies the display rounding heuristic or formats a native value as an
intermediate decimal approximation. Input scans support cooperative cancellation.
The API preserves signed zero, subnormals, infinities and NaN, and rejects complete
invalid lexical strings and unsupported native types before conversion.

The double exponent typo in the published XSD text is resolved by the working
group's recorded decision in W3C R-214 / issue 2206: the integer-significand
exponent interval is -1074 through 971. The implemented native design, rounding
proof and authoritative references are in design/xml-ieee-conversion.md.

The public regression passes five cases / 597 assertions in AST, IR, JIT and
tiered modes (20 cases / 2388 assertions). The native harness passes 1380 checks
over all four standard rounding directions, pre-existing floating-point flags,
classic/comma C++ locales, cancellation and recovery. Three Python methods compare
3144 results with an independent integer-rational oracle: 1248 decimal strings,
816 exact native number/integer inputs and 1080 native binary64 inputs.

The review fixed two test ownership issues: NaN-boxed large integer temporaries
need ValueHolder, and closure completion with detached workers is not a native
thread join. The concurrency test now owns a thread pool with deterministic
teardown. The locale facet uses stack ownership on exceptional exits. Production
overflow handling accepts either standard-library infinity or clamped overflow
reporting. No suppression, delay, timing retry or precision heuristic was added.
Final native C++ and AST/IR Valgrind checks have zero errors and no lost
allocations. Qore runs use -b --enable-debug and the already approved PCRE2
interpreter test control; the existing DWARF reader warning remains tracked in P9.

All 64 existing XML suites pass 742 cases / 15319 assertions; together with the
new public regression this is 65 suites / 747 cases / 15916 assertions. SOAP
intentionally checks three failed assertions within passing cases. Native,
AOT and final documentation builds are clean; the combined compilation unit
also passes syntax compilation. Both-version survey and strict coverage are
unchanged outside version fields: 89 selected WSDLs / 756 directions, zero
selected failures and 220 tracked broad failures. The preceding full Python
150-method / 33 tracked later-phase failure baseline is not relabeled as a new
run; this increment runs its three new methods and both corpus drivers.

The full 62-item audit has 25 Pass, 37 N/A and no failed items in
audits/P3-21-native-ieee.md. Final native XML SHA-256:
e5f15836d1d3b1577d223fcff29fa59ce916192c229cac579eb3343ed3c0ac02.
Debug core remains c8b0739f796b93c0f056cbf2a37050d6902de45c3e9361ed3565754ac5549afb.
Evidence prefix /tmp/wsdl-p3-21- includes reviewed checks/corpus/build-docs,
lifecycle checks, cpp-owned-locale checks, unity syntax and final hashes.
Main Qore remains clean on develop at 9dab82749. Nothing was pushed or installed,
and its shared build was not touched. All remaining P3 and P4-P9 criteria remain
in scope; P3 acceptance is not complete.

## P3-22 — WSDL IEEE builtin scalars and providers

The native prerequisite is committed as `aa3751f`. Main Qore remains clean on
`develop` at `9dab82749`; it has no uncommitted work to include and has not been
pushed. This increment uses the same isolated Debug core and private XML module.
No main-checkout build, runtime installation or C++ change is part of P3-22.

Root cause: WSDL used Qore's permissive binary64 float conversion for both IEEE
builtins and soft providers. The `aa3751f` WSDL source on the current runtime
returns `16777217.0` for binary32 text `16777217`, and accepts `1tail` as `1.0`
in both decoding and providers. `/tmp/wsdl-p3-22-baseline/` records the reduction.
`XsdIeeeLexicalHelper` now invokes the exact native conversion on the original
input and remaps only lexical rejection. `XsdIeeeDataType` validates precision,
requiredness and reconstructed metadata; native lists cannot preconvert input.
String serialization preserves normalized valid text. Native serialization emits
round-trip-safe target values, and decoded results remain native floats.

The integration tests exposed missing `WSMessageHelper` float/double sample
entries. Both now supply a rounded native number rather than an unknown-type
placeholder. The old interop test expected an intermediate native serializer
value and no binary32 overflow; it now checks serialized text and the correct
rounded/overflowed decoded value. No source fixture was changed.

The new Qore suite passes 6 cases / 793 assertions across AST, IR, JIT and tiered,
and against the built AOT WSDL module. All 65 affected Qore suites pass 748 cases /
16,120 assertions. SOAP's three deliberate assertion failures remain contained
inside passing test cases. The focused three-suite matrix passes in all four
execution modes. AOT compilation, Qdx/Doxygen and the documentation example are
clean. This Qore-only increment does not require another Valgrind run; the native
prerequisite's Valgrind evidence and the separately tracked P9 environment warning
ledger remain unchanged.

The seven new Python methods pass. They cover 24 real SOAP 1.1/1.2 contracts,
1,248 input messages (648 valid / 600 invalid), 648 checked binding outputs,
6,848 provider results (3,648 valid outputs including 192 examples / 3,200
rejections), and 12,576 exact rational-reference conversion comparisons.
Both validators assess 5,544 document verdicts. See
[IEEE scalar evidence](ieee-scalars-evidence.md) for the exact matrix and the
source-adjudicated 72 libxml2 false positives for missing exponent digits.
Xerces and an independent complete lexical grammar reject every such input.
The original invalid documents stay in the mandatory test matrix. Private
libxml2 2.15.4 independently reproduces the same defect as lxml's libxml2 2.12.10.

Both-version corpus status is unchanged: 89 selected WSDLs / 756 directions,
zero selected failures and 220 tracked broad failures. The survey differs only
in two existing FloatEnumerationType diagnostic values, now rounded to binary32.
The coverage report changes four corresponding diagnostics and 16 float/double
output bodies. An independent rational check against the original source values
confirms all 16 outputs preserve the required target IEEE values. Every other
non-version field matches P3-21. No failure changed to a skip or an unassessed
success.

Frozen production WSDL SHA-256:
`3e9aa3351b0933110dffa7905f6b9249995ece492b70d980cf0789cdb61f57e8`.
Native XML remains
`e5f15836d1d3b1577d223fcff29fa59ce916192c229cac579eb3343ed3c0ac02`;
Debug core remains
`c8b0739f796b93c0f056cbf2a37050d6902de45c3e9361ed3565754ac5549afb`.
Evidence prefix `/tmp/wsdl-p3-22-`: final-* suite/build/corpus logs,
runtime-hashes.json, corpus-values.json, *-comparison.json, matrix-counts.json
and the original/native-validator reproducers. The full 160-method Python
run completes in 700.836 seconds with exactly the preceding 33 P4/P5/P6 failure
signatures, zero new/removed failures, zero errors and zero warnings. Source and
runtime hashes remain unchanged. The current reports are regenerated from the
same tested outputs. Full [P3-22 audit](audits/P3-22-ieee-scalars.md): 20 Pass,
42 N/A, 0 Fail. This is a tested scalar increment, not full P3 acceptance.

Next: IEEE value-space bounds, enumerations, fixed values, list/union identity
and patterned restrictions. XSD 1.0 requires NaN identity for schema comparisons,
excludes incomparable values from bounds, identifies the two zeros, and keeps
float/double primitive value spaces disjoint in unions. Extend the existing
numeric facet/field framework with explicit partial comparisons rather than
reusing decimal lexical comparisons or adding display-rounding heuristics.
All remaining P3 and P4-P9 requirements remain in scope.

## P3-23 — IEEE facet and composite value identity

P3-22 is committed as `cbc343d`. Main Qore remains clean on develop at
`9dab82749`; the user's commit request is satisfied and nothing is pushed.
No C++ change, installation or main-Qore build belongs to this increment.

The shared numeric facet/field framework now handles float/double target
rounding, explicit NaN partial comparison, enumeration/fixed value identity,
primitive-specific list/union keys and adjacent target examples. Numeric
providers expose `getBuiltinName()` and reject conflicting known builtin
metadata. The enumeration sample path includes float, preserving pattern
spellings such as `001.00e0`. The existing integer-to-float list metadata
negative test remains negative; its inconsistent provider now rejects.

The pre-change reductions are `/tmp/wsdl-p3-23-{preflight,serialize-preflight}.qr`
and their logs. Serialization wrongly admitted values rounding to exclusive
endpoints and rejected ones rounding to inclusive endpoints; decoding admitted
NaN through ordinary bounds. Two audit findings are also fixed: native decimal
fixed values compared through short display strings, and digit-count fixed
facets compared against an unrelated scalar range. Dedicated negative and
positive regressions cover both corrections. Counts now use their own integer
count space, while scalar comparisons use the datatype's value space.

The new Qore suite passes 13 cases / 4,837 assertions. All 66 affected suites
pass 761 cases / 20,957 assertions. SOAP's three intentional assertion failures
remain within successful cases. The focused IEEE/numeric/declaration matrix
passes AST, IR, JIT and tiered modes, and the new suite passes against the AOT
WSDL module. WSDL/SoapDataProvider AOT, Qdx/Doxygen and the executed design
example pass without diagnostics. No new Valgrind run is needed for Qore-only
changes; native/core runtime hashes remain unchanged.

Eight Python methods cover 228 value-processing SOAP contracts plus 40
schema-only binding contracts, 2,844 input messages (1,128 valid / 1,716
invalid), 1,128 outputs, 16,992 provider results and 1,128 adjacent boundary
intervals. Xerces checks 11,640 documents; libxml2 checks 11,480, with 160
unreachable checks for three rejected valid repeated-exclusive schemas.
The original schemas remain unchanged. The IEEE matrix requires precisely
372 libxml2 NaN-ordering false positives; every such document must fail both
Xerces and the independent rational/partial-order predicate. Private libxml2
2.15.4 reproduces the same NaN-as-largest source defect as lxml's 2.12.10.
See [IEEE facet evidence](ieee-facets-evidence.md).

Eight IEEE W3C families now belong to the strict gate, with independent exact
rounding and zero-sign checks shared from `ieee_reference.py`: 97 selected
WSDLs / 828 directions, zero selected failures. There are 24 resolved broad
failures (8 each for Float/DoubleSimpleTypePattern and 4 each for their
EnumerationType families), no new failures, and 196 remaining tracked broad
failures. The final reviewed corpus files are `/tmp/wsdl-p3-23-reviewed-*.json`.
Historical fixtures, findings and adjudication remain unchanged.

Final frozen WSDL SHA-256:
`10a963ad9b69540a40925acaa6ed376ae787b1bbd92b1f62017c443d34000946`.
Native XML remains
`e5f15836d1d3b1577d223fcff29fa59ce916192c229cac579eb3343ed3c0ac02`;
Debug core remains
`c8b0739f796b93c0f056cbf2a37050d6902de45c3e9361ed3565754ac5549afb`.
Evidence prefix `/tmp/wsdl-p3-23-reviewed-` covers final suites, modes, AOT,
documentation and corpus. The full 169-method Python run completed in 822.191
seconds with the preceding 33 P4/P5/P6 failure signatures and one stale strict-gate
count assertion (89/756 instead of 97/828). Production, test and runtime hashes
were unchanged during that run. The assertion now expects the expanded selection
and explicitly checks all eight IEEE families, retaining their historical phase
ownership. The corrected gate passes in 17.591 seconds; the complete affected
coverage test file completes 10 methods in 23.126 seconds with only its two
existing P6 binding-version failures. The combined comparison retains exactly
the previous 33 failure signatures. No production code changed after the full
run. Its other 168 methods retain their recorded results; the run is not described
as wholly passing conformance. There are no errors or new warning diagnostics.
The earlier run intentionally interrupted before the fixed-count correction is
not claimed as completed verification. Evidence retains all original logs under
`/tmp/wsdl-p3-23-final-frozen-*` and the corrected gate under
`/tmp/wsdl-p3-23-reviewed-gate.log`. Current reports use the final reviewed corpus
outputs. Full [P3-23 audit](audits/P3-23-ieee-facets.md): 21 Pass, 41 N/A, 0 Fail.

### Next P3 temporal reductions (read-only)

`/tmp/wsdl-p3-24-temporal-preflight.qr` and its log reduce the next remaining
scalar defects on the current runtime. Zoned date/time serialization drops
timezones; time formatting loses precision after milliseconds and dateTime
conversion truncates beyond microseconds. An absent dateTime zone acquires the
program's zone. A dateTime is wrongly accepted as date, a date as dateTime,
and XSD 1.0 year zero is accepted. Valid hour 24 midnight is rejected. The
five-digit and negative-year failures originate in
`qore_absolute_time::set()` in core `lib/qore_date_private.cpp`: it consumes
exactly four unsigned year digits. Partial gMonth accepts invalid month 13
and timezone +15:00. Empty P/PT durations already reject correctly.

No temporal implementation or representation decision is claimed yet.
Strict temporal grammar/value identity must precede the flexible core parser,
and lexical forms without a lossless native representation need explicit
preservation, consistent with the existing scalar and retained-XML contracts.
Negative-year/calendar semantics, arbitrary years/fractions, timezone partial
order, durations and partial dates require normative and independent checks.
A core extended-year fix, if needed, must be separately tested/audited using
the isolated build and committed to main develop without touching parallel work.
All remaining P3 and P4–P9 acceptance criteria remain in scope.


## P3-24 — Temporal scalar prerequisites (in progress)

P3-23 is committed on XML develop as `039958f`. Its final reference-file whitespace
cleanup was followed by all three native IEEE conversion methods passing, and the
staged diff is clean. Nothing was pushed. Main Qore remains clean on develop at
`9dab82749`; the following prerequisite is being tested in `/tmp/wsdl-core-date`.

The isolated core patch handles separated signed/extended years within the native
integer calendar range, preserving unsigned compact date/time forms. Reductions
also prove negative weekday indexes and 16-bit truncation in `get_years()` and
`date.years()`. Epoch calculation now widens before subtraction/multiplication,
counts negative leap years with floor division, and restores the March-based year
before narrowing. Weekdays use an equivalent positive Gregorian cycle year.
Qore accessors use existing `getInfo()` without changing the legacy C++ ABI.
Negative year formatting writes the sign separately from at least four digits.
The native calendar continues to use astronomical year zero, distinct from XSD 1.0.

The new `examples/test/qore/vars/extended-years.qtest` has seven cases, including
native year limits, compact forms, explicit offsets, malformed input/recovery,
a complete negative Gregorian cycle and full-year accessors. A deterministic
native test requests cancellation before entering the year scanner and then checks
recovery. Initial failing evidence is `/tmp/wsdl-p3-24-core-before.log`.
During calendar review, 2004-12-31 wrongly returned 2005-W01-5 and 2005-01-01
returned 2004-W52-6. The common 53-week rule wrongly excluded Thursday-start
leap years. Both directions are corrected with positive/negative-year regressions;
`/tmp/wsdl-p3-24-iso-week-before.{qr,log}` retains the original reduction.

Source backups for applying only this prerequisite to main Qore are in
`/tmp/wsdl-p3-24-core-base/`. The isolated checkout contains older prerequisite
changes too; they must not be committed wholesale. Its first build passed, but
source refinements followed and final build/tests/Valgrind/audit are still pending.
No P3-24 core or XML acceptance is claimed. WSDL temporal representation, lexical
validation, partial ordering, facet/list/union/provider integration and independent
binding matrices remain to implement before P3 can close.


The first frozen core build passed and its initial suite passed six of seven
cases. Correcting the test's compact-date expectation then exposed a separate
native defect: `QoreString(DateTime*)` writes extended dates into a fixed 15-byte
buffer, and compact negative years omit magnitude padding. A standalone Valgrind
reduction reports six memory errors from that constructor
(`/tmp/wsdl-p3-24-string-overflow-before.log`). The constructor now delegates to
the growing string implementation; both compact concatenation paths preserve the
full signed year. Native tests cover all three paths with literal expected values
and an explicit UTC program context. Final verification has restarted with this
root fix; the earlier failed runs remain preserved, not counted as final passes.
An additive wide ISO-week overload also prevents week-year truncation at the
maximum calendar year. Focused native/QPP Doxygen checks have zero diagnostics.


### P3-24 core prerequisite committed

Qore main `develop` now contains `516e6f434` (extended calendar years and safe date
strings), with a clean working tree and no push. Only the tested eight-file delta
and four new regression/design/audit files were applied; older isolated work and
the shared Qore build were left intact. All seven native/QPP files and both test
sources match the final isolated source hashes exactly.

Final core runtime SHA-256:
`80078ec30d71bc618b7bb40991bad63604303f379c3e47e6dd41d58d0dbc56fd`.
The core matrix passes 92 cases / 76,940 assertions across AST/IR/JIT/tiered and
UTC/Prague, including five affected existing suites. The final runtime passes the
new seven-case / 9,481-assertion suite, its AOT executable, native deterministic
cancellation and all three compact string paths. Valgrind reports zero errors and
zero definitely/indirectly/possibly lost bytes in the new suite, existing date
suite and native helper. The previously tracked DWARF-reader warning remains
visible; these instrumentation runs are not called warning-free. Focused native
and QPP documentation logs are empty; the implemented example runs successfully.
Full Qore audit: 21 Pass, 41 N/A, 0 Fail, committed beside the regression.

All 66 affected XML suites pass (761 cases / 20,957 assertions). The both-version
survey resolves eight decode failures; bidirectional coverage resolves sixteen
Date/DateTime element/attribute decode failures, with zero new failure signatures.
Broad failures fall from 196 to 180. Strict selection is unchanged at 97 WSDLs /
828 directions with zero selected failures. Source/catalog hashes are unchanged.
Typed temporal values are still unassessed outside explicit existing assertions;
these improvements do not complete the XML temporal contract. The new reports and
exact comparison are retained under `/tmp/wsdl-p3-24-core-{survey,coverage}.json`
and `/tmp/wsdl-p3-24-core-report-comparison.json`; committed XML reports still
represent P3-23 until the XML temporal increment is complete.

Remaining P3-24 work is strict temporal grammar and exact value representation,
including missing timezones, arbitrary years/fractions, hour-24 normalization,
calendar partial order, durations, facets/collections/providers and independent
SOAP binding matrices. No XML production temporal change is claimed yet.

### P3-24 XML calendar implementation and verification

The XML increment implements `date`, `gYear`, `gYearMonth`, `gMonthDay`, `gMonth`
and `gDay`. DateTime/time and duration retain their prior production paths and
remain unfinished P3 work. The pending leap-second policy question affects
DateTime/time; elapsed time is not approval. Duration work can proceed independently.

Calendar grammar is anchored ASCII with XML whitespace collapse, Gregorian field
checks, XSD 1.0 year labels and explicit timezone limits. Arbitrary years remain
exact strings. Zoned dates within native year limits decode to native dates with
their original offset; unzoned/out-of-range dates and partial calendars remain
validated strings. This public compatibility change is explicit in WSDL release
notes and `design/wsdl-calendar-values.md`, including an executed example.
Facets, fixed values, provider choices and ordered list/union identity share exact
calendar value semantics and missing-timezone partial ordering. No rounding or
tolerance is used. Native inputs project fields without dropping their offset.

The provider/binding matrix exposed invalid partial-calendar defaults and a date
sample path that bypassed pattern validation. Both root causes are fixed; every
sample is checked against its complete restriction chain. Provider metadata,
optional/reconstructed types, repeated choices, malformed inputs and deterministic
cancellation/recovery have targeted regressions. Real local HTTP tests cover
SoapClient/SoapHandler, actual SOAP 1.1 and 1.2 bindings, original/reconstructed
schemas, all six types, required attributes, ordered lists/unions, arbitrary years
and failed-request recovery with bounded queues and cleanup.

Requirement ownership remains P3 in the plan's original-family register.
`test_calendar_values.py` covers atomic elements, attributed simple content,
repeated elements, lists, unions, detached providers and generated examples in
both directions. Its independent reference uses arbitrary-precision ordinal-day
arithmetic, distinct from production's normalized tuples and year suffix carry.
The 1,838-row seeded boundary worker includes native year limits, 1,000-digit
years, complete positive/negative Gregorian cycles, timezone boundaries and exact
facets. `calendar-values-evidence.md` maps requirements and root causes to primary
specifications and pinned independent validators. The exact 133 scalar diagnostic
triples preserve 126 libxml2 ordering defects, six old-libxml2 whitespace defects
(fixed in private 2.15.4), and one obsolete Xerces gMonth spelling. No upstream
fixture or historical finding was changed; unexpected oracle differences fail.

Completed gates on the frozen final runtime:

- All 69 affected Qore suites pass: 780 cases / 26,409 assertions. Evidence:
  `/tmp/wsdl-p3-24-calendar-final-suites.log` and per-suite logs. The final test
  diagnostic-label correction was then checked in all modes and compiled modules.
- The three new suites pass 19 cases / 5,451 assertions in each AST/IR/JIT/tiered
  mode under UTC and Europe/Prague: 152 cases / 43,608 assertions total. Evidence:
  `/tmp/wsdl-p3-24-calendar-modes-final.log` and `calendar-modes.json` with the
  same `/tmp/wsdl-p3-24-` prefix. Compiled-module runs pass another 19 / 5,451;
  the documented example also executes successfully.
- All nine new Python methods pass in 260.063 seconds; the exact 1,838-row
  boundary matrix and both binding/consumer directions pass. Logs are
  `/tmp/wsdl-p3-24-calendar-python-final.log` and boundary evidence described above.
- WSDL, SoapDataProvider, SoapClient and SoapHandler compiled-module targets and
  WSDL Qdx/Doxygen documentation pass with zero diagnostics. No XML C++ changes
  require another Valgrind run; the prerequisite's separate native evidence remains
  recorded above, including its known DWARF-reader warning.
- Both-version survey: parse 276/17, decode 1,012/102 and serialize 1,010/2
  success/failure. Input validation reports 1,026 valid / 106 rejected / 4
  unassessed; outputs report 964 valid / 46 rejected and eight valid-input,
  invalid-output cases. These remain diagnostic failures, not conformance passes.
- Strict selection expands from 97 WSDLs / 828 directions to 114 / 1,100 with
  zero selected failures and exact calendar/attribute value checks. Broad coverage
  resolves twelve failures against the core prerequisite baseline (180 to 168),
  with zero added failure signatures and unchanged source/catalog hashes. Eight
  DateSimpleTypePattern decode failures and four GMonthAttribute invalid-input
  acceptances are resolved. Combined with the core prerequisite, 28 failures are
  resolved against committed P3-23. The new reports are now the current checked-in
  reports; original findings remain intact.

The full 179-method Python discovery ran against frozen production and test
sources. Its completed comparison and commit gate are recorded below.

### Next P3 duration root causes (independent investigation)

The existing duration regex admits `P1DT`, contrary to XSD 1.0 §3.2.6.1's required
component after `T`. Native serialization omits microseconds, emits embedded
negative fields (`P-1D`), and accepts absolute dates as durations. Nonstring
deserialization falls through to unrestricted string conversion. A relative date
with one day and minus one hour is representable as `PT23H`; opposing month and
second groups have no XSD duration representation without an external reference
date. Combining native whole seconds separately from microseconds avoids overflow
at the native 32-bit day boundary. Initial reductions are preserved in
`/tmp/wsdl-p3-25-duration-before.log` and `duration-native-probe.log` with the same
prefix. The scratch lexical conversion experiment is outside repository source;
it is not counted as implemented or accepted work.

Duration lexical/native/provider validation is the next independently testable
increment. Duration bounds, value equality, choices, list/union identity and
sample construction remain in P3 and require the four reference dates in XSD 1.0
§3.2.6.2 and Appendix E. Direct comparison of source strings or approximate seconds
cannot implement that partial ordering. Current independent reductions show
libxml2's `xmlSchemaCompareDurations()` ignores Gregorian 100/400-year exceptions;
both tested versions reject `P400Y` versus enumerated `P146097D`, while Xerces
accepts. Both validators also accept `PT.5S`, contrary to XSD 1.0's digit-before-
and-after-decimal grammar; libxml2 accepts `PT1.S` too. Private 2.15.4 fixes the
old duration-whitespace defect. Normative grammar remains authoritative. Sources:
[XSD 1.0 duration](https://www.w3.org/TR/xmlschema-2/#duration),
[Appendix E](https://www.w3.org/TR/xmlschema-2/#adding-durations-to-dateTimes),
[the later fractional-grammar discrepancy report](https://lists.w3.org/Archives/Public/www-xml-schema-comments/2023JulSep/0000.html).
These findings are explicitly retained for the following duration work, not
silently deferred to a later phase or counted as passing calendar requirements.

During the final XML gate, parallel development rebased main Qore develop. The
calendar prerequisite is now `db964e98f` (formerly `516e6f434`). A scoped diff
confirms all seven native/QPP files and both regression sources are unchanged;
main develop remains clean and eight commits ahead. This XML task performed no
pull, shared rebuild, installation or push. Its isolated tested runtime is frozen.

### P3-24 final XML commit gate

Full Python discovery ran **179 methods in 1,118.493 seconds**, retaining exactly
**33 previously tracked P4/P5/P6 failure signatures**, with **zero new signatures,
zero removed signatures and zero errors**. These known later-phase checks remain
failing tests. There are no current-increment failures or warning diagnostics.
Evidence: `/tmp/wsdl-p3-24-calendar-python-all.log` and the exact comparison in
`/tmp/wsdl-p3-24-calendar-python-comparison.json`. All production and test files
match the hashes frozen before this run; subsequent changes are execution/audit
records and the updated core commit reference in validator evidence.

The full 62-item audit is complete: **21 Pass, 41 N/A, 0 Fail**, with every item
and supporting evidence in `audits/P3-24-calendar-values.md`. The final diff is
limited to the six calendar primitives and their tests, providers, reports,
selection and documentation. Source/runtime/compiled-module hashes are retained
in `/tmp/wsdl-p3-24-calendar-final-hashes.json`. WSDL source SHA-256 is
`de49bcecea41c030e8d7cde079b141df591f342e3ee12f1132d93776b070d87a`;
its compiled module SHA-256 is
`628b0ac7180d543823f7b9a4e48b6ec5a7368bae041ad7f67589085684ac3a28`.
The native runtime and XML module match the separately recorded tested hashes.
This completes the calendar increment, not P3 or final interoperability acceptance.

Further duration reductions in `/tmp/wsdl-p3-25-duration-facet-oracles.json` show
both validators round distinct decimal seconds into equal binary values, including
`PT1.00000000000000001S` and `PT1.00000000000000002S`, and underflow sufficiently
small fractions to zero. Xerces stores seconds as `double` in `DurationDV`; libxml2
also stores/computes duration seconds as `double`. Exact duration facet work must
preserve these distinctions. The separate rational four-anchor scratch reference
confirms the prescribed comparison and Gregorian-cycle aliases; none of this
scratch duration code is included in the calendar commit.

## P3-25 — Strict duration lexical/native conversion

P3-24 calendar values are committed on XML develop as `9f6e735`; no push occurred.
This increment addresses duration lexical/native conversion and validated scalar
providers. Exact duration bounds, enumeration/fixed/choice identity, derived
provider facets and collection value identity remain the next P3 increment.
DateTime/time work still awaits the unresolved leap-second policy question.
P4–P9 remain in scope and have not begun implementation.

The original duration regex accepted `P1DT`. Native serialization omitted
microseconds, emitted embedded negative component signs and accepted absolute
dates. Deserialization coerced unrelated categories to strings; generic soft-string
providers bypassed duration grammar. The new helper uses complete ASCII grammar
and retains XML lexical text without bounded numeric conversion. Native relative
dates normalize month and whole-second groups separately, preserve microseconds
and reject opposing group signs. The output remains a string. Keeping microseconds
separate prevents 64-bit overflow at the native 32-bit day limit. No core C++ change,
rounding heuristic, lexical cap or fixture-specific behavior is added.

`XsdDurationDataType` retains requiredness and strict conversion through optional
copies, serialization and enclosing providers. Audit exposed one missing identity
branch: the new provider could be accepted as a numeric/calendar base in public
metadata. A failing negative regression reproduced that omission; the shared
known-provider check now rejects it, including list item metadata. Reconstruction
validates optionality before assignment. Interruption retains its category and
provider/list conversion recovers without partial state.

Requirement ownership remains P3 lexical/native duration handling. New tests:

- `wsdl-duration-values.qtest`: eight cases / 869 assertions, covering grammar,
  empty/malformed/Unicode/category negatives, whitespace, signs, microseconds,
  every native year/day limit, 1,000-digit components/fractions, metadata,
  optional/reconstructed providers, basic lists/unions and cancellation/recovery.
- `wsdl-duration-consumers.qtest`: one case / 20 assertions through local HTTP,
  actual SOAP 1.1/1.2 bindings and original/reconstructed WebService instances.
  Requests/responses preserve native and arbitrary-precision durations, required
  attributes, basic lists and union alternatives. Invalid requests reject before
  a following valid request succeeds; queue/I/O deadlines and cleanup are bounded.
- `test_duration_values.py`: all three methods pass. Atomic elements, attributed
  simple content and repeated values use independent integer-month/rational-second
  assertions in both binding versions and directions, detached providers and
  generated examples. Component preservation here is not substituted for XSD's
  four-anchor duration identity/ordering.

`duration-validator-defects.json` and `duration-values-evidence.md` retain exact
normative/source evidence for three lexical oracle discrepancies. Both libxml2
versions and Xerces accept `PT.5S`; libxml2 also accepts `PT1.S`, contrary to XSD
1.0 Second Edition's digit-before/after rule. libxml2 2.12.10 handles leading but
not trailing duration whitespace; private 2.15.4 fixes the component-loop tail.
The binding matrix requires exactly 36 incorrect libxml2 and 12 incorrect Xerces
verdicts; generated/reconstructed outputs have zero disagreements. All native
2.15.4 scalar reproductions match the fixture and stderr is empty. Original W3C
fixtures and historical findings are unchanged.

The final affected suite rerun after the metadata audit fix passes **71 Qore suites,
789 cases / 27,298 assertions**, including WSDL interoperability and all required
SOAP consumers. The affected Python run executes **29 methods in 36.468 seconds**
and retains exactly the two previously tracked P6 selected-binding-version failure
signatures, with no new failures or errors. Its source/test set is frozen. This
increment uses the affected Python subset; the immediately preceding calendar
increment's 179-method discovery is separately recorded above and is not claimed
as a run of these new duration changes. Evidence:
`/tmp/wsdl-p3-25-duration-final-suites.log`,
`/tmp/wsdl-p3-25-duration-python-affected-final.log` and
`/tmp/wsdl-p3-25-duration-python-comparison.json`.

The final both-version survey and strict coverage retain exactly the previous
counts and failure signatures: 168 broad failures, zero selected failures,
114 selected WSDLs / 1,100 directions, and unchanged corpus/catalog hashes.
The survey remains at 102 decode failures, two serialization failures and 46
invalid outputs, including eight valid-input/invalid-output cases. These remain
visible diagnostics assigned to unfinished work. Current reports now record the
final duration source hash. Full duration corpus value promotion remains tied to
its following exact-facet/identity increment.

WSDL/SoapDataProvider/SoapClient/SoapHandler compiled modules and WSDL Qdx/Doxygen
rebuild without warnings/errors. No native change requires Valgrind. The final
mode/zone, compiled-module/example results, complete audit and source hashes are
recorded below before committing. Initial failing reductions and audit reproduction
remain under `/tmp/wsdl-p3-25-duration-*before.log`.

### P3-25 final commit gate

The final new suites pass in AST/IR/JIT/tiered under UTC and Europe/Prague:
**72 cases / 7,112 assertions across eight combinations**. Compiled-module runs
pass another **nine cases / 889 assertions**, and the implemented design example
runs without output. Logs: `/tmp/wsdl-p3-25-duration-modes-final.log` and
`/tmp/wsdl-p3-25-duration-aot-final.log`, with their adjacent JSON summaries.
The complete 62-item audit is **20 Pass, 42 N/A, 0 Fail** in
`audits/P3-25-duration-values.md`. No source or test changed after final verification;
only the execution/audit records were completed. All intended file and runtime/qmod
hashes are retained in `/tmp/wsdl-p3-25-duration-final-hashes.json`.

This completes the independently tested lexical/native duration increment.
P3-26 must implement exact four-anchor duration relations, bounds and declarations,
enumeration/fixed/finite choices, list/union identity, derived provider metadata and
valid sample construction before duration acceptance can close. The exact
fraction/400-year oracle defects and reference experiment recorded above remain
part of that work. No P3 completion or final interoperability acceptance is claimed.

## P3-26 — Exact duration facets and composite identity

P3-25 is committed as `d8da402`. P3-26 completes its following exact duration
relation, four bounds/declarations, enumeration/fixed/finite-choice identity,
list/union semantics, derived providers and validated samples. Main Qore was clean
on `develop` at resumption, with the separately committed calendar prerequisite
at `db964e98f`; no main-repository work, installation or push was performed here.

Root cause: generic duration restrictions coerced values for numeric comparisons,
used authored strings for equality, and lost constraints in detached providers.
The implementation now uses XSD 1.0 §3.2.6.2/Appendix E reference-date addition.
Signed decimal limbs, Euclidean 400-year cycles and exact fractional strings avoid
native range limits and binary rounding. The four reference results distinguish
incomparable month/day values and identify 400-year Gregorian aliases. This is
normative value comparison; Qore's display-rounding heuristic is not applied.

`XsdDurationRestrictionDataType` retains inherited lexical patterns, exact bounds,
enumerations and optionality. Construction rejects contradictory, weakened or
changed fixed bounds and incompatible builtin metadata. Repeated inherited
exclusive endpoints follow the XSD declaration rule. `XsdDurationDataField`, fixed
attributes, list facets and union identities share exact four-reference-date keys.
Finite choices validate replacements before changing state. Sample construction
uses one decimal place finer than all endpoints and bounded nearby month/second
candidates, including anchor-relative seconds for negative month endpoints. Every
candidate passes all inherited constraints; unsuccessful search raises the existing
explicit sample-generation error.

The independent reference uses Python integers and Fraction arithmetic rather than
the production limb/cycle calculation. The **1,376-row** boundary matrix passes
wire encoding/decoding, reconstructed providers, all four bounds and enumeration,
including arbitrary magnitudes, tiny signed fractions, zero/century transitions
and seeded mixed-component aliases. Actual SOAP 1.1/1.2 WSDL binding tests cover
both directions, scalar/record/repeated values, detached element/message providers
and examples. Local HTTP SoapClient/SoapHandler tests carry restricted/fixed/list/
union durations in requests and responses, with invalid-request recovery.

The pinned validator fixture records **16 exact triples in 11 groups**: eight
fractional-second defects in both libxml2 and Xerces, and eight Gregorian duration
comparison defects in both libxml2 versions. Private libxml2 2.15.4 reproduces all
16 with empty diagnostic stderr. Production keeps the normative verdicts, including
the valid generated value `PT1.000000000000000009S` below the exclusive
`PT1.00000000000000001S` bound. Sources, complete fixture and reproducer commands
are in `duration-facets-evidence.md`; original corpus bytes are unchanged.

### P3-26 verification and commit gate

- All **72 affected Qore suites, 800 cases and 29,678 assertions** complete
  successfully, with no warnings or test-case errors. The existing soap suite's
  summary retains its baseline assertion accounting (1,031 total / 1,028 succeeded,
  all 20 cases successful); no new test failure is hidden by that accounting.
  Log: `/tmp/wsdl-p3-26-duration-final-suites.log`, with per-suite logs.
- The three duration suites pass **20 cases / 3,269 assertions** per mode/zone,
  **160 cases / 26,152 assertions** over AST/IR/JIT/tiered × UTC/Europe-Prague.
  `/tmp/wsdl-p3-26-duration-modes.log` and adjacent JSON retain every result.
- Local compiled modules pass another **20 cases / 3,269 assertions**; the expanded
  design example executes with no output. WSDL/SoapDataProvider/SoapClient/SoapHandler
  qmods and WSDL Qdx/Doxygen build without warnings/errors. Logs:
  `/tmp/wsdl-p3-26-duration-aot.log` and
  `/tmp/wsdl-p3-26-duration-build-docs-final.log`.
- The affected Python run executes **34 methods in 119.111 seconds**, retaining
  exactly the two known P6 selected-binding-version failures, with no new failures,
  errors or warnings. All new methods pass. The final import/format cleanup is
  rechecked by the three-method reference/coverage unit run in **22.205 seconds**.
  Logs: `/tmp/wsdl-p3-26-python-affected.log`,
  `/tmp/wsdl-p3-26-duration-final-reference.log` and
  `/tmp/wsdl-p3-26-duration-python-comparison.json`. This is an affected subset,
  not a new full Python discovery run; the prior full-run baseline remains above.
- Both-version survey counts and all **168** broad coverage failure signatures
  are unchanged. The strict gate adds DurationElement/DurationAttribute with
  independent value assertions and passes **116 WSDLs / 1,120 message directions**
  with **zero selected failures**. `/tmp/wsdl-p3-26-duration-report-comparison.json`
  records empty added/removed failure sets. Current reports retain all wider
  diagnostics, including 102 decoding failures, two serialization failures,
  46 invalid outputs and eight valid-input/invalid-output examples.
- The full audit is **21 Pass, 41 N/A, 0 Fail** in
  `audits/P3-26-duration-facets.md`. No C++ changed, so Valgrind is not required.
  All intended source/report/audit and built-artifact hashes are captured in
  `/tmp/wsdl-p3-26-duration-final-hashes.json` before commit. The frozen Debug core
  SHA256 remains `80078ec30d71bc618b7bb40991bad63604303f379c3e47e6dd41d58d0dbc56fd`;
  the unchanged native XML qmod SHA256 is
  `ea937cab716ed204aef3d3d90f0af17ee1930d9650ef7a6f3fceffbcfcac54fc`.

P3 remains active. The leap-second compatibility decision for dateTime/time is
still awaiting the previously requested explicit policy answer; no answer or
approval has been inferred. Continue independent P3 binary/QName/entity/XML-RPC
requirements while that decision is pending. All P4-P9 ownership and acceptance
criteria remain open; this increment is not final interoperability acceptance.

## P3-27 — Strict binary lexical/native conversion

P3-26 is committed as `6218d07`. Main Qore is clean on `develop`, eight commits
ahead of origin; the latest request to commit uncommitted main-repository work
requires no further commit. No Qore files, shared build, installation or push are
part of this increment. The isolated calendar-prerequisite runtime stays frozen.

Binary reductions exposed permissive base64 padding/unused-bit acceptance,
rejection of valid whitespace between padding characters, coercion of empty
unrelated native categories to empty octets, and raw-string whitespace loss before
serialization. `XsdBinaryLexicalHelper` now validates complete XSD hex/base64
grammar, converts encoded characters to ASCII before native decoding, and keeps
raw serializer string bytes intact. `XsdBinaryDataType` retains encoded-text
validation, requiredness and binary output through optionality, reconstruction
and enclosing providers. Required omission and present empty content stay distinct.

The fixed input contract is documented in `design/wsdl-binary-values.md`: serializer
strings are raw bytes; decoder/provider strings are encoded XML text. Both native
and string representations preserve bytes without rounding or normalization of
raw data. Full binary facet/finite-choice and collection identity acceptance is
the following P3 increment, not a completed criterion here.

All **74 affected Qore suites, 810 cases / 30,683 assertions** pass, with no new
warnings or test-case errors. The soap suite retains its separately documented
baseline assertion accounting. New binary suites contribute **10 cases / 1,005
assertions**, including native categories, every final base64 pad-bit alternative,
all 256 octets, 64 KiB values, UTF-16 encoded XML text, raw UTF-8/UTF-16/ISO-8859-1
bytes, metadata rejection, list/union fallback, interruption/reuse, and real HTTP
requests/responses through original and reconstructed SOAP 1.1/1.2 bindings.
Log: `/tmp/wsdl-p3-27-binary-final-suites.log` and adjacent per-suite logs.

The two new suites also pass **80 cases / 8,040 assertions** across AST/IR/JIT/
tiered × UTC/Europe-Prague, and another **10 / 1,005** using local compiled
modules. The design example runs with no output. WSDL/SoapDataProvider/SoapClient/
SoapHandler qmods and WSDL Qdx/Doxygen rebuild without warnings/errors.
Evidence: `/tmp/wsdl-p3-27-binary-modes.log`, `binary-aot.log` and
`binary-build-docs.log` under the same `/tmp/wsdl-p3-27-` prefix.

The three new Python methods pass in **26.923 seconds**. Exact Python byte
decoding/re-encoding, Xerces and both libxml2 versions retain the three precise
MIME-tolerance discrepancies in `binary-validator-defects.json`. The input matrix
requires exactly 36 libxml2 false positives and zero Xerces disagreements;
all generated/reconstructed outputs validate. Native private 2.15.4 reproduces
the same three verdicts with empty stderr. Root causes and normative sources are
in `binary-values-evidence.md`; no Qore verdict is waived. The larger affected
Python regression set and final audit are recorded below when complete.

Both-version survey counts and all **168 broad failure signatures** are unchanged.
Strict coverage remains **116 WSDLs / 1,120 directions**, zero selected failures;
current reports now carry WSDL source SHA256
`97e23ea13f0eec165955786dd6185fdd4297da22684ef57641cca1b5ab98e843`.
`/tmp/wsdl-p3-27-binary-report-comparison.json` records empty added/removed sets,
unchanged original corpus/catalog hashes and preserved broader diagnostics.

Following binary reductions are retained in
`/tmp/wsdl-p3-28-binary-facet-baseline.log`: binary enumerations compare a native
binary to authored text, pattern paths call unsupported `string(binary)`, and
unrestricted detached providers lose those facets. P3-28 owns lexical retention,
byte identity, inherited restrictions, fields/fixed values, lists/unions and
checked samples. The leap-second policy question remains unanswered; no approval
is inferred and dateTime/time behavior is unchanged. P4-P9 remain open.

### P3-27 final commit gate

The affected Python set completes **40 methods in 284.852 seconds**, with exactly
the two known P6 selected-binding-version failure signatures and no new failures,
errors or warnings. All new binary and affected size/list/union methods pass.
Evidence: `/tmp/wsdl-p3-27-binary-python-affected.log` and
`binary-python-comparison.json` under the same prefix. This is the affected
subset; the prior full-discovery baseline is not claimed as a current run.

The full 62-item audit is **20 Pass, 42 N/A, 0 Fail**, recorded in
`audits/P3-27-binary-values.md`. No implementation/test files changed after final
verification. The complete intended file and built-artifact hashes are retained
in `/tmp/wsdl-p3-27-binary-final-hashes.json` before commit. The frozen Debug
core and native XML qmod match the previously recorded tested hashes; there are
no C++ changes requiring Valgrind. This completes the independently testable
lexical/native binary increment; remaining binary restrictions and all other
open P3-P9 criteria stay in scope.

## P3-28 — Binary restrictions and retained lexical values

P3-27 is committed as `17b6e75`. The binary restriction increment is complete; its commit gate is recorded below. Root causes and normative evidence are in `binary-values-evidence.md`.
It separates encoded lexical patterns from octet lengths/enumerations/fixed values,
adds immutable `XsdBinaryValue` and validating reconstructed restriction providers,
and preserves exact finite choices, list items and selected union identities.

Independent testing found and corrected three additional defects during this
increment: pattern samples could end in an incomplete encoding unit; union samples
replaced a selected binary carrier with a raw string; and union patterns used
unnormalized input rather than the selected leaf member's whitespace policy.
The initial outer-whitespace carrier interpretation was wrong. Both validators
reject a binary union pattern requiring surrounding spaces, because its member
collapses those spaces first. Carriers now retain normalized text. The generic
union fix propagates leaf normalization through nested schemas/providers, including
string, normalizedString, token, numeric and list members. Two earlier Qore-only
list-union tests were corrected accordingly; no validator discrepancy is waived.

Audit made the union binary input boundary explicit: union strings retain XML
lexical values, whereas atomic binary serializers retain their raw-byte convention.
An attempted extension of the atomic convention to unions broke the existing HTTP
string fallback `AB==`; the final change validates encoded union text before
invoking a binary member serializer. Native binary inputs remain octets. Binary
carriers work inside union-item lists, and union metadata includes their object
output alternative. Final unit, HTTP, reconstructed-provider, independent matrix,
modes/AOT, docs/build, corpus and 62-item audit results follow at completion.

Development evidence uses `/tmp/wsdl-p3-28-binary-*`. The first six-method facet
matrix after leaf normalization passed in 136.530 seconds; the seven-method union
whitespace set, including the selected token/numeric/list matrix, passed in 44.193
seconds. Subsequent union-input and metadata audit fixes require affected reruns;
these development results are not claimed as the exact final commit gate.

The initial corpus promotion passed 120 WSDLs / 1,148 directions with zero selected
failures and the same 168 broad failure signatures. Original corpus/catalog hashes
and survey counts were unchanged. Final reports must carry the final WSDL source
hash before commit. Main Qore was verified clean on develop (ahead nine); no shared
checkout edits or pushes occurred. The unanswered leap-second policy question
remains pending, and dateTime/time behavior is unchanged. P4-P9 remain open.

### P3-28 final Qore, build and corpus gates

The final implementation passes **75 Qore suites, 822 cases / 31,220 assertions**.
The existing soap suite retains its documented 1,031 total / 1,028 succeeded
assertion accounting, with all 20 cases passing. No new warning or test-case error
occurs. Evidence: `/tmp/wsdl-p3-28-binary-complete-suites.log` and adjacent
`binary-complete-<suite>.log` files under the same prefix. Binary values/facets/HTTP
contribute **21 cases / 1,441 assertions** (987 + 362 + 92).

All six affected suites (the three binary suites and union whitespace/list identity/
union-item lists) pass **384 cases / 17,216 assertions** over AST/IR/JIT/tiered ×
UTC/Europe-Prague, and **48 cases / 2,152 assertions** using local compiled modules.
The complete binary design example executes with no output. Qmods for WSDL,
SoapDataProvider, SoapClient and SoapHandler, plus WSDL Qdx/Doxygen, build without
warnings/errors. Evidence: `/tmp/wsdl-p3-28-binary-modes-complete.log`,
`binary-modes.json`, `binary-aot-complete.log`, `binary-aot.json` and
`binary-build-docs-complete.log` under the same prefix.

The both-version survey counts and every **168 broad diagnostic failure signature**
remain unchanged. Strict selection adds HexBinaryElement/Attribute and
Base64BinaryElement/Attribute, now **120 WSDLs / 1,148 message directions**, zero
selected failures. Every original corpus and catalog hash is unchanged. Current
reports carry final WSDL SHA256
`7f041223c5499298218116d3c74a58a8c5ddf8f461f7b0b0b10978877972353f`.
Evidence: `/tmp/wsdl-p3-28-binary-report-comparison.json` and the
`binary-survey-complete` / `binary-coverage-complete` logs and JSON reports.

The frozen Debug core SHA256 remains
`80078ec30d71bc618b7bb40991bad63604303f379c3e47e6dd41d58d0dbc56fd`;
the native XML qmod remains
`ea937cab716ed204aef3d3d90f0af17ee1930d9650ef7a6f3fceffbcfcac54fc`.
No native code changed. The final Python regression and complete audit follow.


### P3-28 final Python and audit gate

The exact final source passes the affected **58-method** Python run in **602.796
seconds**, retaining exactly the two known P6 selected-binding-version failures.
All new binary facet/list/union methods and selected union whitespace methods pass;
there are no new failures, errors or warnings. Exact signatures and empty
added/removed sets are in `/tmp/wsdl-p3-28-binary-python-comparison.json`; full log:
`/tmp/wsdl-p3-28-binary-python-complete.log`. The earlier 58-method gate took
647.592 seconds with the same two signatures; only the later run is claimed as
verification of the final source. Original corpus, historical findings and
validator defect classifications were preserved.

The full 62-item audit is **21 Pass, 41 N/A, 0 Fail**, recorded in
`audits/P3-28-binary-facets.md`. Audit findings were corrected and affected checks
rerun. `/tmp/wsdl-p3-28-binary-verify-gate.py` verifies unchanged final code/test
hashes, Qore totals, clean build/mode/AOT diagnostics and exact Python signatures.
The final intended-file and artifact hashes are retained in
`/tmp/wsdl-p3-28-binary-final-hashes.json` before commit. All implementation inputs
match the verified WSDL SHA above. No push is authorized or performed.

This completes the binary facet/choice/collection increment. QName/entity context,
dateTime/time policy and remaining XML-RPC/P3 criteria remain in scope; P4-P9
have not begun. Read-only next-name reductions are in
`/tmp/wsdl-p3-29-name-preflight.qr`, `.log` and `.md`; they do not modify this commit.

## P3-29 — QName lexical grammar, provider patterns and examples

P3-28 is committed as `494633c`. This increment completes QName lexical checking
without claiming namespace-context or enumeration-value acceptance. Root causes,
normative references and independent reproductions are in
[qname-lexical-evidence.md](qname-lexical-evidence.md); the implemented contract
and executable example are in [the design](../../design/wsdl-qname-lexical.md).

| Requirement | Implementation and evidence |
| --- | --- |
| P3-QName-grammar | Both NCName components follow the referenced XML 1.0 Second Edition productions; builtin serialization/decoding and reconstructed providers reject malformed and empty text with the expected categories. |
| P3-QName-lexical-facets | XML whitespace collapse precedes inherited patterns; detached providers retain those patterns. Deprecated QName lengths impose no value-length constraint. |
| P3-QName-examples | Builtin examples are local names; restricted examples pass complete scalar validation or raise XSD-SAMPLE-ERROR. Malformed enumeration spellings fail schema construction. |
| P3-QName-boundaries | 4,036 independently generated character boundaries pass libxml2 2.12.10, Xerces-J 2.12.2 and all three Qore conversion paths, also with PCRE2 JIT disabled. |
| P3-QName-consumers | 42 actual SOAP contracts / 612 input messages cover both versions and directions, atomic/attribute/simple-content/repeated values, providers and examples. The 216 accepted inputs preserve checked namespace/local identity. Seven schema-only cases cover malformed names and equivalent local aliases. |

The new Qore suites pass **8 cases / 335 assertions**: lexical 7/307 and actual
HTTP consumers 1/28. The frozen-source regression gate passes **77 Qore suites,
830 cases / 31,555 assertions**, including the existing schema/SOAP/XML-RPC/CDA/
Cargo consumers. The soap suite retains its documented 1,031 total / 1,028
succeeded assertion accounting, with all 20 cases passing. No new warnings or
test-case errors occur. Logs: `/tmp/wsdl-p3-29-qname-final.log` and its adjacent
`qname-final-<suite>.log` files.

The two QName suites plus existing builtin-name/list suite pass **136 cases /
8,800 assertions** across AST/IR/JIT/tiered and UTC/Europe-Prague. Local compiled
modules pass **17 cases / 1,100 assertions**, and the full design example runs
with no output. WSDL, SoapDataProvider, SoapClient and SoapHandler qmods and WSDL
Qdx/Doxygen build cleanly. Evidence: `/tmp/wsdl-p3-29-qname-modes.json`,
`qname-aot.json`, `qname-build-final.log` and `qname-no-jit.log` under that prefix.

The four-method standalone QName matrix passes in **58.417 seconds**. The final
affected Python gate completes **52 methods in 427.691 seconds**, with exactly
the two known P6 selected-binding-version failures and no new failures, errors or
warnings. Logs: `/tmp/wsdl-p3-29-qname-python-final.log` and
`qname-python-gate.log`; exact baseline comparison: `qname-python-comparison.json`.
An initial enum check could reject equivalent namespace aliases; the audit
replaced it with the intended lexical-only check and added independent regressions.
The initial overlapping development save/read error in schema-composition is
superseded by the complete frozen-source rerun above.

The comparable both-version survey retains every prior count and source/catalog
hash. Strict coverage remains **120 WSDLs / 1,148 message directions**, zero
selected failures; all **168 broad failure signatures** are unchanged. QName
output-namespace and entity-context failures remain visible. Reports:
`/tmp/wsdl-p3-29-qname-survey-final.json`, `qname-coverage.json` and
`qname-report-comparison.json` under that prefix. An additional survey with the
offline catalog (`qname-survey.json`) resolves three imports absent from the
legacy survey's default configuration; its changed stage counts are configuration
coverage, not QName fixes. The strict coverage gate always uses that pinned catalog.

The full 62-item audit is **20 Pass, 42 N/A, 0 Fail**, recorded in
[P3-29-qname-lexical.md](audits/P3-29-qname-lexical.md). Frozen WSDL SHA256:
`5e3a364edfaec0c732282db12dbe6a29f6fd4657db5689fb4b6639dd4c9f35f6`.
Code/test/example hashes are in `/tmp/wsdl-p3-29-qname-source-hashes.json`; the
final intended-file/artifact manifest is `qname-final-hashes.json` under that prefix.
The Debug core and native XML qmod retain their P3-28 hashes. No native source,
main-Qore worktree change, install or push is part of this increment.

P3 remains active. Next reductions in `/tmp/wsdl-p3-30-qname-context.qr` and `.log`
show a valid enum alias rejected, the same prefix rebound to a wrong namespace
accepted, and an enumerated provider accepting an unrelated QName. The namespace
loss boundary and affected scalar/attribute paths are recorded in
`/tmp/wsdl-p3-30-qname-context-preflight.md`. QName value identity, ENTITY/ENTITIES,
dateTime/time policy and other remaining P3 criteria stay in scope. No answer to
the pending leap-second question is inferred. P4-P9 have not begun.


## P3-30 — Explicit QName identity and native dependency validation

P3-29 is committed as `f6a4615`. This increment implements immutable
`XsdQNameValue` identities and explicit-context `XsdQNameDataType` providers.
It also fixes two libxml2 QName defects exposed by independent validation.
The [value contract](../../design/wsdl-qname-values.md),
[dependency behavior](../../design/xml-qname-validation.md) and
[root-cause evidence](qname-values-evidence.md) describe the implemented behavior.
Ordinary WSDL schema enumeration/default/fixed conversion and QName wire prefix
allocation remain open; this explicit API does not claim their completion.

| Requirement | Implementation and evidence |
| --- | --- |
| P3-QName-explicit-identity | Exact namespace/local comparison, lexical retention, full binding validation, implicit XML/default-reset handling, immutable metadata and reconstruction. |
| P3-QName-explicit-providers | String/object return metadata; optional/mandatory copies; record/list validation; independent contexts, cancellation and concurrent use. |
| P3-QName-native-oracle | Dependency lookup supplies the implicit xml binding; QName/NOTATION comparison equates absent and empty namespace URIs. Native validation passes all generated pairs. |
| P3-QName-dependency-selection | Runtime probe covers 48 schema/document pairs through DOM and streaming validation. Unpatched current releases fall back; corrected older-version backports remain system-selected. Original/corrected hashes, offline overrides, timestamps, distribution and install isolation are checked. |

The new Qore suite passes **10 cases / 278 assertions**. The frozen regression
gate passes **78 suites / 840 cases / 31,833 assertions**, including the existing
SOAP, schema, retained XML, XML-RPC, CDA and Cargo consumers. The soap suite
retains its documented 1,031 total / 1,028 succeeded assertion accounting, with
all cases passing. The final log is `/tmp/wsdl-p3-30-qname-complete.log`; per-suite
logs use the adjacent `qname-complete-<suite>.log` prefix. No new warnings or errors
occur in these gates.

QName value/lexical/HTTP suites pass **144 cases / 4,904 assertions** across
AST/IR/JIT/tiered and UTC/Europe-Prague. Compiled modules pass **18 cases / 613
assertions**; the complete new design example executes without output. WSDL,
SoapDataProvider, SoapClient and SoapHandler qmods, native documentation and WSDL
Qdx/Doxygen build cleanly. The new suite also passes with PCRE2 JIT disabled.
Evidence: `/tmp/wsdl-p3-30-qname-modes.json`, `qname-aot.json`,
`qname-build-complete.log` and `qname-no-jit.log` under that prefix.

The new independent Python method passes in **4.902 seconds**. It checks **336
retained envelopes**, including **160 valid QName inputs**, **2,016 conversion
verdicts** and **1,008 schema/document pairs** against Xerces and both native and
Python libxml2. Python's unchanged libxml2 2.12.10 retains four precisely
classified empty-default-namespace enumeration rejections; native and Xerces
validation plus exact value assertions pass. The matrix tests retained XML
scope and explicit providers, not new ordinary SOAP conversion. The existing
actual SOAP 1.1/1.2 HTTP suites also pass.

The affected Python gate completes **52 methods in 267.829 seconds**, retaining
exactly the two known P6 selected-binding-version failures for request and
response. The exact signatures match P3-29, with no new failures, errors or
warnings. Logs: `/tmp/wsdl-p3-30-qname-python-complete.log`,
`qname-python-gate-complete.log` and `qname-python-comparison-complete.json` under that prefix.

All **17 CMake provider integration methods** pass in **37.883 seconds** with
no warning diagnostics. They exercise real shared backports and the unpatched
2.15.4 release, both corrected source overrides, tampered inputs, reconfiguration,
offline/cross builds, selection changes and installation. Source-distribution
entries were added for both new CMake inputs. Complete logs:
`/tmp/wsdl-p3-30-qname-cmake-complete.log` and
`/tmp/qore-xml-libxml2-test-yb26iipq/commands.log`.

Valgrind verifies the final 48-pair DOM/streaming probe with **zero errors and
zero live allocations**. The complete 336-row worker and new Qore suite run
with `qore -b --enable-debug --exec-mode=ast` and the previously authorized
`QORE_PCRE2_NO_JIT=1`: **zero errors and zero definitely, indirectly or possibly
lost bytes**. All 336 worker results were checked. The existing core DWARF-reader
warning remains tracked for P9. The initial worker run used PCRE2 JIT, reproduced
its already root-caused diagnostic, and was stopped; only the completed
interpreter runs are claimed as memory-check evidence. No suppression was added.
Logs: `/tmp/wsdl-p3-30-qname-probe-valgrind-final.log`,
`qname-worker-valgrind-final.log/.jsonl` and `qname-values-valgrind-complete.log` under
that prefix.

The both-version survey and strict corpus reports differ from P3-29 only in
WSDL source hash. All counts, source/catalog hashes and **168 broad failure
signatures** are unchanged. Strict coverage remains **120 WSDLs / 1,148 message
directions**, zero selected failures. Reports and complete structural comparison:
`/tmp/wsdl-p3-30-qname-survey-complete.json`, `qname-coverage-complete.json` and
`qname-report-comparison-complete.json` under that prefix.

The full audit is **22 Pass / 40 N/A / 0 Fail**:
[audits/P3-30-qname-values.md](audits/P3-30-qname-values.md). Final WSDL SHA256 is
`3684be4393f6c63faf470894745d324229202a4be745a6957b393b00e13aa469`; the corrected Debug native XML qmod SHA256 is
`0b205d392e45a9c50f01aec6026ce3e325a1a23b5ee9f6c598eb170055ea45fd`. The isolated Debug core remains
`80078ec30d71bc618b7bb40991bad63604303f379c3e47e6dd41d58d0dbc56fd`.
The final review preserves explicit QName objects through repeated conversions
and providers with different defaults; unboxing a no-namespace object could
otherwise change its identity. New regressions and affected gates were rerun.
The final input/artifact manifests use `/tmp/wsdl-p3-30-qname-complete-source-hashes.json`
and `qname-final-hashes.json` under that prefix. Main Qore remains clean on
develop; no core edit, installation or push was made.

P3 remains active. Next is scoped QName conversion through declarations,
attributes, lists/unions and ordinary SOAP input/output, preserving both value
identity and lexical restrictions. ENTITY/ENTITIES, dateTime/time policy and
other remaining P3 criteria remain in scope. The pending leap-second question
has no inferred answer. P4-P9 have not begun.


## P3-31 — QName enumeration declaration scopes and recursive JIT storage

P3-30 is committed as `42046f7`. This increment captures each enumeration
literal's namespace identity at its own declaration scope, retains duplicate
spellings with different bindings through late base resolution, and validates
QName grammar, bound prefixes, inherited patterns and inherited enumeration
membership. Temporary captures are released on success and failure. Nested
namespace/local indexes compare exact identities. Whole-schema reconstruction
repeats these checks from retained source documents.

The [implemented contract](../../design/wsdl-qname-values.md) and
[declaration evidence](qname-declarations-evidence.md) distinguish these schema
checks from ordinary QName instance/provider/wire conversion, which remains
open. The new independent matrix has **66 declarations / 198 schemas / 396
actual SOAP 1.1 and 1.2 binding contracts**, including atomic, forward-reference
and simple-content models. Xerces-J 2.12.2 and libxml2 2.12.10 agree except for
three precisely asserted `xmlns:Name` declaration verdicts. The XML Infoset's
exclusion of `xmlns` from in-scope namespaces and pinned Xerces bytecode establish
that validator defect. Fixture hashes and original results are retained under
`/tmp/wsdl-p3-31-declaration-fixtures.json` and `declaration-oracles.json` with
that prefix; no upstream fixture was changed.

The JIT mode matrix initially exposed a core defect after enough schema parses
promoted `XsdSchema::parseTypes` to native code. Its closure-backed `schema`
loop local reused the caller's binding during recursive include processing,
so the outer parse visited the child declarations twice. LLVM closure loads and
stores omitted instantiation of callee-owned locals; AOT already performed it.
A reduced native regression and LLVM dump establish the root cause. The fix is
committed in main Qore develop as **`f135ddac7`**, with no push or installation.
Tests preserve their original order and keep JIT enabled.

The core increment passes its **62-item audit: 19 Pass / 43 N/A / 0 Fail**,
recorded in Qore's `examples/test/ir/audits/recursive-closure-locals.md`.
The new core suite passes **3 cases / 28 assertions**, with deterministic native
compilation completion, all four execution modes and source-stripped AOT.
Six affected existing suites pass, including JITSmoke and typed foreach; five
QUnit summaries total **194 cases / 5,237 assertions**. The native driver and
Qore scenario under `qore -b --enable-debug --exec-mode=jit` both pass Valgrind
with **zero errors and zero definite/indirect/possible loss**, without
suppressions. The authorized `QORE_PCRE2_NO_JIT=1` is used; the existing core
DWARF-reader warning remains tracked for P9. Core evidence uses the
`/tmp/wsdl-p3-31-core-*` and `recursive-*` prefixes. Other developers' main-Qore
history and work were preserved, and the main checkout is clean after commit.

Against the corrected isolated Debug core, **79 XML Qore suites / 853 cases /
31,947 assertions** pass. The soap suite retains its documented 1,031 total /
1,028 succeeded assertion accounting, with all 20 cases passing. All QName
suites pass **248 cases / 5,816 assertions** across AST/IR/JIT/tiered and
UTC/Europe-Prague. Compiled modules pass **31 cases / 727 assertions** and the
complete design example runs without output. WSDL, SoapDataProvider, SoapClient
and SoapHandler qmods and WSDL Qdx/Doxygen build without warnings or errors.
Logs: `/tmp/wsdl-p3-31-declaration-gate-core-fixed.log`,
`declaration-modes-core-fixed.log`, `declaration-aot-core-fixed.log`, and
`declaration-build-final.log` under that prefix; corresponding JSON reports
retain all suite summaries.

The final affected Python gate completes **55 methods in 369.185 seconds**.
Exactly the two known P6 selected-binding-version assertions remain failing,
with no new failures, errors or warning diagnostics. Complete signatures and
comparison are in `/tmp/wsdl-p3-31-declaration-python-core-fixed.log` and
`declaration-python-comparison-core-fixed.json` under that prefix.
Both corpus reports differ from P3-30 only in WSDL source hash: strict coverage
remains **120 WSDLs / 1,148 message directions**, zero selected failures, and all
**168 broad failure signatures** remain unchanged. The repo's current reports
are refreshed; complete comparison is
`/tmp/wsdl-p3-31-declaration-report-comparison-core-fixed.json`.

The XML increment's full audit is **20 Pass / 42 N/A / 0 Fail**:
[audits/P3-31-qname-declarations.md](audits/P3-31-qname-declarations.md).
WSDL SHA256 remains
`1cb5abba5c8c177722e65c55778f87bda6c76eeee98d1bdb9e36dd084d527f26`.
The corrected isolated Debug core is
`745c1da619df1407bda9d75442c9012551a67c91ca4e3c4ab4a6834da5be0b8f`;
XML's native qmod remains
`0b205d392e45a9c50f01aec6026ce3e325a1a23b5ee9f6c598eb170055ea45fd`.
The final declaration inputs were frozen in
`/tmp/wsdl-p3-31-declaration-source-hashes-final.json`.

The additional full QName declaration JIT Valgrind run passes all **13 cases /
114 assertions**, with **zero errors and zero definite/indirect/possible loss**,
without suppressions. It uses `qore -b --enable-debug --exec-mode=jit` and the
previously authorized PCRE2 interpreter setting. The known core DWARF-reader
warning remains a P9 environment finding. The first attempt reached its
240-second deadline before cleanup; its forced-termination leak summary is
superseded by `/tmp/wsdl-p3-31-declarations-valgrind-jit-complete.log`.

P3 remains active. A separately reduced pre-existing lifetime defect makes
`findType(...).serializeToData()` access a deleted `XsdAbstractType::nsc`; it also
fails against unchanged P3-30. A scratch ownership correction demonstrates
successful reconstruction and identifies the builtin namespace/type-cache cycle
that its cleanup tests must cover. This is next, before ordinary QName
wire/provider integration. ENTITY/ENTITIES, dateTime/time policy and other P3
criteria remain in scope. The leap-second question has no inferred answer;
P4-P9 have not begun.

## P3-32 — Declaration namespace ownership

P3-31 is committed as `d5985db`. The two `XsdAbstractType` constructors now own
rather than weakly reference their declaration namespace registry. Temporary
registries created for schema additions and imports therefore remain usable
through detached types, elements and attributes. No namespace map, conversion
rule, native source or Qore source is changed in this increment. The main Qore
checkout is clean on develop at `f135ddac7`, ahead ten commits, with no push.

The [ownership contract](../../design/wsdl-schema-identity.md#declaration-namespace-ownership)
and [regression evidence](namespace-ownership-evidence.md) document component
lifetime, indexed reconstruction and the builtin-cache cycle. The new suite
passes **13 cases / 105 assertions**; **12 cases fail against exact previous
source**, demonstrating deleted contexts and premature cleanup. It covers
nested imports/chameleon includes, sibling scope isolation, detached providers,
raw/binary reconstruction, QName declaration identities, failure/retry,
serialization errors, cancellation and deterministic concurrent copies.
Destructor-counted tests prove live ownership and cycle release, including
exception and interruption cleanup. The complete documentation example passes.

All **80 Qore suites / 866 cases / 32,052 assertions** pass. The soap suite
retains its previously documented 1,031 total / 1,028 succeeded assertion
accounting, with all twenty cases passing. Five affected suites pass **352
cases / 6,656 assertions** across AST/IR/JIT/tiered and UTC/Europe-Prague;
compiled modules pass **44 cases / 832 assertions**. WSDL, SoapDataProvider,
SoapClient and SoapHandler qmods and WSDL Qdx/Doxygen build without warnings
or errors. Gate, mode, compiled and build logs use
`/tmp/wsdl-p3-32-ownership-{gate,modes,aot,build}.log`; the first three have
corresponding JSON summaries.

The affected Python gate completes **55 methods in 400.364 seconds**, retaining
exactly the two previously tracked P6 selected-binding-version assertions.
There are no new failures, errors or warning diagnostics; exact comparison is
`/tmp/wsdl-p3-32-ownership-python-comparison.json`. Existing independent matrices
exercise actual SOAP 1.1/1.2 bindings, both directions, original/reconstructed
consumers and preserved scalar values. Both corpus reports differ from P3-31
only in WSDL source hash: **120 selected WSDLs / 1,148 directions**, zero selected
failures, and **168 unchanged broad failure signatures**. Full comparison is
`/tmp/wsdl-p3-32-ownership-report-comparison.json`; current repo reports are
refreshed without changing original fixtures or findings.

The complete new ownership suite under `qore -b --enable-debug --exec-mode=jit`
passes Valgrind with **zero errors and zero definite/indirect/possible loss**,
without suppressions. The authorized `QORE_PCRE2_NO_JIT=1` is used; Qore JIT stays
enabled. The existing core DWARF-reader warning remains recorded for P9.
Log: `/tmp/wsdl-p3-32-ownership-valgrind.log`. The full
[audit](audits/P3-32-namespace-ownership.md) is **20 Pass / 42 N/A / 0 Fail**.

Final WSDL SHA256 is
`b2618ceffda47428e2d9042e4ad3410d631c6bc676666dc615d357759f43d417`;
the frozen Debug core remains
`745c1da619df1407bda9d75442c9012551a67c91ca4e3c4ab4a6834da5be0b8f`.
Final intended-file hashes are in `/tmp/wsdl-p3-32-ownership-manifest.json`.
No push or installation was performed.

Next: ordinary QName instance/provider/list/union/fixed/default conversion and
output namespace preservation. A new reduced baseline in
`/tmp/wsdl-p3-33-qname-wire-baseline/` contains four actual SOAP contracts and
24 documents with agreeing libxml2/Xerces validity verdicts. It reproduces the
remaining lexical-only conversion and enumeration failures; complete inputs,
outputs and hashes are retained. Architecture notes are in
`/tmp/wsdl-p3-33-qname-integration-preflight.md`. ENTITY/ENTITIES, dateTime/time
policy and all remaining P3 criteria remain open. The pending leap-second
question has no inferred answer. P4-P9 have not begun.

## P3-33 — Preserve caller-owned scalar objects

P3-32 is committed as `1ad6ecf`. Complex record conversion now removes consumed
entries from its local hash copy without explicitly deleting objects retained
by the caller. The five cleanup sites cover sequence/all members, choice keys
and discarded attribute containers. The independently reduced baseline uses
the already-supported `XsdBinaryValue`: serialization succeeds, then access to
the original value raises `OBJECT-ALREADY-DELETED`. This is an XML conversion
defect; no native or Qore source change is needed. The main Qore checkout is
clean on develop at this commit gate.

The [ownership evidence](caller-owned-values-evidence.md) and
[implemented contract/example](../../design/wsdl-binary-values.md#caller-ownership-during-record-conversion)
describe the root cause and retained reference behavior. All **9 new cases /
147 assertions** pass, and all nine cases fail against exact previous WSDL
source. Coverage includes both conversion directions, shared siblings, repeated
values, nested records, choices, reconstruction, failure after an earlier
converted member, interruption and four synchronized concurrent callers.
The HTTP consumer suite passes **1 case / 148 assertions**, reusing the same
retained request and response objects through actual SOAP 1.1/1.2 bindings and
original/reconstructed services. The documentation example executes successfully.

The complete Qore gate passes **81 suites / 875 cases / 32,255 assertions**.
The soap suite retains its previously recorded assertion accounting with all
twenty cases passing. Five affected suites pass **40 mode/timezone invocations /
344 cases / 13,992 assertions** across AST/IR/JIT/tiered and UTC/Europe-Prague;
compiled modules pass **43 cases / 1,749 assertions**. After the final test-only
brace cleanup, the new suite also passes all eight mode/timezone combinations,
compiled execution and Valgrind again. Four affected qmods and WSDL Qdx/Doxygen
build without warning/error diagnostics. Logs and JSON summaries use
`/tmp/wsdl-p3-33-caller-values-{gate,modes,aot,build}`; the final eight runs are
in `/tmp/wsdl-p3-33-caller-values-final-modes.json`.

The affected Python gate completes **64 methods in 404.684 seconds**, with
exactly the two previously tracked P6 selected-binding-version failures and
no new failures, errors or warnings. The comparison is
`/tmp/wsdl-p3-33-caller-values-python-comparison.json`. Independent matrices
include binary values/facets, actual bindings, both directions, reconstruction
and exact value preservation. Both corpus reports differ only in WSDL source
hash: **120 selected WSDLs / 1,148 directions**, zero selected failures and
**168 unchanged broad failure signatures**. The complete structural comparison
is `/tmp/wsdl-p3-33-caller-values-report-comparison.json`.

Final Valgrind execution of the complete new suite uses
`qore -b --enable-debug --exec-mode=jit` with the authorized
`QORE_PCRE2_NO_JIT=1`. It reports **zero errors and zero definite, indirect or
possible loss**, with no suppressions. The known core DWARF-reader warning
remains tracked for P9. Log:
`/tmp/wsdl-p3-33-caller-values-valgrind-final.log`. The full
[audit](audits/P3-33-caller-owned-values.md) records **20 Pass / 42 N/A / 0 Fail**.

Final WSDL SHA256 is
`339e0fd59630f0bd442146baf4e2a3f50bf39e54ed473d25312eba3dfe63e364`;
the frozen Debug core remains
`745c1da619df1407bda9d75442c9012551a67c91ca4e3c4ab4a6834da5be0b8f`.
Intended-file hashes are in `/tmp/wsdl-p3-33-caller-values-manifest.json`.
No push or installation was performed.

P3 remains active. Next is QName instance/provider/list/union/fixed/default
conversion and output namespace preservation. Scratch code now preserves
QName identities across inherited bindings, local rebindings and default
namespace resets: 24 scoped inputs and 24 outputs validate with both independent
oracles, including structural element/attribute identity checks. That incomplete
implementation is excluded from this commit; scratch architecture and remaining
paths are recorded in `/tmp/wsdl-p3-33-prototype-state.md`. ENTITY/ENTITIES,
dateTime/time policy and all other P3 criteria remain open. The pending leap-second
question has no inferred answer. P4-P9 have not begun.

## P3-34 — Isolate QName union trial errors in libxml2

P3-33 is committed as `115ea97`. The private libxml2 build now propagates
`fireErrors` into `xmlSchemaValidateQName()` and guards its unbound-prefix
diagnostic. A failed QName candidate still returns its datatype error, while
a later valid union member can succeed without contaminating the validation
context or invoking an application error callback. This fixes the dependency's
existing error-reporting contract; no WSDL source or Qore core change is made.
The fetched/offline libxml2 source remains byte-identical, with exact original
and corrected compile-input hashes verified by CMake.

The [implemented design](../../design/xml-qname-validation.md) and
[regression evidence](qname-union-validator-evidence.md) record the normative
ordered-union requirement and root cause. The native probe passes **148
schema/document pairs** through DOM and streaming validation, including **100
new union pairs**, callback accounting and DOM context reuse after rejection.
The exact prior dependency rejects seven valid pairs; the partial-backport
fixture preserves this failure. All **18 CMake provider tests** pass in
37.507 seconds, including system/bundled selection, old advertised versions,
partial fixes, offline/cross builds, source integrity, reconfiguration and
staged notice installation. Logs: `/tmp/wsdl-p3-34-provider.log` and
`/tmp/qore-xml-libxml2-test-mnmphkkf/commands.log`.

The new Qore suite passes **5 cases / 351 assertions**, including separate
invalid content/attribute paths, collection candidates, ordered enumeration,
exact XML values and cancellation/recovery. The independent matrix checks
**30 schemas / 300 documents** against pinned Xerces-J 2.12.2 and both native
Qore parsing APIs. All normative verdicts agree; Python's separate libxml2
2.12.10 has exactly **21 recorded false negatives**, each with its required
error type/count. Complete fixtures and verdicts are retained under
`/tmp/xml-qname-union-validator-bhanf7v2/` and reproduced by the committed test.
The fixture manifest hash is
`4504254bd15b7e1ce2e33ca48893d6bb1a48fc994994d2ad5dfdbdeec13d46ad`.

The full Qore gate passes **82 suites / 880 cases / 32,606 assertions**.
The soap suite retains its previously recorded assertion accounting, with all
twenty cases passing. Eight AST/IR/JIT/tiered and UTC/Europe-Prague runs of the
new suite pass **40 cases / 2,808 assertions**. Native C compiles with
`-Wall -Wextra -Werror`; the Debug native module, probe and Doxygen build without
warnings/errors, using the installed `/usr` prefix and frozen isolated Qore.
The complete design example runs successfully. Logs and summaries use
`/tmp/wsdl-p3-34-native-{gate,modes,docs}` plus
`/tmp/wsdl-p3-34-{configure,build}.log`.

The affected Python gate completes **65 methods in 394.138 seconds** and
retains exactly the two previously tracked P6 selected-binding-version
assertions. There are no new failures, errors or warnings; comparison is
`/tmp/wsdl-p3-34-native-python-comparison.json`. Both corpus reports are
structurally identical to P3-33: **120 selected WSDLs / 1,148 directions**,
zero selected failures and **168 unchanged broad failure signatures**.
The original broad survey was rerun with matching arguments for that comparison;
an additional explicit-catalog survey is separately retained. Comparison:
`/tmp/wsdl-p3-34-native-report-comparison.json`. Unchanged current reports are
not rewritten, and historical findings/source fixtures remain intact.

Valgrind passes the complete native probe and complete new Qore suite with
**zero errors and zero definite/indirect/possible loss**, without suppressions.
Qore runs with `-b --enable-debug --exec-mode=jit` and the authorized
`QORE_PCRE2_NO_JIT=1`; the existing core DWARF-reader warning remains tracked
for P9. Logs: `/tmp/wsdl-p3-34-native-valgrind.log` and
`/tmp/wsdl-p3-34-native-qore-valgrind.log`. The full
[audit](audits/P3-34-qname-union-validator.md) records **22 Pass / 40 N/A / 0 Fail**.

The resulting native XML qmod SHA-256 is
`c1014ef946c9ef5fd1d62988eac45b8950ae402fb4041585188deca53b3682f9`.
WSDL remains
`339e0fd59630f0bd442146baf4e2a3f50bf39e54ed473d25312eba3dfe63e364`;
the frozen Debug core remains
`745c1da619df1407bda9d75442c9012551a67c91ca4e3c4ab4a6834da5be0b8f`.
Main Qore is clean on develop. No push or installation was performed.

P3 remains active. Two independently reduced native reader defects are assigned
to the next increment before resuming WSDL QName integration: scalar cursor
conversion calls a hash-only helper, and `schemaValidate()` passes its documented
XSD text argument to a schema-location API. Their root causes and exact baseline
failures are recorded in the evidence above and `/tmp/wsdl-p3-35-reader-next.md`.
The incomplete QName namespace/provider/list/union prototype remains in scratch
and is excluded from this commit. ENTITY/ENTITIES, dateTime/time policy and all
other P3 requirements remain open; no answer is inferred for the pending leap-
second decision. P4-P9 have not begun.

## P3-35 — Native reader scalar and empty values

P3-34 is committed as `ed0f53b`. `XmlReader::toQore()` and `toQoreData()` now
use an owned `QoreValue` conversion helper instead of the hash-only document
helper. Their documented scalar/empty values are returned safely, containing
boundaries are retained, and an empty element does not consume its following
sibling. Document-oriented parsing keeps its hash contract. The cursor methods'
incorrect `RET_VALUE_ONLY` flags are removed because they advance reader state.
No WSDL, libxml2 or Qore core source change is included.

The [implemented contract/example](../../design/xml-reader-values.md) and
[root-cause evidence](xml-reader-values-evidence.md) record the exact prior
Debug assertion and cursor semantics. The new suite passes **10 cases / 524
assertions**, covering scalar/empty/nested/mixed values, UTF-8 and both UTF-16
byte orders, attributes, grouping flags, document hashes, schema validation,
discarded results, invalid XML and interruption. An armed stream triggers
failure or cancellation after entering a record, preserving the original
exception and exercising partial-value cleanup. The saved baseline abort now
returns the expected string. The complete design example executes without output.

The existing independent QName union matrix now checks both cursor APIs for
all **30 schemas / 300 documents**, in addition to its document/cursor-read
checks. Pinned Xerces-J 2.12.2 validates every schema and assesses every
instance. Qore preserves exact accepted text/empty values and rejects every
invalid instance with the intended category. The previously recorded **21
old-libxml2 false negatives** remain unchanged. Final fixture/results artifacts
are `/tmp/xml-qname-union-validator-q1c2mf_5/`; the unchanged fixture manifest
hash is `4504254bd15b7e1ce2e33ca48893d6bb1a48fc994994d2ad5dfdbdeec13d46ad`.

The full audit corrected the side-effect flags and added an immediate pending-
exception check after the reader operation. All final gates were rerun against
the frozen resulting native build. **83 Qore suites / 890 cases / 33,130
assertions** pass; the soap suite retains its prior documented assertion
accounting with all twenty cases succeeding. Eight AST/IR/JIT/tiered and
UTC/Europe-Prague runs pass **80 cases / 4,192 assertions**. Debug native and
Doxygen builds, QPP generation and executed examples have no warnings/errors.
Logs use `/tmp/wsdl-p3-35-reader-gate-final.log`, `reader-build-frozen.log`,
`reader-modes.json` and `reader-example.log` under that prefix.

The affected Python gate runs **29 methods**: the 300-document native matrix,
15 survey tests and 13 coverage tests. It retains exactly the two previously
tracked P6 selected-binding-version assertions, with no new failures/errors/
warnings. Exact signatures are in
`/tmp/wsdl-p3-35-reader-python-comparison.json`. Both corpus reports are
structurally identical to P3-34: **120 selected WSDLs / 1,148 directions**, zero
selected failures and **168 unchanged broad failure signatures**. Comparison:
`/tmp/wsdl-p3-35-reader-report-comparison.json`. Original fixtures, historical
findings and unchanged current reports are preserved.

The complete new suite and affected existing `xml`, `xml-literal` and
`xml-whitespace` suites all pass Valgrind: **53 cases / 2,832 assertions**,
**zero errors and zero definite/indirect/possible loss**, without suppressions.
Every run uses `qore -b --enable-debug --exec-mode=jit` and the authorized
`QORE_PCRE2_NO_JIT=1`. The existing core DWARF-reader warning remains a P9
finding. Logs use `/tmp/wsdl-p3-35-reader-valgrind-final.log` and
`reader-valgrind-{xml,xml-literal,xml-whitespace}.log` under that prefix.
The complete [audit](audits/P3-35-xml-reader-values.md) is **25 Pass / 37 N/A /
0 Fail**.

The final native XML qmod SHA-256 is
`879f7178ed7307f9a36a9f549e26660f6c7d26cfd3c19cf7c2b4034c896853ff`;
source/native hashes are frozen in `/tmp/wsdl-p3-35-reader-frozen-native.json`.
WSDL and isolated Debug core retain their P3-34 hashes. Main Qore has newly
appeared concurrent AsyncIoController and WebSocketHandler edits; these are
not part of the XML work and are preserved in progress. No push or installation.

P3 remains active. The separate schema-attachment API conflict is next. With
no preference received yet, the stated compatibility assumption preserves
`schemaValidate()`'s existing file/URI behavior, corrects its documentation and
adds explicit `schemaValidateString()` for XSD text. The question remains open
to user steering; this increment does not change schema attachment. General
WSDL QName namespace/provider/list/union integration remains in scratch,
followed by ENTITY/ENTITIES, dateTime/time policy and the other P3 criteria.
No answer is inferred for the pending leap-second decision. P4-P9 have not begun.

## P3-36 — Reader schema attachment and resource state (in progress)

The compatible API correction preserves `XmlReader::schemaValidate()` as a
file/URI method and adds `schemaValidateString()` for XSD text. Its prior
string documentation contradicted the actual libxml2 file/URI call. The
optional API preference was presented to the user; work proceeds with the
stated compatible default, without treating silence as approval of a workaround
or of the outstanding leap-second decision.

The retained failing reproducer `/tmp/wsdl-p3-36-attach-baseline.qr` attaches an
integer schema, tries a missing replacement, then reads invalid integer content.
The old native API detached the first schema before parsing the replacement and
reported the invalid XML as valid. The new implementation compiles a candidate
first, checks reader state again after resource callbacks, and owns any candidate
retained by a native context even if allocating its SAX plug fails. Started/tree
readers reject attachment; reader destruction releases the native context before
its schema. Constructor text schemas use the same attachment path.

A separate reproducer `/tmp/wsdl-p3-36-schema-sandbox-baseline.qr` proved that
native schema file loading bypassed both PO_NO_FILESYSTEM and a deny-all
filesystem policy. The shared compiler now provides a scoped resource exception
context; callbacks enforce file/URI policy and block fallback after exceptions.
Callback streams belong to individual resources, allowing nested compilation and
restoration of the outer context. HTTP resource loading uses Qore's checked
transport and retains the final redirect URI as the base of relative imports.
The libxml2 >=2.14 path uses its per-schema resource loader; an isolated older
library compatibility harness is being checked separately. Production CMake still
rejects the unpatched installed libxml2.

The initial native regression is `test/xml-reader-schemas.qtest`: 11 cases /
173 assertions, including strings/streams, replacement success/failure, reader
boundaries, UTF encodings, NUL rejection, policy, callback fallback/cancellation,
nested parsing and reentrant advancement of the target reader. Independent HTTP
coverage is `test_schema_resources.py` plus `schema-resource-loader.qr`: five
methods for redirects/import bases, preserved ISO-8859-1 bytes, schema/document
rejections, denied destinations and recovery. This test fixture sets
XML_CATALOG_FILES to the empty string so host catalog configuration cannot affect
the independent server or the network-policy assertions; production catalog
loading is not disabled and remains subject to filesystem policy.

### Core prerequisite: HTTP/1 response persistence

The independent HTTP/1.0 server exposed a core transport bug: response parsing
ignored the HTTP version when deciding connection persistence and matched a
Connection field only when its entire value was `close`. A redirect could reuse
a nonpersistent connection and fail with HTTP1-CONNECTION-CLOSED. The separately
audited core fix applies RFC 9112 section 9.3, parsing comma-separated/repeated
options and giving close precedence. The native connection is marked closed
before the response future becomes available, using its existing dispatch path.

The isolated core is Debug with `/usr` prefix and no installation. Its current
SHA-256 is `8fe8c3c1bc4b1c09eddb76f0001cdba50f98be6ea3dcabe3f4e92b05e8eadd6b`,
superseding the frozen P3-35 core only for this increment. The implementation
SHA-256 is `3c6855a2660fa6766f740ff6410711db0f7c392be5976f4f8c482b3b49f55e5d`.
The new core regression has four cases / 111 assertions and passes AST, IR, JIT
and tiered modes. Its deterministic server keeps a nonpersistent socket open
until the client closes, detecting prohibited reuse without a FIN timing race.
The existing HTTPClient suite reports 256 assertions (22 completed cases and two
existing proxy/HTTP3 prerequisite skips; 63 assertions run before the HTTP3 skip).
Existing HttpClientIo redirects pass seven cases / 16 assertions; all five
independent schema HTTP methods pass. The full core audit is 25 Pass / 37 N/A /
0 Fail in `examples/test/qore/classes/HTTPClient/audits/http1-persistence.md`.

Valgrind with Qore JIT enabled and the authorized PCRE2 interpreter test setting
reports zero errors and zero definite/indirect/possible lost bytes. Alongside the
known DWARF-reader warning, a system SSSD warning remains a P9 environment finding:
`fstat(-1)` is called by `libnss_sss.so.2` during the c-ares service-name lookup for
socket bind. `/tmp/wsdl-p3-36-core-http-fstat.strace` records the syscall stack
through `sss_cli_check_socket`, `getservbyname_r`, and
`QoreCaresAddrInfoResolver::start`. Neither warning is suppressed or counted as a
clean environment check. This does not close the P9 environment requirements.

Core logs/manifests are `/tmp/wsdl-p3-36-core-final-*`. Core files copied into the
main develop checkout match the tested isolated source; concurrent AsyncIoController
and WebSocketHandler work is excluded. Core commit `1b357c9bd` is on the main repository's develop branch, without pushing.
The 84-suite XML gate (901 cases / 33,303 reported assertions) and both-version
corpus reports show no regressions; all previous suite results and both corpus
reports are structurally identical to P3-35. Native XML gates, final documentation, full audit
and commit remain pending; P3 and the overall P1-P9 plan are still open.


### P3-36 final native gates

The final implementation and [evidence](xml-reader-schemas-evidence.md) include
HTTPS certificate verification, catalog policy, a legacy FTP peer, partial-stream
failure/interruption and buffer-bound tests. The attachment suite is now 12 cases /
191 assertions, with 96 cases / 1,528 assertions across four modes and two timezones.
The full 84-suite gate reports 902 cases / 33,321 assertions; both-version raw and
strict corpus reports remain structurally identical to P3-35. All 300 independent
QName union documents pass both new attachment paths with exact values. The Python
coverage run retains exactly the two P6-selected-binding-version failures.

Affected native Valgrind tests pass 51 cases / 914 assertions with zero errors and
zero definite/indirect/possible lost bytes. The additional same-process HTTP batch
also has zero memory errors/loss. Known unsuppressed DWARF/SSSD warnings and the
unchanged native local-file loader's blocking-I/O review remain explicitly P9 work.
Debug/Release builds and docs pass without warnings/errors; the final attachment
and HTTP matrix pass the Release module and the isolated old-libxml2 compatibility
build. The full native audit is 26 Pass / 36 N/A / 0 Fail.

Core TLS prerequisite `8bbe7eed1` corrects only the default debug logging level,
retaining caught exceptions and certificate verification. Its three independent
TLS cases pass all four modes and Valgrind. It was committed on the main core
repository's develop branch without pushing, after the separate 62-item audit.
The frozen core for this increment is now
`e7445dbdfd81e79f053c78cb9e60b77c368eaa04a619f9093014091ae4bda8da`.

The independently reproduced raw-schemaLocation anyURI failure is retained in
[schema-uri-findings.json](schema-uri-findings.json) and assigned to the next P3
native-URI increment, alongside the offline oracle's Java URI/file-key issues.
A direct libxml2 C probe proves this failure exists without Qore. The valid raw
source is not rewritten or counted as passing. P3 is not complete; the WSDL QName,
list/union, provider, sample and wire integration work also remains active.


P3-36 was committed as `7a5ef5d` on develop, without pushing. Final source/artifact
hashes are in `/tmp/wsdl-p3-36-native-final-manifest.json`.

## P3-37 — Schema-location anyURI resolution

The next increment starts from the preserved URI finding. Source inspection shows
separate raw xmlBuildURI calls in xmlSchemaParseIncludeOrRedefineAttrs (includes
and redefines) and xmlSchemaBuildAbsoluteURI (imports and runtime schema hints).
The fix must apply the XSD anyURI-to-URI mapping at those resolution boundaries,
leaving original XML/schema lexical text unchanged, and retain percent escapes
without double escaping. The configured dependency must be behaviorally probed
for this defect too; the current pinned source is libxml2 2.15.4, whose original
archive/source files remain immutable. XML Base resolution and the existing
oracle's URI key normalization need boundary coverage before choosing the exact
patch. The QName/list/union WSDL integration scratch remains paused until this
native prerequisite passes.


P3-37 preflight is `/tmp/wsdl-p3-37-preflight.py`: 36 include/import/redefine
cases spanning raw versus escaped names, filesystem bases, XML Base and Unicode/
percent-containing directory names. The initial dependency passes the 18 escaped
references and rejects the 18 raw references. Existing percent escapes must retain
their URI meaning; the fixture explicitly encodes a literal filename percent before
comparing the raw-Unicode/space and fully encoded URI forms.

The first scratch native prototype is `/tmp/wsdl-p3-37-prototype.py` and builds an
isolated module in `/tmp/wsdl-p3-37-libxml/build-debug` without modifying upstream
sources or the production module. An early attempt escaped filesystem bases and
therefore changed their paths; this was rejected. libxml2 2.15.4 deliberately uses
xmlResolvePath for bases without `://`, so those bases must remain filesystem paths.
Further XML Base/URI and no-document-base cases remain to verify. XML Base Second
Edition section 3.1 recommends returning unescaped LEIRIs from base-access APIs;
a global eager escaping change to xmlNodeGetBase would need to preserve that
contract and is not the selected implementation.

A prototype missing-import path also exposed the existing Debug schema warning
handler's unconditional stdout printf, which corrupts JSON application output.
Its root is qore_xml_schema_warning_func in src/ql_xml.qpp. Preserve a regression
for optional missing imports and caught unresolved-type errors when addressing it;
do not strip the warning from diagnostic-driver output.


The direct base/URI probe `/tmp/wsdl-p3-37-base-probe.c` identifies a related
resource-identity defect: resolving `a%2Fb.xsd` against an HTTP base produces
`a/b.xsd`. Root cause: xmlBuildURISafe parses with percent unescaping before
reassembling the path. The scratch patch `/tmp/wsdl-p3-37-uri-patch.py` preserves
raw percent-encoded URI components through this resolver and teaches serialization
to retain valid percent triplets from raw components. It does not relax parsing of
invalid URI syntax. Include/import/redefine and XML Base tests must exercise this
identity preservation, not only schema validity. No production URI patch or probe
change has been applied yet.


The expanded scratch prototype now passes all 36 component/filename/XML Base
cases. `/tmp/wsdl-p3-37-base-helper.c` resolves XML Base LEIRIs while preserving
existing encoded values and returning newly resolved raw Unicode/space values;
it preserves reserved percent escapes and leaves malformed UTF-8 encoded. Direct
base tests return `http://example.org/wine/rosé` and retain `white%2Fwine`.
The prototype broad XML gate passes all 84 suites before production integration.

New durable regressions are in `test_schema_uris.py`. Live HTTP tests found a
module-loader error in P3-36: Qore's default client encoding changed `%2F` into
`%252F`. The correct existing API is setPreEncodedUrls(true), now added to the
loader. With that setting and the prototype dependency, actual request paths
preserve percent escapes and raw Unicode schema locations resolve correctly.
No new Qore core change is needed for this finding.

The native schema warning callbacks now use debug level 5 rather than unconditional
stdout output. A same-process regression keeps an optional missing import valid,
retains XSD-SYNTAX-ERROR when its type is required, then validates a later schema.
The baseline fails because the warning corrupts JSON output; the driver is not
changed to filter diagnostics. Runtime/parser warning behavior remains unchanged
in Release builds. Final dependency patches, CMake behavioral probes, independent
oracle URI normalization, comprehensive direct API checks, audit and commit remain
pending for P3-37.


P3-37 core prerequisite was committed as `3b70f8ccd` on main Qore develop, with no
push. It removes the incorrect tilde entry from pre-encoded URL rejection. The
independent HTTP peer covers ten exact successful targets and 39 rejected paths
per run, constructor/setter behavior and recovery. All four modes and three
Valgrind processes pass with zero memory errors/loss. The 84-suite XML gate and
both-version raw/strict reports are unchanged. Full audit: 19 Pass / 43 N/A / 0 Fail.
Core artifact SHA-256: `40c2824efa1fdd66cd20c50ad767dd18614c6f6f2842d9a5fd4e94311e89802e`.
Concurrent main-repository developer changes were preserved.

The native URI prototype now uses libxml2's existing extended parser mode for XML
Base, preserving raw Unicode and encoded octets directly. Its missing NUL
terminator guard was fixed before use; the earlier custom escape/decode helper is
retired. RFC 3986 vectors also exposed missing absolute-path normalization, incorrect
extraneous parent handling and collapse of empty URI path segments. The resolver
now uses linear in-place dot-segment removal preserving empty segments and percent
escapes; filesystem normalization separately corrects its absolute-root check.
The direct probe passes 106 URI/XML Base checks, including invalid percent syntax,
public raw/decoded parser compatibility and source-attribute preservation.

The checksum-guarded production CMake patch is being integrated with a behavioral
URI probe. It chains the existing QName source copy and leaves upstream sources
immutable. HTTP resource tests pass all twelve character forms, including tilde,
colon, reserved percent escapes, raw/escaped Unicode and query separators. The
full production dependency/provider, independent oracle and memory gates remain
pending before the XML commit; P3 remains active.


The integrated direct probe now includes 24 runtime schema-hint checks. They
exposed three additional boundaries: no-base streaming references bypassed the
anyURI mapper; noNamespaceSchemaLocation was split as a whitespace list; and
XmlReader supplied its document URI through a locator which assembly ignored.
The fixes map no-base references too, normalize one complete anyURI value, process
both hint attributes independently and consult the streaming locator. DOM/streaming,
absolute/relative, namespace-only/combined hints, whitespace and invalid integer
content all pass. The direct URI/XML Base allocation test passes 29 injected
allocation/recovery cases with zero Valgrind errors and all blocks freed.

The final module loader also escapes direct raw HTTP schema locations exactly once
before enabling pre-encoded URL mode. A direct raw Unicode/space URL previously
sent invalid HTTP bytes after that mode was enabled; the root boundary now handles
raw and escaped locations consistently. Live tests assert both exact request targets.

The offline oracle now uses raw-component RFC 3986 resolution and URI-identity keys.
Java URI.resolve/normalize were directly shown to collapse empty segments and use
older query/parent rules, so they are not used as the resolution oracle. Pinned
Xerces ignores XML Base in schema composition: XSDHandler.doc2SystemId reads the
SchemaDOM document URI (verified against the pinned JAR bytecode), and all three
component relations use it for the resolver base. Six exact false negatives remain
recorded; all twelve identical source schemas validate natively and reject bad
integers. The harness does not rewrite schema bytes or add aliases for the wrong
URI. Initial evidence: /tmp/xml-schema-uri-oracle-ao2k0vx6/results.json.

The production CMake provider matrix passes 20 methods, including an otherwise
QName-fixed shared library whose URI probe fails. Initial final gates and memory
checks are in /tmp/wsdl-p3-37-final-*. The first multi-target make command regenerated
its build files but retained its old in-memory target graph for the newly added
allocation target; a fresh invocation built all targets successfully. No source
workaround was needed. Full final evidence/audit and the XML commit are still pending.

### P3-37 final evidence and audit

The implementation and [final evidence](schema-uri-evidence.md) close the exact
historical native URI finding without changing its original source. The complete
probe passes 142 URI/component/runtime-hint checks. Allocation failure/recovery
passes 29 checks; both standalone native executables free all blocks under
Valgrind with zero errors and no suppressions. Six live URI methods pass all four
Qore execution modes, and all seven existing resource methods pass in Debug and
Release. The reader's eight mode/timezone runs pass 96 cases / 1,528 assertions.

The full 84-suite XML gate passes 902 cases / 33,321 reported assertions. All 300
QName oracle documents preserve exact values across six native paths and Xerces.
Final raw and strict corpus reports are structurally identical to P3-36; the
coverage unit tests retain exactly the two P6-selected-binding-version failures.
Survey unit tests pass all 15 methods. The 20-method provider matrix verifies
URI-sensitive selection, passing backports and immutable source/reconfiguration.
Debug/Release and documentation builds complete without warnings/errors.

Affected Qore Valgrind tests pass 51 cases / 914 assertions; three additional HTTP
processes pass exact targets, direct raw/encoded locations and failure recovery.
All have zero memory errors and zero definite/indirect/possible lost bytes.
Known unsuppressed environment warnings and native file I/O interruptibility remain
explicit P9 findings. The independent oracle's five URI and seven existing methods
pass their checks. Six exact Xerces XML Base schema false negatives, with document
checks still unreachable, are retained in
[schema-uri-validator-defects.json](schema-uri-validator-defects.json).

The full [62-item audit](audits/P3-37-schema-uris.md) is 20 Pass / 42 N/A / 0 Fail.
Its brace cleanup in the extracted URI parser helper was rebuilt and retested.
Final hashes are in `/tmp/wsdl-p3-37-final-manifest.json`. The earlier oracle load
failure caused by overlapping a module relink is retained in its log; the completed
build's URI/QName oracle and corpus reruns pass. P3 remains active; the next work
resumes QName/list/union WSDL provider, sample, reconstruction and wire integration.

P3-37 was committed as `1442c65` on develop without pushing.

## P3-38 — XSD 1.0 nested union composition

Resuming the QName prototype reproduced a list-of-unions output failure: scoped
lexical objects were coerced to strings before namespace allocation. The scratch
fix now preserves those objects through list output, pattern retention and final
binding checks. Its direct, list, restricted-list and union-of-list wire cases each
pass eight inputs and four valid outputs against Xerces and all six native paths.
The earlier 96 scoped QName/list/union inputs and their 96 outputs, provider/choice
checks and nine existing scratch regression suites also pass. This larger QName
implementation remains in scratch and is not part of the current production diff.

A nested-union variant exposed an independent production composition error.
XSD 1.0 Part 2 section 4.1.2.3 replaces an explicit union member with that union's
member definitions. Restrictions on the nested union do not carry into the outer
union. Xerces correctly accepted a case the initial scratch expectation marked
invalid; that expectation is preserved in its failed diagnostic log, not used to
weaken validation. A reduced numeric example shows production Qore falling through
from the wrongly restricted integer member to double for `2` and rejecting `true`.

The production fix resolves and validates the full dependency first, then references
the original union definition during composition. Shared nodes retain declaration
order without exponential member expansion. Direct restricted uses, atomic/list
member constraints and restrictions on the composed union remain effective.
The temporary resolution map is cleared on success and failure. The new qtest
passes four cases / 108 assertions in AST, IR, JIT and tiered modes. Its 32-level
shared graph preserves identity and bounded provider serialization.

The two independent Python methods pass five definitions / 37 lexical cases across
15 schema shapes, 444 request/response inputs, 252 valid outputs and 2,608 detached
consumer outcomes (1,584 valid outputs including examples). Every source/output is
checked by pinned Xerces and independent libxml2. Named/inline composition,
primitive order, retained outer/list constraints and negative errors are covered.
The full 85-suite gate passes 906 cases / 33,429 reported assertions without warnings.
Corpus comparison, final audit and commit are recorded below when complete.

Final raw and strict corpus reports retain every P3-37 result, with only the WSDL
source hash changed. Survey unit tests pass 15 methods, and coverage unit tests
retain exactly the two P6-selected-binding-version failures. Documentation builds
without warnings/errors. The full audit is 19 Pass / 43 N/A / 0 Fail; see
[union composition evidence](union-composition-evidence.md). No C++ changes or
native rebuild were needed. Final hashes are recorded in
`/tmp/wsdl-p3-38-composition-final-manifest.json`.

P3-38 was committed as `2fd307f` on `develop`, without pushing.

## P3-39 — QName instance and detached-provider integration (in progress)

The 21 prototype layers have been integrated into uncommitted `qlib/WSDL.qm`.
The prototype rebuild remains pinned to `/tmp/wsdl-p3-39-base-WSDL.qm` (P3-38)
and must not overwrite production: subsequent fixes now live in the working tree.
The exact prototype lineage is `/tmp/wsdl-p3-39-prototype-manifest.json`.

The scoped list output layers preserve retained string-fallback values through
lists and nested unions. QName field choices now compare namespace URI/local
identity, including repeated values and reconstructed fields. Their display
spelling remains lexical, and provider patterns apply independently.

A reduced custom-provider callback demonstrated that ambient serialization
namespace state overrode an independent QName provider's explicit bindings.
The prototype now passes retained lexical context directly to the intended QName
or union member, including list items; callbacks retain their own namespaces.
Selected QName and list results retain their actual typed values. Tests exercise
independent nested calls, cancellation/error propagation, recovery and schema/
provider reconstruction. The reproducer and before/after logs are
`/tmp/wsdl-p3-39-provider-scope.qr` and `/tmp/wsdl-p3-39-provider-context-types-*`.

Inspection of the scratch runner found that it reported child-suite failures
without failing its own process. It now asserts every result. Three regressions
in union normalization were traced to an internal deserialization probe creating
its trial cache before establishing namespace context. A nested call then used
an independent cache and lost the selected primitive identity. Establishing that
context at the probe entry fixes all ten existing list/union/attribute suites;
the exact results are in `/tmp/wsdl-p3-39-regressions-context.log`.

Provider metadata tests reproduced recursive conversion of a cyclic QName base
and trusting a stale serialized field-membership index. Reconstruction now
rejects cyclic bases and rebuilds field indexes from their authoritative choices.
QName restriction conversion traverses deep built-in chains iteratively and
indexes enumeration identity. The new scratch qtest
`/tmp/wsdl-p3-39-provider-hardening.qtest` passes six cases / 63 assertions,
including a 600-level chain, aliases, defaults, repeated choices, atomic failed
updates, malformed metadata and reconstruction. Full-suite verification against
the rebuilt prototype is running through `/tmp/wsdl-p3-39-scratch-full-gate.py`;
its result is not inferred from the targeted tests.

The previous 96 scoped inputs / 96 outputs and five fallback/composition wire
matrices pass after the provider-context change. Final integrated coverage,
namespace-conflict handling, standalone output contracts, malformed metadata
corner cases, documentation, full audit and commit remain outstanding. P3 is
still active, and P4-P9 have not started. The leap-second decision remains
pending; no answer or scope approval is inferred.


The integrated context matrix now passes 144 scoped inputs (124 valid) and 80
ordered fallback inputs (48 valid), original/reconstructed services, five native/
detached provider paths and both SOAP versions/directions. Every output is checked
for expanded QName values and retained unbound prefixes. Six native validation
paths and pinned Xerces assess the inputs and outputs. Logs are
`/tmp/wsdl-p3-39-qname-scoped-matrix.log` and
`/tmp/wsdl-p3-39-qname-fallback-matrix.log`.

Additional root causes fixed in production: union field choices now convert
enumerations with their declaration scopes; schema serialization scopes are bound
to the intended `Namespaces` object so independent callbacks keep their registry;
and list-item union conversions preserve lexical context at the item boundary even
when sharing their caller's trial cache. Retained list tokens keep QName/scoped
objects if a value-preservation probe needs original spellings. Focused callback,
thread barrier, cancellation, field alias and reconstruction tests pass. The new
standalone `XsdSchema::serializeXmlValue()` returns a complete retained element,
including QName attributes and simple content.

A pinned Xerces schema warning is separately adjudicated: the 2.12.2
`XSDAbstractTraverser.checkEnumerationAndLengthInconsistency()` final branch uses
Java string length on list enumeration text. XSD 1.0 Part 2 section 4.3.1.3 requires
list item count. The matrix asserts this exact single `FacetsContradict` warning
for its one restricted-list schema; document verdicts and all native paths remain
mandatory. Source jar: Maven `xercesImpl-2.12.2-sources.jar`, preserved locally as
`/tmp/wsdl-p3-39-xerces-sources.jar`. No production validation is weakened.

The first integrated 88-suite gate is running. New scoped-value integrity tests
pass 3 cases / 52 assertions. Example generation exposed discarded declaration
bindings in `getUnionSample()`; the reduced native/retained-XML sample matrix is
being fixed and added to the permanent matrix before final verification. No P3-39
commit or final audit has occurred. The main Qore checkout is clean at `4e049e0d8`;
no core change or push was made during this integration step.


### P3-39 final integration audit and verification

Production is now authoritative; do not rebuild the old prototype over it.
Further audit reductions fixed output-retention leakage into independent schema
callbacks, retained XML's unbound-prefix requirements during envelope allocation,
union enumeration samples, patterned QName-capable lists, standalone QName-list
union identity and standalone list binding conflicts. New scope maps restore
node-local declarations, and list serialization identifies QName items from the
resolved schema without constructing detached provider graphs.

The new standalone suite passes seven cases / 1,206 assertions, including two
128-level sibling trees with distinct bound and unbound prefixes and conflicts
in both list-item orders. Provider-context, provider-facet and scoped-value suites
pass 4/122, 7/87 and 3/52 cases/assertions respectively. All four suites pass in
AST, IR, JIT and tiered modes on source SHA-256
`46bd191122fb85d5d5c2160fb0e63dacd0bc122ab1868a09370dbccc27e44091`.
Three documented examples execute; Doxygen builds without warnings/errors.

Independent existing QName lexical/value/declaration and union-composition tests
pass eight Python methods. Survey tests pass 15 methods, normative tests five,
and corpus tests fourteen. Coverage tests run fourteen methods with exactly the
two unchanged P6 selected-binding-version assertion failures; the new QName
mutation check and strict selection pass. No skip or expected-failure annotation
was introduced. The final 89-suite XML gate passes 929 cases / 35,144 reported assertions on the
above source, with no warnings or failures.

The enlarged all-scoped worker reached its 300-second deadline. A reduced
patterned-list contract produced 296 identical rows in AST (79.26 seconds) and
JIT (69.44 seconds); removing redundant provider construction reduced the AST
run to 48.45 seconds with identical results. These are Debug diagnostic timings
under concurrent load, not Release benchmarks. The permanent matrix now bounds
each scoped worker to one schema shape while retaining both binding versions,
all values, seven consumers, reused/reconstructed providers and examples. Its
full 4,072-outcome / 3,776-document rerun passes both methods in 306.276 seconds;
`/tmp/wsdl-p3-39-final-context.log` records the complete result. All Xerces and six
native-path verdicts, expanded values and retained-XML assertions pass.

Updated current reports add QNameElement and QNameAttribute to the strict gate:
122 descriptions / 1,156 directions, 1,060 passing exact-value checks and zero
failed/missing/skipped checks. Raw output rejections are 42 (four fewer), including
four valid-input invalid outputs (four fewer). Bidirectional coverage has exactly
160 broader failure signatures, eight fewer QName output-schema failures and no
new signature. The full audit is in `audits/P3-39-qname-context.md`, with all 62 checklist items resolved: 20 Pass / 42 N/A / 0 Fail. See `qname-context-evidence.md` for root causes,
public contracts, matrix counts and exact Xerces warning adjudication.

The generated fixture inventory is `/tmp/wsdl-p3-39-final-fixtures.json`, SHA-256
`a51d5d278a0c2d6c47b2b37bd77451b841f756c71c4bb0a54eaf0b0b2eaae68b`.
The main Qore checkout was rechecked clean at `4e049e0d8`; no Qore commit or push
was required. P3 remains active; ENTITY/ENTITIES and the unresolved dateTime/time
leap-second policy remain next criteria, followed by all P4–P9 requirements.

Final source/artifact/test/report hashes are in `/tmp/wsdl-p3-39-final-manifest.json`.
The exact report comparison is `/tmp/wsdl-p3-39-final-report-comparison.json`;
all original corpus hashes, input verdicts and every non-QName case are unchanged.


P3-39 was committed as `a0d57a1` on `develop`, without pushing.

## P3-40 — Native ENTITY/ENTITIES validation

The native increment is implemented and verified. The four original corpus
families still need WSDL document-context integration: their eight messages lack
unparsed-entity declarations and are invalid. Native standalone XML now accepts
correct declarations and rejects undeclared/parsed/parameter names, with ordered
union selection, typed enumeration/list values and first declaration bindings.
Built-in list minimums are inherited and contradictory effective length bounds
fail schema construction.

The reader also propagates schema callback errors when libxml2 reports a node or
ordinary EOF, preserving ownership of partial conversion results. GDB identified
invalid ENTITY defaults as the source of the original 336-byte leak. The expanded
pre-fix test reproduced 21,840 leaked bytes; the final eight-case suite is clean
under Valgrind, as is the native 78-site allocation-failure test. The existing
isolated core DWARF diagnostic remains recorded for P9 without suppression.

The final gate passes 90 Qore suites / 937 cases / 35,897 reported assertions.
ENTITY's eight cases / 753 assertions pass on Debug and Release and in all four
execution modes. Four independent Python methods cover 5,679 documents, 39,753
native verdicts, 432 schema constructions and external-resource/DOCTYPE policy.
Nine exact Xerces inherited-minimum false acceptances are independently root
caused; native rejection remains mandatory. Provider tests (22), survey tests
(15), oracle protocol tests (7), resource/URI tests (18), native probes and the
executed example pass. Builds and Doxygen have no warnings/errors.

The complete both-version corpus report is exactly unchanged. WSDL source SHA-256
remains `46bd191122fb85d5d5c2160fb0e63dacd0bc122ab1868a09370dbccc27e44091`.
See [native evidence](entity-native-evidence.md), the
[implemented design](../../design/xml-entity-validation.md), and the
[62-item audit](audits/P3-40-entity-native.md): 21 Pass / 41 N/A / 0 Fail.
Exact source/artifact/log hashes are in `/tmp/wsdl-p3-40-final-manifest.json`.
The reproducible fixture inventory is `/tmp/wsdl-p3-40-final-fixtures.json`, SHA-256
`7ea2cfba6ff302d0bd98da0cebc0c13a1fde684ee7e79e8d4a3dc036ab40a383`.

P3 remains active. WSDL ENTITY/ENTITIES conversion/provider/sample behavior is
next; standalone XML declarations must not relax SOAP's DOCTYPE prohibition.
The dateTime/time leap-second decision remains unanswered. No decision or scope
reduction is inferred; all P4–P9 requirements remain in scope.

P3-40 was committed as `abd5785` on `develop`, without pushing. The main Qore
checkout was rechecked clean on `develop` at `4e049e0d8`; no core commit was needed.

## P3-41 — WSDL ENTITY document-context integration (preflight)

The initial reduction is `/tmp/wsdl-p3-41-preflight.py`, with generated contracts
and results below `/tmp/wsdl-p3-41-preflight`. It exercises actual SOAP 1.1 and
1.2 bindings, both directions, reconstructed services/message providers, scalar,
simple-content/attribute and repeated-element shapes, and generated examples.
Pinned Xerces independently validates each emitted payload. No WSDL production
change has been made yet.

The implementation must keep XSD datatype/facet checks distinct from containing-
document constraints. Schema enumeration/default compilation and detached lexical
value operations cannot invent an instance DTD. A selected ENTITY member must
retain its document constraint even though its primitive value identity is a
string; a failed context check must not redirect an ordered union to a later
string member. The existing `XsdUnionTrialResult` and list-item capture mechanisms
retain primitive identity but currently discard this selected-type obligation.
SOAP and retained XML document entry points must enforce their document context;
trial rejection, cached member selection, provider metadata/comparisons, callbacks
and sample generation need independent recovery/selection tests.

### P3-41 implementation and verification

The preflight completed with 336 schema-invalid outputs, 192 datatype rejections
and 240 valid outputs among 768 outcomes. The implemented increment retains
ENTITY obligations independently of primitive identity and checks them after
selected datatype/facet conversion at element, attribute, array and WSDL part
boundaries. It includes typed RPC parts and complete/retained XML. Pure datatype
provider operations and schema enumeration compilation retain their existing
contracts; message-provider instance validation and native sample selection are
next integration criteria, not claimed complete by this increment.

The nil regression was root caused to emitting `xsi:nil` without registering the
instance namespace in standalone output. Review also caught a prospective default
regression: revalidating lexical defaults in instance namespaces would reinterpret
QName prefixes. The fixed `getInstanceDefaultValue()` checks the already compiled
value using a private output registry, retaining declaration identity. New tests
cover QName/string defaults, reconstruction and rebound prefixes.

The final Qore gate passes 92 suites / 948 cases / 36,146 reported assertions.
The nine-case ENTITY value suite passes 185 assertions in AST, IR, JIT and tiered
modes; the two-case local HTTP/RPC suite passes 64 assertions. The independent
matrix exercises 72 actual SOAP binding contracts, both directions, reconstructed
services and providers, retained XML and examples: 2,880 outbound outcomes with
888 valid outputs; 9,216 inbound/consumer outcomes with 7,392 independent document
verdicts (6,528 valid / 864 invalid). Every schema, diagnostic, repeated occurrence,
value and reachable stage is checked. The example and Doxygen build pass.

The strict gate now covers 126 descriptions / 1,172 directions with no selected
failure and all 1,060 value checks passing. Exactly sixteen broader ENTITY failure
signatures disappear, leaving 144. Raw output rejections fall from 42 to 34 because
the eight original invalid messages are now rejected during decoding. All 2,399
non-ENTITY raw rows, all 289 non-ENTITY coverage cases and all corpus hashes are
unchanged. `/tmp/wsdl-p3-41-comparison.json` records the exact comparison.

Survey tests pass fifteen methods. Coverage tests run fourteen methods with only
the same two P6 binding-version assertions failing (request/response SOAP 1.1
through the mixed-description fixture). No skips or expected failures were added.
The HTTP invalid-callback-output case additionally reduces the P7 fault-origin
issue: `SoapHandler::makeSoapFaultResponse()` unconditionally selects Sender/Client,
including for server serialization failures. `/tmp/wsdl-p3-41-fault-reduction.log`
records both versions. This follows the plan's explicit later-phase ownership;
the ENTITY suite verifies rejection/recovery without claiming fault conformance.

See [the design](../../design/wsdl-entity-values.md),
[evidence](entity-wsdl-evidence.md) and [full audit](audits/P3-41-entity-wsdl.md).
No C++ changed and no new Valgrind run is required. The main Qore checkout remains
clean on `develop` at `4e049e0d8`, with no core commit or push needed.

The leap-second question was presented again while independent P3 work continued:
follow XSD 1.0 with retained leap-second text, or explicitly approve rejection as
an interoperability limitation. No answer or limitation is inferred. P3 remains
active, followed by every P4–P9 requirement.

Final fixture inventory: `/tmp/wsdl-p3-41-final-fixtures.json`, SHA-256
`72779be7ef62588dd0caed4d665bde317af9dc23ac30ac00ada9699ae5e9731e`, preserving 72 WSDLs and twelve manifest/result files under
`/tmp/wsdl-p3-41-complete-artifacts`. The final independent run passes in 127.262
seconds; see `/tmp/wsdl-p3-41-completeness-final.log`. Source, artifact and log
hashes are in `/tmp/wsdl-p3-41-final-manifest.json`. The full audit resolves all
62 checks: 19 Pass / 43 N/A / 0 Fail.

P3-41 was committed as `a6bb218` on `develop`, without pushing.

## P3-42 — Complete message providers

`/tmp/wsdl-p3-42-preflight.qr` isolates six scalar contracts and their reconstructed
message providers: ten provider acceptances (five inputs, original/restored) fail
instance serialization, and five of six native examples are unusable. The exact
baseline is `/tmp/wsdl-p3-42-preflight.log`. Direct string-first values, integer
alternatives and empty custom lists remain valid.

An uncommitted `XsdMessageDataType` prototype retains the existing HashDataType
field metadata and adds a private-namespace check of supplied part values after
field conversion. It prevents native-container shortcuts and preserves optional
copies/reconstruction. Its initial reduction changes the ten false acceptances
into `RUNTIME-TYPE-ERROR`; native samples have not been changed. The prototype is
not audited or ready to commit. The independent matrix, metadata/projection and
callback/recovery tests must establish that the retained schema context preserves
all provider contracts before choosing the final implementation.

The final message adapter retains resolved part components and applies existing
schema instance conversion after normal field conversion, with private namespace
allocation and no global document-validation flag. Field metadata, optional and
soft copies, field projections, enclosing providers and caller-owned values are
covered. Groups/complex types explicitly transport their private emptiability
metadata; their compiled type graphs and declaration QName defaults reconstruct.

Final verification passes 93 Qore suites, 957 cases and 36,372 assertions. The new
nine-case suite passes 226 assertions in AST/IR/JIT/tiered modes, including malformed
metadata, shared graphs, reentrant schema callbacks, actual program interruption
and synchronized concurrent use. The independent matrix passes 12,096 outcomes
and 8,280 document verdicts in 137.108 seconds. All 72 generated WSDLs are unchanged.

The survey's 2,411 rows and coverage report's 293 cases compare exactly with P3-41;
only WSDL source provenance changes. Strict selection has no failure; 144 broader
failure signatures remain. Survey tests pass fifteen methods; coverage tests
retain exactly the two known P6 binding-version failures. The catalog example and
Doxygen build pass. No C++ or main-Qore changes, installs or pushes were made.

The initial optional-group test reproduced the already tracked P4 missing-group
semantics; its source and failure log are preserved, and group metadata is tested
independently here. Native sample generation remains the next independent P3 fix.
See [provider evidence](message-providers-evidence.md),
[the design](../../design/wsdl-message-providers.md) and
[all 62 audit checks](audits/P3-42-message-providers.md): 20 Pass / 42 N/A / 0 Fail.

P3-42 was committed as `a0bdea1` on develop, without pushing.

## P3-43 — Native sample instance checks

The existing generator may return datatype-valid values that cannot form the
requested instance (the P3-42 preflight retains five such native samples across
six scalar contracts). The boundary check now validates generated
element/type-part candidates before returning them, raising XSD-SAMPLE-ERROR for
ordinary schema rejection and propagating other failures. Nested generation is
assembled before one root check. The existing choices option remains an
explanatory all-alternative representation.

Review found and fixed bypassed public subclass hooks in the initial nested
builder. The final implementation preserves dispatch with a consumed child-call
context, restored on exit and isolated per thread. Reentrant calls validate
independently. The unknown-message diagnostic now includes its missing argument.
The final regression suite fails eight of nine cases against parent `a0bdea1`.

Final verification passes 94 suites, 966 cases and 36,510 reported assertions,
without warnings or failures. The new nine-case suite passes 138 assertions in
all four execution modes. The independent ENTITY matrix passes 12,096 outcomes
and 8,280 document verdicts; the QName matrix passes 4,072 worker outcomes and
3,776 document checks with its existing, explicitly adjudicated diagnostic.
All 72 ENTITY WSDLs and every survey/coverage outcome remain unchanged. Strict
selection passes; 144 broader signatures and the two known P6 coverage-test
failures remain visible. Examples and Doxygen pass. The final documentation-only
source edit was followed by new-suite, example, documentation and report checks.

See [verification evidence](sample-instances-evidence.md),
[implemented design](../../design/wsdl-sample-instances.md) and
[the full audit](audits/P3-43-sample-instances.md): 19 Pass / 43 N/A / 0 Fail.
No native or main-Qore change, installation or push was made. Remaining P3 scalar
criteria and P4-P9 are still open; this increment does not close the plan.

P3-43 was committed as `77acb1b` on develop, without pushing.

## P3-44 — Native time output and core offset prerequisite (in progress)

Refreshing the temporal reduction on the current core confirms that dateTime
already retains explicit offsets. Time output still writes only milliseconds
and omits its offset. The new three-case native/HTTP reduction fails every case
against P3-43, including an actual response changing
`23:59:59.123456-03:30` into local `23:59:59.123000+01:00`.
Source/log: `test/wsdl-time-output.qtest`, `/tmp/wsdl-p3-44-before.log`.

An uncommitted formatter preserves all six native microsecond digits and an
explicit XSD offset, rejecting durations and offsets outside whole minutes in
the allowed range. Boundary testing exposed two core defects: date.getUtcOffset()
uses the standard offset rather than the date's instant, and the timezone manager
reserves the valid -1-second offset as an unset sentinel. The latter also loses
that offset through serialization. Reductions and core tests are in
`/tmp/wsdl-core-date/examples/test/qore/vars/date-utc-offset.qtest`, with initial
failure logs `/tmp/wsdl-p3-44-core-before.log` and
`/tmp/wsdl-p3-44-core-sentinel-before.log`.

The isolated core now looks up date offsets by epoch and uses zero as the initial
fallback until its reverse scan finds a standard type, without reserving an
offset sentinel. A 54-byte authored TZif tests a standard offset of -1 second.
The core build, final tests, Valgrind and full audit remain pending; no core change
has yet been copied into the main checkout or committed. Native time output and
its independent binding matrix also remain uncommitted until that prerequisite
and all XML gates pass.

The leap-second question now has an explicit normative conflict attached:
[the XSD 1.0 value model](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#dateTime)
and its Appendix-E-based comparison algorithm disagree for equivalent leap-second
offset spellings, as reduced in [the W3C issue report](https://lists.w3.org/Archives/Public/www-xml-schema-comments/2002AprJun/0043.html).
The second-edition errata contain no Part 2 correction. The user was asked whether
to preserve leap-second identity under the value model or approve rejection as
an interoperability limitation. No answer is inferred. This independent native
output increment does not decide that question or complete strict dateTime/time
lexical, arbitrary-fraction and facet acceptance. P3 and P4-P9 remain open.

### Core prerequisite committed; XML formatter needs the lossless input path

Qore main develop now contains `49513fe97`, with a clean working tree and no
push. Only the eight tested source/test/fixture/documentation files were copied
from the isolated checkout. The new core suite passes five cases/611 assertions
in AST/IR/JIT/tiered and AOT; the main-source copy also passes with the isolated
runtime. The final union with the four existing suites contains 108 cases and
42,416 reported assertions across 20 suite/mode runs. Both new/existing date
suites have zero Valgrind errors and zero lost bytes. The known isolated-core
DWARF-reader warning remains visible and unsuppressed. Focused documentation and
the example pass; Python zoneinfo confirms the transition and authored-TZif
expectations. All 62 core audit items resolve: 23 Pass / 39 N/A / 0 Fail.
Core source/evidence: `examples/test/qore/vars/audits/date-utc-offset.md` in Qore;
exact manifest `/tmp/wsdl-p3-44-core-final-manifest.json`. The new Debug library
SHA-256 is `bc3501b6e25140bad2034d68f13f0c37aa5f7b3feb373e39d2ec4bd9dceae536`.

The native-clock prototype passes its initial three-case/362-assertion suite in
all four modes and its independent matrix (672 input/round-trip documents plus
1,840 detached-consumer/example documents; 16.945 seconds). The 95-suite gate
also passed before the additional regression below. These checks cover native
values with explicit offsets; they do not establish absence preservation.

Review of the full reports exposed a new regression for unzoned XML times. The
legacy parser assigns the program's zone, and the corrected native formatter
then writes that offset. The raw survey's 2,411 rows and all coverage counts/
failure identities are unchanged, but the TimeAttribute and TimeElement emitted
bodies reveal the changed timezone presence. Those values are not yet assessed
by the strict temporal-value gate, so unchanged failure counts cannot validate
this change. The new fourth case in `test/wsdl-time-output.qtest` now fails for
that exact reason: `/tmp/wsdl-p3-44-unzoned-regression.log` (four cases, three pass,
one error, 363 reported assertions). It is a required failure, without a skip or
expected-failure annotation.

The XML formatter, tests and draft implementation documentation remain
uncommitted. They must be completed with the lossless temporal input/provider
contract and re-audited before committing; no independent formatter acceptance
is claimed. The leap-second interpretation is still awaiting the user's answer.

### Leap-second interpretation approved; upstream integration

On 2026-09-10 the user explicitly approved preserving leap-second values and
timezone-equivalent identity. This resolves the pending question above; strict
temporal work proceeds using that value model, with normative assertions for
independent validators that cannot represent leap seconds.

The user also requested remote develop updates. Both repositories fetched
successfully: XML `eef38e7` fixes regular-file PROPFIND resource hashes; Qore
`6aa122698` includes provider discovery/catalog updates and `2d329a7a0` fixes JIT
code lifetime through module shutdown. Both merge cleanly with the local work;
merge commits await integration checks and the full audit.

### Remote updates integrated; strict temporal work active

The XML merge is committed as `fe0f4a9` and Qore as `537b61514`, without pushes.
XML's three WebDAV suites and WSDL interop pass 19 cases/317 assertions; the
exported merge's entire both-version report matches committed counts, rows,
inputs, scope and source/catalog hashes. Full XML merge audit: 16 Pass/46 N/A.
Qore's integration passes 109 cases/1,751 assertions including AOT/JNI. The
full JIT shutdown suite passes Valgrind (8 cases/42 assertions); separate
per-process logs for the affected compiled module-delete callback show zero
errors and zero lost bytes in every process. The existing DWARF-reader warning
remains visible. Qore audit: 25 Pass/37 N/A; review corrected eight incoming test
headers to local relative requirements. Both merge audits record all 62 checks.
The refreshed isolated Debug libqore SHA-256 is
`71b856d6290cfbc2b87b26da5e069fd795f9c11b3784d2ac1695930628a821b3`.

The uncommitted XML helper now includes strict time/dateTime grammar, exact
fraction strings, missing-zone preservation, midnight carry without year zero,
and the approved leap-second value model. Providers use the shared calendar
contract and preserve strings whenever native dates would lose information.
New unit tests pass 6 cases/1,422 assertions before the latest floating-leap
boundary additions; native/lossless HTTP tests pass 5 cases/436 assertions.
The existing calendar value/facet suites pass (6/1,975 and 12/3,224).
Bounded example generation now tries fixed builtin prefixes when a pattern
leaves leading calendar/clock components unconstrained; every candidate is
validated through all restrictions.

A first independent matrix found binary64 seconds in both libxml2 and Xerces,
confirmed by native source and `javap` on the pinned Xerces JAR. Both falsely
accept distinct long-fraction enumeration values. Four exact reductions are
retained in `temporal-validator-defects.json`; rational-value assertions and
Java XMLGregorianCalendar's BigDecimal comparison separately distinguish them.
The current matrix passes three methods: 1,296 input/round-trip documents,
3,072 detached-consumer/example documents, and ten independent Java value
comparisons. Both validators have 24 explicitly adjudicated false positives
per builtin on inputs; none on the emitted consumer documents. These are
validator limitations, not passing normative verdicts.

The temporal change is still uncommitted. Remaining work includes broadening
normative/independent leap-second and temporal partial-order coverage, auditing
all scalar consumer paths and documentation, promoting exact temporal values
into the strict corpus gate, and rerunning the final affected suites, both-version
survey, coverage and complete commit audit. P3 is not closed; P4-P9 remain open.


### P3-44 completed: strict dateTime/time values and output

The temporal increment now validates lexical input before native conversion,
retains timezone absence and exact fractions/years/leap seconds as necessary,
compares facets and collection identities exactly, and preserves native output
microseconds/offsets. The approved leap-second value interpretation is implemented.
The [durable contract](../../design/wsdl-time-output.md),
[verification evidence](temporal-values-evidence.md) and
[full audit](audits/P3-44-temporal-values.md) describe the final behavior.

Review fixed corrupted union metadata acceptance and zero-fraction ordering
(Qore sorts empty strings last; fractional zero must sort before positive values).
All 96 affected Qore suites pass: 980 successful cases / 38,536 reported assertions.
Temporal tests pass 9/1,578, native/lossless HTTP tests 5/436, union/list identity
10/231, all in AST/IR/JIT/tiered. Independent matrices assess 6,880 documents and
718 seeded temporal boundaries, with exact rational/decimal comparisons. Four
binary64 schema-validator false positives and one Java direct-time ordering
limitation remain explicitly adjudicated; normative expectations are mandatory.
Doxygen and the executable example pass. Full audit: 19 Pass / 43 N/A / 0 Fail.

Strict selection now includes all dateTime/time element and attribute fixtures:
130 WSDLs / 1,260 message directions, zero selected failures. Both-version survey
rows/counts and all 144 diagnostic failure identities are unchanged. Fifteen
survey tests pass; the fifteen coverage tests retain exactly the two previously
tracked P6 binding-version failures. P3 phase acceptance is the next review;
P4-P9 remain authorized and unfinished.

A parallel pull --rebase moved main Qore develop from merge 537b61514 to 422e1ee14
on top of remote 6aa122698. The UTC-offset fix and all seven affected native files
remain identical to the tested snapshot, and the main tree is clean. That rebase
removed the merge's eight test-header changes and audit from the current tree;
they remain in the historical merge and isolated test snapshot. This XML work
preserves that parallel history. No push or installation was performed.

## P3-45 — XML-RPC character data and HTTP encoding prerequisite

The deferred XML-RPC text work is implemented, tested and audited. See [the contract](../../design/xmlrpc-character-data.md) and
[evidence](xmlrpc-text-evidence.md) for root causes, reference identities and tests.
The new Qore suite passes 13 cases / 226 assertions in all four execution modes.
Independent Expat/XML-RPC decoding checks 272 generated documents, with 34 actual
HTTP value/fault exchanges. All affected native and peer Valgrind runs are clean.
The current full gate passes 97 suites / 998 cases / 38,810 reported assertions;
the existing three caught comparator-negative assertions remain documented in P1.

Qore develop commit `38e8e0e52` fixes buffered request-body charset metadata and
HTTP protocol fields inheriting a prior body charset. Its full 62-item audit is
committed beside the new core test. The isolated Debug runtime matches the changed
main source and passed 105 core cases / 987 assertions plus focused Valgrind.
No main Qore changes remain from this work and nothing was pushed or installed.

XML merge `aec7c38` integrates remote `c1403ef`. The remote anyAttribute scalar
hash widening is retained. Positive text fixtures now declare mixed=true; a
separate element-only wildcard fixture rejects text in both directions. Native
XSD checks confirm that distinction. The merge's full audit is
[audits/P3-45-remote-anyattribute.md](audits/P3-45-remote-anyattribute.md).
Qore origin/develop remained at the already integrated `6aa122698`.

All 2,411 survey rows and the 144 diagnostic failure records are unchanged;
strict coverage remains 130 WSDLs / 1,260 directions with zero selected failures.
The two existing P6 binding-version tests remain diagnostic failures. P3 acceptance
review and all P4-P9 requirements remain in scope. The [full XML-RPC audit](audits/P3-45-xmlrpc-character-data.md) records
25 Pass / 37 N/A / 0 Fail across all 62 checks. Next: finish the P3 acceptance
review before implementing P4. The complete P1-P9 plan is not yet finished.

## P3-46 — Literal scalar attributes and final HTTP integration

XML-RPC increment P3-45 is committed as `cd684fc`. The P3 acceptance review
confirmed strict selection of all 43 original P3 families, then added a focused
numeric/boolean HTTP consumer matrix. Its first valid request exposed unconditional
SOAP reference processing of ordinary literal `id` attributes. The binding and
value helpers now require an encoded reference context before resolving references;
literal values reach their schema unchanged. See the
[implementation and evidence](literal-attributes-evidence.md).

The new suite passes three cases / 1,336 assertions in all four execution modes,
including 44 HTTP exchanges per mode, invalid client/handler values and recovery.
The independent literal matrix checks 32 inputs and 20 outputs with both validators,
also in all four modes. An old positive synthetic reference assertion used an
RPC/literal contract; it now rejects that invalid input, while a separate actual
RPC/encoded contract checks valid and missing references in both directions.

The full affected gate passes 98 suites / 1,001 cases / 40,146 reported assertions.
Doxygen, three executable examples, the both-version survey and strict coverage
pass their gates. All 2,411 survey rows and 144 diagnostic failure identities are
unchanged; all 1,260 strict message directions pass. The complete Python phase
inventory initially ran 68 files / 248 methods and exposed the known P4/P5/P6
diagnostics plus a 90-second regex-consumer deadline. That deadline is being
investigated independently before P3 acceptance. Its unchanged 90-second worker
deadline passes in an isolated rerun (three methods / 101.591 seconds total); the
initial parallel timeout remains in the log. No phase completion is inferred
from this increment. P4-P9 remain authorized and unfinished.

The [P3-46 audit](audits/P3-46-literal-attributes.md) resolves all 62 items:
18 Pass / 44 N/A / 0 Fail. Final source and runtime hashes are recorded in
`/tmp/wsdl-p3-46-final-manifest.json`. No C++ changed and no native installation
or push was performed. Next: consolidate the full P3 acceptance matrix.


## P3-47 — Phase acceptance (2026-09-10)

P3-46 is committed as `defff2c`. The complete scalar phase now passes its
acceptance criteria; [P3-acceptance.md](P3-acceptance.md) contains the reviewed
matrix, and [P3-acceptance.json](P3-acceptance.json) records all 43 original
families, ten criterion groups, 49 audit fingerprints/commit records and the
complete final test inventory. The original findings remain unchanged.

The final committed-source gate passes 99 Qore suites / 1,006 successful cases /
40,743 reported assertions, plus 1,380 standalone native IEEE checks. This adds
the native IEEE suite to the 98-suite P3-46 gate. All three caught comparator
negatives in soap.qtest remain documented; all its cases pass. The final Python
inventory runs 69 files / 249 methods. Only four explicitly assigned diagnostic
files fail, with all 33 failure records identical to the prior inventory: four
P4 choice failures, one aggregate P5 wildcard-example failure, two P6 selected
binding/version failures, and 26 P6 header/body/RPC records. There are no new
errors, warnings, skips, or missing/duplicate files.

The regex suite passed alone with its unchanged 90-second worker deadline before
the rest of the final inventory ran in parallel. The initial parallel timeout is
retained as evidence; it was not accepted as a passing result or hidden by changing
the test. The final long QName matrix passes both methods in 407.943 seconds.
Final logs/manifests use `/tmp/wsdl-p3-final-`; the precise runtime hashes are in
the committed register. All final Python Qore invocations use -b via a temporary
invocation wrapper, and debugging remains enabled.

All 2,411 both-version survey rows, their counts, and the 144 both-direction
coverage failure identities remain unchanged. The current reports now identify
the final WSDL source fingerprint. Every original P3 family is strictly selected;
130 descriptions / 1,260 message directions pass the strict gate. Eight original
P2-labelled runtime content failures retain the P5 owner established at P2
acceptance. P4 has 76 corpus records; the remaining 60 are labelled P5. Actual
SOAP 1.1/1.2 binding and HTTP scalar coverage comes from the authored matrices,
not from changing the envelope namespace in the W3C archive.

Both repositories were fetched again: no further remote develop commits were
pending, main Qore remained clean, and no push was performed. P1/P2/P3 are complete.
P4 is the next implementation phase; P4-P9 retain their complete original scope.
The initial P4 read-only review identified loss of declaration order at schema
parsing plus split element/choice emission and flattened group occurrence metadata.
No P4 implementation preceded this acceptance.

The [P3-47 full audit](audits/P3-47-acceptance.md) records 5 Pass / 57 N/A /
0 Fail across all 62 checks. Final phase-boundary reruns again pass the required
Qore interoperability suite and all 15 survey harness methods.

## P4-01 — Ordered construction and native occurrence counts (2026-09-10)

P3 acceptance is committed as `66fa548`. The first P4 increment constructs one
ordered particle graph for complex types and named groups. It retains declaration
positions before namespace stripping, shared element/type identity, complete
occurrence strings, empty compositors, named references and base-before-extension
order. Reconstruction covers complete schemas and detached types. The implemented
[model contract](../../design/wsdl-particles.md) separates declaration counts from
the existing native field adapters; runtime matching remains the next P4 criterion.

Independent occurrence tests exposed two libxml2 defects: digit-only count parsing
and a zero-count local declaration becoming a consuming automaton transition.
Checked build-tree corrections address both causes, and the provider runtime probe
rejects partial backports missing either correction. The downloaded archive is
unchanged. The [native contract](../../design/xml-particle-counts.md) records the
retained native integer capacity and cancellation boundaries. Autotools distributions
now include the occurrence inputs and two previously missing ENTITY inputs.

The final affected gate passes **101 Qore suites / 1,020 cases / 43,196 reported
assertions**, including the native IEEE suite. The three deliberately caught
comparator assertions in soap.qtest retain their documented accounting; all 20
cases pass. The model suite passes 10 cases / 1,854 assertions and native count
suite 4 / 597 in AST, IR, JIT and tiered modes. Existing compositor and SOAP array
context suites pass 8 / 57 and 9 / 46 in each mode. Independent matrices pass all
four modes with 80 model rows, 12 expected construction errors and 880 native
validation rows. Their completeness checks prevent missing/extra results.

The [independent evidence](particle-counts-evidence.md) records the two corrected
libxml2 defects and two Xerces-J lexical defects. Original signed schemas and
separately named canonical derivatives are both tested. The exact Xerces false
acceptances and unreachable document stages remain explicit; native tests assert
the normative results rather than adopting a validator mistake.

The provider integration suite passes 23 methods; the added source-distribution
check passes separately, for 24 total methods. The native runtime probe passes
all namespace/QName/URI/ENTITY/occurrence checks. Valgrind passes the probe, native
count suite and existing reader-schema suite (12 cases / 191 assertions), with
zero errors, zero definite/indirect/possible loss and no suppressions. Qore runs use
the previously authorized `QORE_PCRE2_NO_JIT=1`; Qore JIT remains enabled. The
initial run with PCRE2 JIT reproduced its known uninitialized-load diagnostic and
is retained as a failed run, not counted as passing. The known core DWARF warning
remains assigned to P9.

The affected WSDL/native Doxygen targets and extracted invoice example pass
without warnings. A broader `docs` build reports 22 independent cross-reference/
parameter warnings, recorded as failing diagnostics in
[P9-documentation-diagnostics.json](P9-documentation-diagnostics.json). They include
missing external tags and a link to the removed XmlRpcConnection constructor-info
API; the P9 complete documentation gate must resolve every record. No warning is
suppressed and no full-documentation success is claimed.

All **2,411 baseline both-version survey rows** and their counts/inputs are
identical to P3 acceptance. The additional catalog-enabled diagnostic has 2,415
rows and no unassessed inputs; its different dependency configuration is not used
to claim an implementation improvement. The complete adjudicated coverage uses
the catalog and retains all **144 failure records**, including 76 owned by P4.
All **130 descriptions / 1,260 selected directions** still pass. The four known
nested-choice runtime failures are reproduced unchanged. All 15 survey harness
methods pass. Current reports identify the final WSDL source hash.

Logs use `/tmp/wsdl-p4-01-`; the committed
[validation inventory](P4-01-validation.json) records exact source/runtime hashes
and the complete Qore suite inventory. A final documentation-only exception entry
was followed by the model suite, affected docs and both corpus reports against
the final source. Both repositories were fetched again: XML has no incoming
develop commits; main Qore is clean and synchronized at `a9dd15fe3`, containing
the independently committed schema and container-type fixes. XML tests use the
isolated, previously verified Debug prerequisite runtime recorded in the inventory.
Nothing was installed globally or pushed.

The [full P4-01 audit](audits/P4-01-particle-construction.md) resolves every one of
the 62 checklist items with zero Fail. P1/P2/P3 remain complete. P4 ordered runtime
matching/serialization, whole-group semantics, ambiguity checks, consistent field
metadata and samples remain in progress; P5-P9 retain their full authorized scope.

## P4-02 — Bounded ordered particle recognition (2026-09-10)

P4-01 is committed as `47d14ea`. `XsdParticle::matchesElementNames()` now checks
complete ordered child-name sequences against whole nested particle counts. It
shares the tested scalar regex matcher through a typed expanded-name predicate;
there is no surrogate character encoding or expansion of large declared counts.
Shared group graphs keep independent caller continuations. All groups retain their
own permutation/required-member rules. Element wildcard metadata captures its
namespace constraint in the declaration context and survives reconstruction.

The [implemented design](../../design/wsdl-particles.md) documents the polynomial
bounds, empty-language distinction, zero-component omission and thread/cancellation
contract. The new structural API does not yet replace message field adapters or
perform UPA, value, nil or dynamic-type checks. Those remain explicit P4/P5 work;
no corpus failure has been reclassified as passing by this increment.

The final affected gate passes **102 Qore suites / 1,031 cases / 43,488 reported
assertions**, including the new matcher suite's 11 cases / 292 assertions. The
existing soap.qtest comparator accounting is unchanged: three intentional caught
negative assertions and all 20 cases passing. Matching, model and affected regex
suites pass in AST, IR, JIT and tiered modes. The independent matching matrix
passes all four modes with **11 schema families / 270 documents / 22 actual SOAP
binding contracts / 2,160 worker rows per mode**, covering each bound input/output
root and original/reconstructed graphs. Fixed inventory checks prevent missing or
extra rows. Existing independent regex execution, count and character-class
matrices pass all 11 methods; no scalar regression or timeout remains.

The [independent evidence](particle-matching-evidence.md) records exactly two
libxml2 zero-count false acceptances and one Xerces empty-choice false acceptance.
The Qore predicate rejects all three under the normative XSD 1.0 rules. The
independent implementations remain unchanged. Focused tests also cover 81-digit
counts, finite count gaps, 10,000 input names, 1,000 positions, 80 nested repeats,
shared group DAGs, malformed reconstruction, invalid all placement, cancellation
and four concurrent calls. All test processes have bounded completion deadlines.

The affected Doxygen target and updated invoice example pass without warnings.
This increment changes Qore code only; the native module/library hashes are
unchanged and new Valgrind runs are not required. The final source/runtime hashes
and complete suite inventory are in [P4-02-validation.json](P4-02-validation.json).
Logs use `/tmp/wsdl-p4-02-`.

All **2,411 baseline survey rows**, original inputs, counts, **144 coverage failure
records**, 293 case records and both-direction stage accounting are identical to
P4-01. The current reports update only the WSDL source fingerprint. All **130
selected descriptions / 1,260 directions** pass strict coverage. The four existing
nested-choice runtime failures and 22 independent P9 documentation warnings stay
recorded as failing diagnostics.

Both remotes were fetched: no incoming develop commit remained. Qore develop is
synchronized at `a9dd15fe3`, including the pushed container-type fix. Subsequent
uncommitted core type-system work appeared while this audit ran and is preserved
for the active parallel developer. XML tests continue to use the isolated tested
Debug runtime identified in the inventory. Nothing was installed or pushed.

The [full audit](audits/P4-02-particle-matching.md) resolves all 62 checks with zero
Fail. P4 ambiguity validation, ordered message conversion, field metadata and
sample generation remain in progress. P5-P9 retain their complete original scope.

## P4-03 — Exact construction-time particle attribution (2026-09-10)

P4-02 is committed as `e71a61d`. Schema construction now checks unique particle
attribution after group and base resolution, before legacy occurrence projection
can mutate shared declarations. Unused named groups and each present nested
component are checked. `XsdParticle::validateDeterminism()` applies the same rule
to reconstructed graphs. Actual expanded names and wildcard namespace constraints
determine overlap; repeated iteration boundaries around one declaration may remain
ambiguous without violating unique declaration attribution.

The implementation follows published weak-determinism/flexibility algorithms with
exact rational thresholds. Occurrence values and shared reference paths are never
expanded. An arbitrary-integer multiplication overload supports exact cross-product
comparisons, including adjacent 80/81-digit count thresholds. The implemented
[design](../../design/wsdl-particles.md) documents the algorithm and resource bounds.
The [independent evidence](particle-ambiguity-evidence.md) records specification
references, complete finite-prefix enumeration and exact validator discrepancies.

The final affected inventory passes **103 Qore suites / 1,045 cases / 43,578 reported
assertions**. This includes the final attribution suite's **14 cases / 90 assertions**;
the audit added unused-group, extension-boundary and absent-zero-group coverage after
the full gate, then reran that suite in all four modes. Production source did not
change after the gate. Existing matcher, model and duration suites pass AST, IR,
JIT and tiered modes. The new independent tests pass all four modes: **300 finite
schema cases (242 valid / 58 ambiguous), 600 actual binding descriptions and 2,536
worker rows**, plus **12 focused schemas / 24 bindings / 72 rows** per mode. Every
bound request/response and reconstructed graph is accounted for. No emitted case
is skipped or partially enumerated. Failure/recovery, four concurrent callers and
interrupt/reuse tests pass. A rejected schema preserves previously shared group
requiredness and allows a subsequent valid schema addition.

Four additional native libxml2 attribution bugs were reproduced and root-caused:
counter-insensitive automaton analysis rejects two valid counted-boundary models;
transition coalescing loses declaration identity and accepts duplicate-choice
positions, including inside a surrounding empty language. Private libxml2 2.15.4
reproduces all four. [P4-native-attribution-diagnostics.json](P4-native-attribution-diagnostics.json)
keeps these as **failing requirements assigned to the next P4 native attribution
increment**, which must be repaired before P4 acceptance. Xerces-J 2.12.2 has one
independently asserted false rejection because its UPA builder reduces an inner
2..3 range to 1..2. Neither independent implementation was changed. This increment
establishes the Qore schema check; it does not claim native validation is repaired.

Both corpus reports retain identical counts, all **2,411 baseline rows**, source
hashes, inputs, **144 failure records**, 293 case records and complete stage
accounting. Only the WSDL module fingerprint changes. Strict coverage passes all
**130 selected descriptions / 1,260 message directions**. Affected Doxygen output
and the updated invoice example pass without warnings. Native code/binaries are
unchanged; this Qore-only increment requires no new Valgrind run. The complete
[P4-03 validation inventory](P4-03-validation.json) records hashes and suite results;
logs use `/tmp/wsdl-p4-03-`.

Both remotes were fetched. XML has no incoming develop commit; main Qore develop
is clean and synchronized at `cb90afb7b`, including the parallel deferred-constant,
separated-module-source and binary multipart fixes. Tests use the unchanged isolated
Debug runtime identified by its binary hash, not an unverified newer core build.
No installation or push was performed.

The [full audit](audits/P4-03-particle-attribution.md) resolves all 62 checks:
**19 Pass / 43 N/A / 0 Fail**. P4 native attribution, ordered message conversion,
field metadata and sample generation remain in progress; the four compositor
runtime failures remain visible. P5-P9 keep their entire original scope, including
the 22 separately recorded P9 documentation diagnostics.

## P4-04 — Native particle-use identity (2026-09-10)

P4-03 is committed as `17c5b40`. The private libxml2 provider now retains source
particle-use identity while lowering content models to automaton transitions.
Two references to one declaration and two uses of a shared group remain distinct;
multiple emissions of one counted source position retain one identity. Callback
declaration data remains unchanged. A compiler-local map keyed by parent use and
particle address prevents atom equality/coalescing from erasing competing uses.
All-group members, wildcard transitions, atom copies and substitution members use
the same identity contract. Input/output source hashes pin both corrected C files,
and upstream bytes are unchanged.

The [implemented design](../../design/xml-particle-identity.md) documents identity,
ownership and resource bounds with an executed shared-group example. Native
[identity evidence](native-particle-identity-evidence.md) records root causes,
provider behavior and the remaining findings. The final gate passes **104 Qore
suites / 1,051 cases / 43,671 reported assertions**. The new native suite passes
**six cases / 93 assertions** in AST, IR, JIT and tiered modes, including DOM and
streaming schema error categories, global/group/substitution collisions, all and
wildcard cases, repeated emission, content values, invalid integers, recovery and
interruption. The existing native occurrence suite also passes all four modes.

CMake's **nine-case particle identity probe** accepts complete system backports and
rejects incomplete ones independently of their advertised version. All **26 provider
and source-distribution tests** pass with zero compiler warnings, including offline
fallback, cross-build verification, unexpected-source rejection, unchanged input
hashes, stable reconfiguration and isolated install ownership. The private allocation
fixture checks **327 fault points**, map growth, allocation-free re-entry, recovery
and zero live allocations. Affected docs-module and the new example pass warning-free.

Valgrind passes the identity and occurrence Qore suites and the standalone allocation
fixture with **zero memory errors, zero definite/indirect/possible losses and zero
suppressions**. The standalone test frees all heap blocks. The Qore runtime retains
116,230 reachable bytes in LLVM/loader process-lifetime allocations; a first run
classified those reachable blocks as errors, and its full stacks were inspected and
retained. No lost allocation or invalid access was found. The existing isolated-core
DWARF diagnostic stays P9-owned. Qore tests use `-b --enable-debug` with the previously
authorized PCRE2 JIT testing switch under Valgrind. No system installation was made.

The [12-schema native recheck](P4-04-native-attribution.json) now rejects duplicate
choices correctly and retains **three failing P4 requirements**: exact-boundary and
nested-count-2 require exact counter-feasibility analysis; empty-language-component
requires checking present model-group constraints before unreachable-state removal.
This refines P4-03's root-cause explanation of the latter: identity loss was one
problem, but automaton reduction also removes the unreachable competing positions.
The original four-failure record remains historical evidence. These three failures
are assigned to the next P4 native counted-attribution/component increment and must
close before P4 acceptance. Independent lxml/Xerces binaries and their discrepancy
lists remain unchanged.

Both corpus reports are completely identical to P4-03: **2,411 baseline rows**, all
source/input hashes, **144 coverage failures**, 293 case records and stage accounting.
All **130 selected descriptions / 1,260 message directions** pass strict coverage.
The [validation inventory](P4-04-validation.json) records the changed native binary,
checked C source hashes, unchanged WSDL/core binary hashes and complete suite list.
Logs use `/tmp/wsdl-p4-04-`; the final provider artifacts are
`/tmp/qore-xml-libxml2-test-uqe2ommw`.

The [full audit](audits/P4-04-native-particle-identity.md) resolves all 62 checks:
**20 Pass / 42 N/A / 0 Fail**. P4 continues with native counted attribution and
component checks, then ordered message conversion, field metadata and samples.
P5-P9 retain all original requirements, including the 22 separately recorded P9
documentation diagnostics. No push was performed.

## P4-05 — Native counted attribution and execution (2026-09-10)

P4-04 is committed as `0bacf95`. The private dependency now checks exact counted
component attribution before automaton reduction. Every present group is checked,
including unused definitions and components inside an empty surrounding language.
Zero-count particles contribute no child component. The checker uses a memoized
source DAG, sparse name predicates and exact integer ratios; inherited particles
retain their original count source. The [implemented design](../../design/xml-particle-attribution.md)
includes an executed fixed-boundary example and documents ownership and execution.

The [12-schema native matrix](P4-05-native-attribution.json) now passes all 24
DOM/reader rows, closing P4-04's three remaining attribution/component failures.
Abstract declarations contribute only usable substitution members, and native
callbacks now follow the admitted declaration. All groups retain required empty
members as an empty language. The [native attribution evidence](native-particle-attribution-evidence.md)
records normative requirements, root causes and independent-validator evidence.

Correct schema acceptance exposed lost nested counter operations in native epsilon
reduction: the initial finite-language oracle found 28 false acceptances. The fix
preserves schema increments and their upper bounds. Nullable terms use a zero
execution minimum without modifying source occurrence fields; saved/restored
progress marks prevent counting repeated empty iterations. The correction is
restricted to schema automata, preserving generic regexp and Relax NG behavior.
The original independent validators and their recorded discrepancy lists remain
unchanged; native fixes do not reinterpret those results.

The final gate passes **105 Qore suites / 1,059 cases / 43,828 reported assertions**.
The native suite passes **eight cases / 157 assertions** in AST, IR, JIT and tiered
modes. The complete finite-language oracle uses seed 4103 and checks **1,000 models**
(765 valid / 235 invalid), **2,000 schema rows** and **41,630 DOM/reader document rows**
per mode, including negative mutations and complete row accounting. Every mode
passes all 43,630 rows. Existing SOAP/provider/HTTP, failure recovery and interruption
suites remain in the affected gate.

All **30 CMake provider/source-distribution tests** pass with CMake 4.3.0 and zero
compiler warnings. An **11-case behavior probe** detects incomplete attribution
and counter backports. Exact arithmetic checks **1,399 operations**, summary tests
cover 11 boundaries (including adjacent 80/81-digit ratios) and four malformed
programs, and direct all-summary assertions verify required versus optional empty
members. Allocation fixtures exhaust **134 arithmetic/set, 229 checker and 15
executor fault points**, with baseline ownership and successful fresh reuse.

Valgrind passes the final native Qore suite and all three standalone fixtures:
**zero memory errors, zero definite/indirect/possible losses and zero suppressions**.
Standalone fixtures free every heap block. Qore retains 116,230 bytes in 46
LLVM/loader process-lifetime blocks; its known isolated-core DWARF diagnostic stays
P9-owned. Only Valgrind uses the authorized PCRE2 JIT testing switch. Affected
native documentation, the executed example and all 15 survey harness methods pass.
No system installation was made.

The entire both-version corpus reports are identical to P4-04: **2,411 baseline
rows**, source/input hashes, **293 coverage cases**, **144 failure records** and all
stage accounting. Strict coverage has no selected failures across **130 descriptions
/ 1,260 message directions**. The [validation inventory](P4-05-validation.json)
records final source/runtime hashes and complete suite results. Logs use
`/tmp/wsdl-p4-05-`; final provider artifacts are
`/tmp/qore-xml-libxml2-test-gz7woxfi`.

A separate native occurrence-range defect remains explicitly failing and assigned
to the next P4 increment: the scanner saturates at `INT_MAX`, then rejects finite
maxima above the `UNBOUNDED` sentinel (`1 << 30`) before exact attribution runs.
The [range diagnostic](P4-native-count-range-diagnostics.json) retains eight schemas
/ 16 DOM-reader rows with **14 failing requirements**, including a small positive
control and a negative schema rejected for the wrong reason. Large exact helper
arithmetic does not imply that those native occurrence attributes already parse.
This defect must close before P4 acceptance; no range limitation or workaround has
been approved. Ordered WSDL message conversion, field metadata and samples remain
P4 requirements, including the four visible compositor runtime failures.

The [full audit](audits/P4-05-native-particle-attribution.md) resolves all 62 checks:
**20 Pass / 42 N/A / 0 Fail**. Both remotes were fetched again; no incoming develop
commit remained. Main Qore is clean and synchronized at `cb90afb7b`; the XML remote
bugfix at `c1403ef` is already included. The tested isolated core is recorded by
binary hash. No push was performed. P5–P9 retain their complete scope, including
mandatory Python CI setup, supported-platform acceptance and the 22 previously
recorded P9 documentation diagnostics.

## P4-06 — Exact native occurrence ranges (2026-09-10)

P4-05 is committed as `35e54e3`. The private dependency now preserves arbitrary
finite occurrence bounds through parsing, automaton construction and DOM/reader
execution. The root cause was the lexical/control-field ceiling and a numeric
maximum colliding with `UNBOUNDED` (`1 << 30`). The correction keeps exact source
attributes and separate finite identity, with owned exact counter bounds and
executor values. Small finite counters retain integer storage. Unbounded counters
saturate at the minimum, where all larger values are language-equivalent; finite
maxima remain exact. No rounding, numerical cap or scope exception is introduced.
The [implemented design](../../design/xml-particle-ranges.md) documents semantics,
ownership, storage cost, rollback/diagnostics and an executed batch example.

The [current range report](P4-06-native-count-ranges.json) passes all **eight schemas
/ 16 DOM-reader rows**, with unchanged fixture hashes and attribution-specific
rejection of the ambiguous schema. The historical 14 failing requirements remain
in their original report. Min/max ordering is checked before absent-particle
removal, including unused groups, and XSD 1.0 all-group restrictions remain active.
Nullable and inherited particles retain exact original bounds without counting
empty iterations.

The final affected gate passes **106 Qore suites / 1,067 cases / 44,362 reported
assertions**, with no test warnings. The range suite passes **eight cases / 534
assertions** in AST, IR, JIT and tiered modes. The complete native finite-language
oracle again passes **1,000 models / 43,630 schema-document rows per mode**.
All **33 CMake provider/source-distribution tests** pass under CMake 4.3.0 with zero
compiler warnings. An eight-case DOM/reader range probe detects an incomplete
backport even when the prior attribution/counter checks pass; AUTO uses the
private fallback and SYSTEM rejects it. Reconfiguration preserves checked source
hashes and timestamps.

Counter arithmetic matches Python integers across **881 boundary cases**, two
lexical-equivalence pairs, 33 malformed lexical positions and five invalid
configurations. Private execution tests reach **80/81-digit boundaries**, finite
`INT_MAX`, distinct counter offsets, rollback, resets, diagnostic snapshots and
unbounded saturation. Allocation fixtures exhaust **six execution and six schema
bridge fault points**, plus the affected prior **229 checker / 15 executor**
fault points, with baseline ownership and successful fresh reuse. The final
expanded executor fixture was rebuilt and rerun after the complete provider gate.

Valgrind passes the range Qore suite and five standalone fixtures with **zero
memory errors, zero definite/indirect/possible losses and zero suppressions**.
Standalone fixtures free every heap block. The same isolated-core DWARF diagnostic
remains P9-owned; Qore retains 116,230 bytes in 46 LLVM/loader process-lifetime
blocks, with no lost allocation. Only Valgrind uses `QORE_PCRE2_NO_JIT=1`.
Affected native documentation, both executed design examples and all 15 survey
harness methods pass. No system installation or push was performed.

The entire both-version corpus reports are identical to P4-05: **2,411 baseline
rows**, source/input hashes, **293 coverage cases**, **144 failure records** and
all stage accounting. Strict coverage passes **130 descriptions / 1,260 message
directions**. The [validation inventory](P4-06-validation.json) records source and
runtime hashes, complete suite results and evidence paths. Logs use
`/tmp/wsdl-p4-06-`; provider artifacts are `/tmp/qore-xml-libxml2-test-9gmlk1wx`.

The [full audit](audits/P4-06-native-particle-ranges.md) resolves all 62 checks:
**20 Pass / 42 N/A / 0 Fail**. Main Qore remains clean and synchronized at
`cb90afb7b`; the remote XML bugfix at `c1403ef` is included. P4 now continues with
ordered WSDL conversion, field metadata and samples, including its four visible
compositor runtime failures. P5–P9 retain the full original scope, supported-platform
and mandatory Python/corpus/peer CI acceptance, and previously recorded P9
documentation diagnostics.

## P4-07 — Ordered terminal declaration projection (2026-09-10)

P4-06 is committed as `b77835e`. `XsdParticle::attributeElementNames()` now returns
one actual terminal declaration per ordered input child. Fixed boundaries retain
distinct same-name declarations; shared group references retain caller continuation.
Accepted empty content returns an empty list and rejected content returns `NOTHING`.
The [implemented design](../../design/wsdl-particles.md) documents the public
contract, executed invoice example and resource bounds.

Common zero/one/unbounded trees use automaton predecessor traces with cached
closures. General finite/shared graphs reuse memoized endpoint recognition and
reconstruct one witness through predecessor frontiers. Nullable repetitions use
positive progress; empty spans do not expand shared graphs. Numeric counts are
not expanded or rounded. All mutable state is call-local. This projection selects
declarations; value/nil/dynamic-type/wildcard validation remains with its consumers.

The final gate passes **107 Qore suites / 1,075 cases / 54,512 reported assertions**,
without warnings. The new attribution suite passes **eight cases / 10,150
assertions** in AST, IR, JIT and tiered modes, and against the freshly compiled AOT
WSDL module (**1,154 variants**). It covers fixed declaration identity, alternating
nested groups, reconstruction, exact finite gaps, huge nullable counts, all,
wildcards, 10,000 input names, a shared empty DAG, cancellation/reuse and four
concurrent callers using deterministic queues and bounded cleanup.

An independent complete marked-language oracle checks **1,000 generated models /
42,630 construction and declaration-projection rows per mode**. It compares exact
source-position paths for original and reconstructed graphs, including all finite
words and deletion/replacement/prepend/append mutations. There are 765 valid and
235 invalid schemas. Four deterministic 250-model batches, each bounded by 180
seconds, retain every expected row; no model or failure is skipped. This replaces
the insufficient aggregate AST worker deadline without changing runtime behavior.

Both-version survey and coverage reports differ from P4-06 only in the WSDL source
hash: **2,411 baseline rows**, original input/source hashes, **293 coverage cases**,
**144 visible failure records** and all stage accounting remain unchanged. Strict
coverage passes **130 descriptions / 1,260 message directions**. All 15 survey
harness methods, affected WSDL documentation and two executed design examples pass.
The [validation inventory](P4-07-validation.json) records source/binary hashes,
complete suite summaries and per-mode oracle results. Logs use `/tmp/wsdl-p4-07-`.
No native source or binary changed, so no new Valgrind run was required. Normal
PCRE2 JIT remains enabled; no system installation or push was performed.

The [full audit](audits/P4-07-ordered-terminal-projection.md) resolves all 62 checks:
**19 Pass / 43 N/A / 0 Fail**. Both remotes were fetched. Main Qore was fast-forwarded
from `cb90afb7b` to **`95bdf29f4`**, the ProviderIndex deferred-initialization fix;
XML's remote `c1403ef` is already included. The isolated tested core remains
identified by its unchanged binary hash. P4 continues with actual ordered value
conversion, independent field cardinality metadata and particle-driven samples;
its four compositor runtime failures remain visible. P5–P9 retain the full original
scope, including mandatory Python/corpus/peer CI, supported platforms and the
previously recorded documentation/debug-information diagnostics.

## P4-08 — Ordered child value conversion (2026-09-10)

P4-07 is committed as `09f5f68`. Complex-content decoding now matches the complete
ordered child-name word before projecting native fields. Each position uses its
selected terminal declaration and converts one occurrence without mutating shared
limits. Alternating groups, repeated list-valued/nil children, shared group
continuations and extension ordering retain the existing native field contract.
Ambiguous direct local names require expanded identities; malformed names, empty
occurrence lists and unknown XML metadata are rejected. SOAP transport parsing
preserves order, and optional inner content no longer makes a required wrapper
optional.

Retained `XsdXmlValue` validation checks decode/encode constraints per child and
attribute while preserving original lexical text and order. A copied namespace
registry belongs to a thread-local validation scope restored on exit. Custom
encode checks remain active, with native reuse after failure and four concurrent
callers covered. All four compositor runtime negatives are now correctly rejected.
The original `SoapUiReq_1` remains unchanged and is tested as invalid: its extension
members are out of order and its `issue3367` wrapper lacks required `i3367`. A
separately identified derivative fixes only those two defects for the existing
value assertions; provenance is recorded in the README.

An AOT prerequisite surfaced when `XsdParticle::concatenate()` invoked its private
typed-list constructor from `XsdComplexType` with member operands. The constructor
was present but runtime overload selection used the unrelated caller's class.
Qore **`72890415a`** records/restores the lexical class at constructor dispatch,
including null global context. It was committed to main Qore `develop`, which is
clean; nothing was pushed. Its full audit has **18 Pass / 44 N/A / 0 Fail**.
All 13 affected core suites pass (nine QUnit suites: 83 cases/319 assertions, plus
four standalone regression scripts), including AST/IR/JIT/tiered, stripped AOT
O0/O3, access denial, exceptions/reuse and child Programs. The isolated debug
runtime was synchronized with current native sources, including upstream container
retyping/deferred-constant fixes; its git-version string identifies the old snapshot,
so the inventory also records source parity and the actual tested binary hash.

The final XML gate passes **108 suites / 1,087 cases / 54,665 reported assertions**
without warnings. Per execution mode, particle values, XML consumers and element
collisions pass **33 cases / 706 assertions**. The independent matrix checks
**248 rows / 124 input verdicts / 112 outputs per mode**, covering original and
reconstructed schemas, actual SOAP 1.1 and 1.2 bindings, both directions, exact
native values and retained lexical order. The AOT WSDL build contains **1,157
variants**, and its value suite passes **11 cases / 107 assertions**. That suite
and the reduced core constructor scenario both have **zero Valgrind errors and
zero lost bytes**, without suppressions. Qore debugging is enabled, signals are
disabled for tests, and PCRE2 JIT is disabled only for Valgrind. Affected docs and
three executed design examples pass; the survey harness has 15 passing methods
and the compositor harness has two.

The both-version baseline has **2,443 rows**, with all original input/source hashes
preserved and no formerly passing-stage regression. **32 decoding failures now
pass**; their newly reachable native serialization failures remain visible. The
full coverage ledger still has **293 cases / 144 failures**, and strict coverage
passes **130 descriptions / 1,260 directions**. Exactly 64 failure records move
from decode to serialize: 44 P4, 16 P5, and four original P2 primary labels for
`MixedComplexContent`, whose runtime ownership was already explicitly assigned
P5. Current stage accounting has **860 unassessed value/infoset directions**.
The strict aggregate worker initially exceeded its unchanged 60-second deadline
under concurrent gate load. The complete unchanged command passed in isolation
in 66.316 seconds including validators; no timeout, filter, case or criterion
was changed. Both attempts remain in `/tmp/wsdl-p4-08-` logs.

The [inventory](P4-08-validation.json) records complete suite summaries, mode and
oracle counts, source/binary hashes, changed failure stages and the core commit.
The [full XML audit](audits/P4-08-ordered-value-conversion.md) resolves all 62 checks:
**19 Pass / 43 N/A / 0 Fail**. The known 22 broad documentation diagnostics and
GCC/dependency debug-information diagnostics remain explicit P9 work. No install
or push was performed. P4 continues with native particle serialization, independent
field-cardinality metadata and particle-driven samples; P5-P9 retain the complete
original scope.

## P4-09 — Exact occurrence metadata (2026-09-10)

P4-08 is committed as `6ebdd39`. `XsdParticle::getElementOccurrenceRanges()`
now exposes exact named-element minima/maxima for the complete accepted language.
Sequence sums, choice extrema (including absent fields), repetition products,
optional all-groups and shared group references use decimal integer arithmetic.
Impossible languages differ from accepted empty content, and zero-count
declarations contribute no component. Wildcard positions are excluded from named
field counts. The child-before-parent graph is summarized once without expanding
numeric counts or shared definitions; the implemented bound is `O(mk)` map work
and storage plus digit-dependent arithmetic.

Complex provider fields derive requiredness, scalar/list shape and repeated enum
choices from these bounds. A field common to every choice alternative can be
required; separate uses of a shared optional/repeated group do not contaminate
another type's metadata. Expanded-name collisions retain separate fields. Item
validators, attributes and reconstructed types/providers retain their existing
contracts. The bounds are extrema, so complete particle checks still enforce
field correlations, order, exclusivity and unattainable intermediate counts.

The new tests exposed a prerequisite in Qore: an absent optional soft list was
dispatched to the item validator as a single missing item. Main Qore commit
**`f1dd175f0`** fixes missing collection/default dispatch while preserving explicit
NULL and missing-valued item validation. Its 62-item audit resolves **20 Pass /
42 N/A / 0 Fail**. Nine core checks pass **75 cases / 2,875 assertions**, including
the new **5-case / 129-assertion** regression in all four execution modes. An
explicit compiled-module run also passes 5/129. The isolated DataProvider-qmod
target was rebuilt with the exact changed source and contains **2,117 variants**;
the six directly related classes and all five existing provider suites match main
Qore sources. No C++ source changed, and the libqore/native XML hashes are unchanged.

XML validation passes **109 suites / 1,098 cases / 54,884 reported assertions**
without warnings. The occurrence suite has **11 cases / 219 assertions**, covering
both actual SOAP bindings and directions, original/reconstructed providers,
repeated enum choices, huge/unbounded limits, a `2^70` shared graph, malformed
graphs, cancellation and concurrent reuse. Per AST/IR/JIT/tiered mode, three
affected Qore suites pass **28 cases / 402 assertions**. Independent complete
languages check **1,000 models / 2,530 rows per mode** (765 valid models, 235
required schema rejections). The existing value matrix also passes **248 rows /
124 independently assessed inputs / 112 outputs per mode** with lxml and Xerces.
The compiled WSDL module contains **1,162 variants** and passes 11/219.

Both-version survey preserves all **2,443 stage rows/verdicts** and all original
source/input/catalog hashes. Strict coverage passes **130 descriptions / 1,260
directions** on its first isolated run. All **293 cases / 144 visible failures**
and stage accounting, including **860 unassessed value/infoset directions**, are
unchanged. Current reports only update runtime/source-version metadata. All 15
survey-harness methods, affected WSDL documentation, four WSDL design examples,
SoftList qdx extraction and its design example pass without warnings.

The [inventory](P4-09-validation.json) records source/artifact hashes and complete
gate/mode rows. The [full XML audit](audits/P4-09-occurrence-metadata.md) resolves
all 62 checks: **19 Pass / 43 N/A / 0 Fail**. Both remotes were fetched again and
had no additional commits; the previously pulled `95bdf29f4` Qore bugfix and XML
`c1403ef` remain included. No install or push was performed. No new Valgrind run
was required for these Qore-only changes; normal PCRE2 JIT remains enabled.

P4 continues with native serialization of complete ordered groups, removal of
legacy shared group field mutations, and particle-driven sample generation.
P5–P9 retain the full original scope, including the separately recorded broad
documentation and GCC/dependency debug-information diagnostics.

## P4-10 — Native particle emission (complete)

After P4-09 `bd57449`, native named-element emission now uses exact count-vector
allocation and ordered XML keys. The one-occurrence adapter retains shared
element limits and existing scalar/list/nil/type conversion. Complete attribution
selects each actual declaration before value conversion. The
[implemented contract](../../design/wsdl-particles.md#native-named-element-emission)
records canonical native behavior, the lossless `XsdXmlValue` alternative, exact
resource bounds and independent research. This increment does not close P4.

Greedy branch/count decisions fail when a suffix reserves an earlier choice's
name or attainable counts have gaps. The allocator deduplicates count vectors
in the compiled DAG, retains compact indexed witnesses, and bounds nonempty
iterations by supplied child count. Its general unordered state space is
explicitly exponential in distinct names; ordered matching retains its polynomial
bound. Nonadjacent same-name occurrences keep separate XML generator keys.

Audit reproduced and fixed a P4-09 ownership bug: with a zero-occurrence qualified
`a` beside an active unqualified `a`, provider field inspection used `delete` on
an inactive `XsdElement` in a temporary map and destroyed the shared object.
The fix uses `remove` and shares active declaration projection across provider,
encoder and decoder. `inactiveNames()` tests repeated metadata inspection,
original/reconstructed schemas, local/expanded fields, encoding, decoding and
object survival. The failing reproduction remains in
`/tmp/wsdl-p4-10-inactive-field.qr` and `.log`.

Final source SHA-256:
`a92e785c691589ca52407c703d9cc924ed488da9e40c5d6ac48c19dc4d80625e`.
The [validation inventory](P4-10-validation.json) and
[complete audit](audits/P4-10-native-emission.md) record:

- 110 suites, 1113 cases and 56270 reported assertions, with no warnings or failing
  cases. The three pre-existing caught SOAP comparator negatives remain intentional.
- Four affected suites pass 43 cases/1787 assertions in each execution mode;
  the final new suite contributes 15 cases/1385 assertions in all four modes.
  Shared group continuations, wildcard ordering, 600 ordered children, huge
  counts, interruption and four synchronized callers are covered.
- The independent finite-language oracle checks 1000 models and 15132 rows per
  mode, including all original/reconstructed probes and 235 required schema
  rejections. Both actual SOAP bindings and both directions pass the 248-row
  value matrix with 224 independently valid retained/native outputs per mode.
- AOT compiles 1173 variants and the explicit compiled module passes 15/1385.
  All five particle design examples, 15 survey-harness methods, two compositor
  context methods (including the former nested-choice failure) and affected
  API documentation pass without warnings.
- The both-version survey preserves all 2443 row identities and original
  provenance. Twenty-two emission failures and four SequenceChoice output-order
  failures now produce valid XML. Two P5 dynamic-type failures only change
  diagnostics. Serialization failures fall from 34 to 12 and rejected outputs
  from 34 to 30; no valid-input/invalid-output row remains in this diagnostic.
- Strict coverage passes 130 selected descriptions/1260 directions on its first
  isolated final-source run. Broader failures decrease from 144 to 92. The
  904 explicitly unassessed value/infoset directions include 44 newly reachable
  outputs; they are not counted as successful value-preservation checks.
- All 62 audit items are resolved: 19 Pass, 43 N/A, zero Fail. No C++ source
  changed and native XML/libqore hashes are unchanged, so no new Valgrind run
  is required. Normal PCRE2 JIT remains enabled.

Final logs use `/tmp/wsdl-p4-10-final-*`. The focused `serialization-complete`
mode records supersede the first 14-case AST serialization run after shared-group
and wildcard tests were added. Earlier `verified-*` runs predate the inactive-field
fix and are diagnostic evidence only. Both current reports are updated; original
fixtures, findings and provenance remain unchanged.

The existing builtin `^type^` wrapper failure remains explicitly assigned to P5:
selecting an identical builtin type is rejected by the base
`XsdAbstractType::checkExtends()`, including through the unchanged legacy public
`serializeValue()` reproducer. The [finding](p5-native-type-wrapper-finding.md)
retains the normative identity rule and failure; it is not a passing expected
rejection. The P4 wrapper test uses the supported complex-type path.

Both origin/develop branches were fetched and are already contained locally.
Main Qore is clean at `f1dd175f0` (ahead two); no Qore change was needed in P4-10.
No push or installation was performed. The unrelated `test/cmake/__pycache__/`
directory is not staged. Next work is P4 sample generation, removal of legacy
shared group occurrence mutation and phase acceptance. P5-P9 retain their full
scope, including the recorded broader documentation/debug-information findings.

## P4-11 — Bounded structural sample selection (complete)

After P4-10 `b1f38c4`, `XsdParticle::getSampleElementNames()` selects a complete
structural example within explicit nonempty-repetition and total-child budgets.
Shortest and preferred words are computed once per compiled graph node. Required
suffixes reserve capacity; repetitions retain complete groups; nullable terms can
satisfy huge minimum counts with empty iterations. Choices, all groups, namespace
wildcards and shared references have defined behavior. No shared declaration is
modified, and generation errors are distinct from schema rejection. See the
[implemented API, shipment example and bounds](../../design/wsdl-particles.md#bounded-structural-examples).

The helper baseline `/tmp/wsdl-p4-11-sample-before.qr` demonstrates the remaining
integration problem: a batch requiring two quantity/note pairs is generated as
one pair because `WSMessageHelper` reads flattened fields. The complete-particle
validator correctly rejects it. This primitive is independently usable and tested;
the next P4 increment connects it to native samples and removes legacy shared
group count adjustments. P4 remains open.

Final source SHA-256:
`5e0627f9524ac8fabeaea9fdcee6bc046cb5eb41aa6bd2476dd7f362b6086fb4`.
The [validation inventory](P4-11-validation.json) and
[62-item audit](audits/P4-11-bounded-samples.md) record:

- All four modes pass 10 sample cases/190 assertions and 19360 independent rows:
  765 valid models, 235 schema rejections, 12852 successful original/reconstructed
  samples and 5508 exact budget/language generation rejections per mode.
- Sixteen existing suites pass 304 cases/16420 reported assertions. The existing
  three caught SOAP comparator negatives remain intentional. The survey harness
  passes all 15 methods. No test warning or failing case remains.
- AOT compiles 1180 variants and its explicitly loaded artifact passes 10/190.
  The new shipment example and affected WSDL/module docs pass without warnings.
- All 2443 survey rows and the complete isolated strict ledger retain their prior
  outcomes and provenance. All 130 selected descriptions/1260 directions pass;
  92 broader failures and 904 unassessed value/infoset directions remain visible.
  Current reports change only their WSDL source hash; stale README ledger counts
  are corrected to match them.
- All 62 audit checks pass or are individually not applicable: 19 Pass, 43 N/A,
  zero Fail. No C++ source changes; native XML/libqore hashes are unchanged, so
  no additional Valgrind run is needed. Normal PCRE2 JIT remains enabled.

Final logs use `/tmp/wsdl-p4-11-final-*`. The strict gate starts from deterministic
process completion after the remaining checks and runs in isolation. Early
`first`/`second` logs are diagnostic development runs, not final acceptance.
Both remotes were fetched and are already included. Main Qore is clean at
`f1dd175f0`; nothing was installed or pushed. P5-P9 and the tracked builtin type
wrapper identity defect retain their complete scope.

## P4-12 — Complete native helper samples (complete)

After P4-11 `f687c55`, normal `WSMessageHelper` samples use complete particle
schedules, canonicalized and attributed exactly as native serialization before
values are generated. Repeated groups retain every member, XSD list children
retain occurrence boundaries, and typed complex parts include children and
attributes. Active graph declarations provide consistent namespace aliases and
schema field order across providers, encoding, decoding and examples. Group
finalization no longer mutates shared element occurrence limits.

The positive integer `max_elements` option defaults to 10000 per message part,
including the root and nested children. Construction reserves positions before
callbacks; converted output is counted before return, including whole override
values and embedded fragments. The latter closes an audit reproduction where
a five-element override passed a two-element budget. Root/reentrant contexts
restore on failure/interruption; public nested overrides and exactly-once root
validation remain intact. Recursive types terminate with permitted empty content
or raise a precise sample error. No instance is truncated. See the
[implemented contract and executed shipment example](../../design/wsdl-sample-instances.md#complete-groups-and-bounded-construction).

Final source SHA-256: `30deed41e0db35384ed2d9a1ba2b502c9662112020bc781acf2290cad90f4548`.
The [inventory](P4-12-validation.json) and
[62-item audit](audits/P4-12-helper-particles.md) record:

- 111 suites: 1133 cases/56558 reported assertions; the final seven added fragment
  assertions raise the composed final count to 56565. Existing caught SOAP
  comparator negatives remain intentional; no failing case or warning remains.
- The final 19-case/243-assertion sample suite passes all four source modes and
  explicit AOT. The 1186-variant qmod, affected docs, shipment example and all
  15 survey harness methods pass without warnings.
- Each mode passes 1000-model/15132-row independent ordering coverage, 248 value
  rows/224 validated outputs, and 208 sample rows/352 validated outputs. All 32
  expected sample errors request insufficient budgets. Both actual bindings,
  directions, reconstruction and comments are included.
- All 2443 diagnostic rows and strict ledger outcomes remain unchanged. The first
  isolated final-source strict run passes 130 selected descriptions and 1260
  directions; 92 broader failures and 904 unassessed value/infoset directions
  remain visible. Original fixtures and historical findings are untouched.
- All 62 audit items resolve: 19 Pass, 43 N/A, zero Fail. No C++ change or native
  artifact change; no new Valgrind run, PCRE2 JIT disablement, install or push.

Final evidence uses `/tmp/wsdl-p4-12-final-*`; the final five-mode supplement
supersedes earlier sample rows after seven fragment assertions were added with
no production change. Development `preaudit` and `audit` runs are superseded.
Strict coverage starts from deterministic process completion after the gates.
Both develop remotes were fetched and already included. Main Qore's concurrent
AOT closure changes are preserved; this increment changes no main Qore files.

P4 remains open. The [worker finding](p4-worker-order-finding.md) proves that
24 remaining P4 failures come from the diagnostic caller's unordered XML hash.
The next increment fixes that caller and expands strict value/order acceptance
for all 13 P4-owned families. P5-P9 retain their complete required scope.

## P4-13 — Ordered corpus and P4 acceptance (complete)

After helper integration `e8ea3b6`, the corpus worker now uses the ordered XML
hash required by `WSOperation`. The reduced repeated-pair worker test fails
before that parser flag and passes after it in both actual SOAP bindings and
directions, while wrong/missing group members still fail for the intended
reason. This closes the [24-direction caller finding](p4-worker-order-finding.md)
without reordering invalid input or changing any original fixture.

The strict selection now covers every message in all 13 P4-owned families.
Complete element/string observations preserve expanded names, attributes,
occurrence counts and values. The native contract retains order within each
field; the retained XML contract compares original interleaving. Empty complex
containers and exact string whitespace are distinct. Mutations demonstrate
that lost/extra nodes, changed values/names/attributes and changed occurrence
order cannot pass. The iterative predicate handles 2000 nested containers.

The [validation inventory](P4-13-validation.json) and
[62-item audit](audits/P4-13-particle-acceptance.md) record:

- 18 Qore suites pass 333 cases/16941 reported assertions, with no warning or
  new failing case. Existing caught SOAP comparator negatives remain intentional.
  Three reference tests and all 16 worker-harness methods pass.
- Each of AST, IR, JIT and tiered execution passes 240 original/reconstructed,
  request/response corpus rows. Eight rows reject invalid source content through
  both APIs; all 696 native/retained outputs independently validate and preserve
  their required values/order. Every original WSDL, inline schema and message
  digest is verified. SOAP 1.2 derivative descriptions change only the binding
  extension namespace, with exact hashes and actual binding identity recorded.
- The 2455-row survey preserves every previous successful row. Twelve unordered
  decode failures become successes with 12 new independently valid outputs.
  The original source hashes and historical findings are unchanged.
- The final isolated strict gate passes 142 selected descriptions/1376 directions.
  All 120 P4 directions pass their requirements: 116 valid values and four
  required source rejections. Broader failures fall from 92 to 68, removing only
  the 24 P4 decode failures. No P4 failure remains; 812 broader value/infoset
  directions remain explicitly unassessed.
- Coverage unit tests retain exactly the two previously routed P6 selected-binding
  assertions. Their failures stay visible and are not counted as passes. The
  expanded strict-count assertion is updated and passes; a misspelled runner
  filename is corrected to the existing provider suite, which passes.
- All 62 audit items resolve: 16 Pass, 46 N/A, zero Fail. WSDL source, compiled
  WSDL, native XML and libqore hashes are unchanged from P4-12. No C++ changes,
  additional Valgrind run, rebuild, install, PCRE2 JIT disablement or push.

P4 acceptance is complete across its implementation increments:

| Required behavior | Implemented evidence |
|---|---|
| Ordered nested sequence/choice/all/group graphs and exact limits | P4-01 through P4-07; `wsdl-particle-model`, matching, ambiguity and attribution suites; implemented bounds in `design/wsdl-particles.md` |
| Complete matching, declaration selection and ordered value conversion | P4-08; `wsdl-particle-values`, independent finite languages, both bindings/directions and reconstructed schemas |
| Requiredness/occurrence metadata without mutating shared declarations | P4-09 and P4-12; exact provider ranges, reusable groups and optional collection runtime prerequisite `f1dd175f0` |
| Complete native group emission and lossless ordered instances | P4-10 and P4-13; count-vector allocation, retained XML, 1000-model ordering oracle and every owned corpus message |
| Bounded valid samples and clear generation failures | P4-11/P4-12; complete structural words, total-element budgets, callback/reentrant scopes and independent example outputs |
| Negative/boundary/adversarial behavior and documented resource bounds | Model/matching/attribution/occurrence suites cover empty/finite/unbounded/huge counts, wrong order, incomplete groups, ambiguity, cancellation and synchronized callers; no exponential derivation backtracking |

Logs use `/tmp/wsdl-p4-13-final-*`; the inventory distinguishes the corrected
runner diagnostic and the two retained P6 failures. P5 is next, including the
[builtin wrapper identity finding](p5-native-type-wrapper-finding.md), full
wildcard/mixed/dynamic/nil semantics and the already tracked wildcard example
failure. P6-P9 retain their complete agreed scope and outstanding environment/CI
requirements. Concurrent main Qore development remains untouched.


## P5-01 — Native type identity and annotation ownership (complete increment)

Parent: `ca181ff` (P4 acceptance). P1-P4 remain complete; P5 is now in progress.
The [native wrapper finding](p5-native-type-wrapper-finding.md) is resolved for
component identity. Full P5 derivation, substitution and content acceptance are
still required; no broader capability is declared complete by this increment.

### Root causes and implemented behavior

- The abstract compatibility check rejected the declaration's own simple type.
  Identity now accepts the same resolved object and equivalent canonical XSD
  builtin definitions across namespace registries; custom conversion classes and
  foreign user components are not equated merely by name. Equivalent builtins
  normalize to the declaration before ordinary conversion/count checks.
- Element form incorrectly selected the namespace of `xsi:type`, and delegated
  converters could overwrite the selected annotation. Owned type namespaces are
  translated into the caller's output registry; metadata merges retain other
  attributes, comments and occurrence/value boundaries. Anonymous simple types
  cannot emit their base/member as their own type; existing scalar `anyType`
  inference keeps its runtime annotation.
- Annotated complex simple content nested a value hash inside `^value^` and
  failed XML generation. The scalar and lexical bindings now contribute directly
  to the containing complex element, which owns its type annotation.
- Complex selection compared extension local names and validated base attributes
  before dispatching an explicit type. Direct extensions compare resolved bases;
  wire QNames resolve in the instance scope before derived attributes/content are
  checked. Unknown, malformed, unbound and incompatible selections fail with the
  deserialization error category. Scoped namespace state is restored on failure.

Normative references: XSD 1.0 Structures [simple type identity, clause 1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-derived-ok),
[complex derivation and its component-identity note](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-ct-derived-ok),
[Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
and section 3.14.7 builtin definitions; second-edition errata were consulted.
The [implemented design](../../design/wsdl-type-selection.md) describes the
native component contract, annotation ownership, namespace allocation and bounds.

### Final verification and audit

The [inventory](P5-01-validation.json) and [62-item audit](audits/P5-01-type-identity.md)
record 19 Pass / 43 N/A / 0 Fail and exact hashes/commands:

- Full Qore gate: 112 suites, 1144 cases, 56907 reported assertions; no warnings.
  Three pre-existing, intentionally caught SOAP comparator negatives are recorded
  within their successful suite and are not new failures.
- Focused identity suite: 11 cases/342 assertions in AST, IR, JIT, tiered and AOT.
  Tests include scalar precision, named/anonymous types, list/union/occurrence
  boundaries, nil, complex/simple content, same-local-name collisions, derived
  required attributes, invalid instance QNames, cancellation and synchronized reuse.
- Final independent matrix: 224 rows, 72 required errors and 416 validated outputs
  in each of the four source modes plus compiled WSDL. Actual SOAP 1.1/1.2 bindings,
  both directions, reconstruction and post-error reuse are covered. Same-element
  QName collisions remap both type and instance prefixes without changing values;
  prefix spelling alone is not a conformance failure. Non-QName cases also force
  low-level annotations; complete XML APIs handle QName namespace allocation.
- 1189-variant AOT build, affected docs, executed invoice example, 16 survey harness
  tests, complete QName context matrix and independent particle-value matrix pass.
  Native XML/libqore hashes are unchanged; no C++ edits, new Valgrind run or install.
- Both-version survey: all 2455 original current rows/counts unchanged. Isolated
  strict ledger: all 142 descriptions/1376 directions retain their passing selected
  outcomes; 68 broader failures remain unchanged. Value accounting remains
  1264 ok / 0 failed / 196 unreachable / 812 unassessed / 0 missing / 0 skipped.

The initial supplementary runner allowed only 240 seconds for a broad QName test
whose recorded acceptance runtime was about seven minutes. That runner timeout
and the dependent gate's missing inventory are preserved as failed orchestration,
not passes. The corrected aggregate limit is 900 seconds, with unchanged internal
300/180-second child limits; the final test passes in 360.851 seconds. A misspelled
optional suite path was corrected and is superseded by the full 112-suite gate.

Both remotes were fetched and had no incoming commits. The main Qore checkout is
clean at `1c63ff2c5`, including the other developer's AOT module-lifetime fix and
our earlier `f1dd175f0`/`72890415a` fixes. This increment makes no main Qore edits
and performs no push. The isolated tested runtime remains identified by its
artifact hashes, independently of that concurrent main checkout update.

Next: retain/enforce per-schema and per-component `block`/`final` defaults and full
resolved type derivation, then complete the remaining P5 content/substitution/nil
and identity requirements. P6-P9, the known dual-binding diagnostic and broad
P9 docs/debug-info findings retain their full plan ownership.


## P5-02 — Type final exclusions and native defaults (complete increment)

Parent: `d223ed4` (P5-01). Source parsing now retains applicable per-schema
`finalDefault` and per-type `final`, including explicit empty overrides,
anonymous declarations, imported/included/chameleon sources and serialized
copies. The resolver checks restrictions, list items, composed union members
and complex/simple-content derivations against their actual resolved bases.
Canonical builtins keep their intrinsic controls; encoded array adapters retain
the enclosing component's metadata. Invalid tokens and prohibited anonymous
attributes fail with `WSDL-ERROR`. Metadata remains immutable after construction,
and source defaults restore on errors.

The [implemented design](../../design/wsdl-type-final.md) and
[specification evidence](type-final-evidence.md) document the XSD 1.0 mapping.
Normative Datatypes 4.1.2 filters irrelevant extension from simple defaults and
replaces nested unions with their actual member definitions. The non-normative
Structures duplication and independent-validator disagreements do not override
those rules. Original oracle verdicts and four output-only reference derivatives
are separately identified and hashed; disagreements are not conformance passes.

The native investigation found that libxml2 2.15.4 applies finalDefault only to
named simple types. The private build now initializes the anonymous branch with
the same three flags. Its generated source has checked input/output hashes; the
upstream archive/source stays unchanged. A 12-case behavior probe rejects the
uncorrected dependency, including backports with all preceding fixes. AUTO uses
the corrected private dependency, SYSTEM rejects a failing implementation, and
a fully corrected system backport remains usable.

The [validation inventory](P5-02-validation.json) and
[62-item audit](audits/P5-02-type-final.md) record **22 Pass / 40 N/A / 0 Fail**:

- Full gate: 114 suites, 1157 cases and 57498 reported assertions, no warnings;
  all preceding suite results are unchanged. Three caught legacy SOAP comparator
  negatives remain intentional within their successful suite.
- WSDL final tests: 10 cases/514 assertions in AST, IR, JIT, tiered and compiled
  WSDL. Native final tests: 3 cases/77 assertions in all four source modes.
  Cases cover metadata, imports/copies, empty/invalid/default controls, anonymous
  types, method distinctions, failed reuse and synchronized concurrent consumers.
- Final independent matrix: 87 schemas/174 actual SOAP 1.1/1.2 descriptions,
  438 rows, 86 required construction errors and 352 independently valid outputs
  in each of AST, IR, JIT, tiered and AOT. Originals/copies and both directions
  preserve exact typed values and expanded names. This supersedes the earlier
  86-schema mode matrix after one further negative fixture was added.
- 34 native provider tests pass. The native behavior probe, native final suite
  and 12-case/191-assertion reader schema cancellation/lifecycle suite pass under
  Valgrind with zero errors and zero lost blocks. Only Valgrind disables PCRE2
  JIT through `QORE_PCRE2_NO_JIT=1`; ordinary tests retain JIT.
- AOT builds 1194 variants (12149708 bytes). Affected WSDL/native docs and the
  executed invoice example pass without warnings. All 16 survey harness methods,
  union composition, attribute/simple-content values and prior type-identity
  matrices pass. The supplementary runner's nonexistent filename is preserved
  as failed orchestration, then corrected to the existing attribute-value suite.
- Both-version survey retains all 2455 rows and all previous counts. Isolated
  strict coverage retains 142 descriptions/1376 directions with zero selected
  failures. All 68 broader failures and 1264 ok / 0 failed / 196 unreachable /
  812 unassessed value directions remain unchanged. Only recorded WSDL version
  digests change; original sources and historical findings remain untouched.

Final WSDL SHA-256 is
`7827754908f1a91bf01b955283017458d0f779e73ee524013112e0712688f3a9`;
native XML is `6ce26fee5b3101eb20c7c59f763393770ea5325a80002cadaf4981c1380b33bb`.
The pinned isolated libqore artifact is unchanged. Logs use `/tmp/wsdl-p5-02-*`;
the inventory distinguishes final matrix/gates from superseded development runs.
Both develop remotes were fetched and already included. Main Qore remains clean
at `1c63ff2c5`; this increment changes no main Qore source and performs no push
or installation.

P5 remains in progress. Next: instance `block`/abstract controls and complete
resolved dynamic derivation, followed by substitution groups, wildcard/mixed/
generic content, nil/default/fixed and document identity acceptance. The known
P6 dual-binding diagnostic and P9 environment/CI/docs/debug-info requirements
retain their full ownership.


## P5-03 — Instance derivation, block and abstract controls (complete increment)

Parent: `460349d` (P5-02). Instance type selection now follows complete resolved
simple/complex derivation with effective block exclusions. Construction retains
source-scoped blockDefault and explicit empty overrides; global references retain
their declaration's block, abstract and nillable properties. Abstract selected
types and direct abstract element instances reject. Optional absent occurrences
create no instance. Direct type, element, native-wrapper and retained XML paths
share the checked expanded-QName selection.

The [implemented design](../../design/wsdl-type-substitution.md) and
[specification evidence](type-substitution-evidence.md) describe XSD 1.0 type
ancestry, fixed exclusion sets and annotation ownership. Worklists deduplicate
pairs on enqueue and cache base union lookups, including absence. Tests cover
1000-step complex/unrelated simple chains, 10000 repeated member references and
40 levels of shared union edges, with defensive termination on a mutated cycle.
No Debug-build performance claim is made.

The [validation inventory](P5-03-validation.json) and
[62-item audit](audits/P5-03-type-substitution.md) record **19 Pass / 43 N/A / 0 Fail**:

- 115 suites pass 1170 cases/57779 reported assertions with no warnings. The
  affected IEEE suite adds an unbound-prefix negative. Three caught legacy SOAP
  comparator negatives remain intentional within their successful suite.
- The new Qore suite passes 13 cases/280 assertions in AST, IR, JIT, tiered and
  compiled WSDL. It covers controls, QName errors, imports/copies, optional absent
  references, direct APIs, adapter metadata, failed reuse and synchronized consumers.
- The final matrix passes 104 schema/type cases (62 valid/42 invalid) in all five
  modes. Each mode has 832 actual SOAP 1.1/1.2 request/response rows, 336 required
  rejections in each conversion path and 992 independently valid outputs. Both
  pinned input validators agree. Exact native values and expanded names are
  asserted; nonidentical native selections must emit their type annotation.
- AOT builds 1210 variants (12315444 bytes); WSDL/native docs and the executed
  invoice example pass. Prior final-control and type-identity matrices, all 16
  survey harness methods, union composition and attribute/simple-content tests pass.
- The isolated both-version survey preserves all 2455 rows and every count.
  Strict coverage retains 142 descriptions/1376 directions with zero selected
  failures and all 68 broader failures. Values remain 1264 ok / 0 failed /
  196 unreachable / 812 unassessed / 0 missing / 0 skipped. Only WSDL digests change.

The initial broad gate exposed non-hash metadata access and missing namespace
context in detached probes/test fragments. Those causes are fixed and the final
full gate passes. A union probe now binds QName value prefixes, preventing a
selected boolean value from changing lexical form after detached validation.
IEEE and array test callers supply their actual enclosing output context;
unbound wire prefixes still fail. The first matrix's extra part-wrapper
expectation and malformed negative test-call references were corrected. All
superseded diagnostic failures remain identified separately from final passes.

Final WSDL SHA-256 is
`e8e08d237bd074dcf5eb0275dbb35534fe846090a610b1ca3b99e5ca3d59c959`.
Native XML and isolated libqore hashes remain unchanged. There are no C++ edits,
new Valgrind run, installation or push. Both remotes were fetched and already
included; main Qore remains clean at `1c63ff2c5`.

P5 remains in progress: native selected-type retention, element substitution and
final exclusions, wildcard/mixed/generic content, nil/default/fixed and document
identity requirements remain. P6-P9 retain full ownership, including the known
dual-binding diagnostic and platform/CI/docs/debug-info findings.


## P5-04 — Portable native type capture (complete increment)

Parent: `c0b4633` (P5-03). Explicit `preserve_types` decoding retains selected
types at element and WSDL type-part boundaries using `XsdQNameValue` in the
existing `^type^`/`^val^` wrapper. Saved values and receiving schemas can be
reconstructed independently. Output resolves the QName against its own schema
and repeats derivation, block, abstract, facet and content checks. Existing
component wrappers keep strict component identity; default native shapes are
unchanged. SoapClient call options and SoapHandler registration expose capture
explicitly. Conflicting XML/native representation choices reject before I/O or
registration. The [implemented contract](../../design/wsdl-native-type-values.md)
and [evidence](native-type-values-evidence.md) document the decisions.

The [validation inventory](P5-04-validation.json) and
[62-item audit](audits/P5-04-native-type-values.md) record **19 Pass / 43 N/A / 0 Fail**:

- 116 Qore suites pass 1187 cases/58265 reported assertions without warnings.
  Three caught legacy SOAP comparator negatives are intentional within their
  successful suite. Cargo, CDA and SOAP provider consumers remain in the gate.
- The new unit suite passes 17 cases/486 assertions in AST, IR, JIT, tiered and
  compiled WSDL/SoapClient/SoapHandler. It includes invalid receiver definitions,
  root/header/type-part boundaries, independent copies, nil/list/QName values,
  cancellation, synchronized consumers and 24 local HTTP calls.
- The 105-case matrix (63 valid/42 invalid) passes in all five modes. Each mode
  checks 840 actual SOAP 1.1/1.2 request/response/copy rows, requires 336 rejecting
  rows in both conversion paths and independently validates 1008 outputs with
  exact values and expanded names. Both pinned input validators agree.
- The original W3C TypeSubstitutionUsingXsiType example passes with capture:
  8 actual-binding/direction/schema-copy rows validate 2 original inputs and 24
  native/retained outputs, preserving part numbers, derived description and Part2.
  Original hashes are checked; the SOAP 1.2 derivative changes only the WSDL
  binding extension namespace and asserts the binding identity.
- AOT builds all three changed modules; the inventory records exact variant and
  byte counts. All three module documentation targets and the executed invoice
  example pass. Prior type substitution/final/identity, union composition,
  attribute values and all 16 survey harness methods pass.
- The isolated both-version corpus preserves all 2455 survey rows and every
  previous result except the WSDL digest. Strict coverage retains 142 descriptions/
  1376 directions, zero selected failures and 68 broader failures. Value counts
  remain 1264 ok/0 failed/196 unreachable/812 unassessed/0 missing/0 skipped.

Root-wrapper extraction and header flattening originally mishandled selected
native roots. The audit also caught incorrect wrapper acceptance in attribute
and simple-content text serialization. Wrapper handling now has a separate
WSDL type-part entry point, and eight negative scalar-context cases prevent
regressions. All boundaries are fixed and the full final gate was rerun.
A temporary reconstructed service exposed pre-existing weak operation/message dependencies. Its committed
source reduction and full P6 ownership are recorded in
[the lifetime finding](p6-operation-lifetime-finding.md); it is not counted as a
passing detached-operation test. Malformed test callbacks and temporary example
syntax were corrected before the final passing runs.

Native XML and isolated libqore hashes remain unchanged. No C++ edits, Valgrind
rerun, installation or push occurred. Both remotes were fetched and already
included; main Qore remains clean at `1c63ff2c5`.

P5 remains in progress. Next: native provider integration and sample/consumer
acceptance. Element final/substitution groups, wildcard/mixed/generic content,
complete nil/default/fixed and document identity remain required. P6-P9 retain
their full scope. The default diagnostic corpus still reports its native type
loss; explicit capture tests do not silently change that report's API choice.


## P5-05 — Native selected-type providers (complete increment)

Parent: `f41e327` (P5-04). Explicit schema/message provider factories validate
captured native type wrappers against receiving definitions, retain derived
fields and expose declared/wrapper metadata. Recursive graphs share definitions
and survive Serializable reconstruction with rebuilt identity indexes. Finite
choices compare unwrapped values with the existing scalar rules; QName choice
context is retained. Abstract examples select concrete definitions, and anonymous
metadata uses resolved components. The [contract](../../design/wsdl-native-type-values.md),
[evidence](native-type-providers-evidence.md), [inventory](P5-05-validation.json)
and [62-item audit](audits/P5-05-native-type-providers.md) record the implementation.

- 118 Qore suites pass 1203 cases/58850 reported assertions without warnings.
  Three caught legacy comparator negatives are intentional within the successful SOAP suite.
- The new unit suite passes 15 cases/521 assertions; HTTP integration passes
  1 case/64 assertions and 12 calls. All four source modes and AOT pass, including
  saved providers, both actual bindings/styles, metadata, choices, variants,
  recursive and anonymous definitions, negative selections, cancellation and concurrency.
- Each mode's independent 105-case matrix checks 840 rows, requires 336 rejecting
  rows in each conversion path and validates 1008 outputs. Original W3C type
  substitution passes 8 binding/direction/copy rows with exact values and Part2.
- WSDL and five dependent qmods build; WSDL/native documentation, compiled Cargo
  and CDA consumers, the executed invoice example and supplements pass. The
  inventory records module variants/bytes and full temporary asset staging.
- The isolated both-version corpus preserves 2455 rows and all previous counts
  except the WSDL digest. Strict coverage retains 142 descriptions/1376 directions,
  zero selected failures, 68 broader failures and unchanged value accounting.

All 62 audit items pass or are inapplicable: 27 Pass/35 N/A/0 Fail. Initial tests
and audit exposed nonpublic serialized helper classes, stale identity indexes,
missing QName comparator context and invalid abstract/anonymous metadata examples.
These causes are fixed; final gates were repeated after the fixes. Anonymous
nonidentity components reject before they can be advertised as selected types.
The initial Cargo AOT harness lacked bundled schemas; it now stages the existing
qmod and unchanged complete module assets. Superseded diagnostics remain distinct
from final passing evidence. No C++ edits, new Valgrind run, installation or push
occurred. Native XML and isolated libqore hashes remain unchanged. Both remotes
were fetched and included; main Qore is at `1c63ff2c5` with unrelated Azure/OpenAPI work in progress.

P5 remains in progress. Next: element final/substitution groups, followed by
wildcard/mixed/generic content, complete nil/default/fixed and document identity.
Binding/part-aware SoapDataProvider capture and sample integration belongs with
P6 message-shape work; the new datatype APIs and HTTP consumers are covered here.
P6-P9 retain full ownership, including operation lifetime and existing dual-binding,
platform, CI, documentation and debug-info findings. The legacy default corpus
still reports its type loss; capture tests do not silently change its API choice.


## P5-06 — Element affiliation and native substitution constraints (complete increment)

Parent: `725c1b2` (P5-05). Global element affiliations resolve by expanded name
after imports and includes. Forward and transitive omitted types inherit the
head's exact component; missing heads, cycles, incompatible types and final
exclusions fail at construction. Concrete membership applies head element
blocks and all intermediate complex type blocks. References keep their own
occurrences and refer to the global graph; failed additions restore published
membership. See the [implemented design](../../design/wsdl-element-substitution.md),
[evidence](element-substitution-evidence.md), [inventory](P5-06-validation.json)
and [complete audit](audits/P5-06-element-substitution.md).

- 119 Qore suites pass 1215 cases/59100 reported assertions without warnings.
  The three caught legacy comparator negatives remain intentional in their
  successful SOAP suite. New declaration tests pass 12 cases/250 assertions;
  new native tests pass 5 cases/168 assertions.
- AST, IR, JIT, tiered and AOT pass the declaration suite and both independent
  matrices. Each mode checks 72 schemas, 384 actual-binding/direction/copy rows,
  64 required construction errors and 320 independently valid exact-value
  outputs. The group matrix checks 62 maps and 102 documents over 31 groups.
- The independent checks exposed missing builtin restriction flags and a wrong
  extension-bit guard in libxml2. The private correction counts all methods.
  Four lxml and one Xerces verdict discrepancies remain explicit normative
  negatives, with specification and source/bytecode root causes recorded.
- The 45-schema configure probe and 35 provider tests check real broken/fixed
  system libraries, AUTO fallback, SYSTEM rejection, source hashes and stable
  reconfiguration. Native regression and full-probe Valgrind runs report zero
  errors and no lost blocks. The latter frees every allocation.
- WSDL and five dependent qmods plus WSDL/native documentation build without
  warnings. Compiled native-provider HTTP, Cargo/CDA and saved-provider tests,
  the executed quantity example, prior final/native-value matrices and all
  16 survey harness methods pass.
- The isolated both-version corpus retains 2455 rows and all prior counts,
  except the WSDL digest. Strict coverage retains 142 descriptions/1376
  directions, zero selected failures, 68 broader failures and unchanged value
  accounting. No corpus fixture or historical finding was modified.

All 62 audit items are recorded: 21 Pass/41 N/A/0 Fail. Native XML changes to
the rebuilt dependency; isolated libqore remains unchanged. Both remotes were
fetched and included. Main Qore is still at `1c63ff2c5` with unrelated
Azure/OpenAPI/MIME work in progress; this XML increment made no main-Qore edits,
system installs or pushes.

P5 remains in progress. Next: WSDL particle attribution for alternate member
names and selected root identity, then native/retained conversion, providers
and sample selection. Wildcard/mixed/generic content, complete nil/default/fixed
and document identity remain required. P6–P9 retain their full scope, including
binding/part-aware SoapDataProvider integration, operation lifetime, platform
and CI acceptance. Native XML substitution coverage does not hide the WSDL
corpus failures that require runtime member-name support.


## P5-07 — Child substitution particles (complete increment)

Parent: `09b3abc` (P5-06). Concrete member names now occupy their original
particle position with shared counts and one all-group slot. Conversion and
providers use the actual member declaration. Construction validates implicit
members for UPA and declaration consistency, including unused groups and models
affected by incremental additions; cancellation after publication restores
previous memberships. See the [design](../../design/wsdl-substitution-particles.md),
[evidence](substitution-particles-evidence.md), [inventory](P5-07-validation.json)
and [full audit](audits/P5-07-substitution-particles.md).

- The final 120-suite gate passes 1229 cases/60607 reported assertions without
  warnings. The three caught comparator negatives in the legacy SOAP suite
  remain intentional within a successful suite.
- The new Qore suite passes 14 cases/1507 assertions in AST, IR, JIT, tiered and
  AOT. Each mode also passes 53 schemas/310 documents/2586 rows, with 992 SOAP
  outputs and 58 standalone samples independently validated by pinned Xerces.
  Both actual SOAP bindings, directions and reconstructed graphs are covered.
- Tests exposed and corrected dropped present empty members, abstract-type
  sample selection despite available concrete members, and flattened SOAP
  extraction using head-only fields. Explicit and flattened inputs now preserve
  member values; emptiable records retain the enclosing message element.
- WSDL and four dependent qmods rebuild, the unchanged CDA target remains
  current, and WSDL documentation builds without warnings. All 13 supplement
  commands pass: compiled unit/provider/HTTP/Cargo/CDA consumers and matrix,
  prior declaration/final/native-value checks, native unit, the executed design
  example and 16 survey harness methods. No native code changed, so a new
  Valgrind run is not required; unchanged binary/source fingerprints are saved.
- The final both-version survey has 2457 rows. Strict coverage passes 143 WSDLs
  and 1384 directions, including all eight original SubstitutionGroup paths.
  Four broader deserialization failures are removed, none are added, 64 remain
  visible, and value/missing/skip failures are zero. The changed strict harness
  method passes; the separate known P6 dual-binding failure stays open.
- Supporting lxml/Xerces omissions remain explicitly adjudicated negative
  cases. The newly isolated pre-existing native EDC omission is a failed P5
  requirement owned by the next native increment; its complete schemas and
  unchanged native fingerprints remain in the linked finding and diagnostics.

All 62 audit checks are recorded: 19 Pass/43 N/A/0 Fail. Both origins were
fetched with no incoming develop commits. Main Qore remains at `1c63ff2c5`;
concurrent Azure/OpenAPI/MIME/RestSchemaActions/Serializable work was preserved.
This increment made no main-Qore edits, system installs or pushes.

P5 remains open. Next: native element-declaration consistency, followed by
selected substituted message-root identity, remaining wildcard/mixed/generic
content, complete nil/default/fixed behavior and document identity constraints.
P6–P9 retain every binding, protocol, attachment, platform and CI requirement.


## P5-08 — Native element-declaration consistency (complete increment)

Parent: `cc16263` (completed/audited P5-07). The private native dependency now
checks EDC after substitution resolution, including unused groups, imported
members, inherited particles and nested anonymous types. Per-model hashes and
visited graphs preserve declaration/type identity without expanding counts.
See the [design](../../design/native-element-consistency.md),
[root cause](p5-native-element-consistency-finding.md), [inventory](P5-08-validation.json)
and [complete audit](audits/P5-08-native-element-consistency.md).

- The final gate passes 121 suites/1237 cases/60736 reported assertions without
  warnings. The three intentional caught comparator negatives remain inside a
  passing legacy SOAP suite. Native tests pass 8 cases/129 assertions in all four
  source modes, including imported member/group conflicts and reader recovery.
- The new 43-schema independent matrix passes 25 valid documents, 18 required
  construction errors per parser and 50 retained original/reconstructed values
  in AST/IR/JIT/tiered/AOT. lxml's 18 EDC omissions and Xerces's eight unused-group
  omissions remain explicit normative negatives. The prior EDC suite passes
  both methods, including 30 schemas/60 bindings and both-direction consumers.
- Child-substitution matrices pass 53 schemas/310 documents/2586 rows and 1050
  independently validated payloads/samples per mode. Both native discrepancy
  entries from P5-07 have been removed after required rejection passes. All 13
  compiled/provider/HTTP/Cargo/CDA/previous-matrix/harness supplements pass.
- The 34-schema configure probe tests behavior without depending on our error
  text or code. All 38 distinct provider tests pass (the final 37-test gate plus
  the new corrected-library test with alternative diagnostics), covering AUTO
  fallback, SYSTEM rejection, corrected system use, hashes, idempotence and
  source distribution. All 69 allocation faults reject construction and clean up.
- Native unit, complete configure probe and allocation-test Valgrind runs report
  zero errors and no lost memory. The latter two free every allocation. Native
  docs build without warnings and the documented order/quantity example runs.
- The both-version survey and strict coverage are unchanged from P5-07: 2457
  survey rows, 143 selected WSDLs/1384 directions, zero selected/value/missing/skip
  failures and 64 broader failures retained. No corpus source or historical
  finding was modified.

All 62 audit checks are recorded: 19 Pass/43 N/A/0 Fail. Native XML changes to
its private dependency; the six existing WSDL/consumer qmods and isolated
libqore remain unchanged. Both origins were fetched with no incoming develop
commits. Main Qore's concurrent work was committed separately as `35dc29f31`;
this increment made no main-Qore edits, system installs or pushes.

P5 remains open. Next: selected substituted message-root identity, followed by
remaining wildcard/mixed/generic content, complete nil/default/fixed behavior
and document identity constraints. P6–P9 retain every binding, protocol,
attachment, platform and CI requirement.

## P5-09 — Selected complete-element and message-root identity

Parent: `3e122cf`. Complete schema elements and document SOAP body/header parts
now preserve concrete substitution roots through native values, retained XML,
providers, samples and Serializable reconstruction. The portable outer wrapper
uses `^element^` as an `XsdQNameValue` and `^val^` for the selected member value;
explicit selected types remain an independent inner wrapper.

The initial decimal-head/integer-member reproducer failed native/retained
conversion, retained providers and XML samples in both bindings despite correct
membership metadata. Every complete-root boundary now resolves and uses the
selected declaration. WSDL document parts use an iterative complete matching
with a linear ambiguity check; duplicate selected roots cannot overwrite body
or header parts. Ordinary declared roots retain their representation.

Expanded coverage also exposed and fixed explicit empty part presence, added
schema replay ordering and stale message type maps, provider alternatives after
schema additions, header owner ID zero, and actionless SOAP 1.2 member routing.
The HTTP fixture explicitly permits omitted actions. These root causes and the
independent witness method are recorded in
[substitution-roots-evidence.md](substitution-roots-evidence.md).

Final validation is recorded in [P5-09-validation.json](P5-09-validation.json):

- New unit suite: 12 cases/1357 assertions; HTTP suite: 2 cases/134 assertions,
  10 real exchanges through SoapClient, SoapHandler and SoapDataProvider.
- Both suites and the independent matrix pass AST/IR/JIT/tiered and compiled
  WSDL. The matrix covers 34 schemas/116 documents/996 rows and independently
  checks 816 outputs plus 44 samples in each mode, including member/type
  expanded names and typed values.
- All 16 compiled/consumer/previous-matrix/harness supplements pass, including
  Cargo/CDA, native providers, prior child substitution and native XML checks.
  Six module qmods and WSDL Doxygen documentation build without warnings.
- The 123-suite acceptance gate passes 1251 cases/62227 reported assertions
  without warnings. Three intentional caught comparator negatives remain in
  the passing legacy SOAP suite; per-suite results are retained in the inventory.
- Both-version diagnostic survey and strict coverage have exactly the P5-08
  results apart from the WSDL source fingerprint: 2457 survey rows, 143 selected
  WSDLs/1384 directions, zero selected/value/missing/skip failures, 64 broader
  failures retained. Corpus sources and historical findings remain unchanged.

The full 62-item audit is in
[audits/P5-09-substitution-roots.md](audits/P5-09-substitution-roots.md).
No C++ changed; native XML and isolated libqore fingerprints match P5-08.
Both origins were fetched with no incoming develop commits. Main Qore remains
clean at `35dc29f31`; this increment made no main-Qore edits, installs or pushes.

P5 remains open. Next: wildcard attribute and element instance processing,
ordered mixed/generic content, complete nil/default/fixed behavior and document
identity constraints. P6–P9 retain all binding, protocol, attachment, independent
peer, platform and mandatory-CI requirements.


P5-09 was committed locally as `a2ce739` (no push).

## P5-10 — Wildcard attribute instance processing (in progress)

Parent: `a2ce739`. The reduced `/tmp/wsdl-p5-10-attribute-before.qr` and its
log reproduce lost wildcard attributes and missing strict/lax instance checks.
`anyAttribute` was a broad legacy content flag (also set by element wildcards),
while the resolved namespace/processContents component was unused at runtime.
The new `test/wsdl-wildcard-attributes.qtest` first failed all four cases.

Current changes enforce the effective attribute wildcard independently of
child admission, resolve global attributes through a shared completed registry,
preserve expanded names and typed known values, and retain unassessed lexical
text/context using the existing XsdScopedLexicalValue. Namespace contexts and
serialized providers retain the registry. Ordinary attribute-map providers now
validate names and constraints as well as explicit native providers.

Initial unit coverage passes four cases/134 assertions. The affected 14-suite
run found one legacy SOAP diagnostic regression: native unqualified attribute
names supplied an uninitialized namespace string to XsdQNameValue. It was fixed
with an explicit empty namespace; the SOAP suite now passes. Other affected
suites passed. Provider reconstruction required a public Serializable registry
class; the new provider class also preserves validation through soft copies.

Next: imported/additional declarations and rollback, fixed/list/QName values,
namespace collisions and malformed native attributes, inherited wildcards,
XSD 1.0 section 3.4.4's wildcard-ID restrictions, provider metadata/soft variants,
both SOAP bindings/directions and HTTP, independent validators, all source/AOT
modes, full existing-suite/corpus gates, documentation and the 62-item audit.
No P5-10 commit has been made. No C++ or main-Qore changes, install or push.


P5-10 expansion: wildcard IDs now enforce XSD 1.0 section 3.4.4 clauses 5.1/5.2.
Imported same-local-name declarations, fixed values, failed additions and
reconstruction pass the initial expanded unit suite (7 cases/192 assertions).
The XML namespace URI needs the reserved `xml` output prefix; its omission
from the default prefix table was corrected. Malformed native names and XML
characters now reject with serialization errors. No new native C++ changes.

The independent 24-schema/192-document matrix is under development. It exposed
a separate pre-existing native libxml2 wildcard-ID reporting defect, root-caused
in [p5-native-wildcard-id-finding.md](p5-native-wildcard-id-finding.md) and assigned
to the next native increment P5-11. Pinned Xerces rejects all six required
negatives; lxml's omissions remain explicit. Native DOM/reader acceptance is
recorded as a failure, not conformance.

The first complete SOAP matrix also exposed empty wildcard-only element
provider requiredness. Empty complex content without required attributes now
retains its native NOTHING representation. Simple-content provider/field
selection also accounts for effective attribute wildcards. The current unit
suite adds simple-content/soft/provider cases; final source/compiled matrices,
HTTP tests, corpus checks, documentation and audit remain unfinished.

P5-10 implementation and acceptance are complete. The final unit suite passes
13 cases/302 assertions; the registry ownership suite passes 2 cases/17 assertions.
Native/retained HTTP consumers pass 4 cases/138 assertions and eight exchanges
per execution mode. The 39-schema/324-document independent matrix passes 2592
rows and 4248 independently validated outputs per mode. All three Qore suites
and the matrix pass AST, IR, JIT, tiered and compiled WSDL.

The audit found and corrected a provider-field admission bypass: a caller-added
field must still satisfy the effective wildcard and available declaration.
Required-field aliases now normalize before conversion, duplicate XML names
reject, metadata reconstruction is checked, and unassessed context includes
absence of a default namespace. The complete SOAP output namespace map is now
collected after body/header conversion in per-message state. Concurrent use,
cancellation, failed output, schema addition/rollback and saved-provider
publication/lifetime checks pass.

The final 125-suite regression gate plus the registry suite pass 1270 cases and
62684 reported assertions without warnings or errors. The legacy SOAP suite
still includes its three intentional caught comparator negatives. Six qmods and
WSDL Doxygen build cleanly. All 19 compiled/consumer/previous-matrix/harness
supplements and the compiled registry suite pass; the shipment example executes.

Both-version survey completes 2455 rows. Strict coverage now selects 144 WSDLs
and 1388 message directions, including the four original invalid
AnyAttributeOtherStrict cases. Those four previously accepted invalid messages
now reject correctly. Broader failures decrease from 64 to 60, with no added
failure; no selected, value, missing or skipped failures. Historical findings
and original corpus sources remain unchanged.

See [wildcard-attributes-evidence.md](wildcard-attributes-evidence.md),
[P5-10-validation.json](P5-10-validation.json), and the full
[62-item audit](audits/P5-10-wildcard-attributes.md). No C++ changed; native XML
and isolated libqore hashes match P5-09. Both origins were fetched with no incoming
develop commits. Main Qore remains clean at 35dc29f31, ahead one. No main-Qore
edits, installs or pushes were made.

Next is P5-11's independently reproduced native wildcard-ID reporting defect.
P5 then retains element wildcard processing, mixed/generic content, complete
nil/default/fixed and document identity semantics. All remaining P6-P9 criteria
remain required.


## P5-11 — native wildcard ID constraints

P5-10 was committed locally as `ccc7820`. P5-11 adds missing native wildcard-ID
reports, correct base-type ancestry and referenced-constraint evaluation.
The native unit passes 4 cases/627 assertions across AST/IR/JIT/tiered, including
schema errors, recovery, cancellation and concurrent readers. Independent tests
cover 180 documents and 100 ancestry schemas with explicitly adjudicated
supporting-validator discrepancies. CMake detects missing backports; all 40
distinct provider tests pass. The new native unit, full probe and all 30 injected
constraint-allocation failures pass Valgrind with zero errors/lost blocks.

The 127-suite gate passes 1,274 cases/63,311 assertions. All 19 compiled and
consumer supplements pass, native documentation builds without warnings, and
the shipment ID example executes. Both-version survey/strict reports exactly
match P5-10: 2,455 rows, 144 selected WSDLs/1,388 directions, no selected failures
and 60 broader failures. Original corpus sources and historical findings remain
unchanged. See [the evidence](native-wildcard-ids-evidence.md),
[validation inventory](P5-11-validation.json) and
[full audit](audits/P5-11-native-wildcard-ids.md).

An additional consumer Valgrind run found a Qore core error-cleanup cycle.
The isolated metadata case and a minimal program without XML reproduce it;
an acyclic error does not leak. This result is retained as a failure in
[p5-deserialization-cycle-finding.md](p5-deserialization-cycle-finding.md).
P5-12 must fix this independent core prerequisite before continuing XML content
work. Native P5-11 cleanup itself is verified. Both origins were fetched again,
with no incoming develop commits. Main Qore remains clean at `35dc29f31`;
no Qore edit, installation or push was made in this increment.

P5 still requires element wildcards, mixed/generic content, complete
nil/default/fixed semantics and document identity. All remaining P6-P9 criteria
remain required.


## P5-12 — failed deserialization graph cleanup

P5-11 was committed locally as `99565bb`. Its separately reproduced core cycle
is fixed in main Qore develop commit `0eb8abb81`. The index invalidates failed
objects while retaining all target references, then releases those references.
No incomplete user destructor is invoked; escaped references are deleted objects,
original errors remain available, successful identity is unchanged, and pending
interruption after a native/custom hook follows the same cleanup path.

The new core test passes six cases/94 assertions in AST/IR/JIT/tiered modes.
All 20 core checks pass 130 cases/1484 assertions. Fourteen Valgrind runs have
zero errors and no lost blocks, including the full wildcard metadata consumer
that previously leaked, HTTP/registry consumers and existing constructor/class
regressions. The known Debug DWARF-reader warning remains explicitly recorded.
The native build, ordinary tests and strict release-note table processing are
clean. The main checkout's three changed C++ files match the tested runtime.

All 127 XML suites pass 1274 cases/63311 reported assertions; the legacy SOAP
suite's three intentional caught comparator negatives remain. Nineteen AOT,
consumer, matrix, harness and example supplements pass. Both-version survey and
strict coverage exactly match P5-11: 2455 rows, 144 selected WSDLs/1388 directions,
zero selected failures and 60 broader failures. Both origins were fetched with
no incoming develop commits. No install or push was made.

See [core-graph-cleanup-evidence.md](core-graph-cleanup-evidence.md),
[P5-12-validation.json](P5-12-validation.json) and
[the complete XML audit](audits/P5-12-core-graph-cleanup.md). The separate Qore
commit contains its full 62-item native audit. Original failure evidence remains
in [the core finding](p5-deserialization-cycle-finding.md).

The next P5-13 native prerequisite is [strict wildcard instance-type assessment](p5-native-wildcard-type-finding.md).
A 24-document temporary prototype confirms the early missing-declaration check
prevents valid xsi:type assessment; moving that check after type resolution
matches the specification and Xerces while retaining negative outcomes.
P5 then retains element wildcard, mixed/generic, complete nil/default/fixed and
identity requirements. P6-P9 remain required; this increment is not phase closure.

## 2026-09-12 — issue #5452 port from 2.x

Completed equivalents of fb20cc8 and 3d07e70 using the existing ordered particles.
Native decode field order and explicitly empty required flat records are fixed;
source normalization only rewrites containers needing suffix merging. Original
34-assertion regression and 284-assertion expanded schema/SOAP cases pass.
128-suite gate, 13 mode/AOT/independent supplements, both-version corpus and
warning-free WSDL docs pass. See [evidence](element-order-port-evidence.md),
[inventory](element-order-port-validation.json) and [all 62 audit checks](audits/element-order-port.md).
The deployed Qore is 0eb8abb81. No push/install; concurrent main Qore work remains
outside this port. Next: fix the independently reduced schema-whitespace parser
finding, then finish P5-13 native wildcard assessment with phase-correct allocation
tests from the separate investigation. P5-P9 acceptance remains open.
