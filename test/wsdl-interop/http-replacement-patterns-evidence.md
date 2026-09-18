# HTTP URI replacement pattern evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

[WSDL 1.1 section 4.7](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_http:urlReplacement)
defines patterns from the declared message-part names and searches before replacing
values. Parenthesized text that is not one of those patterns remains literal URI
text. All message parts must be encoded into the request URI. Repeated occurrences
of one pattern are distinct from a part having multiple values.

The previous compiler treated every opening parenthesis as the start of a part
reference. It rejected valid literal parentheses or compiled undeclared part names
that failed only during serialization. It also appended directly to its existing
map, so repeated calls accumulated stale entries and failures left partial state.
The compiler now receives the selected message, recognizes its exact patterns,
checks coverage and replaces the token map only after successful compilation.

The 19-document matrix includes literals, nested/unmatched/empty parentheses,
case-sensitive and Unicode part names, multiple and repeated parts, empty values,
zero-part messages, substitution values resembling patterns, percent escapes and
missing patterns. Baseline serialization rejected eight valid rows. Three invalid
missing-pattern rows silently omitted declared parts; the fourth failed late with
an overload error. These construction errors now have the `WSDL-ERROR` category.

All 19 documents validate with pinned Xerces against the original HTTP/MIME schemas
and corrected core WSDL schema already recorded by the grammar matrices. Four
schema-valid descriptions fail the separate all-parts semantic rule; their exact
identities and rationale are retained. A Python regular-expression substitution
and `urllib.parse.quote` independently check the wire paths. Original source bytes
remain unchanged when services are reconstructed.

The Qore suite exercises original, serialized and data-serialized services,
detached operations, provider acceptance/examples, request paths and XML responses.
Each of the 15 valid descriptions makes real GET and POST calls in all three
service forms, for 90 local HTTP exchanges without endpoint overrides. Separate
cases check failed-update rollback, successful replacement, legacy one-argument
behavior, UTF-16 input conversion and 4,096 levels of literal parentheses.

```sh
QORE_MODULE_DIR=build-debug:qlib:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-http-replacement-patterns.qtest
python3 -B test/wsdl-interop/test_http_replacement_patterns.py -v
```

The [implemented design](../../design/wsdl-http-mime.md) describes compilation and
routing. This increment does not complete the remaining P6 binding/MIME matrix.
