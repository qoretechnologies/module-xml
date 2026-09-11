# WSDL/SOAP compatibility implementation plan

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: P1 corpus/adjudication, P2 schema/representation, P3 scalar and P4 particle acceptance are complete on `develop`; P5 is in progress with native type identity, annotation ownership, construction-time final exclusions, instance derivation/block/abstract controls and explicit portable native type capture implemented. Explicit schema/message native providers, metadata and HTTP consumers are implemented. Remaining P5 content semantics and P6 binding/part-aware SoapDataProvider integration are open.
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
