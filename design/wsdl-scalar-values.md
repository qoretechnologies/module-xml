# WSDL scalar lexical validation

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdBaseType` validates integer XML lexical forms before native conversion in
both serialization directions. All thirteen integer builtins require ASCII
digits; signed integer types permit one leading sign, while XSD 1.0 unsigned
types require digits alone. Empty or absent text, fractions, exponents, trailing
data and non-ASCII digits raise `SOAP-SERIALIZATION-ERROR` or
`SOAP-DESERIALIZATION-ERROR` at the corresponding API boundary. Boolean, null,
binary and structured values cannot masquerade as native integers.

Whitespace normalization replaces TAB, LF and CR with SPACE. Collapse additionally
merges SPACE runs and removes leading/trailing SPACE. Other characters remain
available for lexical validation to reject; generic language whitespace trimming
is unsuitable. `normalizedString` uses replacement and `token` uses collapse.
For example, an integer field containing `" \t001\r\n "` has the value one;
`"1.0"`, `"1tail"` and `"1\x00tail"` are invalid integer lexical forms.

Integer bounds are compared as canonical decimal strings: sign first, then digit
count and lexical order, with the ordering reversed for negative values. No
bounded numeric conversion precedes validation. All eight bounded types enforce
their exact minimum/maximum, and the four sign-constrained unbounded types enforce
their sign. Values within signed 64-bit range become native integers. Larger
values remain strings, as do noncanonical spellings of `xs:integer` retained by
its existing API. For example, `xs:unsignedLong` returns `18446744073709551615`
as a string; `18446744073709551616` is rejected instead of clamped.

Native integer, float and number inputs must denote finite integral values.
Float formatting uses zero fractional digits and no grouping; number formatting
uses `NF_Raw`, preserving the exact stored MPFR integer. These paths preserve
the supplied numeric value, including precision already chosen by the caller.
Use decimal strings when the originating value must not first undergo floating
point rounding. Native negative zero is integer zero, which is valid for unsigned
types; an unsigned XML string containing a sign is still invalid.

`XsdIntegerDataType` applies these same rules before provider conversion, including
inside lists and after Serializable reconstruction. `getValueType()` returns
`NOTHING` to prevent enclosing list providers from coercing lexical strings first.
The output type hash reports `int`, plus `string` where large or retained lexical
values require it. Bounded integer providers retain the `NT_INT` base category;
mixed int/string providers report `NT_ALL`. Optional providers additionally accept
and return `NOTHING`; null remains invalid. Invalid values raise
`RUNTIME-TYPE-ERROR`, and absent required values raise `MISSING-VALUE-ERROR`.

```qore
%modern
%requires WSDL
WSDL::XsdIntegerDataType orderNumber("unsignedLong");
auto value = orderNumber.acceptsValue("18446744073709551615");
@assert(value == "18446744073709551615");
```

Integer examples use negative values for negative/nonpositive types. General
facets and the other scalar requirements retain their phase ownership in the
interoperability execution plan. Retained XML values continue to use the additive
public contract documented in `wsdl-xml-values.md`.

`test/wsdl-integer-lexical.qtest` covers all integer builtins, invalid value types,
attributes/simple content, reconstruction, lists/unions and whitespace. The
independent `test/wsdl-interop/test_integer_lexical.py` exercises actual SOAP 1.1
and 1.2 bindings in both directions, validates 936 input/output documents with
libxml2 and Xerces, and compares exact small integer values and expanded names.

`test/wsdl-integer-range.qtest` adds all thirteen builtin bounds, arbitrary-size
values, native numeric inputs, provider metadata and reconstruction. Independent
`test_integer_range.py` checks 1,200 documents across actual SOAP 1.1/1.2 bindings,
both directions, attributes/simple content, provider conversion and generated
examples. Exact Python integers and Xerces acceptance govern value fidelity;
96 libxml2 rejections of valid arbitrary-size input integers are explicitly
recorded as the retained P1 oracle disagreement.

Boolean strings accept exactly `true`, `false`, `1` and `0` after XML whitespace
collapse. Native booleans and numeric zero/one are accepted, including negative
zero. Other numbers, missing text, null, binary/structured values and invalid
spellings are rejected before conversion. Serialization emits `true` or `false`;
deserialization returns native booleans. This is an XML binding input contract;
it does not use the wider numeric truth conversion defined for XPath casts.
List decoding collapses XML whitespace before splitting items, so TAB, LF and CR
are separators just as SPACE is. Empty and whitespace-only lexical lists are empty
lists; non-XML separators remain part of the item for its validator to reject.
Scalar decoding joins ordered `^value^` and `^cdata^` fragments before lexical
validation, ignoring comments and rejecting child elements. Splitting `false`
between text and CDATA must still return `False`; appending `tail` must fail.
A single native `^value^` wrapper retains its native type. Retained XML carriers
keep the original XML nodes; this text projection is used only for validation.

`XsdBooleanDataType` shares this validation and returns `NOTHING` from
`getValueType()` so enclosing list providers cannot first turn every nonempty
string into `True`. Its native base category remains `NT_BOOLEAN`/`bool`.
Optional and mandatory copies retain validation after Serializable reconstruction;
only optional providers accept `NOTHING`, while null is always invalid. Invalid
provider values raise `RUNTIME-TYPE-ERROR`; required omissions raise
`MISSING-VALUE-ERROR`. For example, a list `("false", "1")` produces `(False, True)`,
whereas `("false", "yes")` is rejected.

`test/wsdl-boolean-lexical.qtest` checks lexical boundaries, native numeric values,
provider lists/optionality, reconstruction, attributes, simple content and unions.
`test_boolean_lexical.py` independently validates both directions of actual SOAP
1.1/1.2 bindings, boolean lists/unions, native provider values and generated examples
with libxml2 and Xerces, and compares the resulting boolean values.

Decimal strings use the XSD 1.0 decimal lexical space: an optional sign, ASCII
digits with an optional decimal point, and at least one digit. XML whitespace
is collapsed before validation. Exponents, nonfinite values, trailing data,
non-ASCII digits and other native value categories are rejected with the
corresponding SOAP or provider error. Native finite integers, floats and numbers
are accepted; boolean/null/binary/container values are not decimals.

Serialization preserves validated decimal text. Native float/number input uses
Qore 3.0 `toStringRoundTrip()`, which selects the shortest significand that
reconstructs the source binary value at its original precision and expands its
exponent into plain decimal notation. For example, `123.45n` emits `123.45`,
while `number("1.00000000000000000001")` retains its meaningful final digits.
This is a numeric binding policy; it does not apply the display heuristic or
round a value merely to satisfy a schema facet.

Deserialization retains the familiar native float result only when that float's
round-trip spelling reproduces the normalized input text exactly. Otherwise the
result is a string. Thus `"123.45"` returns a float, but `"+001.2300"`,
`"12345678901234567890.123456789"`, values beyond binary64's range and nonzero
values below its range remain exact strings. This prevents both precision loss
and loss of authored spellings needed by patterns. In particular, `9898.00` stays
valid through decoding and reserialization. Signed zero is retained on the wire;
all decimal zero spellings still denote the same XSD value.

`XsdDecimalDataType` applies the same rules before provider/list conversion and
reports float/string output alternatives (`NT_ALL`). Its conversion type is
`NOTHING`, so enclosing lists cannot coerce strings first. Optional providers
also accept/return `NOTHING`, while mandatory omission raises
`MISSING-VALUE-ERROR`. Null and invalid decimal input raise `RUNTIME-TYPE-ERROR`.
Serializable reconstruction and optional/mandatory copies retain these rules.

```qore
%modern
%requires WSDL
WSDL::XsdDecimalDataType amount();
auto exact = amount.acceptsValue("12345678901234567890.123456789");
@assert(exact == "12345678901234567890.123456789");
```

`test/wsdl-decimal-lexical.qtest` covers lexical boundaries, precision/range,
native inputs, provider lists/optionality, reconstruction and attributed simple
content. `test_decimal_lexical.py` checks 784 documents across real SOAP 1.1/1.2
bindings, both directions, lists/unions, CDATA, providers and examples. Xerces
and Python Decimal comparisons remain mandatory for all valid documents. Older
libxml2 versions have the already adjudicated 24-digit decimal pre-parser limit;
those rejections are recorded explicitly, including fractional leading/trailing
zeros, while newer libxml2 versions may accept every valid case.

The binding follows [XSD decimal](https://www.w3.org/TR/xmlschema-2/#decimal).
Its native-number policy is consistent with the canonical-spelling approach of
[BigDecimal.valueOf(double)](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/math/BigDecimal.html#valueOf(double));
it is separate from XPath's float-to-decimal casting contract. Qore's MPFR-backed
number type is binary floating point, so original decimal text remains the
representation for exact decimal source values. WSDL requires Qore 3.0 for the
new formatter.

Decimal and integer restrictions validate normalized lexical input at each
derivation step. Numeric bounds and enumeration use canonical decimal value
keys: sign, integer length, integer digits and fractional digits determine order
without a floating point cast. Canonical keys are used only for comparison;
the caller's lexical spelling remains available for pattern validation and output.
For example, `1.00000000000000000000` fails a minimum of
`1.00000000000000000001`; `1.23` belongs to an enumeration declared as `+001.2300`.

Digit facets follow XSD 1.0 Second Edition sections 4.3.11–12. Integer leading
zeros and fractional trailing zeros do not count. Fractional leading zeros do:
`0.0012` needs four total digits and four fractional digits under that edition's
`i * 10^-n` rule, which bounds both the coefficient and `n`. Zero has one total
digit and no fractional digits. Native values are checked using the same exact
round-trip spelling used for serialization; display rounding cannot make an
out-of-range value satisfy a bound or digit limit.

`XsdNumericRestrictionDataType` carries a scalar `XsdNumericFacetInfo` snapshot
and its base provider. It retains no transient namespace graph, and both survive
Serializable reconstruction. Each provider in the derivation chain checks its
own restrictions before conversion. A step with a pattern returns a string and
reports that string output category; inherited patterned values also remain
strings. Scalar/list inputs reach validation before any soft conversion.

`XsdNumericDataField` gives fields the same numeric enumeration semantics.
Generic DataProvider string-key equality cannot express equivalent XML numeric
spellings. The numeric field retains declared `AllowedValueInfo` spellings and
uses exact canonical keys for comparison, independently of its provider's type
facets. It also checks numeric fixed attributes and choices for repeated elements.
Omission is accepted only through the provider's optional/default rules. Declared
numeric enumeration spellings are value-space metadata: an additional pattern
may require the caller to use a different lexical spelling of that same value.

Numeric samples first validate the proposed value and pattern/enum candidates.
Otherwise they find the interval nearest zero, including inherited and builtin
bounds, and construct an exact decimal grid value subject to digit limits.
Every result passes full serialization validation. Empty integer intervals and
pattern/enumeration intersections the generator cannot construct raise
`XSD-SAMPLE-ERROR`; they never produce a knowingly invalid example. List example
generation constructs a list from a valid item example.

The focused numeric facet suite covers exact boundaries, 2000-digit integers,
underflow, negative/zero values, native precision, patterns, inherited constraints,
provider/field reconstruction, optionality, repeated choices and fixed attributes.
`test_numeric_facets.py` checks both actual SOAP bindings and both directions
with libxml2 and Xerces, asserting exact Decimal values and expanded names.
Its 864 lexical input/output documents and 576 reconstructed provider/example
outputs form a 1,440-document independent matrix, with negative provider errors
checked separately.

References: [numeric bounds](https://www.w3.org/TR/xmlschema-2/#rf-minInclusive),
[enumeration](https://www.w3.org/TR/xmlschema-2/#rf-enumeration),
[totalDigits](https://www.w3.org/TR/xmlschema-2/#rf-totalDigits),
[fractionDigits](https://www.w3.org/TR/xmlschema-2/#rf-fractionDigits).

Restriction providers keep private configuration fixed after construction or
reconstruction. As with `QoreDataField`, callers configure numeric field choices
before sharing a field between threads; acceptance itself does not mutate the
field. Choice setters validate and construct replacement maps before publishing
them, so a failed update retains the previous choices.

Numeric restriction declarations are validated during dependency finalization,
before publishing a schema or provider. A restriction cannot widen inherited
digit counts or numeric bounds, change a fixed facet through any ancestor,
weaken numeric whitespace collapse, or introduce length facets. Integer-derived
types retain fractionDigits fixed at zero. Bound and enumeration literals must
map through the base datatype, including inherited patterns. The current step's
own pattern need not match the enumeration's declared spelling: enumeration
constrains values, and a different spelling of that value can satisfy the pattern.

XSD 1.0 permits a repeated inherited exclusive endpoint even though that endpoint
is outside the base value space. The declaration still needs a valid lexical
mapping; base enumeration/digit constraints do not invalidate this exception.
Opposite bounds must satisfy the edition's explicit inclusive/exclusive ordering
rules, including inherited and builtin endpoints. Equal exclusive endpoints in
one restriction are permitted; their empty value space causes sample generation
to raise `XSD-SAMPLE-ERROR`. An own-step enumeration/digit intersection may also
be empty without making the declarations themselves invalid.

`XsdFacetCount` retains `totalDigits` and `fractionDigits` as an `int`, or a
canonical decimal `string` beyond the native integer range. For example,
`<xs:totalDigits value="9223372036854775808"/>` is legal and retains that exact
string in `XsdSimpleType.totalDigits` and the provider's scalar metadata.
Comparisons use exact integer text. Example generation converts a count to an
integer only after proving it is smaller than the bounded candidate size.

The existing streaming schema grammar pass now checks simple derivation/facet
expanded names, annotation position and multiplicity, and facet attributes and
content before grouped XML hashes erase namespace/order information. Foreign
namespace facet attributes remain permitted. Facet values and `fixed` attributes
are validated before conversion; `whiteSpace`'s NMTOKEN value uses whitespace
collapse. The grammar stack uses memory proportional to XML depth and is local
to each parse. Annotation application content remains opaque.

`wsdl-facet-declarations.qtest` verifies these rules, large-count metadata,
provider reconstruction, examples and failed-addition rollback. The independent
`test_facet_declarations.py` matrix checks atomic and simple-content restrictions
through both actual SOAP bindings and both directions, comparing exact Decimal
values and expanded names. Its specification adjudication records compiler
disagreements separately from production acceptance. Other scalar families retain
their remaining P3 acceptance work.

## Strings and length restrictions

String enumeration literals are interpreted in the base datatype's value space.
The most derived `whiteSpace` rule normalizes incoming text before ancestor
patterns, enumeration and length constraints run. XML whitespace means SPACE,
TAB, CR and LF; a nonbreaking space is preserved. This distinction matters when
a restriction introduces collapse alongside an enumeration containing surrounding
spaces: the enumeration does not acquire the new whitespace rule, and the
intersection can be empty. Provider field choices include only values accepted
by the complete derived restriction. Inherited choices are filtered as well.

`length`, `minLength` and `maxLength` use exact `XsdFacetCount` values and validate
applicability, narrowing, fixed ancestors and consistent intervals before use.
An exact length and a minimum/maximum at one step must satisfy the ancestor
conditions in XSD 1.0 part 2 section 4.3.1.4. Strings count Unicode code points,
including one for a supplementary character and two for a base plus combining
mark. Binary values count octets; XSD lists count items. QName and NOTATION
length facets are always satisfied as specified by XSD 1.0. The existing text
representation of NMTOKENS, IDREFS and ENTITIES is preserved; XML whitespace
collapse supplies item boundaries and their builtin minimum is one item.

`XsdSizedRestrictionDataType` holds `XsdSizedFacetInfo` plus its base provider.
Constructors and reconstruction validate metadata and its value category before
publication. The wrapper normalizes text before base conversion, then checks its
own constraints. String enumeration membership is built once and rebuilt from
validated metadata on restoration. Optional and nested list wrappers keep validation; no weak schema
reference or direct-conversion shortcut is used. Builtin text providers apply
whitespace processing and reject nonscalar input. A repeated list-valued element
uses an outer occurrence list whose entries are item lists, including a single
occurrence and an empty item list. Restricted lists and complex simple content
retain this distinction during serialization.

Example generation validates candidates through the complete schema type. It
tries viable string choices and bounded pattern/length candidates. List-length
examples resize the supplied item sample; binary-length examples use bounded
zero octets. Existing valid samples are retained. Generation is bounded to 256
characters, items or octets and raises `XSD-SAMPLE-ERROR` when no valid candidate
is constructed; this resource bound does not limit accepted application values
or schema facet counts. Generated string enumerations use this same validation.

For example, a token restricted to three characters accepts `" A  B "` as `"A B"`;
a provider and its reconstructed copy return the same value. A two-item integer
list accepts `["01", "+2"]` with both integer values preserved. A repeated element
can carry `[["01", "+2"], ["3", "4"]]`, producing two elements with two items each.

`wsdl-string-list-facets.qtest` covers declarations, values, providers, optionality,
metadata rejection, examples and failed schema additions. `test_sized_facets.py`
checks both SOAP bindings and directions, reconstructed contracts/providers,
attributes, repeated values and generated messages against libxml2 and Xerces,
with explicit typed-value, binary and expanded-name assertions. Named validator
defects and the Xerces code-point-count setting are documented in
`test/wsdl-interop/sized-facets-adjudication.md`. The element-choice setter requires
the core DataProvider fix in commit `cbb8aceb2`.

Compiled XSD patterns match the entire input; translated legacy PCRE strings use
absolute `\A` and `\z` assertions. A trailing newline is part of a preserved
string and cannot be ignored by a `$` end anchor. Sample verification uses the
same complete-value requirement. Native scalar inputs to
list serialization count as one item, following its existing singleton conversion.
NOTHING used as an empty list must satisfy the same zero-item constraints.

## Ordered list values and retained lexical tokens

For lists whose atomic items use string, boolean, decimal or integer conversion,
`XsdListItemInfo` retains the builtin, item provider and effective whitespace rule.
It has no weak schema/namespace references. `XsdListDataType` validates every item
and rejects empty or XML-whitespace-bearing tokens before returning a native list.
The empty native list is distinct from a list containing an empty string.

List restrictions normalize XML whitespace before locating item boundaries. Their
patterns apply to the joined whole-list lexical form. A pattern-bearing restriction
returns each original token as a string, preserving lexical forms such as
`("001", "002")` or `("1", "0")` through reconstruction and serialization.
The tokens still pass the complete item type. Ancestor patterns remain enforced.
Without a whole-list pattern, existing atomic item representations are retained.

Enumerations parse through the base list. Ordered keys use exact canonical decimal
values for decimal/integer items, boolean truth values for boolean items, and exact
strings for text items. Keys encode token lengths so concatenation cannot collapse
distinct item sequences. Equivalent facet spellings are deduplicated in order;
an empty enumeration value has a distinct empty-list key. Same-step lexical patterns
are independent of enumeration declaration spellings.

`XsdListRestrictionDataType` retains counts, patterns, ordered enumeration values
and inherited validation. Reconstruction checks metadata before publishing it and
rebuilds transient count/membership state. Optional variants construct new providers.
Both list provider classes return `NOTHING` from `getValueType()` and an empty direct
conversion map, requiring validation inside ordinary repeated-list providers.

`XsdListDataField` compares complete choices and repeated-element choices using the
same ordered value keys. Replacement metadata is fully resolved before publication;
a failed update leaves choices and membership maps unchanged. Field providers always
enforce their own restrictions, including lexical patterns. These finite choices
represent values; callers must still supply spellings accepted by the type. Message
provider fields retain their public WSDL **part names**; message serialization uses
the existing element argument mapping. Configure schema/field metadata before sharing
it with concurrent consumers; runtime acceptance does not mutate restriction state.

For example, an invoice list enumerated as `01 +2` with pattern `001 002` accepts
`("001", "002")`, rejects `(1, 2)` for the pattern, and rejects `("002", "001")`
for item order. A string list accepts `("A\u00a0B", "C")` but rejects `("A B", "C")`
because a SPACE inside the first item would introduce an additional item on the wire.

Generated examples try declared list spellings, bounded pattern candidates and
bounded length adjustment, validating every candidate against the complete type.
An empty facet intersection or unsupported bounded search reports `XSD-SAMPLE-ERROR`.
No invalid placeholder is emitted. The test matrices and oracle diagnostic decisions
are documented in `test/wsdl-interop/list-values-adjudication.md`.

## Boolean restrictions and value constraints

Boolean-derived types allow only `pattern` and `whiteSpace` facets; whitespace is
fixed to XML `collapse`. Enumeration, bounds, length and digit facets are rejected
at schema construction. This follows XSD 1.0 Part 2 §3.2.2.3.

Patterns inspect the normalized lexical spelling before native boolean conversion.
A restriction with a pattern retains its accepted spelling as a string; an ancestor
pattern has the same effect through further derivation. Without a pattern, the
existing native boolean representation remains. Native booleans and numeric zero/one
use `false`/`true` as their candidate lexical forms and must pass the same patterns.
For example, a flag with pattern `0|1` accepts `"0"`, retains that text on output and
rejects native `False`; callers needing that pattern supply an explicit XML spelling.

`XsdBooleanRestrictionDataType` retains a strong base provider and typed pattern
metadata. Reconstruction validates the base family and compiled patterns before
publication. Optional and repeated providers perform the same validation, including
when a base provider supplies a default value. Acceptance does not mutate metadata;
configuration and field choice updates must finish before sharing with consumers.

Fixed attributes compare boolean truth values after type validation, including
references and complex-type restrictions. `XsdBooleanDataField` applies the same
value equality to finite whole/repeated field choices while its provider separately
checks lexical patterns. Failed choice replacements preserve prior metadata. Thus a
fixed `false` flag accepts `"0"` if the type permits that spelling, and rejects `"1"`.

Example generation validates the supplied starting value, then the four legal
normalized spellings. This exhausts the boolean lexical space; an empty intersection
of patterns reports `XSD-SAMPLE-ERROR`. See `wsdl-boolean-facets.qtest` and
`test_boolean_facets.py` for schema, serialization, field/provider reconstruction,
default/fixed, list-item, cancellation and independent SOAP regression coverage.

## Union provider traversal

`UnionDataType` tries member providers in declaration order and returns the first
accepted conversion. For example, boolean/integer members map `"1"` to `True`,
while integer/boolean members map it to integer `1`. Member restrictions remain
active in detached and reconstructed providers. Only ordinary type, missing-value
and field-value rejection permits another trial; cancellation and unexpected
errors propagate. Schema union conversion likewise catches only its directional
SOAP validation error. Builtin date and binary decoding translates only the
native parser's input-rejection category to that SOAP error, retaining its
diagnostic and allowing a later union member to accept the value.

Union providers explicitly track requiredness. Mandatory providers reject an
omitted value; optional variants accept omission while retaining every constraint
on supplied values. Serialized metadata validates a nonempty ordered provider
list and boolean optionality before publication. Older metadata without optionality
is interpreted as mandatory. `getValueType()` returns `NOTHING` and the direct
conversion map is empty, requiring enclosing occurrence lists to validate each
union item instead of accepting arbitrary values through `AutoType`.

Each runtime or metadata operation caches shared nested union results for its
duration. Object contexts hold typed maps without repeated copy-on-write cloning;
the cache contains both accepted conversions and ordinary rejections. Metadata
keys distinguish input/output categories, simplified names, fields and assignability
targets. Active entries detect cyclic member metadata and raise
`XSD-SIMPLETYPE-ERROR`. Shared subgraphs therefore take work proportional to their
edges and scalar comparisons, rather than their exponentially expanded trees.

Contexts are thread-local and cleared or restored with `on_exit`. A reentrant call
with a different input gets independent state, including different scalar native
types, signed zeros and number precision. NaN inputs can reuse failed trials;
list/hash comparison applies the same rules to each item. Date comparisons also
retain their timezone spelling. No cache survives the root
call, so later operations see the configured member providers afresh. Configure
public member lists before sharing providers between threads and keep member
validation stable for the duration of an operation.

`wsdl-union-providers.qtest` verifies declaration order, reconstruction, nested
lists, requiredness, invalid metadata, 28-level shared graphs, cycles, cancellation
cleanup and numeric reentrancy. `test_union_providers.py` checks real SOAP 1.1/1.2
requests/responses, simple content/attributes, repeated values, detached consumers
and examples; its reference results are documented in
`test/wsdl-interop/union-providers-evidence.md`.

Schema serialization and deserialization also cache each shared member result for
one conversion. Their caches are separate: serialization includes namespace state
and type-attribute policy, while deserialization includes the element name, type
map and multireference map, including signed zero, NaN and number precision in
referenced values. A reentrant call changing any input receives a new context and restores the outer one afterward. Ordinary SOAP rejections can be
reused; cancellation and unexpected errors unwind without publication. Rejection
diagnostics summarize immediate nested union failures instead of duplicating
entire shared graphs. Atomic rejection messages retain their specific cause.
The native-list metadata query caches shared schema members with cycle detection
as well, so element and provider shape checks do not expand shared unions.

`wsdl-union-schema-graphs.qtest` counts terminal visits in 32-level shared graphs,
checks bounded diagnostics, cycles, error recovery and all reentrant conversion
contexts. `test_union_schema_graphs.py` uses independently validated atomic/list
graphs through real SOAP bindings, reconstructed schemas/providers and examples.

For boolean, decimal/integer, text and binary members, union conversion carries a
primitive-family/value identity separately from the native result. Integer and
decimal share an exact decimal value space; boolean, string, hexBinary and
base64Binary remain distinct primitive families. A lexical value is retained as
a string when converting it to a native value would change its family or value
on serialization. For example, `"01"` in a boolean/integer union remains a string:
native integer `1` would select the earlier boolean member. In a union containing
a string restricted to `true|false` followed by boolean, `"1"` stays `"1"`, because
canonical `true` would select the string member. Unambiguous values retain their
existing native representations.

The conversion checks run once at the owner of each contextual union operation.
Serialization checks the emitted XML text, including type-attribute namespace
context. Deserialization checks whether serialization and reselection preserve the
original identity. An unchanged emitted spelling needs no further read. Nested
unions reuse traversal state; probes restore per-thread state on errors and
cancellation. Custom member subclasses retain their own conversion semantics;
an inherited builtin name alone does not establish an atomic identity.

Union restriction patterns inspect the lexical spelling, before native conversion
can turn XML `false` into Qore string `"0"`. Their accepted spelling is retained.
Enumeration declarations must be valid in the base union and compare in that
base's value space. Thus an integer/decimal enumeration `01` accepts `1.0`, while
a boolean/integer enumeration `1` rejects `01`. Union patterns use the selected leaf member's whitespace rule, propagated through nested unions. Restrictions are checked after
the base has selected its member; a failed restriction does not select a different
member of that same base.

`XsdUnionAtomicInfo` retains only builtin spelling rules, effective whitespace,
pattern retention and the corresponding provider object. It retains no source
schema, namespace registry or transport options. Provider serialization follows
the current ordered member list; reordering keeps metadata associated with its
member object, and replacement members retain their own validation behavior.
Restoration validates metadata, checks every enumeration against the base union,
and rebuilds transient lookup maps. Older metadata
without atomic descriptions retains its former conversion behavior.

`XsdUnionDataField` uses primitive value keys for scalar and repeated choices.
The field's provider enforces its schema facets independently of field choices
and the `creatable` flag. Choice setters build replacement maps before publishing
them, so a failed update preserves the previous constraints. Optional variants,
list items, defaults and reconstructed fields use the same comparisons.

`wsdl-union-value-identity.qtest` covers ambiguity, enumeration, patterns, nested
restrictions, list items, binary families, metadata changes, declarations and
field choices. `test_union_value_identity.py` checks actual SOAP 1.1/1.2 bindings
in both directions with independent primitive-value assertions and validators,
including attributed/repeated values, detached providers and generated examples.

List members whose items use the atomic families above carry ordered item identities.
Each item key includes its primitive family; the whole list key uses length-prefixed
item keys. Integer and decimal lists can therefore compare equal, while boolean
and decimal items remain distinct. Empty lists compare equal regardless of item
type, and a single-item list remains distinct from an atomic value.

`XsdUnionListInfo` records the item spelling rules and the corresponding list and
item providers. A union accepts either XML list text or native item lists for these
members. XML text is split at XML whitespace boundaries before member conversion;
native string items must each have a nonempty, whitespace-free spelling after the
item's own normalization. A supplied empty binary item is rejected because its
empty spelling cannot represent a list item. Empty lists themselves remain valid.
Only the selected binary builtin's lexical parser errors permit trying the next
member; unexpected errors from custom providers still propagate.

When conversion would change list member selection, the result retains the original
item spellings in a native list. For example, with a list of strings restricted to
`true|false` before a boolean list, `"1 0"` becomes `["1", "0"]`. Serializing native
booleans as `true false` would instead select the string list. Unambiguous native
values and the existing `xs:integer` spelling policy are preserved. Whole-union
patterns retain the lexical string after the selected list member collapses XML whitespace.
QName-capable patterned collections retain native lists of token spellings and
namespace-bearing values instead, including empty lists. A single string cannot
preserve the independent namespace identity of each item; the QName value contract
describes the additive representations.

Detached metadata follows member reordering and pruning. Restoration checks list
shape, exact list/item provider identities, mandatory items and atomic spelling
rules. Missing list descriptions retain the older native-list conversion contract.
Providers advertise lexical string input when a current member has a list
description. Finite choices use the same ordered primitive keys, and failed choice
updates leave existing constraints intact.

`wsdl-union-list-identity.qtest` covers these conversions, facets, choices, metadata,
binary item boundaries and semantic probe failures. `test_union_list_identity.py`
checks both SOAP bindings and directions, attributed/repeated values, reconstructed
consumers and examples, using independent ordered primitive values and validators.
The previously adjudicated libxml2 empty-list enumeration compiler defect is counted
explicitly; Xerces assesses every document, with no waiver of Qore value checks.

For list members whose items are atomic unions, `XsdUnionListInfo.union_items`
selects per-item conversion capture instead of a single atomic descriptor.
The actual schema/provider item conversion publishes its selected primitive identity
after any native-value preservation probes. List comparison collects these identities
in order. It does not replay item validation to infer which member accepted a value.
Restriction wrappers retain the underlying list identity, while each item union
still enforces its own facets. For a boolean/int item union, `1 01 2` has boolean,
decimal and decimal items; it is distinct from the all-decimal `1.0 1.0 2.0`.
The all-decimal `01 2` does compare equal to `1.0 2.00` in an enclosing union
that also permits a decimal list.

Capture state is local to a thread and restored on every exit, including a failure
after earlier items converted successfully. A target and provider call depth isolate
reentrant conversions. Shared item unions reuse the existing bounded traversal
contexts. Detached metadata requires a mandatory union item provider and excludes
simultaneous atomic item metadata. Older atomic-list metadata defaults the new flag
to false. Public member graphs must be configured before concurrent use.

`wsdl-union-list-items.qtest` covers these comparisons, restrictions, native item
boundaries, binary/text values, metadata restoration, choices, error cleanup and
shared/cyclic graphs. `test_union_list_items.py` checks both SOAP bindings,
directions and reconstructed consumers. The Xerces list-kind comparison defect is
counted separately with exact diagnostics, libxml2 validation and independent
ordered values; see `test/wsdl-interop/list-values-adjudication.md`.

List-owned restrictions use `XsdListItemInfo.union_item` when each item is a
union, with no atomic builtin descriptor. Schema conversion captures the selected
identities from the actual underlying list. Inherited wrappers share that capture;
enumeration declarations are evaluated in the base type before this restriction's
own lexical patterns. Equivalent values deduplicate without collapsing boolean
and decimal families.

Provider restrictions capture the actual base list conversion and apply their
own count, pattern and enumeration facets to it. Nested restrictions reuse the
item capture over their interval, so identity inference does not replay item
validators. Original string tokens provide whole-list pattern spellings; native
values use the selected member's lexical form. Reconstructed providers require a
mandatory union item in their base; reconstructed fields validate the item
metadata too. Atomic-list metadata remains compatible when the union flag is absent.

For example, a boolean/int item union with list enumeration `true +1 +2` and
list pattern `1 001 002` accepts and retains `1 001 002`. It rejects `true +1 +2`
for its pattern, and rejects `1 1 2` because its second item is boolean.
`wsdl-list-union-facets.qtest` and `test_list_union_facets.py` cover these rules,
including inherited facets, empty lists, field updates, metadata corruption,
cancellation/reentry cleanup, generated examples and both SOAP bindings.

Union whitespace is governed by the successfully validating member (XSD 1.0
Part 2 section 4.3.6). The union itself does not introduce collapse: a leading
`xs:string` member retains whitespace; `xs:token` collapses it. Ordered bounds
are invalid on union restrictions, which permit only pattern and enumeration.
Scalar serialization recombines retained comments with a `^value^` wrapper when
the selected member returns a scalar; it does not use hash-plus-scalar addition,
which would discard the comments. Scalar text/CDATA fragments are still joined
before member validation.

`XsdScalarTextHelper::elementContent()` creates the element-only validation view:
it removes XML whitespace fragments, rejects non-whitespace or non-string text,
and keeps element/attribute identities. Nonmixed complex types and SOAP
Body/Header/RPC containers use this view even when inherited `xml:space` retained
formatting in the input. Scalar types continue to consume the complete lexical
text. Retained XML carriers are not modified by validation.

## Builtin name values and builtin lists

`Name`, `NCName`, `NMTOKEN`, `ID`, `IDREF` and `ENTITY` apply XML whitespace
collapse and validate the datatype's character grammar before conversion.
`XsdNameLexicalHelper` defines the XML 1.0 Second Edition productions referenced
by XSD 1.0, including Unicode BaseChar, Ideographic, Digit, CombiningChar and
Extender ranges. The same classes implement regex `\i` and `\c` escapes.
XML parser component-name rules remain independent of these datatype rules.

`NMTOKENS`, `IDREFS` and `ENTITIES` retain the compatible public string form.
Each collapsed token must satisfy its item grammar, and the list must contain
at least one token. For example, `" Αλφα\t中文 "` becomes `"Αλφα 中文"`;
`"A !"` is invalid for every builtin name list. `XsdSizedFacetInfo.name_type`
retains the builtin grammar in detached providers and requires a matching text
category and collapse rule. Omission remains controlled by provider optionality.
Document-level ID uniqueness/references and declared unparsed entities require
schema/document context; token grammar does not establish those constraints.

Restrictions normalize enumeration values through the base type. Ordered tokens
determine builtin-list equality; inherited pattern and item-count facets apply
to schema conversion, reconstructed providers, choices and bounded examples.
A list enumeration `" A  B "` accepts `"A\tB"` and rejects `"B A"`.
Union identity records one string-family key per item: a single-item list `A`
is distinct from atomic string `A`, while compatible user-defined lists share
ordered item identity. The public `XsdUnionAtomicInfo` descriptor also carries
these builtins because their public value remains scalar text.

See `test/wsdl-builtin-list-values.qtest`, `test_builtin_list_values.py` and
[builtin name/list evidence](../test/wsdl-interop/builtin-list-values-evidence.md).

## XSD regex character sets and grammar

`XsdRegexHelper::toPcre()` parses the XSD 1.0 grammar before constructing backend
expressions. It rejects unknown escapes, PCRE-only syntax, malformed classes,
unbalanced groups, invalid quantifier syntax and reversed bounds. `^` and `$`
remain literal characters. The wildcard excludes both CR and LF. Category
escapes use the XSD category list, and block escapes require the `Is` grammar
and a recognized block. XML name escapes use the shared XML Second Edition
classes described above.

Every class term is a complete single-character expression. Combining terms
therefore preserves Unicode complements inside positive and negative groups.
Ranges accept literal or escaped single-character endpoints. Subtraction uses
single-character negative lookahead and retains right-nested set semantics.
The class parser stores parent groups explicitly; assembling the result takes
space proportional to the pattern's translated size without recursive descent
through subtractions or repeatedly copying the growing result.

For example, a product-code restriction `[a-z-[aeiou]]+` accepts `brz` and rejects
`bra`. `[\D]` rejects Arabic-Indic decimal digits as well as ASCII digits;
`[\P{IsGreek}]` accepts `A` and rejects `Α`. These constraints survive schema
and provider reconstruction and apply to both serialization directions.

Generation first validates syntax, bounds repetition counts before native
integer conversion, avoids multiplication overflow, and skips repetition of
empty atoms. It searches a fixed character alphabet when separate pattern
candidates do not satisfy the complete derivation chain. Types without patterns
retain their supplied examples. Every returned sample is checked; failure to
find a candidate remains `NOTHING` at the helper or `XSD-SAMPLE-ERROR` at the
type/example API. Cancellation and unexpected errors propagate.

PCRE translation remains available as an API; its return value still has the
backend's compilation/matching limits. Schema pattern compilation uses the
structural representation below for every new constraint. See
`test/wsdl-regex-classes.qtest`, `test_regex_classes.py`, and
[regex evidence](../test/wsdl-interop/regex-classes-evidence.md).
The independent boundary matrix checks every start/end and adjacent code point
of all 326 normative character ranges against both pinned validators.


Valid XSD repetitions are not restricted to PCRE's 65535 count field or compiled
bytecode size. `XsdPatternConstraint` is a typed union of the existing anchored
PCRE string and the immutable `XsdCompiledPattern`. New constraints always store
the original source and build a structural program after XSD grammar validation.
Matching does not depend on full-expression PCRE compilation or backtracking.
Boolean, numeric, string, builtin-list, list and union provider constraints use
the same dispatch as schema serialization and deserialization. Older serialized
PCRE strings remain valid metadata; unsupported objects are rejected.

The structural object serializes only original source, never an arbitrary graph.
Reconstruction validates source and builds fresh transient nodes before publishing
the program. Malformed metadata raises `DESERIALIZATION-ERROR`. Internal nodes
are immutable, have only earlier children, and contain character predicates,
sequences, alternatives, repetitions and explicit character-set operations.
The existing XSD grammar parser emits them with explicit parse stacks, so deep
groups and nested subtraction do not use the Qore call stack.

Repetition bounds are canonical decimal strings. Minimum consumed widths saturate
at input length plus one. Counts are compared with those input-derived limits
before conversion to native integers. A nonnullable atom needs at least one
character per useful iteration; impossible minima fail immediately. Nullable
atoms can pad any minimum with empty iterations. Their matcher ignores zero
progress and retains the earliest visit to each offset, which leaves at least
as much maximum-count budget as a later visit. Nonnullable variable-width atoms
preserve attainable count/offset states until the minimum is met, including gaps
between possible counts. After the minimum is met, earlier visits dominate later
visits as well. Pure closure identities collapse nested stars and pluses;
general bounded repetitions remain intact.

Expressions whose repetition bounds are zero/one or unbounded compile to Thompson
fragments, with two states per grammar node. Character-set nodes remain atomic
predicates. Epsilon closure uses an explicit stack and deduplicates states, so
nullable cycles terminate. Matching advances state sets for each code point and
caches only state-set/character transitions reached by that input. The graph is
immutable after construction; subsets, transitions and predicate results are
local to the match. Numeric counts are never expanded into graph copies.

General counted matching uses per-call stacks and memoized endpoint sets for each node/start
position. Sequence joins and alternation unions preserve every possible endpoint.
Character-set predicates use iterative Boolean evaluation and cache results per
node/character. Flat groups of character predicates are scanned directly instead
of allocating a frame and cache entry for every character. A root repetition
of literal text checks the exact input-derived count and compares bounded UTF-8
byte segments, preserving cancellation without rescanning Unicode prefixes. For example, a fixed
record pattern `[a-z]{65536}` needs work proportional to the supplied record,
without expanding 65536 regex instructions. General ambiguous expressions can
require polynomial endpoint storage and processing; Qore sandbox deadlines and
cancellation apply. No mutable match state is shared or serialized.

`wsdl-regex-counts.qtest` covers large literal/group counts, arbitrary bounds,
nullable padding, Unicode, 2000-level groups/subtractions, corrupted metadata,
legacy providers, each affected provider family, bounded examples, cancellation
recovery and concurrent use. `test_regex_counts.py` directly compares 66 small
expression languages against Python full matching over all binary strings of
length zero through six, for original and reconstructed patterns. It also drives
Unicode/set cases through the structural object even when PCRE could compile
them. Real SOAP bindings and reconstructed element/message providers exercise
large counts with exact lexical comparisons. Independent validator limitations
and the explicit bounded reference schemas are recorded in
[repetition evidence](../test/wsdl-interop/regex-counts-evidence.md).

Ordinary ambiguous expressions such as `(a|aa)+|a+b` accept a long run of `a`
followed by `b`, even when a backtracking backend would exhaust its match budget
on the first alternative. `wsdl-regex-execution.qtest` checks both validity
outcomes through reconstructed schemas and providers, count holes, 10,000-character
inputs, interruption/reuse and synchronized concurrent matches.
`test_regex_execution.py` covers actual SOAP contracts, examples and exhaustive
small-language comparisons. See [execution evidence](../test/wsdl-interop/regex-execution-evidence.md)
for the independent validator limit and separate equivalent schemas. Legacy
serialized PCRE strings retain their backend behavior because they do not carry
the original XSD source; reconstructing new source-retaining constraints rebuilds
the structural program.
