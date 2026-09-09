# Native reader scalar and empty values

Copyright (C) 2026 Qore Technologies, s.r.o.

Both `XmlReader::toQore()` and `toQoreData()` already documented scalar strings
and `NOTHING`. Their implementation nevertheless called `parseXmlData()`,
which returns `QoreHashNode*` and asserts that the XML stack produced a hash.
Advancing to `<value>text</value>` and converting its content aborts in Debug.
The independent baseline at `ed0f53b` is retained as
`/tmp/wsdl-p3-35-reader-scalar-baseline.qr`, with status -6 and the assertion
in `/tmp/wsdl-p3-35-reader-baseline.json`. The native module SHA-256 was
`c1014ef946c9ef5fd1d62988eac45b8950ae402fb4041585188deca53b3682f9`.
No QName or schema is required to reproduce the defect.

The cursor methods now use `parseXmlValue()`, which returns an owned
`QoreValue` and bounds conversion by the containing element's depth. A
self-closing element returns `NOTHING` without consuming its following
sibling. Explicit empty start/end pairs stop at their closing tag. A holder
owns completed values until exception checks succeed; the existing XML stack
owns partial values. Pending exceptions are checked immediately after reading,
and the empty fast path still checks cancellation. The separate document
helper retains its hash return contract.

The methods mutate cursor state, so the inappropriate `RET_VALUE_ONLY` flags
are removed. Discarding the result still advances the reader. The new suite
exercises this in every supported execution mode without unused-result
warnings. Public notes and an executable [example](../../design/xml-reader-values.md)
describe cursor boundaries, attribute access and both grouping defaults.

`test/xml-reader-values.qtest` has **10 cases / 524 assertions**. It covers
Unicode and whitespace in UTF-8/UTF-16LE/UTF-16BE, scalar attributes, empty
values with and without attributes, adjacent and nested elements, CDATA,
comments, mixed and repeated children, explicit/default grouping flags,
fresh readers, EOF, XmlDoc, schema validation and malformed input.
An armed InputStream begins rejecting or interrupting only after the reader
has entered a record, testing original exception preservation and release of
partial conversion state. Separate tests cover interruption before scalar,
complex and empty conversion and later successful calls.

The existing independent QName union matrix now exercises both cursor APIs
on all **300 documents**, with **30 schemas** assessed by pinned Xerces-J
2.12.2. Accepted strings and absent content are asserted exactly; invalid
schema values retain `PARSE-XML-EXCEPTION`. This is additional native cursor
coverage, not a claim that WSDL's remaining QName namespace integration is
complete. The previous 21 old-Python-libxml2 false negatives remain explicitly
accounted for, with no Qore discrepancy waived.

Full regression, mode/timezone, corpus, compiler, documentation and Valgrind
results are recorded in [EXECUTION.md](EXECUTION.md). The separate
`schemaValidate()` text-versus-location API conflict remains the next native
reader task; no schema attachment behavior changes in this increment.
