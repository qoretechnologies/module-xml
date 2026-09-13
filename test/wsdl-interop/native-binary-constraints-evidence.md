# P5-18c native binary constraints and normalization ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

On `8cec041`, the native compiler accepted hexadecimal and Base64 default/fixed
declarations whose canonical spellings failed their patterns. The existing
selected-value canonical checker omitted both binary families. It now checks
uppercase hexadecimal and whitespace-free Base64 forms without replacing the
declaration's original computed value or namespace context.

The lexical investigation also confirmed native acceptance of `YW!Jj`, `YQ==!`
and `YWJj` followed by a nonbreaking space. Both Base64 scans ignored arbitrary
non-alphabet characters. They now permit only XML whitespace outside the alphabet,
while retaining complete padding and unused-bit validation. See the
[implemented design and normative references](../../design/native-binary-constraints.md).

Allocation testing found three ownership/error paths:

- Hexadecimal string and Base64 buffer allocation failures returned invalid-input
  status. Both now free their temporary value and take internal-error cleanup.
- Normalization used a nullable-string result that conflated no change with
  allocation failure. Private status-bearing variants retain the public ABI while
  datatype validation propagates failure before continuing.
- A normalized-string value could normalize twice and overwrite its first owned
  buffer with null. An existing normalization buffer now remains owned until cleanup.

The standalone sweeps test success, every permanent allocation failure, rejection
and recovery with and without computed outputs. The broader normalization cases
include integers, normalizedString, token, NCName, URI and binary values.

Acceptance is recorded in [P5-18c-validation.json](P5-18c-validation.json):
153 Qore suites, 55 dependency-provider tests, the independent 208-schema/229-document
matrix, 570 new native assertions, 151 datatype allocation faults and 2,688
canonical-declaration allocation faults. Native sweeps and direct Qore Valgrind
report zero errors and zero lost memory. Build and affected API docs are clean.
Both corpus modes match `8cec041` at every case, count and stage, retaining all
tracked later-phase failures and unassessed preservation records.

Raw evidence is under `/tmp/wsdl-p5-18c-binary/final/`. The initial binary gate
also passed all 153 suites; the final gate additionally includes the normalization
ownership correction. A temporary CMake refactor omitted a separator and failed
its output hash guard in three provider checks; it was corrected and the entire
55-test provider suite rerun. Only final passing results are accepted. The private
dependency's generated source bytes are verified by checked hashes.

`/tmp` quota prevented writing one auxiliary expected-source artifact; complete
test records were retained. Superseded provider builds were removed and final
provider fixtures use `build-debug/test-artifacts` for temporary storage. The
allocation investigation is written up in `/tmp/wsdl-p5-18c-binary/README.md`;
these fixes belong to module-xml and require no separate main-Qore change.

The [full audit](audits/P5-18c-native-binary-constraints.md) covers all 62 checks.
No installation or push. WSDL binary canonical declarations, float/calendar
canonical forms, instance default projection, key/unique/keyref, complete typed
preservation and P6–P9 remain required work. The WSDL prototype under the raw
evidence directory is preparatory and is not included in this native increment.
