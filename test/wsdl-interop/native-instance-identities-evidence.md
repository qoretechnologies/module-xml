# P5-20h native instance identity evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment repairs native validation of builtin instance attributes and
selected list varieties. WSDL instance tuple integration remains in P5-20f;
this is not P5 or SOAP conformance acceptance.

## Requirements and causes

[XSD 1.0 Structures §3.2.7](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Built-in_Attribute_Declarations)
assigns the four `xsi` attributes QName, boolean, URI-list and URI types.
Libxml2's meta-attribute paths bypassed identity assessment for both simple and
complex element content. The new private helper assesses present attributes
with their builtin types before ordinary attributes. It does not invent absent
attributes or assess skipped element subtrees.

[XSD 1.0 Datatypes §2.5](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#datatype-dichotomies)
distinguishes atomic, list and union varieties. Previously a one-item list could
compare equal to an atomic value. Empty lists used the same null compiled-value
pointer as nil and were wrongly unqualified. Keys now retain nil and selected
list variety separately, including the selected union member. Matched default
attributes are converted in declaration namespace scope to retain that variety;
schema-owned values remain borrowed until replaced by instance-owned values.

The formatter's unchecked appends could continue after a failed allocation or
lose owned storage. Checked growable buffers now propagate failure. QName text
also duplicated its namespace instead of appending its local name; NOTATION
text omitted its namespace. Both now retain the complete expanded name. This
format is used for internal hashing and diagnostics, not a new XML lexical form.

Valgrind isolated a further leak to invalid lexical `xsi` attributes selected by
an identity field. Popping the stream state without its match history left a
field active past its selector. Invalid matches now discard that history before
popping. The detailed isolation and allocation investigation is retained in
`/tmp/wsdl-p5-20h-xsi-identities/ALLOCATION-FORMAT.md`.

## Regressions and independent results

`fixtures/instance-identities.json` contains 41 schemas and 121 documents:
51 valid and 70 invalid. It covers all four attributes, simple/complex owners,
key/unique/keyref, prefix aliases, boolean and URI normalization, absence,
wildcard modes, invalid lexical forms, cardinality, list/atomic distinctions,
empty lists, nil, union order, defaulted QName lists and instance prefix rebinding.
The accepted pre-increment dependency disagreed with 36 expected outcomes.

The pinned Xerces runner agrees on 118 documents. Its three known differences
are `@*`, `@xsi:*`, and `@xsi:type | @xsi:nil` selecting two attributes.
[XSD 1.0 Structures §3.11.4 clause 3](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-identity-constraint)
requires at most one node. Xerces' `XPathMatcher.java` stops after its first
matching attribute and suppresses later union-branch matches when an earlier
branch matched. Those three expectations remain invalid and are explicitly
labelled `attribute-field-first-match`; oracle acceptance is never counted as
normative success. The pinned source archive SHA256 is
`3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.

Run `python3 test/wsdl-interop/test_instance_identities.py -v` for independent
results, and `qore -b --enable-debug test/xml-instance-identities.qtest` with the
local Debug binary module and repository qlib paths. The public test checks DOM,
reader and parse-with-schema behavior, error categories, context reuse and
unchanged document text: 434 assertions. Direct native DOM/stream validation of
all 121 documents also passes with zero Valgrind errors and zero exit bytes.

The provider suite runs direct QName/NOTATION formatting checks, positive and
negative configure probes, broken-system AUTO fallback and SYSTEM rejection,
source hash guards, source distribution and idempotence for both changed native
translation units. `test/cmake/libxml2_instance_identity_allocation.c` injects
single and persistent failures at 162 positions, checks exact live allocation
counts and recovery, and checks rejection/reuse for six invalid lexical cases.
Native allocation Valgrind has zero errors and zero exit bytes. Fault hooks only
exist in the standalone test translation unit.

Qore Valgrind runs the direct frozen ELF with `-b --enable-debug` and
`QORE_PCRE2_NO_JIT=1`. It reports zero errors and zero lost bytes; 114,614 bytes
remain reachable in the runtime. The runtime is a frozen independently prebuilt
Release copy of concurrent core work, including the separately verified core
optionality fix. This does not claim an installed or committed Qore release.
The XML module and private dependency use the verified Debug build.

## Final gate and scope

Exact sources, runtime provenance, commands, final test counts, corpus comparison,
Valgrind logs and guide hashes are in [P5-20h-validation.json](P5-20h-validation.json).
The [full audit](audits/P5-20h-native-instance-identities.md) records all 62 checks.
The four legacy/native SOAP-version survey and strict coverage reports remain
visible diagnostic reports; their successful command status is not conformance.
Known later-phase failures retain their classifications.

Artifacts are retained under `/tmp/wsdl-p5-20h-xsi-identities/`. No installation,
push, main-Qore mutation or CI pipeline execution is part of this increment.
