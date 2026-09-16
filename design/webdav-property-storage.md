# WebDAV property storage

Copyright (C) 2026 Qore Technologies, s.r.o.

The in-memory and file-backed property handlers store a typed map:
resource URL → namespace URI → property name → value. An absent resource entry
represents no stored properties. It is not a `NOTHING` value inside the typed map.

`cp(source, target)` replaces the target's complete property set. When the source
has no stored properties, it removes the target entry, including stale properties.
Qore's copy-on-write containers keep later source and target changes independent.
`move(source, target)` performs the replacement and source removal under the same
write lock. Moving a property set to its own URL preserves it.

For example, after copying a resource without custom properties onto an existing
resource, the property handler leaves no custom properties on the destination:

```qore
InMemoryWebDavPropertyHandler properties();
properties.set("/destination", "urn:orders", "status", "old");
properties.cp("/source-without-properties", "/destination");
@assert(!exists properties.getAll("/destination"));
```

Both implementations serialize mutations with `RWLock`. The file-backed handler
also holds the exclusive lock while saving, since saving changes both the JSON
file and the dirty flag. Its save calls are synchronous. Reading or synchronizing
a completed property set therefore observes a complete preceding mutation.

`test/WebDavPropertyHandler.qtest` covers missing entries, replacement, copy
independence, move cleanup, identical URLs, persistence and concurrent operations.
The client and handler integration suites cover actual HTTP COPY/MOVE requests.
