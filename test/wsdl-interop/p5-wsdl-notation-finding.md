# WSDL NOTATION conversion gap

Copyright (C) 2026 Qore Technologies, s.r.o.

During P5-18j, inspection of `BuiltinTypes`, `XsdBaseType::deserializeValue()` and
the native element-default fixture identified a separate WSDL gap. NOTATION is
advertised as a builtin, but the WSDL value converter has no NOTATION dispatch and
the schema model does not yet maintain the notation declarations needed to
validate expanded-name values. Native XML validation already covers these
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
