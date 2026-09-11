# Complete substitution roots: P5-09 evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

Implementation parent: `3e122cf`. Production changes are in `qlib/WSDL.qm`.
The [implemented contract](../../design/wsdl-substitution-roots.md) documents
the portable representation, component ownership and matching algorithm.

## Requirement and root causes

[XSD 1.0 Structures, second edition](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/)
defines element substitution eligibility using the head/member declarations,
type derivation and blocking constraints. P5-06/P5-07 established those sets.
Complete-element conversion still compared or emitted only the head name.
The reduced fixture declares abstract decimal `Container` and integer
`Quantity` affiliated with it; a document-style WSDL part refers to `Container`.
Valid `Quantity` content `017` failed native and retained decoding, retained
serialization, retained-provider validation and XML sample generation in both
actual SOAP bindings. The new unit fixture uses the equivalent
`head`/`quantity` declarations; the independent numeric fixture includes the
original decimal/integer relationship and lexical value.

The fix retains the selected declaration as `^element^` / `^val^`, with an
`XsdQNameValue` selector. Conversion resolves the member and uses its root,
type and instance constraints. Selected `xsi:type` remains an independent inner
wrapper. XML carriers already retain their selected root and stay unchanged.

[WSDL 1.1 sections 2.3 and 3.5](https://www.w3.org/TR/wsdl.html) leave
document-style part order undefined. Overlapping head/member parts therefore
need a complete, unique assignment by expanded names. Iterative augmenting
paths find an assignment; an alternating graph detects ambiguity. Native and
retained body/header paths share this rule. Duplicate roots cannot overwrite
another part during serialization.

Additional regressions exposed and fixed:

- Explicit `NOTHING` under part/message keys lost presence because lookup used
  `exists`; key-presence checks now retain the selected empty element.
- Reconstructed `WebService` objects replayed added schemas before rebuilding
  inline WSDL declarations. Replay now follows inline construction; successful
  additions also refresh message type maps. Failed additions preserve them.
- An existing provider read a live substitution set after schema additions,
  but its value providers still represented the old set. It now consistently
  snapshots alternatives, including after `Serializable` reconstruction.
- Header assignment must treat the first owner ID `"0"` as present even though
  that string is false in a boolean expression. Presence is checked explicitly.
- A SOAP 1.2 request without an action reached HTTP 501 because handler request
  names contained only the head. Registration now includes admitted document
  body members. Tests explicitly set `soapActionRequired="false"`, as permitted
  by the [SOAP 1.2 binding extension](https://www.w3.org/submissions/2006/SUBM-wsdl11soap12-20060405/).

## Executable evidence

| Area | Checks |
| --- | --- |
| Complete roots | `wsdl-substitution-roots.qtest`: 12 cases, 1357 assertions; native/retained schema and SOAP paths, both directions and actual versions, copies, providers, samples, empty/nil members, imported and no-namespace collisions, selected types, malformed selectors and member values |
| Part ownership | Same suite: broad/narrow body and header parts, missing/duplicate/ambiguous values, unknown part API errors, all 27 three-occurrence combinations, a 64-part overlap chain, cancellation and two concurrent readers |
| HTTP consumers | `wsdl-substitution-root-http.qtest`: 2 cases, 134 assertions and 10 exchanges through SoapClient/SoapHandler/SoapDataProvider; native root retention, optional type capture, saved providers, retained lexical `017`, and actionless SOAP 1.2 native/retained requests |
| Independent validators | `test_substitution_roots.py`: 34 schemas, 116 documents, 996 ordered result rows, 816 independently validated outputs and 44 samples per execution mode |
| Execution engines | Both new Qore suites and the independent matrix pass AST, IR, JIT, tiered and compiled WSDL; the compiled supplement also covers prior substitution/provider suites and Cargo/CDA consumers |
| Existing behavior | All 123 suites/1251 cases/62227 reported assertions in the acceptance inventory pass; the legacy SOAP suite includes three intentional caught comparator negatives; six qmods and WSDL documentation build without warnings |
| Corpus | Both-version diagnostic survey and strict selected coverage retain exactly the previous stage results; only the WSDL source fingerprint changes |

The independent matrix embeds each root inside an XSD witness referencing the
WSDL head. Merely validating a member as a standalone global element would
not establish its eligibility at that head. Both lxml and pinned Xerces
validate output; expanded names, QName-valued `xsi:type`, numeric values and
record fields are compared separately. Required normative negatives retain
the four existing supporting-validator block disagreements from P5-06.
The witness embeds complete serialized bytes so QName namespace bindings are
not discarded by an XML library's reparenting optimization.

Run the new tests with the local development runtime/module paths and debugging:

```sh
qore -b --enable-debug test/wsdl-substitution-roots.qtest
qore -b --enable-debug test/wsdl-substitution-root-http.qtest
python3 test/wsdl-interop/test_substitution_roots.py -v
```

[P5-09-validation.json](P5-09-validation.json) records each command result,
fixture/source/runtime SHA-256, source-mode matrix, compiled staging procedure,
corpus accounting and all 62 audit items. It embeds the four acceptance runner
scripts. The [audit](audits/P5-09-substitution-roots.md) records individual
Pass/N/A decisions. No C++ changed; native XML/libqore fingerprints match P5-08.

## Remaining acceptance

P5 remains open for wildcard, mixed/generic content, complete nil/default/fixed
and document identity semantics. P6–P9 retain their binding, protocol,
attachment, independent-peer, platform and mandatory-CI requirements. These
tests do not establish complete SOAP or WS-I conformance. The diagnostic
corpus still records 64 broader failures; selected coverage has no failures,
missing cases, skipped cases or typed-value failures.
