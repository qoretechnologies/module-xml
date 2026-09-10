# P3-46: literal scalar attributes and HTTP consumers

Copyright (C) 2026 Qore Technologies, s.r.o.

The final P3 consumer review added a real HTTP matrix for exact numeric, boolean,
list/union and patterned values. Its first valid request failed with an internal
`substr(nothing, integer)` exception. `SoapBinding::deserializeMessageImpl()`
unconditionally called `processMultiRef()`, which removed the schema-defined
top-level `id` attribute and then treated ordinary children as encoded accessors.
`XsdData::getValue()` also interpreted any `href` as a reference without a context.

[WSDL 1.1 section 3.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body)
distinguishes concrete literal schemas from encoded values. Attributes in a literal
part therefore reach that schema's normal validation. The binding now supplies a
reference context only for an encoded body. `XsdData::getValue()` preserves its input
when that context is absent. Actual encoded references still resolve through their
map and missing targets raise `INVALID-REFERENCE`, following
[SOAP 1.1 section 5](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383512).
No fixture-name condition, permissive conversion or attribute renaming was added.

The affected `soap.qtest` contained a synthetic reference response for the RPC/literal
`setInfo` operation in `test/test.wsdl`. Its undeclared-prefix negative was retained.
Declaring that prefix still cannot make `href` valid on its schema-defined string;
the second variant now requires rejection too. The original hash and WSDL are
unchanged. An actual RPC/encoded contract in the new suite supplies the positive
reference test, in both directions and after service reconstruction.

## Verification

`test/wsdl-scalar-consumers.qtest` passes three cases / 1,336 assertions in AST,
IR, JIT and tiered modes. Each run checks 44 HTTP exchanges: eight successful
responses and 36 deliberately invalid handler responses. Another 36 invalid
client values fail before sending. Both actual SOAP versions and original/rebuilt
services are covered, with distinct request and response values. The matrix checks
1,002-digit integers, exact long decimals, unsigned maxima, binary32/binary64 ties,
signed zero, infinity/NaN, boolean lists, ambiguous union identity, retained patterns,
token whitespace and simple-content attributes. Native type and value assertions
prevent a self-round-trip from hiding coercion. Queues and socket calls have bounded
deadlines; listeners are bound before calls and servers stop on every exit.

`test_literal_attributes.py` passes in each of the four execution modes. It checks
32 independently authored inputs and 20 outputs with libxml2 and pinned Xerces,
across both actual bindings and message directions. Exact attributes, expanded names,
text and child order are compared. Cases include top-level and nested `id`/`href`,
empty/local/external URI spellings, `root`, qualified/unqualified name collisions,
unsigned overflow, negative unsigned input and invalid nested integers. Invalid
values require `SOAP-DESERIALIZATION-ERROR`. Every manifest stage is accounted for.
The mode-specific worker also supplies `-b --enable-debug` explicitly.

All 98 affected Qore suites pass: 1,001 successful cases / 40,146 reported assertions.
The three previously documented caught comparator negatives in `soap.qtest` remain
part of its assertion accounting; all 20 of its cases succeed. The first broad run
identified its invalid reference expectation; `/tmp/wsdl-p3-46-soap-final.log`
supersedes that suite's initial result. The reviewed combined manifest is
`/tmp/wsdl-p3-46-reviewed-full-gate.json`.

Both-version survey rows and counts, and both-direction strict coverage failures
and stage accounting, are identical to the preceding gate. Strict selection has
130 WSDLs / 1,260 directions and zero selected failures. The 144 broad diagnostic
failures remain visible with their existing ownership. Original corpus files,
historical findings and selected expectations are unchanged.

The WSDL Doxygen build and all three Qore examples extracted from the touched
scalar/IEEE designs pass without diagnostics. No C++ changes or installation were
made; affected native Valgrind evidence remains in the preceding increment.

Logs: `/tmp/wsdl-p3-46-{scalar-http,scalar-http-fixed,scalar-references,modes}.log`,
`/tmp/wsdl-p3-46-literal-{ast,ir,jit,tiered}.log`,
`/tmp/wsdl-p3-46-{full-gate,soap-final,survey,coverage,docs,examples}.log`.
The initial HTTP failure and broad-gate failure are retained as reduction evidence.
The complete Python phase review, including its regex deadline investigation and
known P4/P5/P6 diagnostics, remains a separate P3 acceptance gate.
