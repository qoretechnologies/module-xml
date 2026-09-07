"""Small specification predicates for the adjudicated XSD 1.0 oracle disagreements.

Copyright (C) 2026 Qore Technologies, s.r.o.
These independent test predicates cover the scalar disagreements in P1, not all XSD datatypes.
"""

from decimal import Decimal
import re

from lxml import etree


UNSIGNED_MAX = {"unsignedByte": 255, "unsignedShort": 65535, "unsignedInt": 4294967295,
                "unsignedLong": 18446744073709551615}
INTEGER_BOUNDS = {"integer": (None, None), "positiveInteger": (1, None), "negativeInteger": (None, -1),
                  "nonNegativeInteger": (0, None), "nonPositiveInteger": (None, 0)}
MONTH = re.compile(r"--(?:0[1-9]|1[0-2])(?:Z|[+-](?:(?:0[0-9]|1[0-3]):[0-5][0-9]|14:00))?")


def lexical_valid(datatype: str, lexical: str) -> bool:
    """Apply the XSD 1.0 lexical rule and value bound without permissive numeric conversion."""
    value = lexical.strip(" \t\r\n")
    if datatype == "gMonth":
        return MONTH.fullmatch(value) is not None
    if datatype in UNSIGNED_MAX:
        return re.fullmatch(r"[0-9]+", value) is not None and Decimal(value) <= UNSIGNED_MAX[datatype]
    if datatype in INTEGER_BOUNDS:
        if re.fullmatch(r"[+-]?[0-9]+", value) is None:
            return False
        number = Decimal(value)
        minimum, maximum = INTEGER_BOUNDS[datatype]
        return (minimum is None or number >= minimum) and (maximum is None or number <= maximum)
    if datatype == "decimal":
        return re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", value) is not None
    raise ValueError(f"no P1 normative predicate for datatype: {datatype}")


def same_number(datatype: str, expected: str, actual: str) -> bool:
    """Compare exact numeric values only after validating both lexical representations."""
    if datatype not in UNSIGNED_MAX and datatype not in INTEGER_BOUNDS and datatype != "decimal":
        raise ValueError(f"not a P1 numeric datatype: {datatype}")
    return (lexical_valid(datatype, expected) and lexical_valid(datatype, actual)
            and Decimal(expected.strip()) == Decimal(actual.strip()))


def select_value(payload: etree._Element, assertion: dict) -> str:
    """Select one scalar using expanded element/attribute names, independent of prefix spelling."""
    path = assertion["elements"]
    if not isinstance(path, list) or not path or payload.tag != path[0]:
        raise ValueError("normative assertion has a missing or wrong root element")
    nodes = [payload]
    for name in path[1:]:
        nodes = [child for node in nodes for child in node if child.tag == name]
    if len(nodes) != 1:
        raise ValueError("normative assertion must select exactly one element")
    if "attribute" in assertion:
        value = nodes[0].get(assertion["attribute"])
        if value is None:
            raise ValueError("normative assertion attribute is absent")
        return value
    if any(isinstance(child.tag, str) for child in nodes[0]):
        raise ValueError("normative assertion selected complex content")
    return nodes[0].text or ""


def check_assertions(payload: etree._Element, assertions: list[dict]) -> list[dict]:
    """Check explicit fixture lexical/value expectations; contradictions fail the harness."""
    result = []
    for assertion in assertions:
        value = select_value(payload, assertion)
        if value != assertion["lexical"]:
            raise ValueError("normative assertion lexical evidence changed")
        valid = lexical_valid(assertion["datatype"], value)
        if type(assertion["valid"]) is not bool or valid != assertion["valid"]:
            raise ValueError("normative assertion contradicts the XSD 1.0 lexical/value rule")
        if "value" in assertion and not same_number(assertion["datatype"], assertion["value"], value):
            raise ValueError("normative assertion exact numeric value mismatch")
        result.append({"datatype": assertion["datatype"], "lexical": value, "valid": valid,
                       **({"value": assertion["value"]} if "value" in assertion else {})})
    return result
