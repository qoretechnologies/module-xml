# Attribute value constraint oracle adjudication

Copyright (C) 2026 Qore Technologies, s.r.o.

`test_attribute_values.py::AttributeValuesTest::test_attribute_defaults_reject_invalid_schema_constraints`
contains a global string attribute `unit` fixed to `EUR`, and a local reference
that changes the fixed value to `USD`. libxml2 2.12.10 (lxml 6.1.1) accepts the
schema without a diagnostic, both with and without a global element using the
containing complex type.

[XSD 1.0 §3.5.6, Attribute Use Correct, clause 2](https://www.w3.org/TR/xmlschema-1/#au-props-correct)
requires a local value constraint referring to a fixed global declaration to be
fixed to the same value. Xerces-J 2.12.2 rejects the source with
`au-props-correct.2`; Qore rejects it with `WSDL-ERROR`. The source is invalid.
The libxml2 acceptance is an explicit oracle limitation, and does not count as
a valid-source result. A libxml2 version that rejects it satisfies the same test.

The positive test independently checks eight SOAP outputs across request and
response directions and separate actual SOAP 1.1/1.2 bindings. Both validators
accept the output payloads, and exact attribute checks require `false`, `7` or
explicit `0`, and `EUR`. Four supplied `USD` inputs must fail deserialization.
