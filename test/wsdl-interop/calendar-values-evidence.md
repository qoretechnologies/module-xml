# Calendar lexical and value evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment covers `date`, `gYear`, `gYearMonth`, `gMonthDay`, `gMonth` and
`gDay`. DateTime, time and duration remain separate unfinished P3 work. The
calendar implementation and public conversion contract are described in
[the design](../../design/wsdl-calendar-values.md).

## Requirements and independent references

[XSD 1.0 Second Edition §§3.2.9–3.2.14](https://www.w3.org/TR/xmlschema-2/#date)
define these calendar types. Field grammar, year-zero exclusion, timezone limits
and XML whitespace rules precede conversion. Period starts determine ordering;
missing timezones retain uncertainty. Enumeration and fixed values compare values,
while patterns constrain lexical spelling. The target remains XSD 1.0, including
its negative year labels; XSD 1.1's different year numbering is not substituted.

`calendar_reference.py` validates the authored lexical cases and calculates exact
integer ordinal minutes. Its negative-year formula counts all preceding labeled
years, skipping zero and using Gregorian divisibility for leap days. Tests cover
both complete 400-year cycles, consecutive-year lengths, BCE/CE adjacency,
1,000-digit carry/borrow and touching timezone uncertainty endpoints. This is
independent of WSDL's normalized field tuples and string carry algorithm.

`test_calendar_values.py` exercises the six primitives in atomic elements,
attributed simple content and repeated elements. Actual SOAP 1.1 and 1.2 bindings
cover requests and responses, reconstructed schema/message providers and generated
examples. List and union matrices compare ordered items and primitive families.
The 1,838-row deterministic boundary matrix uses seed 20260909 and checks direct
serialization, deserialization, reconstructed providers and all four bounds plus
enumeration where applicable. It includes native year limits and arbitrary years.

## Exact validator discrepancies

`calendar-validator-defects.json` contains 53 minimal schema groups and 133 scalar
reproductions. Each records the normative expected result, libxml2 2.12.10,
private libxml2 2.15.4 and pinned Xerces-J 2.12.2. It contains no fixture-specific
production behavior. The binding matrix looks up exact builtin/facet/text triples,
checks the independent reference result, and requires the recorded oracle verdict.
Unexpected discrepancies and incorrect disagreement counts fail the test.

The original binding run exposed these differences; generated and reconstructed
outputs reduce to the same 133 scalar triples. Every Qore acceptance/rejection and
typed-value assertion remains mandatory. No upstream W3C fixture or historical
finding is modified.

### libxml2 calendar ordering: 126 reproductions

Both tested libxml2 versions reproduce these errors. In
[`xmlschemastypes.c` v2.15.4](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemastypes.c),
`xmlSchemaDateNormalize()` returns a duplicate for partial dates and for zero
stored offsets. Consequently, `xmlSchemaCompareDates()` cannot apply the ±14-hour
uncertainty adjustment to a missing timezone. For partial dates, the same-type
comparison uses unnormalized calendar days and `TIME_TO_NUMBER`, which adds the
stored timezone offset. This reverses some same-day offset comparisons and fails
equivalent cross-day values. The mixed-type mask branch is not involved.

Examples: `date` with `minInclusive="2000-06-15"` incorrectly accepts
`2000-06-15-00:01`, whose relation is indeterminate. `gYear` with
`minInclusive="2000Z"` incorrectly rejects `2000-00:01`. The enumerations
`gMonthDay="--01-02+14:00"` and `gDay="---02+14:00"` incorrectly reject
`--01-01-10:00` and `---01-10:00`. Xerces and exact ordinal comparison agree
with the expected result in every ordering reproduction.

### libxml2 calendar whitespace: six reproductions

libxml2 2.12.10 rejects the six valid calendar examples surrounded by XML
whitespace. Its
[`xmlSchemaValidateDates()`](https://github.com/GNOME/libxml2/blob/v2.12.10/xmlschemastypes.c)
resets the date fallback pointer to the untrimmed input; its early successful
timezone branch also checks end-of-input before consuming trailing whitespace.
Private 2.15.4 preserves the trimmed start pointer and consumes trailing whitespace;
it agrees with Xerces on these cases. The old source SHA-256 is
`e59123786317788ba59cb99c112eaa8c908f7604841e7708678a11170694cedd`.

### Xerces obsolete gMonth spelling: one reproduction

Xerces accepts `--01--`; both libxml2 versions reject it. XSD 1.0 Second Edition
§3.2.14.1 specifies `--MM` with an optional timezone and excludes other forms.
`MonthDV.parse()` in the pinned 2.12.2
[source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar)
still contains a compatibility branch that skips two trailing hyphens, with a
comment saying it should be removed after incorporation of the erratum. The
second edition already incorporates that correction. Qore rejects the original
invalid input with the expected SOAP/provider category.

Native 2.15.4 reproductions use `XmlReader` schema validation and consume each
document fully; stderr is empty and expected validation exceptions are recorded.
The six whitespace cases are the only differences from the libxml2 2.12.10
verdicts among these 133 reproductions.

## Integration defects corrected

The earlier partial-calendar paths checked only loose regular expressions; date
serialization discarded offsets and decoding assigned a program timezone to
unzoned values. Calendar restriction facets used generic comparisons, and list,
union and detached-provider identity omitted calendar value semantics.

The independent provider matrix additionally exposed invalid partial-calendar
default examples and a date-enumeration path that bypassed pattern validation.
`WSMessageHelper` now supplies valid calendar samples and validates date-valued
enumeration examples. The original failures remain in the execution evidence;
passing checks use the corrected implementation.

Qore prerequisites were committed separately to core develop as `db964e98f` (formerly `516e6f434`).
That native change preserves extended years and fixes compact date string safety;
its own tests, Valgrind and full audit are recorded in the core commit. No native
code changes are part of this XML calendar increment.
