# Selected WSDL binding membership

Copyright (C) 2026 Qore Technologies, s.r.o.

`WebService::getBindingOperation(binding, operation)` previously looked up only
in the binding's abstract port type. It could return an operation omitted from
the requested concrete binding. The local/qualified and imported regression
cases fail on `0c72ca6` with that behavior; the baseline log is retained in the
validation inventory.

The lookup now validates `Binding::getComponentKey()` through the operation's
existing `getBinding()` method before returning. This keeps the established
`WSDL-BINDING-ERROR` for an operation without that binding. Unknown port-type
operations still raise `WSDL-OPERATION-ERROR`. A NOTHING binding retains global
lookup, and `getPortTypeOperation()` still exposes abstract unbound declarations.
There is no new membership map or mutation.

This reflects the distinction between abstract port types and concrete bindings
in [WSDL 1.1 section 2.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_bindings).
The durable implementation is documented in
[component references](../../design/wsdl-component-references.md).

The focused test covers three cases and 134 assertions: complementary SOAP 1.1
and SOAP 1.2 bindings, an empty binding, unbound operations, local and expanded
names, colliding imported names, missing operations/bindings, saved services,
and successful reuse after failed lookup. SoapClient produces valid requests
for its selected service port and rejects omitted operations before a request
can be sent. The broad Qore gate includes actual SOAP peer exchanges.

The broader gate exposed an existing fixture mismatch: test/soap.qtest selected
postForm from GET binding b2, although test/test.wsdl binds it only under POST
binding b3. The test now selects b3 and asserts that b2 rejects postForm. Its
POST body, method and deserialization assertions are unchanged.

See [validation](P6-11-validation.json) and the
[62-check audit](audits/P6-11-binding-selection.md). No native code changes or
Valgrind run are required. Corpus classification does not depend on this public
selection guard; P6-10's semantic corpus results remain the baseline.

P6 still requires overloaded operation identities, abstract input/output defaults
and the remaining concrete binding matrix. This increment does not change global
first-match operation lookup or RPC wrapper names. P7–P9 remain open.
