# P6-34 HTTP operation URI boundaries

Copyright (C) 2026 Qore Technologies, s.r.o.

[WSDL 1.1 sections 4.5–4.7](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_http:operation)
define relative operation locations, automatic query separators, and replacement
of declared parts. An empty relative URI is permitted by the required anyURI
attribute; absence of that attribute is different. Unicode URI spellings are
accepted by the schema and must retain their characters during part conversion.

Four root causes were reduced before implementation:

- Truth-value checks rejected empty locations as missing and treated an empty
  zero-part replacement map as an absent binding.
- Replacement matching combined byte-sized literal lengths with character-based
  substring/search positions.
- URL-encoded decoding used a character position plus a byte-sized location to
  remove its prefix, truncating values after a Unicode location.
- Handler registration rejected fixed queries. TreeMap's component-relative
  unmatched suffix cannot be interpreted as the original URI suffix: it omits
  a separator and is not the boundary rule for an HTTP operation location.

The implementation checks presence and consistent UTF-8 byte boundaries.
Fixed-query locations share the handler's template route collection and lifecycle;
ordinary static routing checks the actual complete path/query boundary. URI
encoding and decoding remain delegated to Qore's core functions.

The 16 fixture rows cover GET and POST, URL encoding/replacement and opaque MIME,
empty and Unicode locations, zero-part requests, and fixed query prefixes. An
independent Python URI observer checks wire values and the pinned Xerces grammar
checks all 16 documents plus 16 missing-location derivatives. Qore additionally
rejects an empty template when a declared part has no replacement pattern.
Source, both saved-service forms and detached operations exercise typed provider
acceptance/examples, both wire directions and UTF-16 direct request paths.
Actual HTTP calls cover every row; negative requests distinguish a fixed query
value from a longer value and a path from a longer resource name. Removal and
re-registration exercise fixed-query route ownership.

```sh
QORE_MODULE_DIR=build-debug:qlib:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-http-uri-boundaries.qtest
python3 -B test/wsdl-interop/test_http_uri_boundaries.py -v
```

See [implemented design](../../design/wsdl-http-mime.md). This increment does not
close the remaining P6 binding/component and attachment matrix or P7–P9.
