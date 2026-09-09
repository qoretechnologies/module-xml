"""Independent XSD 1.0 binary lexical/value reference.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import base64
import binascii
import re


def value(builtin, text):
    """Return exact octets; validate pad bits by independent canonical re-encoding."""
    collapsed = re.sub(r"[ \t\r\n]+", " ", text).strip(" ")
    if builtin == "hexBinary":
        if not re.fullmatch(r"(?:[0-9a-fA-F]{2})*", collapsed):
            raise ValueError("invalid hexBinary lexical form")
        return bytes.fromhex(collapsed)
    if builtin != "base64Binary":
        raise ValueError("unknown binary datatype")
    compact = collapsed.replace(" ", "")
    try:
        decoded = base64.b64decode(compact, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("invalid base64Binary lexical form") from error
    if base64.b64encode(decoded).decode("ascii") != compact:
        raise ValueError("nonzero unused bits or noncanonical padding")
    return decoded
