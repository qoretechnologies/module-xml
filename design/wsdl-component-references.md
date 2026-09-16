# WSDL component references within a document

Copyright (C) 2026 Qore Technologies, s.r.o.

`WebService` checks component references before constructing messages, operations
and bindings. The ordered reader collects declarations by component kind and
expanded name, then resolves collected references after the complete document
has been read. Forward references therefore have the same behavior as references
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
validation. Public document-local lookup names remain unchanged.

For example, a shipping binding may declare its own prefix for a header message:

```xml
<soap:header xmlns:orders="urn:partner-orders"
             message="orders:Authorization" part="token" use="literal"/>
```

The `Authorization` message must be declared in `urn:partner-orders`. Its prefix
need not be declared at the WSDL root, and it cannot borrow an `Authorization`
message declared in a different namespace. Declaration/reference tables belong
to the construction call and introduce no shared mutable state.
