# Identity declaration grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL schema construction checks identity declaration representation before XML
children are grouped. A per-reader frame table validates a single selector
followed by one or more fields, optional leading annotations, element ownership,
allowed attributes, required names and keyref QNames. The annotation helper
continues to own annotation placement, attributes and document-wide ID checks;
arbitrary annotation payload is ignored by the identity grammar helper.

Selector and field paths require a nonempty alternative on each side of `|`.
Optional initial descendant selection, dot steps, wildcard and qualified name
tests, and equivalent explicit child/attribute axes follow the XSD 1.0 subset.
Only a field's final step may select an attribute. XML whitespace can separate
tokens but cannot split a QName/name test or a double-slash token. Prefixes
resolve on the selector or field declaration itself; an unqualified XPath name
does not inherit the XML default namespace. These checks do not rewrite source
text or namespace declarations. A failed addition discards its local frame
table and the schema's existing transactional addition restores prior state.

For example, this declaration has a valid ordered selector and field:

```xml
<xs:unique xmlns:xs="http://www.w3.org/2001/XMLSchema" name="productCode">
  <xs:selector xpath="product"/>
  <xs:field xpath="@code"/>
</xs:unique>
```

Native component references have the separate QName whitespace-collapse rule.
The private libxml2 resolver validates the spelling, interns bounded slices
excluding surrounding XML whitespace, then resolves namespaces and components.
This applies to type, base, list item, reference, substitution and keyref
attributes. Default namespaces and chameleon target-namespace fallback retain
their prior behavior. The resolver checks dictionary allocation and uses the
status-returning namespace lookup so allocation of the implicit `xml` binding
cannot be misreported as an unbound prefix. All resulting strings remain owned
by the schema dictionary; no trim buffer or shared mutable state is introduced.

CMake probes normalized and invalid component QNames before selecting system
libxml2. Private source correction verifies both source hashes and preserves
build-tree timestamps on unchanged reconfiguration. Focused allocation tests
exercise only the resolver phase with one-shot and persistent failures, after
initializing builtin types, and release the test's last-error record between
trials. Valid inputs must report memory failure; invalid inputs may retain their
primary syntax error if diagnostic formatting itself cannot allocate.

Tests: `test/wsdl-identity-grammar.qtest`, `test/xml-component-qnames.qtest`,
`test/wsdl-notation-http.qtest`, the independent identity-grammar/component-QName
checkers, and `test/cmake/libxml2_component_qname_allocation.c`.

Normative sources: [XSD 1.0 identity representation and XPath subset](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cIdentity-constraint_Definitions),
[QName whitespace](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#QName).
