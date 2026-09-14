# Retained XSD identity-constraint components

Copyright (C) 2026 Qore Technologies, s.r.o.

Element declarations retain immutable `XsdIdentityConstraint` objects. Each
contains its schema target namespace, normalized local name, category, selector,
ordered fields and the expanded referenced component name for a keyref. A local
unqualified element still declares its identity components in the schema target
namespace. Element references expose the global declaration's constraints.

`XsdIdentityPathHelper` compiles the restricted XSD 1.0 XPath language into typed
alternatives and steps. The same compiler validates the ordered reader grammar
and builds retained metadata. Steps distinguish self, child and attribute axes,
exact expanded names, namespace wildcards and unrestricted wildcards. Each
alternative records an initial descendant selection. Unqualified name tests
select no-namespace names regardless of the default XML namespace. Each selector
and field uses its own declaration scope; only referenced prefixes are retained.

Construction queues definitions from global and local elements, including unused
types, unused groups and zero-occurrence particles. Shared group uses reuse the
same declarations. Once imports, includes and type finalization are complete,
the resolver builds a complete candidate map. It rejects duplicate component
names, missing keyref targets, keyref-to-keyref references and unequal field
counts before publishing the map. Incremental additions restore the previous
registry with the other schema state on failure. Publication is a construction
operation and must finish before concurrent readers use the graph.

Definitions contain values and compiled paths, with no element, namespace or
registry backlinks. Serializable definitions rebuild their transient paths from
validated portable metadata. The registry serializes metadata rather than
referenced definition objects, so validation during restoration does not depend
on object hook order. Detached elements and namespace contexts retain this
information; saved schemas reconstruct it from their original source documents.

For example, inspect a catalog's item-code definition before exposing its schema:

```qore
XsdElement catalog = schema.getElement("urn:catalog", "catalog");
foreach XsdIdentityConstraint constraint in (catalog.getIdentityConstraints()) {
    printf("%s: %s, %d fields\n", constraint.getExpandedName(),
        constraint.getCategory(), constraint.getFieldPaths().size());
}
```

These objects describe declarations and validate their component relationships.
They do not themselves evaluate instance tuples. Tests are in
`test/wsdl-identity-components.qtest` and the authored component fixture matrix.
The governing requirements are XSD 1.0 Structures Second Edition
[§3.11.1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cIdentity-constraint_Definitions)
and [§3.11.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#c-props-correct).
