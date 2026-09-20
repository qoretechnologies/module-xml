# WSDL HTTP request URLs

Copyright (C) 2026 Qore Technologies, s.r.o.

`HttpBinding` produces an operation URI reference after replacing URL patterns or adding the URL-encoded query. `SoapClient` resolves this reference against the native client's complete configured endpoint using Qore `resolve_url()` with `RESOLVE_URL_ENCODE | RESOLVE_URL_NO_FRAGMENT`, then calls `HTTPClient::sendUrl()` for the exchange. The selected WSDL service/port supplies the endpoint unless the constructor's `url` option overrides it.

Absolute paths replace the endpoint path. Relative paths use the endpoint's containing directory; empty and query-only references retain the applicable base components. Network-path references select their own authority. Percent-encoded octets and explicitly empty queries retain their identity. Fragments are not sent. Operation serialization remains independent of a deployment endpoint, and saved services use the same request path.

URI parsing, reference resolution, transport selection, redirect resolution and credential challenges belong to Qore. The request-local API preserves the client URL, HTTP configuration, queues, connection management, TLS options and timeouts through success and failure. SOAP bindings retain their existing endpoint path and `send()` behavior.

SoapClient's public `headers` map is a set of client defaults. Before supplying these to `sendUrl()`, the client removes default `Authorization`, `Cookie` and `Host` fields when Qore-parsed scheme, host and effective port identify a different origin. HTTP and HTTPS default ports are normalized; host case is ignored, while UNIX socket path case is significant. Message headers from an explicit call remain associated with its selected target. Qore then applies its native redirect rules. This preserves existing header customization without changing native default headers during a request.

Endpoint selection calls `setURL()`, which resets native credentials. Explicit username/password options are applied afterward if the selected endpoint supplied neither username nor password, matching native HTTPClient constructor precedence. User information in an operation reference is never installed as client credentials.

The focused Qore tests check source and saved services, provider calls, replacement data, query boundaries, origin scope, credential precedence and concurrent alternating targets. An independent Python HTTP peer checks actual request lines, payload bytes, redirect metadata and failure/recovery behavior with event-driven shutdown.

`SoapHandler` resolves each HTTP operation template against all matching port addresses before registering it. Explicit `addMethod()` paths override that resolution and apply to both matching and decoding; bindings without ports retain mount-relative routing. A root-only internal URI context supplies Qore's resolver when there is no port base. Its authority is never used for transport. Equivalent resulting paths are registered once. All paths are compiled and duplicate registrations checked under the write lock before any route becomes visible.

Each registration owns a shallow binding copy and, for replacement templates, a separate input descriptor. Immutable message/schema graphs remain shared. Opaque temporary tokens protect replacement part names during URI encoding and are restored before compiling the route; Unicode literals therefore match the encoded request without changing part identities. Matching prefers a complete raw path and supports the mount-relative path as well. Decoding uses the exact path that matched. Encoded slashes remain data and are decoded only as replacement values. A resolved template that loses an input part cannot decode that part and rejects at registration.

For an empty operation reference, generated GET parameters replace a base query, while a zero-part input retains the base query. Fixed queries remain part of template matching. Dot-only replacement values are percent-encoded before reference resolution so `.` and `..` remain data. Literal operation dot segments still follow Qore's normal resolution.
