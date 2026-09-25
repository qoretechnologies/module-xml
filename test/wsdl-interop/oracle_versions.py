"""The pinned versions of the suite's independent validators.

Copyright (C) 2026 Qore Technologies, s.r.o.

Expected validator behavior, including every adjudicated disagreement with the XML Schema specifications, belongs to
a validator version. Xerces-J is pinned by the digest of its JAR (oracle/manifest.json, checked in independent.py).
libxml2 is used through lxml, and distributions build lxml against their own libxml2, whose versions validate
differently. The suite therefore runs with the lxml wheels pinned by requirements.txt, which bundle libxml2 2.14.6.
"""
from lxml import etree

LXML = (6, 0, 2, 0)
LIBXML2 = (2, 14, 6)


def problems():
    """Returns a description of each difference from the pinned validator versions."""
    found = []
    if etree.LXML_VERSION != LXML:
        found.append(f"lxml {etree.LXML_VERSION} is not the pinned {LXML}")
    if etree.LIBXML_VERSION != LIBXML2:
        found.append(f"lxml uses libxml2 {etree.LIBXML_VERSION}, not the pinned {LIBXML2}")
    if etree.LIBXML_COMPILED_VERSION != LIBXML2:
        found.append(f"lxml was compiled against libxml2 {etree.LIBXML_COMPILED_VERSION}, not the pinned {LIBXML2}")
    return found


def check():
    """Raises RuntimeError unless the pinned lxml and libxml2 are in use."""
    found = problems()
    if found:
        raise RuntimeError("the suite requires the pinned lxml validator (install requirements.txt into a virtual "
                           "environment; see README.md): " + "; ".join(found))
