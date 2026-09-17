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
For example:

```qore
WSOperation submit = service.getBindingOperation("{urn:orders}OrdersSoap", "submit");
WSMessage request = service.getMessage("{urn:orders}SubmitRequest");
```

SOAP RPC wrapper namespaces come from the selected input or output `soap:body`
`namespace` attribute, with the existing operation target namespace fallback when
absent. Deserialization checks the expanded wrapper identity before converting
its values. The binding and port-type document namespaces may differ.

`getWSDL()` and `getWSDLHash()` describe the original root bytes. `getHash()`
fingerprints the retained source graph: root source, sorted WSDL and XSD
resource keys and content digests, and ordered added-schema source records.
Services without dependencies or added sources retain the root SHA-256 digest.
Successful schema additions invalidate the cached fingerprint. This identifies
sources, not option-dependent semantic equivalence.

Construction and schema extension finish before a service is shared for concurrent
use. Temporary document and namespace state restores on every exit. Retained
source bytes support offline reconstruction; callbacks are not serialized, and
saved services rebuild their component keys from their source graph.
