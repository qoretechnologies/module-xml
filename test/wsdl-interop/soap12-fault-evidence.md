# P7-04 SOAP 1.2 fault grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

## Implemented behavior

The shared envelope validator recognizes SOAP 1.2 Fault by expanded name before
native namespace projection. It validates the sole-Fault Body rule; required,
ordered and singleton Code/Reason/Node/Role/Detail fields; iterative Code/Subcode
Value QName resolution and the five top-level codes; Reason Text language and
simple content; Node/Role URI grammar through Qore; and Detail element content.
Ordinary application values named Fault remain application data. Source, saved,
retained, node and HTTP paths use the same validator. Valid fault exceptions retain
the existing public contract. This increment does not add a new fault generation API
or claim complete P7 acceptance.

## Requirements and cases

Primary requirements: [SOAP 1.2 Part 1, section 5.4](https://www.w3.org/TR/soap12-part1/#soapfault)
and [section 6](https://www.w3.org/TR/soap12-part1/#useofuris). The 73 authored cases
include 26 valid messages and 47 negative messages. Tests cover every optional-field
combination, all standard top codes, default/local/unbound QName scope, nested
subcodes, multilingual and empty reasons, duplicate languages, XML whitespace and
CDATA, missing/duplicate/reordered/foreign fields, mixed content and URI errors.

The existing `soap-envelope-peer/schemas.json` pins the unmodified W3C SOAP and XML
schemas. `test_soap_faults.py` verifies their byte hashes before schema validation.
Six cases require stricter SOAP expectations than the XSD alone: duplicate/sibling
Faults pass the schema's Body wildcard, and Node/Role references containing raw
non-ASCII or braces pass xs:anyURI but violate SOAP's RFC 3986 URI requirement.
These differences are explicit per case, not expected-failure exemptions.

Reason Text requires its own xml:lang; inherited language is insufficient. Distinct
languages are a SHOULD, so duplicate languages remain valid. The pinned XML lang
union allows a truly empty string to reset language. Its empty-string member
preserves whitespace; whitespace-only values are rejected rather than globally
collapsed to a reset. The audit regression and independent schema verify this edge; see
[XSD 1.0 whiteSpace](https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace) for union member normalization.

Root cause: previous envelope checks stopped at Body and native fault decoding
removed namespaces before interpreting fields. Invalid fields could consequently
be reported as ordinary server faults. Validation now runs while qualified names
and scalar lexical data are intact; malformed faults fail before projection.

## Validation

All **26 affected Qore suites pass: 375 cases / 16,438 assertions**. Five focused
SOAP suites also pass compiled: **16 cases / 5,479 assertions**. The new fault suite
passes **2 cases / 1,098 assertions**, covering 73 explicit cases across source,
saved-object and saved-data services and a 64-level Subcode chain.

Six independent Python gates pass. The new fault gate checks the exact pinned W3C
schema expectations and **444 HTTP response exchanges**, including negative-message
recovery with persistent clients and native/retained decoding. All 16 corpus commands
meet their recorded outcomes. Six semantic reports match P7-03 except for the WSDL
source digest. Documentation and three-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 continues with SOAP 1.1 fault grammar, complete fault data/generation and declared
header-fault integration, HTTP/action/media rules and assertion accounting. P8–P9
remain open. No Qore mutation, installation, push or CI trigger belongs to this increment.
