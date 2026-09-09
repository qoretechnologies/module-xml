# WSDL and SOAP interoperability coverage

Copyright (C) 2026 Qore Technologies, s.r.o. The W3C fixtures retain their original copyright notices.

The W3C XML Schema Databinding collection is a useful independent source of WSDL 1.1 descriptions,
XSDs, and SOAP messages. Running it against this module exposed defects that the existing tests missed.
The small regression suite runs offline in the normal `test/*.qtest` CI loop. The larger survey is a
diagnostic tool with explicit failures and coverage limits, not a conformance certification.

See [PLAN.md](PLAN.md) for the phased implementation plan, acceptance checks, and a complete mapping
of the recorded findings and validator disagreements to the work needed to resolve them.
See [EXECUTION.md](EXECUTION.md) for implementation progress and commit/audit evidence.

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
python3 test/wsdl-interop/test_qname_union_validator.py -v
```

Use the local module through `QORE_MODULE_DIR`. The resource tests use independent
loopback HTTP/HTTPS servers and ephemeral certificates generated by `openssl`.
With a module built against libxml2 advertising `LIBXML_FTP_ENABLED`, also run
`python3 test/wsdl-interop/legacy_schema_ftp.py -v`. This compatibility check
does not bypass the production dependency probe. See
[schema attachment evidence](xml-reader-schemas-evidence.md) for the exact build,
memory checks and the separately recorded open URI-resolution finding.

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

`--strict` requires the explicit [strict-selection.json](strict-selection.json) to pass: 114 WSDLs,
including all 14 source-invalid descriptions, and 1,100 selected message/direction combinations. Positive
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

[coverage-report.json](coverage-report.json) preserves the complete current ledger, including 196 failed
requirements assigned to remaining phases. Its stage accounting includes unreachable, missing, skipped and
unassessed work. In this run 1,268 value/infoset assessments remain unimplemented, explicitly counted as
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
Runtime wildcard value validation and preservation remain tracked under P5.

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

The current string/length matrix covers 163 schemas and 326 actual contracts,
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
[evidence](qname-lexical-evidence.md). General QName namespace context,
enumeration identity and output prefix handling remain open requirements.

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
[independent evidence](qname-union-validator-evidence.md). General WSDL QName
instance/output integration remains a separate open P3 criterion.


## Native reader cursor values

`qore --enable-debug test/xml-reader-values.qtest` checks scalar and empty
cursor conversion, sibling boundaries, mixed content/grouping, document
hashes, errors, partial stream failure and cancellation. The QName union
validator matrix also checks both cursor methods for all 300 documents,
including exact scalar/empty results. See [the reader contract and example](../../design/xml-reader-values.md).
