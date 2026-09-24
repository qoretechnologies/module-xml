# WS-Addressing

Copyright (C) 2026 Qore Technologies, s.r.o.

This document describes how the WSDL module implements WS-Addressing 1.0: the Metadata that WSDL descriptions
state (WS-Addressing 1.0 Metadata), and its WS-Policy 1.5 attachment. The pinned sources are in
`test/wsdl-interop/normative/` (`sources.json`, `addressing`).

## Actions

`WSOperation` keeps the explicit actions of its input, output and faults, and the name and target namespace of
its port type. Explicit actions come from `wsam:Action`, and from the `wsaw:Action` attribute of the 2006
WS-Addressing WSDL Binding. Both must be absolute IRIs, and when both are present they must agree. The action
of a message is:

1. its explicit action;
2. for an input and a binding, the binding's non-empty SOAP action (Metadata section 4.4.1);
3. the default action (section 4.4.4): `[target namespace][delimiter][port type][delimiter][input|output name]`,
   and `...[delimiter][operation][delimiter]Fault[delimiter][fault name]` for a fault. The delimiter is `:` for
   a `urn:` target namespace and `/` otherwise. No `/` is added after a namespace ending in `/`. The input and
   output names are the effective WSDL 1.1 names (`getInputName()` and `getOutputName()`).

Metadata example 4-8 lists the output name as `CheckAvailabilityResponse` while its output declares
`name="Availability"`, and it computes the action from `Availability`. The rule uses the declared name, and so
does the implementation.

Operations saved before WS-Addressing support have no port type name. Their default actions raise
`WSDL-OPERATION-ERROR`, while explicit and SOAP-derived actions still work. A `WebService` reparses its WSDL
when it is restored, so it always has them.

## Policies

`WsdlPolicyCatalog` is construction-only state of `WsdlComponentRegistry`. It indexes the `wsp:Policy` children
of each WSDL document's `wsdl:definitions` by document and `wsu:Id` or `xml:id`, and by `Name`.

A policy reference is resolved as follows:
- A `#fragment` reference resolves in the referring document.
- Any other reference resolves by `Name`, or else like a WSDL import of the referring document, to a loaded
  document's fragment.
- An unresolved or cyclic reference is a `WSDL-ERROR`.
- Expanding a reference switches the current document, so references inside an imported policy resolve in that
  policy's own document.

Policies attached to an element are its child `wsp:Policy` and `wsp:PolicyReference` elements and its
`wsp:PolicyURIs` attribute. Both WS-Policy 1.5 and 2004/09 are accepted, and the attachments are merged as a
conjunction.

Normalization (WS-Policy 1.5 Framework section 4.3) projects each alternative onto three flags:
`addressing`, `anonymous_responses` and `non_anonymous_responses` (`WsAddressingAlternative`).
- `wsp:Policy` and `wsp:All` are cross products. `wsp:ExactlyOne` is a union.
- `wsp:Optional` adds an alternative without the assertion.
- `wsam:Addressing` sets `addressing` for each alternative of its nested policy, whose `wsam:AnonymousResponses`
  and `wsam:NonAnonymousResponses` set the response flags.
- Other assertions do not change an alternative, and their nested policies are not evaluated.
- Unknown WS-Policy operators are errors.

A policy therefore has at most eight distinct alternatives, so normalization cannot grow exponentially.
Duplicates are removed, and results are sorted in a canonical order.

The 2006 `wsaw:UsingAddressing` element on a port or binding, and inside a policy, is treated as `wsam:Addressing`.
As an element, it is optional unless it is marked `wsdl:required="true"`.

Attachment subjects follow WS-Policy 1.5 Attachment section 4.1:
- `OperationalBinding::getAddressingAlternatives()` is the merge of the binding's policy and the binding
  operation's policy.
- The port's policy is kept separately (`WebService::getPortAddressing()`).
- `WebService::getAddressingPolicy()` merges both for one port, or uses the binding alone, and reduces the result
  to `WsAddressingPolicy`.

`WsAddressingPolicy` has four fields:
- **`supported`**: some alternative contains the assertion.
- **`required`**: every alternative contains it.
- **`anonymous`**: some alternative permits anonymous responses. This includes alternatives without WS-Addressing,
  whose responses are anonymous.
- **`non_anonymous`**: some WS-Addressing alternative permits non-anonymous responses. It is always true when no
  alternative uses WS-Addressing.

A policy containing `wsam:Addressing` may be attached only to ports, bindings and binding operations (Metadata
section 3.1, WS-I R1156). Attachments to services, `wsdl:message` elements, port types with their operations and
messages, and the binding's messages and faults are rejected.
Policies without the assertion may be attached anywhere.

Description checks:
- **R1157:** a binding that attaches the assertion to some operations must attach it to all of them.
- **R1158:** an effective alternative with both response assertions is rejected. This is checked for the binding
  merged with each operation, and again with each port's policy.
- **Actions:** checked with each effective policy (`Binding::checkActions()`). An explicit input action must
  equal a non-empty SOAP action (R2901, for SOAP 1.1 and 1.2). With WS-Addressing supported and no explicit
  input action, a SOAP action that supplies the action must be absolute (Metadata section 4.4.1).
- **Empty SOAP actions:** an empty SOAP action counts as absent, since it supplies no action.

`wsdl:required="true"` is accepted on the elements that are processed: `wsp:Policy`, `wsp:PolicyReference`, a
port's `wsa:EndpointReference`, and `wsaw:UsingAddressing` on ports and bindings. Other required extensions are
still rejected.

## Endpoint references

A port may be extended by one `wsa:EndpointReference` (Metadata section 4.1).
- Its `wsa:Address` must be an absolute IRI equal to the port's address. The comparison uses the address as
  declared, before a relative location is resolved.
- Each reference parameter must be namespace-qualified. It is kept as XML with all its in-scope namespace
  declarations, so it can be copied into a message as-is (Core section 3.2 and SOAP Binding section 3.4).
- `wsa:Metadata` and extensions are ignored.
- `WebService::getWSDL()` with a base URL rewrites a supported port's endpoint reference address together with
  its `soap:address`, so a published WSDL remains valid.

Port metadata is transient in `WebService` (`port_addressing`) and is rebuilt when the WSDL is parsed again.
