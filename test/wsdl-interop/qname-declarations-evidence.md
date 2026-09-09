# QName enumeration declaration identity

Copyright (C) 2026 Qore Technologies, s.r.o.

The declaration parser previously stored enumeration literals as string keys.
This discarded each facet's namespace context and merged identical spellings
bound to different URIs. Finalization checked QName grammar alone. An unbound
prefix or a namespace/local value outside an inherited enumeration could
therefore survive schema construction.

The parser now captures each literal's normalized text and resolved URI while
the declaration scope is active. It keeps all literals through deferred base
resolution. QName finalization validates grammar, prefix binding, inherited
patterns and every inherited enumeration. A nested namespace/local index
compares identities without prefix matching or URI normalization. Temporary
capture state is released on successful and failed finalization. The raw
schema sources retained by `XsdSchema` reconstruct the same declaration checks.

The normative requirements are XSD 1.0 [QName lexical/value spaces](https://www.w3.org/TR/xmlschema-2/#QName),
[enumeration representation and valid restriction](https://www.w3.org/TR/xmlschema-2/#rf-enumeration)
and [QName interpretation](https://www.w3.org/TR/xmlschema-1/#src-qname).
Enumeration literals must be valid for the base. A base pattern constrains the
literal spelling, even when a different prefix denotes the same QName value.
The newly declared restriction's own pattern is an instance constraint and
does not impose an additional spelling requirement on its enumeration literals.
URI comparison follows [Namespaces in XML 1.0 section 2.3](https://www.w3.org/TR/REC-xml-names/#ComparingURIRefs).

`wsdl-qname-declarations.qtest` covers schema/type/restriction/facet scopes,
unbound and malformed values, exact URI and local names, duplicate spellings,
default resets, implicit `xml`, inherited pattern branches, forward/inline
bases, chameleon includes into two namespaces, failed-addition recovery,
reconstruction, cancellation, concurrent copies and 1,024 distinct identities
sharing one lexical spelling. Non-QName enumeration regressions ensure that
capturing an unresolved declaration does not impose QName rules on other types.

`test_qname_declarations.py` checks 66 declarations in atomic, forward-reference
and simple-content models: 198 independent schemas and 396 WSDL parse results
across actual SOAP 1.1 and 1.2 binding contracts. These are declaration checks,
not new instance-conversion or protocol coverage. Xerces-J 2.12.2 and Python
libxml2 2.12.10 validate the unchanged generated sources independently.

## Xerces reserved-prefix disagreement

Xerces accepts `xmlns:Name` both as an enumeration literal and as instance QName
text. The [XML Infoset element definition](https://www.w3.org/TR/xml-infoset/#infoitem.element)
explicitly excludes `xmlns` from in-scope namespace items. Its binding is not
available for QName value interpretation; ordinary undeclared prefixes reject.
WSDL and libxml2 reject all three declaration models in the matrix.

The root is Xerces `NamespaceSupport.reset()`, which seeds both `xml` and `xmlns`
bindings, followed by `QNameDV.getActualValue()` looking up a prefix without
excluding `xmlns`. This is visible in the
[Apache namespace source](https://raw.githubusercontent.com/apache/xerces2-j/trunk/src/org/apache/xerces/util/NamespaceSupport.java)
and [QName validator](https://raw.githubusercontent.com/apache/xerces2-j/trunk/src/org/apache/xerces/impl/dv/xs/QNameDV.java).
`javap -c` verifies the same initial bindings in the pinned, unmodified 2.12.2
JAR (SHA256 `6fc991829af1708d15aea50c66f0beadcd2cfeb6968e0b2f55c1b0909883fe16`).
The test asserts this exact disagreement, including empty Xerces diagnostics;
it never turns the invalid WSDL declaration into a pass or changes the source.

Initial draft fixtures used raw Unicode and braces in namespace URI references.
Namespaces 1.0 requires URI references, so those fixtures were invalid; the final
matrix uses valid percent-encoded URI spellings and tests Unicode composition
in QName local names. This differs from XML Base, whose specification permits
extended IRIs.

## Recursive native execution regression

The complete declaration suite exposed a core JIT storage defect during
chameleon include parsing. An inner `parseTypes` call overwrote its caller's
closure-backed loop variable, so the caller subsequently processed the child's
declarations again. JIT `LoadClosure` and `StoreClosure` omitted instantiation
of owned body locals before the runtime's name-based lookup; AOT already
instantiated them. A small recursive tree walker reproduced the same wrong value
after deterministic native compilation completion.

Qore develop commit `f135ddac7` creates the current call's own binding before
these accesses, using the existing frame-aware helper. It excludes captured
outer locals and parameters. Native recursion, escaped-reference, uninitialized
capture, exception/reuse and Valgrind tests accompany the fix. The unchanged
XML test order now passes in every execution mode and both tested time zones.
The separate core audit and exact final library hash are recorded in EXECUTION.md.

## Separate detached-type lifetime finding

A direct `findType(...).serializeToData()` call can fail with
`OBJECT-ALREADY-DELETED` for `XsdAbstractType::nsc`. Both constructors store a
weak reference to the declaration's `Namespaces`; the temporary namespace
registry can be destroyed after schema construction. Whole-schema
reconstruction reparses retained sources and does not take this failing path.

The reduction also fails against the unchanged `42046f7` WSDL source:
`/tmp/wsdl-p3-31-detached-before.qr` and `.log`, loading
`/tmp/wsdl-p3-31-before/WSDL.qm`. This is a separate pre-existing finding assigned
to the next P3 increment, before namespace-aware detached schema integration.
It is not a passing reconstruction case or a reason to relax declaration checks.
No speculative old-metadata recovery branch is included in this change.
