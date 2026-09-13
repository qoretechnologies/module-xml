# WSDL empty-element default values

Copyright (C) 2026 Qore Technologies, s.r.o.

An explicitly present element with no character or element children uses its
default or fixed constraint. Missing occurrences remain subject to particle
requirements; optional missing children are not invented. Comments and empty
CDATA do not prevent default application. Whitespace characters do. Nil follows
its separate receiving-declaration rules.

The approved interpretation assesses the declaration's canonical lexical value
under the actual selected type. Original declaration values, spellings and
namespace bindings remain available through `getValueConstraint()`. For example,
a boolean-first `boolean|string` declaration with `fixed="1"` has original
boolean value `True`. An empty occurrence with `xsi:type="xs:string"` receives
the string `"true"`. The decision and specification/reference differences are
recorded in [the decision record](../test/wsdl-interop/default-identity-investigation.md).

QName text supplied by a declaration uses that declaration's namespace bindings.
Attributes on the instance retain their own bindings. A scoped lexical carrier
passes only the simple value into its declaration scope; complex attributes are
validated before that scope is entered. Mixed content keeps its ordered text
fragments and uses their existing scoped representation. Document identity and
entity checks still belong to the instance validation context.

## Preserving empty occurrences

Legacy decoding remains the default (`preserve_types=False`) and returns the
converted native value. Explicit preservation returns `XsdDefaultValue` with the
complete native value, including complex-content attributes. A selected-type
wrapper, when required, surrounds this carrier. The carrier is serializable and
has no mutators; container values returned by `getValue()` follow Qore's ordinary
value-copy semantics.

For an order quantity declared with `default="+017"`:

```qore
XsdDefaultValue quantity(17);
XsdXmlValue wire = schema.serializeXmlValue("", "quantity", quantity);
# The quantity element is present and empty; its declaration supplies 17.
```

For the fixed boolean/string example, a receiving element accepts:

```qore
hash<auto> status = {
    "^type^": new XsdQNameValue(XSD_NS, "string"),
    "^val^": new XsdDefaultValue("true"),
};
```

Writing explicit `true` text would fail the original boolean fixed-value
comparison under the selected string type. Retaining the empty occurrence avoids
changing its value-constraint assessment. Legacy decoding intentionally does not
retain this state; applications requiring that round trip opt into preservation.
`XsdXmlValue` continues to retain complete original XML when lexical fidelity is
needed, including comments.

Serialization checks the supplied native value and attributes with the selected
type, then compares its typed identity with the canonical constraint assessed
under that type. Only matching values may become empty XML. The expected-value
comparison suspends duplicate identity registration, while the actual supplied
value contributes normal document bindings. Children, invalid attributes,
unconstrained receivers and mismatching values reject. Temporary scopes restore
their predecessors on success, custom exceptions and cancellation.

## Providers

`XsdDefaultDataType` wraps an ordinary constrained element provider. It preserves
native type names, tags, record/list metadata, examples and ordinary conversion,
and adds the explicit carrier to accepted/returned type metadata. Optional,
mandatory, soft and saved variants retain receiving-element validation. Selected
type providers also accept carriers inside their existing type wrappers. Repeated
elements retain an outer occurrence list, distinct from list-valued defaults.

`SoapClient` can return preserved values with `preserve_types=True`; handlers can
enable the corresponding native decoding mode. `SoapDataProvider` currently uses
ordinary request metadata and legacy response decoding. It accepts a default
carrier for a declared value; selected-type wrappers and the `preserve_types`
request option are not exposed by that provider's existing API.

Tests cover actual-type lexical restrictions, saved schemas/providers, empty
strings/lists, QName scopes, mixed content, presence/nil distinctions, document
IDREF closure, malformed saved state, custom exceptions and cancellation. The
HTTP suite exercises both SOAP bindings with bounded requests and deterministic
queue observations. The independent matrix retains pinned-Xerces disagreements
explicitly. WSDL NOTATION and key/unique/keyref remain separately tracked P5 work.
