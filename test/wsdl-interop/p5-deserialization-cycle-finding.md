# Failed cyclic deserialization retains core objects

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: fixed by Qore develop commit `0eb8abb81` in P5-12. See
[final evidence](core-graph-cleanup-evidence.md) and [inventory](P5-12-validation.json).
The following sections preserve the original P5-11 failure evidence.
P5-11 changed only native libxml2 behavior.
The new native unit, complete C probe and native allocation-failure checks have
zero Valgrind errors and no lost blocks. The broader existing wildcard consumer
suite has a failed Valgrind result, retained explicitly in the P5-11 inventory.

`test/wsdl-wildcard-attributes.qtest` passes all assertions, but its malformed
serialized provider metadata triggers leaked objects. Commenting out the other
12 cases retains the failure in the single `metadata()` case. The following
minimal program removes XML and DataProvider entirely and reproduces it:

```qore
%modern
class AbortSerialization inherits Serializable {
    public { string value = "test"; *AbortSerialization next; }
    private:internal deserializeMembers(hash<auto> members) {
        next = members.next;
        if (members.value == "reject") {
            throw "EXPECTED-ERROR", "rejected serialized value";
        }
        value = members.value;
    }
}
AbortSerialization original();
original.next = original;
hash<SerializationInfo> state = original.serializeToData();
state._index."0"._class_data."AbortSerialization".value = "reject";
try {
    auto rejected = Serializable::deserialize(state);
    throw "MISSING-ERROR", rejected;
} catch (hash<ExceptionInfo> error) {
    @assert(error.err == "EXPECTED-ERROR");
}
printf("Rejected custom deserialization\n");
```

Run with the isolated checked runtime:

```sh
source /tmp/wsdl-core-date-env.sh
QORE_PCRE2_NO_JIT=1 valgrind --error-exitcode=99 --leak-check=full \
  --show-leak-kinds=definite,indirect,possible \
  --errors-for-leak-kinds=definite,indirect,possible \
  qore -b --enable-debug --exec-mode=ast /tmp/wsdl-p5-11-deserialize-cycle.qr
```

Removing `next` and its two assignments gives zero Valgrind errors and zero lost
blocks. The cyclic version reports 1,232 definitely lost bytes in 20 blocks and
14,176 indirectly lost bytes in 118 blocks. It does not load the XML module.
These are failure measurements, not passing compatibility evidence.

`ObjectIndexMap::~ObjectIndexMap()` in `lib/QoreSerializable.cpp` calls
`qore_object_private::obliterate()` on indexed objects during exception cleanup.
That function decrements the reference count and returns immediately when any
reference remains, before clearing members or running recursive-reference
cleanup. The rejected self-reference therefore keeps the object and its program
alive. Both the isolated runtime source and current main develop have this path.
The corresponding acyclic failure is reclaimed normally.

The fix must clean failed deserialization graphs without invoking user
constructors/destructors on incomplete objects, releasing index ownership twice,
losing the original exception or damaging successful cyclic/shared graphs.
Required checks include self/mutual cycles, hash/list links, custom hooks,
partially restored inheritance, successful identity preservation and Valgrind.
Main Qore changes remain authorized for tested/audited local develop commits;
no push or installation is authorized by this finding.
