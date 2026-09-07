# WSDL and SOAP interoperability coverage

Copyright (C) 2026 Qore Technologies, s.r.o. The W3C fixtures retain their original copyright notices.

The W3C XML Schema Databinding collection is a useful independent source of WSDL 1.1 descriptions,
XSDs, and SOAP messages. Running it against this module exposed defects that the existing tests missed.
The small regression suite runs offline in the normal `test/*.qtest` CI loop. The larger survey is a
diagnostic tool with explicit failures and coverage limits, not a conformance certification.

See [PLAN.md](PLAN.md) for the phased implementation plan, acceptance checks, and a complete mapping
of the recorded findings and validator disagreements to the work needed to resolve them.
See [EXECUTION.md](EXECUTION.md) for implementation progress and commit/audit evidence.

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
rejection of the invalid signed inputs is assigned to P3.

The Python tests require Python 3.10+, `lxml`, and Qore's `json` module in addition to `xml`. They test the
real Qore subprocess, version selection, fixture checksums, empty input, namespace preservation,
malformed messages, offline resolution, and separation of input/output validation failures.
They also verify that missing, duplicate, malformed, or out-of-order worker results fail the survey.

## Fixture provenance

The first P2 increment covers declaration-local namespaces, distinct no-namespace
type identity, standalone schema reconstruction, failed-addition rollback and ordered
schema grammar. `ElementTypeDefaultNamespace` is included in the strict gate with
exact string comparisons in both directions. The derivation increment adds both empty
extension fixtures. Attribute construction and scalar `anySimpleType` support add
four families with exact text/attribute checks: 30 descriptions and 108 message-direction
combinations. The other broad failures remain visible; P2 is not yet complete.
See [the implemented design](../../design/wsdl-schema-identity.md) and [execution record](EXECUTION.md).

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

`--strict` requires the explicit [strict-selection.json](strict-selection.json) to pass: 23 WSDLs,
including all 14 source-invalid descriptions, and 68 selected message/direction combinations. Positive
cases require independent exact-value assertions; negative cases require the intended exception category.
Missing, duplicate, stale, malformed or unclassified entries fail. This selection is deliberately named
and bounded; it does not turn known implementation failures elsewhere into passing conformance tests.

[coverage-report.json](coverage-report.json) preserves the complete current ledger, including 449 failed
requirements assigned to later phases. Its stage accounting includes unreachable, missing, skipped and
unassessed work. In this run 1,860 value/infoset assessments remain unimplemented, explicitly counted as
unassessed. Successful schema validation is insufficient to close them. Exact numeric checks already
detect 40 failed value-preservation cases, including large integer derivatives clamped to 64-bit limits
and decimal values emitted with exponent notation. The report retains each expected and actual value.
Valid large `integer` values that preserve their exact number override only the documented libxml2
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
