# XSD repetition counts and structural matching

Copyright (C) 2026 Qore Technologies, s.r.o.

The baseline at 9b7ebe4 rejects valid XSD patterns `a{65536}`,
`(ab){32768}` and `a{0,999999999999999999999999}` when constructing a schema.
The reduced probe and initial eight-case regression are retained under
`/tmp/wsdl-p3-19-repetition-` and `/tmp/wsdl-p3-19-unit-baseline.log`.
Six cases fail at schema construction; leading-zero and reversed-bound cases
already behave correctly.

[XSD 1.0 Part 2 Appendix F](https://www.w3.org/TR/xmlschema-2/#regexs)
defines quantity bounds as decimal digit sequences with an ordered minimum
and maximum. It does not impose PCRE's 65535 limit. The
[PCRE2 limits documentation](https://www.pcre.org/current/doc/html/pcre2limits.html)
and [repetition documentation](https://www.pcre.org/current/doc/html/pcre2pattern.html#SEC17)
explain the bounded quantifier field and compiled-code expansion for repeated
groups. These failures occur before JIT execution. Disabling JIT or raising the
link size does not supply arbitrary XSD counts.

WSDL now validates XSD grammar, retains normal anchored PCRE strings, and uses
`XsdCompiledPattern` when the backend cannot compile a valid expression.
The source-only Serializable object rebuilds immutable postorder nodes.
Repetition counts remain decimal strings; input-derived width bounds precede
native conversion. Nullable repetitions can pad their minimum with empty
matches. Nonnullable variable-width repetitions retain attainable count/offset
states rather than approximating them with a continuous interval. All match
state is local, and iterative loops observe Qore cancellation.

The direct differential matrix contains 66 expression trees and every string
over `a`/`b` of length zero through six. Original and reconstructed structural
objects must agree with Python `re.fullmatch`: 16,764 results. Another 24 XSD
Unicode/class definitions exercise the structural object directly for 292
results, including cases normally handled by PCRE. Malformed grammar, 2000-level
groups and subtraction, long multibyte literals, nullable counts, metadata
corruption, all affected provider families, concurrent reuse and cancellation
recovery are covered by `test/wsdl-regex-counts.qtest`.

The actual-binding matrix defines eight datatype restrictions, 24 schemas and
48 separate SOAP 1.1/1.2 contracts. Request/response paths check 384 original
input documents and 168 emitted documents. Reconstructed element/message
providers produce 2,432 result rows, including rejection and example outcomes;
1,136 accepted provider/example documents are independently checked. The matrix
requires exact lexical strings and correct error categories, including original
65,536-character values. No source fixture or production result is rewritten.

## Independent implementation limits

Both lxml/libxml2 2.12.10 and Xerces-J 2.12.2 reject the six authored expressions
with 24-digit bounds. The original schema verdicts remain mandatory in the
matrix. Xerces document outcomes remain explicitly `unreachable`, with their
schema-compilation cause; they are never counted as document-validation passes.
The large but native-range literal/group counts are checked against both
validators using their original schemas and payloads.

libxml2's `xmlFAParseQuantExact()` accumulates into `int` and rejects overflow.
This is present in both inspected source versions:

- [libxml2 2.12.10 xmlregexp.c](https://raw.githubusercontent.com/GNOME/libxml2/v2.12.10/xmlregexp.c),
  SHA-256 `130bc6a62d3f01c67d8b2bf302932391a20f236a73f8c31e1f37cd5d87df06de`.
- [libxml2 2.15.4 xmlregexp.c](https://raw.githubusercontent.com/GNOME/libxml2/v2.15.4/xmlregexp.c),
  SHA-256 `3b2ba46567d52d898864b9c3b7478066c25720cbb9ad69f5961f6b329cd64aaf`.

Xerces `RegexParser.parseFactor()` also accumulates bounds into Java `int` and
reports quantity overflow when the accumulator becomes negative. Its
`RegularExpression.compile()` closure branch expands exact and finite maximum
counts into repeated operation objects. A separate diagnostic at
`a{0,2147483647}` exhausts the pinned worker's 256 MB heap before a document
verdict; its stdout and exact Java stack remain in
`/tmp/wsdl-p3-19-oracle-{stdout,stderr}.log`. That incomplete diagnostic is not
acceptance evidence. The completed matrix uses overflowing 24-digit counts
whose explicit schema rejection is deterministic, together with the bounded
reference documents below. It does not treat worker failure as a schema verdict.

The inspected files come from the pinned
[Xerces 2.12.2 source JAR](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar),
SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
`RegexParser.java` has SHA-256
`1e176ed434cb441ff3c42a45ff1cd1b3c6763eddcfa00985b504509d2ec5e09a`;
`RegularExpression.java` has SHA-256
`98af70872570c639290af469f1be713e58b7433bc0fefb7414a3bd92b446c0a4`.
No native library, JAR or upstream source is modified in this increment.

## Separately identified bounded references

For the six overflow families, every original input/output document is also
checked by both validators against a separately named schema. Replacement
must occur exactly once; payload bytes are unchanged. The test explicitly
asserts a maximum of 16 Unicode characters for every supplied scalar text and
attribute value before relying on this comparison. These schemas preserve
membership for that bounded domain, not the complete languages.

Let `N` be the original 24-digit bound:

| Original pattern | Reference pattern | Why membership agrees through length 16 |
| --- | --- | --- |
| `a{0,N}` | `a{0,16}` | A successful iteration consumes one character. |
| `(a?){N}` | `a{0,16}` | Empty iterations can pad any count through 16 up to N. |
| `(){N}` | `()` | Both accept only the empty string. |
| `a{N}` | `a{17}` | Neither accepts a string of length at most 16. |
| `((a\|b){2}){0,N}` | `((a\|b){2}){0,8}` | Each outer iteration consumes exactly two characters. |
| `(Α\|中\|𐀀){1,N}` | `(Α\|中\|𐀀){1,16}` | Each iteration consumes one Unicode character. |

The two test methods add 18 reference schemas each and 1,464 document
assessments in total. Every reference document must have the expected verdict
in both validators. Exact Qore input/output assertions still apply to the
original large-count expressions. No `unreachable` result is substituted for
these mandatory checks.

## Implementation findings resolved before the commit gate

The exhaustive matrix caught Qore `split()` dropping the trailing empty field
in `{n,}`; parsing now retains the comma explicitly. The first large SOAP matrix
exceeded its existing 60/90-second worker deadlines. Root repeated literals now
compare bounded UTF-8 byte segments after exact count validation; flat predicate
groups avoid per-character frame/cache allocation. Deadlines and matrix coverage
are unchanged. Cancellation testing caught the initial whole-string fast path
having no loop cancellation point; bounded segment comparison restores it,
including the accepted empty input. Grammar parsing now indexes Unicode code
points once instead of repeatedly scanning prefixes. A sample test expectation
was corrected because the Unicode alternative can produce the valid `Α` example.

The final execution and full 62-item audit are recorded in EXECUTION.md and
`audits/P3-19-regex-counts.md`. Passing these repetition checks does not establish
P3 acceptance: remaining regex execution, primitive/date/IEEE/binary/QName/
entity/XML-RPC work and P4-P9 requirements retain their scope.

Accounting correction during P3-20 review: the binding harness emits one
repeated payload per value, whereas consumer variants also test two list sizes.
An instrumented run records 384 binding input and 168 binding output documents,
1136 consumer documents, and 456 + 1008 bounded-reference documents. The original
P3-19 record mistakenly used consumer variant multiplicity for binding counts.
The corrected figures above do not change test coverage or outcomes; exact
records are in `/tmp/wsdl-p3-20-repetition-accounting.json`.
