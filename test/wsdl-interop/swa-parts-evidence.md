# SOAP MIME attachment part evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

Committed P6-41 cannot serialize CXF `echoData`: its `data` part is outside the
explicit SOAP body selection and remains unconsumed. The reduced baseline is
`/tmp/xml-swa-parts/main-baseline.log`. The new binding codec selects attachments
independently of body and header parts, preserving public WSDL part identities.

Type-based parts carry raw media, independently of their abstract XSD type
(WS-I Attachments Profile R2943). Global-element parts carry schema-valid XML
(R2942/R2944), using the shared standalone XML codec. Required part presence,
Content-ID part encoding, media alternatives, charset/BOM handling and independent
SOAP root metadata are checked. Explicit maps preserve body/header/attachment
placement; native and retained XML consumers can forward the decoded values.

Audit probes exposed single-attachment flattening and qualified-header placement
errors. The fixes preserve attachment part-name keys and return three distinct
maps whenever header identities require namespace qualification. Provider types
follow the selected client binding, validate complete messages without I/O, retain
raw media values, and generate valid binding-aware examples. Abstract-message
providers continue to describe the schema independently of MIME bindings.

The focused suite passes 19 cases / 876 assertions. Coverage includes SOAP 1.1
and 1.2, UTF-8/ISO-8859-1/UTF-16, source/saved/detached graphs, both directions,
empty bodies/media, shared XML roots, Unicode identifiers, body/header overlap,
imported colliding header names, retained XML forwarding, saved/soft/optional
providers, selected ports, concurrency and local HTTP consumers. Negative cases
cover absent/duplicate/malformed part IDs, media ambiguity/incompatibility,
wrong XML roots, unbound values and invalid provider requests before transport.

The pinned Apache CXF 4.1.3 peer independently generates three attachment
operations and six complete golden HTTP messages. Python's email parser compares
root XML infosets and each part's exact decoded bytes. Seven Python tests verify
pinned dependencies, source/saved/detached capture replay, 24 actual CXF/Qore calls
in both directions across native/retained XML consumers, and 60 additional
malformed-request/response and recovery exchanges. The separately named WSDL
derivative removes only an invalid `expectedContentTypes` annotation from an
anyURI-derived element; the original remains unchanged and exact derivative
comparison is tested. See the [peer record](swa-peer/README.md) and
[W3C annotation restrictions](https://www.w3.org/TR/2005/NOTE-xml-media-types-20050504/#expectedContentTypes).

All 58 final gates pass: 41 debug Qore suites (1,669 cases / 54,721 assertions),
15 independent Python gates, docs and astparser. All 16 corpus commands meet
expected outcomes. Six semantic reports match P6-41 except runtime version
metadata, preserving the separately classified legacy projection failures.
Production/test sources and installed Mime are hashed before and after execution.
Build type: Debug. WSDL, SoapClient, SoapHandler and SoapDataProvider also compile
as QMODs, and the same 19-case / 876-assertion suite passes with all four compiled
modules loaded from build-debug/qlib-qmod. No C++ changes or Valgrind requirement.

The 62-item audit records 27 Pass / 35 N/A / zero Fail. See
[validation](P6-42-validation.json), [audit](audits/P6-42-swa-parts.md), and
[durable design](../../design/wsdl-swa-parts.md). Artifacts:
`/tmp/xml-swa-parts/`. The installed shared dependency remains Qore
`79348ce8c1494a717ec3d1e40c07eafafdfc9c37` / Mime 1.9; no Qore repository changes.

P6 still requires general multipart layout compilation/execution and complete
HTTP URI behavior, including the separate request-local URL API handoff in
`/tmp/xml-http-base-resolution/QORE-REQUEST-URL.md`. Full href/swaRef/XOP/MTOM
reference semantics belong to P8 and are not claimed by this attachment-part
increment. P7–P9 remain incomplete.
