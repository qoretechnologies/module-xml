# HTTP query and form part presence

Copyright (C) 2026 Qore Technologies, s.r.o.

[WSDL 1.1 section 4.6](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_http:urlEncoded)
requires every message part to be encoded as a name/value pair. An explicit empty
value has a key and is distinct from an omitted pair.

The previous GET decoder returned `{}` for no query or an empty query, bypassing
all message validation. Nonempty queries and POST forms reached a converter which
passed absent values to scalar converters; missing strings became empty strings.
The owning all-part converter now requires each wire key before type conversion.
GET always uses that converter. HTTP normalization can represent a zero-byte body
as `NOTHING`; POST/MIME form decoding maps it to an empty form and applies the same
checks. Empty string values and zero-part messages remain valid. Extra unbound keys
retain the API's existing ignored behavior.

The five models contain 31 wire forms covering strings, integers, booleans, pairs
and zero-part messages. The Qore suite runs GET, POST urlEncoded and POST MIME form
bindings with plain and fixed-query operation locations. It checks source and both
saved services, detached operation handles, provider examples, request/response
conversion, 90 successful HTTP calls and 180 missing-part rejections before the
callback. Valid calls after rejections verify recovery. Python's independent form
parser preserves explicit empty values; pinned Xerces validates the corresponding
five schemas and 31 value documents, including invalid repetitions and omissions.

Run:

```sh
QORE_MODULE_DIR=build-debug:qlib:/tmp/xml-http-part-values/runtime:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-http-part-presence.qtest
python3 -B test/wsdl-interop/test_http_part_presence.py -v
```

The local installed Mime binary predates Qore's empty-form serialization fix
`de36905d44619d10bf4d896bec961be8f024a35a`. Current source and the current built
`Mime.qmod` return an empty string for an empty form. Validation uses a frozen copy
of that binary in the indicated temporary module directory. Its hash is recorded;
no Qore source or installation was modified. An updated installation can use its
normal Mime module instead.

All 20 affected Qore suites pass: 605 cases / 15,199 assertions. The final focused
suite has 30 cases / 2,646 assertions. Seven independent gates, including six CXF
peer tests, documentation and astparser pass without warnings or errors. The broad
run used the initial 20-case focused test; ten MIME form cases were then added and
the focused test rerun. Production and dependency hashes are identical across
both runs. This test-only extension and the original results remain recorded.

All 16 corpus gates meet their expected outcomes; the six semantic reports are
unchanged from P6-35. The legacy P5 diagnostic still returns its expected status 1
for approved projection losses; it is not reported as a passing conformance test.
The approved 180-second corpus worker timeout is retained. No C++ changes were
made, so this increment does not require another Valgrind run.

[Validation](P6-36-validation.json) records commands, source hashes and local
artifacts under `/tmp/xml-http-part-values/`. The [audit](audits/P6-36-http-part-presence.md)
records all 62 checks. This completes the part-presence correction; the broader
P6 binding and MIME acceptance work remains open.
