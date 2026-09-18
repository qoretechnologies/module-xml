# Multipart input normalization evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The old XML reader skipped a first boundary at byte zero, rejected binary bodies,
left transfer encodings undecoded and did not validate missing or duplicate roots.
The reduced baseline remains in `/tmp/xml-multipart-layouts/reader-baseline.log`.

The reader now delegates MIME framing to Qore Mime 1.9, selects the first or
explicit Content-ID root, validates part/root metadata and decodes transfer
encodings to bytes. Client and handler retained XML paths share charset/BOM root
decoding. The handler no longer extracts MIME parameters with regular expressions;
it routes XOP roots even without SOAPAction. Native callbacks avoid an unnecessary
second root string conversion. The audit restored an unintended URI whitespace
regex change; the established URI-space rejection remains covered by URI gates.

The installed Qore/Mime fix is 79348ce8c1494a717ec3d1e40c07eafafdfc9c37. It fixes
legal delimiter padding, complete closing-delimiter recognition, preservation of
repeated fields and the related writer's type/start parameters. All six originally
failing dependency regressions now pass using the installed module, without a
runtime override or changes to the Qore repository.

The 50-wire matrix includes 23 valid and 27 invalid messages. Its Qore suite passes
53 cases / 798 assertions, covering string/binary input, root ordering/identity,
quoted/case-varied/folded headers, preambles and epilogues, transfer encodings,
charsets, empty and 100-part messages, opaque MIME bypass and shared-writer output.
Python's email parser independently checks all valid root selections and bytes.

Ninety-six independent HTTP exchanges exercise both directions, source/saved
services, native/retained XML, actionless XOP-root dispatch, malformed responses,
malformed requests and recovery. These checks cover transport normalization;
they do not claim complete WSDL attachment-part binding or XOP reference semantics.

All 50 gates pass, including 34 Qore suites (1,608 cases / 52,945 assertions),
independent matrices, pinned CXF peers, docs and astparser. All 16 corpus commands
meet their expected outcomes. The six semantic corpus reports match P6-40 apart
from runtime version metadata; the legacy P5 projection's expected failure remains
separate from native conformance. Source files and the installed Mime binary were
hashed before and after validation. Build type: Debug. No C++ changes or Valgrind
requirement.

All 62 audit checks pass or are inapplicable: 18 Pass / 44 N/A / zero Fail.
See [validation](P6-41-validation.json), [audit](audits/P6-41-multipart-input.md),
and [durable input design](../../design/wsdl-multipart-input.md).
Artifacts: `/tmp/xml-multipart-acceptance/`.

P6 still requires multipart WSDL layouts, attachment binding replay and complete
HTTP URI execution. The request-local URI API handoff remains in
`/tmp/xml-http-base-resolution/QORE-REQUEST-URL.md`. P7–P9 remain incomplete.
