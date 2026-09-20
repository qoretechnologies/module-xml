# Independent WSDL HTTP request URL peer

Copyright (C) 2026 Qore Technologies, s.r.o.

`contract.wsdl` declares a GET operation and a schema-bound XML response. The test generates named operation-reference, endpoint, input-representation and saved-service variants without public network dependencies. `handler.qr` accepts independent Python HTTP requests and checks callback values for source/saved/data services. `client.qr` executes the real SoapClient and SoapRequestDataProvider APIs; Python's HTTP server records the request lines, headers and payload bytes independently.

The matrix follows [WSDL 1.1 sections 4.3–4.7](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_http:operation) and [RFC 3986 section 5.2](https://www.rfc-editor.org/rfc/rfc3986.html#section-5.2). WSDL operation locations remain relative URI references; a network-path reference can select another authority. URL replacement precedes reference resolution. Explicit empty queries are distinguished from absent queries. Dot-only replacement values remain percent-encoded data through resolution. The combined peer suite performs 56 HTTP exchanges in five tests.

Run from the repository root:

```sh
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-http-request-url.qtest
python3 -B test/wsdl-interop/test_http_request_url.py -v
```

Listeners use ephemeral loopback ports. A stop request wakes each blocking server, and process completion and thread joins have bounded deadlines. No sleeps or polling are used. The installed Qore runtime must supply `HTTPClient::sendUrl()` and the response-body media-type fix.
