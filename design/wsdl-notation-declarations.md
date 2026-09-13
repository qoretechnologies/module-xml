# WSDL notation declaration storage

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdSchema` retains notation identifiers in a separate expanded-name symbol space.
`XsdNotationInfo` contains `namespace_uri`, `local_name`, `public_id` and `system_id`.
An absent identifier is `NOTHING`; an explicitly empty identifier is `""`.
Names and identifiers use XSD whitespace collapse. Public identifiers are tokens,
not DTD public literals; system identifiers retain their relative URI spelling.
No external resource is fetched for either identifier.

The streaming grammar check validates notation attributes, names and IDs and permits
one optional XSD annotation. Existing schema-source handling rejects character data.
Foreign attributes remain legal. Notation declarations occupy their own symbol
space, so a type, element or attribute can have the same expanded name. Two notation
declarations with that name are an error, including names equal after normalization.

The parser collects declarations from the complete import/include graph before
publishing them to a shared `XsdNotationRegistry`. Chameleon declarations adopt each
including target namespace. Namespace-context copies share the registry, allowing
retained types to observe successfully added declarations. Schema construction must
finish before concurrent reads; concurrent mutation of one schema is unsupported.

Publication occurs before type finalization so declaration-dependent facet and
constraint processing can use the table. A failed addition restores the old table,
including through contexts retained before the addition. It also restores the
existing component, source and dependency registries. Registry replacement validates
a complete new map before assigning it.

`Serializable` reconstructs schemas from retained source/dependency bytes. Detached
namespace contexts serialize the registry directly. Reconstruction checks container
and field types, normalized names, XML characters, identifier presence and agreement
between each map key and the expanded declaration identity. Returned metadata hashes
have value semantics and cannot mutate the registry.

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' "
    "targetNamespace='urn:media'><xs:notation name='jpeg' "
    "public='image/jpeg'/></xs:schema>");
hash<XsdNotationInfo> jpeg = schema.nsc.getNotation("{urn:media}jpeg");
@assert(jpeg.public_id == "image/jpeg");
@assert(!exists jpeg.system_id);
```

The no-namespace lookup key is `"{}jpeg"`. Use an expanded key, including the empty
namespace, to keep lookup independent of declaration prefixes.

Requirements: [XSD 1.0 Part 1 §3.12](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cNotation_Declarations)
and [schema composition §4.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#composition).
The registry supplies declaration metadata; NOTATION instance conversion has its
separate acceptance assignment in the [P5 gap register](../test/wsdl-interop/p5-wsdl-notation-finding.md).
