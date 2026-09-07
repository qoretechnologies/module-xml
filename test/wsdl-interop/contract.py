"""Inspect corpus WSDL component identities without using the implementation under test.

Copyright (C) 2026 Qore Technologies, s.r.o.
This records WSDL 1.1 references and binding metadata; it is not a complete WSDL validator.
"""

from lxml import etree


WSDL = "http://schemas.xmlsoap.org/wsdl/"
XSD = "http://www.w3.org/2001/XMLSchema"
SOAP = {"http://schemas.xmlsoap.org/wsdl/soap/": "11", "http://schemas.xmlsoap.org/wsdl/soap12/": "12"}


def qname(node: etree._Element, value: str) -> str:
    """Resolve a QName in the declaration's own namespace context, without local-name fallback."""
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"invalid QName: {value!r}")
    parts = value.split(":")
    if len(parts) > 2 or any(not part for part in parts):
        raise ValueError(f"invalid QName: {value!r}")
    if len(parts) == 2:
        namespace = node.nsmap.get(parts[0])
        if namespace is None:
            raise ValueError(f"unbound QName prefix: {value}")
        local = parts[1]
    else:
        namespace, local = node.nsmap.get(None, ""), value
    # QName validates XML NCName characters independently of the module under test.
    if etree.QName(local).namespace is not None:
        raise ValueError(f"invalid lexical QName: {value!r}")
    return f"{{{namespace}}}{local}" if namespace else local


def describe(document: etree._Element) -> dict:
    """Record each message part, port and binding, and request/response references separately.

    Component errors are reported with a category and evidence. Schema grammar,
    derivation and body validity are assessed independently by the XSD oracles.
    Imported WSDL definitions are reported as an unmeasured scope (P6), never
    inferred from unrelated local names. The W3C echo corpus has no WSDL imports.
    """
    if document.tag != f"{{{WSDL}}}definitions":
        raise ValueError("not a WSDL 1.1 definitions document")
    namespace = document.get("targetNamespace", "")
    result = {"target_namespace": namespace, "messages": {}, "port_types": {}, "bindings": {},
              "ports": [], "errors": [], "imports": [], "inline_schemas": []}

    def expanded(local: str) -> str:
        return f"{{{namespace}}}{local}" if namespace else local

    def reference(node: etree._Element, attribute: str) -> str | None:
        try:
            return qname(node, node.get(attribute))
        except ValueError as error:
            result["errors"].append({"err": "WSDL-QNAME", "line": node.sourceline, "desc": str(error)})
            return None

    def add(target: dict, node: etree._Element, value: dict) -> None:
        name = node.get("name")
        if not name or expanded(name) in target:
            result["errors"].append({"err": "WSDL-COMPONENT-NAME", "line": node.sourceline,
                                     "desc": f"missing or duplicate {node.tag} name: {name}"})
        else:
            target[expanded(name)] = value

    elements, types = set(), set()

    def extension(node: etree._Element) -> dict:
        return {"element": node.tag, "attributes": dict(node.attrib),
                "namespaces": {key or "": value for key, value in node.nsmap.items()},
                "children": [extension(child) for child in node if isinstance(child.tag, str)]}

    for schema in document.findall(f"{{{WSDL}}}types/{{{XSD}}}schema"):
        ns = schema.get("targetNamespace", "")
        names = {"elements": [], "types": []}
        for child in schema:
            name = child.get("name")
            if name and child.tag in (f"{{{XSD}}}element", f"{{{XSD}}}complexType", f"{{{XSD}}}simpleType"):
                key = f"{{{ns}}}{name}" if ns else name
                if child.tag == f"{{{XSD}}}element":
                    elements.add(key)
                    names["elements"].append(key)
                else:
                    types.add(key)
                    names["types"].append(key)
        result["inline_schemas"].append({"target_namespace": ns, "line": schema.sourceline, **names})
    for node in document.findall(f"{{{WSDL}}}import"):
        result["imports"].append({"namespace": node.get("namespace"), "location": node.get("location"),
                                  "status": "not_assessed"})
    for node in document.findall(f"{{{WSDL}}}message"):
        parts = []
        seen = set()
        for part in node.findall(f"{{{WSDL}}}part"):
            item = {"name": part.get("name")}
            if not item["name"] or item["name"] in seen:
                result["errors"].append({"err": "WSDL-PART-NAME", "line": part.sourceline,
                                         "desc": f"missing or duplicate message part: {item['name']}"})
            seen.add(item["name"])
            for kind in ("element", "type"):
                if part.get(kind) is not None:
                    item[kind] = reference(part, kind)
            if ("element" in item) == ("type" in item):
                result["errors"].append({"err": "WSDL-PART-TYPE", "line": part.sourceline,
                                         "desc": "part must specify exactly one element or type"})
            parts.append(item)
        add(result["messages"], node, {"parts": parts})
    for node in document.findall(f"{{{WSDL}}}portType"):
        operations = []
        for op in node.findall(f"{{{WSDL}}}operation"):
            item = {"name": op.get("name"), "extensions": [extension(child)
                for child in op if isinstance(child.tag, str) and not child.tag.startswith(f"{{{WSDL}}}")]}
            for direction in ("input", "output"):
                io = op.find(f"{{{WSDL}}}{direction}")
                if io is not None:
                    item[direction] = {"message": reference(io, "message"), "name": io.get("name")}
            operations.append(item)
        add(result["port_types"], node, {"operations": operations})
    for node in document.findall(f"{{{WSDL}}}binding"):
        value = {"port_type": reference(node, "type"), "soap_version": None, "operations": []}
        for uri, version in SOAP.items():
            binding = node.find(f"{{{uri}}}binding")
            if binding is not None:
                value.update(soap_version=version, style=binding.get("style", "document"),
                             transport=binding.get("transport"))
        for op in node.findall(f"{{{WSDL}}}operation"):
            item = {"name": op.get("name"), "extensions": [extension(child)
                for child in op if isinstance(child.tag, str) and not child.tag.startswith(f"{{{WSDL}}}")]}
            for direction in ("input", "output"):
                io = op.find(f"{{{WSDL}}}{direction}")
                if io is not None:
                    item[direction] = {"name": io.get("name"), "extensions": [extension(child)
                        for child in io if isinstance(child.tag, str)]}
            value["operations"].append(item)
        add(result["bindings"], node, value)
    for service in document.findall(f"{{{WSDL}}}service"):
        for port in service.findall(f"{{{WSDL}}}port"):
            result["ports"].append({"service": expanded(service.get("name", "")), "port": port.get("name"),
                                    "binding": reference(port, "binding"), "addresses": [
                {"element": child.tag, "location": child.get("location")}
                for child in port if isinstance(child.tag, str)]})

    def require(key: str | None, available: dict, kind: str) -> None:
        if key not in available:
            result["errors"].append({"err": "WSDL-UNRESOLVED-" + kind.upper(), "desc": str(key)})

    if not result["imports"]:
        for value in result["port_types"].values():
            for op in value["operations"]:
                for direction in ("input", "output"):
                    if direction in op:
                        require(op[direction]["message"], result["messages"], "message")
        for value in result["bindings"].values():
            require(value["port_type"], result["port_types"], "port-type")
        for port in result["ports"]:
            require(port["binding"], result["bindings"], "binding")
    # A missing inline declaration can be imported; expose it as a reference for
    # assessment with the complete schema component set, not as a false error.
    for value in result["messages"].values():
        for part in value["parts"]:
            if "element" in part:
                part["declared_inline"] = part["element"] in elements
            elif "type" in part:
                part["declared_inline"] = part["type"] in types or (
                    part["type"] is not None and part["type"].startswith(f"{{{XSD}}}"))
    return result
