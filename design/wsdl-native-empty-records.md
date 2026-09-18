# Empty native complex records

Copyright (C) 2026 Qore Technologies, s.r.o.

With `preserve_types=True`, a present non-simple, non-array, non-mixed complex
value decodes as an empty hash when it has no fields. Element parts and type parts
share this rule in `XsdDocumentValueHelper`; namespace declaration placement does
not change the result. Content and attribute validation precede normalization.
A selected derived type retains its ordinary `^type^` / `^val^` wrapper around
the empty record. Explicit nil uses `XsdNilValue`; omission remains separate.
The ordinary decoder's existing empty projections remain compatible.

Native provider graphs use a hash provider for empty complex records, including
bare `complexType`, empty sequence/all and inherited empty content. The complex
type's value provider is mandatory: optionality belongs to the receiving element
occurrence and its nil contract. An empty content model does not make the element
absent. Optional/mandatory copies, soft providers and saved provider graphs retain
these distinctions. Ordinary providers retain their existing projection policy.

A native provider with a fieldless complex record obtains its sample from the
schema helper and retains an empty hash. Generic hash samples containing invented
keys cannot describe an empty schema type. Complete message provider examples
return validated, normalized part maps; a zero-part message returns an empty map.
This also applies the declared scalar precision to generated numeric examples.

For example, an empty request element uses `{"body": {}}` with the corresponding
WSDL part name. A native message provider accepts that record and its example can
be passed to the operation serializer. Missing mandatory values and nonempty
content in an empty type reject; a nillable element can instead receive an explicit
`XsdNilValue` without conflating nil with the empty record.
