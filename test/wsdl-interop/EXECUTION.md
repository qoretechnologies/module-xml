# WSDL/SOAP implementation execution record

Copyright (C) 2026 Qore Technologies, s.r.o.

Execution started 2026-09-07 on `develop` at `c81b2db`, with a clean working tree.
The authoritative scope and acceptance criteria remain in [PLAN.md](PLAN.md).
P1 corpus/adjudication and P2 schema/representation acceptance are complete; P3 scalar work is next. No scope reductions or workarounds are approved.

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
