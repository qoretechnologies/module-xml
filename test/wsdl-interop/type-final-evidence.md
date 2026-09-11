# P5-02 type final specification and validator evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The implemented criterion is construction-time type `final` enforcement,
including applicable source `finalDefault` values. Instance `block` restrictions,
element substitution exclusions, abstract dispatch and complete dynamic type
retention remain P5 work. No P5 phase-completion claim follows from this increment.

The previous WSDL parser deleted simple/complex declaration attributes and never
retained schema derivation defaults. Its late resolver consequently accepted
restrictions of final bases, lists of final item types, unions of final atomic/list
members, and prohibited complex derivations. The fix captures effective component
properties during source parsing and checks the resolved dependencies. Tests
exercise forward resolution, originals/copies, imports, chameleon inclusions,
explicit empty overrides, builtin identity, invalid-token diagnostics, error
recovery, concurrent readers and legacy array adapter metadata.

Normative requirements are [XSD 1.0 Datatypes 4.1.1–4.1.2.3](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/)
and Structures [3.14.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-restricts)
and [3.4.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-ct-extends).
The [schema for schemas](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#schema)
prohibits explicit `final` on anonymous simple types. The
[second-edition errata](https://www.w3.org/2004/03/xmlschema-errata)
contain no amendment to these controls. The matrix deliberately uses XSD 1.0
composition and component constraints; it does not substitute XSD 1.1 rules.

The independent matrix enumerates **87 schemas / 174 SOAP descriptions**, including
44 valid and 43 invalid schema models. In each execution mode its **438 rows**
contain **86 required construction errors** and **352 valid output documents**.
Valid cases test both actual bindings, both directions and originals/copies;
invalid cases fail construction before any binding can be used. The worker also
compiles every schema with the native reader and requires `XSD-SYNTAX-ERROR` for
invalid schemas. Exact native values and expanded envelope/payload names are
asserted independently of output schema validation. The inventory records hashes
for every generated source, description and validator reference derivative.

The following boundaries require specification adjudication:

| Cases | Normative result | lxml 6.1.1 / libxml2 2.12.10 | Xerces-J 2.12.2 |
| --- | --- | --- | --- |
| `anonymous-default-restriction`, `-list`, `-union` | Invalid: anonymous base/item/member inherits the source default | Incorrectly accepts | Incorrectly accepts |
| `simple-content-restriction-final` | Invalid: synthesized simple content restricts a final base | Rejects | Incorrectly accepts |
| `anonymous-explicit-simple` | Invalid: local simpleType cannot have final | Rejects | Incorrectly accepts |
| `simple-extension-default-extension`, `-#all` | Valid: irrelevant extension is filtered from simple final | Accepts | Incorrectly rejects |
| `composed-union`, `composed-restricted-union` | Valid: constraints use the actual atomic/list members after XSD 1.0 composition | Accepts | Incorrectly rejects |

For the last row, the interpretation follows the explicit component mapping:
Datatypes 4.1.2.3 replaces each nested union with its member definitions, and
Structures 3.14.6 checks the final sets of those resulting member definitions.
The replaced union's own properties do not transfer to those members. This is
the same XSD 1.0 replacement rule already used for union-level facets. Direct
restriction of a final union and list derivation from a final union remain
subject to that union's own restriction/list exclusions and have negative tests.
For simple extension, Structures 3.14.2 explicitly identifies its duplicated
mapping as non-normative; its extra extension token does not override the
normative Datatypes mapping and its note about filtering irrelevant defaults.

These validator verdicts are recorded as disagreements, not conformance passes.
For valid schemas incorrectly rejected by Xerces, output-only reference derivatives
remove the irrelevant extension default (retaining restriction/list/union), or
remove `final="union"` from the union definition replaced during composition.
The original bytes still undergo native construction, WSDL conversion and lxml
validation. Reference derivatives are separately hashed; they establish output
value/content validity and do not replace the normative classification of the
original construction. Invalid schemas accepted by an oracle never generate
passing message rows.

Root causes in the dependency implementations are independently reproducible:

- libxml2 2.15.4 `xmlSchemaParseSimpleType()` applies default flags only in its
  global-type branch. The private correction adds the same three flag assignments
  to the anonymous branch. It preserves source hashes and allocation behavior.
  A 12-case configure probe rejects the uncorrected dependency, including a
  backport containing every preceding correction. AUTO selects the fixed private
  build; SYSTEM rejects the uncorrected one; a fully fixed backport stays SYSTEM.
- Xerces `XSDSimpleTypeTraverser.findDTValidator()` checks final only for QName
  references, while inline definitions arrive through `traverseLocal()`. The synthesized
  simple-content restriction likewise reaches the datatype factory without a
  final check on its simple base. It
  checks a QName-named union before expanding its members. Its `getSimpleType()`
  also passes the schema default without filtering extension. Finally,
  `XSAttributeChecker` registers `final` for local simpleType declarations.
  These independent-oracle defects are retained in the expected-verdict matrix.

The inspected official [Xerces 2.12.2 source artifact](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar)
has SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
The execution JAR remains the previously pinned repository artifact. No external
validator behavior is silently corrected or counted as a module success.
