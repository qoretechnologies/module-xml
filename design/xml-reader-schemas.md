# XML reader schema attachment

Copyright (C) 2026 Qore Technologies, s.r.o.

`XmlReader::schemaValidate(location)` loads a schema file or URI. This retains the
method's historical behavior and corrects its former description as an XSD-text
argument. `schemaValidateString(text)` explicitly compiles text. The constructor's
`xsd` option uses the same compilation and attachment path, with `xml_input_io`
providing an optional resource callback.

A schema can be attached to a string or InputStream reader before its first read.
Readers walking an existing XmlDoc cannot attach a streaming validation context;
use XmlDoc validation for those trees. All state checks also precede loading an
invalid candidate, so a late call does not initiate resource access.

## Ownership and replacement

A replacement schema is compiled before the reader's current validator is changed.
Compilation or resource-loading failure leaves the previous validator available.
After compilation, the reader's state is checked again: a resource callback can
reenter and advance that reader while the candidate is being compiled.

Once native attachment begins, the native context may retain the new schema even
if allocating its SAX plug fails. The reader therefore owns that candidate on
both successful and failed attachment. An attachment failure blocks subsequent
reads until a successful retry; it cannot silently turn validation off. Reader
cleanup releases the native context before releasing the compiled schema.

These lifetimes follow the
[libxml2 reader schema contract](https://gnome.pages.gitlab.gnome.org/libxml2/html/xmlreader_8h.html).
No schema object is passed through a temporary whose destruction precedes the
native context that refers to it.

## Resources and callbacks

The shared schema compiler scopes its exception context to the current thread and
restores the previous context during nested compilation and cleanup. Each callback
resource owns its own InputStream, so nested invocations do not overwrite a shared
stream slot. A callback returning NOTHING permits ordinary resource resolution;
an exception instead returns a failed resource that prevents unchecked fallback.
The original exception survives native parser cleanup.

Memory-only schema text and callbacks require no external-resource permission.
Actual file and catalog loads enforce the program's filesystem restriction and
its sandbox path policy. File URI decoding uses libxml2's path rules before the
policy check. Authorized files continue through libxml2's native file loader.
HTTP/HTTPS resources use Qore's transport, including destination and redirect
checks, cancellation and decoding of HTTP content encodings. XML bytes retain their
own document encoding. Redirects update the schema's base URI before relative
imports are resolved. HTTPS verifies the certificate and hostname using Qore's
configured OpenSSL trust store, including explicit `SSL_CERT_FILE` and
`SSL_CERT_DIR` configuration. Legacy FTP builds use Qore's FTP transport for that scheme.

libxml2 2.14 and later provide a per-schema resource loader. Older supported
builds use an entity-loader wrapper scoped to this compiler; other calls delegate
to the previously installed loader. These implementations preserve the respective
input-buffer ownership rules of the old and new native APIs.

System catalogs are not disabled. They are themselves resources subject to
filesystem policy. Applications needing catalogs must permit those files and the
resources they resolve. The independent HTTP test server uses an explicitly empty
catalog configuration for isolation, and a separate catalog test checks both
catalog access and access to the resolved schema.

## Example

```qore
%modern
%requires xml

XmlReader quantities(new StringInputStream("<quantity>17</quantity>"));
quantities.schemaValidateString(
    '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="quantity" type="xs:int"/></xs:schema>');
@assert(quantities.read());
@assert(quantities.toQore() == "17");
@assert(!quantities.read());
@assert(quantities.isValid());
```

For an existing schema package, call
`reader.schemaValidate("/opt/contracts/catalog.xsd")` before the first read.
Imports then resolve relative to that package rather than to a text buffer with
no document base URI.

## Verification

`test/xml-reader-schemas.qtest` covers attachment, ownership, failed replacement,
state, encoding, cancellation, filesystem policy, nested callbacks and reentrant
advancement. `test/wsdl-interop/test_schema_resources.py` uses an independent local
HTTP server and explicitly configured catalogs to verify resource resolution and
policy. The 300-document QName union matrix checks both attachment methods against
the same pinned Xerces verdicts and exact text/attribute values used for the native
DOM and constructor-reader paths. The older libxml2 compatibility harness is kept
separate from the production dependency probe and its known QName defects.
`legacy_schema_ftp.py` runs explicitly against a module built with
`LIBXML_FTP_ENABLED`, verifying byte-preserving transfers, relative includes,
failed transfers, destination denial and recovery with an independent FTP peer.
