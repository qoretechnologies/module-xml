# Native element defaults and expanded-name ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

The native conversion, DOM validation and streaming reader assess an empty
non-nilled element using its declaration's default or fixed constraint.
[XSD 1.0 cvc-elt 5.1.1 and 5.1.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
require the canonical spelling to satisfy the actual type, including a type
selected by `xsi:type`. The selected instance value supplies identity-constraint
comparisons. Original declaration text and computed constraint values remain
unchanged. The [approved PSVI interpretation](../test/wsdl-interop/default-identity-investigation.md)
records the ambiguity introduced by the E1-56 erratum and the explicit decision.

For example, an element declared as boolean with default `1` can use an actual
boolean restriction whose pattern accepts `true`. An empty occurrence satisfies
that restriction; one whose actual restriction accepts only `1` fails. Explicit
text `1` still satisfies the latter restriction. A boolean-or-string declaration
with the same default and actual `xs:string` contributes string `true` to an
identity constraint, independently of the declaration's boolean value.

`qoreXmlValidateElementDefault` creates a temporary canonical lexical using the
existing exact numeric, binary, IEEE and calendar helpers. Mixed lists preserve
the selected identity of each declaration item while constructing this spelling.
The ordinary actual-type checker then selects the instance value. Empty CDATA
and comments do not prevent default application; character whitespace does.
The existing nil, content-model and attribute checks still run. Validation does
not insert text into the module's parsed XML views or DOM documents.

QName and NOTATION lexical values use namespace bindings on their declaration,
including unprefixed values in a nonempty default namespace and the implicit
`xml` prefix. An instance's same-spelled prefix cannot rebind a default. A
scoped validation-context pointer selects declaration namespace lookup while
leaving instance document ownership, DTD ENTITY checks, identity bindings and
reader/SAX state intact. The pointer is restored on every return path.

Namespace lookup returns an explicit status and a short-lived borrowed URI.
Reader lookup uses the current node and checked namespace search, avoiding an
allocated lookup result that could conflate an allocation failure with an
unbound prefix. QName lexical splitting, namespace/local-name copies, value
construction and `xsi:type` dictionary insertion check every allocation.
Value constructors consume strings only on success; their callers release both
strings on failure. Deep copies check every owning string arm, including
numeric and binary values, and free partial value lists without touching the
original. Context-free public datatype validation retains its prior lexical-name
representation; contextual validation stores expanded names.

The correction has no Qore runtime dependency and adds no public module API or
I/O. Mutable state belongs to the current validation context or local owned
values. Traversal and storage are linear in lexical length or namespace depth.
Existing Qore entry/I/O cancellation boundaries remain in force.

CMake probes canonical actual-type defaults, declaration namespace identity and
QName allocation-error propagation independently. `AUTO` uses the private
checksum-pinned provider when the installed library fails; `SYSTEM` reports the
failed capability. The transformation runs after exact calendar ownership,
checks complete input/output hashes and preserves generated timestamps on an
unchanged reconfiguration. All transformation inputs are distributed.

`test/xml-element-defaults.qtest` and the reproducible Python matrix exercise all
three native APIs, rejection categories and unchanged XML views. The standalone
C test injects single and persistent allocation failures into default assessment,
QName/NOTATION conversion, type expansion and deep copies of heterogeneous value
lists. It verifies original ownership, scope restoration and successful recovery.
Pinned Xerces results are compared separately, with the PSVI interpretation and
calendar/NOTATION differences explicitly recorded in the test and evidence.
