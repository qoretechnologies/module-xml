# SOAP assertion and profile-requirement ledger

Copyright (C) 2026 Qore Technologies, s.r.o.

## What this is

[`assertion-ledger.json`](assertion-ledger.json) accounts for every one of the 140 assertion
identifiers published in the W3C SOAP 1.2 test collection and every requirement in the WS-I Basic
Profiles 1.2 and 2.0 — 493 rows in all. Each row records the requirement as its source states it,
whether it applies to this implementation, and which executable cases cover it.

The plan for this phase requires that no assertion be marked not-applicable merely because an older
test collection says it was not tested, and that every applicable assertion carry a
specification-based rationale and an exact executable mapping. Those two rules are enforced
mechanically rather than asserted in prose, by [`verify_ledger.py`](verify_ledger.py).

## Current normative sources, not the 2003 collection

The test collection dates from 2003 and indexes the First Edition. The requirements are revalidated
against the Second Edition, W3C Recommendation 27 April 2007, pinned under
[`normative/`](normative/) with SHA-256 digests recorded in
[`normative/sources.json`](normative/sources.json). The collection is pinned too, but only as the
source of the assertion identifiers.

Sections are located through the documents' own heading elements
([`soap_sections.py`](soap_sections.py)) rather than through flattened text. A flattened document
cannot tell a heading from a cross-reference to it — "see 2.6 Processing SOAP Messages" reads exactly
like the heading it points at — and an earlier text-based pass silently attributed the wrong body to
section 2.6 because of it.

Revalidating every row against the current text produced concrete corrections:

- **Stale section numbers.** The collection cites Part 1 section 2.7.4, which does not exist in the
  Second Edition; the relayed-infoset requirement is 2.7.2.1. Several Part 2 state-machine rows cite
  table numbers that have since changed. Each such row records how it was resolved, by subject.
- **Superseded wording.** Part 1 section 4.2 no longer says a binding need not use "the XML 1.0
  serialization"; it says a binding need not use "an XML serialization for transmission". The
  role, `mustUnderstand` and `relay` attribute sections now state the sender and receiver obligations
  in a single combined sentence. Part 1 section 6 cites RFC 3986, which subsumes the separate RFC 2732
  IPv6 reference the First Edition carried. Thirty-three rows record a `superseded` note of this kind, covering both changed wording and the
  renumbered state-machine tables.
- **A correction to our own earlier review.** A working note claimed the "value MUST be one of the
  roles assumed by the node" constraint on the fault `Role` element was absent from the current
  section 5.4.4. It is present, and the row quotes it. That note was written from the collection's
  commentary rather than from the current text, which is precisely the failure mode the pinned
  sources now prevent.

## What the verifier enforces

`verify_ledger.py` fails unless all of the following hold:

- the pinned specification documents match their recorded digests;
- every published assertion identifier appears exactly once, with no extra rows;
- every quoted requirement is still present verbatim in the section the row cites, so a quote cannot
  be paraphrased, invented, or left stale when the source changes;
- every applicable assertion routed to this phase names at least one executable case, and every named
  case exists in the suite — the file must exist and the case name must appear in it;
- every excluded assertion carries a rationale, and a rationale that appeals to the old collection's
  coverage rather than to the specification is rejected outright.

The gate was checked against deliberate damage: an invented quote, a mapping to a case name that does
not exist, a mapping to a file that does not exist, a collection-based excuse, an applicable row with
no mapping, and a deleted row. All six were reported, each with the correct diagnosis.

## The WS-I profiles

The profiles are pinned differently from the W3C documents, for a reason worth recording. They are
served through a CDN that rewrites contributor email addresses into per-response obfuscation tokens,
so two downloads of the same document have the same length but different bytes: **a digest of the raw
HTML is not reproducible and cannot pin the source.** What is reproducible is the requirement text.
[`wsi_requirements.py`](wsi_requirements.py) extracts each numbered statement, and two independent
downloads produce byte-identical extracts. The extracts carry the digests
([`normative/wsi12-requirements.json`](normative/wsi12-requirements.json),
[`normative/wsi20-requirements.json`](normative/wsi20-requirements.json)) and are what the ledger
quotes. This also keeps 86 KB of requirement text in the repository instead of 2.7 MB of unstable HTML.

Extracting them surfaced two things:

- `R4005` in BP 1.2 and `R5010` in BP 2.0 carry their anchor on the *preceding rationale paragraph*
  rather than on the statement. Keying extraction off the `<a name=...>` anchor silently drops them;
  keying off the statement's own leading identifier finds all 184 and 169.
- `R9999` in both profiles is the specification's own notational example — "Any WIDGET SHOULD be round
  in shape" — used to demonstrate how a requirement is written. It is not a requirement, and the
  ledger says so rather than quietly counting it.

Nothing in the WS-I accounting appeals to WS-I's own `TESTABLE`/`NOT_TESTED` classification. That is
the profile's statement about its own test suite, not about this implementation; the classification is
carried on each row as metadata and the verifier rejects any rationale that leans on it.

## Accounting

Current state, after P8-07 covered the 26 rows routed to P8 and P9a-08 closed the 49 WS-Addressing gaps:

| Outcome | W3C | BP 1.2 | BP 2.0 | Total |
| --- | --- | --- | --- | --- |
| Covered by executable cases | 126 | 174 | 159 | 459 |
| Not applicable, with a source-based rationale | 14 | 10 | 10 | 34 |
| **Total** | **140** | **184** | **169** | **493** |

993 executable mappings, every one verified to exist.

At P7 the accounting was 388 covered, 49 recorded gaps, 30 not applicable and 26 routed to P8, with 815
mappings. The sections below record why the P7 gaps were gaps and how P9a closed them.

## WS-Addressing: recorded as gaps at P7, closed in P9a

P9a implements WS-Addressing 1.0 Core, SOAP Binding and Metadata. In P9a-08 (2026-09-24) each of the 49
rows was revalidated against its pinned profile statement, and the two profiles' wordings were checked separately
where they differ (SOAP 1.1 or 1.2 names, R1144's SOAPAction header or action parameter, R2901's
"non-empty" or "if present").
- **Covered:** 45 rows (23 requirements), each mapped to the cases that assert its behavior, in both
  directions where it has two sides.
- **Not applicable:** R1203 and R1204 in both profiles (4 rows). They apply only to a non-addressable
  service instance, which receives its inputs on HTTP responses. SoapHandler is always an addressable HTTP
  server, so the condition cannot arise. This scope decision was approved on 2026-09-24.

Mapping the rows found three defects, fixed in P9a-08:
- **R1041:** an addressing node did not understand `wsa:FaultDetail`, a WS-Addressing defined header block,
  so a MustUnderstand fault could name it as not understood.
- **R2745:** an explicit empty per-call SOAP action omitted the SOAPAction header. It now sends `""`. The
  new `send_soapaction` client option omits the header for servers that reject it, and is refused for
  WS-Addressing requests (R1144).
- **R2901, Basic Profile 2.0:** a present but empty `wsoap12:operation` soapAction was treated as absent.
  It must now equal an explicit input action.

The verifier now rejects any WS-Addressing row recorded as a gap.

At P7, 49 rows were recorded as gaps, not exclusions. They are the profile requirements that depend on
WS-Addressing: the `wsa:Action` header block, the `wsam:Addressing` policy assertion and the
anonymous/non-anonymous response rules. This module implements SOAP 1.1 and 1.2 messaging over WSDL
1.1 and provides no WS-Addressing support, so those requirements apply to a Basic Profile conformance
claim and are not met.

Calling them "not applicable" would have been the easy accounting and the wrong answer: it converts a
conformance shortfall into a clean total. The verifier enforces the distinction — a gap must say what
is missing, and a row cannot be both applicable and excluded.

The module makes no formal Basic Profile conformance claim; it cites individual requirements (R2745,
R2933, R2943) as guidance. This ledger does not create such a claim.

The 14 not-applicable rows are not a residue of untested requirements. Two are the conformance
statements of Part 1 section 1.2, which range over the other mandatory requirements rather than
describing behavior of their own; every requirement they range over is itself a row here. The other
twelve are requirements addressed to the authors of a SOAP feature, module or protocol binding
specification. This implementation defines none of those — it uses the HTTP binding specified in
Part 2 section 7 — so there is no artifact of ours for those requirements to constrain.

The 26 rows routed to P8 are the SOAP Data Model, SOAP Encoding and RPC Representation requirements.
They are deliberately not counted as covered: the literal and schema-value coverage in this phase
exercises neither the encoding graph nor the RPC representation, and counting it would be exactly the
false credit the plan warns against.

## Two assertions that were blocked and are now covered

`x2-bindformdesc-dlock` and `x2-http-reqsoapnode-dlock` were recorded as blocked on a core defect at
P7-13. The requirement reads:

> When using streaming SOAP bindings, requesting SOAP nodes MUST avoid deadlock by accepting and if
> necessary processing SOAP response information while the SOAP request is being transmitted.

Qore's HTTP/1.1 client could not satisfy that for a buffered request body, which was handed off and
fixed. Both rows now map to the duplex suite, which is sized so that a client that did not accept
response information while transmitting could not complete the exchange at all. The related
streaming permission in section 6.2.3 — that a responding node MAY begin transmitting a response
while the request is still being received — is covered by the same suite.

## A defect this accounting surfaced, now fixed

Running the mapped suites the P7 sweep did not already cover surfaced two long-standing failing
methods in `test/wsdl-interop/test_soap_container_whitespace.py`:
`test_header_part_round_trip_requirement_p6` and
`test_single_rpc_parameter_round_trip_requirement_p6`. They had been recorded at P3 in
[union-whitespace-evidence.md](union-whitespace-evidence.md) as requirements that "remain failing
tests until P6", and [P6-acceptance.md](P6-acceptance.md) did not account for them.

Both came down to one gap: serialization did not accept the bare value that decoding returns for a
single selected part. A binding with `parts="body"` over a message that also carries a header-bound
part decodes the body to a bare scalar, but serialization then counted *message* parts rather than
*selected* parts and sent the bare value into part matching, which rejected it; the RPC path failed the
same way with `RUNTIME-TYPE-ERROR`. The fix is on the serialization side and leaves the documented
decoded shape untouched. All three methods now pass. The design is recorded in
[wsdl-body-parts.md](../../design/wsdl-body-parts.md).

A first attempt changed the decoded shape instead, keying it off the binding's declared headers. The
full suite caught that it broke `soap.qtest`, `wsdl-header-identities.qtest` and
`wsdl-header-merge.qtest`, which deliberately pin the existing shape; it was withdrawn in favour of
the serialization-side fix.

## Scope

The accounting is complete for both sources, but it is accounting, not acceptance. P7 acceptance also
requires the mandatory behavior for the advertised scope to pass, and the defects above are unresolved.
At P7, the 26 W3C rows routed to P8 were not claimed and the 49 WS-Addressing gaps were open by construction;
P8-07 and P9a-08 have since covered them.

## Reproduction

```
python3 test/wsdl-interop/verify_ledger.py
```
