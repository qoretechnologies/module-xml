# Native counted attribution evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P4-05 closes the three attribution/component failures retained by P4-04. The
[12-schema matrix](P4-05-native-attribution.json) now passes all 24 DOM/reader rows.
The original diagnostics remain unchanged historical evidence. The implemented
[design](../../design/xml-particle-attribution.md) describes exact thresholds,
component ownership, abstract-name matching and counter execution.

The applicable requirements are [XSD 1.0 cos-nonambig](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-nonambig)
and [particle validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-particle).
The native automaton's old conflict check ignored feasible count contexts, so it
rejected `a{2}a` and `(b?a{2,3}){2}b`. Removing unreachable automaton states also
hid a duplicate-choice component after an empty-language sibling. The correction
checks every present component before automaton reduction, including unused named
groups. A zero maximum contributes no child component.

The checker uses the same independently tested exact weak-attribution analysis as
P4-03, with a memoized source DAG, sparse name/predicate sets and exact integer
ratios. It never expands a large count or rounds a threshold. Published summaries
are immutable; parent combinations own their sets. Synthetic inherited particles
retain their original occurrence source. Wildcard intersections use namespace
constraints; abstract declarations contribute only their usable substitution
members. Native transitions follow those same predicates, fixing a callback that
previously chose an abstract head instead of the admitted local declaration.
Required empty-language members make an all group empty; optional members and an
optional whole group remain distinct. Private summary assertions check that fact
independently of document validation.

Enabling the correctly accepted schemas exposed a second root cause in execution:
epsilon reduction overwrote nested counter increments, and copied guarded paths
could lose an increment. The finite oracle initially found 28 false acceptances in
three models. For example, `(b?{1,2}|a?){2}` must reject `aab`. Retaining schema
increment operations, carrying guarded increments and checking each upper bound
closes these failures. The counter changes are confined to schema automata.

Keeping epsilon operations initially allowed a large nullable minimum to enumerate
empty iterations until the native execution limit. The final executor uses zero
as a nullable term's effective minimum without modifying its source counts. It
also remembers which counters have advanced since the last input token; another
empty increment of the same counter cannot improve a match. Progress marks survive
counter resets, clear on consumed input and restore with rollback state. Positive
and negative billion-minimum examples complete without that iteration explosion.
These Debug timing diagnostics are not Release performance benchmarks.

Verification includes:

- `xml-particle-attribution.qtest`: eight cases / 157 assertions in AST, IR, JIT
  and tiered modes. It checks accepted/rejected schemas, exact declaration values,
  nested bounds, native count boundaries, inherited counts, abstract callbacks,
  empty all groups, nullable repetition and invalid-document error categories.
- `test_native_particle_attribution.py`: seed 4103, 1,000 complete finite models,
  765 accepted / 235 rejected. Every accepted language and its specified deletion,
  replacement and prefix/suffix mutations produce 41,630 DOM/reader document rows;
  schema rows bring the total to 43,630 per execution mode. Completeness, order,
  error categories, reader child counts and text values are asserted.
- `test_libxml2_provider.py`: 30 tests, including an 11-case attribution probe,
  incomplete backports, unchanged upstream sources, source-hash rejection,
  reconfiguration, offline fallback, cross-build handling and isolated installation.
  The math fixture checks 1,399 integer/ratio and invalid-input operations against
  Python integers/Fraction. Eleven summary boundaries include adjacent 80/81-digit
  thresholds, absent particles and present components inside empty languages;
  four malformed summary programs reject.
- Standalone allocation fixtures exhaust 134 arithmetic/set, 229 schema-checker
  and 15 executor fault points, verify baseline ownership after every failure,
  and successfully reuse fresh contexts. They also check empty all summaries.
- Valgrind passes the native Qore suite and all three standalone allocation
  fixtures with zero memory errors, zero definite/indirect/possible losses and
  zero suppressions. Standalone fixtures release all heap blocks. Qore retains
  116,230 bytes in 46 LLVM/loader process-lifetime blocks; its known isolated-core
  DWARF diagnostic remains P9-owned. Only Valgrind uses `QORE_PCRE2_NO_JIT=1`.

The [validation inventory](P4-05-validation.json) records the full affected gate,
source/runtime hashes and corpus comparisons. Both-version baseline and strict
coverage reports remain identical to P4-04: 2,411 baseline rows, 293 coverage cases,
144 recorded failures and no selected failures across 130 descriptions / 1,260
message directions. The survey harness, affected native documentation and the
executed fixed-boundary example pass. Native qtests run in the existing CI glob;
mandatory Python/dependency setup remains the explicit P9 deliverable. No CI run
or platform acceptance is inferred from local checks.

A separate P4-owned native count-range defect remains visible in
[P4-native-count-range-diagnostics.json](P4-native-count-range-diagnostics.json).
The lexical scanner saturates at `INT_MAX`, then rejects finite maxima above the
`UNBOUNDED` sentinel (`1 << 30`) before exact attribution runs. Eight schemas / 16
DOM-reader rows include a small positive control and 14 failing requirements,
including an ambiguous schema rejected for the wrong reason. Run
`native_particle_ranges.py --output REPORT.json` to reproduce the diagnostic.
This is not a supported-range decision or a passing conformance test; the defect
must close before P4 acceptance. The exact arithmetic helper's large-number tests
do not imply that the native parser already accepts those occurrence attributes.

Independent lxml 6.1.1/libxml2 2.12.10 and Xerces-J 2.12.2 remain unchanged. Their
previously documented count-attribution disagreements are still asserted; agreement
between independent validators does not override the specification. Ordered WSDL
message conversion, field metadata and sample generation also remain P4 work.
