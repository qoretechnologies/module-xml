# Abstract operation identities and empty SOAP messages

Copyright (C) 2026 Qore Technologies, s.r.o.

Port-type construction previously stored operations by XML name alone, so a
later overload replaced the earlier declaration. Binding construction ignored
input/output selection labels and attached bindings to that remaining object.
Four reduced baseline cases expose the lost declaration, incorrect selection,
accepted mismatched labels and accepted ambiguous bare lookup.

P6-14 retains every effective input/output signature and the abstract message
order. Authored labels remain nullable; explicit getters derive the WSDL defaults.
Unique operations retain their existing public keys. Overloaded operations use
`name(input,output)` for lookup, while their XML names continue to define RPC
wrappers. Concrete binding labels narrow the candidate set; public binding
lookup also checks actual membership before deciding ambiguity. Imported port
types retain their namespace identity. Services rebuild from retained WSDL;
standalone operations retain the pattern and selection key. Old standalone
graphs cannot recover missing two-message order and report that limitation when
an input default is requested.

[WSDL 1.1 section 2.4.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_names)
defines the abstract defaults, and
[section 2.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_bindings)
defines operation selection in bindings. The pinned WSDL4J 1.6.3 oracle checks
all four patterns through its own effective-label lookup, input-only/output-only
and combined binding selectors, imports, duplicate signatures and unresolved
bindings. WSDL4J's undefined placeholders are rejected by the oracle; parsing
success alone does not count as successful resolution. A separate pinned WSDL
schema test accepts zero-part messages and rejects operations with no input or
output. This does not claim full WSDL4J grammar validation.

The zero-part fixtures also exposed truthiness checks that omitted RPC wrappers
and document Bodies, then rejected empty wrappers during decoding. RPC calls
now keep an operation wrapper even with no parameters, and SOAP messages retain
the required Body element. Decoding distinguishes key presence from value
presence and returns an empty body map. Missing or incorrectly named wrappers,
missing Bodies and unexpected body content reject. The body structure follows
[SOAP 1.2 sections 5.1 and 5.3](https://www.w3.org/TR/soap12-part1/#soapbody);
RPC wrapping follows [WSDL section 3.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body).
The old header-only fixture declared neither input nor output. It now uses a
valid zero-part input message, with the original header values still asserted.

The focused Qore suite passes 12 cases / 481 assertions. It includes source and
saved graphs, independently authored envelopes, both SOAP versions/directions,
RPC literal/encoded empty wrappers, empty document Bodies with native and
retained-XML decoding, malformed inputs and real HTTP overload dispatch with
distinct actions and integer/string values. Seven independent oracle tests
cover WSDL operation selection and schema grammar.

The full regression and corpus results are recorded in
[P6-14-validation.json](P6-14-validation.json), with the complete
[62-check audit](audits/P6-14-operation-identities.md). The test-only correction
of retained-XML method names and retained completed-suite accounting are explicit
in that record. Production sources remained unchanged across that resumed gate.
See the [durable component design](../../design/wsdl-component-references.md)
for the implemented API and saved-graph contracts.

The remaining P6 binding matrix includes explicit empty body-part selection,
header/fault partitioning, interaction-pattern transport restrictions and HTTP/MIME
behavior. P7–P9 remain open. No C++ changes or Valgrind requirement accompany
this increment.
