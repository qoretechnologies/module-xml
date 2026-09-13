# Native NOTATION acceptance

Copyright (C) 2026 Qore Technologies, s.r.o.

P5-19a corrects the native prerequisites for the separately tracked WSDL NOTATION
gap. It is based on `16be41b`, with the installed/frozen Qore runtime
`8c0c22c150c6e51ed09976ca99d74041ec074620`. The installed ELF and library hashes
still match the verified runtime. Nothing was installed or pushed.

The original parser accepted a notation with neither identifier, unknown
attributes and used unenumerated NOTATION types. Its name storage also retained
whitespace that the NCName datatype collapses. Allocation injection exposed
unchecked attribute-content extraction and ID normalization. The corrected
implementation and its boundaries are described in the
[native design](../../design/native-notations.md).

The behavioral provider test reconstructs the immediately preceding private
library: element defaults and QName allocation probes pass, while the new
NOTATION probe fails. AUTO selects the corrected bundled library and SYSTEM
rejects the broken one. A corrected system library passes, including the
alternative-diagnostic fixture. Reconfiguration preserves generated source
contents/timestamps. Three older synthetic backport tests now locate the active
`xmlschemas.c` target source instead of assuming the last correction's directory.

The authored matrix contains **64 schemas and 231 documents**. It covers required
and empty identifiers, foreign/schema attributes, normalized names/IDs,
duplicates, missing declarations, inherited/late enumerations, local/global
attributes and elements, simple content, collection types, default/fixed values,
imports, no-target-namespace schemas and instance type selection. Namespace aliases
compare equal; equal public identifiers do not equate different notation names;
NOTATION and QName have distinct primitive identity in uniqueness constraints.
The three native APIs assert the intended error category and preserve the input
XML. The Qore suite has **848 assertions**.

Pinned Xerces-J 2.12.2 is checked separately for schema and instance verdicts.
Seven explicit disagreements are retained: direct NOTATION list/union components,
used unrestricted simple content, and used/unused collections of an unrestricted
restriction. These components violate the schema-use requirement in
[XSD 1.0 Part 2 §3.2.19](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#NOTATION).
Xerces accepts them. The test records those actual oracle outcomes without
converting the module's required rejections into passing inputs. The same section
specifies a nonempty lexical space of declared notation QNames; the schema-use
constraint is not an additional prohibition on instance-only type selection.

`public` follows the XML Schema token grammar, `system` follows anyURI, and at
least one must be present, per
[Part 1 §3.12](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cNotation_Declarations).
The compatibility recommendation concerning attributes and no namespace does not
prohibit namespaced element values. The final matrix includes late simple-content
restriction as a control for valid intermediate definitions.

Final checks:

- All **166 Qore suites** pass, including schema callbacks, cancellation,
  SOAP/provider/HTTP consumers and the new NOTATION suite.
- All **65 dependency/provider tests** pass, including source distribution,
  behavioral selection, idempotence and native allocation paths.
- All **13 supplemental runs** pass: four execution modes, six Python checks
  including the independent matrices and survey tests, and three Valgrind runs.
- All **1,064 single/persistent injected allocation failures** propagate, release
  owned resources and allow recovery. The absent-attribute control retains its
  legitimate empty value independently of extraction failure.
- Direct-ELF Valgrind runs on NOTATION, existing element defaults and the native
  allocator test report zero errors and zero definitely/indirectly/possibly lost
  memory. Qore runs use `-b --enable-debug` and `QORE_PCRE2_NO_JIT=1`; ordinary
  acceptance uses JIT normally.
- Both SOAP-version surveys and strict coverage, with legacy and native decoding
  recorded separately, are **byte-identical** to the parent reports.
- Debug native/module compilation and native documentation complete without
  warnings or errors. The full audit has **19 Pass, 43 N/A, zero Fail**.

The broad Qore manifest includes the independent Python provider test. That file
changed during the Qore run solely to repair the three synthetic source-path
fixtures; no executed Qore input changed. The final full provider run verifies its
own frozen hash. The inventory retains both facts rather than claiming that the
broad manifest was unchanged.

Reproduce with `qore -b --enable-debug test/xml-notations.qtest`,
`python3 -B test/wsdl-interop/test_notations.py -v` and
`python3 -B test/cmake/test_libxml2_provider.py -v`, selecting local Debug XML and
qlib through `QORE_MODULE_DIR`. The imported fixture's relative schema location
is resolved to its committed local file for native APIs; pinned Xerces receives
the same bytes through its explicit resource map. No network service is needed.

Logs, commands, runtime/source hashes and complete corpus reports are under
`/tmp/wsdl-p5-19-notation/final/`; the committed
[inventory](P5-19a-validation.json) and [audit](audits/P5-19a-native-notations.md)
record the exact candidate. Intermediate failures and superseded runs remain in
`/tmp/wsdl-p5-19-notation/` for diagnosis.

This closes the native notation prerequisite. WSDL notation declaration storage,
value/provider conversion and both SOAP consumers remain the next P5 increment,
followed by key/unique/keyref and complete typed-preservation accounting. P5 and
P6–P9 are not yet complete.
