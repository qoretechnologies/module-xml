# WSDL declaration identity

Copyright (C) 2026 Qore Technologies, s.r.o.

`WebService` accepts a document whose root is the expanded name
`{http://schemas.xmlsoap.org/wsdl/}definitions`. The namespace URI determines
identity; a matching local name in another namespace is not a WSDL root.

Before component construction or schema dependency retrieval, an `XmlReader`
pass checks declaration names and duplicate declarations in the core WSDL tree.
Names are XML NCNames with XML Schema whitespace collapse. The grouped source
view retains those normalized names, so duplicate detection and public lookup
use the same identity. Namespace aliases do not introduce new symbol spaces.

Messages, port types, bindings and services each have their own global name
space. A message's parts and a service's ports each have a separate local scope;
fault names belong to their operation. An operation name alone is not treated
as unique because WSDL permits overloads. The declaration validator does not
traverse documentation or foreign extension payloads to collect declarations.

Invalid roots, absent/invalid required names and duplicate declarations raise
`WSDL-ERROR`. Validation state belongs to one construction call, so a failed
construction cannot contaminate a later service. Saved services rebuild from
their retained WSDL and apply the same checks.

Empty port types and services are valid named components. Their operation and
port maps are initialized to empty hashes and published before child traversal.
Lookup, reports and serialization therefore preserve empty components.

For example, a contract inventory can inspect an abstract service before its
ports are added by the producer:

```qore
WebService service('<definitions xmlns="http://schemas.xmlsoap.org/wsdl/">'
    + '<service name="PartnerOrders"/></definitions>', {"async_only": True});
hash<ServiceInfo> orders = service.getService("PartnerOrders");
@assert(orders.port.empty());
```

`test/wsdl-declaration-identity.qtest` covers document identity, required names,
namespace aliases, normalized names, distinct symbol spaces, duplicate local
names, ignored documentation payloads, empty components and saved graphs.
