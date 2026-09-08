# XSD regex character sets and grammar evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P3-18 covers grammar validation, character sets and bounded sample generation.
The authoritative grammar is [XSD 1.0 Part 2 Appendix F](https://www.w3.org/TR/xmlschema-2/#regexs).
Productions 1–10 define groups and quantifiers; 12–22 define nonempty character
groups, ranges and subtraction; 24–37 define escapes, categories and blocks.
The prose limits unescaped hyphens to the ends of a positive group. Subtraction
is applied to that group, so `[a--[a]]` denotes the singleton hyphen set. The
category grammar excludes `Cs`; block names require `Is`. `.` excludes CR/LF.
Word classes use Unicode categories, and name classes use the referenced XML
1.0 Second Edition productions. No PCRE extensions are imported implicitly.

The later [W3C block-name note](https://www.w3.org/TR/xsd-unicode-blocknames/)
explicitly distinguishes XSD block syntax from Unicode's general loose-matching
recommendation. It does not license arbitrary PCRE script/property syntax.
The existing block lookup remains available, after the XSD property grammar check.

## Production root causes and fixes

The old translator returned PCRE `\i`/`\c` for class-contained name complements,
passed block complements through untranslated, and retained ASCII `\D`, `\w`
and `\W` inside classes. It also omitted mandatory closing brackets, treated
unescaped `]` as a literal at class start, and passed PCRE-only syntax through.

The translator now parses XSD syntax and emits complete single-character terms.
Positive groups form unions; negative groups and nested subtraction preserve
set complement/difference semantics. Parent groups are assembled iteratively.
Quantifier bounds are compared exactly without native integer overflow. Sample
generation limits work before integer conversion, handles empty atoms directly,
and searches bounded candidates across intersecting restrictions. An audit
regression showed that this last search must be conditional on an actual pattern
facet; the no-pattern date/string/integer regression preserves supplied examples.

Initial six Qore cases fail on P3-17. Final source and AOT run twelve cases /
988 assertions, including schema/provider reconstruction, exact error kinds,
Unicode, escaped ranges, empty branches/groups, leading-zero counts, 40 nested
subtractions, 2000-level translation, large sample counts, cancellation/recovery,
and preservation of examples for types without patterns.

## Independent oracle adjudications

The original schemas are always supplied unchanged to Qore and both validators.
Qore must satisfy the normative input and exact-value assertions. The following
validator defects are explicitly recognized; correct verdicts from fixed libxml2
versions are accepted. No other disagreement is permitted.

| Expression | Required behavior | Observed validator defect and root cause |
| --- | --- | --- |
| `[\P{IsGreek}]`, `[^\P{IsGreek}]` | Complement and double complement of the Greek block | libxml2 2.12.10 and 2.15.4 store `\P` negation on the atom, while the range matcher uses per-range negation. The verdict is reversed for nonempty one-character inputs. |
| `[a-z-[a-z-[aeiou]]]` | Vowels | Both libxml2 versions flatten nested subtraction into ranges with exclusion flag 2. The matcher excludes the whole inner alphabet and cannot restore vowels. |
| `[\--/]`, `[\[-\]]` | All code points between the escaped endpoints | 2.12.10 routes every escape directly to its class-escape parser, never the range parser; the intervening hyphen is dropped. 2.15.4 fixes escaped bracket ranges, but its raw-hyphen check also discards an escaped hyphen range start. |
| `[a--[a]]` | Hyphen only | libxml2 attempts a reversed `a`-to-`-` range. Xerces likewise attempts a range before recognizing the subtraction token and raises `parser.cc.8`. Neither recognizes the final literal hyphen of the positive group. |
| `[]` | Invalid: positive groups are nonempty | libxml2's character-group loop does not require any term before `]`. |
| `[a-b-c]`, `[\d-a]` | Invalid: a middle hyphen cannot be a standalone term | libxml2's range parser advances past the disallowed hyphen without reporting an error. |
| `a{2,1}` | Invalid: minimum exceeds maximum | libxml2 assigns both counts without comparing them. |
| `a}` | Invalid unescaped metacharacter | libxml2's ordinary-character predicate does not exclude braces. |
| `\p{Greek}`, `\p{Cs}` | Invalid category/block syntax | Xerces's generic property lookup registers raw block names and `Cs`; its schema-mode exclusion list does not remove these entries. |
| `\Qabc\E` | Invalid single-character escapes | Xerces's inherited `parseAtom()` default branch creates literal characters for unknown escapes. It accepts `QabcE`, rather than implementing PCRE quoting. |

The 32 invalid-schema cases retain exact Qore `XSD-SIMPLETYPE-ERROR` checks.
Xerces 2.12.2 accepts exactly the three expressions in the last two rows;
libxml2 2.12.10 accepts the five expressions in the four preceding rows.
The validators reject all other invalid-schema expressions in this matrix.

Six affected valid-schema families also have separately identified, set-equivalent
derivatives. Replacements are explicit in `test_regex_classes.py`: Greek block
complements become literal block ranges, double subtraction becomes `[aeiou]`,
hyphen subtraction becomes `[-]`, and escaped ranges become explicit sets.
Each replacement must occur exactly once. These additional jobs use distinct
identifiers and preserve every document byte. Both validators must give the
normative verdict on every derivative document. The original hyphen-subtraction
schema failures and unreachable Xerces documents remain asserted separately.

## Source provenance

Source inspection uses these unmodified upstream files:

- [libxml2 v2.12.10 xmlregexp.c](https://github.com/GNOME/libxml2/blob/v2.12.10/xmlregexp.c),
  SHA-256 `130bc6a62d3f01c67d8b2bf302932391a20f236a73f8c31e1f37cd5d87df06de`.
  Relevant functions are `xmlFAIsChar`, `xmlFAParseCharClassEsc`,
  `xmlFAParseCharRange`, `xmlFAParsePosCharGroup`, `xmlFAParseCharGroup`,
  `xmlFAParseQuantifier` and `xmlRegCheckCharacter`.
- [libxml2 v2.15.4 xmlregexp.c](https://github.com/GNOME/libxml2/blob/v2.15.4/xmlregexp.c),
  SHA-256 `3b2ba46567d52d898864b9c3b7478066c25720cbb9ad69f5961f6b329cd64aaf`.
  The private build's direct `XmlDoc::validateSchema()` reproducer confirms
  the retained defects and the changed escaped-range behavior, with empty stderr.
- [Xerces-J 2.12.2 source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar),
  SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
  `ParserForXMLSchema.parseCharacterClass()` contains the hyphen path;
  `RegexParser.parseAtom()` and `processBacksolidus_pP()` contain the escape paths;
  `Token.categoryNames`, block registration and `getRange()` explain property lookup.
  The binary remains pinned by `oracle/manifest.json`.

## Coverage and reproduction

Run `qore -b --enable-debug test/wsdl-regex-classes.qtest` and
`python3 test/wsdl-interop/test_regex_classes.py -v` using the local module paths
in README. The Python matrix covers 26 definitions, 78 original schemas,
156 actual SOAP contracts, 1872 inputs and 804 emitted binding documents,
11232 provider results and 5440 provider/example documents. It checks atomic
elements, simple content with attributes, repeated elements, both actual binding
versions, both directions, detached element/message providers and reconstruction.

There are 18 equivalent schemas and 1788 additional independent document
assessments: 588 binding documents and 1200 provider/example documents. Across
original and derivative jobs, there are 9904 document assessments; 172 original
hyphen-subtraction assessments remain explicitly unreachable in Xerces. All
those documents also receive mandatory normative checks through a derivative.
No unreachable assessment is counted as independent validation success.

Evidence is retained under `/tmp/wsdl-p3-18-`: initial reduced probes and baseline,
oracle-probe, native-oracle, independent-equivalent, final-unit-guarded,
exact-checks, aot-final-unit, docs-final, exact-survey/coverage and frozen-python.
Two earlier full Python runs were deliberately interrupted for audit fixes and
are not final verification. Source hashes and final acceptance results are
recorded in the audit and execution record.

This increment does not close P3. PCRE's finite count, bytecode-size and nesting
limits can still reject valid XSD patterns. Those backend limits remain required
P3 work, alongside the remaining primitive/date/IEEE/binary/QName/XML-RPC criteria.
