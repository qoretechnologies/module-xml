# Wildcard attribute instances: P5-10 evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

Implementation parent: `a2ce739`. Production changes are in `qlib/WSDL.qm`.
The [implemented contract](../../design/wsdl-wildcard-attributes.md) describes
expanded names, typed and unassessed values, registry ownership and providers.

## Requirements and root causes

[XSD 1.0 Structures, sections 3.4.4 and 3.10.4](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/)
require wildcard namespace admission and distinguish required declaration
validation, validation when a declaration is available, and skipped assessment.
The completed wildcard metadata already existed, but instance conversion used
the broad legacy `anyAttribute` flag. Valid attributes were discarded during
decode and rejected during serialization; strict/lax declaration constraints
were not enforced. The reduced initial fixture declares an integer attribute
and a wildcard-only root. It reproduced both lost `017` and accepted invalid
integer text before the fix; all four initial unit cases failed.

The implementation resolves known attributes in a completed shared global map,
retains typed values through existing scalar APIs, and preserves unassessed
text with `XsdScopedLexicalValue`. Expanded keys distinguish same-local-name
attributes. Empty/default namespace context and tabs, LF and CR remain intact.
Declared uses take precedence; aliases cannot overwrite another attribute.
The same checks apply to ordinary and explicit native providers.

Additional regressions identified and fixed:

- Wildcard-only and simple-content provider construction omitted the attribute
  map. Empty complex values also lost their established native `NOTHING` form.
- Native hash assignment could bypass the attribute-map provider. Its direct
  type shortcuts are disabled, and soft copies preserve its validation.
- Caller-added provider fields could masquerade as declared schema attributes.
  Admission now consults the actual declaration map even for an added field.
- Reserved XML attributes require the `xml` prefix. Foreign wildcard attributes
  also introduce namespaces absent from the original schema.
- SOAP copied namespace declarations before converting body/header parts.
  It now publishes the complete map afterward, using a separate map per message.
- A decoded unassessed value must retain absence of a default namespace, so
  combining it with incompatible QName output cannot silently change its context.

XSD 1.0's per-element wildcard-ID rules are enforced in the WSDL layer. A separate
pre-existing [native reporting defect](p5-native-wildcard-id-finding.md) remains
assigned to P5-11: libxml2 sets the two error states but does not report them.
Six lxml omissions are explicit supporting-validator discrepancies; Qore and
pinned Xerces must still reject those inputs. Native DOM/reader acceptance is
recorded as a failure and is not included in a conformance claim.

## Executable evidence

| Area | Checks |
| --- | --- |
| Instance/provider unit | `wsdl-wildcard-attributes.qtest`: 13 cases/302 assertions; all processing modes and namespace forms, fixed/list/QName values, imported and no-namespace declarations, inherited groups and derivation, alias collisions, malformed native/serialized metadata, empty/simple content and soft providers |
| Registry ownership | `wsdl-wildcard-attribute-registry.qtest`: 2 cases/17 assertions; live publication, serialized snapshots, failed additions, detached provider lifetime and malformed registry reconstruction |
| HTTP/lifecycle | `wsdl-wildcard-attribute-http.qtest`: 4 cases/138 assertions; eight loopback exchanges through SoapClient/SoapHandler/SoapDataProvider, native and retained requests/responses in both bindings, four concurrent serializers, failed conversion and cancellation recovery |
| Independent matrix | `test_wildcard_attributes.py`: 39 schemas/324 documents, 2592 ordered result rows and 4248 independently validated outputs per mode; known values and unassessed lexical namespace bindings are compared separately |
| Execution engines | Three unit/HTTP/registry suites and the independent matrix pass AST, IR, JIT, tiered and compiled WSDL; registry tests have their own five-mode runner |
| Existing behavior | The 125-suite regression gate plus registry suite pass 1270 cases/62684 reported assertions; the legacy SOAP suite includes three intentional caught comparator negatives |
| Build/consumers | Six qmods and WSDL Doxygen build without warnings; 19 compiled/consumer/previous-matrix/harness supplements plus compiled registry pass, including Cargo/CDA and the executed shipment example |
| Corpus | Both-version survey completes all 2455 rows; strict coverage selects 144 WSDLs/1388 directions with no selected, missing, skipped or value failures; 60 broader failures remain, down from 64 |

The independent matrix validates input and three output forms: SOAP native
serialization, standalone serialization and retained XML. It includes both
request/response directions and reconstructed WebService/provider graphs.
Actual SOAP 1.1 and SOAP 1.2 binding declarations are used. Imported resources
are supplied from an explicit offline cache; unknown resources fail.

The four removed corpus failures are the original invalid
`AnyAttributeOtherStrict` messages in both versions and directions. They now
raise `SOAP-DESERIALIZATION-ERROR` for the missing strict global declaration.
These required rejections are added to `strict-selection.json`. Lower diagnostic
serialization counts reflect rejected invalid input, not lost valid coverage.
Original corpus files and historical findings are unchanged.

Run with the local development runtime/module paths and debugging:

```sh
qore -b --enable-debug test/wsdl-wildcard-attributes.qtest
qore -b --enable-debug test/wsdl-wildcard-attribute-registry.qtest
qore -b --enable-debug test/wsdl-wildcard-attribute-http.qtest
python3 test/wsdl-interop/test_wildcard_attributes.py -v
```

[P5-10-validation.json](P5-10-validation.json) records source/fixture/runtime
SHA-256 values, command results and five replayable acceptance runners.
The [full audit](audits/P5-10-wildcard-attributes.md) records every checklist item.
No native code changed; native XML and isolated libqore match P5-09.

## Remaining acceptance

P5 remains open for the native wildcard-ID report, element wildcard processing,
mixed/generic content, complete nil/default/fixed and document identity semantics.
P6-P9 retain all binding, protocol, attachment, independent-peer, supported-platform
and mandatory-CI requirements. These results do not establish complete SOAP or
WS-I conformance.
