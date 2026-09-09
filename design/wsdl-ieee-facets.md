# WSDL IEEE restrictions and value identity

Copyright (C) 2026 Qore Technologies, s.r.o.

IEEE restrictions use the strict conversion described in
[WSDL scalar conversion](wsdl-ieee-scalars.md). Values and facet endpoints are
rounded directly to the declared binary32 or binary64 format before comparison.
No decimal-display heuristic, tolerance or epsilon participates in validation.
For example, float `minExclusive="1"` rejects `"1.00000001"`: both denote the
same binary32 value. Double retains enough precision to distinguish them.

## Comparisons and lexical forms

`XsdNumericFacetHelper` dispatches to the builtin's value comparison. Decimal
and integer comparisons retain exact text; native decimal carriers use the
existing lossless decimal formatter. IEEE comparison returns a partial relation:
equal, less, greater or incomparable. XSD 1.0 identifies NaN with itself and
identifies both zeros. NaN and any other value are incomparable. Thus a NaN
inclusive bound admits only NaN, a NaN exclusive bound admits nothing, and
ordinary numeric bounds reject NaN. Infinity participates in the ordinary order.

Patterns still constrain normalized XML spelling. IEEE conversion does not
replace an authored spelling before pattern validation. Restrictions preserve
strings when the pattern requires them, including `001.00e0`; unrestricted
decoded values retain native float output. Bounds, enumeration and fixed
values use target identity independently of that spelling.

Facet construction checks inherited endpoints, fixed facet identities and
contradictory bounds in the same value space. Repeating the same exclusive
endpoint is valid even when different decimal spellings round to that endpoint.
`totalDigits` and `fractionDigits`, including zero, are inapplicable to IEEE
types and cause a schema error. Fixed digit counts on decimal-derived types use
their own integer count space, independently of the field's builtin range.

## Providers, fields and collections

`XsdNumericRestrictionDataType` uses the same constraints for standalone,
optional, reconstructed and nested-list providers. Numeric provider classes
expose `getBuiltinName()`. Reconstruction rejects conflicting known base
provider identities, such as float metadata wrapping a double or integer
provider. Custom providers retain their existing conversion responsibility.

`XsdNumericDataField` keys finite choices by rounded identity. It retains their
authored spellings for display and validates new choice lists before replacing
the previous metadata. Failed updates preserve the previous restrictions.
The shared fixed-attribute comparator also handles IEEE, decimal, integer,
boolean, list and union identities in references and complex restrictions.

IEEE list enumeration compares items in order, including NaN and both zeros.
Union identities retain the selected primitive family: float, double and
decimal have disjoint value spaces under XSD 1.0. Numeric promotion must not
make a float member satisfy a double-only enumeration. Existing union lexical
preservation keeps the selected family stable through serialization and
detached provider reconstruction.

## Valid examples at IEEE boundaries

Example generation first validates pattern candidates, the supplied default,
inherited enumeration spellings and zero. For bounded IEEE types it then tries
each endpoint and its adjacent representable target value toward the permitted
side, checking every candidate against the whole restriction chain. The work
is bounded by the number of declared facets; it never enumerates the float
value space. Failure to find a valid candidate raises `XSD-SAMPLE-ERROR`.

The adjacent-value calculation uses `logb` to extract the binary exponent and
`exp2` to obtain an exact power-of-two spacing. It handles powers of two,
subnormals, signs, zero and infinity explicitly. Every finite addition or
subtraction produces an exactly representable target value. The exponent must
not come from a rounded logarithm. An independent test walks IEEE encodings to
construct singleton and empty intervals around boundary and seeded values.

```qore
%modern
%requires WSDL

XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:simpleType name="Reading"><xs:restriction base="xs:float">
      <xs:minExclusive value="1"/>
      <xs:maxInclusive value="1.00000011920928955078125"/>
    </xs:restriction></xs:simpleType></xs:schema>', {"async_only": True});
XsdSimpleType reading = cast<XsdSimpleType>(schema.findType("Reading"));
float sample = reading.getSampleValue(0.0);
@assert(sample == 1.00000011920928955078125);
@assert(cast<XsdNumericRestrictionDataType>(reading.getDataProviderType()).getBuiltinName() == "float");
```

Normative references are [XSD 1.0 float/double](https://www.w3.org/TR/xmlschema-2/#float),
[datatype equality](https://www.w3.org/TR/xmlschema-2/#dt-equal) and
[minExclusive derivation](https://www.w3.org/TR/xmlschema-2/#rf-minExclusive).
The [GNU exponent documentation](https://sourceware.org/glibc/manual/latest/html_node/Exponents-and-Logarithms.html)
explains exponent extraction. [Independent evidence](../test/wsdl-interop/ieee-facets-evidence.md)
records validator disagreements without changing the original schemas or expected values.
