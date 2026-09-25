# WSDL/SOAP compatibility implementation plan

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: P1–P5 acceptance is complete under the approved explicit native-capture and retained-XML contracts. P5-22b adds complete typed corpus accounting and an exact-order P5 selection; see [P5 acceptance](P5-acceptance.md). The ordinary decoding default and its documented projection losses remain unchanged and separately reported. P6 binding/component acceptance is complete; see [P6 acceptance](P6-acceptance.md). P7 SOAP processing is in progress, followed by P8–P9; the recorded QName AOT stack issue remains assigned to P9 runtime acceptance.
See [EXECUTION.md](EXECUTION.md) for acceptance evidence and remaining implementation criteria.
Prepared 2026-09-07 after `cc13171` on `develop`.
Keep proposals here; put durable implementation details in `design/` only after implementation.

The objective is to close every finding in [findings.json](findings.json), resolve every recorded
validator disagreement, and test the WSDL/SOAP behavior the payload-only survey does not exercise.
The initial target is WSDL 1.1, XSD 1.0, and SOAP 1.1/1.2, including the module's advertised legacy
encoding and attachment features. WSDL 2.0 is a distinct future capability: the current parser does not
implement it, and no claim for it is included in this plan's completion criteria.

The numeric serialization fixes, eight W3C fixture families, regression suite, and diagnostic driver
are already committed. The baseline has 293 WSDLs and 568 SOAP 1.1 messages: 22 WSDL parsing failures,
58 decoding failures, one serialization failure, and 24 rejected plus three unassessed serialized
payloads. Of independently valid inputs, 52 fail decoding, one fails serialization, and 11 produce
invalid XML. The input oracle also rejects 52 messages and cannot assess six. These sets overlap;
they are stage counts, not independent bug counts or a compliance percentage.

## Approved optional transport scope

CXF's XML binding and JMS transports are outside this plan's transport implementation
scope by explicit user approval. Retain their binding/port metadata, keep supported
SOAP ports usable in mixed contracts, and reject selection of unsupported ports.
Implementing those transports is tracked separately in
[Qore #5454](https://github.com/qoretechnologies/qore/issues/5454). The required metadata and
selection behavior is implemented in P6-27; full transport execution remains deferred.

## Execution rules and phase boundaries

Implement phases P1 through P9 in order. Split a phase into small commits where necessary, keeping
each commit independently testable. Do not start implementing the next phase until the current
phase's required tests pass without warnings or errors. Known failures outside the current phase
remain in the diagnostic report and must not be counted as passing tests.

For every implementation commit:

1. Reduce the failing external example to a reproducible case and establish the relevant specification
   requirement. Add positive, negative, boundary, and integration tests that fail for the right reason.
2. Fix the root cause. Do not weaken validation, drop data, special-case fixture names, or add a
   compatibility workaround to make a test pass. Seek approval before any proposed workaround.
3. Run the new tests, affected existing suites, and both-version corpus survey. Compare expanded
   names and typed values as well as schema validity. Preserve every previously passing valid case.
4. Run `audit-changes` on the exact changes being committed, fix findings, rerun affected checks,
   and record every checklist item as Pass, Fail, or N/A with evidence.
5. Update API examples, release notes, current coverage, and implemented design documentation when
   appropriate. Commit only after these checks pass. Never force-push.

Qore tests use `%modern`, executable permissions, local module paths and relative `%requires`, and
run with `--enable-debug`. Use event/barrier completion and bounded timeouts for service tests, not
sleeps or polling. For any C++ work, verify the installed Qore prefix before configuring; use
`build-debug` with `LD_LIBRARY_PATH`, and run affected tests under valgrind with `qore -b --enable-debug`.
For performance checks use `build` only after verifying `CMAKE_BUILD_TYPE=Release`.

## P1 — Complete and adjudicate the reference corpus

**Deliverables:** a pinned, offline corpus and a requirement/status record for every WSDL and message.

- Inventory the original archive and both message versions. Preserve the original files and their
  checksums. Obtain the five missing import dependencies from authoritative sources, pin them, and
  resolve them locally through the cache/catalog. Follow all transitive imports.
- Verify WSDL wrappers and references, not only the separately supplied echo XSD. Investigate missing
  wrappers, the `ImportTypesNamesapce` spelling, and descriptions generated from whole-schema patterns.
  Keep any corrected test document as a separately named derivative with the exact correction recorded.
- Adjudicate all 52 oracle-rejected inputs, six unassessed inputs, and three unassessed outputs using
  the applicable XSD 1.0 text/errata and a second independent XSD implementation. Two agreeing tools
  support a finding but do not override the specification. Include signed zero, large integers,
  ENTITY/ENTITIES, `gMonth`, invalid content, and nondeterministic content models.
- Give every case a status: valid supported input; valid input requiring a fix; invalid source with
  evidence; or a reproducible validator defect. Resolve provisional classifications before closing P1.
  Invalid descriptions/messages get expected-rejection tests; validator limitations get a separate
  normative value assertion rather than silently losing coverage.
- Record request and response requirements independently. Bind each row to the actual inline schema,
  message part, port and binding. Pin representative CXF contracts listed in the README and all imports
  for the binding/protocol phases; no dependency on public service availability.
- Extend the report to count missing/skipped/unreachable stages explicitly, record expected exception
  kinds, and distinguish source defects from implementation failures. Add a strict test mode for an
  explicitly selected, adjudicated corpus; keep the broad diagnostic mode available.

**Acceptance:** every original file remains accounted for; no missing dependency or unclassified source
disagreement; deterministic offline runs; every valid failing case has an implementation phase and
reproducer. Test catalog resolution, missing resources, malformed manifests, worker failure/cancellation,
complete reporting, and both SOAP versions. Source defects cannot justify relaxing production parsing.

## P2 — Correct schema namespace, type, and attribute resolution

**Depends on P1.** Repair schema construction before expanding serialization behavior.

- Resolve QNames in the declaration's namespace context, including locally rebound/default prefixes,
  no-target-namespace schemas, and builtin types used as extension/restriction bases. Distinguish an
  absent namespace from an unrecognized prefix; never resolve a QName using an unrelated local-name match.
- Complete import/include/chameleon handling, cycles and deduplication. A chameleon schema included
  into two namespaces must acquire the correct types in each namespace rather than sharing the wrong
  cached component. Preserve exception-safe namespace/context restoration after failed resolution.
- Implement attribute references, anonymous simple types, default types, required/prohibited use,
  default/fixed values, and namespace qualification. Support attributes in simple-content derivations.
  Unresolved attributes must produce a schema error, not a method call on NOTHING.
- Honor element/attribute local `form` overrides independently of schema defaults. Cover global refs,
  qualified attributes, same-local-name components in different namespaces, and inherited declarations.
- Define and test the public data contract for information that current flat hashes/scalars lose:
  lexical form, expanded QName, dynamic type, ordered repeated particles, mixed text and wildcard nodes.
  First evaluate the existing `^type^`/`^val^` mechanisms. Document any necessary additive representation,
  how existing callers retain compatible behavior, and how SoapClient, SoapHandler, example generation,
  data-provider types and Serializable objects consume it. Do not silently change returned field types.

**Acceptance:** all adjudicated P2 schemas parse and referenced types/attributes resolve correctly;
wrong/unbound namespaces and contradictory declarations fail with specific errors; qualified/unqualified
output validates; failed parsing does not corrupt subsequent parses. Include imports in real WSDLs,
serialized/deserialized schema objects, data-provider field reporting, and nested/reused namespace tests.

## P3 — Separate lexical validation from values and preserve scalar correctness

**Depends on P2's type resolution and value-contract decisions.**

- Apply whitespace normalization and pattern facets to XML lexical forms at every derivation step.
  Apply numeric bounds, digit facets, and enumeration to the correct value space. Preserve valid lexical
  distinctions where serialization must satisfy a pattern (`009`, `9898.00`, dates, scientific notation).
  Merely moving a pattern check before conversion is insufficient if reserialization still fails it.
- Compare enumerations by the base type's value semantics: equivalent numeric spellings, booleans,
  dates, binary values, lists/unions, QName namespace identity, and NaN as defined by the datatype rules.
- Eliminate silent decimal and large-integer precision loss. Cover every signed/unsigned bound including
  `unsignedLong`, arbitrary-size integer derivations, and decimal output without exponent notation.
  Verify overflow/underflow and IEEE float versus double semantics, signed zero and special values.
- Validate scalar lexical input before permissive Qore conversion: booleans, integers, decimals,
  float/double, binary encodings, list items and unions. Cover empty input, trailing garbage, invalid
  booleans, invalid digits, whitespace, malformed base64/hex, and invalid union alternatives.
- Handle five-digit/negative years, absent versus explicit timezone, valid timezone bounds, fractional
  seconds, leap/calendar limits, durations and partial dates including `gMonth`. Root-cause the Qore date
  boundary; if the representation/parser requires C++ changes, make a separately tested Qore fix.
- Extend the XSD regular-expression checks for derivation, Unicode, subtraction, repetition and invalid
  expressions; ensure example generation returns a valid value or a precise unsupported-generation error.

**Acceptance:** every valid P3 input decodes and reserializes with the same required value and valid
lexical form; all invalid scalar inputs fail for the intended reason. Use independent validators plus
exact value/precision assertions so a schema-valid but changed number cannot pass. Exercise attributes,
elements, lists/unions, simple content, client/server requests and responses, and generated examples.

## P4 — Represent and process ordered schema particles

**Depends on P2. P3 must pass before implementation starts.**

- Replace the split/flattened sequence-element and choice handling with an ordered particle model that
  retains sequence, choice, all, group references, and occurrence limits at every level. Preserve schema
  order through extension/restriction and late resolution.
- Match and serialize groups as groups: absent optional groups, exact finite counts, unbounded counts,
  nested optional/repeated sequences, repeated choices with alternating alternatives, and empty groups.
  Keep `xs:all` semantics distinct from sequence order and enforce the XSD version's constraints.
- Preserve ordered instances when repeated particles share member names or contain different alternatives.
  Use the tested lossless representation from P2 where flat hashes cannot express the message.
- Make minimum/maximum occurrences, requiredness, and choice exclusivity apply to the complete particle.
  Do not emulate optional groups by marking every child independently optional, or repeated groups by
  raising each child's maximum. Update field metadata and sample generation consistently.

**Acceptance:** `SequenceChoice` emits the choice before `Cvalue`; every valid sequence/choice/group
fixture matches and round-trips in order. Reject missing group members, extra occurrences, wrong order,
mixed alternatives and ambiguous schemas. Include zero/one/boundary/unbounded cases and adversarial
nested inputs; matching must have documented resource bounds and avoid exponential backtracking.

## P5 — Preserve XML content and dynamic type information

**Depends on P2-P4.**

- Preserve expanded QNames in values and attributes, allocating/remapping prefixes only at output.
  Keep local declarations, shadowing, default-namespace resets and namespace identity intact.
- Preserve ordered wildcard elements and mixed text. Enforce `namespace` constraints and
  `processContents=strict/lax/skip`, including unknown declarations, other/no namespace, attributes,
  and inherited wildcards. Skipping schema validation must not lose XML information.
- Implement `anyType` and `anySimpleType` for empty, scalar, attributed and complex content with the
  correct representation. Handle default/fixed element values, nillability, absent versus empty versus
  nil, nil with content, and required attributes on nilled elements.
- Resolve substitution groups, abstract heads/types, valid `xsi:type` derivation and restrictions from
  `block`/`final`. Preserve the selected element/type so reserialization retains derived fields.
- Cover identity constraints where required by the advertised validation behavior: IDs/references,
  keys/uniqueness/keyrefs, and unparsed-entity constraints. Coordinate ENTITY/DTD conclusions with P1
  and the SOAP document restrictions tested in P7; do not enable prohibited SOAP constructs to satisfy
  a standalone XSD fixture.

**Acceptance:** all QName, wildcard, mixed-content, generic-type and substitution fixtures retain their
expanded names, values and order through request/response processing. Independently validate output
and compare the meaningful XML infoset; prefix spelling and formatting alone must not cause failures.
Invalid type substitutions, unresolved QNames, forbidden wildcards and invalid nil/content combinations
are negative tests. Include collisions between identical local names in different namespaces.

The native character-content prerequisite is implemented in P5-16a: empty CDATA
contributes no characters, element-only CDATA whitespace is assessed as text,
and default/fixed assessment preserves event ownership. See
[native evidence](native-character-content-evidence.md). This does not close the
WSDL declaration-level nil/default/fixed requirements above.

P5-16b validates element constraint declarations after final type resolution and
preserves their lexical/typed values and namespace context through references
and reconstruction. See [declaration evidence](element-constraints-evidence.md).
P5-16c implements receiving-element nil validation and ordered mixed conversion,
including native carriers, providers and actual SOAP consumers. See
[nil and mixed evidence](nil-mixed-values-evidence.md). Instance default/fixed
conversion and identity constraints remain the next P5 requirements.

P5-16e fixes private builtin particle layout/ownership and native empty-group
effective-content mapping; see [native anyType evidence](native-anytype-evidence.md).
P5-16f completes WSDL effective anyType inheritance and active inherited/group
wildcard metadata, including providers, saved schemas and both actual SOAP
bindings; see [inheritance evidence](anytype-inheritance-evidence.md). Instance
empty-element defaults and identity processing remain open. The approved API
policy keeps legacy decoding as the default and uses explicit `preserve_types=True` for native type retention; both corpus modes
must be reported separately, retaining legacy failures.

P5-17a implements native document ID/IDREF bindings with selected computed values,
validation-root owner identity, defaults, subtree isolation and checked cleanup.
See [native ID evidence](native-id-bindings-evidence.md). The corresponding
WSDL checks are implemented and verified in P5-17b below.

P5-17b implements WSDL ID/IDREF/IDREFS root closure from selected values,
including saved providers and both SOAP HTTP directions. Qore scope cleanup is
fixed by `c203380c4` and verified with immediate compilation on `8c0c22c15`.
The final 149-suite gate passes, and corpus runs resolve all 16
invalid identity corpus directions without changing the legacy preservation
default. See [WSDL ID evidence](id-bindings-evidence.md). Empty-element defaults,
key/unique/keyref and complete typed-preservation accounting remain P5 work.

P5-18a adds native canonical integer/decimal/boolean declaration checks, including
selected list/union values and all element/attribute constraint paths. This is a
prerequisite for empty-element defaults; instance PSVI/type adjudication remains
separate. See [native numeric constraint design](../../design/native-numeric-defaults.md).

P5-18b applies those declaration checks to WSDL construction and saved schemas,
preserving the original selected value through canonical reassessment, message
providers and both SOAP bindings. See [evidence](wsdl-canonical-constraints-evidence.md).
Float/calendar/binary canonical declaration spellings, empty-element defaults,
key/unique/keyref and complete typed-preservation accounting remain required.

P5-18c extends native canonical declaration checks to binary values, enforces
the XSD Base64 alphabet, and fixes binary/whitespace allocation-error propagation
and normalized-string buffer ownership. See [native binary design](../../design/native-binary-constraints.md).
P5-18d implements the corresponding WSDL binary canonicalization with preserved
selected octets, lexical carriers and saved providers; see
[evidence](wsdl-binary-constraints-evidence.md). Float/calendar canonical forms
and instance-default PSVI remain open.

P5-18e implements native IEEE conversion and canonical declarations, including
locale/rounding-state independence, complete exponent syntax and explicit
shortest-round-trip precision policy; see [evidence](native-ieee-constraints-evidence.md).
P5-18f implements the corresponding WSDL canonical capture, preserving original
IEEE values through saved schemas/providers and both SOAP bindings; see
[evidence](wsdl-ieee-constraints-evidence.md). P5-18g implements exact WSDL calendar canonical forms; see
[evidence](wsdl-calendar-constraints-evidence.md). The separately root-caused
[native calendar counterpart](p5-native-calendar-constraints-finding.md) is
resolved by P5-18h with exact owned year/fraction components, independent
reference checks and allocation recovery; see [evidence](native-calendar-constraints-evidence.md). Instance-default PSVI, remaining identity constraints
and typed accounting stay open.

P5-18i implements native canonical actual-type defaults, declaration-scoped
QName/NOTATION identity, checked type expansion and complete value-copy ownership;
see [evidence](native-element-defaults-evidence.md). The PSVI interpretation is
approved. WSDL default application and retained empty values, remaining identity
constraints and complete typed accounting remain P5 work.

P5-18j implements WSDL canonical actual-type defaults and `XsdDefaultValue`
empty-state preservation, with saved providers, independent instance/declaration
namespace scopes and both SOAP HTTP bindings. All 165 Qore suites and 18
supplements pass; see [evidence](wsdl-element-defaults-evidence.md). The separately
reproduced [NOTATION gap](p5-wsdl-notation-finding.md), key/unique/keyref and complete
typed-preservation accounting remain required before P5 can close.

P5-19a implements native NOTATION declaration, normalized-name and type-use
constraints, with allocation-safe content/ID handling and cached ancestry checks.
All 166 Qore suites, 65 provider tests and 13 supplements pass, including three
clean Valgrinds. Both decoding-mode corpus reports are unchanged; see
[evidence](native-notations-evidence.md). WSDL NOTATION declaration storage and
conversion remain next, followed by key/unique/keyref and typed accounting.

P5-19b retains WSDL notation declaration identifiers in a shared typed registry,
including normalized/empty identifiers, imports, chameleon includes, saved contexts
and atomic rollback. All 167 Qore suites and eight supplements pass; the four
corpus reports retain the parent's results. See [declaration evidence](notation-declarations-evidence.md).
NOTATION value/type-use/provider/HTTP integration remains the next P5 increment,
followed by key/unique/keyref and complete typed accounting.

P5-19c fixes the QName attribute-choice wrapper defect independently reproduced
during NOTATION record tests. All 38 affected Qore suites and six supplements pass;
saved providers and both HTTP directions retain QName identity. Corpus results
are unchanged; see [evidence](qname-attribute-provider-evidence.md). NOTATION
integration remains next, then identity constraints and complete typed accounting.

P5-19d implements distinct NOTATION values, enum-derived uses and scalar/list/union/
constraint/provider/HTTP integration. The 169-suite broad run and final 57 affected
suites pass; eight supplements include 2,736 binding rows. The report retains 24
identity/legacy-projection failures and 48 classified default-context oracle
disagreements. See [evidence](notation-values-evidence.md). Remaining declaration
annotation/document-ID grammar, key/unique/keyref and typed accounting must finish
before P5 closes.

P5-19e fixes native annotation foreign attributes and documentation URI checking.
The 117-schema independent matrix, 20 affected suites and 66 provider tests pass;
Valgrind is clean and corpus reports are unchanged. See
[evidence](native-annotations-evidence.md). The [WSDL grammar counterpart](p5-wsdl-annotation-finding.md),
key/unique/keyref and typed accounting remain open before P6.

P5-19f implements ordered WSDL annotation/document-ID grammar, heterogeneous
source grouping and complex-type documentation text preservation, with native URI
validation. Final 55 affected suites plus xsd-compliance, 12 supplements and clean
Valgrinds pass; corpus results are unchanged. See [evidence](wsdl-annotations-evidence.md).
The independently reproduced [scalar URI/language gap](p5-wsdl-uri-language-finding.md)
is next, followed by key/unique/keyref and complete typed accounting.

P5-19g implements builtin URI/language validation across schemas, restrictions,
saved providers and SOAP consumers. All 174 broad suites plus the new content
suite pass, with 18 supplemental executions and unchanged corpus outcomes; see
[evidence](uri-language-evidence.md). Key/unique/keyref declaration storage and
scoped instance validation, then complete typed accounting, remain before P6.

## P6 — Complete WSDL component and binding interoperability

**Depends on P2-P5.** This covers behavior the current W3C echo survey does not exercise.

- Add a WSDL 1.1 grammar/component-validation matrix. Resolve imported definitions and namespace-qualified
  messages, parts, port types, operations, bindings and services with duplicate/cycle/undefined-reference
  diagnostics. Test overloaded operations and input/output names against the applicable binding rules.
- Select the requested service/port/binding explicitly; SOAP version and operation style/use must come
  from that binding. Test a document exposing SOAP 1.1, SOAP 1.2 and HTTP bindings together.
- Cover document/literal wrapped and bare operations, RPC/literal, operation-level style overrides,
  zero/multiple parts, explicit empty `parts`, body/header partitioning, headers from another message,
  header faults, declared faults, and one-way request/response shapes.
- Complete advertised HTTP GET/POST and MIME binding behavior with URL encoding/replacement, part
  placement, typed responses/faults, and invalid binding combinations. Keep unsupported WSDL interaction
  patterns explicit rather than silently binding them to request/response behavior.
- Replay pinned CXF contracts and golden messages, including the README's bare/RPC/headers/empty-parts
  examples. Build actual SOAP 1.2 binding tests; accepting a SOAP 1.2 envelope through a SOAP 1.1 contract
  must not be counted as SOAP 1.2 binding coverage.
- Resolve the independently reproduced [operation handle ownership defect](p6-operation-lifetime-finding.md)
  as part of component/consumer lifecycle checks, including complete binding/header dependencies.
  Implemented in P6-02 with saved graphs, exact cleanup counts and both HTTP ports;
  see [ownership evidence](operation-ownership-evidence.md).

**Acceptance:** every advertised binding has parse, serialize, deserialize and local HTTP integration
coverage for both directions. Correct operation/part/QName selection is independently asserted. Invalid
descriptions fail before sending a request. Include sample-message and data-provider integration tests.

## P7 — Enforce SOAP processing and HTTP requirements

**Depends on P6.** Use WS-I profiles and the W3C SOAP 1.2 assertion identifiers as traceable requirements.

- Validate envelope namespace/version, Header/Body structure and order, document restrictions, qualified
  header blocks, valid processing attributes, and version-mismatch behavior. Test malformed and unexpected
  messages as well as valid envelopes. Prefix spelling must not affect processing.
- Implement roles/actors, `mustUnderstand`, relay and targeted/untargeted headers according to the SOAP
  version and node role. Use explicit handler capabilities; never silently ignore an unknown mandatory
  targeted header. Test intermediary and ultimate-receiver behavior separately.
- Generate and decode conforming faults: correct version-specific codes, QName subcodes, multilingual
  reasons with required language attributes, roles/nodes/actors, details and declared/header faults.
  Preserve fault data and map protocol failures to the required fault/status behavior.
- Verify SOAPAction absent/empty/quoted values and SOAP 1.2 action media-type parameters, content types,
  charset/encoding, HTTP methods/statuses, one-way/empty responses and transport failures. Cover profile
  WS-Addressing requirements where applicable; extension capability and mandatory-header handling must
  remain explicit.
- Run local Qore-client/external-server and external-client/Qore-server exchanges against a pinned
  independent SOAP implementation. Capture known-good messages and compare normalized envelopes/headers.
  Use ready events and request completion signals, deterministic teardown and bounded deadlines.

**Acceptance:** every applicable WS-I/W3C protocol assertion has an executable test or a reviewed,
specification-based not-applicable rationale. All mandatory behavior for advertised roles/profiles passes.
Malformed messages, unknown mandatory headers and action/version mismatches produce the correct fault,
and every generated fault validates. Test transport interruption and exception-safe cleanup.

## P8 — Complete attachment and legacy encoding interoperability

**Depends on P6-P7.** Keep WS-I literal conformance and SOAP encoding results separate.

- Exercise MIME multipart/related, SOAP with Attachments and MTOM/XOP end to end: root part selection,
  `Content-ID`/`cid:` resolution, media-type parameters, binary fidelity, multiple/empty/large attachments,
  boundary parsing and appropriate SOAP-version content types. Resolve every reference exactly once
  according to the protocol; reject missing/duplicate/malformed/conflicting identifiers.
- Complete the advertised SOAP encoding behavior for arrays, dimensions/ranks, sparse/offset forms,
  multi-reference values, sharing/cycles, nil and mixed scalar/complex data. Distinguish SOAP 1.1 and
  1.2 encoding namespaces/rules and compare independently generated messages.
- Make limits on depth, references, counts and payload size explicit and testable. Implement cancellation
  and deterministic cleanup for interrupted transfers and invalid graphs without truncating valid data.

**Approved scope (2026-09-22):** implement SOAP 1.2 Encoding and the SOAP 1.2 RPC Representation (Part 2
sections 3-4 and Appendix B), which covers all 26 W3C assertions routed to P8. The SOAP 1.1 section 5 rules stay
distinct. Today a SOAP 1.2 binding that declares the SOAP 1.2 `encodingStyle` is serialized with the SOAP 1.1
encoding namespace; that silent substitution is a defect this phase removes. The independent encoding peer is
Apache Axis 1.4: Maven Central JARs, pinned offline by SHA-256 like CXF, for live SOAP 1.1 rpc/encoded exchanges
in both directions. It is complemented by a pinned corpus of W3C SOAP 1.2 test-collection and SOAPBuilders
interop messages. CXF 4.1.3, already pinned, is the live SwA and MTOM/XOP peer.

Increments:

1. P8-01 - pin and verify the independent sources: the Axis 1.4 closure with a manifest and notices, a Java 17
   smoke exchange, and the encoded message corpus with provenance.
2. P8-02 - SOAP 1.1 encoding completeness: arrays (rank, dimensions, offset, position/sparse, partial), multi-ref
   sharing and cycles, nil and mixed values, both directions, against Axis and the corpus.
3. P8-03 - SOAP 1.2 encoding graph: `enc:id`/`enc:ref` with the uniqueness constraints, `nodeType`, `itemType`,
   `arraySize`, nil and type-name computation, both directions; removes the 1.1 substitution.
4. P8-04 - SOAP 1.2 RPC Representation: invocation, response and `rpc:result`, the one-child encoding
   restriction, RPC headers and faults, and Appendix B name mapping.
5. P8-05 - attachment reference semantics: SwA `cid:` resolution exactly once, rejection of missing,
   duplicate, malformed or conflicting identifiers, MTOM/XOP in both directions against live CXF, SOAP 1.2
   content types, and binary fidelity for empty, large and many parts.
6. P8-06 - explicit, tested limits on graph depth, references, counts and payload size, plus cancellation
   and deterministic cleanup for interrupted transfers and invalid graphs.
7. P8-07 - revalidate the 26 routed ledger rows against the current text and map them to tests; P8
   acceptance.

**Acceptance:** pinned CXF attachment contracts and an independent encoded-message corpus pass in both
directions with byte-identical binary content and preserved reference semantics. Negative messages fail
with descriptive protocol errors; no hangs, leaked resources or unbounded traversal. Profile claims
must not mistake success on RPC/encoded tests for WS-I literal-profile conformance.

## P9 — Enforce coverage in CI and close the gap register

**Depends on P1-P8.**

- Promote each adjudicated valid regression into mandatory offline CI. Include the Python survey tests
  and dependency setup explicitly; the current `test/*.qtest` loop alone does not run them. Keep the full
  pinned corpus and independent-peer tests in a reproducible required job with archived result artifacts.
- Run supported Linux variants, including Ubuntu and Alpine. Use installed/native dependencies only
  where intended, and verify the development Qore modules are loaded. Include serialization of parsed
  schema/service objects, client/server lifecycle tests, and affected Cargo/CDA/SOAP provider tests.
- Add deterministic generated/boundary/mutation cases for scalar values, namespaces, groups, bindings,
  faults and attachments. Record seeds for reproducibility; expected valid/invalid behavior must come
  from requirements or an independent implementation, not from the code under test.
  - **Progress (2026-09-25):** seeded generation with independent references covers scalar values (calendar,
    temporal, duration and IEEE lexicals), particle groups (complete finite languages and Xerces), namespace
    scopes (P9d-02, expat, `test_namespace_scopes.py`) and SOAP faults (P9d-03, the pinned W3C envelope schemas
    and lxml, `test_soap_fault_generation.py`). Bindings and attachments remain.
- Track requirement identifiers, fixture hashes, expected behavior, actual result, fix commit and test
  location. Include response processing, typed-value/infoset comparisons, HTTP behavior and error codes
  in reported coverage. Add assertions that prevent missing/skipped/duplicate cases from improving counts.
- Audit all changes before each commit and publish implemented capabilities/limits, examples, release
  notes and durable design details. Preserve the original findings as evidence and publish a separate
  current result set; do not rewrite the old baseline to conceal failures.
- Track performance with a deterministic benchmark rather than with test timeouts. Use pinned workloads,
  starting with the captured list-values worker manifest and one SOAP message per binding style. Record
  per-phase costs (WSDL construction, `Serializable` copy, provider construction, value conversion,
  serialization, sample generation) against a recorded reference, with byte-identical output. Report a
  regression beyond a stated tolerance as a finding. Treat subprocess timeouts in gates as hang guards with
  measured headroom, never as performance assertions. On 2026-09-22 the list-values worker took 79.7 s,
  against 25.9 s on 2026-09-09, after P5-P7 validation work; see the performance triage in `EXECUTION.md`.
  A Qore-level sampling profiler based on `get_all_thread_call_stacks()` works since Qore `fb66fa989`. Its first
  profile of the worker is flat: no function has more than about 3.6% self time.
  - **Implemented (P9b, 2026-09-25):** `benchmark/` holds the pinned workloads (the captured 384-row list-values
    manifest and a binding-style order workload), the `bench.qr` driver, `benchmark.py`, and a Release reference,
    `reference.json`. `test_benchmark.py` checks the pinned inputs, byte-identical outputs and the comparison
    rules, without timing assertions. See [the benchmark README](benchmark/README.md).
  - **Implemented (P9c-01, 2026-09-25):** CI runs the complete Python suite on Ubuntu and Alpine in six shards per
    distribution, and a verify job fails on any missing, duplicate, skipped or failed test. See
    [Continuous integration](README.md#continuous-integration).

**Final acceptance:** zero unclassified findings or missing corpus dependencies; zero rejected valid
inputs in supported scope; zero serialization failures or invalid outputs for those inputs; no value,
namespace, type, order or binary-content loss; invalid inputs rejected for the intended reason; all
applicable advertised protocol/binding requirements pass in both directions. All required tests pass
without warnings/errors, with no regression skips added to hide a gap. Deliberately unsupported optional
capabilities must be explicit, tested as such and approved as scope decisions, not silently treated as fixed.

### P9a — WS-Addressing and the WS-I gap register

**Approved scope (2026-09-23, defaults 2026-09-24):** implement WS-Addressing 1.0 in full: Core, SOAP Binding and
Metadata, including the WS-Policy 1.5 attachment of `wsam:Addressing`. This closes the 49 ledger rows recorded as
WS-Addressing gaps (25 WS-I requirements, in Basic Profile 1.2 and 2.0). The approved defaults are:
- **Incoming headers:** a SoapHandler endpoint processes WS-Addressing headers whenever a request carries them,
  as if every endpoint supported WS-Addressing optionally. A `wsam:Addressing` policy makes them required. A
  handler option disables addressing, which restores the previous MustUnderstand fault for such headers.
- **Response endpoints:** a handler sends replies or faults to a non-anonymous `wsa:ReplyTo` / `wsa:FaultTo` only
  when it is configured with a callback that approves each address, and when the effective policy allows
  non-anonymous responses. Otherwise it answers with `wsa:OnlyAnonymousAddressSupported`, as R1146 allows. The
  `none` address is always accepted. This follows the SOAP Binding section 7 warning that a sender can direct
  a receiver's messages to arbitrary endpoints.

The independent peer is CXF 4.1.3 with `WSAddressingFeature` and WS-Policy. Its `cxf-rt-ws-addr`,
`cxf-rt-ws-policy` and `neethi` JARs are already pinned in `cxf-peer/manifest.json`.

Increments:

1. P9a-01 - pin the WS-Addressing 1.0 Recommendations, WS-Policy 1.5 Framework and Attachment, and the two
   schemas in `normative/`, with a source test for the rules the implementation cites. Record this scope.
2. P9a-02 - WSDL addressing metadata:
   - actions: explicit `wsam:Action`, plus the legacy `wsaw:Action` of the 2006/05 WSDL binding; the
     non-empty SOAPAction for inputs; and the WSDL 1.1 default action pattern for inputs, outputs and faults;
   - `wsa:EndpointReference` on `wsdl:port`, with its address matching the SOAP address, and its reference
     parameters;
   - WS-Policy 1.5 and 2004/09: inline `wsp:Policy`, `wsp:PolicyReference` and `wsp:PolicyURIs`,
     normalization (`wsp:Optional`, `ExactlyOne`, `All`, nested policies), and effective endpoint and
     operation policies;
   - `wsam:Addressing` (required or optional) with `AnonymousResponses` and `NonAnonymousResponses`;
   - description rules R1156-R1158 and R2901, Metadata 3.1 and 4.4.1;
   - `wsdl:required` policy references accepted;
   - saved objects keep the metadata.
3. P9a-03 - message addressing properties in SOAP:
   - endpoint reference and MAP types;
   - header serialization, with `wsa:IsReferenceParameter` and absolute IRIs;
   - parsing with the cardinality and validity rules;
   - the predefined faults, with SOAP 1.2 subcodes and the SOAP 1.1 `wsa:FaultDetail` header;
   - the SOAPAction relationship (R1144, R2745, SOAP Binding section 4).
4. P9a-04 - clients: SoapClient and SoapClientIo send MAPs when the policy requires them or the caller asks.
   - `wsa:To` comes from the endpoint reference or the address (R1154, R1155).
   - Message IDs are generated; ReplyTo, FaultTo and mustUnderstand are configurable.
   - Responses are checked: `wsa:RelatesTo` must match the request's MessageID, and `wsa:Action` must match
     the output or fault action.
   - Received MAPs are returned to the caller.
5. P9a-05 - handler, anonymous responses:
   - MAPs are processed all or none (R1143), and WS-Addressing headers are never reported as NotUnderstood
     (R1041).
   - Headers the policy requires are enforced, including a missing message ID when a reply is expected
     (R1163).
   - Actions are checked (R2900, `wsa:ActionNotSupported`), and a missing `wsa:To` is never faulted (R1153).
   - Replies carry reply MAPs, and faults carry fault actions (R1035). Faults go on the HTTP response (R1036,
     R1145, R1161).
   - The disable option is added.
6. P9a-06 - non-anonymous responses:
   - **Handler:** approves addresses through the authorizer, enforces the response policy, and discards replies
     to `none`. Replies and faults are sent as separate HTTP requests, with faults going to FaultTo before
     ReplyTo (R1146, R1152, R1162), and the back-channel answer is 202.
   - **Clients:** a decoupled reply endpoint receives responses and correlates them by `wsa:RelatesTo`, with
     limits, timeouts and cancellation. Messages to non-anonymous destinations are HTTP requests (R1202-R1204).
7. P9a-07 - live CXF interop with `WSAddressingFeature` and policy-annotated WSDL: anonymous and decoupled
   responses, SOAP 1.1 and 1.2, in both directions.
   - The same exchanges also run over HTTP/1.1, HTTP/2 and HTTP/3 between the module's own clients and handlers.
     CXF 4.1.3 has no HTTP/3 transport, and its HTTP/2 transport needs Jetty artifacts that are not pinned.
   - Done. CXF drops a reply that arrives before the 202, so SoapHandler sends decoupled replies and faults from
     the 202's `after_send` callback (HttpServerUtil 1.6, requested as a core change on 2026-09-24). CXF clients
     then pass on the non-anonymous port too.
8. P9a-08 - revalidate the 49 rows against the pinned text and map them to tests; update the documentation,
   release notes and a durable design document; P9a acceptance. A row may be reclassified only with
   specification-based evidence.
   - Done 2026-09-24 except acceptance:
     - 45 rows are covered and mapped to tests.
     - R1203/R1204 (4 rows) are not applicable (non-addressable service instances), which was approved.
     - Three defects were fixed: R1041 `wsa:FaultDetail`, R2745 explicit empty SOAPAction (with the approved
       `send_soapaction` option), and BP 2.0 R2901 for a present empty soapAction.
     - `verify_ledger.py` rejects WS-Addressing gaps.
     - P9a accepted 2026-09-25; see [P9a acceptance](P9a-acceptance.md).

**Acceptance:** every applicable WS-Addressing row is covered by tests that exercise both directions where the
requirement has two sides. CXF exchanges pass for anonymous and decoupled responses. Invalid MAPs fail with the
predefined WS-Addressing faults. No request can make a handler contact an address that its configuration did
not approve.

## Commands at implementation phase boundaries

Run these from the repository root, plus the tests and independent fixtures specific to the phase:

```sh
qore --enable-debug test/wsdl-interop.qtest
python3 test/wsdl-interop/test_survey.py -v
python3 test/wsdl-interop/survey.py /tmp/wsdl-corpus/databinding/examples/6/09 \
  --soap-version both --output /tmp/wsdl-survey-current.json
```

Affected Qore suites currently include `soap.qtest`, `soap-features.qtest`, `xsd-compliance.qtest`,
`soap-comprehensive.qtest`, `soap-known-good.qtest`, `SoapHandler.qtest` and `SoapClient.qtest`.
P2-P5 also require tests for the affected `XsdSchema`/provider consumers. P6-P8 require real local
HTTP/peer integration checks, not just calls to `WSOperation`.

## Coverage of the original findings

P1 adjudicates every original finding and oracle disagreement. The table below assigns a primary
implementation/disposition phase to every distinct pattern in their union. It covers all 108 retained
failure/unassessed-output rows and all 58 rejected/unassessed input records: **103 distinct patterns**.
Classification-only entries in P1 may close only with evidence of a source/validator defect and a test;
any valid module failure must be reassigned to its implementation phase. The table is an ownership map,
not a claim that every listed fixture is a valid conformance test or an independent defect.

| Phase | Original patterns |
| --- | --- |
| P1 | `BlockDefault`, `FinalDefault`, `ImportNamespace`, `ImportSchemaNamespace`, `ImportTypesNamespace`, `NoTargetNamespace`, `QualifiedLocalAttributes`, `QualifiedLocalElements`, `SchemaVersion`, `TargetNamespace`, `UnqualifiedLocalAttributes`, `UnqualifiedLocalElements` |
| P2 | `ChameleonInclude`, `ComplexTypeAttributeExtension`, `ElementFormUnqualified`, `ElementTypeDefaultNamespace`, `ExtendedSimpleContent`, `GlobalAttribute`, `GlobalAttributeSimpleType`, `GlobalAttributeUnqualifiedType`, `GlobalComplexTypeEmptyExtension`, `GlobalElementComplexTypeEmptyExtension`, `GlobalElementComplexTypeSequenceExtension`, `ImportSchema`, `Include`, `IncludeRelative`, `LocalAttributeSimpleType`, `LocalElementSimpleType`, `MixedComplexContent` |
| P3 | `DateAttribute`, `DateElement`, `DateSimpleTypePattern`, `DateTimeAttribute`, `DateTimeElement`, `DecimalAttribute`, `DecimalElement`, `DecimalSimpleTypePattern`, `DoubleEnumerationType`, `DoubleSimpleTypePattern`, `ENTITIESAttribute`, `ENTITIESElement`, `ENTITYAttribute`, `ENTITYElement`, `FloatEnumerationType`, `FloatSimpleTypePattern`, `GMonthAttribute`, `IntSimpleTypePattern`, `IntegerAttribute`, `IntegerElement`, `LongSimpleTypePattern`, `NegativeIntegerAttribute`, `NegativeIntegerElement`, `NonNegativeIntegerAttribute`, `NonNegativeIntegerElement`, `NonNegativeIntegerSimpleTypePattern`, `NonPositiveIntegerAttribute`, `NonPositiveIntegerElement`, `PositiveIntegerAttribute`, `PositiveIntegerElement`, `PositiveIntegerSimpleTypePattern`, `ShortSimpleTypePattern`, `UnsignedByteAttribute`, `UnsignedByteElement`, `UnsignedIntAttribute`, `UnsignedIntElement`, `UnsignedIntSimpleTypePattern`, `UnsignedLongAttribute`, `UnsignedLongElement`, `UnsignedLongSimpleTypePattern`, `UnsignedShortAttribute`, `UnsignedShortElement`, `UnsignedShortSimpleTypePattern` |
| P4 | `ChoiceChoice`, `ChoiceMaxOccursFinite`, `ChoiceMaxOccursUnbounded`, `ChoiceMinOccursFinite`, `MinOccurs1`, `SequenceChoice`, `SequenceMaxOccursFinite`, `SequenceMaxOccursUnbounded`, `SequenceMinOccurs0`, `SequenceMinOccurs0MaxOccursUnbounded`, `SequenceMinOccurs1MaxOccursUnbounded`, `SequenceMinOccursFinite`, `SequenceSequenceElement` |
| P5 | `AnyAttributeOtherStrict`, `AnySimpleTypeAttribute`, `AnySimpleTypeElement`, `AnyTypeElement`, `ExtendedSequenceLax`, `ExtendedSequenceLaxOther`, `ExtendedSequenceSkip`, `ExtendedSequenceSkipOther`, `ExtendedSequenceStrict`, `ExtendedSequenceStrictAny`, `ExtendedSequenceStrictOther`, `GlobalElementAbstract`, `MixedContentType`, `QNameAttribute`, `QNameElement`, `SubstitutionGroup`, `TypeSubstitutionUsingXsiType` |
| P8 | `SOAPEncodedArray` |

P6-P7 cover unmeasured WSDL/HTTP/SOAP requirements; P8 additionally covers attachments; P9 covers CI and completion. They have no artificial baseline counts assigned to them.

P5-20d enforces native key fields against the assessed element declaration,
including references, substitutions, wildcard assessment and dynamic types.
Attribute fields on nillable owners remain valid. See
[native key evidence](native-key-nillable-evidence.md). This independent native
fix is independent of the P5-20c Qore serialization prerequisite, now verified,
and the nil unique/keyref interpretation accepted in P5-20e. WSDL scoped tuples
and typed accounting remain open.

P5-20e implements the explicitly approved nil-as-missing identity value
interpretation in native validation, retaining node cardinality, admissible
field types and key declaration restrictions. The interpretation question is
resolved; see [decision](nil-identity-interpretation.md) and
[native evidence](native-nil-identities-evidence.md). WSDL instance tuples must
use the same approved rule after the accepted P5-20c component layer. The original historical W3C fixture remains invalid because of
its anyType field; its separately identified typed derivative is valid.

P5-20g repairs native identity-table inheritance and local precedence, with
configure-time detection, allocation recovery and comparison-bound tests. See
[native table evidence](native-identity-tables-evidence.md). P5-20f WSDL scoped
tuples remain in progress; the [skipped-subtree rule](skipped-subtree-interpretation.md)
is now explicitly approved.

P5-20h implements native builtin-instance-attribute identity fields, selected
list/atomic and empty-list values, default union variety, checked QName/NOTATION
formatting and invalid-attribute XPath cleanup. See
[native evidence](native-instance-identities-evidence.md). The
[legacy anySimpleType projection policy](legacy-identity-projection.md) is
approved; its expected rejection remains separate from lossless success.
WSDL tuple integration and the remaining P5 acceptance criteria are still open.


P5-20i completes ordinary recursive-provider graph construction and explicit
validating-record optionality after verifying Qore `16ae86ca7`. Saved/soft graphs,
metadata, nested rejection, interruption/retry and concurrent consumers pass;
see [acceptance evidence](recursive-providers-evidence.md). Scoped tuple
integration and complete typed accounting remain P5 requirements.


P5-20j integrates scoped key/unique/keyref instance validation and its
P5-20f prototype acceptance: selected typed capture, provider/SOAP consumers,
owned table propagation, failure/interruption recovery and native provenance.
See [acceptance evidence](identity-tuples-evidence.md). The independent qdx
parser correction is prepared separately in /tmp; no main-Qore change was made.
Complete P5 typed/infoset accounting remains required before P6.


P5-20j completes scoped WSDL key/unique/keyref instance tuples, and P5-21
preserves character whitespace at WSDL instance boundaries with an explicit
native parser flag. The latter passes 193 suites, four Valgrinds and independent
character comparisons through both actual SOAP bindings; see
[character evidence](character-whitespace-evidence.md). Complete typed-value and
namespace-context accounting remains the next P5 acceptance criterion. P6–P9
remain open; the exploratory PSVI comparison does not close these criteria.

P5-22a qualifies the independent typed observer and comparison predicate, including
exact scalar/list values, selected types, namespace dependencies, character order,
strict result completeness and bounded resource handling. See
[observer evidence](typed-observer-evidence.md). Mandatory corpus accounting is
the next P5 task; existing unassessed stages remain visible until that integration
and acceptance are complete.


P5-22b integrates mandatory source/output typed observations, preserves every existing
normative assertion and adds the 172-WSDL/1,564-direction strict P5 selection. All
2,096 valid native directions are assessed without loss; 176 invalid-source
directions reject as required. Legacy projection losses remain twelve explicit
failure records. See [P5 acceptance](P5-acceptance.md) and
[typed coverage evidence](typed-coverage-evidence.md). P6 is the first incomplete phase.

P6-01 implements binding-specific request/fault/default-response versions, scoped
extension identity, saved metadata and real dual-port HTTP coverage. All existing
coverage tests now pass, including the former independent SOAP 1.1 binding failures.
See [binding-version evidence](binding-version-evidence.md). The explicit response
version override retains its historical compatibility behavior; strict incoming
version enforcement remains P7. Detached operation ownership is the next bounded
P6 increment; component, parts and HTTP/MIME acceptance remain open.

P6-02 closes detached operation/message/header/helper ownership and old weak-graph
reconstruction, with initialized zero-part maps and type-safe constructor QName
records. Thirty affected suites, clean Valgrind and unchanged complete corpus
results are recorded in [ownership evidence](operation-ownership-evidence.md).
The next P6 work is WSDL grammar/component/reference validation and imports,
followed by the remaining parts/header/HTTP-MIME acceptance matrix.

P6-03 validates document/declaration identity before grouping and preserves empty
services and port types through saved graphs. See [declaration evidence](declaration-identity-evidence.md).
The paired complete enterprise/partner tests pass; independently observed Qore
collector cost is routed to the separate runtime investigation for P9 acceptance.
Full grammar, imported QName component resolution and the remaining binding matrix
are still P6 work. No phase boundary is claimed.

P6-04 validates document-local expanded component references, scoped header
prefixes and namespace/reference whitespace; see [evidence](component-references-evidence.md).
Imported component graphs and full grammar remain required. The next import
increment must also repair the explicitly routed URI-resolution prerequisite in
`/tmp/wsdl-p6-05-import-catalog/location-finding.md` before integrating the catalog.
The WebDAV checkpoint pipeline 56986 is green on both supported CI distributions;
subsequent P6 increments remain local and P9 acceptance is not complete.

P6-05 repairs URI component resolution and HTTP root/nested schema retrieval,
including asynchronous base propagation and fragment-free request targets. The
new full-document URI interface passes the RFC examples. See
[location evidence](location-resolution-evidence.md). WSDL import catalog
integration, full-document bases for query-only schema references and the rest
of the P6 component/binding matrix remain open; no phase boundary is claimed.

P6-06 retains full non-file document URIs through WSDLLib, SoapClient, asynchronous
loading, nested schemas and saved sources. Query-only references, fragment cache
identity, cycles and restoration of active defaults are covered in
[source-location evidence](document-locations-evidence.md). WSDL import catalog
integration and canonical file-resource handling remain P6 work.


P6-07 implements the transitive WSDL/XSD import catalog and expanded component
registry, shared schema instantiation, qualified public lookups, saved dependency
sources and selected RPC body namespaces. See [import evidence](imported-components-evidence.md).
The 35-suite gate passes 457 cases / 7,256 reported assertions; the separate full
enterprise fixture passes 5 cases / 85 assertions. All six corpus reports retain
the prior results, with only version metadata changed. Canonical file URIs,
redirect-effective bases, overloaded operation/input-output names, explicit
operation selection and the rest of the P6 binding matrix remain required.

P6-08 implements canonical local file URIs across WSDLLib, SoapClient, async
loading, added schema files and saved graphs. Literal bare/legacy paths, callback
references and older cache keys remain compatible. See [file URI evidence](file-uri-evidence.md).
Redirect-effective bases, overloaded operation/input-output names, explicit
operation selection and the remaining binding matrix are still required in P6.

P6-09 replaces module-level URI resolution with Qore 3.0 resolve_url(), shares
file URI conversion with FileLocationHandler and uses native HTTP effective-URL
metadata for schema bases. See [shared URI evidence](qore-uri-evidence.md).
WSDL resource-result/redirect graph integration and the remaining P6 binding
work remain open; this is not a phase-completion claim.

P6-10 integrates FileLocationHandler resource results across root/dependency
loading, redirect aliases and offline saved graphs. XML decoding uses BOM,
transport charset and XML encoding detection consistently. See
[redirect evidence](redirect-resource-evidence.md). Operation overloads,
input/output names, binding selection and the remaining P6–P9 matrix remain open.

P6-11 verifies concrete binding membership before returning an operation from
getBindingOperation(), including imported and saved services. See
[binding selection evidence](binding-selection-evidence.md). Overloaded operation
identities, abstract input/output defaults and the rest of the binding matrix
remain open, followed by P7–P9.

P6-12 separates SOAP RPC wrapper names from abstract input/output labels in both
wire directions. See [RPC naming evidence](rpc-operation-names-evidence.md).
This prerequisite preserves operation-based wire names before overload/default
name work; overloaded identities, abstract defaults and the remaining P6–P9
matrix remain open.

P6-13 ports issue 5453 from 2.x: native SOAP body/header merging preserves
colliding message/part names, scalar values and selected type/element wrappers.
Earlier 2.x fixes remain present, including cached XSD pattern compilation.
See [header merge evidence](header-merge-evidence.md). Operation overloads,
abstract defaults and the remaining P6–P9 acceptance criteria remain open.

P6-14 implements overloaded operation identities, all four abstract default-label
patterns and concrete binding signature selection. Zero-part document/RPC messages
retain the required Body/wrapper structure. See
[operation identity evidence](operation-identities-evidence.md). Explicit empty
body-part selection, the remaining header/fault and interaction-pattern binding
matrix, HTTP/MIME interoperability and P7–P9 remain open.

P6-15 preserves explicit empty and ordered body-part selections, normalizes XML
list whitespace, rejects invalid part references, applies selections to RPC
decoding and keeps declared fault detail independent of ordinary output selection.
See [body-part evidence](body-parts-evidence.md). The approved omitted-parts standard default, concrete header/fault and interaction-pattern binding rules, HTTP/MIME
interoperability, pinned CXF replay and P7–P9 remain open.

P6-16 implements the approved standard omitted-body default, separate native maps
for overlapping Body/Header parts, missing literal body-part validation and
standard concrete interaction-pattern checks. See
[standard binding evidence](standard-body-defaults-evidence.md). Concrete
fault/headerfault rules, remaining HTTP/MIME binding behavior, pinned CXF replay
and P7–P9 remain open.

P6-17 compiles concrete SOAP fault descriptions, validates source/manual/saved
associations and uses independent document-style detail serialization. See
[fault binding evidence](fault-bindings-evidence.md). Headerfault handling, typed
fault consumption, the remaining HTTP/MIME and pinned CXF matrix, and P7–P9
remain open.


P6-18 preserves colliding imported header message names through native and retained
XML projections, saved graphs and consumers. See [header identity evidence](header-identities-evidence.md).
Concrete header metadata/headerfault handling, typed fault consumption, remaining
binding grammar, HTTP/MIME, pinned CXF replay and P7–P9 remain open.


P6-19 retains concrete header namespace/encoding metadata and validates source,
manual and saved descriptions. See [header metadata evidence](header-metadata-evidence.md).
Headerfaults, typed fault consumption, full grammar, HTTP/MIME and CXF remain P6;
P7 includes header qualification and inherited protocol metadata, followed by P8–P9.


P6-20/P6-21 implement owned headerfault declarations, explicit serialization,
native/retained XML consumption of header and body fault values, and SoapHandler
headerfault dispatch. The Qore forward-container prerequisite is verified.
All 26 affected suites and all 16 corpus commands pass their expected gates;
all six semantic reports are unchanged. The approved configurable worker deadline
preserves the 60-second default; this full run used 180 seconds. See
[fault evidence](headerfaults-evidence.md). Remaining binding grammar, HTTP/MIME,
pinned CXF replay and P7–P9 remain open.


## P6-22: HTTP MIME XML part selection and transport

Explicit MIME XML input/output part selections now resolve against the selected
abstract messages. HTTP-only services serialize successful responses without a
SOAP version override; HTTP errors remain errors even with SOAP-shaped bodies.
Source, saved and detached metadata and a real local client/server exchange pass.
The affected gate passes 9 suites / 86 cases / 2,765 reported assertions; the
SOAP comparator suite intentionally catches its negative assertions. Docs and
astparser pass; audit: 18 Pass / 44 N/A / zero Fail. No C++ changes.
See [validation](P6-22-validation.json), [audit](audits/P6-22-http-mime.md) and
[implemented design](../../design/wsdl-http-mime.md). Full binding grammar,
the remaining HTTP/MIME matrix and pinned CXF replay remain in P6, followed by P7–P9.


## P6-23: HTTP form placement and URI encoding ownership

`http:urlEncoded` POST uses a typed form body; GET retains query parameters.
HTTP-bound SoapClient uses HTTPClient pre-encoded URL mode so reserved characters
and Unicode reach the peer after exactly one encoding pass. Source, saved-service
and detached-operation tests cover both forms, invalid types and empty values.
Four real local exchanges assert typed callbacks and raw request targets.
The affected gate passes 11 suites / 144 cases / 3,082 reported assertions; the
SOAP comparator suite intentionally catches its negative assertions. Docs and
astparser pass; audit: 18 Pass / 44 N/A / zero Fail. See
[validation](P6-23-validation.json) and [audit](audits/P6-23-http-form.md).
The remaining binding grammar/HTTP/MIME and pinned CXF matrix remain P6 work,
followed by P7–P9; this increment is not a phase-completion claim.


## P6-24: HTTP URL-replacement routing and lifecycle

The handler matches complete replacement templates separately from static paths,
using raw request paths and removing handler mount prefixes before decoding.
Static mounted lookups retain exact-match checks. Duplicate/ambiguous templates
reject, registration holds the write lock, and removeService drops both HTTP
route kinds. The old SoapClient expected-failure case now asserts success and
callback values. The focused suite passes 4 cases / 187 assertions; the affected
gate passes 12 suites / 148 cases / 3,270 reported assertions. SOAP comparator
negative assertions remain intentional. Docs/astparser pass; audit: 18 Pass /
44 N/A / zero Fail. See [validation](P6-24-validation.json) and
[audit](audits/P6-24-http-replacement.md). Remaining P6 binding grammar and the
HTTP/MIME/CXF matrix still precede P7–P9; no phase boundary is claimed.


## P6-25: distinct message parts sharing an element QName

Message parts retain separate internal argument identities even when they refer
to the same element. The selected binding can place their independent values in
Body and Header; wire QNames and public part-name/provider fields remain stable.
Duplicate part names and ambiguous same-body selections still reject. Both SOAP
versions, both directions, saved graphs, native/retained forms and HTTP consumers
pass. The unmodified pinned SwA contract now loads, and WSDL4J independently
confirms its request/response part declarations; this is not an attachment gate.
The affected gate passes 30 suites / 519 cases / 10,639 reported assertions; the
final focused test adds two raw decoder checks and passes 4 cases / 96 assertions.
Docs/astparser pass; audit: 18 Pass / 44 N/A / zero Fail. See
[validation](P6-25-validation.json) and [audit](audits/P6-25-shared-part-elements.md).
The pinned document-header contract has undefined inoutHeader body-part names;
the RPC-header contract includes a CXF-specific XML binding. Their source and
capability adjudication and remaining P6 work still precede P7–P9.


## P6-26: schema-aware HTTP MIME XML values

MIME XML now serializes the selected document part with per-call namespace
bindings and decodes by expanded root identity. Qualified children, QName values,
nil, saved graphs and retained lexical XML work in both directions and through
real HTTP consumers. Encoding and formatting options reach the XML generator.
SOAP-only processing-instruction restrictions remain specific to SOAP. Wrong,
missing, repeated and extra roots reject; the legacy unqualified-global-element
expectation now asserts rejection and supplies valid qualified XML for success.
The gate passes 14 suites / 169 cases / 3,989 reported assertions;
all 16 corpus commands meet expected outcomes. Docs/parser pass; audit: 18 Pass /
44 N/A / zero Fail. See [validation](P6-26-validation.json),
[audit](audits/P6-26-http-xml-values.md), and the
[implemented design](../../design/wsdl-http-mime.md).
Remaining P6 binding/CXF work and P7–P9 are still open.


## P6-27: retained optional CXF transport metadata

CXF XML and JMS declarations now retain metadata without blocking supported SOAP
ports. Unsupported bindings do not register callable operations; client port
selection rejects explicitly, including URL overrides. Source/saved services and
standalone bindings retain namespace and extension data. Mounted WSDL output
rewrites supported address elements by component ownership and preserves other
URLs, comments, PIs and CDATA. Real mixed-contract SOAP exchanges pass.
The original RPC-header and MTOM contracts load. WSDL4J independently confirms
that the original document-header contract names undefined `in`/`out` parts for
`inoutHeader`; it remains an expected source rejection. No pinned source changed.
The gate passes 32 suites / 531 cases / 10,984 reported assertions;
all 16 corpus commands meet expected outcomes and six semantic reports are unchanged.
Docs/parser and the independent observer pass; audit: 18 Pass / 44 N/A / zero Fail.
See [validation](P6-27-validation.json), [audit](audits/P6-27-optional-transports.md)
and [implemented design](../../design/wsdl-optional-transports.md).
Full XML/JMS transport execution remains outside scope as approved and is tracked
in [Qore #5454](https://github.com/qoretechnologies/qore/issues/5454).
Remaining P6 grammar/CXF replay and P7–P9 are still open.


## P6-28: independent CXF binding replay and live peers

The pinned bare, RPC/literal, SOAP 1.2 and RPC-header contracts, plus the explicitly
corrected document-header derivative, pass 19 reference message pairs. Original
CXF sources and their hashes remain unchanged. An offline CXF 4.1.3/JAXB/Jetty peer
performs 76 live calls across both Qore/CXF directions and source/saved services,
and replays all 19 captured reference requests against CXF. Qore tests additionally
exercise detached operations, native/retained values, providers and samples.
Root-cause fixes retain empty complex records at type-part boundaries, give native
providers occurrence-based optionality and valid empty examples, normalize complete
message examples, avoid invented SOAP actions and dispatch bare scalar/empty bodies.
Ambiguous empty dispatch rejects and service removal restores a unique candidate.
Four identity fixture inputs use explicit empty objects for present empty records;
the independent identity gate passes all 340 stages and 278 validation documents.
Substitution-root and wildcard-attribute regressions now test native capture
separately from the unchanged ordinary empty projection, including saved/soft
providers and missing-versus-present values.
All 179 Qore suites pass: 1758 cases / 87,379 reported assertions.
The six-test peer gate, docs and astparser pass without diagnostics. All 16 corpus
commands meet expected outcomes and all six semantic reports are unchanged.
Audit: 19 Pass / 43 N/A / zero Fail; no C++ changes or push.
See [validation](P6-28-validation.json), [audit](audits/P6-28-cxf-peer.md),
[peer instructions](cxf-peer/README.md), [derivative provenance](cxf-derived/README.md),
and [empty-record design](../../design/wsdl-native-empty-records.md).
Remaining full P6 grammar/binding acceptance and the attachment-specific CXF gates
still require completion; P7–P9 are not complete.


## P6-29: core grammar and optional extension isolation

Core WSDL declarations validate ordered children, attributes, documentation,
character data, operation shape, parameter tokens and schema-instance metadata
before grouping. Unknown required extensions fail; optional foreign payloads
cannot shadow component or binding names. Schema normalization starts only at
actual document/inline schema roots, preserving XSD-looking vendor metadata.
The pinned corrected 2004-08-24 WSDL schema independently assesses all 312 authored
documents, including 22 schema-valid required-capability rejections. The focused
suite passes 314 cases / 3,580 assertions across original, serialized and data-saved
services, request/response values, providers/samples, retained unsupported metadata
and recovery. The full gate passes 180 Qore suites / 2073 cases /
91,003 reported assertions. All 16 corpus commands meet expected outcomes;
all six semantic reports are unchanged. Six CXF peer tests, docs and astparser
pass without diagnostics. Audit: 18 Pass / 44 N/A / zero Fail; no C++ changes.
See [evidence](wsdl-grammar-evidence.md), [validation](P6-29-validation.json),
[audit](audits/P6-29-core-grammar.md) and
[implemented design](../../design/wsdl-core-grammar.md).
Remaining top-level WSDL constraints, binding extension grammar and HTTP/MIME/CXF
acceptance stay in P6;
P7–P9 are not complete. No push until development completion.


## P6-30: SOAP binding extension grammar

Direct SOAP binding declarations now validate version-specific attributes, required
values and content before grouping. Headers admit same-namespace headerfaults;
other declarations have empty content. URI/token normalization fixes legal lexical
whitespace in transport URIs, fault names and header references while preserving
the original WSDL text. The 295-document matrix covers both versions and seven
contexts through source, serialized and data-serialized services, detached
operations, provider samples, requests/responses and body/header faults.
Xerces assesses all documents against byte-pinned original schemas. Fourteen
ignored incomplete location hints and two SOAP 1.2 fault wildcard discrepancies
have explicit specification-based classifications. The focused suite passes
295 cases / 6,455 assertions. The full gate passes 181 suites / 2368
cases / 97,458 reported assertions. All 16 corpus commands meet expected
outcomes; six semantic reports are unchanged. Six CXF peer tests, documentation
and astparser pass without diagnostics. Audit: 18 Pass / 44 N/A / zero Fail;
no C++ changes or Valgrind requirement.
See [evidence](wsdl-soap-grammar-evidence.md), [validation](P6-30-validation.json),
[audit](audits/P6-30-soap-grammar.md) and
[implemented design](../../design/wsdl-soap-extension-grammar.md).
Remaining top-level WSDL constraints, HTTP/MIME grammar, SOAP binding semantics
and attachment-specific CXF acceptance stay in P6. P7–P9 remain incomplete.
No push until development completion.


## P6-31: HTTP and MIME leaf declaration grammar

The declaration reader checks five HTTP and two MIME leaf extension contexts.
Attribute ownership, required values and empty content validate before grouping;
URI/token normalization preserves original source while fixing method, endpoint
and part lookup. Core, SOAP and HTTP/MIME declarations share schema-instance
lexical checks. The audit fixes SOAP body xsi:type selection for the published
tFault derivation, including its required name/prohibited parts and unchanged body
semantics. Eight valid/invalid derived-type cases bring the SOAP matrix to 303.
The original HTTP/MIME schemas independently assess all 187 matrix
documents; seven unused incomplete location hints have explicit specification-based
semantic rejections. The Qore suite passes 188 cases / 3,162 assertions, including
24 live HTTP calls through source, serialized and data-saved services without
endpoint overrides. Namespace aliases, GET/POST, detached operations, provider
examples, both wire directions and invalid media types are exercised.
All 20 affected Qore suites pass (933 cases / 20,356 assertions), with
three independent grammar runners, six CXF peer tests, docs and astparser clean.
Audit: 18 Pass / 44 N/A / zero Fail; no C++ changes. The P6-30 full regression/corpus
baseline remains separately recorded; this increment reruns affected paths.
See [evidence](http-mime-grammar-evidence.md), [validation](P6-31-validation.json),
[audit](audits/P6-31-http-mime-grammar.md) and
[implemented design](../../design/wsdl-http-mime-grammar.md).
Remaining P6 work includes top-level WSDL constraints, concrete binding semantics,
MIME multipart grammar/alternatives and attachment contract replay. P7–P9 are still
incomplete. No push until development completion.


## P6-32: HTTP URL-replacement pattern compilation

HTTP templates recognize exact declared message-part patterns and preserve other
parentheses as URI literals, including nested, empty and unmatched parentheses.
All declared parts must have patterns; missing patterns reject at construction.
Compilation is atomic and repeated descriptor updates replace their prior maps.
Unicode part names and UTF-16 caller strings retain their characters. The legacy
one-argument setter keeps its documented interpretation of parenthesized tokens.
The 19-document matrix has independent Python substitution and pinned-Xerces
schema checks. Four schema-valid negative descriptions have explicit all-parts
semantic adjudications. The Qore regression passes 22 cases / 1,187 assertions,
including 90 live GET/POST exchanges through source and both saved service forms,
plus detached operations, provider examples, rollback and nested literals.
All 14 affected Qore suites pass (365 cases / 7,825 assertions), as do
two independent matrix runners, six CXF peer tests, docs and astparser without
warnings. Audit: 18 Pass / 44 N/A / zero Fail. No C++ changes or push.
See [evidence](http-replacement-patterns-evidence.md),
[validation](P6-32-validation.json), [audit](audits/P6-32-http-replacement-patterns.md)
and [implemented design](../../design/wsdl-http-mime.md).
P6 top-level constraints, remaining concrete binding/MIME behavior and attachment
contract replay remain open before P7–P9. This is not a phase-completion claim.


## P6-33: MIME media types and opaque HTTP bodies

MIME declarations and wire headers use complete media-type parsing and constraint
matching, including both WSDL wildcard components, quoted parameters, charsets,
nested MIME type values and duplicate-value checks. Source/saved descriptors
retain parameters; explicit charsets control text encoding. SoapClient and
SoapHandler preserve opaque MIME bodies even for XML and multipart types.
SOAP 1.2 action parameters are quoted; handler routing uses exact declared actions
or actual body elements. Invalid descriptor updates leave prior state intact.
The independent matrix covers 91 declaration/wire pairs and 18 classifications;
the Qore suite passes 98 cases / 2,741 assertions with 38 actual MIME HTTP calls.
All 17 affected Qore suites pass (523 cases / 10,803 reported
assertions), plus independent MIME/grammar checks, six CXF peer tests, docs and
astparser. All 16 corpus gates meet expected outcomes; six semantic reports are
unchanged. The full strict regression now uses the approved 180-second worker
bound and a separate 360-second outer deadline for worker plus independent checks.
Audit: 18 Pass / 44 N/A / zero Fail; no C++ changes or push.
See [evidence](media-types-evidence.md), [validation](P6-33-validation.json),
[audit](audits/P6-33-media-types.md) and [implemented design](../../design/wsdl-http-mime.md).
Top-level WSDL constraints, remaining concrete binding/MIME behavior and attachment
contract replay remain P6 work before P7–P9; this is not phase completion.


## P6-34: Empty, Unicode and fixed-query HTTP locations

HTTP operation locations distinguish empty relative URIs from missing attributes.
Empty replacement maps retain their zero-part binding meaning. URI matching and
query prefix removal use consistent UTF-8 byte offsets, including alternate
caller encodings. Fixed-query locations use the handler template registry and
lifecycle; static routes compare actual URI boundaries. Near-matching path names
and query values reject instead of reaching the callback.
The 16-fixture Qore matrix passes 17 cases / 996 assertions, including source,
both saved-service forms, detached operations, provider examples, both directions,
54 successful HTTP calls and 18 rejected HTTP calls. Independent Python URI
observation and pinned Xerces check 16 valid and 16 missing-location documents.
All 18 affected Qore suites pass (540 cases / 11,799 reported
assertions), plus independent matrices, six CXF peer tests, docs and astparser.
All 16 corpus gates meet expected outcomes; six semantic reports are unchanged.
Audit: 18 Pass / 44 N/A / zero Fail; no C++ changes or push.
See [evidence](http-uri-boundaries-evidence.md), [validation](P6-34-validation.json),
[audit](audits/P6-34-http-uri-boundaries.md) and [implemented design](../../design/wsdl-http-mime.md).
Remaining top-level/component constraints, binding combinations, MIME multipart
and attachment replay stay in P6 before P7–P9. This is not phase completion.


## P6-35: WSDL URI constraints and native anyURI content

Supplied target namespaces now require absolute URIs; HTTP operation locations
require relative references. Imports use the same rules, and Qore URI mapping
classifies values without changing stored namespace/location spelling. Independent
validation also exposed native acceptance of bare schemes. The shared XSD 1.0
anyURI validator now enforces RFC 2396 absolute-URI content while general RFC 3986
resolution remains unchanged. CMake detects affected libraries and applies the
checksum-verified private correction with allocation-error cleanup intact.
The 33-document WSDL matrix passes 35 cases / 754 assertions and 21 actual HTTP
calls through source/saved consumers. Pinned Xerces agrees on grammar assessment;
13 schema-valid semantic negatives and two lexical negatives are explicit.
The URI/language matrix now has 89 documents. All 30 affected Qore suites pass
(1,254 cases / 25,660 reported assertions), plus independent matrices,
six CXF peer tests, 12 CMake tests, docs and astparser. Native and configured-Qore
Valgrinds have zero errors/lost bytes; initial PCRE2-JIT diagnostics are separately
recorded. All 16 corpus gates meet expected outcomes; six semantic reports are
unchanged. Audit: 22 Pass / 40 N/A / zero Fail. No push.
See [evidence](uri-constraints-evidence.md), [validation](P6-35-validation.json),
[audit](audits/P6-35-uri-constraints.md) and [datatype design](../../design/wsdl-uri-language-values.md).
Remaining P6 work includes concrete binding combinations, complete HTTP part/URI
behavior, MIME multipart grammar/alternatives and attachment contract replay;
P7–P9 remain incomplete. The empty-query part-validation bypass is reproduced in
`/tmp/xml-http-part-values/` for the next binding increment.


## P6-36: HTTP query and form part presence

HTTP GET queries and POST/MIME forms enforce the presence of every declared part,
including absent queries and normalized zero-byte bodies. Explicit empty strings
remain valid; empty integer/boolean values fail their type checks. Zero-part
messages work, and extra unbound keys retain their existing ignored behavior.
The shared part converter checks key presence before conversion; all GET queries
reach it. Thirty cases / 2,646 assertions cover 31 forms, source and both saved
services, detached operations, providers/examples, 90 successful HTTP calls and
180 missing-part rejections before callbacks. Independent Python parsing and
pinned Xerces agree on values and invalid forms.
All 20 affected Qore suites pass (605 cases / 15,199 assertions),
plus seven independent gates (including six CXF peer tests), docs and astparser.
All 16 corpus gates meet expected outcomes; six semantic reports match P6-35.
Validation uses current Qore's already-fixed Mime binary for empty form output.
Audit: 18 Pass / 44 N/A / zero Fail. No C++ changes or push.
See [evidence](http-part-presence-evidence.md), [validation](P6-36-validation.json),
[audit](audits/P6-36-http-part-presence.md) and [design](../../design/wsdl-http-mime.md).
P6 still requires concrete binding combinations, remaining URI behavior,
MIME multipart grammar/alternatives and attachment replay before P7–P9.


## P6-37: Concrete extension ownership and type-part routing

The structure scanner retains the enclosing binding namespace and validates
SOAP/HTTP operation/message extensions before namespace stripping. Protocol/version
mismatches, duplicate declarations, conflicting URL mappings and output URL mappings
reject with WSDL-ERROR. Prefix aliases, default namespace scopes, opaque optional
extensions and absent SOAP operations work through local/imported and saved services.
Actionless document type-parts now register their selected wire names for dispatch.
The 65-document independent Python/Xerces matrix separates 24 supported cases
from 41 schema-valid semantic negatives. The Qore suite passes 67 cases / 1,924
assertions, including detached handles, providers, 156 successful HTTP calls,
six unselected-route rejections and recovery.
All 29 affected Qore suites pass (1,337 cases / 30,613 assertions),
plus nine independent gates (including six CXF peer tests), docs and astparser.
All 16 corpus gates meet expected outcomes and six semantic reports match P6-36.
Audit: 18 Pass / 44 N/A / zero Fail; no C++ changes or push.
See [evidence](binding-extension-ownership-evidence.md), [validation](P6-37-validation.json),
[audit](audits/P6-37-binding-extension-ownership.md) and [design](../../design/wsdl-core-grammar.md).
MIME multipart grammar, nested header retention and alternative compilation remain
required P6 work; the next root-cause probes are in `/tmp/xml-mime-part-grammar/`.
P7–P9 remain incomplete.


## P6-38: MIME multipart grammar and nested SOAP metadata

The stream now validates MIME containers and delegates SOAP/MIME leaves to their
own grammars. Namespace-aware projection isolates optional foreign payloads before
grouping. Compilation retains root-part SOAP headers/headerfaults, body hints and
all content alternatives under the correct internal argument identity. Missing
primary SOAP bodies and non-root headers reject before publication.
The pinned corrected 2004 MIME schema and WSDL4J independently assess 120 documents:
40 supported descriptions, 26 schema-valid semantic negatives and 54 grammar
negatives. The Qore suite passes 120 cases / 9,748 assertions and 228 actual HTTP
header/body calls, through local/imported/saved and detached consumers. Shared-element
attachment fixtures cover declarations and saved metadata, not attachment octets.
All 30 affected Qore suites pass (1,457 cases / 40,361 assertions),
plus eleven independent gates, docs and astparser. All 16 corpus commands meet
expected outcomes; six semantic reports match P6-37. Audit: 18 Pass / 44 N/A /
zero Fail; no C++ changes or push.
See [evidence](mime-part-grammar-evidence.md), [validation](P6-38-validation.json),
[audit](audits/P6-38-mime-part-grammar.md) and [design](../../design/wsdl-mime-part-grammar.md).
Complete MIME representation alternatives and remaining HTTP URI behavior stay in
P6. A concrete SoapClient base-URI concatenation failure is reduced in
`/tmp/xml-http-base-resolution/` for the next increment. P7–P9 remain incomplete.


## P6-39: MIME content defaults and complete media declaration checks

Direct and multipart content bindings share WSDL single-part/unrestricted-type
defaults and media validation. Empty content elements are present declarations.
Every multipart alternative validates syntax and parameter constraints before
publication; ambiguous/unknown parts and explicitly empty media types reject.
The 70-document matrix has 38 supported and 32 invalid descriptions; its Qore
suite passes 70 cases / 4,636 assertions and 12 HTTP exchanges. Python, Xerces and
WSDL4J independently distinguish general WSDL defaults from the published WS-I
schema's stricter required-part rule. Saved services, detached handles and providers
retain the metadata. All 31 affected Qore suites pass (1,527 cases /
44,997 assertions), plus 14 supplemental gates. All 16 corpus commands meet
expected outcomes and six semantic reports match P6-38. Audit: 18 Pass / 44 N/A /
zero Fail. No C++ changes or push.
See [evidence](mime-content-defaults-evidence.md), [validation](P6-39-validation.json),
[audit](audits/P6-39-mime-content-defaults.md) and [design](../../design/wsdl-mime-part-grammar.md).
P6 still requires MIME representation alternatives, attachment replay and complete
HTTP URI behavior. The latter requires Qore's request-local absolute URL API;
write-up and two-server reproducer: `/tmp/xml-http-base-resolution/QORE-REQUEST-URL.md`.
P7–P9 remain incomplete.


## P6-40: Direct HTTP MIME representation selection

Direct content, form and schema-XML declarations retain distinct representations.
Content-Type selects a unique format; the approved explicit-selector API resolves
overlaps through WSOperation, SoapClient and SoapHandler. Selection precedes
encoding/decoding, with no schema fallback. Opaque and XML media types cannot be
relabelled by final header overlay. Saved descriptions and existing native value
shapes remain supported. Duplicate equivalent media declarations retain a default.
HTTP binding bytes keep their selected charset; UTF-16 BOM handling is explicit.

The 17-document matrix passes 20 cases / 6,940 assertions, including 204 local
HTTP calls, source/imported/saved/detached/provider paths and concurrent selectors.
Forty-eight independent Python/Qore exchanges cover both directions and three
charsets. ET, Xerces and WSDL4J independently assess the declarations. All
32 affected Qore suites pass (1,547 cases / 51,937 assertions)
within 47 gates; all 16 corpus commands meet expected outcomes and six semantic
reports match P6-39. Audit: 18 Pass / 44 N/A / zero Fail. No C++ changes or push.
See [evidence](mime-representations-evidence.md), [validation](P6-40-validation.json),
[audit](audits/P6-40-mime-representations.md), and [design](../../design/wsdl-http-mime.md).

P6 still requires mixed/nested multipart layouts, attachment contract replay and
complete HTTP URI execution. The latter requires the Qore request-local target
API described in `/tmp/xml-http-base-resolution/QORE-REQUEST-URL.md`. P7–P9 remain
incomplete.


## P6-41: Multipart input normalization

SOAP multipart input now shares Qore Mime framing, validates its selected root
and identifiers, decodes transfer encodings to bytes, and shares charset/BOM root
decoding across native and retained XML consumers. Installed Qore 79348ce8c / Mime
1.9 resolves all six shared-parser/writer regression failures. No Qore changes or
runtime override were needed.

The 50-wire matrix passes 53 cases / 798 assertions, with independent Python
framing/byte checks and 96 HTTP exchanges covering both directions, saved services,
retained XML, actionless XOP-root dispatch, negatives and recovery. All 50 gates
pass: 34 Qore suites / 1,608 cases / 52,945 assertions, independent matrices, CXF
peers, docs and astparser. All 16 corpus commands meet expected outcomes; six
semantic reports match P6-40. Audit: 18 Pass / 44 N/A / zero Fail. No C++ changes
or push.

See [evidence](multipart-input-evidence.md), [validation](P6-41-validation.json),
[audit](audits/P6-41-multipart-input.md), and [design](../../design/wsdl-multipart-input.md).
P6 still requires multipart layout compilation, attachment binding replay and the
request-local URI API integration; P7–P9 remain incomplete.


## P6-42: SOAP MIME attachment parts and concrete provider types

Attachment parts now serialize independently of SOAP body/header selection.
Type-based parts carry raw media; global-element parts use schema XML. Native
and retained XML consumers preserve media alternatives, public part identities,
qualified headers and separate values for overlapping locations. SoapDataProvider
uses the concrete selected binding, preserves raw bytes and supplies validated
examples through saved, soft and optional types.

The focused suite passes 19 cases / 876 assertions. Independent pinned CXF golden
messages and 24 live calls cover three operations in both directions, plus 60
negative/recovery exchanges. The original CXF fixture remains unchanged; a named
and exactly checked derivative removes one invalid media annotation. All 58 gates
pass: 41 Qore suites / 1,669 cases / 54,721 assertions, 15 independent gates,
docs and astparser. All 16 corpus commands meet expected outcomes and six semantic
reports match P6-41. All four changed modules compile to QMOD and the focused suite
also passes with the compiled modules. Audit: 27 Pass / 35 N/A / zero Fail.
No C++ changes or push.

See [evidence](swa-parts-evidence.md), [validation](P6-42-validation.json),
[audit](audits/P6-42-swa-parts.md), and [design](../../design/wsdl-swa-parts.md).
General multipart layout compilation/execution and request-local HTTP URI
integration remain required P6 work. Full attachment reference semantics remain
P8 work; P7–P9 are incomplete.


## P6-43: HTTP MIME entity trees

The implementation retains recursive HTTP MIME declarations, independent entity values, explicit ambiguous-format selections, related root identities and concrete provider types. Source, saved and detached operations use the same contract.

Installed Qore `e8768a8a0` resolves both ordinary-literal conversion failures. The independent core reproducer passes 5 cases / 5 assertions. XML's focused tree and literal suites pass 15 cases / 676 assertions in both source and compiled-module checks. No XML coercion workaround is present.

All 43 affected Qore suites pass: **1,684 cases / 55,397 assertions**. All 16 independent Python gates pass, including five MIME peer tests with 32 external decoding variants, four live HTTP exchanges and 32 malformed-input/recovery pairs. All 16 corpus commands meet their expected outcomes; six semantic reports match P6-42 apart from runtime version metadata. Documentation, eight-file astparser checks and all four compiled QMODs pass without warnings/errors.

The full audit reports **28 Pass / 34 N/A / zero Fail**. All work targets `develop` in the main checkout. No C++ change, Qore source change, installation or push was made. Request-local HTTP URL support and its XML integration remain required P6 work; P7–P9 remain incomplete.

See [evidence](mime-entity-tree-evidence.md), [validation](P6-43-validation.json), [audit](audits/P6-43-mime-entity-trees.md), and [design](../../design/wsdl-http-multipart.md).


## P6-44: Resolved HTTP client and handler URLs

Qore's installed `HTTPClient::sendUrl()` passes its 13-case / 186-assertion core suite. SoapClient resolves HTTP operation references with Qore's RFC 3986 API after serialization, keeps per-call targets separate from persistent configuration, and scopes its default Authorization/Cookie/Host headers to the configured origin. Explicit call headers retain their target scope. The constructor now applies username/password options after endpoint selection, preserving URL-credential precedence.

All 45 affected Qore suites pass: **1,698 cases / 55,868 assertions**. All 17 independent Python gates and 16 corpus commands meet their expected outcomes. The new Python peer checks 56 actual HTTP exchanges. Six corpus reports retain P6-43's semantic results. Documentation, eight-file astparser checks and the compiled WSDL/SoapClient/SoapHandler suites' 14 cases / 471 assertions pass without warnings/errors.

The full audit reports **18 Pass / 44 N/A / zero Fail**. This increment changes no C++, Qore source or installation and is committed only to the main `develop` checkout. P6 remains open for final binding acceptance; P7–P9 are incomplete. No push until development completion.

See [evidence](http-request-url-evidence.md), [validation](P6-44-validation.json), [audit](audits/P6-44-http-request-url.md), and [design](../../design/wsdl-http-request-url.md).


## P6-45: Declaring-document service port addresses and P6 acceptance

Service port addresses now resolve with Qore against the URI of the WSDL document declaring the service. Imported services use their own effective retrieval URI, including redirects. Saved sources reproduce the same address without network access; inline sources without document context retain the declared reference, and explicit client endpoint overrides remain authoritative.

All 203 phase-boundary Qore suites pass: **3,257 cases / 136,416 assertions**. All 18 independent Python gates and 16 corpus commands meet their expected outcomes. The new port-address suite passes 4 cases / 519 assertions in both source and compiled WSDL; its loopback loaders cover 63 HTTP exchanges, while the independent Python peer covers another 28. Six corpus reports match P6-44 except for the WSDL source hash. Documentation and three-file astparser checks pass without warnings/errors.

The full audit reports **18 Pass / 44 N/A / zero Fail**. P6 acceptance is complete within the approved optional-transport scope; P7 SOAP processing is next, followed by P8 attachments/encoding and P9 CI/runtime acceptance. No C++ or Qore changes, installation or push.

See [port evidence](port-locations-evidence.md), [validation](P6-45-validation.json), [audit](audits/P6-45-port-locations.md), [P6 acceptance](P6-acceptance.md), and [implemented location design](../../design/wsdl-location-resolution.md).


## P7-01: SOAP envelope structure, version and document restrictions

Native and retained SOAP consumers now share container validation before namespace projection. Serialization rejects unqualified header blocks, including raw compatibility fragments. Selected binding versions are enforced, version-negotiation faults retain their required SOAP 1.1 transition behavior, and SOAP 1.2 fault reasons carry xml:lang. Invalid requests reject before callbacks and valid requests recover on the same client.

All 204 Qore suites pass: **3,265 cases / 137,774 assertions**, including the audit follow-ups. All 22 independent Python gates and 16 corpus commands meet their expected outcomes. The focused envelope suite passes **8 cases / 1,330 assertions** with source and compiled WSDL/SoapClient/SoapHandler modules. Independent peers pass 168 HTTP exchanges; the Qore suite adds 120. Documentation and 15-file astparser checks pass without warnings/errors. All six corpus comparisons preserve classifications, outcomes and values, with only the explicitly recorded SOAP 1.2 binding/output-context changes.

The pinned W3C archive remains unchanged; SOAP 1.2 payloads explicitly select named, hash-recorded binding derivatives. Earlier positive test bindings and synthetic header fixtures now produce conforming envelopes. The archive-role worker accepts a bounded configurable timeout; its complete integration test covers every original archive file.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ or Qore checkout changes, installation or push. P7 continues with processing attributes, roles/actors, mustUnderstand/relay, complete faults and action/media/HTTP requirements; P8–P9 remain open.

See [evidence](soap-envelope-evidence.md), [validation](P7-01-validation.json), [audit](audits/P7-01-soap-envelope.md), [binding derivatives](soap12-binding-derivatives.md), and [implemented design](../../design/soap-envelope-processing.md).


## P7-02: SOAP header boolean lexical validation

SOAP 1.1 mustUnderstand and SOAP 1.2 mustUnderstand/relay now validate their version-specific lexical spaces before decoding or emission. Namespace context selects the protocol attributes; unqualified, foreign-version and descendant attributes are not interpreted as header processing directives. Native attribute conversion and raw compatibility fragments cannot bypass validation.

All 21 affected Qore suites pass: **359 cases / 10,957 assertions**. Four independent Python gates pass, including 261 new HTTP exchanges and the pinned W3C attribute-declaration matrix. The new suite passes **3 cases / 927 assertions** with both source and compiled WSDL. Documentation and two-file astparser checks pass without warnings/errors. All 16 corpus commands meet their expected outcomes; six semantic reports match P7-01 apart from the WSDL source hash.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ or Qore changes, installation or push. P7 continues with explicit node capabilities, roles/actors, mandatory targeted headers, relay, complete faults and HTTP requirements; P8–P9 remain open.

See [evidence](soap-processing-attributes-evidence.md), [validation](P7-02-validation.json), [audit](audits/P7-02-soap-processing-attributes.md), and [implemented design](../../design/soap-envelope-processing.md).


## P7-03: Explicit SOAP nodes and HTTP adapters

Immutable header capabilities implement actor/role targeting, mandatory preflight,
typed processing outcomes, intermediary relay and targeted application envelopes.
SoapClient and SoapHandler integrate these nodes. Unknown targeted mandatory request
headers generate MustUnderstand faults; SOAP 1.2 faults include scoped NotUnderstood
QNames. Response fault detection uses the envelope-qualified name, keeping application
Fault elements as ordinary schema values; direct and HTTP regressions cover both versions. Response roles use the final request URL plus XML Base. Native, retained,
saved, concurrent and independent CXF/Python paths cover these behaviors, including
occurrence-list filtering of adjacent bound headers.

The installed Qore strict URI fix is verified, and SOAP role validation now uses
RESOLVE_URL_ASCII. All 25 affected Qore suites pass (373 cases / 15,340 assertions),
including the ordinary negative URI suite. All four compiled SOAP suites pass
(14 cases / 4,381 assertions). Independent peers pass 348 new HTTP exchanges; all
16 corpus commands retain the P7-02 semantic results. Documentation and eleven-file
AST checks are clean. Audit: 18 Pass / 44 N/A / zero Fail.

P7 complete fault and HTTP/action rules remain open; P8–P9 follow. No C++ changes,
Qore edits, installation, push or CI trigger belong to this increment.

See [evidence](soap-node-evidence.md), [validation](P7-03-validation.json),
[audit](audits/P7-03-soap-node.md), and [implemented design](../../design/soap-envelope-processing.md).


## P7-04: SOAP 1.2 fault grammar

SOAP 1.2 fault fields now validate before native namespace projection: ordered
required/singleton fields, scoped Code/Subcode QNames and top codes, multilingual
Text with explicit xml:lang, Node/Role URI syntax, Detail content and the sole-Fault
Body rule. Valid fault exceptions keep their existing contract. The XML language
union distinguishes a true empty reset from whitespace-only invalid values.

All **26 affected Qore suites pass: 375 cases / 16,438 assertions**. Five focused
SOAP suites also pass compiled: **16 cases / 5,479 assertions**. The new fault suite
passes **2 cases / 1,098 assertions**, covering 73 explicit cases across source,
saved-object and saved-data services and a 64-level Subcode chain.

Six independent Python gates pass. The new fault gate checks the exact pinned W3C
schema expectations and **444 HTTP response exchanges**, including negative-message
recovery with persistent clients and native/retained decoding. All 16 corpus commands
meet their recorded outcomes. Six semantic reports match P7-03 except for the WSDL
source digest. Documentation and three-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 SOAP 1.1 faults, full fault data/generation and header-fault integration, HTTP/action
rules and applicable assertion accounting remain open, followed by P8–P9. No Qore
edits, installation, push or CI trigger.

See [evidence](soap12-fault-evidence.md), [validation](P7-04-validation.json),
[audit](audits/P7-04-soap12-faults.md), and [design](../../design/soap-envelope-processing.md).


## P7-05: SOAP 1.1 fault grammar and namespace isolation

SOAP 1.1 faults validate required and optional singleton fields, scoped QName codes,
optional language, faultactor URI syntax and detail content while accepting qualified
extensions. Native decoding selects the expanded-name Fault before projection and
retains qualified extension names and in-scope namespace bindings, preventing
collisions with application Body siblings and protocol fields.

All **27 affected Qore suites pass: 377 cases / 17,142 assertions**. Six focused
SOAP suites also pass compiled: **18 cases / 6,183 assertions**. The new SOAP 1.1
suite passes **2 cases / 704 assertions** across source, saved-object and saved-data
services, with additional native/retained namespace-collision checks.

Six independent Python gates pass. The combined fault gate checks the exact pinned
W3C schema expectations and **720 HTTP response exchanges** (276 SOAP 1.1 and 444
SOAP 1.2), including persistent-client recovery after negative messages. All 16
corpus commands meet their recorded outcomes. Six semantic reports match P7-04
except for the WSDL source digest. Documentation and three-file astparser checks
pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 complete fault data/generation, header-fault integration, HTTP/action rules and
applicable assertion accounting remain open, followed by P8–P9. No Qore edits,
installation, push or CI trigger.

See [evidence](soap11-fault-evidence.md), [validation](P7-05-validation.json),
[audit](audits/P7-05-soap11-faults.md), and [design](../../design/soap-envelope-processing.md).


## P7-06: Complete protocol fault data and explicit generation options

Typed fault metadata preserves scoped QName codes/subcodes, ordered multilingual
reasons, actor/node/role references, detail/header/extension values and original XML.
Generic, declared and header-fault serializers accept explicit protocol options.
The audit also corrected SOAP 1.2 encodingStyle placement on protocol fault fields
while preserving permitted application detail encoding and attribute qualification.

All **28 affected Qore suites pass: 383 cases / 18,078 assertions**. Seven focused
SOAP suites also pass compiled: **24 cases / 7,119 assertions**. The new fault-data
suite passes **6 cases / 936 assertions**, covering protocol fields, original XML,
source/saved service graphs, typed serialization, negative recovery and 64 subcodes.

Seven independent Python gates pass. The new three-test gate checks **63 generated
fault variants**, **14 attribute-placement cases** and **462 HTTP exchanges** against
pinned schemas and an independent namespace-aware decoder. The existing fault gate
adds 720 exchanges. All 16 corpus commands meet their recorded outcomes; six semantic
reports match P7-05 except for the WSDL source digest and Qore revision. The final
checks use installed Qore `9d8ce440b`, which includes the verified strict URI fix. Documentation and four-file
astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 header-processor fault mapping, HTTP/action/media rules and complete assertion
accounting remain open, followed by P8–P9. No Qore edits, installation, push or CI trigger.

See [evidence](soap-fault-data-evidence.md), [validation](P7-06-validation.json),
[audit](audits/P7-06-soap-fault-data.md), and [design](../../design/soap-envelope-processing.md).


## P7-07: Handler header faults and application failure boundaries

Declared header-processor faults retain their binding metadata before Body conversion
and dispatch. Application/output failures use Server/Receiver with HTTP 500; protocol
and input faults retain version-specific codes/statuses. Interruption exceptions
propagate. Missing, structured and XML-invalid exception diagnostics produce valid
fault text. Existing client expectations now verify the corrected application behavior.

All **29 affected Qore suites pass: 388 cases / 19,256 assertions**. Eight focused
SOAP suites also pass compiled: **29 cases / 8,293 assertions**. The new handler
suite passes **5 cases / 1,174 assertions**, including both SOAP versions, source and
saved service graphs, native and retained values, action/body routing, fault recovery,
cancellation, and missing/structured/XML-invalid exception diagnostics.

Eight independent Python gates pass. The new gate checks **576 HTTP exchanges**
against unchanged pinned SOAP schemas, independently checking QName fault identities,
status codes, declared header/detail placement, preflight priority and callback counts.
All 16 corpus commands meet their recorded outcomes; all six reports exactly match
P7-06. Installed Qore is `9d8ce440b`, including the verified strict URI fix.
Documentation and four-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 action/media/HTTP rules and complete assertion accounting remain open, followed by
P8–P9. No Qore edits, installation, push or CI trigger.

See [evidence](soap-handler-fault-evidence.md), [validation](P7-07-validation.json),
[audit](audits/P7-07-soap-handler-faults.md), and [design](../../design/soap-envelope-processing.md).


## P7-08: HTTP fault identity and post-processing charset boundaries

SOAP HTTP faults are recognized through MIME/charset decoding and expanded XML
names. Valid UTF-16 and whitespace variants work; fault-shaped application data
retains the original HTTP error. Client and handler reparse generated node XML
as UTF-8 independently of the original wire charset, preserving exact values.

All **30 affected Qore suites pass: 391 cases / 22,088 assertions**. Nine focused
SOAP suites also pass compiled: **32 cases / 11,125 assertions**. The new HTTP fault
suite passes **3 cases / 2,832 assertions**, covering both SOAP versions, source and
saved service graphs, native/retained values, five encodings, fault identity, HTTP
status boundaries, malformed documents and recovery after failures.

Nine independent Python gates pass. The new three-test gate checks **1,806 HTTP
exchanges**: 1,440 encoded fault/success exchanges, 336 transport-error/document
checks, and 30 external-client/handler encoding checks. Generated fixtures validate
against unchanged pinned SOAP schemas and exact Unicode value assertions.
All 16 corpus commands meet their recorded outcomes; all six reports exactly match
P7-07. Installed Qore is `9d8ce440b`, including the verified strict URI fix.
Documentation and four-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 remaining HTTP/action/media rules, one-way/empty responses, interruption and
complete assertion accounting remain open, followed by P8–P9. No Qore edits,
installation, push or CI trigger.

See [evidence](soap-http-fault-evidence.md), [validation](P7-08-validation.json),
[audit](audits/P7-08-soap-http-faults.md), and [design](../../design/soap-envelope-processing.md).


## P7-09: One-way acknowledgments and protocol faults

One-way response decoding reports protocol faults before application-output checks,
accepts whitespace-only empty Bodies, and preserves explicit response-header processing.
SOAP handlers return empty HTTP 202 acknowledgments for successful one-way calls;
processing errors still produce SOAP faults. Success does not imply application delivery.

All **31 affected Qore suites pass: 394 cases / 22,871 assertions**. Ten focused
SOAP suites also pass compiled: **35 cases / 11,908 assertions**. The new one-way
suite passes **3 cases / 783 assertions**, covering source/saved service graphs,
both SOAP versions, direct/native/retained fault handling, generated faults, version
negotiation, whitespace-only Bodies, acknowledgments, header capabilities and recovery.

Ten independent Python gates pass. The new two-test gate checks **228 HTTP exchanges**:
180 external-server/client exchanges and 48 external-client/handler exchanges. It
verifies exact 200/202/204 acknowledgments, optional envelope/header processing,
protocol errors, empty handler bodies with no Content-Type, fault QName identities
against pinned schemas, and callback counts before deterministic shutdown.
All 16 corpus commands meet their recorded outcomes; all six semantic reports match
P7-08 except for the WSDL source digest. Installed Qore is `9d8ce440b`.
Documentation and five-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 remaining HTTP/action/media rules, transport interruption and complete assertion
accounting remain open, followed by P8–P9. No Qore edits, installation, push or CI trigger.

See [evidence](soap-oneway-evidence.md), [validation](P7-09-validation.json),
[audit](audits/P7-09-soap-oneway.md), and [design](../../design/soap-envelope-processing.md).


## P7-10: SOAP request action transport and dispatch

Requests emit version-specific quoted actions. Handlers decode normalized root action
metadata, expose cx.soap_action and reject malformed or mismatched actions before
application dispatch. Route version metadata remains independent of action lookup.
The pinned CXF relative-action source remains a negative control; explicitly named
and hash-recorded corrected bindings drive positive SOAP 1.2 HTTP exchanges.

All **216 Qore suites pass: 3,307 cases / 152,066 assertions**.
Eleven focused SOAP suites also pass compiled: **39 cases / 13,352 assertions**.
The new action suite passes **4 cases / 1,444 assertions** across source/saved service
graphs, native/retained values, raw headers, root media parameters and failure recovery.

All twelve independent Python gates pass. The new two-test gate checks **396 HTTP
exchanges**: 48 external-server/client exchanges and 348 external-client/handler
exchanges. The pinned CXF 4.1.3 gate passes with seven tests, including the explicit
absolute-action derivative and unchanged-source negative controls. All 16 corpus
commands meet their recorded outcomes; all six semantic reports match P7-09 except
for the WSDL source digest. Installed Qore is `9d8ce440b`.
Documentation and thirty-one-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 remaining media/method rules, transport interruption and complete assertion
accounting remain open, followed by P8–P9. No Qore edits, installation, push or CI trigger.

See [evidence](soap-action-evidence.md), [validation](P7-10-validation.json),
[audit](audits/P7-10-soap-actions.md), [CXF source adjudication](cxf-derived/README.md),
and [design](../../design/soap-envelope-processing.md).

## P7-11: SOAP HTTP media and method boundaries

SOAP adapters explicitly validate transport/root media and charset support. Handlers
return plain HTTP 400/405/415 for transport failures and preserve SOAP faults for
recognized-envelope errors. Allow reflects SOAP and explicit HTTP routes; response
validation precedes header callbacks. Invalid request encoding cannot mask the
original error through logging. See [evidence](soap-http-binding-evidence.md).

The **217-suite broad Qore gate passes: 3,309 cases / 152,203 assertions**.
The standards audit then fixed mandatory-header precedence. On that final source,
**35 affected Qore suites pass: 411 cases / 24,802 assertions**.
Thirteen focused SOAP suites also pass compiled: **43 cases / 13,735 assertions**.
The new media/transport suite passes **2 cases / 137 assertions**; mandatory-header
priority passes **2 cases / 246 assertions**.

All fourteen independent Python gates pass on the final source. The new media gate
covers **1,167 HTTP exchanges**; the priority gate adds **192 exchanges** (72 handler,
120 client). Tests check statuses, media/Allow headers, WSDL retrieval, HTTP routes,
invalid bytes, callback counts and recovery across source/object/data service graphs
and native/retained values. All 16 corpus commands meet their recorded outcomes;
all six semantic reports match P7-10 except for the WSDL source digest. Installed
Qore is `9d8ce440b`. Documentation and seven-file AST checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 remains open for transport interruption, complete applicable assertion accounting
and SOAP-response GET MEP applicability/API review; P8–P9 follow. No push or CI trigger.


## P7-12: SOAP transport interruption and cancellation

Independent raw TCP peers verify partial headers/bodies/chunks, event-driven thread
cancellation, peer EOF, callback isolation and same-client/server recovery. Both SOAP
versions, request-response/one-way operations, source/object/data graphs and native/
retained values are covered. Qore's request event and abandonment fixes are verified
on the installed runtime; no XML production workaround was needed.

Six affected native Qore suites pass: **38 cases / 2,223 assertions**. Three independent
Python gates pass, including all **432 new transport exchanges**. The full new matrix
also passes with freshly compiled WSDL, SoapClient and SoapHandler modules (another
432 exchanges). Both peer scripts pass astparser without diagnostics. Installed Qore
is `25346118e`. Audit: **16 Pass / 46 N/A / zero Fail**.

See [evidence](soap-transport-evidence.md), [validation](P7-12-validation.json), and
[audit](audits/P7-12-soap-transport.md). P7 GET and assertion accounting remain open,
followed by P8–P9. No Qore edits, installation, push or CI trigger.


## P7-13: SOAP 1.2 response GET resources

Explicit client retrieval and safe handler-resource APIs reuse selected output/fault
codecs, core request-local URLs and existing response processing. Tests cover both
HTTP directions, GET/POST/WSDL coexistence, route conflicts and removal, immutable
defaults, credential origins, compiled modules and interrupted GET recovery.

Forty affected Qore suites pass: **468 cases / 27,612 assertions**. The new unit
suite passes **4 cases / 156 assertions**. All sixteen independent Python gates pass,
including **336 new HTTP exchanges** and **72 new GET interruption/cancellation
exchanges**. The full transport matrix now covers 504 exchanges. Freshly compiled
WSDL, SoapClient and SoapHandler pass four focused Qore suites (39 cases / 604
assertions), the full new GET matrix and the complete transport matrix.

All 16 corpus commands meet their recorded outcomes; all six semantic reports are
unchanged from P7-11 except for the Qore runtime identifier. The known legacy
projection-loss gate retains its expected exit 1. Documentation and all six changed
Qore files pass documentation/AST checks without warnings or errors. Installed Qore
is `25346118e`. Audit: **19 Pass / 43 N/A / zero Fail**. No C++ change; no Valgrind needed.

See [evidence](soap-response-evidence.md), [validation](P7-13-validation.json), and
[audit](audits/P7-13-soap-response.md). P7 assertion accounting remains open, followed
by P8–P9. No push or CI trigger.

The next P7 assertion review reproduced buffered-upload/early-response deadlock in
core HTTPClient, independently of XML. The core-only and ordinary SOAP reproducers,
positive raw-socket control and source-level root cause are handed off at
`/tmp/qore-httpclient-buffered-duplex/README.md`. The buffered HTTP/1.1 path sends the
whole request before starting response reads; the existing full-duplex branch is
limited to chunked streaming sends. This remains an open P7 dependency, not an
accepted result or an XML workaround.

## P7-14: SOAP full-duplex buffered requests and early responses

Qore fixed the core buffered-upload/early-response deadlock, resolving the P7-13 dependency above. This increment
adds no production code. It supplies executable evidence for the SOAP-level contract:
[soap-duplex](../soap-duplex.qtest) passes 5 cases / 203 assertions over 40 exchanges of 8 MiB, and
[test_soap_duplex.py](test_soap_duplex.py) adds 146 independent exchanges. Both gates prove full duplex rather than
assuming it. `06eef84` adds the `SoapClientIo` async I/O client on `HttpClientIo`. See
[evidence](soap-duplex-evidence.md), [validation](P7-14-validation.json) and
[design](../../design/soap-async-io-client.md).

## P7 assertion accounting

[assertion-ledger.json](assertion-ledger.json) accounts for all 140 W3C SOAP 1.2 Second Edition assertions
(`1205ae7`) and all 353 WS-I Basic Profile 1.2/2.0 requirements (`3a52d68`). 388 rows are covered by 815 verified
executable mappings; 30 are not applicable with specification-based rationale; 49 are recorded WS-Addressing gaps;
26 are routed to P8. [verify_ledger.py](verify_ledger.py) enforces the ledger and was negative-tested against
injected defects. See [evidence](assertion-ledger-evidence.md).

## P7 acceptance

Before acceptance, a full-suite triage fixed or correctly re-scoped every failure outside the P7 sweep. It
corrected SOAP 1.2 fixture actions, stale NOTATION and multipart expectations and the three P6 part round trips
(`138c803`), fixed a recompiled-regex performance defect (`8f1f8b2`), and recalibrated thin hang guards (`eefcf5f`).
On one runtime (Qore `922cd9bb0`), all 271 Qore suites pass **3,581 cases / 172,677 assertions**. 176 of 178
Python gates pass; the two IEEE gates fail only on the documented core NaN-boxing defect and remain required.
All 16 corpus commands match their expected outcomes, with reports semantically unchanged from P7-13. The
CMake-built AOT modules pass 9 suites / 64 cases / 2,650 assertions. Docs, astparser and the ledger verifier are
clean.

See [P7 acceptance](P7-acceptance.md) and [validation](P7-acceptance-validation.json). P8 is next.

## P8-01: Independent encoding sources

The Apache Axis 1.4 rpc/encoded peer and two independent encoded-message corpora are pinned and run offline.
`axis-peer/` holds the six-JAR Maven Central closure and the signature-verified Axis 1.4 source release files:
LICENSE, NOTICE and the SOAPBuilders round 2 interop service. Axis's own client and service complete all 31
round 2 operations on Java 25 (`--release 17`). `encoded-corpus/` holds those 31 exchanges and the 66 W3C SOAP 1.2
test-collection tests that use the SOAP 1.2 encoding or RPC namespaces (150 messages, seven published errata
recorded verbatim). [test_axis_peer.py](test_axis_peer.py) verifies the pins and compares a fresh Axis run with
the corpus in canonical form. See [evidence](encoded-sources-evidence.md),
[validation](P8-01-validation.json) and the [peer](axis-peer/README.md) and [corpus](encoded-corpus/README.md)
READMEs.

## P8-02a: SOAP 1.1 encoded references

Independent elements are found regardless of name repetition. Their SOAP encoding metadata is consumed. The
reference graph is checked up front for dangling, duplicate or invalid ids and cycles. Array members and
fragment references resolve; `SOAP-ENC:Array` and the encoding namespace's builtin type names are accepted; and
a single type-based RPC part serializes its bare struct. [soap-encoded-references](../soap-encoded-references.qtest)
has 7 cases and 52 assertions. 29 of the 31 Axis round 2 operations now decode and re-encode. See the
[design](../../design/soap-encoding.md) and `EXECUTION.md`.

## P8-02b: SOAP 1.1 arrays

Encoded arrays follow SOAP 1.1 section 5.4.2:

- rank-n arrays travel as row-major members with asserted lengths;
- jagged arrays nest member arrays with their own `arrayType`;
- `SOAP-ENC:offset` and `SOAP-ENC:position` place members, with untransmitted and nil members as `NOTHING`;
- the slots an asserted size may allocate are bounded;
- Axis's jagged form of a rank-n declaration is accepted when it is rectangular;
- the qorelanguage/qore#2899 member-name representation is kept;
- a literal element of an encoded array type takes a list as its one value.

[soap-encoded-arrays](../soap-encoded-arrays.qtest) has 9 cases and 68 assertions. All 31 Axis round 2
operations decode and re-encode. See the [design](../../design/soap-encoding.md) and `EXECUTION.md`.

## P8-02c: Live Axis 1.4 interop

[test_axis_interop.py](test_axis_interop.py) runs both directions live. The published contract stays rejected
with its exact `WSDL-ERROR`. The derived contract adds the `xml-soap` Map schema that Axis's own `Java2WSDL`
emits, and it is reproducible, with provenance. Qore's async `SoapClientIo` client verifies all 31 operations
against the Axis service. Axis's `TestClient` verifies all 31 against a `SoapHandler` echo service, which uses
`preserve_types`. That second direction needs a Qore core fix: installed Qore keeps HTTP/1.0 connections open
(handoff `/tmp/qore-http10-keepalive/README.md`). Until the fix is installed, the gate fails at its HTTP/1.0
check. `SoapHandler` now dispatches operations that share a SOAP action by Body element within that action's
operations; a new [soap-actions](../soap-actions.qtest) case covers it. See the
[peer README](axis-peer/README.md) and `EXECUTION.md`.

## P8-02d: SOAP 1.1 Note section 5 examples

The SOAP 1.1 Note's own section 5 examples are an independent fixture source for what Axis never sends:
generic, partial and sparse arrays, mixed member types, polymorphic accessors and multi-reference strings.
Only the 34 quoted examples are committed ([corpus](encoded-corpus/soap11-note.json)), because the Note has no
redistribution terms; its digest is pinned, and the extraction is reproducible. In
[soap11-note-examples](../soap11-note-examples.qtest), 24 instance examples decode as the Note describes, and 3
are rejected with exact errors: 8 cases, 260 assertions. The examples found nine defects, all fixed:
- declared encoding-namespace types, including the generic `SOAP-ENC:Array`;
- instance `arrayType` item types, previously ignored;
- embedded ids;
- element-named members of `anyType` arrays;
- external references;
- `xsi:type` of named restrictions, which Qore itself rejected;
- member-type retention with `preserve_types`;
- generic array output shapes;
- a crash on unresolvable part types.

See the [design](../../design/soap-encoding.md) and `EXECUTION.md`.

## P8-03a: SOAP 1.2 encoding graph

A binding's `encodingStyle` now selects SOAP 1.2 Encoding; previously every encoded body was written with the
SOAP 1.1 URI. `enc:id` and `enc:ref` references span the envelope and may appear inline, and `enc:nodeType` is
validated. Fault codes and subcodes (`enc:MissingID`, `enc:DuplicateID`, `env:DataEncodingUnknown`) reach
`SoapHandler` faults. Two more fixes affect SOAP 1.1 too: encoded structs are matched by member name, and
whitespace between array members is no longer taken as members. An authored
[contract](encoded-corpus/w3c-soap12.wsdl) runs the W3C collection's requests.
[soap12-encoding](../soap12-encoding.qtest) has 6 cases and 74 assertions. See the
[design](../../design/soap-encoding.md) and `EXECUTION.md`.

## P8-03b: SOAP 1.2 arrays

SOAP 1.2-encoded arrays use `enc:itemType` and `enc:arraySize` in both directions instead of SOAP 1.1's
`SOAP-ENC:arrayType`. The rules are selected per part through a thread-local scope. Extents are row-major, an
asterisk may stand only for the first extent (T61), omitted trailing members are `NOTHING`, and the dimension
count must match the declared rank. [soap12-encoding](../soap12-encoding.qtest) has 7 cases and 114 assertions.
The full suite passes on one runtime except the two core-blocked IEEE gates. With the core HTTP/1.0 fix
installed, the Axis interop gate passes in both directions.

## P8-04: SOAP 1.2 RPC Representation and Appendix B

SOAP 1.2 RPC-style bindings with SOAP 1.2 Encoding now follow SOAP 1.2 Part 2 section 4:
- `rpc:result` in both directions, with the return part identified through the WSDL 1.1 `parameterOrder`, which
  operations now retain;
- a single RPC struct in the Body;
- `rpc:BadArguments` and `rpc:ProcedureNotPresent` fault subcodes.

Encoded parameters that are absent or nil decode as `NOTHING`, and `NOTHING` is written as `xsi:nil`; previously
both read and wrote an empty value. `WSDLLib::toXmlName()` and `fromXmlName()` implement Appendix B. The W3C
collection's encoding and RPC tests pass through a `SoapHandler` echo service
([soap12-collection](../soap12-collection.qtest)), with 11 out-of-scope tests and the collection's defective
replies recorded. [soap12-rpc](../soap12-rpc.qtest) adds 7 cases and 79 assertions.

## P8-05a: MTOM/XOP reconstruction and packaging

MTOM input had never worked: the XOP recognizer read regex captures through `$1`, so every MTOM message failed.
`WSDLLib::substXopInclude()` now follows XOP 1.0 sections 2 and 3.2 and SOAP 1.2 MTOM section 4.3.1:
- `xop:Include` is recognized by expanded name wherever its namespace is declared;
- it must be the only child of its element, whose attributes are kept;
- `cid:` references are percent-decoded (RFC 2392), and must name a part that no other `xop:Include` uses.

`packageMtom()` writes `start-info` and takes the XML content type, including SOAP 1.2's, and multipart input
rejects a `start-info` that conflicts with the root. XOP 1.0, SOAP 1.2 MTOM and RFC 2392 are pinned in
`normative/`. [soap-mtom](../soap-mtom.qtest) has 4 cases and 43 assertions. The full suite passes except the two
core-blocked IEEE gates.

## P8-05b: MTOM/XOP output and live CXF exchanges

MTOM output did not exist. `WSDL::SoapMtomScope` now selects it per thread for requests, responses and declared
faults: canonical `base64Binary` content of at least a threshold moves into a binary part referenced by an
`xop:Include`, with `xmime:contentType` as the part's media type. Only referenced parts are packaged, each once
and with its transfer encoding, and an original infoset containing `xop:Include` is sent without XOP (SOAP 1.2
MTOM section 4.3.1). `SoapClient` and `SoapClientIo` take `mtom` and `mtom_threshold` options, and `SoapHandler`
answers MTOM requests with MTOM responses.

Three defects outside MTOM were found and fixed: a route serving one operation in both SOAP versions kept only
the first registration, so the other version's requests failed with `VersionMismatch`; envelope validation read
an absent value as text; and `SoapClientIo` dropped the media parameters of multipart responses.

[soap-mtom-output](../soap-mtom-output.qtest) has 9 cases and 148 assertions, [soap-actions](../soap-actions.qtest)
gains a mixed-version dispatch case, and [test_mtom_xop.py](test_mtom_xop.py) exchanges the unmodified CXF
`mtom_xop.wsdl` contract live with Apache CXF 4.1.3 in both directions, with and without MTOM, each side checking
the other's package form and part count.

## P8-05c-1: SOAP with Attachments references

`href` references in SwA packages now follow the SwA Note, section 3. Before, every reference that was not a
lowercase `cid:` URI raised `SOAP-MESSAGE-ERROR`. That included a same-document `#id`, so encoded messages that
combine multi-reference values with attachments (as Apache Axis 1.x sends them) could not be read.
- A same-document reference keeps its SOAP encoding meaning.
- Any other reference is made absolute against its base URI: `xml:base`, then the root part's `Content-Location`,
  then the package's, then `thismessage:/`.
- The absolute reference matches a part's `cid:` label (RFC 2392 percent-decoding, any case of the scheme) or its
  `Content-Location`, resolved against the package's `Content-Location`.
- Only `href` attributes are references. A reference that matches no part is left for normal resolution.

The SwA Note and WS-I Attachments Profile 1.0 cannot be redistributed. The Note is pinned by digest, with the
section 3 phrases the implementation follows. The profile is pinned as a reproducible requirement extract.
[soap-swa-references](../soap-swa-references.qtest) has 5 cases and 26 assertions. `swaRef` (R2928) follows as
P8-05c-2.

## P8-05c-2: swaRef attachment references

WS-I Attachments Profile 1.0 `swaRef` values (section 4.4, R2928) are now attachment references. Before, they
were plain `anyURI` strings, so no part was ever sent or resolved.
- An element, attribute or message part of type `swaRef`, or of a restriction of it, has the referenced part's
  content as its native value.
- On output, binary data becomes an `application/octet-stream` part and a string a `text/plain` part, and the
  message becomes a SOAP with Attachments package (also combined with MTOM).
- On input, the `cid:` or Content-Location URI resolves to a part of the message; a URI that does not identify
  exactly one part is rejected.
- Envelope values only: XML attachment entities, list items and union members keep URIs, as do retained XML
  values, whose consumers receive the parts in `SoapXmlMessageInfo::parts` and send them with `^parts^`.

[soap-swaref](../soap-swaref.qtest) has 10 cases, and [test_swa_parts.py](test_swa_parts.py) exchanges CXF's
`echoDataRef` live with Apache CXF 4.1.3 in both directions.

## P8-05d: Attachment binary fidelity

Attachment content crosses packages unchanged in both directions. Covered carriers: MIME-bound SwA parts,
swaRef values and MTOM/XOP content, in SOAP 1.1 and 1.2. Payloads:
- empty and single-octet content;
- every octet value;
- delimiter lines;
- runs of CR and LF;
- a 1 MiB line;
- 8 MiB of content;
- 500 parts in one message;
- text in three encodings.

Packages from other senders are framed as RFC 2046 allows, and invalid framing is rejected.
[soap-attachment-fidelity](../soap-attachment-fidelity.qtest) has 6 cases. The live CXF peers exchange
deterministic payloads in both directions: up to 4 MiB for SwA parts and swaRef, and 1 MiB for MTOM.

## P8-06: Message and document limits

**Approved 2026-09-23:** limits are on by default, with these defaults: decoded SOAP-encoded values 10M, resolved
references 100k, array slots per message 16M, array rank 32, XML depth 128, MIME parts 1000, and WSDL/XSD
documents 1000 with import depth 64. They are configurable per WebService, WSOperation, thread
(`SoapMessageLimitsScope`), SoapClient, SoapClientIo and SoapHandler.

**Corrected 2026-09-24:** the XML depth default was first 256. Alpine CI (pipeline 57475) showed that decoding
252 nested levels exceeds an 8 MB thread stack on musl, so the approved default is now 128.

The decompression bomb is a core defect: HttpServer and HTTPClient decompress without a limit. It is handed off
in `/tmp/qore-http-bounded-decompression.md`, and module-xml documents the gap in `max_message_size`.

`SoapMessageLimits` bounds each decoded message:
- **Encoded content:** every decoding of a shared reference is counted, so a reference DAG cannot expand
  exponentially. References, array members (including those behind a zero extent), array rank and nested levels
  are bounded, and lengths are bounded before they are converted.
- **Structure:** element depth is checked on every parsing path before recursive walks. MIME parts are counted.

`max_documents` and `max_document_depth` bound WSDL and schema loading. Interrupted decoding, multipart
parsing and loading leave no state behind. [soap-message-limits](../soap-message-limits.qtest) has 13 cases.

## P8-07: Routed ledger rows and P8 acceptance

All 26 W3C SOAP 1.2 Part 2 assertions routed to P8 are now covered by executable cases, each checked against the
Second Edition text. The three rows that quoted First Edition wording now carry the current sentences, and
`verify_ledger.py` rejects any row still routed to P8. Mapping them found four defects, all fixed:
- struct member labels ignored the namespace name (section 3.1.3);
- the RPC response struct's name was required (section 4.2.2);
- SOAP 1.2-encoded header parts were rejected when the WSDL was loaded;
- coverage for array member names, `xsi:type` precedence, header blocks, `[in/out]` parameters and
  `rpc:BadArguments` for argument count and type was missing, and was added.

**P8 accepted** (2026-09-23), against the phase's acceptance:
- **Pinned CXF contracts, both directions, byte-identical:**
  - `test_swa_parts.py` covers SwA parts and swaRef, up to 4 MiB;
  - `test_mtom_xop.py` covers MTOM/XOP, up to 1 MiB;
  - the local fidelity suite covers the same payloads and boundary edges.
- **Independent encoded-message sources:**
  - live Apache Axis 1.4 exchanges (P8-02c);
  - the SOAP 1.1 Note examples;
  - the W3C SOAP 1.2 test collection gate.
- **Reference semantics:** SwA `href` and swaRef references, the SOAP 1.1 and 1.2 reference graphs and the RPC
  Representation are preserved, with descriptive faults and subcodes for negative messages.
- **Bounded resources:** P8-06 bounds decoding and loading, and interruption leaves no state behind.
- **Literal conformance** stays separate: the WS-I Basic Profile rows are accounted for independently.

Open, outside P8:
- bounded decompression in Qore core (`/tmp/qore-http-bounded-decompression.md`);
- the per-call particle program rebuild (a P9 performance item);
- the 49 WS-I profile gaps recorded in P7 (P9).

## P9a acceptance

P9a is accepted (2026-09-25); see [P9a acceptance](P9a-acceptance.md). WS-Addressing 1.0 Core, SOAP Binding and
Metadata are implemented for WSDL 1.1 SOAP 1.1 and 1.2 services and clients:
- The 49 WS-I rows are covered (45) or not applicable with an approved specification-based rationale (4).
- Live Apache CXF 4.1.3 exchanges pass in both directions for anonymous and decoupled responses.
- The module's own exchanges pass over HTTP/1.1, HTTP/2 and HTTP/3.

P9b (performance) is next. Bounded decompression and the WS-I profile gaps, which were open after P8, are closed
(P8-06 and P9a).
