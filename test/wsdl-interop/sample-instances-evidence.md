# Native sample instance evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P3-43 validates native message candidates through the existing schema instance
conversion before returning them. See [the implemented contract and example](../../design/wsdl-sample-instances.md).
This closes the unchecked-generation boundary; it does not claim that the
remaining P3-P9 schema and protocol work is complete.

## Reductions and corrections

The P3-42 scalar preflight returned five invalid native samples across six
contracts. Lexically valid ENTITY names cannot satisfy the SOAP document's
unparsed-entity requirement. Native element, type-part and multipart generation
now reports `XSD-SAMPLE-ERROR` for a rejected candidate. Independent datatype-only
sampling retains its lexical contract. The existing bounded generator need not
find every possible valid alternative: failure to generate an `ENTITY | int`
candidate does not prevent callers from supplying the valid integer `17`.

The final nine-case suite against immutable parent `a0bdea1` has eight errors
and one passing case (32 reported assertions); see
`/tmp/wsdl-p3-43-before-final.log` and `/tmp/wsdl-p3-43-before-final/`.
The initial implementation also bypassed public subclass hooks for nested
elements. `/tmp/wsdl-p3-43-subclass-before.log` demonstrates the changed value
(`123` instead of the override's `"42"`). A targeted, consumed child-call context
now preserves public dispatch while deferring each intended child's validation
to its root. It is thread-local and restored with `on_exit`, including exceptions
before a subclass enters the base method. Reentrant generation receives its own
check. Tests verify exact callback counts, four simultaneously pending child
calls, controlled exceptions and actual Program interruption with recovery.

The unknown-message diagnostic also lacked its first formatting argument. It
now reports the requested name and known names, with both asserted by the suite.
No invalid sample is silently returned, and no retained XML check is disabled.
The existing `choices: True` native result remains an explanatory description.

## Verification

Commands source `/tmp/wsdl-core-date-env.sh` and run `qore -b --enable-debug`
with local WSDL/xml and the frozen Debug core/DataProvider. The regression gate
passes **94 suites, 966 cases and 36,510 reported assertions**, without warnings
or failures. Logs and structured results are
`/tmp/wsdl-p3-43-reviewed-gate.log` and
`/tmp/wsdl-p3-43-reviewed-xml-gate.json`. The new suite passes nine cases and
138 assertions in each of AST, IR, JIT and tiered modes:
`/tmp/wsdl-p3-43-reviewed-mode-<mode>.log`.

The unchanged independent matrices pass:

| Matrix | Coverage | Final log |
| --- | --- | --- |
| ENTITY, 138.318 seconds | 12,096 outcomes; 8,280 document verdicts, including 864 invalid inputs | `/tmp/wsdl-p3-43-reviewed-entity.log` |
| QName context, 336.536 seconds | 296 inputs; 4,072 worker outcomes; 3,776 independently checked input/output documents | `/tmp/wsdl-p3-43-reviewed-qname.log` |

Both use actual SOAP 1.1 and 1.2 bindings, request/response directions and exact
value/namespace assertions. The QName matrix retains its single previously
adjudicated Xerces schema diagnostic for QName-list enumeration/length; its
expected diagnostic and normative verdict are unchanged, as documented in
[QName context evidence](qname-context-evidence.md). No new allowances or skips
were added. All 72 ENTITY WSDLs are byte-identical to P3-42; the 84-file inventory
is `/tmp/wsdl-p3-43-fixtures.json`.

The final both-version survey preserves all 2,411 rows; the coverage report
preserves all 293 cases, counts and failure identities. Strict selection has no
failure; 144 broader failure signatures remain. Only source provenance changes.
Comparison: `/tmp/wsdl-p3-43-comparison.json`. Fifteen survey methods pass. The
fourteen coverage methods retain exactly the two known P6 binding-version
failures, still reported as failures. Their logs use the
`/tmp/wsdl-p3-43-reviewed-` prefix with `survey-tests` and `coverage-tests`.

A final documentation-only source edit added the class example after the full
gate and matrices. The new suite, both documented examples, Doxygen and both
reports were rerun on those final bytes; executable implementation and tests
are identical to the reviewed gate. Final logs use `/tmp/wsdl-p3-43-` with
`documentation-final`, `example`, `doxygen-example`, `docs-final`,
`survey-final` and `coverage-final` suffixes. Doxygen and examples pass without
warnings or errors.

Final WSDL SHA-256:
`72e9aa0dd0a2e5db8266b08a903e79c217ed6edc670c4b2b397753fd5562b806`.
No C++ changed; Debug native xml retains SHA-256
`95ed6b98adc9c3171883c2c5d8e848431d1bf1720961faca8502ca54466e5824`.
No new Valgrind run is required. Main Qore is clean develop at `4e049e0d8`.
The exact file/log manifest is `/tmp/wsdl-p3-43-final-manifest.json`.
See [all 62 audit checks](audits/P3-43-sample-instances.md).
