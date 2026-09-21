# W3C SOAP 1.2 assertion ledger

Copyright (C) 2026 Qore Technologies, s.r.o.

## What this is

[`assertion-ledger.json`](assertion-ledger.json) accounts for every one of the 140 assertion
identifiers published in the W3C SOAP 1.2 test collection. Each row records the requirement as the
*current* specification states it, whether that requirement applies to this implementation, and which
executable cases cover it.

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

## Accounting

| Outcome | Rows |
| --- | --- |
| Applicable, covered in this phase | 100 |
| Not applicable, with a specification-based rationale | 14 |
| Applicable, routed to P8 | 26 |
| **Total** | **140** |

179 executable mappings, every one verified to exist.

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

## Scope

This is the W3C ledger only. The WS-I Basic Profile 1.2 and 2.0 identifiers are not adjudicated here,
are not pinned in the repository, and no WS-I row is claimed; they remain open work for this phase.
Recording the W3C accounting does not by itself constitute P7 acceptance, which also requires the
WS-I accounting and the mandatory behavior for the advertised profiles to pass.

## Reproduction

```
python3 test/wsdl-interop/verify_ledger.py
```
