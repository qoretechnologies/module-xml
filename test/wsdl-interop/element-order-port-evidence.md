# Element-order fixes ported from 2.x

Copyright (C) 2026 Qore Technologies, s.r.o.

The behaviors in 2.x commits `fb20cc85675909398fbd75bd846aaf247043a405`
and `3d07e7041cd1df10387ec95418c8d8c1a60ca246` are covered on develop's ordered
particle implementation. The original fixture is byte-identical. Its 34 assertions
remain in `soap.qtest`; exception descriptions use the complete-particle diagnostic
and provider field expectations retain develop's additional `^attributes^` field.
No negative assertion or error category was removed.

XSD 1.0 [model-group validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-model-group)
and [particle validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-particle)
require ordered sequences, one admitted choice and the declared occurrence bounds.
Native hash key order is a Qore compatibility contract. Develop already emitted
the correct XML but initialized ordinary native fields before chosen alternatives.
It now initializes both from the ordered particle declarations, preserving absent
ordinary fields and leaving unselected choices/substitutions absent.

| 2.x requirement | develop implementation and regression |
| --- | --- |
| Source declaration order, aliases, nested groups | Shared XsdSchemaSource adapter; particle-model construction/import/reconstruction cases |
| Choices at their sequence position | Authoritative particle serialization; original Order/Mixed fixture |
| Choice-only flat document parts and root attributes | WSMessage field projection; new Only cases with both alternatives and attributes |
| Default required choice | Complete particle validation; original missing-choice negatives plus explicitly empty flat records |
| Extension/restriction exclusivity | Particle derivation; original Ext and new Restricted positive/negative cases |
| Provider and sample order | Original regression plus recursive before/after WSDL corpus snapshots |
| Avoid unnecessary hash rewriting and regex helpers | Reference traversal, conditional suffix merging and string prefix/position operations |
| Standalone, external and main WSDL parsing | Shared adapter; both inline/imported new schema and SOAP tests |
| Customer nested Create/MOAttributes request | New ENUM provisioning case retains msisdn before records and all six record values |

The expanded test has three cases and 284 assertions. It checks actual SOAP
1.1/1.2 bindings in both directions, inline/imported schemas and reconstructed
services, native value/key order, standalone schema values, independent native
schema validation and rejected missing/duplicate choices. The source passes
AST, IR, JIT and tiered execution; the explicitly loaded rebuilt AOT module passes.
The original SOAP suite also passes under AOT.

The broad gate passes 128 suites / 1,278 cases / 63,629 reported assertions.
Three historical comparator-negative assertions in soap.qtest are intentionally
caught; all test cases pass. Thirteen supplements pass, including the 1,000-model
independent finite-language matrix (15,132 rows), particle construction and the
survey harness. qdx and Doxygen complete without warnings.

Before/after normalization produces byte-identical trees for 67 WSDL/XSD files;
one intentionally malformed Imported.xsd retains its parse rejection. The 35-WSDL
snapshot is byte-identical, with 131 operation/direction entries across 29 parsed
files. Six descriptions still fail before operation snapshots: enterprise/partner
whitespace defects described below, the existing issue-4449 import mismatch, two
CXF HTTP/XML binding parse failures, and CXF swa-mime ambiguous part declarations.
Those are recorded failures, not successful report/provider comparisons.
`element-order-snapshot.qr` emits reports, samples, ordered recursive provider
metadata and explicit errors. For example:

```sh
qore -b --enable-debug test/wsdl-interop/element-order-snapshot.qr test/element-order.wsdl
```

A paired local normalization check used the deployed Release Qore `0eb8abb81`
and the XML Release build (both caches verified). Twenty alternating measured
pairs after warmup on enterprise.wsdl have medians 202,963.5 us before and
180,312 us after, about 11% less for parse-plus-normalize in this measurement.
This is not a complete WebService construction benchmark. Exact worker sources,
fixture hashes, timings and binary hashes are in the inventory.

Both-version survey and strict coverage outcomes are unchanged from P5-12; only
runtime/module metadata changes to the deployed Qore and ported WSDL. There are 2,455 survey
rows, zero selected failures across 144 WSDLs / 1,388 directions, and 60 broader
failures. P5-P9 remain open.

## Independent schema-whitespace finding and next increment

The snapshot exposed pre-existing declaration parsers interpreting whitespace-only
`^value^` metadata as a child declaration. Minimal valid examples are
`<xs:restriction base="xs:string"> \n </xs:restriction>` inside a simpleType and
`<xs:complexType name="Value"> \n </xs:complexType>`. Native schema validation accepts
both; WSDL raises XSD-SIMPLETYPE-ERROR / XSD-COMPLEXTYPE-ERROR. They reproduce
enterprise.wsdl and partner.wsdl failures before this port, and before/after
normalization trees remain identical. The next XML increment will apply schema
character-content rules at the declaration boundary, with significant-text
negatives and retained annotation content, then recheck both full descriptions.
This independent finding is routed explicitly under the execution prompt rather
than weakening this port's regression checks.

The separately investigated allocation assertion is a test error: allocation 19
recreates a dictionary after validation. ROOT-CAUSE.md and phase-specific
reproducers are under /tmp/wsdl-native-allocation-investigation/. Correct the
fault-injection assertions in P5-13 after this port and before committing the
native wildcard change. No module-xml production allocation fix is indicated;
the upstream context-reuse observation is unreachable through per-call contexts.
