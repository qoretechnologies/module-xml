# Native binary constraints and lexical validation

Copyright (C) 2026 Qore Technologies, s.r.o.

The native compiler applies the [canonical declaration checks](native-numeric-defaults.md)
to `hexBinary` and `base64Binary`. XSD 1.0 defines
[uppercase hexadecimal digits](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#hexBinary-canonical-representation)
and [Base64 without whitespace](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#base64Binary)
as their canonical forms. For example, a
`hexBinary` type restricted by pattern `ab00ff` accepts that explicit value but
cannot use it as a default: canonical `AB00FF` fails the pattern. A restriction
with pattern `ab00ff|AB00FF` permits the declaration.

The compiler reads the canonical form from the selected computed binary value.
Lists assemble item forms in order; unions canonicalize only their chosen
member. A string-first union keeps its lexical value. Original declaration
values, QName context in mixed lists and explicit XML content remain unchanged.
Empty binary values and empty/singleton lists have distinct computed forms and
are tested separately. Canonical strings and the joining buffer retain local
ownership through success, rejection and allocation failure.

The pinned dependency's Base64 parser formerly ignored any character outside
its alphabet. XSD permits XML whitespace inside the encoded text, but excludes
punctuation and non-XML whitespace. Both the data and padding scans now reject
those characters. Required padding and zero unused bits remain enforced. This
applies to schema declarations and instance validation through conversion, DOM
and streaming APIs. It does not apply MIME's permissive decoding rules to XSD.

The hexadecimal string copy and Base64 buffer allocation formerly returned a
positive invalid-lexical result when allocation failed. Both paths now release
the temporary value and take the existing internal-error cleanup path. They
return a negative failure and leave the computed-value output null, preventing
allocation failures from being mistaken for an ordinary invalid value.

Whitespace normalization has an explicit internal failure status. The public
nullable-string normalization ABI is preserved, but datatype validation calls
the private status-bearing functions and takes the existing error cleanup path
on allocation failure. It also retains an already allocated normalization buffer
instead of overwriting its owner during a second normalized-string assessment.
Allocation tests cover integer, normalizedString, token, NCName, URI and binary
values, with and without computed outputs, including rejected lexical values.

CMake probes canonical validity, strict lexical behavior and allocation-error
classification before accepting the installed provider. AUTO uses the pinned
private source if a probe fails; SYSTEM rejects it. Checked source hashes and
timestamp-preserving output keep the correction reproducible. The dependency
continues to use libxml2's allocation and error APIs; it adds no Qore callback,
global production state, network access or filesystem operation.

`test/xml-binary-constraints.qtest` checks 206 declaration cases and 23 lexical
cases through all native APIs. The independent Python test reproduces the exact
committed fixtures and checks them against pinned Xerces. Both native allocation
sweeps cover binary decoding and canonical reassessment, including empty values,
mixed lists, rejected patterns and recovery after permanent injected failures.

WSDL canonical binary declaration checks and instance default projection are
separate from this native implementation. Float and calendar canonical forms
also retain their P5 coverage ownership.
