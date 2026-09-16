# P6 operation handle ownership finding

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: fixed by P6-02; see [ownership evidence](operation-ownership-evidence.md).
The original independent P6 component/consumer lifetime defect was reproduced in
the committed P5-03 source (`c0b4633`) before native type capture. It is not a
passing native type retention check or an introduced P5-04 regression.

`WSOperation` weakly references its namespace registry and input/output messages
using `:=`. `WSMessage` also weakly references its namespace registry, and
binding message descriptions weakly reference their actual message. Returning an
operation from a temporary `WebService` therefore leaves a handle whose members
are gone. Debug serialization raises `ASSERTION-ERROR` for its absent namespace
container before it can process the value. This is a WSDL object graph ownership
issue, not a Qore temporary-expression or Serializable value bug.

With a verified corpus extraction and the local WSDL module:

```qore
string path = "/tmp/module-xml-wsdl-survey/databinding/examples/6/09/"
    "TypeSubstitutionUsingXsiType/echoTypeSubstitutionUsingXsiType.wsdl";
WebService owner(ReadOnlyFile::readTextFile(path), {"async_only": True});
WSOperation retained = owner.getOperation("echoTypeSubstitutionUsingXsiType");
WSOperation detached = (new WebService(ReadOnlyFile::readTextFile(path),
    {"async_only": True})).getOperation("echoTypeSubstitutionUsingXsiType");
```

The committed source reports `True` for existence of `retained.nsc`, `input`
and `output`, and `False` for all three detached members. The executable reduction
and output are `/tmp/wsdl-p6-operation-lifetime.qr` and
`/tmp/wsdl-p6-operation-lifetime.log`; the baseline module was extracted with
`git show c0b4633:qlib/WSDL.qm` into `/tmp/wsdl-p6-lifetime/WSDL.qm`.

P6 must resolve the public detached-handle contract and the complete ownership
graph, including header messages, binding state, Serializable reconstruction,
cycles and exception/cancellation cleanup. Merely keeping the operation's
namespace registry would leave its other dependencies absent. Existing consumer
code and the P5 tests retain their service owners throughout operation use.


## Resolution

Operations now own their namespace/input/output dependencies, messages own their
namespace contexts, header descriptions own their messages, and sample helpers
retain their source service. Legacy serialized weak members are promoted during
reconstruction. Empty part maps and typed constructor QName records are also
normalized at their source. Tests retain the historical reduction and cover the
complete graph, shared headers, saved providers, HTTP, cancellation and exact
release counts. See [implemented design](../../design/wsdl-operation-ownership.md)
and [validation](P6-02-validation.json). Broader P6 component/binding acceptance
remains open.
