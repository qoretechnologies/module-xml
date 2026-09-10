# P3-44: exact dateTime and time values

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment implements strict clock lexical validation, lossless conversion,
exact value facets and native output for `dateTime` and `time`. The implemented
contract is in [the design](../../design/wsdl-time-output.md). P3 phase acceptance
and P4-P9 remain separate gates; this report does not claim protocol compliance.

## Requirements and root causes

[XSD 1.0 Second Edition dateTime](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#dateTime),
[time](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#time), and
[Appendix D.1](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#isoformats)
define lexical fields, exact fractions, timezone uncertainty and leap seconds.
Patterns constrain text; enumeration and bounds constrain values. Daily clock
identity uses UTC canonical time, with a common arbitrary date for partial ordering.

The prior permissive `date()` path accepted malformed lexical input, assigned a
program timezone to unzoned XML and rounded fractions to native microseconds.
Native time output additionally truncated to milliseconds and omitted the zone.
The shared calendar helper now validates before choosing a native date or an
unchanged validated string. Year labels and fractional digits remain exact strings;
normalization adjusts whole minutes/days without floating-point conversion.
Midnight advances dateTime across month/year boundaries and skips year zero.

The user approved preserving timezone-equivalent leap seconds on 2026-09-10.
The [published Appendix E contradiction](https://lists.w3.org/Archives/Public/www-xml-schema-comments/2002AprJun/0043.html)
would otherwise equate a normalized leap second with the next midnight. Tests
preserve the leap value, offset aliases, inappropriate-date overflow, and missing
timezone distinctions. No historical leap table or rounding heuristic is used.

Two integration defects were fixed during review. Union reconstruction checked
supported builtin names but omitted provider/builtin consistency; it now checks
known providers, including boolean providers. The existing corrupted-dateTime
metadata regression and six additional corruptions reject correctly. Fraction
comparison originally relied on Qore string ordering, which deliberately sorts
empty strings last (`QoreString::compare`). An absent fraction represents zero;
the helper orders zero explicitly before nonzero decimal fractions. Boundary
tests exercise omitted/zero fractions in both operand positions and all bounds.

## Independent evidence and validator limitations

`temporal_reference.py` uses Gregorian ordinal days and Python rational fractions,
independently of the production field tuples and decimal-string carry algorithm.
`test_temporal_values.py` checks grammar, precision, timezone identity and facets
over actual SOAP 1.1/1.2 bindings, both directions, attributed simple content,
repeated elements, detached providers and generated examples. Fixed values,
lists/unions, metadata mutation and interruption/recovery also have Qore tests.

Four exact invalid long-fraction enumeration values are recorded in
`temporal-validator-defects.json`. Both libxml2 2.12.10 and private 2.15.4 store
`xmlSchemaValDate.sec` as `double`; pinned Xerces-J 2.12.2 stores
`AbstractDateTimeDV.DateTimeData.second` as `double`, verified with `javap`.
Both validators therefore accept these distinct decimal values as equal.
Every normative rejection and exact value assertion remains mandatory. The
binding matrix requires exactly 24 false positives per builtin per validator
on input, and zero discrepancies in emitted consumer/example documents. Native
`XmlReader` independently reproduces all four private-libxml2 false positives.

The authored Java oracle uses the JDK `XMLGregorianCalendar` decimal value API.
It checks 46 normative comparisons, including fraction distinctions, daily
aliases, midnight and 36 common-date partial-order comparisons. A 47th direct
time comparison records an API defect: `00:00:00Z` versus `00:00:00` returns less
instead of indeterminate on OpenJDK 25.0.4.1. In
[OpenJDK's implementation](https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.xml/share/classes/com/sun/org/apache/xerces/internal/jaxp/datatype/XMLGregorianCalendarImpl.java),
`compare` normalizes unknown-zone endpoints with `normalizeToTimezone`/`add`;
`add` removes originally undefined date fields, discarding midnight day carries.
Supplying the specification's common date preserves them. The exact discrepancy
is asserted separately from normative expectations, not accepted as conformance.

## Verification

All Qore invocations use `-b --enable-debug` and local module paths. No C++ changed
in this XML increment. The affected core UTC-offset prerequisite and upstream
JIT shutdown fix were separately tested and checked with Valgrind before this
gate. No native installation or push was performed.

| Gate | Result |
| --- | --- |
| Full affected Qore regression gate | 96 suites, 980 successful cases, 38,536 reported assertions; no warnings/errors |
| Temporal lexical/value suite | 9 cases / 1,578 assertions; AST, IR, JIT and tiered |
| Native and lossless local HTTP suite | 5 cases / 436 assertions; AST, IR, JIT and tiered |
| Union/list metadata regression | 10 cases / 231 assertions; AST, IR, JIT and tiered |
| Native independent matrix | 672 input/round-trip and 1,840 consumer/example documents |
| Exact temporal independent matrix | 1,296 input/round-trip and 3,072 consumer/example documents |
| Generated temporal boundaries | 718 cases, seed 20260910; fractions/years up to 1,000 digits, offsets, four bounds and enumeration |
| Independent Java value API | 46 normative comparisons and one separately adjudicated discrepancy |
| Native validator reductions | Four exact private-libxml2 false positives reproduced |
| Survey harness | 15 methods pass |
| Coverage harness | 15 methods; only the two previously recorded P6 SOAP 1.1 binding-version failures remain |
| Documentation | Doxygen and the executable design example pass without warnings/errors |

The full gate's `soap.qtest` retains its prior nested assertion accounting
(1,031 reported assertions / 1,028 successes, all 20 test cases successful).
No regression skip or expected-failure conversion was introduced.

The both-version survey retains all 2,411 rows and every prior count. Strict
selection expands from 126 WSDLs / 1,172 message directions to 130 / 1,260 by
adding all dateTime/time element and attribute examples. All 88 added message
directions have mandatory exact value checks. The selected gate has zero failures;
all 144 diagnostic failure identities and counts remain visible and unchanged.
Mutation tests reject precision, timezone, leap-second and list-item value loss.

Logs use `/tmp/wsdl-p3-44-temporal-` with suffixes `full-gate-reviewed`,
`fixed-modes`, `modes`, `independent-final`, `boundaries`, `native-reductions`,
`survey-tests`, `coverage-tests-final`, `survey`, `coverage-final`, `docs` and
`example`; the native matrix is `/tmp/wsdl-p3-44-time-output-independent-updated.log`.
The final source/artifact/log manifest is `/tmp/wsdl-p3-44-temporal-final-manifest.json`.

The runtime is the isolated Debug build in `/tmp/wsdl-core-date`, prefix `/usr`,
with local XML and WSDL paths. Its historical embedded Git hash does not describe
the dirty source snapshot; the refreshed native files match the integrated core
sources and are separately hashed in `/tmp/wsdl-p3-44-remote-core-final-manifest.json`.
Debug libqore SHA-256:
`71b856d6290cfbc2b87b26da5e069fd795f9c11b3784d2ac1695930628a821b3`.
Debug XML SHA-256:
`95ed6b98adc9c3171883c2c5d8e848431d1bf1720961faca8502ca54466e5824`.
Final WSDL SHA-256:
`a19f1f8b4ef3ab8c0ff70bb0a31d9bdadb5d13677b6b96f3d070a5ef8e99fed2`.

Parallel work subsequently rebased main Qore develop from integration merge
`537b61514` to `422e1ee14` atop remote `6aa122698`; the timezone fix and all seven
affected native files are preserved and the main working tree is clean. The
integration merge's eight test-header corrections and its audit are retained in
that historical commit, rather than the rebased tree. The isolated test snapshot
retains its audited local requirements. This XML increment does not overwrite
the parallel Qore history.

See [the complete 62-check audit](audits/P3-44-temporal-values.md).
