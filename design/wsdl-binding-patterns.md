# WSDL binding interaction patterns

Copyright (C) 2026 Qore Technologies, s.r.o.

Abstract port types retain all four WSDL 1.1 interaction patterns. Concrete
standard SOAP 1.1, SOAP 1.2 and HTTP GET/POST bindings support one-way and
request-response. Notification and solicit-response require binding extensions
that these standard implementations do not provide. Binding construction rejects
those patterns with `WSDL-ERROR` before publishing an operational binding or
performing a service call. Abstract discovery remains available independently.

`WSOperation::addBinding()` applies the same restriction to manual registration
of `SoapBinding` and `HttpBinding` instances, raising `WSDL-BINDING-ERROR` before
changing either binding map. Other `OperationalBinding` implementations can
define their own interaction patterns. Restoring a standalone operation validates
its standard bindings and raises `DESERIALIZATION-ERROR` for a known unsupported
pattern. Source-backed service restoration repeats construction validation.

For example, an output-only notification operation can be inspected and saved as
abstract metadata, but cannot be assigned the module's standard SOAP binding.
A one-way input operation can be bound and invoked through SoapClient/SoapHandler;
it sends the input without expecting an application response message.

Older standalone graphs with both messages but no message-order metadata retain
the documented unknown pattern. Named legacy calls remain available; reload the
original WSDL to recover and validate the original order. Output-only legacy
graphs identify notification unambiguously and reject standard bindings.

See [operation identity](wsdl-component-references.md) for signature selection
and [WSDL 1.1 section 2.4](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_porttypes)
for the distinction between abstract patterns and standard binding support.
