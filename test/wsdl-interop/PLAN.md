# WSDL/SOAP compatibility implementation plan

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: P1–P5 acceptance is complete under the approved explicit native-capture and retained-XML contracts. P5-22b adds complete typed corpus accounting and an exact-order P5 selection; see [P5 acceptance](P5-acceptance.md). The ordinary decoding default and its documented projection losses remain unchanged and separately reported. P6 binding/component implementation is in progress, followed by P7–P9; the recorded QName AOT stack issue remains assigned to P9 runtime acceptance.
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
