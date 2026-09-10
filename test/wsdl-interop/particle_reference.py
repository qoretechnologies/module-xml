"""Independent element/string observations for the P4 corpus assertions.

Copyright (C) 2026 Qore Technologies, s.r.o.
These fixtures have xs:string leaves and element-only complex containers. This
predicate does not replace schema validation or cover mixed/dynamic XML values.
"""

from lxml import etree


def validate_assertion(assertion: dict) -> None:
    """Require an explicit path, string-leaf inventory and ordering contract."""
    if (set(assertion) != {"elements", "datatype", "leaves", "order"}
            or assertion["datatype"] != "particle"
            or not isinstance(assertion["elements"], list) or not assertion["elements"]
            or not isinstance(assertion["leaves"], list) or not assertion["leaves"]
            or assertion["order"] not in ("exact", "per-name")):
        raise ValueError("malformed particle value assertion")
    for names in (assertion["elements"], assertion["leaves"]):
        if any(not isinstance(name, str) or not name for name in names):
            raise ValueError("particle names must be nonempty expanded names")
        for name in names:
            # QName checks the Clark-name syntax, including the local NCName.
            etree.QName(name)
    if len(set(assertion["leaves"])) != len(assertion["leaves"]):
        raise ValueError("duplicate particle string leaf")


def observe(root: etree._Element, leaves: list[str], order: str) -> list:
    """Retain every node, attribute and string value, with explicit sibling order.

    Per-name order is the native flat-record contract: occurrences of one field
    stay ordered, while interleaving distinct names requires retained XML. Exact
    order compares the complete original element sequence. Container indentation
    is ignored; string whitespace is preserved. Iteration avoids recursive calls.
    """
    if order not in ("exact", "per-name"):
        raise ValueError("unknown particle observation order")
    leaf_names = set(leaves)
    pending, result = [root], []
    while pending:
        node = pending.pop()
        children = [child for child in node if isinstance(child.tag, str)]
        attributes = sorted(node.attrib.items())
        if node.tag in leaf_names:
            if children:
                raise ValueError("particle string leaf contains an element")
            result.append((node.tag, attributes, "".join(node.itertext()), 0))
            continue
        if any(text.strip(" \t\r\n") for text in [node.text or "", *(child.tail or "" for child in node)]):
            raise ValueError("particle container contains non-whitespace text")
        if order == "per-name":
            # Python's stable sort retains occurrence order for each field name.
            children.sort(key=lambda child: child.tag)
        result.append((node.tag, attributes, None, len(children)))
        pending.extend(reversed(children))
    return result
