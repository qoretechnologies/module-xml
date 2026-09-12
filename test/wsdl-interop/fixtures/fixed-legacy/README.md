# Saved fixed-element provider before identity metadata

Copyright (C) 2026 Qore Technologies, s.r.o.

`provider.hex` is the exact hex output of `make_hex_string(provider.serialize())`
with WSDL from module-xml develop commit `46f73cd`, Qore 3.0.0/API 2.0 revision
`d66e2cd7e53d7ebe1eb76d52cf1fa75c2061cabe`. The provider is
`schema.getNativeDataProviderType("", "value")` for:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="value" type="xs:int" fixed="17"/></xs:schema>
```

The file is frozen input: do not regenerate it with current WSDL. It contains
the old declaration lexical/type graph and no computed fixed-value identity.
The regression restores it, checks 17, rejects 18, saves/restores it again and
checks concurrent first use. No credentials or external service data are stored.

SHA-256 (hex text, no trailing newline): `2477f2e5f193803bff3ceb0603f618ddf04d4306f3170790c656f89dccbd7a68`.
