# P5-16b element constraint declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

The constructor previously retained only a constraint-present flag and checked
the ban on ID-derived default/fixed values. Invalid lexical defaults and fixed
values therefore passed schema construction, as did constraints on incompatible
complex content. The declaration's converted value and namespace context were
not available to consumers.

`XsdElement` now retains a typed constraint hash and validates it after type
resolution and complex-content finalization. References consult their global
declaration. Conversion runs inside a declaration namespace scope and publishes
only a successful result. Document-dependent ENTITY checks remain instance
requirements; schema declaration validity uses the datatype directly.

| Requirement | Implementation and regression evidence |
| --- | --- |
| P5.EC1: Element Declaration Properties Correct, clause 2 | `validateValueConstraintType()` rejects lexical values outside the resolved datatype; scalar restrictions, lists, unions and forward declarations in the Qore suite and independent matrix. |
| P5.EC2: Element Default Valid (Immediate), clauses 1–2 | `allowsElementValueConstraint()` requires simple content or mixed content with an emptiable particle; empty and element-only models fail, optional/nested-choice mixed models pass. Required attributes remain permitted on the declaration. |
| P5.EC3: Element Declaration Properties Correct, clause 3 | Existing ID-derived constraint ban remains; builtin ID negatives in both local/global independent schemas and affected declaration/derivation suites. |
| P5.EC4: Constraint ownership and namespace identity | Separate defaults/fixed values on a shared type, empty versus absent metadata, qualified/unqualified QName and QName-list values, unbound-prefix union fallback, import-prefix collisions and global references. |
| P5.EC5: Reconstruction and exception safety | Whole-schema and detached-reference serialization retain constraints. Failed schema additions preserve earlier declarations. Controlled conversion failures and real sandbox cancellation retain the previous value, restore QName scope and permit subsequent successful validation. |
| P5.EC6: Actual WSDL binding construction | 188 independently compiled schemas are each embedded in real SOAP 1.1 and SOAP 1.2 binding descriptions: 376 parse outcomes, with exact `WSDL-ERROR` categories for rejection. |

The normative source is W3C XSD 1.0 Second Edition,
[Element Declaration Properties Correct](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct)
and [Element Default Valid (Immediate)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-valid-default).
The matrix uses pinned Xerces 2.12.2 through `independent.py`: 104 valid and 84
invalid schemas, all agreeing. Generated schema hashes and the exact manifest
are recorded in [the inventory](P5-16b-validation.json). Original corpus files
and historical adjudication are unchanged.

The final Qore suite has nine cases/153 assertions. Four source execution modes
and the default-compiled WSDL module pass. The full 137-suite source gate has
1,332 cases/65,931 reported assertions, including the final expanded test.
Fourteen supplements pass, including affected AOT consumers and six Python
suites. The complete new suite has zero Valgrind errors and zero lost blocks.
Documentation and the catalog quantity example pass without warnings.

The both-version corpus and strict adjudicated coverage have exactly the same
outcomes as P5-16a; only the recorded WSDL source hash changes. All 144 selected
WSDLs/1,388 directions pass. The 28 valid-input directions and 44 broader failure
records remain visible. The separately reproduced QName AOT stack finding keeps
P9 runtime ownership. Instance default application, fixed-value comparison,
nil validation and remaining P5/P6–P9 requirements remain open; this increment
completes declaration construction and its public metadata contract.

Reproduce from the repository root with the local debug XML module and local
`qlib` on `QORE_MODULE_DIR`:

```sh
qore -b --enable-debug test/wsdl-element-constraints.qtest
python3 test/wsdl-interop/test_element_constraints.py -v
python3 test/wsdl-interop/survey.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 --soap-version both --output /tmp/wsdl-current.json
python3 test/wsdl-interop/coverage.py /tmp/module-xml-wsdl-survey/databinding/examples/6/09 --strict --output /tmp/wsdl-coverage-current.json
```

Exact commands, artifacts, runtime hashes and logs are in
`/tmp/wsdl-p5-16-declaration-validation/` and the inventory. The
[full audit](audits/P5-16b-element-constraints.md) covers all 62 checklist items.
