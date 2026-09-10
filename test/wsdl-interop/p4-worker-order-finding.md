# P4 corpus worker discards ordered children

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: the P4-13 worker change selects `XPF_PRESERVE_ORDER`. The new worker
regression fails before that change and passes afterward. All 13 owned families
now have native value and retained-order checks; final phase evidence is recorded
in the P4-13 execution entry. The original failure evidence below is preserved.

The current coverage ledger contains 24 P4 decode failures across six payload
examples in five repeated-sequence families, in both SOAP versions and directions. `probe.qr` calls `parse_xml(text)`
without `XPF_PRESERVE_ORDER` before passing its hash to `WSOperation` decoding.
The default XML hash groups repeated names together, losing their interleaving.
`WSOperation::deserializeRequest()` and `deserializeResponse()` explicitly require
an ordered parse. The production SOAP message parser and retained XML APIs
already use the order-preservation flag.

The untouched `echoSequenceMaxOccursFinite-SequenceMaxOccursFinite01-soap11.xml` contains alternating
`mnth`/`weather` pairs. The default parse supplies four `mnth` values followed by
four `weather` values and correctly fails complete-particle validation. Parsing
the same bytes with `XPF_PRESERVE_ORDER` succeeds and reserializes the four pairs
in order, preserving every expanded child name and string value. Independent
libxml2 schema validation accepts that output. The reproduction and exact fixture
SHA-256 is `7f8329dc08b9eebaada3aafc3c771d228319bee6a03bdc0064d2f2ccd7887b2a`.
The reproduction is recorded in `/tmp/wsdl-p4-13-order-probe.qr`, `.log` and `.json`.
XSD 1.0 [Model Group Validation Rules](https://www.w3.org/TR/xmlschema-1/#cvc-model-group)
require ordered partitions for a sequence; group-reference occurrence limits belong
to the reference particle ([Model Group Definitions](https://www.w3.org/TR/xmlschema-1/#Model_Group_Definitions)).

The acceptance checks fix the worker caller, add positive and wrong-order
negative regressions, rerun every original row, and extend strict P4 value/order
coverage. Native canonical ordering and the explicit retained XML path need their
respective value and full-order assertions. Original fixtures and historical
findings must remain unchanged. Selecting the required parser representation is
not permission to reorder invalid XML or weaken the particle validator.
