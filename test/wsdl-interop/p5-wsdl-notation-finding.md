# WSDL NOTATION conversion gap

Copyright (C) 2026 Qore Technologies, s.r.o.

During P5-18j, inspection of `BuiltinTypes`, `XsdBaseType::deserializeValue()` and
the native element-default fixture identified a separate WSDL gap. NOTATION is
advertised as a builtin. At the finding revision, the WSDL value converter had no
NOTATION dispatch and the schema model discarded the notation declarations needed
to validate expanded-name values. Native XML validation already covers these
declarations and their default namespace context in P5-18i.

Constructing an `XsdSchema` from the committed `notation/default` fixture with
the local WSDL reproduces `WSDL-ERROR: invalid value constraint for element
"value": SOAP-DESERIALIZATION-ERROR: don't know how to handle type "NOTATION"`.
The reproduction used the installed/frozen fixed Qore runtime `8c0c22c15` and
local Debug XML; files are in `/tmp/wsdl-p5-18j-wsdl-element-defaults/notation.*`.

[XSD Part 2 §3.2.19](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#NOTATION)
requires names of schema-declared notations and an enumeration-derived type;
direct use of the unrestricted NOTATION builtin is an error. The compatibility
recommendation for attributes and schemas without a target namespace does not
prohibit the element/default fixtures used here.

Required follow-up within P5: implement notation declaration resolution, QName
identity, enumeration/union/list constraints, default/fixed assessment, saved
metadata and provider/consumer conversion with positive and negative tests.
The `notation/default` and `notation/fixed` models in
`fixtures/element-defaults.json` provide the native baseline. Their `wsdl=False`
flag is an explicit coverage assignment, not a passing WSDL result. WSDL
key/unique/keyref similarly remain required before P5 closes.

This finding is independent of the default carrier. It does not authorize
removing NOTATION from supported scope or advancing past P5 with the gap open.


P5-19a completes additional native prerequisites discovered while implementing
this finding: declaration attributes/identifiers, normalized notation names,
enumeration-derived schema uses and allocation-error handling. The native
64-schema/231-document matrix and provider probe now cover them; see
[native evidence](native-notations-evidence.md). The WSDL conversion requirements
above remain open and are the next increment.

P5-19b completes WSDL declaration identifier storage, normalized-name/identifier
checks, duplicate detection, shared namespace registries, schema reconstruction and
failed-addition rollback; see [declaration evidence](notation-declarations-evidence.md).
The remaining required increment includes NOTATION value identity and conversion,
enumeration-derived component uses, remaining annotation/document-ID grammar checks,
list/union/default/fixed values, saved provider metadata and both SOAP HTTP directions.
Declaration storage does not count any previously failing NOTATION conversion as a pass.

P5-19d completes NOTATION value conversion, distinct primitive identity,
enumeration-derived use checks, saved scalar/list/union providers, default/fixed
handling, validated examples and both SOAP HTTP directions; see
[value evidence](notation-values-evidence.md). The qualified NOTATION default
fixtures are now exercised by the dedicated binding worker. The historical
`wsdl=False` selector remains unchanged for the older unqualified-root worker.
Remaining declaration annotation/document-ID grammar is assigned to the next P5
increment. Duplicate identity and legacy selected-type losses remain explicit
failed rows in the new report; key/unique/keyref and typed accounting must follow.
