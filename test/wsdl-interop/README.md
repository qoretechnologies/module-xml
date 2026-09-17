# WSDL and SOAP interoperability coverage

Copyright (C) 2026 Qore Technologies, s.r.o. The W3C fixtures retain their original copyright notices.

P1–P5 acceptance is complete for the approved explicit native/retained-XML
contracts; [P5 acceptance](P5-acceptance.md) records the current complete typed
coverage and the separately retained legacy projection losses. P6–P9 remain open.
The evidence documents below record their individual implementation increments.

P6-01 implements [binding-specific SOAP versions](binding-version-evidence.md),
including scoped declarations, saved services and actual HTTP exchanges on both
ports. P6-02 fixes [detached operation ownership](operation-ownership-evidence.md),
including legacy saved graphs, shared headers, zero-part messages and deterministic
cleanup. P6 component/parts acceptance and P7 protocol enforcement remain open.

Native empty defaults and declaration-scoped QName identity use
`qore -b --enable-debug test/xml-element-defaults.qtest` and
`python3 test/wsdl-interop/test_element_defaults.py -v`. The latter reproduces
263 documents and checks native verdicts, preserved XML and explicit pinned-Xerces
differences; see [evidence](native-element-defaults-evidence.md) and
[the approved interpretation](default-identity-investigation.md).

WSDL default application and explicit empty-value carriers use
`qore -b --enable-debug test/wsdl-element-defaults.qtest`,
`qore -b --enable-debug test/wsdl-element-defaults-http.qtest` and
`python3 -B test/wsdl-interop/test_wsdl_element_defaults.py -v`.
The binding matrix assesses 200 documents through both SOAP versions, directions,
decoding modes and source/saved services. See the
[implemented design](../../design/wsdl-element-defaults.md). The separate
[NOTATION finding](p5-wsdl-notation-finding.md) and key/unique/keyref remain P5 work.

Native NOTATION declaration, type-use and value checks run with
`qore -b --enable-debug test/xml-notations.qtest` and
`python3 -B test/wsdl-interop/test_notations.py -v`. The authored fixtures cover
64 schemas and 231 documents, including imports and primitive value identity.
The fixture JSON and companion XSD are Copyright (C) 2026 Qore Technologies, s.r.o.
See [the native design](../../design/native-notations.md) and
[evidence](native-notations-evidence.md). WSDL conversion remains assigned to the
separate NOTATION increment.

Particle construction checks run with `qore -b --enable-debug test/wsdl-particle-model.qtest`
and `python3 test/wsdl-interop/test_particle_model.py -v`. Native occurrence validation
uses `test/xml-particle-counts.qtest` and `test/wsdl-interop/test_particle_counts.py`.
Both Python matrices accept `QORE_EXEC_MODE=ast|ir|jit|tiered` and use local modules.
See [the ordered model](../../design/wsdl-particles.md),
[native correction](../../design/xml-particle-counts.md), and
[independent evidence](particle-counts-evidence.md). P4 construction, matching,
serialization and value acceptance are complete; see the P4-13 entry in
[EXECUTION.md](EXECUTION.md).

`test/wsdl-particle-matching.qtest` and `test/wsdl-interop/test_particle_matching.py`
exercise the bounded child-name recognizer, including complete counts, empty/absent
groups, shared references, wildcard namespaces and all permutations. See the
[matching evidence](particle-matching-evidence.md) for independently asserted
validator defects and the boundary between recognition and message conversion.

`test/wsdl-particle-ambiguity.qtest` and `test/wsdl-interop/test_particle_ambiguity.py`
check construction-time unique particle attribution with exact count thresholds,
complete finite-prefix oracles and actual SOAP bindings. The [attribution evidence](particle-ambiguity-evidence.md)
records validator disagreements and the native libxml2 requirements resolved by
the subsequent native attribution and count-range corrections.

`test/xml-particle-identity.qtest` checks native DOM/reader schema position identity.
The [native identity evidence](native-particle-identity-evidence.md) records provider
selection, allocation cleanup and attribution diagnostics.

`test/xml-particle-attribution.qtest` and `test_native_particle_attribution.py`
check exact native counted attribution, component constraints, callback selection
and DOM/reader execution against complete finite languages. The CMake provider
suite also tests exact arithmetic, empty-language summaries and allocation cleanup.
See [the native attribution evidence](native-particle-attribution-evidence.md).
`native_particle_ranges.py` separately checks native large-count requirements;
[P4-06-native-count-ranges.json](P4-06-native-count-ranges.json) records the corrected
results. A completed diagnostic run alone does not make recorded failures pass.

The W3C XML Schema Databinding collection is a useful independent source of WSDL 1.1 descriptions,
XSDs, and SOAP messages. Running it against this module exposed defects that the existing tests missed.
The small regression suite runs offline in the normal `test/*.qtest` CI loop. The larger survey is a
diagnostic tool with explicit failures and coverage limits, not a conformance certification.

See [PLAN.md](PLAN.md) for the phased implementation plan, acceptance checks, and a complete mapping
of the recorded findings and validator disagreements to the work needed to resolve them.
See [EXECUTION.md](EXECUTION.md) for implementation progress and commit/audit evidence.
P3 scalar acceptance is complete; its [acceptance matrix](P3-acceptance.md) and
[requirement/test/commit register](P3-acceptance.json) retain the remaining P4-P9 failures and scope.

`test/wsdl-scalar-consumers.qtest` checks exact scalar values through actual SOAP
1.1/1.2 HTTP exchanges, including invalid-value recovery and encoded reference
lookups. `test_literal_attributes.py` independently checks schema-defined `id`,
`href` and `root` attributes in literal messages. See
[the consumer evidence](literal-attributes-evidence.md).

`test/wsdl-qname-declarations.qtest` and `test_qname_declarations.py` validate
QName enumeration declaration scopes and inherited restrictions. The independent
matrix covers 198 schemas and 396 SOAP binding contracts, including simple content
and forward references. See [declaration evidence](qname-declarations-evidence.md)
for the QName rules and the precisely classified Xerces reserved-prefix result.

`test/wsdl-qname-values.qtest` and `test_qname_values.py` exercise explicit QName
values and namespace-aware detached providers, including reconstructed records,
lists, cancellation and concurrent copies. The independent matrix checks 336
retained envelopes, 2,016 conversion verdicts and 1,008 schema/document pairs.
Native dependency fixes and the separate Python libxml2 empty-namespace
limitation are documented in [qname-values-evidence.md](qname-values-evidence.md).
See the [explicit value contract](../../design/wsdl-qname-values.md) and
[dependency behavior](../../design/xml-qname-validation.md).

`test/xsd-float.qtest`, the native `qore-xml-float-test` CMake target and
`test_ieee_conversion.py` cover strict native IEEE conversion, direct binary32
rounding, exact native number boundaries, signed zero, cancellation and floating-point
environment restoration. The three Python methods check 3,144 conversions with
an integer-rational reference. See the [implemented native conversion design](../../design/xml-ieee-conversion.md).
`test/wsdl-ieee-scalars.qtest` and `test_ieee_scalars.py` integrate strict conversion
with WSDL builtins, providers and example generation. They check 24 real SOAP
contracts, 1,248 input messages, 6,848 provider results and 12,576 rational-reference
conversion verdicts. See the [implemented WSDL scalar contract](../../design/wsdl-ieee-scalars.md)
and [validator evidence](ieee-scalars-evidence.md).
`test/wsdl-ieee-facets.qtest` and `test_ieee_facets.py` cover IEEE restrictions,
fixed attributes, provider choices, list/union identity and adjacent-value examples.
The eight Python methods check 228 value-processing and 40 schema-only SOAP contracts, 2,844 input messages,
16,992 provider results and 1,128 boundary intervals. See the
[implemented facet design](../../design/wsdl-ieee-facets.md) and
[independent evidence](ieee-facets-evidence.md). Eight IEEE corpus families
now belong to the strict gate; this increment leaves the remaining P3 scalar work open.

`test/wsdl-regex-classes.qtest` and `test_regex_classes.py` cover XSD regex
grammar, Unicode class complements, ranges, nested subtraction and bounded
example generation. The independent matrix exercises 156 real SOAP contracts
and exact values through reconstructed providers. Original validator defects
and separately identified equivalent schemas are documented in
[regex-classes-evidence.md](regex-classes-evidence.md). Repetition compilation
limits are covered by the following matrix; neither matrix alone closes P3.

`test/wsdl-regex-counts.qtest` and `test_regex_counts.py` cover valid
repetitions beyond PCRE compilation limits. They exercise exact large values,
nullable atoms, deep grammar, original/reconstructed structural patterns,
provider metadata, cancellation and real bindings in both directions.
[Repetition evidence](regex-counts-evidence.md) describes the independent
validators' count limits and separately identified length-bounded references.
The `XsdPatternConstraint` metadata union preserves existing PCRE strings.

## Native type projection modes

The public decoding default remains `preserve_types=False` for compatibility.
Enable `preserve_types=True` to retain selected dynamic types in native values;
see the [API contract and examples](../../design/wsdl-native-type-values.md).
Type capture alone does not retain the complete XML infoset.

Both `survey.py` and `coverage.py` accept `--preserve-types`. Run each mode into
a separate report; `scope.preserve_types` records the setting. For example:

```sh
python3 test/wsdl-interop/coverage.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 \
  --strict --output /tmp/wsdl-coverage-legacy.json
python3 test/wsdl-interop/coverage.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 \
  --strict --preserve-types --output /tmp/wsdl-coverage-types.json
```

Each mode runs the same complete manifest and strict selection. Legacy failures
remain failures in its report; choosing compatibility does not turn information
loss into a passing result. An enabled type-capture report is not a claim of
complete type/infoset coverage outside its explicit assertions. The survey tests
also check expanded selected type names and unchanged values through actual SOAP
1.1/1.2 bindings in both directions, including invalid selections and facets.

## Sources and intended coverage

| Source | Use |
| --- | --- |
| [W3C XML Schema Databinding examples](https://www.w3.org/2002/ws/databinding/examples/6/09/) and [test suite](https://www.w3.org/2002/ws/databinding/testsuite/) | Independent WSDL/XSD/message pairs for primitive types, facets, namespaces, attributes, groups, inheritance, and wildcards. This is the corpus actually surveyed here. |
| [WS-I Basic Profile 1.2](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/BasicProfile-v1.2.html) and [2.0](https://docs.oasis-open.org/ws-brsp/BasicProfile/v2.0/BasicProfile-v2.0.html) | Requirement matrix for interoperable WSDL 1.1 and SOAP 1.1/1.2 respectively, including messages, bindings, actions, and faults. Use the [WS-I assertions](https://ws-i.org/Testing/Tools/2005/01/BP11_TAD_1-1.htm) for the older Basic Profile 1.1 checks. These profiles have not been fully tested by this survey. |
| [W3C SOAP 1.2 assertions and test collection](https://www.w3.org/TR/soap12-testcollection/) | Protocol tests for envelope structure, roles, `mustUnderstand`, faults, encoding, and HTTP bindings. These require a purpose-built local service/intermediary harness beyond WSDL parsing. |
| [Apache CXF WSDL fixtures](https://github.com/apache/cxf/tree/main/testutils/src/main/resources/wsdl) | Additional implementation interoperability cases: `doc_lit_bare.wsdl`, `hello_world_rpc_lit.wsdl`, `hello_world_soap12.wsdl`, `header_doc_lit.wsdl`, `header_rpc_lit.wsdl`, `no_body_parts.wsdl`, `mtom_xop.wsdl`, and `swa-mime.wsdl`. Pin a commit and all imports when adding these. They are candidates, not tested results in this report. |

Keep WSDL 2.0 tests separate: the current `WebService` parser consumes WSDL 1.1 `definitions`.
Keep legacy RPC/encoded compatibility separate from WS-I profile conformance; Basic Profile literal-binding
requirements do not certify SOAP encoding support. Public demo endpoints are unnecessary for these tests.

## Reproduce the regression tests

From the repository root:

```sh
qore --enable-debug test/wsdl-interop.qtest
qore --enable-debug test/wsdl-namespace-context.qtest
python3 test/wsdl-interop/test_survey.py -v
python3 test/wsdl-interop/test_corpus.py -v
```

The Qore suite uses eight unmodified W3C WSDL/XSD pairs and 48 selected SOAP messages across SOAP 1.1 and
1.2. It validates incoming payloads and serialized request/response payloads with libxml2, checks boolean
and unsigned values, and exercises unsigned boundaries, out-of-range rejection, and native/string IEEE
special values. It imports the development `qlib/WSDL.qm` using a relative path. No public service is called.
The W3C WSDLs bind SOAP 1.1; receiving their supplied SOAP 1.2 payloads tests decoding, not negotiation or
SOAP 1.2 outbound binding selection.

The archive's unsigned cases numbered 02 (`-0`) and 03 (`+42`) are invalid under the selected XSD 1.0
unsigned lexical rules, which allow digits without a sign. They remain in the survey and the source
adjudication's negative cases. Xerces accepts these spellings; `normative.py` independently checks the
XSD 1.0 rule. The Qore numeric regression subset uses ordinary positive values and maxima; production
rejection of the invalid signed inputs is implemented in P3-01. The small survey now serializes
48 valid inputs and rejects all 16 signed unsigned inputs with `SOAP-DESERIALIZATION-ERROR`.

The Python tests require Python 3.10+, `lxml`, and Qore's `json` module in addition to `xml`. They test the
real Qore subprocess, version selection, fixture checksums, empty input, namespace preservation,
malformed messages, offline resolution, and separation of input/output validation failures.
They also verify that missing, duplicate, malformed, or out-of-order worker results fail the survey.

Native schema attachment and resource loading have separate checks:

```sh
qore -b --enable-debug test/xml-reader-schemas.qtest
python3 test/wsdl-interop/test_schema_resources.py -v
python3 test/wsdl-interop/test_schema_uris.py -v
python3 test/wsdl-interop/test_schema_uri_oracle.py -v
python3 test/wsdl-interop/test_qname_union_validator.py -v
```

Use the local module through `QORE_MODULE_DIR`. The resource tests use independent
loopback HTTP/HTTPS servers and ephemeral certificates generated by `openssl`.
With a module built against libxml2 advertising `LIBXML_FTP_ENABLED`, also run
`python3 test/wsdl-interop/legacy_schema_ftp.py -v`. This compatibility check
does not bypass the production dependency probe. See
[schema attachment evidence](xml-reader-schemas-evidence.md) for the exact build,
memory checks. The original URI-resolution finding remains historical evidence;
the exact source now has a native regression. See the
[URI implementation](../../design/xml-schema-uris.md) for XSD anyURI, XML Base,
runtime hints, URI identity and the separate Xerces XML Base disagreements.
`cmake --build build-debug --target qore-xml-namespace-probe qore-xml-uri-allocation`
builds the offline native behavior and allocation-failure checks. Run those
executables under Valgrind as well as the affected Qore suites. Set `QORE_EXEC_MODE`
to run the Python resource/URI tests in AST, IR, JIT or tiered mode (default: JIT).

Standalone ENTITY validation has separate checks:
`qore -b --enable-debug test/xml-entities.qtest`,
`python3 test/wsdl-interop/test_entity_context.py -v` and the native
`qore-xml-entity-allocation` target. They cover declaration context, ordered
unions, list facets, schema construction, allocation failures and partial-result
cleanup. The standalone Xerces entry permits internal declarations with external
resources disabled; the SOAP oracle continues to prohibit DOCTYPE. See the
[native contract and validator differences](../../design/xml-entity-validation.md).

XSD 1.0 union composition has separate scalar and interoperability checks:
`qore -b --enable-debug test/wsdl-union-composition.qtest` and
`python3 test/wsdl-interop/test_union_composition.py -v`. They distinguish direct
restrictions from nested union member composition while preserving primitive
selection, list constraints, shared graphs and detached provider behavior. See
[the implemented design](../../design/xsd-union-composition.md).

## Fixture provenance

The first P2 increment covers declaration-local namespaces, distinct no-namespace
type identity, standalone schema reconstruction, failed-addition rollback and ordered
schema grammar. `ElementTypeDefaultNamespace` is included in the strict gate with
exact string comparisons in both directions. The derivation increment adds both empty
extension fixtures. Attribute construction and scalar `anySimpleType` support add
four families with exact text/attribute checks. The local element-form fix adds
ElementFormUnqualified. Qualified-attribute checks add four source-invalid families
to mandatory rejection coverage. AttributeFormQualified, AttributeReference and
AttributeReferenceUnqualified retain exact attribute and child values in the strict gate:
38 descriptions and 140 message-direction combinations.
Other broad failures remain visible with their later-phase ownership. P2 acceptance
and evidence are recorded in EXECUTION.md.
See [the implemented design](../../design/wsdl-schema-identity.md) and [execution record](EXECUTION.md).

The current full Python suite reports a P6 binding-version failure in the authored
dual-binding contract: selecting SOAP 1.1 emits a SOAP 1.2 envelope. Its request and
response assertions remain failing. P2 payload checks execute before those assertions;
separate actual SOAP 1.1/1.2 contracts check attribute values and namespaces in both
directions. The strict corpus gate does not replace the full suite or phase acceptance.

Compositor namespace checks cover declarations on `sequence`, `choice`, and `all`,
nested/default scopes, deferred references and restoration after errors. Run
`qore --enable-debug test/wsdl-compositor-context.qtest` and
`python3 test/wsdl-interop/test_compositor_context.py -v` with the local core module
path described below. Actual SOAP 1.1/1.2 bindings exercise request and response
payloads against libxml2 and pinned Xerces, with exact child names and values.
The Python test also retains four failing subtests for
`P4-nested-choice-exclusivity`: a choice nested in a choice currently flattens its
alternatives together and accepts an independently invalid combination. This
particle-model defect is assigned to P4 and is not a passing namespace check.

`qore --enable-debug test/wsdl-array-context.qtest` covers array annotation scopes,
canonical item lookup, same-local-name and no-namespace items, schema-addition
rollback, provider metadata, reconstruction and captured output prefixes across
added/nested schema contexts. These are P2 schema identity checks; complete legacy
array wire semantics and SOAP-version encoding requirements remain assigned to P8.

The attribute-extension source places `gender` on a string child that does not declare
it. [Separately identified derivatives](derivatives/manifest.json) move that attribute
to its declared parent, recording original/derived hashes and the two exact byte
substitutions. Independent validators and both request/response paths verify the
corrected parent's attribute and inherited child's text. The original remains an
invalid-source rejection requirement; its schema-valid output after dropping the
misplaced attribute is not a conformance pass.

All files under `w3c/`, except our checksum manifest, are copied byte for byte from:

```text
https://www.w3.org/2002/ws/databinding/testsuite/releases/testsuite-latest.zip
SHA-256: 510b1528e5bdaee527c416524e6462c73f5e82b5237af4a4f7fef65904b90aca
Archive path: databinding/examples/6/09/<pattern>/<filename>
Retrieved: 2026-09-07
```

The archive's generated examples identify `examples.xml` revision 1.57 dated 2008-02-20. The website's
current examples need not be byte-identical to this archive. `w3c/manifest.json` records every copied file's
SHA-256. Each fixture preserves the W3C copyright and links to the
[W3C document use terms](https://www.w3.org/Consortium/Legal/copyright-documents) and
[IPR notice](https://www.w3.org/Consortium/Legal/ipr-notice). Local code is not part of the W3C test suite.

## Reproduce the full survey

The original archive is pinned offline at `corpus/w3c-databinding.zip`.
`corpus/inventory.json` records the sizes and SHA-256 hashes of all 4,191 original files,
including HTML, standalone XML, and WSDL 2.0 artifacts that are outside the survey's execution scope.
Extract into a **new** directory, or verify an existing extraction:

```sh
python3 test/wsdl-interop/corpus.py --extract /tmp/wsdl-corpus
# Alternatively, verify every original file in an existing extraction:
python3 test/wsdl-interop/corpus.py --verify /tmp/module-xml-wsdl-survey
```

Extraction validates archive/member hashes, paths, file types, and resource bounds before publishing
the extracted directory. It refuses existing destinations and cleans up staged files on failure or
interruption. The destination must not be created concurrently. No network access is needed.

Then run:

```sh
python3 test/wsdl-interop/survey.py \
  /tmp/wsdl-corpus/databinding/examples/6/09 \
  --soap-version both --catalog test/wsdl-interop/corpus/catalog.json \
  --output /tmp/wsdl-survey.json
```

Use `--soap-version both` to include both supplied envelope versions; the default is `11`.
Use `--qore /path/to/qore` to select the executable. The driver always enables Qore debugging and uses
the local WSDL module. It records the module checksum, input checksums, Qore version, and lxml/libxml2
versions. `--catalog` adds the checksum-verified imports to both Qore's async cache and the independent
validator's resolver. Nested relative imports retain the source URI as their base. Unknown resources,
conflicting cache entries, malformed catalogs, and changed bytes fail explicitly; neither Qore nor the
validator downloads schemas. Omitting `--catalog` reproduces the original missing-resource conditions.

The four W3C static dependency URLs and SOAP 1.1 encoding URL are recorded in `corpus/catalog.json`,
with retrieval dates, hashes, original bytes, and provenance. Four contain XML schemas with no further
imports. **W3C's `Imported.xsd` currently returns HTTP 200 with zero bytes**, also confirmed by its
[published directory index](https://www.w3.org/2002/ws/databinding/examples/6/09/static/).
The catalog preserves that empty source; it does not supply an invented schema. Parsing it must fail:
an XML document requires a document element ([XML 1.0 §2.1](https://www.w3.org/TR/xml/#sec-well-formed)).
Both independent validators reject the empty document. The `ImportSchema` wrapper also references an
element absent from the pinned graph. These source defects are recorded explicitly in the adjudication.
No missing dependency is counted as successful validation.

Schema compilations use separate parsers. A resolver exception in one schema must not contaminate the
next schema's diagnostics; the previous shared parser incorrectly attributed `ChoiceChoice` and
`SchemaVersion` oracle results to unrelated missing imports. Historical findings remain unchanged.

The driver exits successfully when it has produced a complete diagnostic report, even if that report
contains compatibility failures. Worker errors, warnings, incomplete output, timeouts, and invalid corpus
paths fail the command. Review `counts` and `rows`; a zero exit code does not mean conformance.

The checks are WSDL parsing, decoding supplied requests, serializing their values, and independent XSD
validation of payloads before and after serialization. It does not prove value equality for every datatype,
validate the complete WSDL grammar, validate the SOAP envelope against its schema, or test HTTP behavior.
In particular, schema-valid output can still lose decimal precision, timezone information, or dynamic type
information; those require explicit value and infoset assertions.

## Independent source adjudication

The second oracle is Apache Xerces-J 2.12.2, pinned by SHA-256 in `oracle/manifest.json` with the
unmodified Maven JAR and its embedded license/notices. A JDK 11+ (`java`, `javac`) is required.
The worker compiles with `-Xlint:all -Werror`, runs with a 256 MiB heap and a 60-second deadline, and
accepts at most 10,000 schema/document/resource blobs with 64 MiB aggregate raw content. Imported
resources are supplied as bytes; unlisted locations and DTDs are rejected. Tests exercise malformed
results, missing dependencies, duplicate IDs, cancellation and cleanup. Nothing is downloaded at run time.

```sh
python3 -m unittest discover -s test/wsdl-interop -p 'test_*.py' -v
python3 test/wsdl-interop/adjudicate.py /tmp/wsdl-corpus/databinding/examples/6/09 \
  --strict --output /tmp/wsdl-adjudicated.json
```

`--strict` on this command means **every source disagreement is adjudicated**, not that Qore conforms.
The report assesses every payload against the actual inline schema and the separately supplied echo
schema using both libxml2 and Xerces. It also records expanded component names, request and response
message references, parts, bindings, ports, and original/derived-extraction checksums. The SOAP 1.2 input
samples still belong to SOAP 1.1 WSDL bindings; their schema validity is not SOAP 1.2 binding coverage.
Extra source files, altered originals, duplicate cases, undocumented decisions and stale entries fail.

[adjudications.json](adjudications.json) contains specification decisions and P1–P9 ownership;
[adjudication-report.json](adjudication-report.json) contains all 293 echo WSDLs, 1,136 messages and
three retained historical unassessed outputs. The source assessment finds 14 invalid generated WSDLs,
88 invalid messages, and 1,048 valid payloads. All three historical unassessed outputs validate.
These counts do not establish preserved typed values or production rejection of invalid messages.
[current-report.json](current-report.json) retains the separate Qore diagnostic results.

The adjudication explicitly distinguishes:

- missing echo wrappers, unresolved element references, the `ImportTypesNamesapce` spelling and
  invalid nested `wsdl` content generated from whole-schema patterns;
- valid arbitrary-size decimal/integer literals beyond libxml2's precision limit, with exact-value
  predicates that detect rounding and exponent output;
- invalid ENTITY/ENTITIES references to parsed or undeclared entities;
- the corrected XSD 1.0 `gMonth` syntax and timezone bounds (including erratum E2-12);
- invalid qualified attributes, strict wildcards, content and occurrence counts;
- four additional IDREF/IDREFS families whose dangling references Xerces rejects and libxml2 accepts,
  assigned to P5;
- Xerces acceptances of signed unsigned values and obsolete `gMonth` spellings, which are overridden
  by executable normative assertions rather than counted as valid source inputs.

Source defects do not remove the corresponding feature from the implementation plan. The aggregate
`examples.xsd`/`examples.wsdl` sources contain a relative import resolving to a W3C URL that returns
404 (`examples/6/static/RelativeIncluded.xsd`). This invalid source location is adjudicated separately
in `corpus/source-defects.json`; no replacement is mapped to that URI. Their bytes remain pinned and verified.

## Pinned CXF contracts

All eight candidate contracts listed above are now pinned at Apache CXF tag `cxf-4.1.3`, commit
`5b660b5f9d26ae1e606c6291e8beb61ef0d7fcc8`, under `cxf/`, along with the `header.xsd` import and license/
notice files. `cxf/catalog.json` records original URLs, hashes and the complete import graph. The
location-less SwA namespace import is satisfied by a second inline schema. The fixtures are reserved
for P6–P8; pinning and metadata inspection do not claim runtime interoperability. `no_body_parts.wsdl`
omits the body `parts` attribute inside MIME multipart; an explicit empty `parts=""` is a distinct case
covered separately by the component-inventory tests and required by P6.

## Strict Qore selection and complete diagnostic coverage

```sh
python3 test/wsdl-interop/coverage.py /tmp/wsdl-corpus/databinding/examples/6/09 \
  --strict --output /tmp/wsdl-coverage.json
```

This command runs all 293 echo descriptions and both request and response processing for every one of
the 1,136 original SOAP inputs (2,272 message/direction combinations). It verifies the original hashes
and records the actual inline schema hash, expanded message/part names, service, port and binding for
each direction. The worker explicitly selects that binding and operation. Every serialized body is
retained and independently checked with libxml2 and Xerces. Output envelope versions are checked against
the selected binding; the W3C SOAP 1.2 inputs still exercise a SOAP 1.1 contract.

`--strict` requires the explicit [strict-selection.json](strict-selection.json) to pass: 130 WSDLs,
including all 14 source-invalid descriptions, and 1,260 selected message/direction combinations. Positive
cases require independent exact-value assertions; negative cases require the intended exception category.
Missing, duplicate, stale, malformed or unclassified entries fail. This selection is deliberately named
and bounded; it does not turn known implementation failures elsewhere into passing conformance tests.

`test_boolean_lexical.py` adds 616 independently validated input/output documents:
356 lexical inputs and 132 outputs across simple content, attributes, lists and
boolean/integer unions, plus 128 native provider/example outputs. Both actual SOAP
bindings and both directions are exercised with libxml2 and pinned Xerces. Tests
compare boolean values, reject malformed spellings with the intended exception,
and verify that provider lists retain `false` through Serializable reconstruction.
List item boundaries use all four XML whitespace characters. This extends the
existing strict boolean families without changing their scope or original bytes.

`test_decimal_lexical.py` adds 784 independently validated documents: 432 lexical
inputs, 160 serialized outputs and 192 native provider/example outputs. Real SOAP
1.1/1.2 bindings exercise both directions, attributes, simple content, lists,
unions, CDATA and Serializable reconstruction. Python Decimal verifies exact
values and Xerces checks every document. The already adjudicated old-libxml2
24-digit limitation remains explicit; newer libxml2 versions may accept all valid
decimals. Qore 3.0 supplies shortest round-trip native float/number formatting,
while XML decimal text retains its precision and noncanonical spellings.

[coverage-report.json](coverage-report.json) preserves the complete current ledger, including 92 failed
requirements assigned to remaining phases. Its stage accounting includes unreachable, missing, skipped and
unassessed work. In this run 904 value/infoset assessments remain unimplemented, explicitly counted as
unassessed. Successful schema validation is insufficient to close them. Exact numeric checks now pass
all eight formerly failing decimal output cases. Decimal attributes, elements and retained decimal
patterns belong to the strict gate, alongside all thirteen integer builtin families, including original
invalid inputs and exact values in both directions. Signed bounded types use the independent integer
value comparator; their builtin range rejection is also covered by the authored boundary matrix.
Valid large integer values that preserve their exact number override only the documented libxml2
precision limitation; new oracle disagreements remain failures.

The tests also exercise the unmodified CXF `hello_world_soap12.wsdl` with distinct `sayHi` request and
response body elements, a real SOAP 1.2 binding and independently asserted response text. This is local
operation coverage; HTTP peer interoperability remains assigned to P6–P8. Worker tests cover real process
termination/reaping on cancellation, deterministic readiness, temporary-file cleanup, missing stages,
and a schema-valid changed boolean that the strict value gate rejects.

## Whole-archive source accounting

```sh
python3 test/wsdl-interop/archive_roles.py /tmp/wsdl-corpus --output /tmp/wsdl-archive.json
```

[archive-report.json](archive-report.json) assigns a role and provenance to all 4,191 original files.
It checks that all 293 standalone pattern schemas are exact duplicates of their echo schemas, and
compares all 568 bare echo payloads and 568 raw fragments with their corresponding SOAP source content.
The 293 WSDL 2.0 descriptions remain explicitly outside this plan. Historical toolkit scripts, logs
and configuration are retained as data; the scripts are never executed.

The 48 schema/import edges resolve to pinned resources, optional location-less imports, or adjudicated
invalid sources (the empty `Imported.xsd` and two aggregate references to the URL returning 404).
Unknown dependencies, extra source files, duplicate identities and changed source copies fail the run.

Eighteen additional schema/WSDL artifacts receive schema-oracle and Qore parse results. Two historical
toolkit WSDLs and the aggregate schema/WSDL violate the XSD schema grammar by placing imports after
declarations. All 1,136 entries in the aggregate SOAP lists use unqualified echo wrappers; each entry is
linked to the corresponding qualified per-case fixture and its required expanded root name. These are
source defects, supported by the [schema grammar](https://www.w3.org/TR/xmlschema-1/#element-schema) and
[element validity rules](https://www.w3.org/TR/xmlschema-1/#cvc-elt).

Nine valid historical descriptions originally reproduced the local default-namespace type-resolution
defect. Their source lines and expanded type identities are retained. All fourteen valid supplemental
contracts now parse after the namespace and builtin-base fixes. The four invalid sources fail the explicit
ordered schema grammar check, which is credited independently of namespace/import failures.
The full WSDL grammar matrix remains assigned to P6. The 16 output-oracle
disagreements for unchanged invalid IDREF/IDREFS content are separately adjudicated using expanded
names and token values, preserving their existing P5 rejection failures.

## Results, 2026-09-07

Results below include the numeric fixes in this change, using the pinned archive, Qore 3.0.0, and the
Python validator's libxml2 2.12.10. See [findings.json](findings.json) for retained failure evidence and
environment details; regenerate a full report to obtain all successful rows and every input checksum.

| Check | Result |
| --- | --- |
| WSDL 1.1 descriptions inventoried | 293 |
| Supplied SOAP 1.1 messages inventoried | 568 |
| WSDLs parsed / failed | 271 / 22 |
| Messages decoded / failed | 493 / 58; 17 messages could not reach decoding because their WSDL failed |
| Decoded values serialized / failed | 492 / 1 |
| Serialized payloads accepted / rejected / unassessed by XSD oracle | 465 / 24 / 3 |
| Supplied payloads accepted / rejected / unassessed by XSD oracle | 510 / 52 / 6 |
| Oracle-valid inputs rejected during decoding | 52 |
| Oracle-valid inputs decoded but rejected during serialization | 1 |
| Oracle-valid inputs producing oracle-invalid output | 11 |

These are stage counts, not percentages of standards compliance. Some generated descriptions have missing
echo wrappers or incorrect references. Five WSDLs need imports absent from the archive/cache. Some source
payloads disagree with the validator, including unsigned signed-zero examples, enormous integers, and
ENTITY/ENTITIES examples. Such results need manual standards analysis or a second XSD processor; they
must not all be labeled module defects. The report records these separately.

Before the fixes, serialization failed on six decoded values; it now fails on one. Two additional
oracle-valid messages previously produced invalid lowercase infinity; their outputs now validate.

## Fixed defects

`XsdBaseType::serializeValue()` checked `unsignedShort` and `unsignedInt` against the signed maxima
32767 and 2147483647. It now uses the XSD maxima 65535 and 4294967295. The W3C element and attribute
fixtures reproduce both defects. Negative values and the first values above the unsigned maxima remain
rejected. See [XSD unsignedShort](https://www.w3.org/TR/xmlschema-2/#unsignedShort) and
[unsignedInt](https://www.w3.org/TR/xmlschema-2/#unsignedInt).

Floating-point decoding returns native IEEE values. Serialization previously passed native infinities and
NaN to generic XML formatting, producing lowercase spellings, although the string inputs `INF`, `-INF`,
and `NaN` worked. Serialization now maps native special values to the required XSD spellings. See
[XSD float lexical representation](https://www.w3.org/TR/xmlschema-2/#float-lexical-representation).

## Remaining findings and priorities

These issues remain open. No full compliance claim is justified by the current results.

| Priority | Reproducer | Finding and cause |
| --- | --- | --- |
| High | `SequenceChoice` | A choice preceding `Cvalue` is serialized after it. `XsdComplexType::serializeValue()` emits `elementmap` before separately stored choices, losing compositor order. Two independently valid inputs produce invalid output. |
| High | `ElementFormUnqualified` | A local `form="unqualified"` element is emitted in the target namespace. Element serialization uses the complex type's `usedocns` setting and does not honor the local form override. |
| High | `QNameElement`, `QNameAttribute` | QName text such as `ex:QNameElement` is retained while the `ex` namespace declaration is lost. Base QName handling treats the value as a string; output namespace allocation is independent of the value's original context. |
| High | `ExtendedSequenceLax`, `ExtendedSequenceSkip`, `ExtendedSequenceStrict` and related `Other`/`Any` examples | Wildcard children lose their original namespaces on the decode/encode path. Six valid inputs produce invalid output. Namespace context must survive in the value representation. |
| High | `IntSimpleTypePattern`, `DateSimpleTypePattern`, `DecimalSimpleTypePattern`, float/double variants | `XsdSimpleType::deserializeValue()` converts values before validating lexical patterns: `009` becomes `9`, and dates acquire Qore formatting. Patterns must inspect the normalized XML lexical form, while numeric facets inspect the value. |
| High | `FloatEnumerationType`, `DoubleEnumerationType` | Enumeration membership uses lexical hash keys after converting values to floating point. Equivalent scientific-notation values then fail membership. Enumeration needs value-space comparison. |
| High | `SequenceMinOccurs0`, `SequenceMaxOccursUnbounded`, `ChoiceMaxOccursUnbounded`, related group cases | Model groups are flattened into element/choice maps. Group cardinality and ordered repetitions are not represented sufficiently, so valid optional/repeated sequences and choices fail. Simply relaxing member occurrence checks would not preserve ordering. |
| Medium | `ExtendedSimpleContent`, `LocalAttributeSimpleType` | Attributes without an explicit `type` or with an anonymous `simpleType` leave `XsdAttribute.type` unset; decoding calls a method on NOTHING. Attribute defaults and anonymous type resolution need implementation. |
| Medium | `AnyTypeElement`, `AnySimpleTypeElement`/`Attribute`, `MixedContentType`, `SubstitutionGroup`, `TypeSubstitutionUsingXsiType` | Further supported-representation gaps: untyped content, mixed text, substitution-group selection, and preserving a derived type for reserialization. The report retains concrete failures; full implementation requires more than parser acceptance. |
| Medium | `ElementTypeDefaultNamespace`, `GlobalComplexTypeEmptyExtension`, related `anyType` derivations | QName resolution gaps during parsing: declarations can change namespace context locally, and some complex base types are resolved through the named-type registry rather than the builtin-type path. These deserve reduced schema tests before changing resolution. |
| Medium | `DateElement`, `DateTimeElement` and attribute variants | Valid five-digit years reach Qore's date parser and fail. Check the date representation and parsing boundary, including timezone and precision preservation, before choosing the API behavior. |

The next acceptance checks should include schema-valid output **and** preserved values/expanded QNames,
negative messages rejected for the intended reason, and independent client/server exchanges using a pinned
CXF or other SOAP implementation. Add WS-I requirements and W3C SOAP 1.2 protocol assertions as explicit
tests for actions, empty bodies, one-way operations, binding selection, faults, roles/`mustUnderstand`, and
attachments. Keep unsupported features and unresolved findings visible rather than marking them as passing.

## P2 attribute consumer regression

Run `qore --enable-debug test/wsdl-attribute-consumers.qtest` from the repository
root for provider metadata and generated examples. The independent
`test_attribute_values.py` test runs `attribute-consumers.qr` against separate
actual SOAP 1.1/1.2 bindings and validates both request and response outputs with
libxml2 and pinned Xerces. Exact typed defaults, fixed values, child values and
qualified attribute names are asserted; schema validity alone is insufficient.
The worker has a thirty-second deadline and uses temporary local descriptions.

Simple-content provider coverage requires the Qore DataProvider fix in commit
`5c8899669` (required hash fields followed by defaulted fields). With sibling
`module-xml` and `qore` checkouts, test it without installing:

```sh
cmake --build ../qore/build --target DataProvider-qmod
QORE_MODULE_DIR="$PWD/../qore/build/qlib-qmod/DataProvider:$PWD/../qore/qlib" qore --enable-debug test/wsdl-attribute-consumers.qtest
QORE_MODULE_DIR="$PWD/../qore/build/qlib-qmod/DataProvider:$PWD/../qore/qlib" python3 test/wsdl-interop/test_attribute_values.py -v
```

The explicit DataProvider artifact directory keeps these tests on the rebuilt
Release module if another build changes the source-tree qmod symlink. Use the same
module path for the other Qore suites and Python subprocess tests in this directory.

The worker now passes all twelve examples, including simple content, through provider
conversion before serialization. `getFields()` exposes `^value^` and `^attributes^`;
scalar choices are on `^value^`. Existing callers with valid bare scalars retain
scalar outputs when every attribute is optional. Required attributes require the
structured representation. Serializable schema and provider objects retain this contract.

Incoming document element namespace checks are covered by
`test/wsdl-element-namespaces.qtest`, the real HTTP `SoapHandler.qtest` regression,
and `test_element_namespaces.py`. The latter validates 56 original/emitted
documents with both independent validators and checks exact names, order,
lexical values and retained QName bindings across actual SOAP 1.1/1.2 bindings
in both directions. Declared elements retain the existing native record fields;
wildcard elements use expanded XML keys. The generic expansion/restoration API
is described in [the schema identity design](../../design/wsdl-schema-identity.md).
`test/wsdl-element-collisions.qtest` and `test_element_collisions.py` cover
same-local-name declaration collisions, including providers and generated
examples. The independent suite checks 136 documents, with positive and negative
names/values through actual SOAP 1.1/1.2 request/response bindings. Unambiguous
fields keep their local names; colliding fields use expanded names in every
public record consumer. `test/wsdl-message-identity.qtest` and
`test_message_identity.py` cover multipart WSDL argument identities, part-scope
QNames and body/header separation. Their independent matrix checks 160 element
documents and provider/example reconstruction. The eight integer lexical
subtests now pass; the existing P4/P6 subtests remain visible failures.
Retained XML consumer integration is described below; wildcard validation
semantics remain assigned to P5.

`test/wsdl-attribute-derivation.qtest` checks inherited required/fixed constraints,
builtin/named/list/union ancestry, duplicate extension uses, expanded attribute
collisions, inline simple-content bases, provider values and reconstruction.
`test_attribute_derivation.py` checks 44 schema variants through both actual SOAP
bindings and 40 request/response payloads with exact attribute values. Its schema
matrix records libxml2's acceptance of dropped/changed base fixed constraints as
an oracle defect; XSD 1.0
[derivation-ok-restriction.2.1.3](https://www.w3.org/TR/xmlschema-1/#derivation-ok-restriction)
requires preservation, and pinned Xerces rejects those declarations. Omitted
attribute uses remain inherited, as specified by the complex-type property mapping.
Attribute wildcard composition and full derivation/facet restrictions retain
their P2/P3/P5 ownership in the execution record.

`test/wsdl-mixed-base.qtest` and `test_mixed_base.py` cover simple-content
restriction of named mixed bases, nested sequence/choice/all/group emptiability,
effective mixed flags, empty-extension inheritance and group graph errors.
The independent matrix checks 35 schemas and 28 documents across actual SOAP
1.1/1.2 bindings, both directions, reconstructed providers and generated examples.
It records two libxml2 disagreements: outer restriction facets on a mixed base
are ignored, and `complexContent mixed="false"` incorrectly retains an outer
`complexType mixed="true"`. Xerces and Qore enforce the XSD 1.0 complex-type
property mappings; the exact differing verdicts remain asserted in the test.

`test/wsdl-declaration-constraints.qtest` and `test_declaration_constraints.py`
cover exclusive type declarations, local/global/reference properties, empty
declarations, legal boolean spellings, ID-derived value constraints and merged
ID attribute uses. The independent tests check 94 schemas through 188 actual
binding parses and 24 SOAP documents, including reconstructed services,
providers and generated examples. Fourteen libxml2 disagreements and two Xerces
disagreements are explicitly asserted against the cited XSD 1.0 requirements;
Qore rejects the invalid schemas. Runtime ID/IDREF binding and general element
default/fixed semantics remain assigned to P5.

`test/wsdl-attribute-wildcards.qtest` and `test_attribute_wildcards.py` cover
attribute wildcard construction, imported/nested group intersections, extension
unions, restriction admission/subsets, processing strength and metadata views.
The independent matrix checks 82 schemas through 164 actual binding parses and
112 SOAP documents across simple/complex content, qualified/unqualified attributes,
both versions/directions, providers, examples and reconstructed services. Two
libxml2 subset verdict gaps are explicit: it admits `##local` into `##other` and
rejects the empty set as a subset of `##other`; Xerces and Qore enforce XSD 1.0.
Attribute wildcard instance validation and preservation are implemented in P5-10 below. Element wildcard processing remains tracked under P5.

`test/wsdl-element-consistency.qtest` and `test_element_consistency.py` check
conflicting element types before flat field maps merge, including nested named
groups, inheritance, resolved references and absent particles. The independent
matrix covers 30 schemas through both actual SOAP bindings and 20 documents in
both directions, with provider/example and reconstructed-service consumers.
The tests record libxml2's 13 accepted conflicting models and two rejected valid
`+00` occurrence spellings, plus Xerces's two unchecked unused conflicting groups.
Qore enforces the XSD 1.0 construction constraints without those oracle gaps.
These checks do not replace P4 ordered particle matching or P5 substitution groups.

`test/wsdl-reference-permissions.qtest` and `test_reference_permissions.py` check
source-local import permissions, including preloaded components, transitive imports,
included documents and absent namespaces. The Python matrix checks 29 schema graphs
and 24 SOAP documents, with actual bindings in both versions/directions and native,
provider, generated-example and reconstructed consumers. The matrix records seven
libxml2 and two Xerces differing schema verdicts for missing type-reference imports
and empty/absent namespace distinctions. Requirements come from XSD 1.0
[src-resolve](https://www.w3.org/TR/xmlschema-1/#src-resolve),
[src-import](https://www.w3.org/TR/xmlschema-1/#src-import) and the schema target
namespace property mapping; Qore enforces these even when a validator misses them.
The Qore-authored `test.wsdl`, `soap-comprehensive.wsdl` and inline SOAP-feature
contract declare their SOAP encoding imports explicitly. Pinned upstream corpus
bytes are unchanged.

`test/wsdl-unwrapped-values.qtest` and `test_unwrapped_values.py` cover bare
document records with explicit wildcards and nested choices, WSDL message-name
containers, explicit multipart wrappers and header separation. The independent
test validates 60 emitted payload/header documents across both SOAP bindings,
directions and reconstructed services, checking exact names, values and order.
Attribute wildcards and absent particles cannot claim child values. Full group
matching and wildcard runtime validation retain their P4/P5 ownership.

## Retained XML values and consumers

`WSDL::XsdXmlValue` explicitly retains lexical text, namespace bindings, ordered
children/mixed text, comments, CDATA and inherited XML language/space/base context.
Its authoritative XML and context reconstruct through Serializable; the native
scalar/hash APIs retain their defaults. See [the implemented contract and examples](../../design/wsdl-xml-values.md).

Use `WSOperation.deserializeXmlRequest()` / `deserializeXmlResponse()` for
`SoapXmlMessageInfo` containing body part maps, bound header maps and ordered
unbound headers/extensions. `SoapClient.callOperation(..., {"xml_values": True})`
selects that response form. The final `xml_values` option to
`SoapHandler.addMethod()` selects it for callbacks; callbacks return retained
values in ordinary part-name and `^header^` maps. One-way client calls return
`NOTHING`. These explicit XML consumers currently apply to element-based literal
SOAP parts; native APIs continue handling their existing binding representations.

`XsdSchema.getXmlValue()` and `getXmlDataProviderType()` validate global XML
elements through the existing decode/encode rules. `WSMessageHelper.getXmlMessage()`
returns XML examples using the existing native generator. Validation and examples
retain the scalar/particle/wildcard limitations assigned to later plan phases.

Run `wsdl-xml-value.qtest`, `wsdl-xml-context.qtest`, `wsdl-xml-consumers.qtest`
and the corresponding `test_xml_values.py`, `test_xml_context.py`, and
`test_xml_consumers.py` with the local module environment. The consumer suite
covers actual HTTP, both SOAP bindings/directions, providers and reconstruction.
The independent consumer test completes 192 documents and remains failing for
16 required-wildcard examples generated empty by the native helper (P5). Other
retained input/output documents preserve their exact values, names and context;
no rejected example is counted as passing.

## Local verification and documentation

Tests load this repository's modules and the tested core DataProvider prerequisite:

```sh
export PATH=/home/david/src/qore/git/qore/build-debug:$PATH
export LD_LIBRARY_PATH=/home/david/src/qore/git/qore/build-debug
export QORE_MODULE_DIR="$PWD/build-debug:$PWD/qlib:/home/david/src/qore/git/qore/build/qlib-qmod/DataProvider:/home/david/src/qore/git/qore/qlib"
/home/david/src/qore/git/qore/build-debug/qore --enable-debug test/wsdl-interop.qtest
python3 test/wsdl-interop/test_survey.py -v
```

For native memory checks use `QORE_PCRE2_NO_JIT=1 valgrind ... qore -b --enable-debug`.
The switch disables regex JIT programmatically for testing; normal execution keeps
JIT enabled. Native XML fragment and SOAP consumer memory checks are recorded in
EXECUTION.md with zero errors/lost memory after the committed dependency/runtime fixes.
Independent host glibc thread-creation-failure and Valgrind DWARF diagnostics remain
assigned to P9 and are not suppressed.

Configure `build-debug` with `-DCMAKE_BUILD_TYPE=Debug` and the installed prefix
(`which qore` is `/usr/bin/qore` here, so `-DCMAKE_INSTALL_PREFIX=/usr`). Documentation
uses `cmake --build build-debug --target docs-module-final docs-SoapClient docs-SoapHandler`.
CMake's `TAGFILES` parameter supplies generated core/dependency tags with their doc
URLs. The native pass uses generated public QPP declarations, preserves dependency
tags, reads assets from `docs/`, and builds a final pass after WSDL/WebContentUtil tags.
The XML generation option page is included in that public documentation input.
For this checkout, documentation also prepends the existing local JNI and astparser
builds to `QORE_MODULE_DIR`:

```sh
export QORE_MODULE_DIR="/home/david/src/qore/git/module-jni/build-debug:/home/david/src/qore/git/qore/build-debug/modules/astparser:$QORE_MODULE_DIR"
```

The installed JNI module has the stack-frame assertion described in EXECUTION.md;
the local JNI build contains the tested source fix. Existing astparser artifacts
are sufficient for Qdx. Use `-DQore_DIR=/home/david/src/qore/git/qore/build-debug/cmake`
to consume the local exported CMake helpers without installation.

Integer lexical validation is documented in [the scalar design](../../design/wsdl-scalar-values.md).
Run `qore --enable-debug test/wsdl-integer-lexical.qtest` and
`python3 test/wsdl-interop/test_integer_lexical.py -v` with the local core/module
paths described above. The native core prerequisite is ea9ddfc51, which preserves
embedded NUL bytes during regex substitutions. P3-01 covers lexical rejection;
precision, ranges, facets, providers and scalar example generation are developed
as separate increments of the active P3 work.

The exact integer range increment adds `wsdl-integer-range.qtest` and
`test_integer_range.py`: all thirteen builtins, boundaries and adjacent invalid
values, large exact strings, native integral float/number values, attributes,
simple content, providers, reconstruction and generated examples. The independent
matrix checks 1,200 documents across actual SOAP 1.1/1.2 bindings and both
directions. Xerces and Python exact integers verify values where libxml2 has its
recorded arbitrary-integer precision limitation. The core prerequisites for exact
raw number text and numeric temporary ownership are described in EXECUTION.md.

## Exact numeric restriction regression

`qore --enable-debug test/wsdl-numeric-facets.qtest` covers exact decimal/integer
bounds and digit facets, numeric enumeration, retained integer patterns, generated
examples and provider/field reconstruction. `python3
test/wsdl-interop/test_numeric_facets.py -v` independently checks 1,440 documents
across actual SOAP 1.1/1.2 bindings and both directions: attributes/simple content,
lists/unions, native values, reconstructed consumers and generated examples. Both
libxml2 and Xerces validate every document; exact Decimal values and expanded names
are asserted separately. Negative provider cases must raise `RUNTIME-TYPE-ERROR`.

All nine integer pattern families now have exact value assertions in the strict
gate, now expanded with string families: 88 descriptions / 752 message directions,
zero selected failures. The broad
report retains 220 failure rows assigned to the remaining work, versus 252 before
this increment. The 32 resolved rows are eight integer pattern families' formerly
rejected second examples in both versions/directions. Full Python discovery still
exposes the seven tracked P4/P5/P6 failures; these are not passing conformance tests.

Numeric values are compared without rounding to fit a schema. Under XSD 1.0 Second
Edition's `totalDigits` rule, `0.0012` requires four digits because the rule also
constrains fractional scale. The implemented representation and provider equality
rules are described in [the scalar design](../../design/wsdl-scalar-values.md).

`qore --enable-debug test/wsdl-facet-declarations.qtest` checks numeric facet
declarations: required values, XML grammar/namespaces, exact digit counts,
applicability, inherited and fixed bounds, reconstruction and failed-addition
rollback. `python3 test/wsdl-interop/test_facet_declarations.py -v` covers 86
authored cases as 172 atomic/simple-content schemas, 344 actual SOAP contracts,
and 608 input/output documents with exact values and expanded names. See the
[specification adjudication](facet-declarations-adjudication.md) for named
libxml2/Xerces compiler disagreements. Counts above signed 64-bit range remain
exact strings; no display rounding or machine-width clamp is applied. P3 remains
active for the other scalar datatype and facet requirements.

`qore --enable-debug test/wsdl-string-list-facets.qtest` verifies string whitespace
and enumeration, exact character/octet/item counts, valid restriction derivation,
provider reconstruction, metadata rejection, bounded examples and rollback.
`python3 test/wsdl-interop/test_sized_facets.py -v` tests actual SOAP 1.1/1.2 inputs
and outputs, original/reconstructed providers and contracts, attributes, repeated
list-valued elements and generated examples. It checks preserved values and
expanded names in addition to schema validity. The independent Xerces worker
selects code-point counting before datatype initialization; supplementary and
combining characters test that configuration. Named compiler disagreements are
recorded in [the string/length adjudication](sized-facets-adjudication.md), with
normative references. No Qore verdict is waived. Repeated string choice fields
require the core DataProvider setter correction in `cbb8aceb2`.

The current string/length matrix covers 164 schemas and 326 actual contracts,
with 1,400 independently checked input/output documents across parsing, value
conversion, providers, reconstruction and examples. The selected corpus gate
covers 88 descriptions / 752 directions; the broad diagnostic ledger remains
separate from passing conformance assertions.

### Ordered list values and whole-list patterns

`wsdl-list-values.qtest` and `test_list_values.py` cover ordered string, boolean,
integer and decimal list choices; equivalent spellings; exact large values; empty
lists; XML-only item boundaries; item restrictions; inherited and alternative
patterns; detached/reconstructed providers; atomic and repeated field choices;
message providers; failed metadata updates; cancellation and generated examples.
The authored contracts use actual SOAP 1.1/1.2 bindings in both directions.

The independent oracle now distinguishes validity errors from warnings. Results
include an ordered `warnings` list even when validation fails; diagnostics do not
leak to subsequent schemas/documents. Error and fatal-error callbacks still reject
invalid input. [List adjudication](list-values-adjudication.md) records the named
Xerces list-length warnings and libxml2's empty-list enumeration compiler defect.
Both schema verdicts and exact ordered values remain independently checked.

Strict value assertions now support `datatype: "list"` with an explicit scalar
`item_datatype`. They detect item loss, changed order, precision loss and changed
boolean values, and split only XML whitespace. The W3C `List` family expands the
mandatory selection to 89 descriptions / 756 message directions. The broad report
also retains Xerces schema diagnostics, including warnings.

Boolean restriction checks are in `test_boolean_facets.py` and
`../wsdl-boolean-facets.qtest`. They cover valid retained pattern spellings,
forbidden facet declarations, inherited patterns/defaults, fixed-value equality,
list items, detached providers and generated examples in both SOAP versions and
directions. See [boolean-facets-evidence.md](boolean-facets-evidence.md) for the
normative basis and independent schema/value accounting.

Union provider regression checks are in `../wsdl-union-providers.qtest` and
`test_union_providers.py`. They cover ordered member conversion, requiredness,
reconstructed metadata, repeated-list validation, shared nested providers, cycles,
cancellation and reentrant numeric inputs. The independent matrix checks both
actual SOAP bindings and directions, detached consumers and generated examples.
[Union provider evidence](union-providers-evidence.md) records exact value
assertions, the existing libxml2 decimal precision limitation and remaining P3
schema-union criteria.

Union/XML whitespace checks are in `test_union_whitespace.py`,
`../wsdl-union-whitespace.qtest` and `../xml-whitespace.qtest`. They retain exact
string whitespace across actual SOAP 1.1/1.2 bindings, attributes, repeated values,
providers and reconstruction; reject inapplicable union facets; and distinguish
string-member preservation from token-member collapse. Native tests cover XML
CR/CDATA generation, formatting, scalar/mixed parsing, inherited `xml:space`,
encoding, repeated-child grouping and interruption. The precise Xerces own-union
pattern discrepancy is documented in [union-whitespace-evidence.md](union-whitespace-evidence.md).

Shared schema union checks are in `../wsdl-union-schema-graphs.qtest` and
`test_union_schema_graphs.py`. They cover bounded serialization/deserialization
and native-list metadata traversal, positive and negative atomic/list graphs,
cycle rejection, error cleanup, reentrant namespace/type/reference contexts,
actual SOAP 1.1/1.2 bindings and reconstructed consumers. The schema caches are
scoped to one conversion; later calls observe current member configuration.

Union primitive value checks are in `../wsdl-union-value-identity.qtest` and
`test_union_value_identity.py`. They cover boolean/integer and string/boolean
ambiguity, exact decimal enumerations, lexical patterns, distinct binary families,
detached metadata validation, list items and finite field choices. The independent
matrix checks primitive family and value across real SOAP 1.1/1.2 bindings in both
directions, attributed/repeated values, reconstructed consumers and examples.
These checks cover the implemented scalar families; the remaining P3 union and
datatype requirements stay tracked in [EXECUTION.md](EXECUTION.md).

Atomic list members of unions are checked by `../wsdl-union-list-identity.qtest`
and `test_union_list_identity.py`. Ordered primitive item values determine equality,
including integer/decimal equivalence, boolean and binary family distinctions,
empty lists and single-item lists distinct from atomic values. Tests cover retained
spellings, native item boundaries, union facets, provider choices, metadata changes,
errors, both SOAP bindings/directions, reconstructed consumers and examples.
The independent matrix reports the already adjudicated libxml2 empty-list enumeration
compiler defect as unassessed schemas/documents; Xerces assesses all documents and
exact Qore value checks remain mandatory. The matrix also counts libxml2's
base64 punctuation false positives; Qore, Xerces and a strict base64 decoder reject
those inputs. Both oracle defects are explained in the list adjudication document.

Union-valued list items are checked by `../wsdl-union-list-items.qtest` and
`test_union_list_items.py`. For a boolean/int item union, `01 2` contains decimal
values and can equal the decimal-list spelling `1.0 2.00`; `1 2` contains a boolean
and remains distinct. Captured item conversions retain order and family through
enumeration, patterns, finite choices, restriction wrappers and reconstruction.
Tests include empty/native item boundaries, text/binary values, reentrant calls,
shared graphs, cycle rejection and cleanup after a second-item failure. The
independent matrix uses both actual SOAP bindings and directions and records
Xerces's precise list-kind enumeration false negatives alongside mandatory
libxml2 and exact ordered-value checks. See [list adjudication](list-values-adjudication.md).

List-owned facets for union-valued items are checked by
`../wsdl-list-union-facets.qtest` and `test_list_union_facets.py`. The matrices
cover ordered primitive enumeration, lexical patterns, inheritance, item
restrictions, count boundaries, empty lists, actual SOAP 1.1/1.2 contracts,
reconstructed consumers and examples. Qore regressions additionally cover exact
error categories, metadata validation, field choice updates and scoped capture
cleanup. The known libxml2 empty-list enumeration compiler defect remains
adjudicated separately; Xerces and exact empty-value checks remain mandatory.

Builtin name/list rules are checked by `../wsdl-builtin-list-values.qtest` and
`test_builtin_list_values.py`: Unicode name grammar, token boundaries, builtin
list enumeration and union identity, inherited patterns/counts, detached choices,
metadata and examples in both actual SOAP bindings/directions. An additional
6,054-case boundary matrix checks all normative name-character range boundaries
through schema serialization/deserialization, providers, libxml2 and Xerces.
The pinned numeric ranges cite the XML 1.0 Second Edition required by XSD 1.0.
[Name/list evidence](builtin-list-values-evidence.md) records libxml2's missing
builtin-list minimum-length check; the precise empty-input false positives are
counted separately, and Qore and Xerces must reject them. Document-level identity
and unparsed-entity validation remain assigned to P5/P7.

A failed survey worker now includes bounded stderr in its exception message,
while retaining its full captured output and CalledProcessError compatibility.
`test_survey.py` verifies real child failure, cleanup, bounded rendering and
unchanged timeout/cancellation behavior. Worker errors remain hard failures.

Pattern execution checks in `../wsdl-regex-execution.qtest` and
`test_regex_execution.py` cover ambiguous alternatives, nullable closures,
count-state gaps, large inputs, cancellation/reuse and shared immutable programs.
New constraints retain XSD source and avoid full-expression PCRE limits. Both
actual SOAP bindings/directions and reconstructed providers preserve exact
strings and reject invalid inputs with the expected category. The named libxml2
execution limit remains recorded as unassessed; original Xerces checks and
separate language-equivalent schemas assess every affected document.
See [execution evidence](regex-execution-evidence.md).


## Calendar values and providers

Run `wsdl-calendar-values.qtest`, `wsdl-calendar-facets.qtest` and
`wsdl-calendar-consumers.qtest` with debugging enabled, plus
`python3 test/wsdl-interop/test_calendar_values.py -v`. The six calendar
primitives retain timezone absence, arbitrary years and required lexical patterns.
Explicitly zoned complete dates in the native year range return native dates;
other dates and partial calendars remain validated strings. Existing callers
that assume every `xs:date` is native must handle that string alternative.
See [the public contract](../../design/wsdl-calendar-values.md).

The independent matrix checks actual SOAP 1.1/1.2 bindings, both directions,
atomic/simple-content/attribute/repeated values, reconstructed providers, examples,
lists and union primitive identity. A separate integer ordinal reference checks
1,838 seeded offset, year and leap-day cases. Local HTTP tests exercise both
SoapClient and SoapHandler with native, unzoned, extended and partial dates.
The strict W3C selection includes all 18 calendar element/attribute/pattern
families, with exact value assertions and original invalid inputs retained.

[Calendar validator evidence](calendar-values-evidence.md) records 133 exact
reproductions of libxml2 ordering/whitespace errors and Xerces's obsolete gMonth
spelling acceptance. Qore's normative acceptance and value checks remain
mandatory; the oracle comparison requires the exact recorded triples and counts.
To reproduce the native libxml2 verdicts independently of WSDL conversion, run:

```sh
qore -b --enable-debug test/wsdl-interop/calendar-validator.qr \
  test/wsdl-interop/calendar-validator-defects.json
```

The diagnostic prints each native verdict and its expected rejection diagnostic;
its exit status reports successful execution, not standards conformance.
DateTime, time and the remaining P3 requirements stay open.

## Duration values and facets

Run `wsdl-duration-values.qtest` and `wsdl-duration-consumers.qtest` with debugging
enabled, plus `python3 test/wsdl-interop/test_duration_values.py -v`.
Duration conversion validates XSD 1.0 grammar, retains arbitrary component and
fractional precision as strings, and preserves native relative-date signs and
microseconds. Absolute dates and opposing month/second component signs reject.
Optional and reconstructed providers retain validation; local HTTP tests exercise
actual SOAP 1.1/1.2 bindings, attributes, basic lists/unions and request recovery.
See [the public contract](../../design/wsdl-duration-values.md) and
[validator evidence](duration-values-evidence.md). Exact duration facets and collection identity are described below.


`test/wsdl-duration-facets.qtest` covers all four bounds, inherited/fixed
constraints, patterns, exact finite choices, fixed attributes, lists/unions,
provider reconstruction and cancellation, and narrow-interval examples.
`test_duration_facets.py` checks 1,376 arithmetic boundary rows against independent
integer/Fraction reference-date calculations, plus actual SOAP bindings in both
versions/directions with detached element/message providers and generated examples.
The HTTP consumer suite also carries restricted durations, fixed attributes and
list/union enumerations through SoapClient and SoapHandler.

See [duration facet evidence](duration-facets-evidence.md) for the exact validator
disagreements. The strict corpus selection includes `DurationElement` and
`DurationAttribute` with independent duration-value assertions. The selection is
116 WSDLs and 1,120 message directions; all broader P4/P5/P6 findings remain visible.

## Binary lexical values

Run `wsdl-binary-values.qtest` and `wsdl-binary-consumers.qtest` with debugging
enabled, plus `python3 test/wsdl-interop/test_binary_values.py -v`. Strict binary
conversion rejects malformed padding, nonzero unused bits and non-XML whitespace,
accepts XML whitespace between base64 characters, and preserves raw string bytes
when serializing. `XsdBinaryDataType` validates encoded XML strings and returns
octets, including through optional copies and reconstructed providers.
See [the public input contract](../../design/wsdl-binary-values.md) and
[binary validator evidence](binary-values-evidence.md). Actual SOAP 1.1/1.2 HTTP
exchanges and independent binding matrices check exact bytes in both directions,
attributes, simple content, repeated values, providers and examples.

Binary restriction checks in `wsdl-binary-facets.qtest` and `test_binary_facets.py`
cover octet counts/equality, fixed and finite choices, inherited patterns,
reconstructed providers, list/union identities and generated examples. Patterned
values can return `XsdBinaryValue` objects carrying exact bytes and lexical text;
see the public contract above before assuming a restricted value is native binary.
HTTP tests carry these values through actual SOAP 1.1/1.2 bindings in both directions.
Union patterns use the selected leaf member's whitespace normalization, including
nested unions and binary values within union-item lists. Strict coverage now adds
all four binary element/attribute families: 120 WSDLs and 1,148 message directions.

## QName lexical values

Run `wsdl-qname-lexical.qtest` and `wsdl-qname-consumers.qtest` with debugging
enabled, plus `python3 test/wsdl-interop/test_qname_lexical.py -v`.
QName conversion validates both NCName components, collapses XML whitespace,
and rejects empty or malformed text. Providers retain lexical and inherited
pattern checks after reconstruction. Examples satisfy lexical restrictions or
raise `XSD-SAMPLE-ERROR`; deprecated QName length facets do not alter them.

The independent tests cover 4,036 character-boundary inputs, seven schema
declarations, and 42 SOAP 1.1/1.2 contracts with 612 messages in both directions.
They compare namespace/local identity for their local and implicitly bound `xml`
names and independently validate output. Local HTTP tests exercise SoapClient
and SoapHandler, attributes, lists, union fallback and rejection recovery.
See [the lexical contract](../../design/wsdl-qname-lexical.md) and
[evidence](qname-lexical-evidence.md). The [QName value contract](../../design/wsdl-qname-values.md) describes instance
namespace scopes, expanded enumeration identity and structural output prefixes.

## Detached schema namespace ownership

Run `qore --enable-debug test/wsdl-namespace-ownership.qtest` to verify that
types, elements and attributes retain their declaration namespaces after the
schema leaves scope. Tests cover incremental additions, nested imports/includes,
raw and binary reconstruction, provider constraints, failed additions,
serialization errors, cancellation, concurrent copies and cycle cleanup.
See [the ownership contract](../../design/wsdl-schema-identity.md#declaration-namespace-ownership)
and [regression evidence](namespace-ownership-evidence.md). Existing independent
binding matrices continue to check schema validity and preserved values in both
SOAP versions and directions.

## Caller-owned scalar values

Run `qore --enable-debug test/wsdl-caller-owned-values.qtest` to verify that
record conversion preserves retained scalar objects supplied by the caller.
The suite covers sequence/all/choice, nested records, shared and repeated
values, reconstruction, failure recovery, interruption and concurrent calls.
`wsdl-binary-consumers.qtest` reuses the same retained values through real HTTP
requests and responses in both SOAP versions. See [the lifetime contract](../../design/wsdl-binary-values.md#caller-ownership-during-record-conversion)
and [regression evidence](caller-owned-values-evidence.md).


## Native QName union validation

Run `qore --enable-debug test/xml-qname-unions.qtest` and
`python3 test/wsdl-interop/test_qname_union_validator.py -v` from the repository
root with the local native module selected. A failed QName trial no longer
rejects a union whose later member accepts. The tests preserve text/attributes,
verify ordered enumeration identity, cover nested unions and lists, and check
invalid input and cancellation recovery. CMake probes both DOM and streaming
validation and rejects partial backports that still have this defect.
See [the native design](../../design/xml-qname-validation.md) and
[independent evidence](qname-union-validator-evidence.md). The WSDL context matrix below checks the corresponding instance and provider
integration.


## Native reader cursor values

`qore --enable-debug test/xml-reader-values.qtest` checks scalar and empty
cursor conversion, sibling boundaries, mixed content/grouping, document
hashes, errors, partial stream failure and cancellation. The QName union
validator matrix also checks both cursor methods for all 300 documents,
including exact scalar/empty results. See [the reader contract and example](../../design/xml-reader-values.md).


## QName instance scopes and consumers

Run `qore --enable-debug` with `wsdl-qname-provider-context.qtest`,
`wsdl-qname-provider-facets.qtest`, `wsdl-qname-schema-output.qtest`,
`wsdl-scoped-lexical-values.qtest` and `wsdl-qname-consumers.qtest` under `test/`.
Run `python3 test/wsdl-interop/test_qname_context.py -v` for independent XML
and typed-value checks through both bindings and directions, detached element/
message providers, reconstruction, and native/retained-XML examples.

The matrix includes ancestor bindings, local shadowing, default resets, QName
aliases, ordered QName/string fallback, enumerations and lists. One pinned Xerces
schema warning is asserted as a validator defect: its preliminary enumeration/
length comparison counts characters instead of list items. Every document verdict
and all six native validation paths remain required. P5 data-prefix remapping for
native values assembled with conflicting spellings remains tracked in the plan;
current conversion reports conflicting data bindings explicitly. Each scoped worker
handles one schema shape, including both bindings, with a bounded deadline. The
complete inventory is 296 inputs, 4,072 consumer outcomes and 3,776 independently
validated documents. The strict corpus now includes QNameElement and QNameAttribute
with expanded-name checks: 122 descriptions / 1,156 directions. See
[context evidence](qname-context-evidence.md) and [the full audit](audits/P3-39-qname-context.md).

## ENTITY values at WSDL document boundaries

Run `qore --enable-debug` with `test/wsdl-entity-values.qtest` and
`test/wsdl-entity-consumers.qtest`, plus
`python3 test/wsdl-interop/test_entity_wsdl.py -v` using the local modules.
The tests cover selected ENTITY constraints in elements, attributes, simple
content, lists/unions, defaults, retained XML and typed RPC parts. They include
both actual SOAP bindings/directions, reconstructed consumers, local HTTP,
reentrant callbacks, interruption and concurrent recovery.

The independent matrix checks 2,880 outbound and 9,216 inbound/consumer outcomes.
It validates every emitted payload and original valid/invalid input with pinned
Xerces, including exact preserved content and attribute values. Set
`WSDL_ENTITY_ARTIFACT_DIR` to preserve generated WSDLs, manifests and worker rows.
The four original ENTITY/ENTITIES families are mandatory expected rejections in
the strict gate: 126 descriptions and 1,172 selected message directions.
Datatype-only providers and schema facet comparison retain their lexical value
contract; document conversion enforces the selected member's declaration requirement.
See [the public contract](../../design/wsdl-entity-values.md) and
[execution evidence](entity-wsdl-evidence.md).

## Complete message providers

`qore -b --enable-debug test/wsdl-message-providers.qtest` checks message-part
instance requirements before a native provider value can be accepted. It includes
original/reconstructed providers, both bindings/directions, field projections,
container wrapping, QName ownership, component metadata, callback failures,
program interruption and synchronized concurrent calls. The existing
`test_entity_wsdl.py` matrix independently checks every reachable document.
See [the provider contract](../../design/wsdl-message-providers.md).

## Generated native instances

`qore -b --enable-debug test/wsdl-sample-instances.qtest` checks that default
helper calls return a valid candidate or raise XSD-SAMPLE-ERROR before returning.
Coverage includes element/type/multipart entry points, defaults, occurrence
limits, explanatory options, QName identity, callback/recovery and concurrency.
The independent ENTITY and QName context matrices exercise the same consumers.
See [the generation contract](../../design/wsdl-sample-instances.md).

## Exact dateTime and time values

`qore -b --enable-debug test/wsdl-time-output.qtest` checks exact native clock
projection, timezone bounds, daylight-saving offsets, reconstruction and both
SOAP bindings over local HTTP. `python3 test/wsdl-interop/test_time_output.py -v`
adds independently checked native element, simple-content/attribute and repeated
values, detached providers and generated examples in both directions.
`qore -b --enable-debug test/wsdl-temporal-values.qtest` and
`python3 test/wsdl-interop/test_temporal_values.py -v` cover strict grammar,
timezone absence, exact fractions, midnight, leap seconds, facets and reconstructed
providers. Independent rational values detect changes hidden by binary64 schema
validators; exact validator discrepancies remain in `temporal-validator-defects.json`.
The strict corpus selection includes dateTime/time element and attribute values.
See the [conversion contract](../../design/wsdl-time-output.md).

XML-RPC character data has dedicated native and independent HTTP checks:
`qore -b --enable-debug test/xmlrpc-text.qtest` and
`python3 test/wsdl-interop/test_xmlrpc_text.py -v`. They check exact strings,
struct names, UTF-16 bytes, faults, integer boundaries and the separate CPython
literal-CR marshaller defect. See [the value contract](../../design/xmlrpc-character-data.md).


## Native exact occurrence ranges

`xml-particle-ranges.qtest` covers finite ranges above the native sentinel and
integer limits, whole sequences/choices, nullable and inherited particles,
substitution members, wildcards and invalid lexical/range declarations. The
[implemented design](../../design/xml-particle-ranges.md) includes an executable
batch example and explains exact counter storage, rollback and ownership.
`test/cmake/test_libxml2_provider.py` compares 881 boundary cases against Python
integers and exercises native execution and allocation failure. Its behavior
probe rejects incomplete range backports before selecting a system library.

The historical [failing range diagnostic](P4-native-count-range-diagnostics.json)
remains unchanged. [P4-06's current report](P4-06-native-count-ranges.json) records
all 16 DOM/reader requirements passing, including the ambiguous schema rejected
for attribution. Full phase status and broader remaining requirements are in
[EXECUTION.md](EXECUTION.md).

## Ordered value declaration attribution

`wsdl-particle-attribution.qtest` checks declaration selection at fixed boundaries,
repeated/alternating groups, wildcard/all terms, shared and reconstructed graphs,
large inputs, cancellation and concurrent reuse. `test_particle_value_attribution.py`
checks 1,000 complete finite models with 42,630 construction/attribution rows,
including original/reconstructed graphs and invalid mutations. Every accepted
child must select the position given by the independently enumerated marked
language. See the [implemented matcher design](../../design/wsdl-particles.md#declaration-attribution-for-ordered-values).

Ordered value integration is covered by `test/wsdl-particle-values.qtest` and
`python3 test/wsdl-interop/test_particle_values.py -v`. The Python matrix checks
whole optional/repeated sequences, alternating and nested choices, all-groups,
missing members, wrong order and extra occurrences through actual SOAP 1.1/1.2
bindings in both directions. It accounts for every original/reconstructed row,
compares typed native values and retained lexical child order, and validates input
and emitted payloads with pinned libxml2 and Xerces. `wsdl-xml-consumers.qtest`
exercises these groups over local HTTP with native and retained XML consumers.
The historical SoapUI request in `soap.qtest` is preserved as an invalid-order
negative; its explicit derivative reverses the three inherited `issue560` children
into base-first order and supplies the missing required nillable `i3367` child.

## Named-element occurrence metadata

`wsdl-particle-occurrences.qtest` checks exact per-name counts and provider field
requiredness/list shape for nested sequences, alternatives, shared groups and
all-groups. It covers original/reconstructed types and providers, both actual SOAP
bindings and message directions, namespace collisions, repeated enum choices,
unbounded and very large counts, empty/impossible content, invalid graphs,
interruption and concurrent reuse. `test_particle_occurrences.py` checks 1,000
generated models against complete finite languages: 765 valid models produce
original/reconstructed projections, and 235 invalid models must be rejected.
Every run accounts for all 2,530 rows. Set `QORE_EXEC_MODE` to `ast`, `ir`, `jit`
or `tiered`; the default is `jit`.

See the [range and provider contract](../../design/wsdl-particles.md#exact-named-element-occurrence-ranges).
These field bounds describe independent extrema; complete particle validation
still enforces correlations, order, exclusivity and count gaps. The Qore runtime
prerequisite `f1dd175f0` fixes absent optional soft-list values and collection
defaults. Normal named-element samples now use complete particle schedules, and group
finalization no longer changes shared element counts.

## Native particle ordering and emission

`qore -b --enable-debug test/wsdl-particle-serialization.qtest` checks complete
native groups, choice/suffix allocation, count gaps, interleaved repeated values,
list-valued children, empty/nil wrappers, actual declaration selection, huge
counts, all-groups, a 600-child output, interruption and synchronized reuse.
`python3 test/wsdl-interop/test_particle_ordering.py -v` checks 1,000 generated
finite models and every per-name count pair through one beyond the exact maxima,
plus unknown names. Its 15,132 rows include reconstruction, required schema
rejections, accepted native output order and exact per-field value preservation.
The oracle enumerates complete marked languages independently of production.

`test_particle_values.py` additionally emits the decoded native records through
both actual SOAP bindings, in both directions and after reconstruction. Pinned
libxml2 and Xerces validate all 224 retained/native outputs; native checks compare
each field's exact ordered integer values. Set `QORE_EXEC_MODE` for all four modes.
See [the implemented allocation contract and bounds](../../design/wsdl-particles.md#native-named-element-emission).

## Bounded particle samples

Run `qore -b --enable-debug test/wsdl-particle-samples.qtest` for complete group
selection, required suffix reservations, all groups, wildcards, huge empty counts,
shared groups, bounded deep models, cancellation and concurrent reuse.
`python3 test/wsdl-interop/test_particle_samples.py -v` checks 1,000 complete finite
models against an independent exhaustive oracle, with two repetition limits and
six child budgets. All 19,360 rows are required, including schema rejections and
original/reconstructed generation errors. Set `QORE_EXEC_MODE` for AST, IR, JIT
or tiered execution. See the [implemented structural API and resource bounds](../../design/wsdl-particles.md#bounded-structural-examples).

`WSMessageHelper` uses these schedules for normal named-element examples, including
whole-group comments, list-valued child occurrences and typed complex parts. Its
`max_elements` option bounds generated elements per part; root/reentrant scopes
retain independent validation and budgets. Group finalization preserves shared
declaration limits. See the [helper contract and shipment example](../../design/wsdl-sample-instances.md#complete-groups-and-bounded-construction).

`python3 test/wsdl-interop/test_sample_particles.py -v` checks 208 explicit rows
through both actual SOAP bindings and directions, before and after reconstruction,
with and without comments. All 352 native/retained outputs receive independent
schema validation and exact child-order/integer checks. The 32 expected generation
errors request insufficient budgets; they are distinct from invalid XML or
unsupported model classifications. The 19-case `wsdl-sample-instances.qtest` suite
also checks callbacks, same-helper reentrancy, nested lists, recursive types,
metadata reuse, option errors and complete override/fragment output budgets. Set `QORE_EXEC_MODE` for each execution mode.

## P4 corpus value and order acceptance

`probe.qr` parses SOAP input with `XPF_PRESERVE_ORDER`, as required by the
`WSOperation` hash decoding API. This retains interleaved repeated-group members
before complete-particle validation. The worker regression covers both actual
SOAP bindings and directions, complete pairs, wrong order, mixed ordering and
missing members. Original invalid input is still rejected; the worker does not
reorder it before validation.

The strict selection includes all 13 P4-owned families from the plan, with 60
original messages and 120 request/response directions. Four directions must
reject invalid `MinOccurs1` inputs. The other 116 require complete expanded
names, exact `xs:string` values, occurrence counts and order within each native
field. `particle_reference.py` compares whole selected trees, preserves string
whitespace, and ignores indentation only in element-only containers. Its
`per-name` ordering contract corresponds to flat native records; its `exact`
contract compares the complete original child sequence. Schema validation is
required independently of these value assertions. Mixed content and dynamic
value semantics remain separate P5 requirements.

Run `python3 test/wsdl-interop/test_particle_reference.py -v` for mutation checks
covering changed values, whitespace, namespaces, missing/extra nodes, field
occurrence order, attributes, malformed assertions and 2000 nested containers.
`python3 test/wsdl-interop/test_particle_corpus.py -v` checks all 240 explicit
original/reconstructed and request/response rows. Its eight source rejections
must fail in both native and retained APIs. Every one of the 696 successful
native, retained-wire and retained-payload outputs receives independent libxml2
and Xerces validation, plus the relevant complete value/order comparison.
Set `QORE_EXEC_MODE` to `ast`, `ir`, `jit` or `tiered` for each runtime mode.

The corpus test verifies original WSDL, inline-schema and message hashes against
`adjudication-report.json`. SOAP 1.1 uses the original description; the SOAP 1.2
derivative changes only the WSDL extension namespace from
`http://schemas.xmlsoap.org/wsdl/soap/` to
`http://schemas.xmlsoap.org/wsdl/soap12/`, and checks the resulting binding
identity before invoking Qore. Original files remain untouched. `WSDL_CORPUS`
can select a verified corpus root; the default is
`/tmp/module-xml-wsdl-survey/databinding/examples/6/09`.

The normative structural rules are XSD 1.0
[Model Group Validation Rules](https://www.w3.org/TR/xmlschema-1/#cvc-model-group)
and [Particle Validation Rules](https://www.w3.org/TR/xmlschema-1/#cvc-particle).
Retained XML is required when an application needs the original interleaving of
distinct field names. The existing P6 test for selecting between two SOAP
bindings in one description remains a visible failure until that phase.

### Native type identity and annotation checks

`qore -b --enable-debug test/wsdl-type-identity.qtest` checks explicit native
`^type^` / `^val^` wrappers for builtin, named, anonymous, list, union and complex
types. It covers identity across canonical builtin registries, unrelated
same-local-name components, both annotation settings, nil and empty values,
complete occurrence limits, derived attributes, malformed/unbound instance type
QNames, cancellation propagation, conversion counts and synchronized callers.
Type annotations are independently schema-validated with `XmlReader`.

`python3 test/wsdl-interop/test_type_identity.py -v` exercises both actual SOAP
bindings, request and response processing, reconstructed services and reuse after
invalid input. Its 224 explicit rows include 72 required serialization errors
and 416 outputs checked by the pinned libxml2 and Xerces implementations, with
separate exact native-value and expanded-type assertions. Full messages and
detached schema outputs preserve data QName prefixes through final namespace
allocation, including collisions with the selected type and instance-attribute
prefixes on the same simple-content element. Non-QName rows additionally exercise low-level explicit annotations;
the QName rows use the complete XML APIs required by their namespace-allocation
contract. Set `QORE_EXEC_MODE` to `ast`, `ir`, `jit` or `tiered`.

The implemented component identity and annotation ownership rules are documented in
[`design/wsdl-type-selection.md`](../../design/wsdl-type-selection.md). Full P5
selected-type retention, wildcard/mixed/generic content,
substitution groups and nil/default/fixed behavior remain required by the plan.

Type construction final exclusions are checked by `test/wsdl-type-final.qtest`,
`test/xml-type-final.qtest` and `test_type_final.py`. The independent matrix has
87 schemas and 174 actual SOAP binding contracts: 438 worker rows include 86
required construction errors and 352 independently schema-valid request/response
outputs with exact native value comparisons. See the [implemented design](../../design/wsdl-type-final.md)
and [specification/validator adjudication](type-final-evidence.md). This increment
covers type construction; instance controls are checked by the following matrix.

Instance derivation and `block`/abstract controls are covered by
`test/wsdl-type-substitution.qtest` and `test_type_substitution.py`. The independent
matrix has 104 schema/type cases in both actual bindings and directions, including
original/reconstructed services: 832 rows require 336 invalid-instance rejections
and independently validate 992 native-wrapper/retained XML outputs. Both pinned
validators check the original input verdicts. Retained outputs keep their selected
type QName; native values retain the established field shapes. See the
[implemented design](../../design/wsdl-type-substitution.md),
[specification evidence](type-substitution-evidence.md) and
[validation inventory](P5-03-validation.json). P5 remains open for
provider integration with selected native types, element substitution, generic/mixed/wildcard
content, complete nil/default/fixed semantics and document identity constraints.

Explicit native type capture is covered by `test/wsdl-native-type-values.qtest`
and `test_native_type_values.py`. The Qore suite checks 17 cases and 486 assertions,
including root/body/header boundaries, saved values with independent receiving
schemas, invalid selections, cancellation, concurrency and 24 local HTTP calls.
The independent 105-case matrix checks 840 rows, requires 336 rejecting rows and
validates 1008 outputs per execution mode. Actual SOAP 1.1 and SOAP 1.2 bindings
exercise both directions. Set `QORE_EXEC_MODE=ast|ir|jit|tiered` for the matrix.
See the [portable value contract](../../design/wsdl-native-type-values.md) and
[evidence](native-type-values-evidence.md). Default native results and provider
metadata keep their existing shapes. P6 also owns the independently reproduced
[operation handle lifetime defect](p6-operation-lifetime-finding.md).

Native selected-type providers are covered by `wsdl-native-type-providers.qtest`,
`wsdl-native-provider-http.qtest` and `test_native_type_providers.py`. The unit
suite checks 15 cases/521 assertions, HTTP checks 1 case/64 assertions, and each
source/AOT matrix validates 1008 outputs across 840 rows with 336 required
rejections per conversion path. Saved provider graphs, anonymous and abstract
metadata, choices, both bindings/styles, cancellation and concurrency are covered.
See [provider evidence](native-type-providers-evidence.md) and
[P5-05 validation](P5-05-validation.json). Default factories keep their native
field shapes; explicit factories accept captured types. Remaining P5 semantics
and P6 binding/part-aware SoapDataProvider integration stay in the plan.

Element affiliation resolution is covered by `wsdl-element-substitution.qtest`,
`xml-element-substitution.qtest` and `test_element_substitution.py`. The declaration
matrix builds 72 schemas through actual SOAP 1.1/1.2 bindings: 384 rows include
64 required construction rejections and 320 independently valid outputs with
preserved integer values. The membership matrix compares 62 reconstructed/original
maps and 102 documents across 31 groups, retaining four supporting-oracle
disagreements explicitly. The native dependency correction is selected by the
45-schema configure probe and tested with real fixed/broken system backports.
See the [implemented declaration design](../../design/wsdl-element-substitution.md)
and [root causes and specification evidence](element-substitution-evidence.md).

Child substitution processing is covered by `wsdl-substitution-particles.qtest`
and `test_substitution_particles.py`. The integration matrix has 53 schemas and
310 documents across actual SOAP 1.1/1.2 bindings, original/restored graphs and
both directions: 2,586 rows include 992 independently validated SOAP outputs and 58 standalone samples. It
checks concrete member names and values, shared occurrence limits, all slots,
post-membership ambiguity and declaration consistency. Retained values preserve
exact XML; native fields retain member identity and per-field value order.
See the [implemented particle design](../../design/wsdl-substitution-particles.md)
and [regression evidence](substitution-particles-evidence.md).

Complete substitution roots are covered by `wsdl-substitution-roots.qtest`
and `test_substitution_roots.py`. The independent matrix checks 34 schemas,
116 documents in their head's schema context, native/provider identity,
retained XML, both actual SOAP bindings and both directions. It validates
816 outputs and 44 samples with lxml and pinned Xerces. The unit suite also
covers overlapping body/header parts, imported and no-namespace members,
empty/nil values, selected types, schema additions and reconstruction,
cancellation and concurrent reuse. See the
[implemented root design](../../design/wsdl-substitution-roots.md).
`wsdl-substitution-root-http.qtest` adds ten loopback exchanges through
SoapClient, SoapHandler and SoapDataProvider, including native root/type
capture, retained XML and saved providers.
The [native declaration-consistency gap](p5-native-element-consistency-finding.md)
was fixed in P5-08. Selected message roots are implemented in P5-09; remaining
wildcard, mixed/generic content, nil/default/fixed and identity constraints keep P5 open.

Native element declaration consistency is covered by
`../xml-element-consistency.qtest` and `test_native_element_consistency.py`. The latter
checks 43 schemas (25 valid, 18 invalid), independent documents and 50 retained
original/reconstructed values. Both native DOM and reader paths must reject
invalid schemas with `XSD-SYNTAX-ERROR`, while WSDL reports `WSDL-ERROR`.
The 34-schema configure probe and allocation-failure tests live with the
libxml2 provider tests; see `p5-native-element-consistency-finding.md`.


## Wildcard attribute instances (P5-10)

`test/wsdl-wildcard-attributes.qtest` covers effective strict/lax/skip processing,
namespace constraints, inherited groups/derivation, imported and no-namespace
global attributes, typed fixed/list/QName values, wildcard IDs, provider aliases,
soft copies, malformed metadata and lossless unassessed namespace context.
`test/wsdl-wildcard-attribute-http.qtest` exercises both actual SOAP bindings
through clients, handlers and data providers, plus concurrent serialization,
cancellation, failed conversion and shared-schema recovery.
`test/wsdl-wildcard-attribute-registry.qtest` checks completed publication,
serialized provider snapshots, detached lifetime and failed-addition rollback.

`test_wildcard_attributes.py` checks 39 schemas and 324 input documents through
request/response processing and reconstruction. lxml and pinned Xerces assess
input and output; typed values, expanded names and unassessed lexical bindings
are compared separately. Six lxml omissions for wildcard-ID constraints are
explicit; the normative negative remains mandatory for Qore and Xerces.
The separate native DOM/reader defect is recorded in
[p5-native-wildcard-id-finding.md](p5-native-wildcard-id-finding.md) for P5-11.

See [the implemented contract](../../design/wsdl-wildcard-attributes.md) and
[execution evidence](wildcard-attributes-evidence.md). Element wildcard, mixed
and generic content, full nil/default/fixed and document identity requirements
remain open in P5; binding/protocol/attachment and final CI acceptance remain P6-P9.


Native wildcard-ID validation and ID ancestry are covered by
`test_native_wildcard_ids.py` (24 schemas/180 documents and 100 schema cases),
`../xml-wildcard-ids.qtest`, the configure probe and dependency allocation tests.
See [P5-11 evidence](native-wildcard-ids-evidence.md) for normative expectations,
validator differences and local build commands. The additional core cyclic
error-cleanup failure is fixed by the [P5-12 prerequisite](core-graph-cleanup-evidence.md).
The complete wildcard consumer, HTTP and registry suites now pass Valgrind.
The next native finding is [strict wildcard instance types](p5-native-wildcard-type-finding.md).

The 2.x issue #5452 element-order fixes are covered by `test/soap.qtest` and
`test/wsdl-element-order.qtest`, with source normalization and complete flat-record
validation. [Port evidence](element-order-port-evidence.md) records both bindings,
imports, native field/provider/sample order, performance and corpus comparisons.


## Native wildcard instance types and schema declaration whitespace (P5-13)

`xml-wildcard-types.qtest` and `test_native_wildcard_types.py` cover native strict
instance-type assessment, all processing modes, six namespace constraints,
known/unknown types, invalid content and recovery. `wsdl-schema-whitespace.qtest`
and `test_schema_whitespace.py` cover declaration text/CDATA, annotations,
providers, reconstruction, imports and the original enterprise/partner contracts.
The native allocation test distinguishes required validation from optional
post-validation reset, repeating every fault through the public API.
See [evidence](native-wildcard-types-evidence.md),
[design](../../design/native-wildcard-types.md) and
[the full audit](audits/P5-13-native-wildcard-types.md). P5 element wildcard values,
mixed/generic content, complete nil/default/fixed and identity semantics remain
open, followed by P6-P9 acceptance.


## Element wildcard values (P5-14)

`../wsdl-wildcard-elements.qtest`, `../wsdl-wildcard-element-values.qtest` and
`../wsdl-wildcard-element-http.qtest` cover strict/lax/skip assessment, detached
registry lifetime, reconstruction, lexical XML data and explicit retained XML,
provider variants, portable type wrappers, bounded samples and both SOAP
bindings through real HTTP consumers. `test_wildcard_elements.py` checks 36
schemas/684 documents with independent validity and value/name/order assertions.
The [implemented representation](../../design/wsdl-element-wildcards.md) includes
examples and explains when complete XML values are necessary for lossless output.
The deployed Qore shared-container cycle fix closes the provider lifecycle leak.
See [requirement evidence](wildcard-elements-evidence.md), the
[validation inventory](P5-14-validation.json) and [full audit](audits/P5-14-element-wildcards.md).
Generic values and remaining P5-P9 requirements stay open; the known system SSSD
Valgrind warning retains its P9 environment ownership.


## Generic XML values (P5-15)

`../wsdl-generic-values.qtest`, `../wsdl-generic-http.qtest` and
`test_generic_values.py` cover generic scalar/structured XML, known declarations,
selected types, exact numbers, namespace preservation, providers and real SOAP
1.1/1.2 consumers. The independent matrix has four schemas/112 documents and
compares typed values and XML content through native/direct/retained paths.

See [the implemented contract](../../design/wsdl-generic-values.md),
[requirement evidence](generic-values-evidence.md),
[validation inventory](P5-15-validation.json) and
[full audit](audits/P5-15-generic-values.md). All 135 source suites and 27 relevant
supplements pass; both new suites have clean Valgrind error/lost-block summaries.
The separate baseline-reproduced QName AOT stack failure remains a P9 runtime
finding. P5-16 owns nil/default/fixed and the native empty-CDATA correction;
remaining P5-P9 acceptance is still required.


## Native character content (P5-16a)

`../xml-character-content.qtest` and `test_character_content.py` check empty
CDATA, nilled/empty/element-only content, required attributes and default/fixed
assessment through DOM, public reader and XmlDoc. Sixteen schemas/812 documents
agree with pinned Xerces and preserve valid XML data. The configure probe and
provider-selection suite also check real fixed and defective libraries, buffer
ownership, offline builds and reconfiguration.

See [the implemented contract](../../design/native-character-content.md),
[requirement evidence](native-character-content-evidence.md),
[validation inventory](P5-16a-validation.json) and
[full audit](audits/P5-16a-native-character-content.md). Three affected Valgrind
runs have zero errors/lost blocks. All 136 source suites have passing final
results; the original large-WSDL timeout and unchanged-source completion remain
recorded. WSDL declaration-level nil/default/fixed conversion follows separately;
complete P5-P9 acceptance and the independent P9 AOT finding remain open.


## Element constraint declarations (P5-16b)

`../wsdl-element-constraints.qtest` validates default/fixed lexical values and
content eligibility, retained metadata, references/imports, reconstruction,
recovery and cancellation. `test_element_constraints.py` compares 188 schemas
and 376 actual SOAP 1.1/1.2 binding descriptions with pinned Xerces.

See [the implemented contract](../../design/wsdl-element-constraints.md),
[requirement evidence](element-constraints-evidence.md),
[validation inventory](P5-16b-validation.json) and
[full audit](audits/P5-16b-element-constraints.md). Instance default application,
fixed-value comparison and nil handling remain open P5 work.


## Nilled elements and ordered native mixed values (P5-16c)

`XsdNilValue` preserves a present nilled element and its validated native attributes.
Receiving declarations check nillability, boolean lexical forms, content, fixed
constraints, occurrences and required attributes. `XsdMixedContentDataType` keeps
ordered text/CDATA/comment segments and typed child occurrences, including repeated
list values, selected types, substitution members and wildcard XML. Namespace
contexts, saved providers, samples and real HTTP consumers retain these contracts.

See the [nil design](../../design/wsdl-element-nil.md),
[mixed design](../../design/wsdl-mixed-content.md),
[requirement evidence](nil-mixed-values-evidence.md),
[validation inventory](P5-16c-validation.json) and
[full audit](audits/P5-16c-nil-mixed-values.md).

```sh
qore -b --enable-debug test/wsdl-element-nil.qtest
qore -b --enable-debug test/wsdl-element-nil-http.qtest
qore -b --enable-debug test/wsdl-mixed-values.qtest
qore -b --enable-debug test/wsdl-mixed-http.qtest
python3 test/wsdl-interop/test_element_nil.py -v
python3 test/wsdl-interop/test_mixed_values.py -v
```

Use the local debug XML module and local `qlib` in `QORE_MODULE_DIR`, with the
pinned independent validator setup documented above. Element default/fixed
instance conversion, identity constraints and P6–P9 acceptance remain open.

## Canonical numeric constraint declarations (P5-18a)

`xml-numeric-defaults.qtest` checks 396 positive/negative schemas through native
conversion, DOM and streaming validation. `test_numeric_defaults.py` checks the
same committed fixture against pinned Xerces and verifies that its generator
reproduces the exact matrix. The cases include every integer family, exact large
numbers, decimal signed zero, booleans, lists/unions, QName context controls and
element/attribute/reference/simple-content declarations. Run:

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/xml-numeric-defaults.qtest
python3 test/wsdl-interop/test_numeric_defaults.py -v
python3 -B test/cmake/test_libxml2_provider.py -v
```

The native correction checks canonical validity without replacing declaration
values. It precedes the remaining WSDL instance-default work. See
[design](../../design/native-numeric-defaults.md) and
[the separate PSVI investigation](default-identity-investigation.md).

## Native binary constraints (P5-18c)

`xml-binary-constraints.qtest` checks 206 canonical declaration cases and 23
binary lexical cases through conversion, DOM and streaming validation. The
independent Python test reproduces both committed fixtures and checks them with
pinned Xerces. Hexadecimal canonical forms use uppercase; Base64 canonical forms
omit whitespace. Non-alphabet punctuation and non-XML whitespace are rejected.

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/xml-binary-constraints.qtest
python3 -B test/wsdl-interop/test_binary_constraints.py -v
python3 -B test/cmake/test_libxml2_provider.py -v
```

Binary and whitespace normalization allocation failures retain their internal
error status. The normalized-string path retains its owned buffer through
cleanup. See [design](../../design/native-binary-constraints.md) and
[acceptance evidence](native-binary-constraints-evidence.md). WSDL binary canonical
checks, other canonical families and instance defaults remain P5 work.

## WSDL canonical numeric declarations (P5-18b)

WSDL checks the same 396 declarations as the native compiler. Canonical validation
uses the actual selected list/union members and retains the first conversion's
value even when canonical text selects a different union member. Saved schemas,
message providers and both actual SOAP bindings preserve the constrained values.

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-numeric-constraints.qtest
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-numeric-constraints-http.qtest
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_numeric_constraints.py -v
```

The independent matrix checks 2,804 construction/direction records and validates
1,616 serialized SOAP payloads with pinned Xerces, comparing their values and
expanded QName identities independently. See [design](../../design/wsdl-canonical-constraints.md)
and [acceptance evidence](wsdl-canonical-constraints-evidence.md). Empty-element
default projection and other canonical datatype families remain separate P5 work.

## Native IEEE constraints (P5-18e)

Native float/double conversion validates complete XML lexical forms and preserves
the selected IEEE value independently of process locale and rounding state.
Canonical default/fixed declarations use shortest round-trip digits with XSD 1.0
scientific syntax. The private library build uses a C++17 charconv helper.

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/xml-ieee-constraints.qtest
python3 -B test/wsdl-interop/test_ieee_constraints.py -v
python3 -B test/cmake/test_libxml2_provider.py -v
```

The native suite covers 300 declarations and 90 lexical cases. The provider suite
adds 1,314 integer-rational expectations in four rounding modes and tests caller
environment preservation. Pinned Xerces's zero defect and smallest-subnormal
precision differences are recorded explicitly in the declaration fixtures.
See [design](../../design/native-ieee-constraints.md),
[evidence](native-ieee-constraints-evidence.md) and [inventory](P5-18e-validation.json).

## WSDL canonical binary declarations (P5-18d)

Binary default/fixed declarations validate uppercase hexadecimal and unwrapped
Base64 while retaining the original selected values. Tests cover elements,
attributes and references, lists/unions, empty and large values, interrupted
conversion, saved providers and actual SOAP 1.1/1.2 HTTP consumers.

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-binary-constraints.qtest
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-binary-constraints-http.qtest
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_wsdl_binary_constraints.py -v
```

The independent matrix accounts for 1,498 records and validates 880 SOAP
payloads with pinned Xerces while separately comparing their decoded octets.
See [design](../../design/wsdl-canonical-constraints.md),
[evidence](wsdl-binary-constraints-evidence.md) and
[inventory](P5-18d-validation.json). Remaining P5 criteria remain open.

## Native fixed values and scalar validation (P5-16d)

`../xml-value-space.qtest` checks typed fixed-value equality, empty lists,
precision, clock offsets and unsigned lexical forms through all three native XML
APIs. `test_native_value_spaces.py` covers 95 schemas and 774 documents, including
simple and complex simple content, selected-type identity, fixed/enumeration equality and four time range
facets. It preserves original XML and asserts rejection categories. Fourteen
Xerces midnight defects are individually classified in `xerces-time-midnight.json`;
every native expectation remains enforced.

CMake detects the installed library's fixed, time, unsigned and allocation-error
behavior. The private corrections are covered by `test/cmake/test_libxml2_provider.py`
and the allocation-failure executable it builds. See
[native value-space evidence](native-value-spaces-evidence.md),
[validation inventory](P5-16d-validation.json) and
[full audit](audits/P5-16d-native-value-spaces.md).

### Native builtin particle inheritance

`../xml-anytype-particles.qtest` covers builtin particle ownership, direct and
inherited lax content, group references, restrictions, invalid declared children,
cancellation and concurrent parsing. `test_anytype_particles.py` compares ten
schemas and 100 documents through all native XML APIs and pinned Xerces.
The provider suite independently rejects the former inconsistent particle layout
and an otherwise corrected library which still collapses empty group references.
See [native anyType evidence](native-anytype-evidence.md),
[inventory](P5-16e-validation.json) and [audit](audits/P5-16e-native-anytype.md).

[Default/identity semantics](default-identity-investigation.md) remain an open
P5 adjudication; instance default application, WSDL fixed-value enforcement,
identity constraints, the remaining valid corpus failures and P6-P9 stay required.


`test/wsdl-fixed-values.qtest`, `test/wsdl-fixed-http.qtest` and
`test_fixed_values.py` check explicit nonempty element fixed values by XSD value
identity. The independent matrix retains 53 schemas/172 documents/688 actual
SOAP binding directions and validates 1,257 outputs with pinned Xerces. Tests
include native/ordinary providers, constrained examples, saved old-format
providers, forward object references, cancellation and concurrent first use.
See [the fixed-value contract](../../design/element-fixed-values.md) and
[acceptance evidence](fixed-values-evidence.md). Empty-element default processing
and the documented default/identity interaction remain separate P5 work.

## Native document ID bindings (P5-17a)

The native XML APIs enforce document ID/IDREF closure after selecting actual
datatypes, including defaults, unions, lists, wildcards and dynamic types.
`test_native_id_bindings.py` checks 21 schemas and 68 documents against pinned
Xerces and records ten explicit disagreements with the XSD 1.0 owner/default
rules. Independent agreement never replaces the normative native expectations.
The configure probe also checks subtree isolation, nil and DOM type markers.

```sh
qore -b --enable-debug test/xml-id-bindings.qtest
python3 test/wsdl-interop/test_native_id_bindings.py -v
python3 test/cmake/test_libxml2_provider.py -v
```

Use the local Debug module and pinned runtime/validator setup above. See the
[implemented design](../../design/native-id-bindings.md),
[evidence](native-id-bindings-evidence.md), [inventory](P5-17a-validation.json)
and [full audit](audits/P5-17a-native-id-bindings.md). This native prerequisite
does not close WSDL identity processing: the 16 invalid reference acceptances
remain visible in both corpus modes. Empty-element defaults and P6–P9 remain open.

## WSDL document ID bindings (P5-17b)

Qore's scope-cleanup prerequisite is verified in installed build `8c0c22c15`.
The final 149-suite gate and forced AST/IR/JIT/tiered/AOT checks pass.

WSDL checks selected ID/IDREF/IDREFS values within the assessed XML root,
including forward references, same-parent ownership, lists/unions, nil and
assessed wildcards. Ordinary/native/retained providers and actual SOAP 1.1/1.2
HTTP consumers enforce the same checks after conversion. The 16 invalid corpus
identity directions are rejected; native mode has no remaining validity-stage
failure, while legacy mode retains its four documented dynamic-type failures.
Typed preservation is still unassessed for 824 native directions. See
[evidence and reproduction](id-bindings-evidence.md),
[design](../../design/wsdl-id-bindings.md), [inventory](P5-17b-validation.json)
and [full audit](audits/P5-17b-id-bindings.md). Empty-element defaults and
key/unique/keyref constraints remain P5 work; P6–P9 are not complete.

## WSDL IEEE constraints (P5-18f)

`canonical_xsd_float()` supplies canonical scientific text at binary32/binary64
precision. WSDL uses the selected value for declaration reassessment while
retaining original defaults, fixed identities and lexical carriers. The tests
cover 300 schemas, 1,248 SOAP payloads and 1,314 exact-rational API cases.

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/xsd-float-canonical.qtest
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-ieee-constraints.qtest
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-ieee-constraints-http.qtest
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_ieee_canonical.py -v
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_wsdl_ieee_constraints.py -v
```

All 48 pinned Xerces differences remain explicit. Separately identified schema
derivatives assess explicit instances without changing the original declaration
results. See [evidence](wsdl-ieee-constraints-evidence.md),
[design](../../design/wsdl-canonical-constraints.md) and [inventory](P5-18f-validation.json).

## WSDL calendar constraints (P5-18g)

WSDL uses exact calendar arithmetic to validate canonical dateTime/time/date
constraints while retaining selected values, fractional digits, absent timezones
and recoverable date offsets. Tests cover 306 schemas, 18 boundaries and 1,296
SOAP payloads, including saved providers and actual HTTP consumers.

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-calendar-constraints.qtest
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-calendar-constraints-http.qtest
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_calendar_constraints.py -v
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_wsdl_calendar_constraints.py -v
```

The 48 Xerces declaration and 30 fixed-instance differences remain explicit.
See [evidence](wsdl-calendar-constraints-evidence.md),
[design](../../design/wsdl-canonical-constraints.md) and [inventory](P5-18g-validation.json).
The [native calendar defect](p5-native-calendar-constraints-finding.md) remains
required P5 work, independently of the corrected WSDL declaration path.

## Exact native calendars (P5-18h)

Native schema validation now preserves arbitrary calendar years and fractional
seconds through parsing, copy, comparison and canonical formatting. Complete
calendar declarations receive canonical assessment; dates retain recoverable
offsets. Provider checks detect both value and declaration defects independently.

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/xml-calendar-constraints.qtest
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_temporal_values.py -v
python3 -B test/cmake/test_libxml2_provider.py -v
```

The native suite covers 306 declarations across conversion, DOM and reader APIs.
The direct C matrix checks 9,807 exact records, with 105 datatype and 3,273
canonical-declaration allocation failures tested separately. See
[evidence](native-calendar-constraints-evidence.md),
[design](../../design/native-calendar-constraints.md) and [inventory](P5-18h-validation.json).
The preceding native calendar finding is resolved; default PSVI and the remaining
P5–P9 requirements remain active.

## WSDL notation declaration metadata (P5-19b)

`test/wsdl-notation-declarations.qtest` checks notation identifier storage through
schema composition, failed additions, saved schemas and detached namespace contexts.
`XsdNotationInfo` keeps expanded names and public/system identifiers, including the
distinction between absent and empty identifiers. Lookup uses `"{namespace}name"`,
including `"{}name"` for no namespace. See the [API design](../../design/wsdl-notation-declarations.md).

```sh
qore -b --enable-debug test/wsdl-notation-declarations.qtest
python3 -B test/wsdl-interop/test_notation_declarations.py -v
```

The executable Python suite generates 54 independent schema cases and compares
native/WSDL rejection categories, six metadata reconstruction paths and pinned
Xerces 2.12.2. The Qore suite adds 391 assertions for imports/includes, duplicates,
rollback, cancellation, concurrent copies and both inline SOAP binding descriptions.
All 167 regression suites and eight supplements pass. Corpus results remain
unchanged in both decoding modes; see [acceptance evidence](notation-declarations-evidence.md).
NOTATION value conversion and its provider/HTTP integration remain the next P5 work.

## QName attribute provider choices (P5-19c)

Enumerated and fixed QName attributes now expose their scalar validator through
attribute-use wrappers when building finite choices. Saved fields and providers
retain namespace-aware validation and required/optional semantics. The focused
provider and actual SOAP HTTP suites pass 437 and 468 assertions; all 38 affected
suites and six supplements pass. Both decoding-mode corpus results are unchanged.
See [evidence](qname-attribute-provider-evidence.md),
[implemented design](../../design/wsdl-qname-values.md) and
[audit](audits/P5-19c-qname-attributes.md). NOTATION integration remains next.

## WSDL NOTATION values (P5-19d)

`XsdNotationValue` preserves notation identity independently of QName. Scalar,
list, union, default/fixed, saved providers and both SOAP HTTP bindings validate
schema-declared names. Enum-derived schema uses are checked after resolution;
unused intermediate restrictions and dynamic builtin assessment remain supported.
Examples are validated notation values. See [design](../../design/wsdl-notation-values.md),
[evidence](notation-values-evidence.md), [inventory](P5-19d-validation.json) and
[audit](audits/P5-19d-notation-values.md).

Run `wsdl-notation-values.qtest`, `wsdl-notation-http.qtest` and
`python3 -B test/wsdl-interop/test_wsdl_notation_values.py -v` with local modules.
The two Qore suites pass 435 and 440 assertions. The Python matrix covers 66
schemas and 2,736 binding rows; 24 identity/legacy-projection failures remain
explicitly failed rows assigned to subsequent P5 work. A separate reduction
records 48 [default namespace oracle disagreements](notation-default-context-evidence.md).
The original NOTATION default fixtures keep their historical `wsdl=False` selector
for the older unqualified-root default worker; this dedicated worker now covers
both qualified NOTATION default/fixed models without altering the source fixtures.

All 169 suites in the broad run passed across implementation revisions, followed
by 57 affected suites on frozen final inputs and eight supplemental checks. Both
corpus modes retain their prior results. P5 declaration grammar, identity
constraints and complete typed accounting remain open; P6–P9 remain required.

## Native annotation attributes (P5-19e)

The 117 authored schemas in `fixtures/annotations.json` are Copyright (C) 2026
Qore Technologies, s.r.o. Three native APIs and pinned Xerces agree on 54 valid
and 63 invalid schemas. Foreign `lang` attributes are accepted; documentation
`source` values are validated without retrieval. Run `test/xml-annotations.qtest`
and `python3 test/wsdl-interop/test_annotations.py -v`. See
[evidence](native-annotations-evidence.md), [inventory](P5-19e-validation.json),
[full audit](audits/P5-19e-native-annotations.md) and the resolved
[WSDL counterpart](p5-wsdl-annotation-finding.md). Existing corpus results are
unchanged in both decoding modes. Python CI integration remains P9 work.

## WSDL annotations and URI API (P5-19f)

Ordered annotation grammar and document IDs are checked before component grouping.
Complex-type documentation accepts empty and mixed content while retaining text
order. `normalize_xsd_uri()` validates and collapses URI whitespace without
retrieving references. Run `test/wsdl-annotations.qtest` and
`test/xml-uri-values.qtest`; annotated real HTTP coverage is in
`test/wsdl-notation-http.qtest`. See [evidence](wsdl-annotations-evidence.md),
[inventory](P5-19f-validation.json), [audit](audits/P5-19f-wsdl-annotations.md)
and [design/example](../../design/wsdl-schema-annotations.md).
The [scalar URI/language gap](p5-wsdl-uri-language-finding.md) is next, followed by
remaining P5 identity constraints and typed accounting. P6-P9 remain required.

## URI and language values (P5-19g)

The eight authored schemas and 73 documents in `fixtures/uri-language.json` are
Copyright (C) 2026 Qore Technologies, s.r.o. Run `test/wsdl-uri-language.qtest`,
`test/wsdl-uri-language-content.qtest`, `test/wsdl-uri-language-http.qtest` and
`python3 test/wsdl-interop/test_uri_language.py -v`. Both conversion directions
and saved providers validate lexical values while preserving URI spelling,
language case and union primitive identity. Empty defaults follow the approved
canonical-actual-type interpretation. See [design/example](../../design/wsdl-uri-language-values.md)
[evidence](uri-language-evidence.md), [inventory](P5-19g-validation.json)
and [full audit](audits/P5-19g-uri-language.md). Python CI wiring remains P9 work.

## Native identity XPath grammar (P5-20a)

The 54 authored schemas in `fixtures/identity-paths.json` are Copyright (C) 2026
Qore Technologies, s.r.o. Run `test/xml-identity-paths.qtest` and
`python3 -B test/wsdl-interop/test_identity_paths.py -v`. Native APIs reject empty
union arms while retaining legal whitespace, wildcard names and explicit axes.
Two Xerces token-spacing defects remain explicitly classified against the valid
original schemas; see [evidence](identity-paths-evidence.md) and
[implemented design](../../design/native-identity-paths.md). WSDL identity
declarations and instance semantics remain the next P5 increment.

## Identity declaration grammar and component QNames (P5-20b)

The authored 86-schema `fixtures/identity-grammar.json` and 91-schema
`fixtures/component-qnames.json` matrices are Copyright (C) 2026 Qore Technologies,
s.r.o. Run `test/wsdl-identity-grammar.qtest`, `test/xml-component-qnames.qtest`,
`test/wsdl-notation-http.qtest` and the independent Python checkers
`test_identity_grammar.py` and `test_component_qnames.py`. WSDL validates ordered
selector/field declarations and path syntax before grouping; native component
references resolve normalized QNames with checked allocation diagnostics.
See [design/example](../../design/wsdl-identity-grammar.md),
[evidence](identity-grammar-evidence.md), [inventory](P5-20b-validation.json) and
[full audit](audits/P5-20b-identity-grammar.md). Retained identity components,
keyref component resolution and instance tuples remain next in P5; Python CI
wiring and full supported-environment acceptance remain P9 work.

## Retained identity components (P5-20c)

The authored 30-schema `fixtures/identity-components.json` is Copyright (C) 2026
Qore Technologies, s.r.o. Run `test/wsdl-identity-components.qtest` and
`python3 test/wsdl-interop/test_identity_components.py -v` with local modules.
The matrix contains 14 valid and 16 invalid schemas; two explicitly recorded
Xerces forward-keyref oracle defects remain invalid schemas. Reversed-order
derivatives isolate that source-level defect.

Element declarations now retain compiled selectors and ordered fields. The
schema resolves expanded names, duplicate identities, keyref target categories
and field counts before publishing additions. Saved graphs retain validated
metadata. See [design/example](../../design/wsdl-identity-components.md),
[evidence](identity-components-evidence.md), [inventory](P5-20c-validation.json)
and [full audit](audits/P5-20c-identity-components.md). Scoped instance tuple
assessment remains in P5; native key nillability and nil-as-missing are accepted
in P5-20d/e below. Component acceptance passes with the separately fixed prebuilt
Qore runtime; CI environment acceptance remains P9.

## P5-20d native key nillable declaration assessment

Copyright (C) 2026 Qore Technologies, s.r.o. applies to the authored
`fixtures/key-nillable.json` matrix and accompanying regression code.

Native key fields reject nillable element declarations independently of the
instance's `xsi:nil` value. The 63-case matrix covers simple/complex content,
references, substitution members, strict wildcards, dynamic types, shared
constraints, unselected nodes and attribute fields on nil owners.
Run `test/xml-key-nillable.qtest` with local Debug XML and `--enable-debug`,
and `python3 test/wsdl-interop/test_key_nillable.py -v` for pinned Xerces.
See [evidence](native-key-nillable-evidence.md) and
[implemented design](../../design/native-key-nillable.md).

This independent native correction does not implement WSDL instance tuples or
adopt a nil unique/keyref interpretation. P5-20e below implements the approved
interpretation. The separate Qore serialization prerequisite is verified in the
P5-20c component evidence.

## P5-20e approved nil identity values

The user approved nil-as-missing for unique/keyref on2026-09-14. That question
is resolved. The native implementation retains selected-node cardinality,
admissible field types, empty-string values and the key nillable restriction.
The148-case matrix includes96 valid and52 invalid instances, with29 explicitly
classified Xerces differences. Authored JSON fixture content is copyright2026
Qore Technologies, s.r.o.; embedded W3C originals retain their provenance.

Run `test/xml-nil-identities.qtest` with local Debug XML and `--enable-debug`,
and `python3 test/wsdl-interop/test_nil_identities.py -v`. See
[interpretation and corrected historical evidence](nil-identity-interpretation.md),
[native evidence](native-nil-identities-evidence.md) and
[implemented design](../../design/native-nil-identities.md).

The separate Qore serialization fix has now passed the P5-20c component gate
using its prebuilt Debug runtime. Scoped WSDL tuples and complete typed
accounting remain P5 work and use the approved nil-as-missing rule.

Native identity-table inheritance uses `test/xml-identity-tables.qtest` and
`test_identity_tables.py`. The 54 authored documents cover sibling conflicts,
order changes, recursive local precedence, overlapping selectors and composite
keys; their fixture JSON is Copyright (C) 2026 Qore Technologies, s.r.o.
See [implemented behavior](../../design/native-identity-tables.md) and
[validation evidence](native-identity-tables-evidence.md). WSDL instance tuple
validation remains in the ongoing P5-20f increment. The
[skipped-subtree interpretation](skipped-subtree-interpretation.md) is approved.

P5-20h adds native instance-attribute and list-variety assessment.
`test/xml-instance-identities.qtest` exercises 121 documents across 41 schemas,
including lexical rejection, wildcard assessment, attribute cardinality,
empty lists, nil, union selection, defaults and keyrefs. The fixture JSON is
Copyright (C) 2026 Qore Technologies, s.r.o. Run
`python3 test/wsdl-interop/test_instance_identities.py -v` for the pinned Xerces
check. Three multiple-attribute field cases retain an explicit Xerces matcher
difference. See [design](../../design/native-instance-identities.md) and
[evidence](native-instance-identities-evidence.md).

The user approved the [legacy anySimpleType projection policy](legacy-identity-projection.md)
on 2026-09-15. Serialization must reject a projected value if it violates identity
constraints; native type retention and complete XML carriers remain the lossless
paths. The prototype's expected legacy rejection is recorded separately from
lossless success. WSDL instance tuples and the remaining P5 criteria are still
in progress.

Ordinary recursive providers retain complete nested field definitions through
saved graphs and soft copies. Run `test/wsdl-recursive-providers.qtest`,
`test/wsdl-provider-optionality.qtest` and `test/wsdl-provider-graph-size.qtest`
with local XML/WSDL modules and a Qore runtime containing `16ae86ca7`. The last
test checks the shared-graph conversion bound with a leaf-conversion counter.
See the [implemented design and example](../../design/wsdl-recursive-providers.md).

## Scoped WSDL instance tuples (P5-20j)

`test/wsdl-identity-tuples.qtest` validates 165 authored schema/instance pairs
through source/saved schemas, both preservation modes, serialization and ordinary
providers. `test/wsdl-identity-instance-attributes.qtest` adds 36 builtin-instance-
attribute pairs with separate native and WSDL tests. The fixture JSON files are
Copyright (C) 2026 Qore Technologies, s.r.o. Expected WSDL, native and Xerces
outcomes are separate fields; processor choices and reference defects are not
silently treated as validator agreement.

Run with the local XML binary and WSDL source paths:

```sh
qore -b --enable-debug test/wsdl-identity-tuples.qtest
qore -b --enable-debug test/wsdl-identity-instance-attributes.qtest
qore -b --enable-debug test/wsdl-identity-lossless-paths.qtest
qore -b --enable-debug test/wsdl-identity-tuples-http.qtest
qore -b --enable-debug test/wsdl-identity-tuple-lifecycle.qtest
python3 test/wsdl-interop/test_identity_tuples.py -v
python3 test/wsdl-interop/test_identity_tuple_resources.py -v
```

The HTTP test uses distinct SOAP 1.1/1.2 bindings with client, handler and
SoapDataProvider request/response checks. Lifecycle coverage checks custom
conversion counts, interruption/retry, flat table boundaries and concurrent
saved-schema consumers. The structural probe checks retained entries and
inherited-table traversal using a temporary instrumented module.

See the [implemented design and catalog example](../../design/wsdl-identity-tuples.md).
The [legacy projection policy](legacy-identity-projection.md) retains its explicit
expected serialization rejection; that rejection is not counted as lossless
forwarding. Complete P5 typed/infoset accounting and P6–P9 remain required.

Final tuple validation and reference differences are recorded in
[the acceptance evidence](identity-tuples-evidence.md).


## Character whitespace at instance boundaries (P5-21)

`XPF_PRESERVE_WHITESPACE | XPF_PRESERVE_ORDER` retains whitespace between
children even if no other text is present. WSDL message parsing and `XsdXmlValue`
views use both flags; schema-aware conversion removes indentation only for
element-only content. Direct callers supplying parsed hashes should use both
flags too. Whitespace now separates repeated names into ordered keys such as
`entry^1` in XML-value views. The unflagged XML data parser keeps its existing
grouping behavior.

```sh
qore -b --enable-debug test/xml-preserve-whitespace.qtest
qore -b --enable-debug test/wsdl-character-whitespace.qtest
qore -b --enable-debug test/wsdl-generic-http.qtest
python3 test/wsdl-interop/test_character_whitespace.py -v
```

The independent test compares all characters, expanded names, attributes and
ordered children across 288 conversions using both actual SOAP bindings,
both directions, saved providers and both projection modes. It records the
established legacy inferred scalar annotations explicitly; native mode retains
their absence. Xerces validates all 18 sources and 288 outputs. A negative
comparison demonstrates why schema validity alone cannot establish preservation.
See [evidence](character-whitespace-evidence.md), [validation inventory](P5-21-validation.json)
and [audit](audits/P5-21-character-whitespace.md). Complete P5 typed/namespace
accounting and P6–P9 remain open.

The independent typed observer is qualified by
`python3 -B test/wsdl-interop/test_typed_reference.py -v`. Use
`independent.run_typed([SchemaJob(...)], resources)` to obtain checked observations
for documents validated against the same schema, then
`typed_reference.compare(before, after, order="exact")` to compare them.
The explicit `per-name` alternative permits only the established element-only
flat-record ordering contract. See [observer evidence](typed-observer-evidence.md)
for exact scalar/namespace semantics, examples, resource limits and the remaining
coverage-integration boundary. Missing observations fail the harness.

Complete typed corpus accounting uses the stricter P5 selection:

```sh
python3 -B test/wsdl-interop/test_typed_coverage.py -v
python3 -B test/wsdl-interop/coverage.py /tmp/wsdl-corpus/databinding/examples/6/09 \
  --preserve-types --selection test/wsdl-interop/p5-selection.json --strict \
  --output /tmp/wsdl-p5-native-coverage.json
```

Existing normative assertions remain mandatory. Run and retain the legacy report
separately; its type/nil projection losses must remain failures. See
[typed accounting evidence](typed-coverage-evidence.md) for the selection, ordering
contract, observation provenance and coverage boundaries.

## WSDL declaration identity

`test/wsdl-declaration-identity.qtest` checks WSDL root identity, normalized NCNames,
duplicate owner scopes and empty components through source/saved graphs.
`python3 -B test/wsdl-interop/test_wsdl_declarations.py -v` runs 25 pinned-schema
reference cases. See [evidence](declaration-identity-evidence.md) and
[implemented design](../../design/wsdl-declaration-identity.md).

Document-local component references use `test/wsdl-component-references.qtest`
and `python3 -B test/wsdl-interop/test_wsdl_component_references.py -v`.
The shared matrix distinguishes schema lexical validity from correct expanded
reference targets; saved graphs and actual SOAP 1.1/1.2 HTTP exchanges are covered.
See [evidence](component-references-evidence.md) and
[implemented behavior](../../design/wsdl-component-references.md). The rest of the
P6 binding matrix remains required.

Resource URI resolution uses `test/wsdl-location-resolution.qtest`, including the
RFC 3986 examples and real synchronous/asynchronous HTTP schema retrieval.
See [evidence](location-resolution-evidence.md) and
[implemented behavior](../../design/wsdl-location-resolution.md) for the distinct
directory-base and full-document URI interfaces.

`test/wsdl-document-locations.qtest` adds full containing-URI retention through all
HTTP loaders, nested schema references, saved sources and failed additions.
See [source-location evidence](document-locations-evidence.md).


`test/wsdl-imported-components.qtest` checks transitive WSDL/XSD import graphs,
namespace collisions, shared schema instantiation, scoped references, qualified
lookups, saved dependencies and both SOAP versions over local HTTP. Independent
component observations use:

```bash
python3 -B test/wsdl-interop/test_wsdl_imports.py -v
```

The test compiles `oracle/WsdlImportOracle.java` with a local JDK and the pinned
WSDL4J 1.6.3 JAR. It verifies artifact hashes before use and needs no network.
The accompanying upstream license and notice are retained unchanged; their
checksums and provenance are in `oracle/wsdl4j-manifest.json`. WSDL4J supplies
resolved component observations, not complete WSDL or SOAP validation. See
[import evidence](imported-components-evidence.md) for the exact checked edges
and remaining P6 work.

## Local file URI resources (P6-08)

Absolute and localhost file URIs now load escaped filenames consistently through
WSDLLib, SoapClient and asynchronous loading. Nested WSDL/XSD imports retain
canonical containing URIs; saved graphs rebuild after the original files are
removed. Bare and legacy relative file paths retain literal filename semantics.
The new suite passes 7 cases / 291 assertions; see [evidence](file-uri-evidence.md),
[validation](P6-08-validation.json) and [audit](audits/P6-08-file-uris.md).
Redirect-effective URI handling and the remaining P6–P9 requirements stay open.

## Shared Qore URI resolution (P6-09)

WSDL document references, retained XML Base, native HTTP schema locations and
WebContentUtil use Qore 3.0 URI support. File URI conversion uses FileLocationHandler
3.0. See [evidence](qore-uri-evidence.md), [validation](P6-09-validation.json) and
[audit](audits/P6-09-qore-uri.md). WSDL redirect graph integration remains separate.

## Redirect resource metadata (P6-10)

WSDL/SoapClient synchronous and asynchronous loading use effective resource URIs
for dependency bases and retain redirect aliases for offline reconstruction.
Focused tests cover namespace checks, conflicting content, encoding, custom
handlers and failed-addition rollback. See [evidence](redirect-resource-evidence.md),
[validation](P6-10-validation.json) and [audit](audits/P6-10-redirect-resources.md).
The remaining P6 binding/operation work and P7–P9 remain open.
