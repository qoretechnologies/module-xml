# URI and language value acceptance (P5-19g)

Copyright (C) 2026 Qore Technologies, s.r.o.

Based on `0d3e378`, this increment fixes builtin anyURI/language conversions that
previously accepted malformed lexical values as generic strings. Providers retain
explicit text-type metadata, and annotation language attributes share the lexical
helper. URI references are not retrieved or decoded, and language case is retained.
See [root cause](p5-wsdl-uri-language-finding.md),
[implemented design/example](../../design/wsdl-uri-language-values.md),
[inventory](P5-19g-validation.json) and [full audit](audits/P5-19g-uri-language.md).

Final validation uses frozen source hashes throughout:

- All 174 broad Qore suites pass without warnings/errors. The additional focused
  simple-content/collection-constraint suite also passes: 175 distinct Qore suites.
- All three new suites pass in AST, IR, JIT and tiered execution modes:
  URI/language values 1,241 assertions; simple content/defaults 160; actual SOAP
  1.1/1.2 HTTP consumers 312. Six Python supplements pass, for 18 supplemental
  executions including the twelve Qore mode runs.
- The authored eight-schema/73-document matrix agrees with pinned Xerces and
  native XSD validation. WSDL tests compare preserved strings/lists and explicit
  primitive union keys, with original/saved schemas/providers and both decoding
  modes. Cases cover whitespace, Unicode, URI escaping, language boundaries,
  restrictions, lists/unions, malformed declarations/reconstruction, examples,
  optional/list provider variants and cancellation/recovery.
- Actual HTTP contracts exercise requests and responses, selected dynamic types,
  lists/unions, default/fixed attributes, saved message providers and both SOAP
  bindings. Additional simple-content tests validate content and attribute fields.
- Empty union defaults use the already approved canonical-actual-type rule:
  declaration `1` has boolean identity in `language | boolean`; canonical `true`
  selects language for an empty instance. Both identities are asserted separately.
- Native/module/WSDL documentation and metadata targets pass. No C++ changes were
  made; the binary and URI API retain the preceding increment's clean Valgrind evidence.
- Both-version diagnostic surveys and strict selected coverage in legacy/native
  modes retain exactly the parent's results; only the WSDL source hash differs.
  The NOTATION report still records 24 failed compatibility rows and 48 classified
  default-context oracle disagreements. Diagnostic success is not conformance.

The inventory contains commands, individual results and source/fixture/report/log
hashes. Artifacts: `/tmp/wsdl-p5-19g-uri-language/final/`. Tests use the fixed Qore
ELF/library under `/tmp/wsdl-p5-17b-identities/final/runtime`, `-b --enable-debug`
and `QORE_MODULE_DIR=build-debug:qlib`; PCRE2 JIT remains enabled. The installed Qore
library matches the frozen library. Main Qore remains clean/read-only; no install
or push. Unrelated `test/cmake/__pycache__/` is excluded.

Next: retain and validate key/unique/keyref declarations, then enforce scoped
instance tuples and finish typed-preservation accounting. Their root cause is
confirmed independently in `/tmp/wsdl-p5-20-identities/`: WSDL discards these
components and accepts duplicate/missing keys and dangling references. P5 is
still open; P6-P9, including Python CI integration, remain required. No question
is pending.
