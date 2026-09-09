# QName value and dependency evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P3-29 (`f6a4615`) enforces QName grammar, but ordinary WSDL conversion still
compares enumeration strings and loses namespace context in native scalars.
The reduction `/tmp/wsdl-p3-30-qname-context.qr` rejects a valid alias for an
enumerated value, accepts the same prefix rebound to another namespace, and
shows an enumerated provider accepting an unrelated name. Those schema/wire
integration requirements remain open. This increment supplies explicit immutable
QName values and providers, and fixes two native dependency defects required
for reliable independent validation.

[XSD 1.0 §3.2.18](https://www.w3.org/TR/xmlschema-2/#QName) identifies a QName by
its namespace URI and local name. Prefix spelling is lexical information.
The [namespace recommendation](https://www.w3.org/TR/REC-xml-names/#ns-decl)
defines the implicit `xml` binding and empty default-namespace resets.
No numeric rounding or text normalization beyond the datatype's XML whitespace
rule is involved in namespace identity.

`test_qname_values.py` generates 336 envelopes from seven scope arrangements,
twelve lexical inputs, both SOAP envelope versions and distinct request/response
payload names. Of these, 160 contain valid QName values. Text and attributes
are checked through explicit values and original/reconstructed providers:
2,016 conversion verdicts with exact URI, local name, prefix and lexical text.
The envelopes exercise retained XML scope extraction; this is not a claim of
new WSDL binding or native SOAP conversion support.

Three schemas per payload test unrestricted QName, a namespace-qualified
enumeration and a no-namespace enumeration. All 1,008 schema/document pairs
are assessed by pinned Xerces-J 2.12.2, Python's libxml2 DOM validator, and the
selected native dependency through `XmlReader`. The value object's equality
results must agree with the independent enumeration verdicts. Inputs are not
rewritten to make a validator accept them.

The first matrix exposed two libxml2 defects:

- **DOM absent/empty namespace comparison:** libxml2 2.12.10 rejects four valid
  no-namespace enumeration inputs carrying `xmlns=""`. Its QName values retain
  a null URI for an absent binding and an empty URI for an explicit reset;
  `xmlSchemaCompareValuesInternal()` compares those pointers' strings without
  equating the two no-namespace representations. The same comparison exists
  in 2.15.4. The dependency fix compares null and empty URIs equally. The C
  probe checks both declaration-side and instance-side resets in both APIs.
- **Implicit XML binding in streaming validation:** unpatched 2.15.4 rejects
  `xml:lang` when `xmlns:xml` is not explicitly written. Its SAX branch of
  `xmlSchemaLookupNamespace()` searches recorded declarations and returns no
  binding for the predefined prefix. The fix resolves that prefix before
  traversing declaration state. Wrong and unbound ordinary prefixes remain
  rejected.

The native dependency now passes all matrix verdicts. Python's separate,
unmodified libxml2 2.12.10 still rejects the four explicit-reset cases. The test
retains this diagnostic: it requires exactly the two enumeration errors for
the element and attribute, the precise empty namespace identity, and successful
Xerces and corrected native validation. Other mismatches fail. A corrected
Python libxml2 may accept those inputs without changing the normative assertions.

Root-cause reductions are `/tmp/wsdl-p3-30-qname-reset.{xsd,xml}` and
`qname-implicit-xml.xml` / `qname-unrestricted.xsd` under the same prefix.
The new CMake probe runs 48 QName/NOTATION schema/document pairs through DOM and streaming
validation. The provider integration tests prove that even an unpatched current
release falls back, while a corrected backport advertised as 2.12.10 stays
system-selected. Original source hashes and unchanged reconfiguration inputs
are asserted; unexpected source overrides fail explicitly.

The test harness initially kept a method reference to a temporary optional
provider; retaining the provider's lifetime fixed that test error. A worker
hash initialized from string-only members was inferred too narrowly; explicit
heterogeneous initialization fixed its result storage. UTF-8 serialization
corrected the authored Unicode-prefix fixture. A final production review kept explicit QName objects intact through provider
conversion, preventing later default-namespace reinterpretation of an unboxed
no-namespace value. Repeated and successive-provider regressions verify the fix.
None was a production workaround.
Complete test, audit, Valgrind and corpus evidence is recorded in
[EXECUTION.md](EXECUTION.md).
