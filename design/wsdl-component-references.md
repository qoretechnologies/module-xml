# WSDL component references and imported definitions

Copyright (C) 2026 Qore Technologies, s.r.o.

`WebService` checks component references before constructing messages, operations
and bindings. The ordered reader collects declarations by component kind and
expanded name, then resolves collected references after all documents in the import graph
have been read. Forward references therefore have the same behavior as references
to preceding declarations. The separate message, port-type and binding symbol
spaces prevent a reference from selecting a different component kind.

Input/output/fault messages, a binding's port type, a service port's binding,
and direct SOAP input/output headers and their headerfault messages are checked
in the XML element's namespace context. Unbound prefixes, malformed QNames, missing required attributes and
undefined expanded names raise `WSDL-ERROR`. An unprefixed QName uses the default
namespace, including an explicit empty default; `targetNamespace` does not supply
an implicit namespace for references. A matching local name in another namespace
cannot satisfy a reference.

The document target namespace uses XML Schema whitespace collapse in both the
declaration table and namespace container; the retained source bytes are unchanged.
The grouped source view preserves normalized QName attributes and optional
input/output names. Binding construction applies nested namespace scopes for
the operation, input/output and individual header, restoring each previous scope
on exit. Saved services reconstruct from retained source and perform the same
validation from the retained root and dependency bytes.

For example, a shipping binding may declare its own prefix for a header message:

```xml
<soap:header xmlns:orders="urn:partner-orders"
             message="orders:Authorization" part="token" use="literal"/>
```

The `Authorization` message must be declared in `urn:partner-orders`. Its prefix
need not be declared at the WSDL root, and it cannot borrow an `Authorization`
message declared in a different namespace. Declaration/reference tables belong
to the construction call and introduce no shared mutable state. Objects retain
only their namespace contexts and a compact mapping of expanded names to public
component keys.


The document catalog traverses `wsdl:import` edges before component construction.
Each document retains its original XML bytes, parsed view, namespace declarations,
full URI when available, and fallback directory. Imports require both
`namespace` and `location`; every edge checks the retrieved target namespace,
including repeated references to an already loaded resource. WSDL 1.1 imports
can contribute WSDL definitions or XSD schemas. Embedded and imported schemas
contribute to a common type environment and finalize after all documents have
been collected. WSDL-imported schemas share retained bytes and the per-resource,
per-namespace instantiation registry with XSD imports and includes, so reaching
the same schema through both languages does not duplicate its declarations. Messages, port types, bindings and services then compile in that
order, each under its own document namespace context. Compatibility options are
copied into those contexts.

The catalog uses a queue and a resource-key table, so cycles and diamond graphs
reuse already loaded documents. Resource keys omit fragments; non-file URI keys
retain queries. Local files use absolute escaped file URI keys, shared by the
absolute and localhost URI spellings. Roots supplied as XML without a source
URI can be recognized by source bytes and normalized containing directory. Retrieval first uses
retained dependency bytes, then `xsd_cache`; `async_only` raises
`WSDL-ASYNC-IMPORT` with the missing resolved key. Synchronous imports use the
existing location handler or `try_import`. The callback receives the original
unschemed reference when its resolved location names a local file. The resolved location still
identifies its cache entry and determines the base of nested dependencies.

Component identity is `(kind, namespace URI, local name)`. Duplicate expanded
names within one kind reject, including declarations spread across files. The
public message, port-type, binding and service maps expose one entry per component:
a local name when unique within that kind, otherwise `{namespace}local`.
`getMessage()`, `getPortTypeOperation()`, `getBinding()` and `getService()` also
accept an expanded name when the corresponding local name is unique. A bare
ambiguous local name cannot select a component. These lookup aliases are separate
from iterable maps, so services and operations are not enumerated twice.

`Binding::name` remains its XML local name. `getComponentKey()` returns the key
used to select it in the service and its operations. `SoapClient` carries that
key from the selected service port into request/response processing. Operations
retain expanded binding aliases through standalone serialization. Global
`getOperation(name)` retains its documented first-match search; callers selecting
a particular component use `getBindingOperation()` or `getPortTypeOperation()`.
The binding-specific lookup verifies that the selected operation has a concrete
operational binding under `Binding::getComponentKey()`. An operation declared
in the port type but omitted from that binding raises `WSDL-BINDING-ERROR`,
including empty bindings. This uses the operation's existing association map;
no second membership registry is maintained. A `NOTHING` binding argument keeps
global lookup, and port-type lookup still exposes abstract unbound operations.
SoapClient uses this check before serializing or sending a request.
For example:

```qore
WSOperation submit = service.getBindingOperation("{urn:orders}OrdersSoap", "submit");
WSMessage request = service.getMessage("{urn:orders}SubmitRequest");
```

SOAP RPC request wrappers use the operation's XML name. Response wrappers use
that name with the `Response` suffix. Abstract WSDL input/output labels identify
operation messages and do not override either wire name. Serialization and
deserialization use the same rule for detached operations and reconstructed
services. This keeps explicitly named abstract messages from changing dispatch
or the RPC body shape.

SOAP RPC wrapper namespaces come from the selected input or output `soap:body`
`namespace` attribute, with the existing operation target namespace fallback when
absent. Deserialization checks the expanded wrapper identity before converting
its values. The binding and port-type document namespaces may differ.

`getWSDL()` and `getWSDLHash()` describe the original root bytes. `getHash()`
fingerprints the retained source graph: root source, sorted WSDL and XSD
resource keys and content digests, sorted redirect aliases, and ordered added-schema source records.
Services without dependencies, aliases or added sources retain the root SHA-256 digest.
Successful schema additions invalidate the cached fingerprint. This identifies
sources, not option-dependent semantic equivalence.

Construction and schema extension finish before a service is shared for concurrent
use. Temporary document and namespace state restores on every exit. Retained
source bytes support offline reconstruction; callbacks are not serialized, and
saved services rebuild their component keys from their source graph.

## Abstract operation identities

Operations retain their XML name and authored nullable `input_name` and
`output_name` fields. `getMessageExchangePattern()` reports the ordered WSDL
message exchange. `getInputName()` and `getOutputName()` apply effective defaults:

| Pattern | Input default | Output default |
| --- | --- | --- |
| One-way | operation name | absent |
| Notification | absent | operation name |
| Request-response | name + `Request` | name + `Response` |
| Solicit-response | name + `Solicit` | name + `Response` |

Explicit labels override these defaults. The pinned WSDL schema's NCName rules
normalize labels before identity comparison. Two declarations with the same
operation name and effective input/output labels reject as duplicate signatures.
An operation requires at least one abstract input or output message.

Each port type keeps a map of selection keys and an index of XML names to
candidate declarations. Unique XML names remain their existing lookup keys.
Overloads use `name(input,output)`, with an empty slot for an absent message;
NCName labels cannot contain the delimiters. `getOperationNames()` preserves
source order and includes these keys. `WSOperation::getSelectionKey()` returns
the assigned key; `getSignatureKey()` returns the full effective signature.
`WSOperation::name` remains the XML name used for RPC wrappers and default actions.

For example, `lookup(ById,ResultId)` and `lookup(ByName,ResultName)` can coexist
in one port type. Binding input/output labels narrow their candidate set;
omitted labels impose no constraint. A missing or ambiguous binding target
rejects before the binding is assigned. Public binding lookup narrows candidates
by actual binding membership before checking ambiguity. A bare `lookup` thus
works for a binding containing only one of these operations and rejects for a
binding containing both. Global lookup keeps the first matching port-type rule,
while ambiguous bare names within that port type reject.

Standalone serialization retains message order and the assigned selection key.
Service reconstruction rebuilds the indexes from retained WSDL bytes. A legacy
standalone operation with no order metadata can infer one-way/notification from
message presence; with both messages it reports unknown order. Authored labels
and the output `Response` default remain available. Deriving an omitted input
label in that last case raises `WSDL-OPERATION-ERROR` and requires reloading the
WSDL, because `Request` and `Solicit` cannot be distinguished. Wire serialization
does not depend on that accessor. Invalid saved pattern values or pattern/message
presence mismatches reject during reconstruction.

These rules follow [WSDL 1.1 operation names and bindings](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_names).
The independent WSDL4J oracle verifies defaults through `PortType.getOperation`
and observes resolved binding targets, rejecting its undefined placeholders.

## RPC calls with no parameters

An RPC message emits the operation wrapper even when it has no parts. Its
expanded wrapper key must be present on input, including when its native XML
value is `NOTHING`. An empty or whitespace-only wrapper decodes to an empty
hash. Missing/wrong wrappers, extra parameters and significant wrapper text
reject. Fault detail keeps its separate unwrapped path. Both SOAP versions,
request/response directions, literal/encoded bodies and saved operation handles
use the same wrapper-presence rule.

Document messages with no body parts emit an empty SOAP Body and decode to an
empty native hash or retained body-part map. A missing Body still rejects.
Header-only messages use an abstract zero-part message with separately bound
headers; an operation with no abstract input/output declaration is invalid.
