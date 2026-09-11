# Failed graph cleanup prerequisite evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P5-12 fixes the Qore core prerequisite in local develop commit `0eb8abb81`.
The [original failure and reproducer](p5-deserialization-cycle-finding.md) remain
available. XML implementation source and native qmod are unchanged from P5-11
(`99565bb`); the runtime includes the tested graph-cleanup correction.

An exception during a custom deserialization hook could leave self/mutual
references alive after the index dropped its own references. The index now
retains every target until incomplete objects are invalidated and their member
storage is detached. It then releases each index reference exactly once.
Incomplete indexed objects do not run user destructors; escaped references
report `OBJECT-ALREADY-DELETED`, and the original exception remains available.
Entry and post-hook cancellation checks use the same cleanup path.

`FailedObjectGraphs.qtest` checks six cases/94 assertions: self/mutual cycles,
hash/list links, escaped references, successful identity, later peer failures,
native members, automatic member errors, inheritance and deterministic
interruption/recovery. Together with existing serialization and object/container
suites, the core gate has 20 runs/130 cases/1484 assertions. Serialization suites
pass AST, IR, JIT and tiered modes. The three changed C++ files in main Qore are
byte-identical to the compiled isolated sources.

Fourteen Valgrind runs pass with zero memory errors and zero definite, indirect
or possible lost blocks. These include the original minimal cycle, four core
serialization suites in AST/tiered modes, existing object/class tests and the
full XML wildcard consumer, HTTP and registry suites. The old minimal cycle
leaked 1232 definite and 14176 indirect bytes; its acyclic control was clean.
The original P5-11 failure measurements are preserved, not replaced by the new
results. The known Valgrind 3.27.1 `DW_AT_abstract_origin` reader warning remains
an explicit environment finding; no test suppression was added.

The 127-suite XML gate passes 1274 cases/63311 reported assertions. The legacy
SOAP suite retains three intentional caught comparator negatives. All 19 AOT,
provider/consumer, independent matrix, survey harness and example supplements
pass. Build and ordinary test logs contain no compiler/runtime warnings or
errors; the changed Qore release note also passes strict table processing.

The SOAP 1.1/1.2 survey and strict coverage are byte-identical to P5-11: 2455
survey rows, 144 selected WSDLs/1388 directions, zero selected/value/missing/
skipped failures, and 60 still-tracked broader failures. This prerequisite
changes cleanup, not the remaining XML content semantics. Both repositories
were fetched with no incoming develop commits; no install or push was made.

See [the complete inventory](P5-12-validation.json), the Qore audit at
`examples/test/qore/classes/Serializable/audits/failed-object-graphs.md` and
[this XML evidence audit](audits/P5-12-core-graph-cleanup.md). The next independent
native prerequisite is [strict wildcard instance-type assessment](p5-native-wildcard-type-finding.md).
P5 still requires element wildcard processing, mixed/generic content, complete
nil/default/fixed and document identity semantics. P6-P9 remain required.

Reproduction uses `/tmp/wsdl-core-date-env.sh` with `qore -b --enable-debug`.
Valgrind additionally uses `QORE_PCRE2_NO_JIT=1`, `--leak-check=full`,
`--show-leak-kinds=definite,indirect,possible`,
`--errors-for-leak-kinds=definite,indirect,possible` and `--error-exitcode=99`.
All runner sources, commands, per-test logs and exact source/runtime hashes are
recorded in the validation inventory.
