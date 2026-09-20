# Explicit SOAP 1.2 W3C binding derivatives

Copyright (C) 2026 Qore Technologies, s.r.o.

The pinned W3C echo corpus pairs SOAP 1.1 WSDL bindings with both SOAP message
versions. Earlier payload gates decoded both through the original binding and
serialized both as SOAP 1.1. Strict binding-version enforcement requires a real
SOAP 1.2 binding for the SOAP 1.2 payload path.

`survey.inventory()` now supplies a separately named `*-soap12-binding.wsdl`
derivative for each case containing SOAP 1.2 messages. The deterministic transform
changes the sole pinned `xmlns:soap` declaration from the WSDL SOAP 1.1 extension
URI to its SOAP 1.2 extension URI. Original file bytes, schemas, component names,
message content and catalog checksums are unchanged. Both source and derivative
hashes and the exact transform appear under `binding_derivatives` in current
reports; historical reports remain untouched.

Worker manifests explicitly select the derivative for a message's declared
`soap_version`, rather than inferring a different contract from received XML.
Coverage retains the original component identity and separately records each
message's `binding_source` and `binding_version_expected`. Output-envelope checks
use that selected version. This is payload and binding coverage; live independent
SOAP conformance remains in the separate protocol/CXF gates. No production
fallback or cross-version decoding exception is introduced by the fixture adapter.

`test_survey.py` verifies exact derivative bytes, hashes, negative manifests and
both output-envelope namespaces. `test_coverage.py` verifies per-message provenance
and applies the explicit binding derivative to the existing corrected-attribute
payload fixture as well.
