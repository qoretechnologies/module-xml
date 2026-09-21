# WSDL NOTATION value evidence (P5-19d)

Copyright (C) 2026 Qore Technologies, s.r.o.

Based on `7db7ddb`, this increment completes WSDL NOTATION scalar, list, union,
constraint and provider conversion. `XsdNotationValue` preserves a distinct
primitive identity. The schema/provider validates declaration membership and
inherited enumeration/pattern restrictions. Late resolution enforces enum-derived
schema uses while retaining unused intermediates and dynamic builtin assessment.
See the [implemented design](../../design/wsdl-notation-values.md).

Saved providers retain the acyclic declaration registry directly. The initial
prototype retained full namespace/schema graphs and failed while reconstructing
list facets through a partly initialized cycle. Retaining only the data needed
for declaration lookup fixes that dependency. Dynamically selected builtin types
copy the receiving registries into independent output namespace contexts.

An additional wrapper defect was reproduced and fixed: an identity-checking
element provider validated a selected type after its nested provider had restored
the temporary named-type map. Its own validation pass now establishes the
receiving schema's map. Tests cover both QName and NOTATION, original/saved native
and ordinary providers, messages and actual SOAP HTTP consumers. Provider example
generation also now validates notation candidates instead of inheriting a generic
string example that is outside the declared value space.

## Coverage and acceptance

- The broad 169-suite Qore run passes. Example generation and its focused tests
  changed during that run; its inventory records the changed hashes explicitly.
  All 57 affected suites were subsequently rerun against frozen final inputs.
- `wsdl-notation-values.qtest`: 12 cases and 435 assertions covering immutable
  values, no namespace, optional/required providers, scoped aliases, restrictions,
  scalar/repeated/attribute choices, original/saved schemas and providers, lists,
  unions, records, component-use constraints, invalid reconstruction, 300-level
  ancestry, named dynamic types, cancellation, concurrent contexts and examples.
- `wsdl-notation-http.qtest`: 440 assertions through real SOAP 1.1 and SOAP 1.2
  bindings, saved message providers and services, both directions/decoding modes,
  required and defaulted attributes, lists/unions, dynamic types and recovery.
- The binding matrix covers 66 schemas and 2,736 binding rows: 22 invalid schemas
  and 1,424 invalid documents reject; 1,288 valid document rows preserve values.
  Native output validation and pinned Xerces assess all 1,312 emitted payloads.
- The report retains **24 failed compatibility rows**: 16 duplicate-NOTATION
  identity inputs accepted by WSDL and eight legacy-mode QName/NOTATION identity
  changes producing invalid uniqueness results. Key/unique/keyref and complete
  typed accounting remain the next P5 implementation work. These are not passing
  compatibility results or a reduction in supported scope.
  **Resolved by P5-20j** (`9b8276d`, see the resolution section below).
- **48 pinned-Xerces disagreements** concern empty default namespace context.
  A separate four-schema/12-document QName/NOTATION reduction records the actual
  native and Xerces verdicts with unchanged original fixtures and derivative
  provenance; see [the analysis](notation-default-context-evidence.md).
- Eight supplements include all four execution modes and Python NOTATION bindings,
  survey, notation declarations and native NOTATION checks. Every applicable
  regression assertion passes; diagnostic failures remain visible in the report.
- Both-version surveys and strict coverage retain exactly the parent's results
  in legacy/native modes, except the expected WSDL source hash. Existing corpus
  failures remain assigned to the unfinished plan phases.
- Final WSDL docs and metadata generation pass without warnings. No C++ changed;
  no additional Valgrind run is required. Main Qore remains read-only, installed
  Qore matches the verified fixed runtime, and no installation or push occurred.

Commands, hashes and logs are under `/tmp/wsdl-p5-19d-notation-values/`; frozen
final checks are in its `final/` subdirectory. See the
[inventory](P5-19d-validation.json) and [full audit](audits/P5-19d-notation-values.md)
(20 Pass, 42 N/A, zero Fail). Python CI wiring and the complete supported-environment
matrix remain P9 work; this local acceptance does not claim CI or full SOAP compliance.

Remaining P5 work includes general annotation/document-ID grammar, identity
constraints and complete typed-preservation accounting. P6–P9 remain required.

## Resolution of the 24 compatibility rows

Scoped identity tuple validation (P5-20j, `9b8276d`) resolved both groups. The gate
was updated during P7 triage, when the SOAP 1.2 fixture actions became absolute and the
matrix ran again:

- The 16 duplicate-NOTATION rows (`primitive-identity/notation-alias`) now reject at
  decoding with `SOAP-DESERIALIZATION-ERROR`, as the oracle expects. The gate asserts
  the exact duplicate-key diagnostic.
- The eight legacy-mode `primitive-identity/qname-same-name` rows decode with both
  distinct primitive identities. Serialization then rejects them with
  `RUNTIME-TYPE-ERROR` because legacy output omits the `xsi:type` that keeps them
  distinct. This is the [approved legacy projection policy](legacy-identity-projection.md).
  The gate counts these rows as `legacy_projection_rejected`, never as lossless round
  trips.

The matrix now pins exact counts. It has 22 invalid schemas, 1,440 rejected invalid
documents, eight legacy projection rejections, and 1,288 preserved rows. All 1,288
emitted payloads are validated independently. No compatibility rows remain open. The
updated gate fails against the pre-`9b8276d` WSDL, which accepted the duplicate
NOTATION input.
