# MIME multipart grammar and nested SOAP metadata

Copyright (C) 2026 Qore Technologies, s.r.o.

Multipart payloads previously bypassed extension grammar validation and source
projection. Foreign elements named `part` or `body` could compile as MIME/SOAP;
nested attributes and character data were unchecked. The binding compiler also
ignored SOAP headers inside a MIME part, dropped body namespace/encoding hints,
and converted only the first content alternative's public part name to its
internal argument key.

The stream now validates MIME containers and delegates format leaves to the
existing SOAP/MIME grammars. Source projection follows MIME containers with actual
namespace scopes and isolates unknown optional payloads. Compilation retains
nested headers/headerfaults and body hints, requires a primary SOAP body, rejects
headers outside that root part, and maps every content alternative through the
selected message's part map.

The fixture inventory pins the published
[MIME schema dated 2004-08-24](https://schemas.xmlsoap.org/wsdl/mime/2004-08-24.xsd)
with its original license and checksum. It corrects the older schema's
unqualified `part` declaration. The
[WS-I Attachments Profile](https://ws-i.org/Profiles/AttachmentsProfile-1.0.html)
provides the relevant checks: R2905/R2906 permit SOAP headers within the root MIME
part, R2907 requires qualified MIME parts, R2909 keeps alternatives on one abstract
part and R2911 requires one primary SOAP body part. R2917 permits ordinary SOAP
transport when there are no attachment values. General WSDL acceptance remains
separate from full profile conformance: optional part names are retained, and the
profile's stricter explicit-content-part requirement is not imposed globally.

The shared fixtures contain 118 grammar/semantic cases and two shared-element
alternative cases. Forty descriptions are supported. Twenty-six schema-valid
semantic negatives have explicit adjudications; the remaining 54 negatives fail
grammar. Pinned Xerces checks all 120 documents. WSDL4J 1.6.3 independently observes
multipart counts, SOAP body/version/use/parts/hints, nested header message identities,
headerfault counts and attachment alternatives. WSDL4J's raw attribute spellings
are normalized with independent XML whitespace rules, as its existing list-token
limitation is already documented by the body-parts oracle.

The Qore suite passes 120 cases / 9,748 assertions across local/imported source,
both saved-service forms, detached handles and provider examples. Thirty-eight
supported SOAP header/body fixtures make 228 live HTTP calls in both SOAP versions.
The two attachment fixtures test declaration compilation, identity and saved
metadata; they are not counted as binary attachment transport coverage.

```sh
QORE_MODULE_DIR=build-debug:qlib:/tmp/xml-http-part-values/runtime:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-mime-part-grammar.qtest
python3 -B test/wsdl-interop/test_mime_part_grammar.py -v
```

The module path retains the built Qore Mime fix described in
[HTTP part-presence evidence](http-part-presence-evidence.md); this increment does
not modify Qore source or installation. [Validation](P6-38-validation.json) records
all affected gates, corpus comparisons and hashes. [Audit](audits/P6-38-mime-part-grammar.md)
records all 62 checks. Local logs and baseline reductions are under
`/tmp/xml-mime-part-grammar/`. No C++ changes require Valgrind.

Remaining P6 work includes complete MIME representation alternatives and HTTP
URI behavior. P8 still owns full attachment wire/reference interoperability and
legacy encoding acceptance; this declaration fix does not claim those gates.

All 30 affected Qore suites pass (1,457 cases / 40,361 assertions),
plus 13 supplemental gates. All 16 corpus commands meet expected outcomes and
six semantic reports match P6-37. The legacy P5 projection diagnostic retains
expected status 1; it is not a conformance pass.
