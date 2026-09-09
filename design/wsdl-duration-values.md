# WSDL duration lexical values

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdBaseType` validates `xs:duration` text before serialization or deserialization.
The grammar follows XSD 1.0 Second Edition §3.2.6.1: ASCII component digits,
ordered year/month/day and hour/minute/second fields, an optional single leading
minus, at least one component and at least one time component after `T`.
Fractional seconds require digits on both sides of the decimal point. XML
whitespace collapses before validation; other whitespace and trailing text reject.

The decoded value is always an XML string. Component sizes and fractional precision
are retained without native numeric conversion, rounding heuristics or tolerances.
For example, `PT1.00000000000000001S` and `PT1.00000000000000002S` remain distinct.
Original component spelling and zeros are preserved after whitespace normalization.

A native Qore relative date is accepted as an input convenience. Its year/month
components combine into months and its day/hour/minute/second components combine
into whole seconds, with microseconds kept separately. This avoids overflowing
64-bit arithmetic at the native 32-bit day limit. Within-group mixed signs normalize:
one day minus one hour becomes `PT23H`. A consistent negative duration gets one
leading minus sign, and microseconds retain up to six fractional digits.

Opposing nonzero month and second groups cannot be represented by an XSD duration
without a reference date and therefore reject. Absolute dates also reject. The
native formatter supports Qore relative-date forms beyond XSD's grammar, so the
XSD conversion builds and validates its own representation. The decoder applies the
same conversion to explicit native relative-date input; unrelated scalars and
containers are never coerced into duration strings.

`XsdDurationDataType` accepts string/date input and returns string output. Its
empty direct-acceptance map and unspecified native value type ensure enclosing
providers validate every value. Optional and reconstructed providers retain this
contract. Required omission raises `MISSING-VALUE-ERROR`; invalid provider input
raises `RUNTIME-TYPE-ERROR`. Wire serialization/deserialization use their existing
SOAP error categories. Scalar provider metadata is immutable after construction;
reconstruction validates optionality before assigning it. Numeric/calendar restrictions and
list metadata also recognize duration providers and reject incompatible builtin identities.

Basic lists, unions, attributes, elements and messages use this duration conversion.
The exact component checks here establish lossless lexical/native conversion;
they do not substitute component-pair equality for XSD's duration partial order.

```qore
%modern
%requires WSDL

XsdDurationDataType processing_interval();
@assert(processing_interval.acceptsValue(microseconds(-1)) == "-PT0.000001S");
@assert(processing_interval.acceptsValue(days(1) + hours(-1)) == "PT23H");
@assert(processing_interval.acceptsValue("PT0.00000000000000001S") == "PT0.00000000000000001S");
```

[Normative grammar](https://www.w3.org/TR/xmlschema-2/#duration-lexical-representation)
and [independent validator evidence](../test/wsdl-interop/duration-values-evidence.md)
explain the lexical boundaries. Tests cover native limits, 1,000-digit components
and fractions, provider reconstruction/cancellation/recovery and actual SOAP
bindings with independent exact-value assertions and local HTTP exchanges.
