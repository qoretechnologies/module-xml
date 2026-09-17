# RPC wrapper names and abstract WSDL labels

Copyright (C) 2026 Qore Technologies, s.r.o.

SOAP RPC serialization and deserialization used the opposite abstract message
label as the wrapper name: output_name for a request and input_name for a
response. The operation-name fallback worked only when labels were omitted.
An explicitly named input/output could therefore change the wire shape and
hide this through a round trip between the same incorrect writer and reader.

Both paths now use the operation's XML name for requests and append `Response`
for responses. Abstract labels remain available on WSOperation and survive
serialization; they do not define RPC wrappers. This is a prerequisite for
implementing abstract-name defaults and overload identity without changing the
wire format as a side effect.

The request rule is defined by [WSDL 1.1 section 3.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body).
The response convention is clarified by [WS-I Basic Profile R2729](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/csd01/BasicProfile-v1.2-csd01.html#R2729).
This increment implements that naming rule; it does not claim full Basic Profile
conformance or change binding namespace selection.

`test/wsdl-rpc-operation-names.qtest` fails before the fix for explicit labels
and the actual HTTP request wrapper. After the fix, three cases and 252 assertions
pass. The tests inspect expanded body names, use independently written request
and response envelopes, reject both abstract labels and message declaration names
as wrappers, and cover SOAP 1.1/1.2, one-way requests, omitted labels, detached
saved operations and reconstructed services. SoapClient/SoapHandler exchanges
also inspect both wire envelopes, rather than accepting a mutual round trip alone.

The first legacy P5 report attempt timed out in the existing 60-second Qore
worker while other Qore builds/tests were active. Exit code 1 alone was not
accepted: the required report was missing, and validation stopped before staging.
The unchanged rerun completed in 53.875 seconds and produced the complete report
matching the baseline. No deadline or expected result was relaxed.

The final 39-suite Qore gate passes 480 cases / 8,226 reported assertions;
all six corpus reports semantically match P6-10. WSDL documentation and astparser
checks pass without warnings or errors.

See the [validation inventory](P6-12-validation.json),
[62-check audit](audits/P6-12-rpc-operation-names.md) and
[durable component design](../../design/wsdl-component-references.md).
P6 still requires overloaded operation identities and abstract input/output
defaults, then the remaining binding matrix; P7–P9 remain open. No native changes,
installation or push are part of this increment.
