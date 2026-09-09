# XSD pattern execution evidence (P3-20)

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment addresses whole-value pattern matching when backtracking engines
exhaust their execution budgets. It does not complete P3 or later phases.

## Requirement and root cause

[XSD 1.0 Part 2 Appendix F](https://www.w3.org/TR/xmlschema-2/#regexs) defines
patterns as languages, with alternation, concatenation and repetition. For
`(a|aa)+|a+b`, a run of `a` followed by `b` belongs to the second alternative.
The original implementation asks PCRE to match the entire translated expression.
At 100 and 1000 `a` characters, the first alternative exhausts the backend match
limit before the successful alternative is evaluated. Qore reports `REGEX-ERROR`
with PCRE2 error -47. `((a|aa)+b|a+c)` and `(a+)+b|a+c` have the same failure
for the appropriate valid suffix. At 10 characters the examples succeed.

The diagnostic probe and an unmodified P3-18 (`9b7ebe4`) module produce
byte-identical results in `/tmp/wsdl-p3-20-backtracking-{probe,baseline}.log`.
P3-19's counted matcher solved compilation limits but left ordinary expressions
on the same backend execution path. This is an existing defect, not a regression
from structural counts. [PCRE2 limits](https://www.pcre.org/current/doc/html/pcre2limits.html)
document resource limits separately from the expression's language.

New schema constraints now always retain the original source in
`XsdCompiledPattern`. Ordinary zero/one/unbounded closures use Thompson fragments
and state-set simulation; [Russ Cox's description](https://swtch.com/~rsc/regexp/regexp1.html)
explains why merging reachable states avoids enumerating backtracking paths.
The graph has two states per grammar node and never expands numeric quantities.
Epsilon closure uses explicit work lists, with visited-state deduplication.
Only transitions reached by the supplied input are cached, within that match.

Other counts retain the existing input-bounded endpoint matcher. After a
nonnullable repetition meets its minimum, an earlier visit to an offset leaves
at least as much maximum-count budget as a later visit. Before the minimum is
met, distinct count states remain necessary: `(a|aaa){2,3}` accepts lengths
2, 3, 4, 5, 6, 7 and 9, but not 8. Pure nested closures use the exact identities
`(L*)*=L*`, `(L+)+=L+`, `(L*)+=L*`, and `(L+)*=L*`. General bounded repeats are
not replaced by an interval of total lengths.

Original-source reconstruction rebuilds the program, and shared graphs are
immutable after construction. Cancellation and exceptions release per-call
state. Older serialized PCRE strings remain readable with their backend behavior;
they do not carry the original XSD source. `XsdRegexHelper::toPcre()` remains a
translation utility subject to PCRE's own limits.

## Independent validator execution limit

All original authored schemas compile in both pinned validators. Xerces-J
2.12.2 assesses every original document and must agree with the expected verdict,
without warnings. lxml 6.1.1 / libxml2 2.12.10 instead raises
`XMLSchemaValidateError` for 48 invalid binding documents: 12 in the alternatives
family, 24 in the branches family and 12 in the inherited-pattern family.
The diagnostic is `Internal error in XML Schema validation.`, with
`SCHEMAV_INTERNAL` entries including pattern-facet evaluation. These results are
explicitly unassessed, not invalid-input verdicts or passing oracle checks.

Both pinned libxml2 versions contain `MAX_PUSH = 10000000` and the
`xmlFARegExecSave()` guard setting `XML_REGEXP_INTERNAL_LIMIT` after that many
saved backtracking states. A direct `xmlRegexpCompile()` / `xmlRegexpExec()`
probe linked against the project's private libxml2 2.15.4 returns **-6**, the
named internal-limit code, for the same reduced inputs. A newer dependency does
not remove this guard. No validator source, JAR, limit or original document was
modified.

| Expression applied to 100 `a` characters | suffix `b` | suffix `c` | suffix `d` | no suffix |
| --- | --- | --- | --- | --- |
| `(a\|aa)+\|a+b` | 1 | -6 | -6 | 1 |
| `((a\|aa)+b\|a+c)` | 1 | 1 | -6 | -6 |
| `(a+)+b\|a+c` | 1 | 1 | 0 | 0 |

Here 1 means accepted, 0 means rejected, and -6 means no validity verdict.
The direct probe is `/tmp/wsdl-p3-20-libxml-probe.c` and its complete result is
`/tmp/wsdl-p3-20-libxml-native-results.log`. It compiles with the private source
and build include directories, `libxml2.a`, `-lm` and `-lz`.

The affected families receive separately identified `/equivalent` schema jobs,
with unchanged payload bytes. The replacement is globally language-equivalent:
`(a|aa)+ = a+`, because each repetition consumes one or two `a` characters and
single-character repetitions can produce every positive length. Therefore
`(a|aa)+|a+b` becomes `a+|a+b`, and `((a|aa)+b|a+c)` becomes `a+b|a+c`.
The inherited schema changes only its own pattern; the parent `a+b` is intact.
These are separate reference schemas, not modified fixtures or a production
special case. Both validators must assess every equivalent-schema document,
including rejected inputs and accepted provider/example documents. The original
Xerces verdict is still mandatory for each original document.

The test asserts exact schema/document identities, replacement multiplicity,
empty warning lists, error category and the exact affected lexical strings.
The recorded run has 48 unassessed original binding documents; correct verdicts
from a fixed validator remain accepted. Unaffected libxml2 verdicts remain mandatory. An unexpected
schema error, internal error in another family, missing result or invalid emitted
value fails the test.

## Tests and artifact identity

`../wsdl-regex-execution.qtest` has six cases / 348 assertions covering original
and reconstructed schemas/providers, positive and negative alternatives,
nullable closures, count holes, 10,000-character inputs, source preservation,
interruption/reuse and synchronized concurrent calls. The initial three-case
regression failed with two backend execution errors; the final six-case source
suite passes. The 10,000-character case initially exposed excessive endpoint
processing overhead; state-set execution passes the existing test deadlines.
No deadline was raised, and no C++ was changed.

`test_regex_execution.py` exercises 10 authored restrictions, 30 original
schemas and 60 actual SOAP 1.1/1.2 contracts, in both directions and through
reconstructed element/message providers and generated examples. Two additional
methods compare 60 expression languages against Python full matching over every
binary string of length zero through six, for original and reconstructed patterns:
15,240 exact verdicts. The existing count/Unicode tests remain required.


Actual job accounting (captured by `/tmp/wsdl-p3-20-execution-accounting.py`):

| Scope | Original schemas | Original documents | Equivalent schemas | Equivalent documents | Original libxml2 unassessed |
| --- | --- | --- | --- | --- | --- |
| Binding inputs and emitted outputs | 30 | 540 inputs + 264 outputs | 9 | 204 | 48 |
| Reconstructed providers and examples | 30 | 1888 emitted documents | 9 | 464 | 0 |

The provider worker returns 3360 rows, including required rejection rows. Every
row identity and expected category is checked. Repeated payload values are not
counted as separate documents. The combined methods check 2692 original documents
and 668 additional equivalent-schema documents; all original Xerces verdicts
remain required. All four final independent execution methods pass in 72.313 seconds.

The affected source regression gate passes 64 suites, 742 cases and 15319
assertions. SOAP intentionally tests three assertion failures inside passing
cases. AOT and WSDL documentation builds are clean. Both-version survey and
strict coverage match P3-19 outside version metadata: 89 selected WSDLs and 756
directions, zero selected failures, and 220 tracked broader failures. Complete
Python discovery completes 150 methods in 686.339 seconds with the same 33
tracked later-phase failures, zero errors and unchanged source/test hashes.
AOT execution passes all three regex suites (32 cases / 1812 assertions), and
four direct language methods check 32296 original/reconstructed verdicts.

Artifact SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| WSDL source | `767dc84affb55d4800155e443d927a078e7dac3ec7269faf64e497b40ec69274` |
| Qore execution test | `5b6fae4b9bd55188143c59c6e41684ceeacf7e8a2566bd754fcbb82a905cce95` |
| Python execution test | `b6358533c6f92a1d4a785d29c4a2d75a5fe86f7114bcedcbd3746c4186ab1c76` |
| Reduced native probe source | `7517e629e3b11a2cb8682f0bf0a7e0550bb44544b8fb0a297342df6f3bb7dd02` |
| libxml2 2.12.10 `xmlregexp.c` | `130bc6a62d3f01c67d8b2bf302932391a20f236a73f8c31e1f37cd5d87df06de` |
| libxml2 2.15.4 `xmlregexp.c` | `3b2ba46567d52d898864b9c3b7478066c25720cbb9ad69f5961f6b329cd64aaf` |

The original libxml2 sources are pinned at
[v2.12.10](https://raw.githubusercontent.com/GNOME/libxml2/v2.12.10/xmlregexp.c)
and [v2.15.4](https://raw.githubusercontent.com/GNOME/libxml2/v2.15.4/xmlregexp.c).
The private source is under `build-debug/_deps/qore_xml_libxml2-src`; its internal
error constants are in `include/private/regexp.h`.
Xerces remains the pinned offline 2.12.2 artifact described in the corpus README.

The portability audit tightened the recognized internal-error cases to their
exact payload strings and accepts correct original libxml2 verdicts when the
backend is fixed. It does not require an oracle to reproduce a historical defect.
The first frozen full run completed 150 methods in 682.036 seconds with the same
33 later-phase failure signatures and no errors; its unchanged source/test
snapshot is retained under `/tmp/wsdl-p3-20-pre-portability-frozen-*`.

Final verification uses the independently tested Qore fix `9dab82749`, which
initializes an empty string-to-float conversion result. It was found during the
next IEEE preflight, with an independent Valgrind reproducer and core audit;
no XML C++ source changed. The Debug runtime SHA-256 is
`c8b0739f796b93c0f056cbf2a37050d6902de45c3e9361ed3565754ac5549afb`.
The native XML module remains
`8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
Final logs use `/tmp/wsdl-p3-20-final-*`, `frozen-*`, `aot-runtime-final.log`,
`aot-tests.log`, `aot-final.log`, `docs-final.log` and
`execution-accounting-final.log` under the same prefix.
