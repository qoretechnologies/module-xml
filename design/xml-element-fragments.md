# XML element fragments and encoding

Copyright (C) 2026 Qore Technologies, s.r.o.

XML generation accepts string-valued keys beginning with `^xml^`. A suffix permits
multiple fragments in hash insertion order. Each value is a complete XML document;
only its document element is inserted. This retains lexical text, attributes,
namespace scope, ordered children, comments, processing instructions and CDATA
inside the element. XML parsing still applies character-reference, attribute and
line-ending normalization. Declaration/prolog/epilog nodes are not inserted.

`XmlElementFragmentReader` reads to EOF so malformed trailing content cannot pass.
It preserves the document at the first element, keeps it until the reader is reset,
and frees it afterwards. The temporary serialization buffer uses unique ownership.
A fragment without a default namespace declaration receives `xmlns=""`, retaining
its namespace when inserted below a parent with a default namespace. The input
must provide all its own bindings. Native helper symbols are hidden.

Non-string values, embedded NULs and DOCTYPE declarations raise `MAKE-XML-ERROR`.
Malformed XML, unbound prefixes and multiple document elements retain the reader's
`PARSE-XML-EXCEPTION`. Parsing uses normal libxml2 limits and disables network
access. It checks well-formedness; the caller performs any required XSD validation.
Root counting includes fragment keys. Any generation error discards the result
and retains the original exception. Reader/hash/namespace/attribute traversal
checks cooperative cancellation, including failed generation followed by reuse.

Qore string readers receive already-converted UTF-8 bytes. They therefore call
`xmlReaderForMemory` with UTF-8 and the complete byte length, after checking the
library's int size limit. An older XML declaration cannot cause double decoding,
and a NUL cannot silently truncate input. Stream readers retain their separate
encoding contract.

XML 1.0 section 3.3.3 normalizes literal attribute tabs/newlines/carriage returns.
Generation writes these characters as numeric references to retain their values.
Attribute strings are normalized to UTF-8 before escaping, including wide-encoded
input strings. Other XML escaping and numeric-reference formatting remain intact.

Markup generation uses an ASCII-compatible buffer. If the requested output
encoding is not ASCII-compatible, it uses UTF-8 internally and converts the
complete document or fragment afterwards; document declarations still identify
the requested encoding. This avoids interpreting wide tag bytes as C strings and
satisfies the escaping API's encoding requirement. ASCII-compatible output retains
its direct generation path. Modern and deprecated XML entry points share this
contract; conversion errors return no partial document.

`test/xml-literal.qtest` covers namespace isolation, lexical/order preservation,
encoding/formatting, attribute normalization, malformed and hostile inputs,
reader byte lengths, cancellation/recovery and modern/legacy UTF-16 output.
`test/cmake` separately checks the selected native dependency and error cleanup.
