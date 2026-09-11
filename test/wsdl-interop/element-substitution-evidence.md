# P5-06 element affiliation and native substitution evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The prior WSDL parser ignored global element `final` and `substitutionGroup`
values. A member without an explicit type received `anyType`. The retained
before reproduction accepts incompatible integer/string affiliations, cycles
and a builtin restriction excluded by its head's final set. Declaration graph
resolution now rejects these with `WSDL-ERROR` and inherits omitted types from
the resolved head. QName syntax errors use `WSDL-NAMESPACE-ERROR`.

The normative requirements are XSD 1.0 Structures [element property mappings](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Element_Declaration_details),
[Element Declaration Properties Correct](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct),
[Substitution Group OK (Transitive)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-equiv-derived-ok-rec)
and [Type Derivation OK (Simple)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-derived-ok).
The published [second-edition errata](https://www.w3.org/2004/03/xmlschema-errata)
were checked; they do not revise these affiliation or blocking rules. The local
design documents implemented declaration behavior separately from instance type
selection, whose intermediate-block rule is different.

`wsdl-element-substitution.qtest` exercises effective final controls, inherited
types, namespace scopes, imports and chameleon includes, invalid/cyclic graphs,
abstract and blocked members, intermediate complex blocks, references, atomic
incremental construction, cancellation and concurrent reconstruction.
`test_element_substitution.py` builds 72 schemas: 40 valid and 32 invalid.
The shared type-final worker runs actual SOAP 1.1 and 1.2 contracts in both
directions, original and reconstructed: 384 rows, 64 required construction
errors and 320 independently validated outputs. Inherited message roots carry
their integer `item` value through serialization and decoding.

The independent membership matrix supplies 31 schema groups and 102 standalone
particle documents. It compares 62 original/reconstructed WSDL membership maps
with normative expectations and validates documents with native libxml2,
lxml 6.1.1/libxml2 2.12.10 and checksum-pinned Xerces-J 2.12.2. Source schemas and
documents are generated deterministically and are not rewritten for an oracle.
`ORACLE_DIFFERENCES` records four disagreeing documents, all normative negatives:

| Document | lxml 2.12.10 | Xerces-J 2.12.2 | Corrected native libxml2 |
| --- | --- | --- | --- |
| Nonabstract decimal head blocks restriction; transitive int member | accepts | rejects | rejects |
| Abstract decimal head blocks restriction; transitive int member | accepts | rejects | rejects |
| Member restricts an intermediate type which extends the head and blocks extension | accepts | rejects | rejects |
| Union head blocks restriction; member uses the identical builtin int union member | accepts | accepts | rejects |

The first two libxml2 failures come from `xmlSchemaCheckElemSubstGroup()` testing
restriction declaration flags on builtin simple types. Those flags do not carry
the builtin derivation relationship, so its method set was empty. The third
failure comes from the extension accumulator testing the restriction bit: once
restriction was seen, later extension was not recorded. Both errors persist in
unpatched 2.15.4. The private fix counts simple steps as restriction and accumulates
both methods independently. It also fixes the union case: the member type and
union head are different definitions, so the simple derivation's restriction
exclusion applies before the union-member alternative in §3.14.6(2.1,2.2.4).

The Xerces union discrepancy was reproduced against the pinned jar and traced
with `javap -c -p` to `SubstitutionGroupHandler.typeDerivationOK()`. Its union
alternative recurses with the original derived type and a union member, resetting
the accumulated methods. An identical member returns success with no derivation
method, bypassing the containing union's exclusion. The same logic is visible in
the [Apache source](https://github.com/apache/xerces2-j/blob/trunk/src/org/apache/xerces/impl/xs/SubstitutionGroupHandler.java).
This supporting-oracle discrepancy stays explicit; it does not change the
required module verdict or count an invalid instance as valid.

`xml-element-substitution.qtest` covers native DOM and streaming validation,
repetition, invalid values/names, both orders of complex derivation, transitive
abstract groups, union restrictions and schema replacement after failure.
The 45-schema C configure probe checks DOM and reader verdicts; provider tests
build a real shared dependency without only this correction and verify AUTO
fallback, SYSTEM rejection, acceptance of corrected backports, source hashes
and repeat-configuration stability. The source archive includes the new probe
and correction through `Makefile.am`.

This increment completes declaration resolution and native validator blocking.
WSDL particle attribution of alternate member names, preservation of selected
element identity at message roots, native/retained element conversion, provider
shapes and sample selection remain the next P5 work. Their corpus failures stay
visible. Other open P5 semantics and the P6–P9 deliverables retain their existing
ownership; this increment is not the P5 acceptance boundary.
