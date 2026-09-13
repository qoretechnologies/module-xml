# Default QName/NOTATION namespace context: pinned oracle disagreement

Copyright (C) 2026 Qore Technologies, s.r.o.

The NOTATION binding matrix emits empty elements when an `XsdDefaultValue` retains
an applied default or fixed value. Pinned Xerces 2.12.2 rejects 48 such outputs
when the instance omits the schema default's prefix binding, or uses a different
default namespace. The module's native and WSDL validators retain the declaration
identity and accept these outputs. Ordinary mode materializes explicit text and
its namespace binding; those outputs agree with Xerces.

`fixtures/notation-default-context.json` contains four separately identified
schema derivatives and 12 empty documents. Provenance includes original fixture
hashes, model names and the exact QName-base substitution. Original fixtures are
unchanged. Both QName and NOTATION variants compare three instance contexts:
the schema's binding repeated, absent, and rebound. Native DOM/reader/document
validation accepts all 12; pinned Xerces accepts only the four repeated contexts.
The prefix spelling does not occur in the empty instance, and rebinding it does
not change the declaration's already resolved default expanded name.

This behavior is classified against the schema value-constraint component and
[XSD 1.0 cvc-elt 5.1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt),
using the already approved [default interpretation](default-identity-investigation.md).
The WG separately recorded that instance prefix validation for an added QName
default is absent in XSD 1.0 in [issue 2103](https://www.w3.org/Bugs/Public/show_bug.cgi?id=2103),
and deferred it. The later [issue 2748](https://www.w3.org/Bugs/Public/show_bug.cgi?id=2748)
describes namespace fixup as implementation-dependent. That later discussion is
supporting context, not a claim that XSD 1.1 rules replace the project's XSD 1.0 target.

The observed oracle defect is that changing only the empty instance's namespace
context changes acceptance of a declaration-owned QName/NOTATION default. The
report records every disagreement and the actual Xerces verdict; it does not
rewrite emitted XML to repeat an otherwise unused schema prefix. The independent
reduction and binding report run in `test_wsdl_notation_values.py`. All other
emitted payloads require agreement with the native output verdict.
