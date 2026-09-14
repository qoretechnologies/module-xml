# P5-20a native identity XPath prerequisite

Copyright (C) 2026 Qore Technologies, s.r.o.

Based on `7a59f8f`. The libxml2 2.15.4 `xmlPatternCompileSafe()` union loop
advanced past a terminal separator and exited without compiling another arm.
Thus `row|` and `row|other|` were accepted. Empty input independently returned
success with a null result. The correction rejects both forms using the existing
cleanup path; see [implemented design](../../design/native-identity-paths.md).

The authored [54-schema matrix](fixtures/identity-paths.json) has 22 valid and
32 invalid declarations. It covers selectors and fields, wildcard and qualified
names, explicit axes, dot steps, token whitespace, namespace failures, invalid
descendant positions, predicates and empty union arms. Each schema has an empty
document to isolate declaration validity. Three native APIs assert exact error
categories and unchanged DOM data; the focused suite has 195 assertions.

## Independent oracle spacing defect

Pinned Xerces-J 2.12.2 rejects the two otherwise valid selector/field cases with
` . // child::row / . `. Their explicit `xerces_schema_valid: false` records
describe oracle behavior; `schema_valid` remains true. No source is rewritten
to make its original assessment pass. XSD 1.0 Part 1
[§3.11.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#coss-identity-constraint)
allows XML whitespace around tokens, and separately names `.` and `//` tokens.

The [2.12.2 source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar)
has SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
In `org/apache/xerces/impl/xpath/XPath.java`, `Scanner.scanExpr()`'s
`CHARTYPE_PERIOD` branch handles following whitespace by accepting only end of
input or `|`. It throws `c-general-xpath` on the subsequent slash. The parser's
token-level period/double-slash handling would otherwise accept that sequence.
`XPath.java` SHA-256 is
`dc50370d643164396c67c6623876d89ef210813026603f262183d2a01a6a0886`.
Separate diagnostic derivatives `.//child::row/.` pass for both positions;
the original two fail, as expected. The source and eight-row comparison report
are retained under `/tmp/wsdl-p5-20-identities/xerces-source/`.

This increment fixes native declaration parsing only. WSDL currently discards
`key`, `unique` and `keyref` declarations except for reference-placement checks;
its declaration compiler, retained metadata and instance tuple semantics are
the next P5 work. Existing NOTATION identity/legacy-projection failures remain
failures. P5 typed accounting and all P6–P9 requirements remain open, including
Python CI wiring and supported-environment acceptance.

## Acceptance

The [inventory](P5-20a-validation.json) records source and log hashes. All 37
affected Qore suites, 68 provider tests and three Python supplements pass.
The focused direct ELF Valgrind run disables signals and PCRE2 JIT and reports
zero errors and zero lost bytes (117,480 bytes reachable). The direct C matrix
runs 88 checks in four pattern modes with/without a dictionary; its Valgrind
run frees all 486 allocations. Debug build and native documentation are clean.
All four diagnostic/strict corpus reports are byte-identical to P5-19g.
The [62-item audit](audits/P5-20a-native-identity-paths.md) has 18 Pass, 44 N/A
and zero Fail. Main Qore was not modified; nothing was installed or pushed.
