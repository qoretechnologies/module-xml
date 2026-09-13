# P5-17a native ID/IDREF bindings

Copyright (C) 2026 Qore Technologies, s.r.o.

Parent `6a41ffc`; native prerequisite for P5. This increment does not implement
WSDL document identity constraints and does not claim phase acceptance.

## Requirement and root cause

[XSD 1.0 cvc-id](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-id)
requires each token to identify exactly one element in the validation root.
Section 3.15.5 defines the table: ID attributes identify their owner and ID-valued
children identify their parent. Repeated values for the same owner are allowed.
A root ID value has no in-scope parent; an ID attribute can supply its binding.
The Working Group explicitly confirms this distinction in
[issue 9922](https://www.w3.org/Bugs/Public/show_bug.cgi?id=9922).
Selected IDREF list items and defaulted attributes also contribute references.

libxml2 2.15.4 left root ID/IDREF closure as an unimplemented validator TODO.
Its primitive datatype converter also registered attribute IDs during union
member trials before checking facets, while element IDs were absent from the
DOM registry. That registry cannot represent validation-subtree scope or recycled
SAX owners. The fix collects selected computed values in a context-owned table
and checks bindings after traversal. It preserves existing DOM ID lookup and
per-item reference type metadata after successful selection. See the
[implemented design](../../design/native-id-bindings.md).

## Independent adjudication

The committed fixture contains 21 schemas and 68 documents. Pinned Xerces-J
2.12.2 compiles every schema without warnings and agrees on 58 documents. The ten
differences below are enforced explicitly by `test_native_id_bindings.py`; no
fixture or native expectation is changed to obtain agreement.

| Case | XSD/native expectation | Xerces verdict |
| --- | --- | --- |
| `IDREF/elements/duplicate` | valid | invalid |
| `IDREFS/elements/duplicate` | valid | invalid |
| `default-IDREF/missing` | invalid | valid |
| `default-IDREFS/missing` | invalid | valid |
| `root-id-with-attribute/bound` | valid | invalid |
| `root-id-with-attribute/unbound` | invalid | valid |
| `root-id-with-attribute/unbound-reference` | invalid | valid |
| `root-id/unbound` | invalid | valid |
| `siblings/attribute-and-child` | valid | invalid |
| `siblings/same-parent` | valid | invalid |

The parent/root cases follow the explicit owner definition and WG resolution.
The two default cases require references contributed by absent defaulted
attributes; Xerces accepts them without a binding. Original W3C corpus bytes,
selection, catalogs and historical findings remain untouched.

## Verification

The configure probe exercises the 68 documents through DOM, context reuse,
reader and SAX paths, plus four subtree-scope cases, four nil cases and two DOM
metadata cases. It rejects an otherwise corrected provider missing only this
fix; AUTO falls back and SYSTEM rejects. Hash and timestamp checks cover
reconfiguration, and source-distribution tests include the new CMake inputs.

The new Qore suite passes 2 cases / 275 assertions, including exact unchanged
converted values, validation twice on the same DOM, rejection categories,
1,000 forward references, missing references, early reader destruction and
recovery. AST, IR and JIT runs independently check the fixture and Xerces
adjudication. The allocation executable sweeps 1,347 failure positions through
both the public validator and an equivalent path marking validation phases.
Required allocation failures reject and release their state. The existing
optional dictionary allocation during post-verdict context reset leaves the
completed verdict unchanged; the test identifies that phase and checks the
cleared dictionary explicitly. It does not misclassify optional reset allocation
as a successful validation after a required allocation failure.

The full pre-review run passes 147 Qore suites (1,389 cases / 68,197 reported
assertions). After review restored the existing DOM reference marker, all 21
native suites were rerun, along with AST/IR/JIT and Valgrind. This final native
binary has zero Qore Valgrind errors or lost blocks. Provider, standalone
allocation/probe Valgrind and corpus results are recorded in the
[validation inventory](P5-17a-validation.json).

Both complete corpus modes retain their previous rows and case objects:
2,461 survey rows and 293 cases in each mode, 144 strict selected WSDLs / 1,388
directions passing. Legacy mode still has four valid serialization failures and
20 broader failures. Explicit type preservation has 16 broader failures, all
invalid IDREF/IDREFS acceptances in the WSDL layer. These failures remain visible
and required P5 work; P6's separately tracked binding-version failures remain.

Evidence resides in `/tmp/wsdl-p5-17-identities/`; final reruns are in `final/`.
An intermediate provider/corpus run exhausted the user tmpfs quota. Its logs
are retained as `quota-*`; superseded test builds were removed with the
preauthorized guarded helper and the interrupted checks rerun. Those interrupted
runs are not acceptance evidence. No install, push or main-Qore mutation.
