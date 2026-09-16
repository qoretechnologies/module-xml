# Detached WSDL operation ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

Public operation, message, header-description and sample-helper handles retain the
objects required by their methods. Releasing the source `WebService` must not turn
an otherwise valid operation into missing input/output messages or an absent
namespace registry.

| Owner | Retained dependencies |
| --- | --- |
| `WSOperation` | Namespace context, input/output messages, fault messages, operational bindings |
| `OperationalBinding` | Input/output binding descriptions |
| `BindingMessageHeaderDescription` | Actual header message |
| `WSMessage` | Namespace context, part declarations and named type map |
| `Namespaces` and schema types | Existing completed declaration registries and declaration-local contexts |
| `WSMessageHelper` | Its source service, when constructed with one |

An operation does not retain the entire source service. Its messages, bindings and
namespace registries already reach the complete schema graph, including global
wildcard declarations and recursive type definitions. Shared header messages keep
their object identity. Existing namespace/type cycles are handled by Qore's cycle
collector; new operation-to-service back references are unnecessary. Lexical
namespace-scope helpers and the service's borrowed document-routing map retain
their existing scoped/borrowed relationships.

For example, a partner order operation can outlive the service variable:

```qore
WSOperation submit = (new WebService(wsdl_text, {"async_only":True})).getOperation("submitOrder");
hash<auto> message = submit.serializeRequest(order, headers, NOTHING, NOTHING,
    NOTHING, NOTHING, "OrderSoap12");
```

`Serializable` preserves object sharing. Operation, message and header-description
reconstruction hooks explicitly assign their owned dependencies, promoting old
serialized `_weak` references before the deserialization context releases its
objects. Absent or incorrectly typed required dependencies reject with
`DESERIALIZATION-ERROR`; an already-damaged old graph with missing objects cannot
be reconstructed by guessing. New graphs preserve the same ownership directly.

Zero-part messages initialize their argument and part maps to empty hashes.
Reconstruction normalizes old zero-part `NOTHING` maps to the same empty shape,
allowing empty provider records. `WSOperation` QName attribute processing builds
new result records instead of changing scalar entries inside a caller's typed
hash, so parsed XML and typed constructor data have the same behavior.

The source service and its schema must be fully constructed before sharing handles
between threads. This change supplies ownership, not concurrent mutation support.
Serialization keeps existing per-call namespace contexts; independent restored
handles do not share mutable output state.

`test/wsdl-operation-ownership.qtest` covers both SOAP versions, requests/responses,
declared faults, one-way operations, shared headers, recursive values, strict
wildcard declarations, standalone and saved handles, old weak-reference graphs,
malformed reconstruction followed by recovery, and real HTTP with saved providers.
Tracked destructors verify exact release counts on ordinary exit, serialization
failure, construction failure and cancellation. Queue barriers exercise concurrent
restoration without sleeps. Sample helpers retain their source through successful
calls and the existing precise bounded-generation error path.
