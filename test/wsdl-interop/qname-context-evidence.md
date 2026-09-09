# QName instance and provider integration evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

This P3 increment integrates instance QName identity with the explicit value API,
schema facets, detached providers, SOAP bindings and standalone XML output.
It does not complete P3 or the P5 prefix-remapping requirements.

## Requirements and root causes

[XSD 1.0 QName](https://www.w3.org/TR/xmlschema-2/#QName) defines value identity
as namespace URI and local name. The containing element's namespace context
resolves lexical prefixes; declaration registries cannot replace that context.
[Namespace scoping](https://www.w3.org/TR/1999/REC-xml-names-19990114/#scoping)
includes ancestor bindings, local shadowing and empty default resets.
[Union member selection](https://www.w3.org/TR/xmlschema-2/#dt-union) depends on
the first accepting member, so adding a previously absent binding can change
a string value into a QName even when the output remains schema-valid.

The integrated fixes address these distinct losses:

- Instance namespace maps were discarded before QName conversion. Per-thread
  scopes now cover SOAP containers, records, simple content, scalars and lists.
- QName enumeration/default/fixed literals lost declaration bindings; alias
  comparison and provider field choices now use expanded identity.
- String alternatives selected after a QName rejection lost the namespace
  context that selected them. Immutable `XsdScopedLexicalValue` retains it.
- Ambient provider/serialization overrides affected independent callbacks.
  Providers receive explicit context only for the intended member; serialization
  and output-retention scopes additionally identify their namespace registry.
- List-item trial caches and patterned unions dropped retained item values.
  QName-capable collections keep QName/scoped items, including stable empty lists.
  Other patterned unions preserve their established string contract.
- Union example generation iterated raw enumeration keys. Samples now retain
  declaration context through native and retained-XML generation.
- Embedding retained XML could add an ancestor binding that changed its union
  selection. Validated native requirements now inform envelope allocation while
  retaining the original XML text.
- Standalone QName lists discarded bindings during union identity checks and
  could bind a prefix another item needed unbound. Identity checks retain the
  converted declarations; conflicting item requirements raise a serialization
  error. P5 still owns remapping compatible native values with colliding spellings.
- Output traversal copied all inherited bindings at each depth. Input/output
  maps now restore node-local changes; forbidden-prefix filtering visits only
  the current node's declarations.
- List serialization constructed detached item providers merely to identify
  QName item types. It now reads the resolved schema kind without allocating
  the provider graph. The same 296 diagnostic outcomes match before/after.

The public contracts and runnable examples are in
[the QName design](../../design/wsdl-qname-values.md). Errors and cancellation
restore outer state. Field metadata is configured before concurrent use;
immutable values and per-conversion maps are safe to share/use across threads.

## Independent matrix

`test_qname_context.py` defines eleven schemas and twenty-two actual SOAP binding
contracts. The scoped matrix has 216 inputs, 188 valid; the ordered fallback
matrix has 80 inputs, 48 valid. Both directions and original/reconstructed services
exercise seven consumers: native, element provider, reconstructed element provider,
message provider, reconstructed message provider, retained XML and reconstructed
retained XML. Native and retained-XML sample generation add 176 output cases.

The passing final inventory is 4,072 worker outcomes and 3,776 documents:
296 inputs plus 3,480 outputs. Every document is checked by pinned Xerces-J and
six native libxml2 paths: parse, reader, cursor, grouped cursor, attached schema
text and attached schema file. Exact URI/local values, list order, child names,
unbound-prefix requirements and unchanged retained XML are checked separately.
Missing, duplicate or unexpected rows cannot improve the result. Scoped workers
are partitioned by schema shape, each retaining both bindings, all inputs and
reused providers, so matrix growth does not multiply work under one deadline.

Pinned Xerces-J 2.12.2 emits one schema warning for the restricted-list fixture:

```
FacetsContradict: For simpleType definition 'StringOnly', the enumeration value 'ns:Product' contradicts with value of 'length' facet.
```

The exact diagnostic is asserted; all document verdicts remain mandatory.
`XSDAbstractTraverser.checkEnumerationAndLengthInconsistency()` uses Java string
length in its final branch for this enumeration. [XSD 1.0 list length](https://www.w3.org/TR/xmlschema-2/#rf-length)
counts items, and the literal contains one item. The original Xerces source archive
is [xercesImpl-2.12.2-sources.jar](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar),
SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
No production validation or test document is weakened or rewritten.

## Regression and corpus gate

The focused qtests cover malformed Serializable state, finite-choice aliases,
failed updates, optional/default/repeated values, 600 inherited provider levels,
128-level sibling XML trees, custom callbacks, actual thread cancellation, and
real local HTTP client/server exchanges with distinct request/response values.
All 21 focused cases / 1,467 assertions pass in each of AST, IR, JIT and tiered
modes. The final 89-suite XML gate passes 929 cases / 35,144 reported assertions
without warnings or failures. A Debug diagnostic of one
patterned-list contract took 79.26 seconds in AST and 69.44 in JIT before the
provider-allocation fix, with identical rows; AST took 48.45 seconds afterward
with the same rows. These are test-runtime observations under concurrent load,
not Release performance benchmarks. The earlier all-scoped worker exceeded its
300-second deadline; that failure remains in its log and prompted bounded
partitioning by schema shape.

The strict corpus selection adds `QNameElement` and `QNameAttribute`: 122 WSDLs,
1,156 message directions, including eight new expanded-name checks. The coverage
checker independently resolves each QName in its containing element. Mutation
tests reject changed namespaces/local names, unbound prefixes, ambiguous paths,
URI case/escape changes and malformed text, while accepting aliases/default resets.

Relative to P3-38, raw output rejections fall from 46 to 42, and independently valid
inputs producing invalid outputs fall from eight to four. Bidirectional coverage
removes exactly eight QName output-schema failures, retaining 160 broader failure
signatures and no newly introduced signature. Selected failures, missing stages,
skipped stages and failed exact-value checks are zero. The existing two P6
selected-binding-version unit assertions remain failing and tracked separately.

Final test results, source/artifact hashes and the complete 62-item audit are
recorded in [EXECUTION.md](EXECUTION.md) and [the audit](audits/P3-39-qname-context.md)
(20 Pass / 42 N/A / 0 Fail). The two context methods pass in 306.276 seconds.
The final WSDL SHA-256 is `46bd191122fb85d5d5c2160fb0e63dacd0bc122ab1868a09370dbccc27e44091`;
the generated fixture inventory SHA-256 is
`a51d5d278a0c2d6c47b2b37bd77451b841f756c71c4bb0a54eaf0b0b2eaae68b`.
No C++ changes require a new Valgrind run, and no core installation or push is part
of this increment. DateTime/time policy, ENTITY/ENTITIES and remaining P3 criteria,
followed by all P4–P9 requirements, remain in scope.
