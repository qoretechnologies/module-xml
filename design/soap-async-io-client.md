# SOAP async I/O client

Copyright (C) 2026 Qore Technologies, s.r.o.

`SoapClientIo` is the async I/O SOAP client. It is a separate module from `SoapClient` rather than a
replacement for it, following the same pattern as `XmlRpcClientIo` and `WebDavClientIo`: the legacy
client stays available and unchanged, and new code can adopt the async transport without a migration.

`SoapClient` publicly inherits `HTTPClient`, so every `HTTPClient` method is part of its API. Changing
its transport would remove that surface from callers, including `SalesforceSoapClient` and
`SoapConnection` in this repository. `SoapClientIo` therefore composes
`HttpClientIo::HttpClientConnectionManager` instead of inheriting any client class, which is also why
it exposes a deliberately small API rather than re-exporting a transport.

## What is shared and what differs

Only the transport differs. Both clients drive the same `WSDL::WebService` model and the same
transport-independent machinery: `WSOperation::serializeRequest()` builds the request, and
`WSDLLib::parseMultiPartSOAPMessage()`, `WSDLLib::parseSOAPMessage()`,
`WSDLLib::validateSOAPEnvelope()`, `WSDLLib::validateSOAPMediaType()`,
`SoapProcessingNode::processMessage()` and `WSOperation::deserializeResponse()` decode the response.
A service that works with one client works with the other, and envelope validation, mandatory-header
processing, role targeting, fault grammar, native and retained values and type preservation behave
identically because they are literally the same code.

The connection manager reports a response as a `HttpClientResponseInfo` with lowercase headers,
whereas the shared decoders expect an `HTTPClient`-shaped response hash. `SoapClientIo` adapts
between them in one place, merging the response headers to the top level alongside `body`,
`status_code` and `content-type`, so the decoders see the shape they already handle.

A SOAP fault is recognized before any HTTP failure is reported: on status 400 or 5xx the client
parses the body and looks for an envelope-qualified `Fault` by expanded name, and only raises a
transport error when the response is not a fault. That ordering matches `SoapClient` and keeps an
application `Fault` element in an ordinary schema position from being mistaken for a protocol fault.

## Transport behavior

Requests go through one `HttpClientConnectionManager`, which provides connection pooling, redirect
handling, cookie handling and automatic protocol negotiation from HTTP/3 down to HTTP/1.1. Protocol
selection, connect timeout and request timeout are constructor options.

`close()` retires the current manager and installs a fresh one, so the client remains usable
afterwards. The swap happens under a mutex and the retired manager is closed outside it: a concurrent
request either uses the retired manager or the new one, and is never blocked by the close. Every other
member is immutable after construction.

Credentials supplied as `username`/`password` options or carried in the endpoint URL become a Basic
`Authorization` default header. Accepting credentials and dropping them would send unauthenticated
requests to a protected service, so they are applied rather than ignored.

A remote %WSDL is retrieved by the `WSDL` module's own HTTP client, not by the connection manager;
only SOAP operation traffic uses async I/O. This is documented on the constructor because it means
WSDL retrieval does not inherit the client's protocol or timeout settings.

## Connections

`SoapIoConnection` registers the `soapio://` and `soapios://` schemes and returns `SoapClientIo`
objects. The connection URL addresses the %WSDL unless an explicit `wsdl` option overrides it, and
`target_url` overrides the endpoint declared by the selected port. Scheme mapping accepts the
`soap`/`soaps` spellings as well, so an existing SOAP connection URL can be pointed at the async
client by changing only the scheme.
