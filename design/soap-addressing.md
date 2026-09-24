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

## Message addressing properties

`WsaMessageAddressing` holds the properties of WS-Addressing 1.0 Core section 3.1. An absent `to` stands for the
anonymous destination, and an absent `reply_to` for an anonymous reply endpoint, as the absent headers do
(section 3.2).

**Output.** `WsaOutputScope` selects the properties for the messages that the current thread serializes. It is
thread-local, like `SoapMessageLimitsScope`, and validates them first: an action is required, and every IRI must
be absolute.
- **Headers:** `SoapBinding::serializeMessageWithDescription()` adds the header blocks after QName preparation and
  before envelope validation. WSDL-declared headers are therefore unaffected, and `compat_allow_any_header` is
  not involved.
- **Prefix:** the WS-Addressing prefix is `wsa`, or `wsaN` when the message binds `wsa` to another namespace.
- **Header placement:** the Header is created before the Body when the message has none. Repeated names use
  numeric `^N` keys, which `make_xml()` drops.
- **Reference parameters:** each becomes a header block with `wsa:IsReferenceParameter="true"`, replacing an
  existing one (SOAP Binding section 3.4). The marker's prefix is chosen so that it cannot capture a prefix that
  the parameter binds to another namespace.
- **mustUnderstand:** when selected, it marks the property headers, not the reference parameters.
- **SOAP action (WS-I R1144, SOAP Binding sections 2.4 and 4):** a request's SOAP action defaults to the
  `wsa:Action` value. An explicit different action is a `SOAP-SERIALIZATION-ERROR`. An explicit empty action
  sends `SOAPAction: ""` for SOAP 1.1 and the action parameter for SOAP 1.2.

**Input.** `WsAddressingHelper::parse()` works on the `SoapNodeHeader` list of `SoapProcessingNode`, so SOAP roles
decide targeting in one place. Only targeted headers are read.
- **Cardinality:** more than one `wsa:To`, `wsa:ReplyTo`, `wsa:FaultTo`, `wsa:Action` or `wsa:MessageID` raises
  `WSA-FAULT` with `wsa:InvalidAddressingHeader`/`wsa:InvalidCardinality` (SOAP Binding section 3.2.2).
- **Action:** a missing `wsa:Action` is `wsa:MessageAddressingHeaderRequired`.
- **IRIs:** values are whitespace-collapsed and must be absolute. `wsa:To` and addresses fail with
  `wsa:InvalidAddress`.
- **Endpoint references:** they need exactly one address (`wsa:MissingAddressInEPR`, `wsa:InvalidEPR`) and
  qualified reference parameters.
- **Reference parameters:** header blocks with `wsa:IsReferenceParameter` true are returned as they were received,
  with their in-scope namespaces.
- **Result:** a message without targeted property headers has no properties (NOTHING).

**Faults.** `WsaFault` carries [Code], [Subcode], [Subsubcode], [Reason] and [Details] of SOAP Binding section 6.
`serializeFault()` builds the complete envelope:
- **SOAP 1.2:** the code, then the subcode and subsubcode as nested `Subcode` elements, and the details in
  `Detail`.
- **SOAP 1.1:** the most specific subcode is the `faultcode`, and the details go in a `wsa:FaultDetail` header.

`reply()` formulates Core section 3.4:
- It selects the fault endpoint for faults, then the reply endpoint, then the anonymous address.
- The destination and reference parameters come from the selected endpoint reference, and the relationship is a
  reply to the request's message ID.
- A destination of `WSA_NONE` means that the reply must be discarded.
- A request without a message ID raises `wsa:MessageAddressingHeaderRequired` (WS-I R1163).

`checkSoapAction()` accepts an absent or empty SOAP action, or the `wsa:Action` value. Any other value is
`wsa:ActionMismatch`, with a `wsa:ProblemAction` detail.

## SOAP nodes

`SoapNodeOptions.addressing` makes a `SoapProcessingNode` understand the targeted WS-Addressing property headers:
`wsa:To`, `From`, `ReplyTo`, `FaultTo`, `Action`, `MessageID` and `RelatesTo`.
- They are reported as processed, so mandatory ones never cause a MustUnderstand fault, and all of them are
  honored (WS-I R1143).
- A processor registered for one of these names takes precedence.
- Other headers in the WS-Addressing namespace, such as `wsa:FaultDetail`, are not properties and are not
  understood by it.
- The flag is plain configuration, so a node that has it can be saved. Nodes saved before it existed restore it
  as false.

## Clients

`WsAddressingHelper::clientRequest()` decides and builds a call's properties for `SoapClient` and `SoapClientIo`.
- **When to send:** the client's `addressing` option is `True` (always), `False` (never; an error when the policy
  requires WS-Addressing, WS-I R1040), or unset, which follows the port's effective policy (`supported`). A
  per-call `addressing` override hash always enables WS-Addressing.
- **`wsa:To` and reference parameters:** from the port's endpoint reference (R1154), or else the client URL
  (R1155).
- **Other properties:** the binding's input action, a new message ID, and an explicit anonymous `wsa:ReplyTo` for
  request-response operations, which Metadata section 5.1 (WS-I R1142) makes mandatory.
- **Overrides:** they replace fields and are validated. A request-response call needs anonymous `reply_to` and
  `fault_to`, because its response arrives on the HTTP connection.

The request is serialized in a `WsaOutputScope`, optionally with `mustUnderstand`. The response is processed by
the client's node, derived with `addressing` enabled when it lacks it.

`clientResponse()` checks the response:
- The properties must parse.
- They must be present when the policy requires WS-Addressing.
- They must relate to the request's message ID as a reply (Core section 3.4).
- The action must be the output action, or for a fault the WS-Addressing fault, SOAP fault or a declared fault
  action.

Violations raise `WSA-RESPONSE-ERROR`, except that a SOAP fault is still reported as the fault, with the problem
in `info.addressing.error`. The request and response properties are returned in `info.addressing`. They are
recorded after sending, because `HTTPClient::send()` replaces the info hash.

## Handler

`SoapHandler` processes WS-Addressing headers by default (`setAddressing()`).

**Setup.** Its request node is the configured node, derived with `addressing` when it lacks it. Disabling
addressing is refused for operations whose policy supports WS-Addressing, at registration or in the setter,
because such endpoints must understand the headers (WS-I R1041, R1143).

**Registration.** Each SOAP method records:
- `addressing_policy`: `WsAddressingHelper::endpointPolicy()`, which is the binding's policy, merged with the
  port's when exactly one supported port uses the binding;
- `addressing_action`: the input action for the resolved binding.

Methods are indexed by input action, globally and per route (`aam`, `uri_aam`), and `removeService()` removes
them by `unique_id`.

**Requests.**
- The node processes the headers, and `WsAddressingHelper::parse()` fills `cx.addressing`.
- When the SOAP action selects no operation, `wsa:Action` does. A different non-empty SOAP action is then
  faulted.
- After the operation is selected, `checkAddressing()` checks, in order:
  1. required headers;
  2. the SOAP action (R1144);
  3. the input action (R2900);
  4. the message ID of a request-response message (R1163);
  5. the response endpoints: `none` is accepted, an anonymous one is rejected when the policy requires
     non-anonymous responses, and a non-anonymous one is rejected with `wsa:OnlyAnonymousAddressSupported`,
     because the handler answers on the HTTP response (R1146).
- These checks run before the callback, so a rejected request has no application side effects.

**Responses.**
- A reply is serialized in a `WsaOutputScope` with `WsAddressingHelper::reply()` and the output action. A reply to
  `none` is dropped after the callback, with an empty 202.
- **Fault actions:**
  - declared faults carry the fault action (`getFaultAction()`);
  - header faults and generic SOAP faults carry `WSA_SOAP_FAULT_ACTION` (R1035);
  - WS-Addressing faults carry `WSA_FAULT_ACTION`, and are built by `WsAddressingHelper::serializeFault()` with
    HTTP 400 for SOAP 1.2 Sender faults and 500 otherwise.
- **Destination of faults:** they relate to the request's message ID when it is known, and go to the anonymous
  address on the HTTP response, with the reference parameters of an anonymous fault endpoint. A fault endpoint of
  `none` discards faults with a 202, except MustUnderstand and VersionMismatch faults, which R1036 sends on the
  HTTP response.
- **MustUnderstand faults:** they relate to the request through the `all_headers` list that the
  `SOAP-MUST-UNDERSTAND` exception carries.
