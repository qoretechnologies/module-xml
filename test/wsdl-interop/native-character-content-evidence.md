# Native character-content evidence (P5-16a)

Copyright (C) 2026 Qore Technologies, s.r.o.

This independently tested native prerequisite belongs to the P5-16 nil/default/
fixed work. WSDL declaration conversion follows separately; its existing 415
nil-matrix mismatches remain failures. The native correction closes all 18
DOM/reader disagreements in the preceding 756-document diagnostic.

| Requirement | Root cause and implementation | Evidence |
| --- | --- | --- |
| Nilled and empty elements have no character children | SAX/DOM callers cleared EMPTY on zero-length CDATA, and the shared text helper checked nil/type content before ignoring an empty event. The helper now decides emptiness first. | Empty, comment-only and repeated empty CDATA accept; actual spaces, text and children reject. |
| Element-only content admits XML whitespace | The shared helper rejected CDATA by event kind before testing its characters. Text/CDATA now use the same whitespace predicate. | Ordinary/CDATA XML whitespace accepts, non-XML whitespace and other text reject, required child particles still apply. |
| Element value constraints apply to empty content | Prematurely clearing EMPTY prevented default/fixed values from applying. Only actual characters now clear it. | Empty CDATA/comments and split numeric text; fixed disagreement, required attributes and nil/fixed combinations are checked. |
| Buffer ownership is unchanged | Zero-length events return without consuming CREATED input or dereferencing a non-terminated buffer. | Private ownership boundary test covers PERSIST/CREATED/VOLATILE, NULL, empty strings, authoritative zero lengths and both SAX callbacks. |
| Correct system dependency selection | Behavior is measured through DOM and public reader validation, independent of version labels. | AUTO fallback, SYSTEM rejection, genuine fixed backport, idempotent reconfigure, source integrity, offline/cross builds and install isolation. |

Normative requirements are XSD 1.0 [cvc-elt](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
3.2.1 and 5.1, and [cvc-complex-type](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-complex-type)
2.1/2.3. No character item is contributed by an empty CDATA event. The implementation
preserves original XML data and does not rewrite inputs to bypass validation.

`xml-character-content.qtest` passes four cases/545 assertions. The independent
matrix in `test_character_content.py` checks sixteen schemas/812 documents,
specific error categories and preservation of valid XML data through
parse_xml_with_schema and XmlDoc. Public XmlReader and pinned Xerces agree with
all specification-derived verdicts. Fixture hashes are in the validation inventory.

All 45 dependency-selection tests pass. The complete dependency probe, native
ownership test and new Qore suite pass Valgrind with zero errors and zero lost
blocks; both native C runs free every allocation. Debug builds use the existing
`build-debug` directory and `/usr` prefix with local module paths. Nothing was
installed and no main-Qore source was changed.

The complete 136-suite source gate, eleven source-mode/AOT/matrix supplements,
native documentation and executable shipment example are recorded in
[the inventory](P5-16a-validation.json) and
[full audit](audits/P5-16a-native-character-content.md). The both-version corpus
has exactly unchanged outcomes: all 144 selected WSDLs/1,388 directions pass;
28 valid-input directions and 44 broader failure records remain assigned to
subsequent work. This native correction does not close P5 or P6-P9 acceptance.

The upstream internal reader walker is disabled in the pinned library; the
public reader uses the corrected SAX handlers. The disabled call signature was
updated consistently without enabling that unfinished upstream path. All other
native validation entry points retain their existing context/cleanup behavior.

Initial test authoring used a reserved Qore identifier and one single-quoted
literal tab escape; both were corrected before final validation. Original baseline
and first-fixed logs remain under `/tmp/wsdl-p5-16-character-content/`. The final
native source and test inputs contain no warning suppression or scope waiver.

The initial large-WSDL suite hit the harness's 180-second cutoff while Qore was
scanning declaration reference graphs. The exact parent native control completed
in about 152 seconds, and unchanged current code passed the complete suite in
153.666 seconds. That diagnostic had a 600-second bound but finished below the
original cutoff. Original failures and controls are retained; there is no
assertion/fixture change or demonstrated native slowdown. The audit has 18 Pass,
44 N/A and zero failures for this increment.
