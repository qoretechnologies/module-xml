# WebDAV property storage CI repair

Copyright (C) 2026 Qore Technologies, s.r.o.

The module-xml push through `fd9faa5` started
[pipeline 56982](https://git.qoretechnologies.com/mirror/module-xml/-/pipelines/56982).
It happened before the user clarified that the push instruction was intended
for another agent. Further XML work must remain local until development is complete;
no Qore push or image rebuild was performed.

Ubuntu job 202039 and Alpine job 202040 both reported HTTP 500 on WebDAV COPY.
The server exception identifies `InMemoryWebDavPropertyHandler::cp()` assigning
an absent source property map to a nonoptional typed hash entry. These WebDAV
sources did not change between the previous remote XML commit `c1403ef` and
`fd9faa5`. The failure reproduces with the verified local Qore `16ae86ca7`.
The completed Alpine job has exactly three failing cases, all in WebDavClient
and WebDavClientIo; its WSDL/XML suites pass.

The same defect exists in file-backed copy and both move implementations.
A missing source now removes the destination property entry. Populated source
maps retain copy-on-write independence. A same-resource move preserves its
properties. File saves use the exclusive lock because they mutate both the
file and the dirty flag. See [storage design](../../design/webdav-property-storage.md).

The new property suite passes 7 cases / 60 assertions, covering both stores,
missing and populated maps, namespace preservation, copy independence, move
cleanup, same-resource operations, persistence and queue-synchronized concurrent
updates and sync. Five existing client/handler suites also pass: together,
6 suites / 31 cases / 205 assertions. Real HTTP client tests cover the exact
COPY/MOVE and provider operations that failed in CI.

WebDavHandler documentation builds cleanly after supplying the existing
HttpServerUtil tag file and correcting its response-field cross-reference,
Socket method link and missing PROPPATCH parameter documentation. No Qore
source or build was modified. No C++ changes or Valgrind requirement.

[Validation](CI-webdav-properties-validation.json) records commands, source and
log hashes. The [complete audit](audits/CI-webdav-properties.md) classifies all
62 checks: 19 Pass / 43 N/A / zero Fail. Raw reproductions and logs are in
`/tmp/wsdl-ci-webdav-properties/`. This is a local repair, not a green-CI claim.
