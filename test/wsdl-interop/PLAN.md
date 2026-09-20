# WSDL/SOAP compatibility implementation plan

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: P1–P5 acceptance is complete under the approved explicit native-capture and retained-XML contracts. P5-22b adds complete typed corpus accounting and an exact-order P5 selection; see [P5 acceptance](P5-acceptance.md). The ordinary decoding default and its documented projection losses remain unchanged and separately reported. P6 binding/component acceptance is complete; see [P6 acceptance](P6-acceptance.md). P7 SOAP processing is next, followed by P8–P9; the recorded QName AOT stack issue remains assigned to P9 runtime acceptance.
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
- Track requirement identifiers, fixture hashes, expected behavior, actual result, fix commit and test
  location. Include response processing, typed-value/infoset comparisons, HTTP behavior and error codes
  in reported coverage. Add assertions that prevent missing/skipped/duplicate cases from improving counts.
- Audit all changes before each commit and publish implemented capabilities/limits, examples, release
  notes and durable design details. Preserve the original findings as evidence and publish a separate
  current result set; do not rewrite the old baseline to conceal failures.

**Final acceptance:** zero unclassified findings or missing corpus dependencies; zero rejected valid
inputs in supported scope; zero serialization failures or invalid outputs for those inputs; no value,
namespace, type, order or binary-content loss; invalid inputs rejected for the intended reason; all
applicable advertised protocol/binding requirements pass in both directions. All required tests pass
without warnings/errors, with no regression skips added to hide a gap. Deliberately unsupported optional
capabilities must be explicit, tested as such and approved as scope decisions, not silently treated as fixed.

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
