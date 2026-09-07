# Schema composition oracle adjudication

Copyright (C) 2026 Qore Technologies, s.r.o.

`test_composition.py::CompositionTest::test_chameleon_cycles_and_namespace_rejections`
constructs an entirely local graph, with a resolver that records every requested resource.
The two `import-mismatch` and `import-chameleon` sources import `urn:wrong` from a
document with target namespace `urn:a` or with no target namespace, respectively.
Neither source uses an imported component.

libxml2 2.12.10, accessed through lxml 6.1.1, fetches these resources but accepts the
containing schemas without a diagnostic. Xerces-J 2.12.2 rejects them with
`src-import.3.1`: the imported namespace and the retrieved target namespace disagree.
[XSD 1.0 §4.2.3, Import Constraints and Semantics, clauses 2 and 3.1](https://www.w3.org/TR/xmlschema-1/#src-import)
require this match once a referent is supplied. The retrieved schemas are therefore
invalid imports; acceptance by libxml2 does not adjudicate them as valid.

The regression keeps both minimal inputs, checks that libxml2 actually fetched their
dependencies if it accepts them, and requires the normative rejection from Qore
(`WSDL-ERROR`) and pinned Xerces. A libxml2 version that rejects them also satisfies
the test. This is a recorded oracle limitation, not a passing invalid-input case.

The separate Issue4449 derivative preserves all original fixture bytes and checks
each exact substitution and source/derived hash. Its positive graph uses includes
for the shared target namespace. Both validators compile the corrected schemas and
validate the expected `test1` payload; Qore rejects the original inconsistent imports.

`test_simple_dependency_graphs` also records an independent Xerces-J 2.12.2
limitation: it accepts `xs:anySimpleType` as a list item type. That ur-type has no
atomic/list/union variety. [XSD 1.0 §3.14.6, Derivation Valid (Restriction, Simple),
clause 2.1](https://www.w3.org/TR/xmlschema-1/#cos-st-restricts) requires a list's item
type to have atomic variety or to be a union whose members are atomic. libxml2
rejects the source for its absent item-type variety, and the Qore regression
requires `WSDL-ERROR`. The Xerces acceptance remains an adjudicated oracle
limitation, not evidence for treating that declaration as valid.
