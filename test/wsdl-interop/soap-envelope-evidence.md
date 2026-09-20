# P7-01 SOAP envelope and version processing

Copyright (C) 2026 Qore Technologies, s.r.o.

Native decoding removed namespaces before validating the protocol containers. It accepted a Body in the wrong namespace, unqualified header blocks, extra/duplicate containers and incompatible binding versions. Retained decoding applied only part of the same checks. Wire parsing also discarded DTD/PI information before the protocol layer could reject it. Four reduced baseline cases fail for these causes; the audit added a fifth failing probe for raw compatibility-header fragments bypassing namespace qualification.

The shared validator now checks the root, version, container order/cardinality, container attributes and qualified header blocks before payload projection. Serialization applies the same rules after QName output preparation. Raw header fragments pass through the XML generator's standalone namespace isolation and are inspected in a container with the actual namespace bindings. DTD/PI restrictions are checked on incoming wire XML and the complete outgoing document with XmlReader. Already-projected hashes cannot recover discarded constructs. MIME content and non-SOAP MIME XML keep their existing behavior.

Strict version checks use the concrete selected SOAP binding. Incoming request version mismatches take precedence over malformed container content; SOAP 1.2 clients retain the required SOAP 1.1 VersionMismatch transition fault. SoapHandler faults advertise the known supported version with Upgrade/SupportedEnvelope. Both handler-generated and operation-generated SOAP 1.2 fault reasons now include the required language attribute. Explicit named fault APIs preserve their existing wrong-version SOAP-DESERIALIZATION-ERROR contract.

The normative basis is [SOAP 1.1 sections 3–4](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/) and [SOAP 1.2 Part 1](https://www.w3.org/TR/soap12-part1/) sections 2.8, 5.1–5.4 and appendix A. SOAP 1.1's qualified envelope extensions after Body remain allowed; SOAP 1.2 rejects them. For processing instructions, the receiver follows the specification's recommendation to fault.

| Requirement | Executable evidence |
| --- | --- |
| SOAP 1.2 `x1-soapenvelope-prop`, `x1-soapbody-prop`; SOAP 1.1 section 4 structure | `soap-envelope.qtest` valid/invalid/version cases: source, serialized graph and data graph; native and retained request/response paths; namespace aliases, default resets, text and order negatives |
| SOAP 1.2 `x1-soapenv-dtd`, `x1-soapenv-pi`; SOAP 1.1 section 3 | Wire/retained document negatives in `soap-envelope.qtest`, outgoing raw-header PI rejection, Python sender/receiver peers; generic MIME XML positive control |
| SOAP 1.2 sections 5.1–5.3 protocol attributes and qualified blocks | Container attribute, encodingStyle and unqualified-header negatives; qualified optional and compatibility headers; standalone fragment isolation, malformed fragments and caller-owned input preservation |
| SOAP 1.2 section 2.8, appendix A, `x1-soapsupportedenv-prop`, `x1-soapqnamesu-prop` | Both-version live mismatch faults, expanded Upgrade QName checks, SOAP 1.1 transition fault decoding and rejection of unrelated fault codes |
| SOAP 1.2 section 5.4.2 Reason/Text language | lxml validation of both handler and WSDL operation faults against pinned unmodified W3C envelope schemas |

Assertion identifiers refer to the [W3C SOAP 1.2 assertion collection](https://www.w3.org/TR/soap12-testcollection/). This increment covers the rows above; it does not claim the collection's header-role, fault-grammar or HTTP-binding assertions are complete.

Independent Python HTTP peers exercise 168 exchanges in both directions, including repeated use of the same SoapClient after a failed response. lxml checks every emitted response/fault against pinned W3C schemas; schema imports resolve offline and pinned hashes are checked. The Qore suite adds 120 loopback malformed/valid exchanges with callback exclusion and recovery. Existing pinned CXF peers remain part of the regression gate.

Older positive fixtures were corrected where they sent SOAP 1.1 messages to a SOAP 1.2 binding or emitted unqualified SOAP headers. Processing-instruction examples remain negative fixtures, with comments-only derivatives as positive controls. The synthetic imported-header fixture now declares a qualified element; WSDL4J independently verifies that declaration and the original cycle/diamond import assertions remain active.

The immutable W3C payload corpus supplies SOAP 1.2 messages alongside SOAP 1.1-only bindings. [Named SOAP 1.2 WSDL derivatives](soap12-binding-derivatives.md) make that test adapter explicit, hash recorded and separately selected; original archive bytes and checksums remain unchanged. Current reports retain original identities and add per-message binding provenance. Comparison with P6-45 requires exactly the corrected SOAP envelope namespace on SOAP 1.2 output, associated output-observation hashes and metadata additions. All stage outcomes, classifications, failures, value comparisons and input observations must remain identical. Accepted legacy projection losses stay visible.

The whole-archive roles worker exceeded both 60- and 180-second total deadlines. Its 18 historical aggregate contracts complete in approximately 198 seconds; a representative aggregate takes 38.7 seconds on HEAD and 34.6 seconds on the working version, with the same successful parse result. This reduced comparison locates the failure in total deadline sizing, not this increment's protocol checks. It now accepts the same validated 1–3600-second `worker_timeout` option as the survey worker, including a CLI option; its full integration test uses an explicit 600-second limit for the complete aggregate workload. The original default remains 60 seconds. Invalid bounds reject before archive access, and no source fixture or expected classification is changed.

All 204 Qore suites pass: **3,265 cases / 137,774 assertions**, including the audit follow-ups. All 22 independent Python gates and 16 corpus commands meet their expected outcomes. The focused envelope suite passes **8 cases / 1,330 assertions** with source and compiled WSDL/SoapClient/SoapHandler modules. Independent peers pass 168 HTTP exchanges; the Qore suite adds 120. Documentation and 15-file astparser checks pass without warnings/errors. All six corpus comparisons preserve classifications, outcomes and values, with only the explicitly recorded SOAP 1.2 binding/output-context changes.

Evidence: [P7-01 validation](P7-01-validation.json), [audit](audits/P7-01-soap-envelope.md), [implemented design](../../design/soap-envelope-processing.md). Reduced failures, logs and compiled artifacts: `/tmp/xml-soap-envelope/`.

P7 remains open for processing attributes/roles/actors/mustUnderstand/relay, complete faults and action/media/HTTP requirements. P8 and P9 have not started. No C++ change, Qore checkout mutation, installation or push occurred.
