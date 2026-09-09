# Caller-owned scalar objects during record conversion

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdComplexType` used `delete` to consume converted entries from its local input
hash. Qore object references remain shared when a hash is copied. Deleting an
object-valued entry therefore destroys that object even when the caller or an
earlier serialized result still owns a reference. This also affected shared
sibling values, failure after an earlier member, and cleanup during decoding.

A reduced baseline uses the already-supported `XsdBinaryValue` with a
`base64Binary` element. Serialization produces the correct `QQ==` text, then
`payload.getBinaryValue()` raises `OBJECT-ALREADY-DELETED`. The unchanged-source
reproducer and log are `/tmp/wsdl-p3-33-binary-owner-before.qr` and `.log`.
This failure is independent of the ongoing QName scratch implementation that
first exposed it. There is no core compiler or reference-counting change.

Five consuming operations in complex record serialization/deserialization now
use `remove`. They remove the local entry while retaining the normal shared
object lifetime. This includes sequence/all fields, converted choice keys and
discarded attribute containers. Input validation and the check for unconsumed
fields are unchanged. The fix does not clone, replace or explicitly delete
caller objects.

The new nine-case suite has 147 assertions and covers serialization, decoding,
shared sibling and repeated references, nested records, choice branches,
reconstructed schemas and values, errors after an earlier converted field,
program interruption at a later field and four synchronized concurrent callers.
All nine cases fail against exact WSDL source from `1ad6ecf` and pass with the
fix. Baseline and final logs are
`/tmp/wsdl-p3-33-caller-values-baseline.log` and
`/tmp/wsdl-p3-33-caller-values-final.log`.

The binary HTTP consumer suite now retains the request and response hashes,
checks their original objects after a call and repeats the call with those
same objects. Both actual SOAP bindings and original/reconstructed services
pass. The suite has 148 assertions. Existing independent binary/schema/provider
matrices verify exact bytes and XML validity in both directions.

See [the implemented example](../../design/wsdl-binary-values.md#caller-ownership-during-record-conversion)
and [EXECUTION.md](EXECUTION.md) for final tests, source hashes, corpus comparison,
Valgrind results and the complete audit. QName instance conversion remains active
in scratch code and is not included in this lifetime fix.
