# P6-07 imported WSDL components

Copyright (C) 2026 Qore Technologies, s.r.o.

The old constructor compiled only the root WSDL and keyed components by local
name. Imported abstract messages and port types could not supply a separate
binding document, and equal local names in different namespaces could not remain
distinct. The document catalog now collects the transitive source graph before
validating expanded component references and compiling its declarations.

[WSDL 1.1 sections 2.1.1–2.1.2](https://www.w3.org/TR/wsdl.html#_document-n)
define QName linking and imported authoring; the latter includes importing an
XSD document directly. Each import checks the required target namespace, and
references retain their declaration's prefix/default-namespace scope. Relative
HTTP locations use the containing document URI under
[RFC 3986 section 5.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2).

The cross-file fixture also exposed RPC wrappers using the port-type namespace
instead of `soap:body/@namespace`. Serialization now uses the selected input or
output body namespace, and decoding checks that expanded wrapper name. This
corresponds to [WSDL 1.1 section 3.5](https://www.w3.org/TR/wsdl.html#_soap:body).
Operation input/output naming and overload semantics remain separate P6 work.

The final focused suite `test/wsdl-imported-components.qtest` has 15 cases and
166 assertions. It covers:

- Three- and five-document graphs, cycles, diamonds and same-local-name
  messages/port types/bindings/services in distinct namespaces.
- Exact object selection for input, output, fault and header message references;
  scoped prefixes/default namespaces and actual SOAP 1.1/1.2 binding versions.
- Unique local names and explicit expanded public lookups, ambiguous local-name
  rejection, wrong-namespace rejection and standalone saved operation aliases.
- Forward schema types across imported WSDLs, WSDL imports of XSD, shared WSDL/XSD
  schema retrieval/instantiation, self-includes, typed values and invalid values.
- Offline service reconstruction without an external cache, source-graph
  fingerprints, changed dependencies, schema additions and compatibility options.
- Both SOAP versions through local client/handler exchanges, independent authored
  request/response wrappers with different body namespaces, message providers and
  generated examples.
- Exact HTTP query targets through all three loaders, fragment deduplication,
  root cycles, callback reference names, callback interruption and successful retry.
- Missing import attributes/resources, wrong root or namespace, duplicate expanded
  declarations, and conflicting namespace requirements for one cached resource.

The final audit caught a schema reached through both WSDL and XSD import paths
being instantiated twice. The fix shares its retained bytes and the existing
per-resource/per-namespace schema registry. Both traversal orders, a self-include,
offline reconstruction and a single callback retrieval are tested. The large
fixture run started before this correction was terminated and retained under
`/tmp/wsdl-p6-07-imported-components/pre-shared-schema/`; it is not passing evidence.

## Independent observations

`python3 -B test/wsdl-interop/test_wsdl_imports.py -v` runs five tests using the
pinned WSDL4J 1.6.3 artifact. The JAR, upstream license and notice are checked
against `oracle/wsdl4j-manifest.json`; compilation uses `javac -Xlint:all -Werror`.
All imports are restricted to the fixture directory and no network is required.
The [Maven artifact](https://repo.maven.apache.org/maven2/wsdl4j/wsdl4j/1.6.3/)
and [upstream distribution](https://downloads.sourceforge.net/project/wsdl4j/WSDL4J/1.6.3/wsdl4j-bin-1.6.3.zip)
are pinned by checksum, with unmodified notices retained.

The Java observer asserts complete sets of ten resolved rows for the five-document
cycle/diamond graph and sixteen for the namespace-collision graph. Rows identify
binding-to-port-type, service-port-to-binding, input/output-to-message, message
part type, SOAP extension namespace and body namespace. The observer rejects
undefined declarations and missing resources. Its mismatched-import test leaves
the requested binding unresolved; that result is not presented as an independent
direct namespace-mismatch validator. It does not adjudicate all WSDL grammar,
cross-document duplicate declarations, headerfault wire behavior or SOAP messages.
The direct namespace/duplicate checks are asserted by the Qore regressions.

The earlier independent matrices also pass: 25 WSDL declaration cases, 21 QName
lexical/reference cases and seven contract inventory tests. These distinguish
schema lexical validity from reference validity.

See [validation](P6-07-validation.json), [audit](audits/P6-07-imported-components.md)
and [implemented design](../../design/wsdl-component-references.md). Canonical
file URI handling, effective bases after redirects, overload/input-output naming,
explicit operation selection and the remaining P6 binding matrix are still open.
No P6 phase boundary, complete WSDL grammar or SOAP profile conformance is claimed.


## Final gates

The 35 affected suites pass 457 cases / 7,256 reported assertions, including the
existing seven intentionally caught comparator assertions. The separate full
enterprise/partner description suite passes 5 cases / 85 assertions in 644.710 s.
All six corpus reports match P6-06 outside version metadata; native mode retains
2,096 valid successes and legacy mode retains 2,084 successes plus 12 explicit
projection losses. All 176 invalid-source directions remain rejected. Both
module documentation targets complete without warnings or errors. Runtime and
source hashes were unchanged throughout these gates; complete commands and
results are retained under `/tmp/wsdl-p6-07-imported-components/` and summarized
in the validation record.
