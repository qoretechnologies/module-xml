# Selected complete XML elements

Copyright (C) 2026 Qore Technologies, s.r.o.

Complete schema elements and document-style WSDL parts use the concrete
declarations admitted by their substitution head. The selected declaration
supplies the root name, type, attributes, value constraints and nillability.
Child particles already express this identity through their member field names;
see [child substitution](wsdl-substitution-particles.md).

## Native representation

A substituted complete element has two members:

```qore
hash<auto> quantity = {
    "^element^": new XsdQNameValue("urn:orders", "itemCount"),
    "^val^": 17,
};
```

`^element^` must be an `XsdQNameValue`. The receiving declaration resolves its
namespace URI and local name against the concrete substitution group. Prefix
spelling is immaterial. The wrapper requires both keys, permits no extra keys
and cannot contain another element wrapper directly inside `^val^`.

Ordinary values continue to use the declared root. Decoding adds the element
wrapper only when the instance root differs from that declaration. This
retention is automatic: the previously rejected alternate root has no legacy
native representation to preserve. A retained `XsdXmlValue` carries its own
root identity and does not need a wrapper.

An explicit selected type remains an independent inner wrapper:

```qore
hash<auto> quantity = {
    "^element^": new XsdQNameValue("urn:orders", "itemCount"),
    "^val^": {
        "^type^": new XsdQNameValue(XSD_NS, "int"),
        "^val^": 17,
    },
};
```

Use operation decoding's `preserve_types=True` argument when retaining explicit
`xsi:type` choices. The member's type is the receiving base for that inner
selection, including its effective block constraints. See
[native type values](wsdl-native-type-values.md). Both QName carriers and their
containing values survive `Serializable` storage and rebind in the receiver.

## Conversion boundaries

`XsdSchema::serializeXmlValue()` accepts the element wrapper and emits the
selected global root, including a default-namespace reset for a member with
no namespace. Low-level `XsdElement::serializeValue()` still converts the
contents of a known element; it does not replace a caller's outer XML key.

`XsdElement::validateXmlValue()` accepts admitted concrete member roots and
validates against the selected declaration. The retained carrier remains
unchanged, including its lexical text and XML context.

Document-style SOAP request and response conversion applies the same rule to
each body and header part. A single part accepts a bare element wrapper, a
WSDL part wrapper, an element-name wrapper or a message/part wrapper. Explicit
empty values under part and message keys retain their presence. Empty and nil
substitution values still carry `^element^`, even when their native value is
`NOTHING`.

### Matching unordered parts

WSDL 1.1 [section 2.3](https://www.w3.org/TR/wsdl.html#_messages) and
[section 3.5](https://www.w3.org/TR/wsdl.html#_soap:body) do not define an order
for document-style parts. Instance expanded names and the admitted member
sets therefore determine ownership. Selecting the first matching name can
consume a member needed by a narrower part.

The matcher builds a bipartite graph from parts to supplied element
occurrences. Iterative augmenting paths produce a complete assignment. An
alternative edge to an unused occurrence or an alternating cycle proves
that another assignment exists. A topological traversal checks for such
cycles without retrying every assignment.

For `P` selected parts, `N` input occurrences and `E` candidate edges, matching
takes `O(P * E)` worst-case work and `O(P + N + E)` storage. Candidate indexing
also visits each admitted expanded name once. Uniqueness checking is linear
in the graph size. No recursion, occurrence-count expansion or exponential
search is used. Qore loop cancellation applies in every execution mode.

Missing values, duplicate singleton occurrences and ambiguous assignments
raise `SOAP-DESERIALIZATION-ERROR`. Output selection is checked before a
message is returned; ambiguity raises `SOAP-SERIALIZATION-ERROR`. For example,
parts referencing `head` and `quantity` can unambiguously receive `amount` and
`quantity`. Two `quantity` occurrences cannot identify which value belongs to
which part. The matcher does not invent an ordering convention for that wire
message.

Header assignments consider all bound header declarations together. Unbound
headers remain separate in the retained message carrier. A concrete member
and a sibling member cannot both satisfy one header part. Native and retained
serialization prevent duplicate selected header roots from overwriting one
another.

## Providers, samples and reconstruction

`XsdElementDataType` describes the complete native value of a head with
substitution alternatives. `WSMessage::getDataProviderType()` supplies it for
such parts, including in the ordinary provider mode. The explicit
`XsdSchema::getNativeDataProviderType()` factory also supports nested selected
types. Ordinary child providers keep their existing field representation.

`getSelectedElementType(XsdQNameValue)` returns a member's native value
provider. `getInfo()` presents the declared native form when usable and a
wrapper alternative for each admitted concrete element, with exact QName
choices and member value metadata. Soft conversion changes values through
the selected member's provider, preserves the wrapper, and still enforces
schema constraints. Optional and mandatory copies retain the same schema
graph. Finite field choices compare the underlying value without discarding
element or type identity.

The provider snapshots its admitted element alternatives at construction.
Later schema additions do not change an existing provider's accepted members
or metadata. Create a new provider to include those additions. The snapshot
survives provider reconstruction even if the original head has since acquired
additional members.

Native and XML samples choose a concrete member for an abstract head. They
prefer members with concrete declared types. A head with no concrete
instance declaration raises `XSD-SAMPLE-ERROR`.

When reconstructing a `WebService`, the inline WSDL schema is rebuilt before
schemas subsequently supplied through `addSchemaString()`. Those schemas can
import the inline declarations. Successful additions refresh message type
maps; failed additions retain the existing maps. Additions must precede
concurrent use, as specified by `XsdSchema`.

## Example

An order system can store a quantity through an abstract schema head while
retaining the concrete integer member used by its partner:

```qore
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
    'xmlns:o="urn:orders" targetNamespace="urn:orders">'
    '<xs:element name="quantity" type="xs:decimal" abstract="true"/>'
    '<xs:element name="itemCount" type="xs:int" substitutionGroup="o:quantity"/>'
    '</xs:schema>');
hash<auto> quantity = {
    "^element^": new XsdQNameValue("urn:orders", "itemCount"),
    "^val^": 17,
};
AbstractDataProviderType provider = schema.getNativeDataProviderType("urn:orders", "quantity");
auto checked = provider.acceptsValue(quantity);
XsdXmlValue xml = schema.serializeXmlValue("urn:orders", "quantity", checked);
@assert(xml.getNamespaceUri() == "urn:orders");
@assert(xml.getLocalName() == "itemCount");
@assert(schema.getXmlDataProviderType("urn:orders", "quantity").acceptsValue(xml) === xml);
```

## Verification

`test/wsdl-substitution-roots.qtest` covers complete roots, member-specific
conversion, both actual SOAP bindings and directions, body/header ownership,
provider metadata and reconstruction, empty/nil members, imported colliding
names, selected types, exhaustive small assignments, a larger overlapping
graph, cancellation and concurrent reuse.

`test/wsdl-substitution-root-http.qtest` runs ten real local HTTP exchanges
through `SoapClient`, `SoapHandler` and `SoapDataProvider`, covering automatic
root retention, optional type capture, saved native providers and retained XML
lexical values for SOAP 1.1 and SOAP 1.2.

`test/wsdl-interop/test_substitution_roots.py` checks 34 schemas and 116
documents against lxml and pinned Xerces. Each independent input and output
is placed inside a schema witness referencing the WSDL head: validating the
member as a standalone global root alone would not test substitution
eligibility. Existing supporting-validator block omissions remain explicit
normative negatives. The matrix checks typed values, expanded root names,
native/provider equality and retained output in both directions and after
reconstruction.

The SOAP 1.2 HTTP contract explicitly sets `soapActionRequired="false"` and
includes requests without an action, following the
[binding extension's operation rule](https://www.w3.org/submissions/2006/SUBM-wsdl11soap12-20060405/).
Handler registration obtains admitted member request names from document body
parts. The selected binding then validates the full expanded root name.
