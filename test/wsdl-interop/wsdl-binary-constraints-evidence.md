# P5-18d WSDL canonical binary declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL's canonical declaration capture handled numeric and boolean members but
retained the source spelling for binary members. This omitted the second
canonical assessment required by XSD 1.0
[element](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct)
and [attribute](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#a-props-correct)
declaration rules. The selected octets now supply
[uppercase hexadecimal](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#hexBinary-canonical-representation)
or [whitespace-free Base64](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#base64Binary).
This is the WSDL counterpart of native commit `2630052`.

The canonical trial checks validity without replacing the original converted
value, selected member or retained lexical carrier. A hex-pattern-`ab`/string
union can accept canonical `AB` through its string member while retaining the
original binary fixed identity. Binary conversion uses the selected octets
directly, before the other families' textual normalization. This also avoids an
invalid binary-to-string conversion exposed by forced AST execution.

Acceptance uses installed Qore `8c0c22c150c6e51ed09976ca99d74041ec074620`, frozen
under `/tmp/wsdl-p5-17b-identities/final/runtime`, with local Debug XML and WSDL:

- The unit suite covers 206 declarations (110 valid, 96 rejected as WSDL-ERROR),
  saved schemas/providers, selected union identity, interrupted canonical
  conversion and 384-octet values: five cases and 920 assertions.
- The real HTTP suite covers both SOAP bindings, original/native policies,
  SoapClient/SoapHandler/SoapDataProvider, omitted attributes, invalid requests
  and responses, and deterministic shutdown: one case and 88 assertions.
- The independent matrix accounts for exactly 1,498 records, including 880
  request/response SOAP payloads across original/saved services. Pinned
  Xerces-J 2.12.2 assesses 206 schemas and 1,086 documents; Python independently
  compares decoded bytes, selected string values and expanded QName identities.
- Both full corpus modes equal P5-18c at every case and stage. The existing
  four legacy dynamic-type failures and unassessed typed-preservation records
  remain visible; this is not a claim of complete conformance.

The [validation inventory](P5-18d-validation.json) records the final full suite,
forced execution modes, AOT checks, affected documentation build, source hashes
and exact commands. Raw evidence is in `/tmp/wsdl-p5-18d-binary/final/`.
The [full audit](audits/P5-18d-wsdl-binary-constraints.md) covers all 62 checks.
See [reproduction commands](README.md#wsdl-canonical-binary-declarations-p5-18d)
and the [implemented design](../../design/wsdl-canonical-constraints.md).

No native code changes in this increment, so no additional Valgrind run is
required. No Qore source change, installation or push. Float/calendar canonical
declarations, empty-element default PSVI, key/unique/keyref, complete typed
preservation and P6–P9 remain required work.
