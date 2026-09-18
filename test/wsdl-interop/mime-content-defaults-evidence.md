# MIME content defaults and media validation evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The multipart compiler required `part` and `type` although general
[WSDL 1.1 section 5.3](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_mime:content)
permits a single-part default and an unrestricted type default. It also accepted
invalid media strings that the direct content descriptor rejected. An empty
`mime:content` element was lost by value-existence checks in both positions.

`WsdlMediaType::declaration()` now owns defaulting and syntax/parameter validation
for both callers. Binding compilation checks declaration key presence, selects
the sole part when omitted, rejects ambiguous/unknown parts and validates every
alternative before publication. Multipart metadata retains supplied spelling;
an omitted type is stored as `*/*`.

The 70-document matrix includes 38 supported descriptions and 32 semantic
negatives. The corrected published MIME schema has a stricter required-part rule:
its observations are recorded independently, without overriding general WSDL
single-part defaults. Python ElementTree and the independent media parser assess
part/type semantics; pinned Xerces checks grammar; pinned WSDL4J reads all 38
supported descriptions and reports unmodified supplied/absent attributes.

On parent commit, the final test fails 38 of 70 cases (32 pass). The corrected
implementation passes 70 cases / 4,636 assertions through local/imported services,
both saved-service forms, detached operations and providers/examples. Twelve real
HTTP calls exercise direct empty declarations in both directions with an explicit
concrete content type. Multipart rows establish declaration and saved metadata
behavior; attachment octets remain part of the separate transport acceptance.

All 31 affected Qore suites pass (1,527 cases / 44,997 assertions),
plus 12 independent gates (including six CXF peer tests), documentation and parser
checks: 45 gates total. All 16 corpus commands meet their expected outcomes;
six semantic reports match P6-38. The legacy P5 projection diagnostic retains
expected status 1 and is not counted as conformance success.

Artifacts and exact commands: `/tmp/xml-mime-content-defaults/` and
[P6-39-validation.json](P6-39-validation.json). Audit:
[all 62 checks](audits/P6-39-mime-content-defaults.md). No C++ changes or push.

Complete HTTP URI execution needs request-local absolute target support in Qore:
`/tmp/xml-http-base-resolution/QORE-REQUEST-URL.md`. A two-server native reproducer
confirms that passing an absolute URL as the existing send path still targets
the original server. No temporary client reconfiguration or partial configuration
clone is introduced. Remaining MIME representation alternatives and attachment
contract replay also remain in P6; P7–P9 are not accepted.
