# Native document ID bindings

Copyright (C) 2026 Qore Technologies, s.r.o.

Native schema validation records the selected computed ID and IDREF values in a
validation-context-owned hash table. It checks every token when the validation
root closes: each must identify exactly one element. An ID attribute identifies
its owner; an ID-valued child identifies its parent. Repeating a token for the
same owner is valid; using it for different owners is invalid. A root with only
ID-valued simple content has no parent inside the scope and is invalid. These
rules follow [XSD 1.0 cvc-id and section 3.15.5](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-id);
the Working Group confirms the root case in
[issue 9922](https://www.w3.org/Bugs/Public/show_bug.cgi?id=9922).

Values are recorded after datatype selection and facets succeed. Failed union
member trials have no registry or DOM ID side effects. Lists contribute their
selected identity items; a union selecting string contributes no identity even
when another member is IDREF. Defaulted attributes, simple content and assessed
wildcards participate. Nilled values and skipped wildcard content contribute no
value. The table accepts forward references and is checked only after traversal.

Each active element receives a monotonically assigned owner number. No pointer
to a recycled reader/SAX node is retained. The context frees the table on normal
completion, rejection, allocation failure and destruction; reuse resets the
counter. Different validation contexts share no mutable registry state. The
counter checks overflow. Storage grows with the number of distinct tokens;
recording uses hash lookup and root closure scans the table once.

DOM attribute ID lookup remains available after successful datatype selection.
The existing per-item IDREF attribute marker remains independent of list length.
The DOM table is not the validation registry: when validating a subtree, IDs
outside it cannot satisfy references, and an outside DOM entry does not make an
otherwise valid inside binding duplicate. Public standalone datatype conversion
is unchanged. The private patch changes no public headers or Qore API.

For a schema declaring `item/@id` as ID and `item/@ref` as IDREF, this document is
valid, including its forward reference:

```xml
<value><item ref="shipment17"/><item id="shipment17"/></value>
```

Removing the second item leaves an unresolved reference; adding another item
with `id="shipment17"` creates two distinct owners and is invalid. These cases
are executable in `test/xml-id-bindings.qtest` through conversion, DOM validation
and streaming validation. The error categories are `PARSE-XML-EXCEPTION` for
conversion/reader and `XSD-ERROR` for `XmlDoc::validateSchema()`.

The behavior probe includes DOM, streaming, SAX, context reuse, subtree scope,
nil and DOM metadata tests. AUTO falls back to the checksum-pinned private
libxml2 when the installed provider fails; SYSTEM rejects it. The private
build-tree correction verifies both source hashes, leaves the fetched source
unchanged, and preserves timestamps on repeated configuration. Existing Qore
entry and I/O cancellation boundaries remain; no per-item runtime cancellation
hook is added inside the independent libxml2 C library.

See the [regressions and adjudicated validator differences](../test/wsdl-interop/native-id-bindings-evidence.md).
