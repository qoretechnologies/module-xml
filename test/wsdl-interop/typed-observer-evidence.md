# P5-22a independent typed observation harness

Copyright (C) 2026 Qore Technologies, s.r.o.

The pinned Xerces-J 2.12.2 runner now offers `independent.run_typed()`. Every
successfully validated document must return one checked observation. Missing,
duplicate, reordered, malformed or unexpected observations fail the runner;
invalid documents and documents behind invalid schemas explicitly return `None`.
The existing offline catalog, prohibited DOCTYPE policy, diagnostics, dependency
hash verification, process deadlines and temporary-directory cleanup apply.

The observer retains expanded element/attribute names, selected schema and union
member identities, selected list-item types, nil state, default provenance,
ordered character content and local namespace declarations. Decimal values remain
exact decimal strings; float/double values use IEEE bits, retaining signed zero.
Binary values use decoded bytes. Assessed calendar/duration lexical forms feed the
existing exact reference predicates, avoiding fractional-second conversion to
floating point. Named types use expanded names; anonymous identities are stable
only within one compiled `SchemaJob`. Compare related documents in the same job.

`typed_reference.compare()` requires an explicit ordering contract. `exact`
preserves all child order. `per-name` permits regrouping different expanded child
names in element-only content, matching the established flat-record API contract;
order among equal names and all generic/mixed character and child order remain
significant. QName prefix aliases compare by expanded value. Uninterpreted
QName-like lexical tokens retain their actual namespace bindings or absence;
unused namespace declarations do not change equality. Equivalent materialized
schema defaults compare equal while raw default provenance remains observable.
Comments, processing instructions and lexical boundaries remain the responsibility
of complete XML-carrier tests. This harness does not independently establish full
SOAP or XML-infoset compliance.

The Java tree stores local declarations once and coalesces character callbacks
with `StringBuilder`; an iterative JSON writer avoids recursive serialization
and repeated text copies. Python restores namespace scopes through an undo log.
The checked protocol limits observations to 256 element levels. Exceeding that
limit is a harness failure, never an invalid production document or a passing
comparison. Existing limits are 10,000 input blobs, 64 MiB decoded inputs, a
128 MiB manifest, a 256 MiB Java heap, 30 seconds for compilation and 60 seconds
for the worker. Exceptions and cancellation leave temporary artifacts cleaned up.

Run the authored matrix offline:

```sh
python3 -B test/wsdl-interop/test_typed_reference.py -v
python3 -B test/wsdl-interop/test_independent.py -v
```

The 57 comparison pairs cover scalar precision and equivalence, signed zero,
NaN/infinities, binary identity, all whitespace forms, calendar and duration
precision/timezones, QName/list membership, namespace rebinding and sibling scope
restoration, attribute order, nil/defaults, selected dynamic types, repeated-name
order and mixed/generic character content. Negative protocol tests reject even
identically malformed before/after observations. Depths 16/32/64/128/256 retain
linear namespace storage; 257 fails explicitly. The fragmented-text test retains
8,192 character-reference callbacks as one exact text segment. The first depth
test exposed Python `deepcopy` recursion, corrected by copying only the changed
root path; the comparator itself passes the full supported boundary.

A checked run on the P5-21 native coverage report observes 262 inline schemas and
all 4,192 before/after documents for 2,096 pairs. All validate without warnings.
`per-name` finds zero differences; `exact` identifies the 20 previously documented
flat-record/all ordering differences. Existing corpus adjudications and selected
normative assertions remain authoritative for recorded reference defects.
The raw observation/report and execution scripts are retained under
`/tmp/wsdl-p5-typed-accounting/integrated/`; the committed validation inventory
records exact input and implementation hashes.

This increment qualifies the observer and comparator. Integration into mandatory
coverage accounting and CI remains open, so unassessed corpus stages remain
visible. P5 acceptance and P6–P9 are not complete. No runtime API, Qore source,
installation or remote branch is changed by this increment.

Reference contracts: [Xerces XSValue API](https://xerces.apache.org/xerces2-j/javadocs/xs/org/apache/xerces/xs/XSValue.html),
[XSD 1.0 datatype value spaces](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/),
and [XSD 1.0 assessment](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt).
Validator observations support the recorded normative decisions; they do not
supersede the specification or the explicitly adjudicated reference defects.

A complete API example (run with `test/wsdl-interop` on `PYTHONPATH`):

```python
from independent import SchemaJob, run_typed
from typed_reference import compare

schema = b'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="quantity" type="xs:decimal"/>
</xs:schema>'''
report = run_typed([SchemaJob("quantity", "urn:quantity-schema", schema, {
    "before": b"<quantity>17.00</quantity>",
    "after": b"<quantity>17</quantity>",
})])
assert all(row["ok"] is True for row in report["documents"].values())
assert compare(report["observations"]["before"],
               report["observations"]["after"], order="exact")
```
