# WSDL scalar lexical validation

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdBaseType` validates integer XML lexical forms before native conversion in
both serialization directions. All thirteen integer builtins require ASCII
digits; signed integer types permit one leading sign, while XSD 1.0 unsigned
types require digits alone. Empty or absent text, fractions, exponents, trailing
data and non-ASCII digits raise `SOAP-SERIALIZATION-ERROR` or
`SOAP-DESERIALIZATION-ERROR` at the corresponding API boundary. Boolean, null,
binary and structured values cannot masquerade as native integers.

Whitespace normalization replaces TAB, LF and CR with SPACE. Collapse additionally
merges SPACE runs and removes leading/trailing SPACE. Other characters remain
available for lexical validation to reject; generic language whitespace trimming
is unsuitable. `normalizedString` uses replacement and `token` uses collapse.
For example, an integer field containing `" \t001\r\n "` has the value one;
`"1.0"`, `"1tail"` and `"1\x00tail"` are invalid integer lexical forms.

This gate preserves existing native return types and conversions. It does not
establish precision, range, facet, provider or generated-example correctness;
the remaining scalar requirements and their failing diagnostics are maintained
in the interoperability execution plan. Retained XML values continue to use the
additive public contract documented in `wsdl-xml-values.md`.

`test/wsdl-integer-lexical.qtest` covers all integer builtins, invalid value types,
attributes/simple content, reconstruction, lists/unions and whitespace. The
independent `test/wsdl-interop/test_integer_lexical.py` exercises actual SOAP 1.1
and 1.2 bindings in both directions, validates 936 input/output documents with
libxml2 and Xerces, and compares exact small integer values and expanded names.
