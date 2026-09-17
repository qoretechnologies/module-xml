# P6-15 explicit SOAP body-part selection

Copyright (C) 2026 Qore Technologies, s.r.o.

## Root causes and implementation

The body-description constructor discarded empty `parts` attributes through a
truthiness check. Body selection and document single-argument inference also
treated empty lists as omitted. RPC binding decoding ignored explicit selection
and converted the whole message. Declared fault serialization incorrectly applied
the normal output message's part selection to the fault's different message.

Construction now distinguishes omitted attributes from empty selections, collapses
XML list whitespace, preserves selection order, and rejects repeated or unresolved
part names. Both serializers and decoders honor explicit selections, including an
empty Body or empty RPC wrapper. Fault detail uses its own message. Public partial
RPC decoding retains its string-selection compatibility and accepts a list plus an
optional strict-field policy. The audit additionally found an unknown public RPC
part producing a Qore type error; explicit name validation now raises `WSDL-ERROR`.

An isolated module from the preceding commit reproduces eight failing cases out
of nine; calls requiring the new list/strict API were excluded from that baseline.
The final focused suite passes nine cases / 467 assertions, covering both SOAP
versions and directions, document/RPC styles, source and saved descriptions,
retained XML, invalid declarations/values, single-argument inference, independent
fault detail and actual HTTP calls carrying an external-message header.

## Independent evidence

Seven Python tests compile the pinned WSDL4J 1.6.3 observer with all compiler
warnings treated as errors. They verify omitted, empty, single and ordered
selections for both SOAP versions and styles. The WSDL4J implementation has a
separate tokenizer limitation: `StringUtils.parseNMTokens()` splits on SPACE only,
so character-reference TAB/CR/LF remain in a token. Two tests retain those actual
observations. Pinned Xerces independently validates normalized XML list values
and order, including all XML whitespace separators and negative order/name/NBSP
cases. Module regressions are not weakened to copy the oracle's limitation.

Requirements come from [WSDL 1.1 body selection](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body),
[XML Schema list semantics](https://www.w3.org/TR/xmlschema-2/#list-datatypes),
and [WS-I Basic Profile R2213/R2214](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/csd01/BasicProfile-v1.2-csd01.html#R2213).
The latter explicitly permits selecting no body parts. The independent schema
uses a list permitting the empty value, rather than imposing `NMTOKENS`' nonempty
restriction on this profile behavior.

## Validation and remaining scope

Exact final-source suite accounting, baseline and log hashes, documentation and
astparser checks, and six corpus report comparisons are recorded in
[P6-15-validation.json](P6-15-validation.json). The first broad run was discarded
after the public RPC validation finding; the full gate was restarted on the final
source. The first corpus attempt stopped at the strict full-report subprocess's
60-second deadline under competing CPU load. Its log is retained separately;
completion of the already-running external test batch was followed by a successful
unchanged rerun with the same deadlines and acceptance criteria. The [audit](audits/P6-15-body-parts.md) records each of the 62 skill checks.
No C++ changed, so Valgrind is not required for this increment.

The omitted-parts header exclusion remains unchanged in this increment. The user
approved the standard default (all message parts); its implementation is the
next body/header binding increment. Full concrete fault/headerfault metadata,
interaction-pattern restrictions, HTTP/MIME coverage and pinned CXF contract
replay remain P6 requirements. This increment does not close P6 or P7–P9.
