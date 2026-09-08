# Boolean restriction evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 Part 2 [boolean §3.2.2](https://www.w3.org/TR/xmlschema-2/#boolean)
defines four lexical spellings, two values, and only pattern/whiteSpace as applicable
facets. Whitespace is fixed to collapse. [Pattern §4.3.4](https://www.w3.org/TR/xmlschema-2/#rf-pattern)
constrains lexical spellings; same-step alternatives are intersected with inherited
patterns. XML Schema Part 1 [attribute validation](https://www.w3.org/TR/xmlschema-1/#cvc-attribute)
compares fixed constraints in the actual value space.

The preflight `/tmp/wsdl-p3-09-preflight.json` showed Qore accepting invalid boolean
enumeration/ordered-bound schemas and serializing a valid pattern-1 value as `true`.
Pinned Xerces rejected both invalid schemas, accepted all four real SOAP input
payloads and rejected all four emitted payloads. Root causes were missing facet
applicability checks, pattern checks after boolean conversion, and canonical output
that discarded a pattern-required spelling.

The implementation keeps lexical spelling and boolean value checks separate. It
retains accepted patterned strings through schema/provider reconstruction and uses
boolean equality for fixed attributes and field choices. Defaults must pass the
restriction after the base provider supplies them. Examples exhaust the four legal
spellings, detecting empty pattern intersections without an unbounded search.

`test_boolean_facets.py` reuses the accounting and consumer checks from
`test_list_values.py` through explicit case/schema/value hooks. The original list
matrix remains intact. Ten boolean cases produce 30 schemas and 60 real SOAP
contracts per matrix, with atomic values, simple content plus attributes, repeated
values, fixed false flags, and lists of patterned boolean items. The tests check
492 input documents, 228 emitted binding documents, 3104 consumer results and
1600 provider/example documents: 2320 independently validated documents in total.
All values, item order, repeated occurrence counts, expanded payload names and SOAP
envelope versions are asserted separately from schema validity.

Twenty invalid schemas exercise each forbidden facet directly and through a named
boolean base. Qore rejects all 40 SOAP contracts with `XSD-SIMPLETYPE-ERROR`;
libxml2 and Xerces both reject all 20 schemas. The valid matrices require identical
document verdicts from both independent processors and no warnings. No validator
exception or Qore result is waived for this increment.

The focused Qore suite covers metadata rejection, optionality, native scalar
boundaries, ordered text/CDATA, preserved comments, detached providers, inherited
defaults, fixed attribute references/restrictions, atomic choice updates and
controlled cancellation. P3 union, IEEE float/double, calendar/duration, binary,
QName/entity and remaining regex requirements remain open; P4–P9 remain required.
