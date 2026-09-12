# P5-13 native wildcard instance types and schema whitespace

Copyright (C) 2026 Qore Technologies, s.r.o.

The native prerequisite follows element-order port `5c283bf`. It corrects the
strict wildcard's early missing-declaration rejection, libxml2's treatment of
CDATA declaration whitespace, and Qore's interpretation of declaration text.
The allocation investigation requires a test correction, with no production
allocation change. [Implemented behavior and normative references](../../design/native-wildcard-types.md)
cover the native rules; [the source adapter design](../../design/wsdl-particles.md#character-content-in-schema-declarations)
covers Qore's component-construction view.

## Root causes and corrections

`xmlSchemaValidateElemWildcard()` rejected an unknown strict element before
looking at its `xsi:type`. Moving that rejection after existing instance-type
assessment permits XSD 1.0 cvc-assess-elt clause 1.2 while retaining declaration
precedence, namespace admission and selected-type validation. An unresolved type,
invalid value/content/attribute, abstract type or forbidden namespace still fails.
`skip` retains its subtree semantics. The earlier failing finding remains in
[p5-native-wildcard-type-finding.md](p5-native-wildcard-type-finding.md).

`xmlSchemaCleanupDoc()` removed blank XML text but explicitly retained CDATA,
which then became an unexpected declaration child. Its blank-node predicate now
includes CDATA. Complete `documentation` and `appinfo` subtrees are excluded from
cleanup, preserving character data, child markup, comments and processing
instructions. The former xml:space guard was ineffective because
`xmlNodeGetSpacePreserve()` returns -1 for text nodes; removing it does not change
text-node behavior in pinned 2.15.4. Tests also cover xml:space='preserve'.

The Qore source adapter treated whitespace-only scalar declarations and `^value^`
metadata as component content. It now validates and removes declaration whitespace
from the construction view, propagating namespace-aware schema/annotation scope.
Significant text rejects; original source remains available for reconstruction
and native validation. Grammar checks retain their existing facet/restriction
error categories. Complex-type documentation now ignores namespace/attribute
metadata when selecting its single documentation payload. Both original
enterprise.wsdl and partner.wsdl parse successfully; neither source was changed.

The private native source passes through these checked SHA-256 stages:

| Stage | SHA-256 |
| --- | --- |
| Previous wildcard-ID correction | `3a78da4283035b2691688766e2bd6dda205a14cf36ce8430af3ec03677d2e80f` |
| Wildcard instance-type correction | `75e468136eaa0dbf8c95071194d41937d6da6f188ee799a47cf50902a98ad65b` |
| Declaration whitespace correction | `a3db543b225021533cf966759c304f7a955ef85b1b645c1828334413b61b7004` |

The archive remains pinned at libxml2 2.15.4 with SHA-256
`98087fd181d9070724f3fbc65c7377db03038eb92bd882374daff44940138821`.
Only build-tree copies are modified. Both complete probe behaviors are mandatory
for a system candidate; AUTO falls back and SYSTEM rejects a partial backport.
All 43 provider tests pass, including offline builds, fixed/broken shared fixtures,
old-version backports, reconfiguration timestamps, distribution and cleanup.

## Allocation investigation

The separate `/tmp/wsdl-native-allocation-investigation/ROOT-CAUSE.md` proves
allocation 19 happens during dictionary recreation after a successful validation.
The original assertion that every allocation failure must invalidate the document
was incorrect. Plain integer validation has the same optional final allocation;
the wildcard correction is unrelated to its existence.

The committed harness classifies the first failure as preparation, walk or reset.
Required failures must report errors. A reset failure must preserve the already
computed verdict and leave the dictionary null. Each fault is repeated through
`xmlSchemaValidateDoc()`, requiring matching verdicts/allocation counts. All six
valid/invalid document shapes restore live allocation baselines and recover using
a fresh context. There are 131 fault positions per API: 125 required and six
optional reset failures. Valgrind reports zero errors and all 16,434 heap blocks
freed. The provider suite also runs this test.

The separately observed false rejection when reusing a context after reset
allocation failure remains an upstream follow-up. Module-xml constructs and
frees its context per validation call. Revisit that finding before introducing
context reuse; it does not block this prerequisite or remaining WSDL content work.
The investigation and its integration note are hashed in the validation inventory.

## Validation

- `xml-wildcard-types.qtest`: three cases/321 assertions, with DOM, parsed XML and
  readers, selected builtin/restricted/complex types, rejection/recovery,
  interruption and concurrent readers.
- `test_native_wildcard_types.py`: 36 schemas/684 documents/1,368 native paths,
  including 418 invalid documents and six namespace constraints. Xerces-J 2.12.2
  matches every normative verdict. Pinned lxml/libxml2 2.12.10 incorrectly rejects
  32 valid strict instance-type cases; those disagreements are asserted explicitly.
- `wsdl-schema-whitespace.qtest`: five cases/85 assertions, including providers,
  empty and constrained types, saved schemas, imports, annotations and original
  enterprise/partner descriptions. The independent matrix checks 96 schemas in
  memory/native and Qore construction/reconstruction paths. lxml's default parse
  normalizes CDATA; Xerces consumes the original spelling. The native probe also
  checks raw CDATA through both memory and pre-parsed DOM schema constructors.
- Full regression gate: 130 suites/1,286 cases/64,035 reported assertions, with no
  warnings or failed cases. The three historical caught comparator negatives in
  soap.qtest remain unchanged.
- All 27 supplements pass: both new units in AST/IR/JIT/tiered modes, six AOT
  schema/SOAP/provider/HTTP suites, four existing independent/harness suites,
  both new matrices in four modes and the whitespace matrix using WSDL.qmod.
- Native wildcard, complete configure probe, whitespace unit and three wildcard
  consumer/HTTP/registry suites pass Valgrind with zero errors/lost blocks. The
  fault-injection test separately has zero errors and no remaining heap blocks.
- WSDL and native qdx/Doxygen processing is clean; the documented shipment example
  executes and preserves its value. Build type is Debug, prefix /usr, using the
  deployed Qore 0eb8abb81 and the local XML module; no installation was made.

The first temporary AOT HTTP copy used an unresolved relative import. Its
staging script now expands all local module imports; the corrected test passes.
The first Valgrind launcher pointed to a shell wrapper and lacked a Memcheck
summary; the verified runs invoke /usr/bin/qore directly. Neither incomplete run
is counted as memory evidence. Their diagnostic artifacts remain under /tmp.

Both-version corpus outcomes are unchanged: 2,455 survey rows, 144 strict-selected
WSDLs/1,388 directions, zero selected failures and 60 broader failures. Only
runtime/source version metadata changes in the current reports. Original fixtures,
source adjudications and historical findings remain intact. All 62 audit checks
are resolved in [the audit](audits/P5-13-native-wildcard-types.md), with commands,
logs, input hashes and results in [P5-13-validation.json](P5-13-validation.json).

P5 still requires element wildcard value processing, mixed/generic content,
complete nil/default/fixed semantics and document identity constraints. P6-P9
binding/protocol/attachment and CI acceptance remain required. Local native probes
and qtests run during existing CI builds; mandatory Python matrices and supported
Ubuntu/Alpine execution remain P9 requirements. No push or complete-conformance
claim is included in this increment. Both origins were fetched with no incoming
develop commit; concurrent main-Qore work is outside this XML change.
