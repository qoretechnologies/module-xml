# XmlReader cursor values

Copyright (C) 2026 Qore Technologies, s.r.o.

`XmlReader::toQore()` and `toQoreData()` return the value of the current
element's children: a string for ordinary scalar text, a hash for child
elements or mixed/CDATA content, and `NOTHING` for no content. The current
element's attributes remain accessible through the reader's attribute API;
they are not added to its child value. Before the first read, both methods
retain the existing whole-document hash behavior. Document-oriented
`parse_xml()`, `XmlDoc` and SAX iterator conversion retain their hash contracts.

The internal `parseXmlValue()` returns an owned `QoreValue`. It uses the
existing XML stack and parsing flags without narrowing a valid string to a
hash. The separate document helper keeps its hash return type. A holder owns
any completed value until exception checks succeed, and existing stack cleanup
releases partial values on stream failure or cancellation.

| Starting position | Result and ending position |
| --- | --- |
| Before the first read | Whole-document hash, then end of input |
| Nonempty element containing ordinary text | String, cursor at that element's closing tag |
| Element containing child elements or mixed content | Hash of children/content, cursor at its closing tag |
| Explicit empty start/end pair | `NOTHING`, cursor at its closing tag |
| Self-closing element | `NOTHING`, cursor remains on that element |
| End of input | `NOTHING` |

The containing element's depth bounds conversion. A self-closing element must
not advance into a following sibling; the caller's next `read()` advances to
that sibling. Empty-content fast paths still honor cancellation. Both methods
advance mutable reader state, so their QPP flags no longer declare that only
the return value matters. Discarding a conversion result still consumes the
current element's content.

`toQore()` defaults to preserving out-of-order child groups through the existing
`^N` key suffix convention; `toQoreData()` defaults to collapsing same-name
children into lists. Explicit flags continue to control either method. Text,
Unicode, XML whitespace, CDATA and comments follow the same conversion rules
as the other native XML APIs.

Example reading adjacent scalar labels:

```qore
%modern
%requires xml
XmlReader reader("<catalog><label>Product</label><label>Service</label></catalog>");
@assert(reader.read()); # catalog
@assert(reader.read()); # first label
@assert(reader.toQore() == "Product");
@assert(reader.read()); # second label
@assert(reader.toQoreData() == "Service");
@assert(reader.read()); # closing catalog
@assert(!reader.read());
```

`test/xml-reader-values.qtest` checks scalar and empty values, sibling and
nested boundaries, XML encodings, attributes, mixed/CDATA content, grouping
flags, document APIs, schema validation, discarded results, malformed input,
stream errors and interruption. An armed stream triggers failure only after
conversion has started, making cleanup checks deterministic. The independent
QName union validator matrix additionally verifies both cursor APIs against
300 documents whose XSD verdicts come from pinned Xerces, with exact accepted
text and empty values asserted separately.
