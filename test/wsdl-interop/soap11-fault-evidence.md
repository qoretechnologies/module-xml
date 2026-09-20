# P7-05 SOAP 1.1 faults and namespace isolation

Copyright (C) 2026 Qore Technologies, s.r.o.

## Implemented behavior

SOAP 1.1 faults are checked before native namespace projection: at most one
protocol Fault, required unqualified faultcode/faultstring, optional unqualified
faultactor/detail, singleton fields, scoped QName codes, language/URI lexical
values and element-only detail. Qualified extensions cannot replace required
protocol fields. SOAP 1.1 allows custom and dotted QName codes. Its generic receiver
recognizes fields by name without imposing SOAP 1.2 field ordering or sole-Body
content rules. SOAP 1.2 field validation remains unchanged.

Decoding selects the actual expanded-name Fault before projecting fields. SOAP 1.1
qualified extension names remain qualified. In-scope namespace declarations are
retained in the exception argument for both versions. The public exception category
and standard fault field names remain unchanged.

## Requirements, root cause and cases

Primary requirements are [SOAP 1.1 section 4.4](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383507)
and [WS-I Basic Profile 1.2 section 3.4](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/BasicProfile-v1.2.html#SOAPFaults).
The 45 authored cases contain 21 valid and 24 negative messages. They cover standard,
application and dotted codes; local/default/unbound QName scope; XML whitespace;
missing, repeated and foreign fields; qualified extensions; xml:lang; URI references;
empty/populated detail; and application Body siblings. Source, saved, retained, node
and HTTP consumers share the checks.

The exact pinned W3C schemas remain unchanged and their hashes are verified. Seven
SOAP 1.1 cases explicitly differ between the schema and protocol expectations:
SOAP prose permits qualified extensions; WS-I R1016 requires faultstring xml:lang
acceptance despite its omission in the schema; the Body wildcard allows repeated
Faults that SOAP forbids; and xs:anyURI alone does not enforce URI grammar. No
failure is skipped or treated as an expected implementation defect.

The audit reproducer exposed a separate decoding defect: namespace stripping over
the entire Body merged a real Fault with an application sibling named Fault, losing
the protocol code. Stripping direct fault children also merged qualified extension
faultcode values into the standard field and could trigger a type error. The fix
selects by expanded name first and preserves SOAP 1.1 extension qualification. Tests
cover both sibling orders, native/retained paths, exact code/reason/extension values
and retained namespace bindings. Caller input is unchanged.

## Validation

All **27 affected Qore suites pass: 377 cases / 17,142 assertions**. Six focused
SOAP suites also pass compiled: **18 cases / 6,183 assertions**. The new SOAP 1.1
suite passes **2 cases / 704 assertions** across source, saved-object and saved-data
services, with additional native/retained namespace-collision checks.

Six independent Python gates pass. The combined fault gate checks the exact pinned
W3C schema expectations and **720 HTTP response exchanges** (276 SOAP 1.1 and 444
SOAP 1.2), including persistent-client recovery after negative messages. All 16
corpus commands meet their recorded outcomes. Six semantic reports match P7-04
except for the WSDL source digest. Documentation and three-file astparser checks
pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

Complete fault data/generation, declared header-fault integration, HTTP/action/media
requirements and assertion accounting remain in P7; P8–P9 remain open. This increment
includes no Qore mutation, installation, push or CI trigger.
