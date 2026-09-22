#!/usr/bin/env python3
"""Pinned independent SOAP-encoded message corpora and their canonical comparison.

Copyright (C) 2026 Qore Technologies, s.r.o.

Two sources are independent of this module:

- the W3C "SOAP Version 1.2 Specification Assertions and Test Collection", pinned at
  normative/soap12-testcollection.html; the tests whose messages use the SOAP 1.2 encoding or RPC
  namespaces are extracted verbatim;
- the SOAPBuilders round 2 interop exchanges produced by Apache Axis 1.4's own client and service
  (axis-peer/), captured on the wire.

SOAP 1.1 section 5 distinguishes struct accessors by name and allows multi-reference values to be
serialized as independent elements, so Axis orders struct members and multiRef blocks freely. The
canonical form therefore resolves references and compares structs by accessor name, while array
members keep their order.
"""
import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent
COLLECTION = ROOT / 'normative/soap12-testcollection.html'
SOURCES = ROOT / 'normative/sources.json'
CORPUS = ROOT / 'encoded-corpus'
SOAP11_ENV = 'http://schemas.xmlsoap.org/soap/envelope/'
SOAP12_ENV = 'http://www.w3.org/2003/05/soap-envelope'
SOAP11_ENC = 'http://schemas.xmlsoap.org/soap/encoding/'
SOAP12_ENC = 'http://www.w3.org/2003/05/soap-encoding'
SOAP12_RPC = 'http://www.w3.org/2003/05/soap-rpc'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
XSD = 'http://www.w3.org/2001/XMLSchema'
APACHE_MAP = '{http://xml.apache.org/xml-soap}Map'


def collection_bytes():
    data = COLLECTION.read_bytes()
    expected = json.loads(SOURCES.read_text())['collection']['html_sha256']
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('pinned SOAP 1.2 test collection does not match normative/sources.json')
    return data


def _message(label, body):
    """Splits an HTTP-framed example into its start line/headers and the XML entity; records well-formedness."""
    text = html.unescape(body).strip()
    message = {'from': label}
    if not text.startswith('<'):
        head, _, entity = text.partition('\n\n')
        message['http'] = head.splitlines()
        text = entity.strip()
    message['xml'] = text
    if text:
        try:
            etree.fromstring(text.encode())
            message['well_formed'] = True
        except etree.XMLSyntaxError as error:
            # Reproduced verbatim: errata in the published collection are recorded, never corrected here.
            message['well_formed'] = False
            message['parse_error'] = str(error)
    return message


def extract_w3c():
    """Returns the tests whose messages use the SOAP 1.2 encoding or RPC namespaces, in document order."""
    text = collection_bytes().decode('utf-8')
    blocks = re.split(r'(?=<div class="assertion"><h3><a id=")', text)
    tests = []
    for block in blocks:
        head = re.match(r'<div class="assertion"><h3><a id="([^"]+)"', block)
        if not head:
            continue
        description = re.search(r'Description:\s*</h4>\s*<div class="text">(.*?)</div>', block, re.S)
        messages = [_message(' '.join(label.split())[len('Message sent from '):], body) for label, body in
                    re.findall(r'<p>(Message sent from Node\s+\w+)</p><div class="message"><pre>(.*?)</pre>', block, re.S)]
        joined = ' '.join(m['xml'] for m in messages)
        if SOAP12_ENC not in joined and SOAP12_RPC not in joined:
            continue
        tests.append({'id': head.group(1),
                      'description': ' '.join(html.unescape(re.sub(r'<[^>]+>', '', description.group(1))).split()) if description else '',
                      'messages': messages})
    return tests


def _qname(element, value):
    if value is None:
        return None
    prefix, _, local = value.rpartition(':')
    uri = element.nsmap.get(prefix or None)
    return '{%s}%s' % (uri, local) if uri is not None else value


def canonical(xml, mask_types=()):
    """Returns a comparable structure for a SOAP-encoded envelope, resolving href/id and enc:ref/enc:id."""
    root = etree.fromstring(xml.encode() if isinstance(xml, str) else xml)
    env = etree.QName(root).namespace
    if env not in (SOAP11_ENV, SOAP12_ENV):
        raise ValueError('not a SOAP envelope: %s' % root.tag)
    body = root.find('{%s}Body' % env)
    ids = {}
    for element in body.iter():
        if not isinstance(element.tag, str):
            continue
        key = element.get('id') if env == SOAP11_ENV else element.get('{%s}id' % SOAP12_ENC)
        if key is not None:
            if key in ids:
                raise ValueError('duplicate id %r' % key)
            ids[key] = element

    def target(element):
        if env == SOAP11_ENV:
            href = element.get('href')
            return None if href is None else ids[href[1:]] if href.startswith('#') else href
        ref = element.get('{%s}ref' % SOAP12_ENC)
        return None if ref is None else ids[ref]

    def value(element, stack):
        referenced = target(element)
        if referenced is not None:
            if isinstance(referenced, str):
                return {'external': referenced}
            if id(referenced) in stack:
                return {'cycle': True}
            stack = stack | {id(referenced)}
            element = referenced
        if element.get('{%s}nil' % XSI) in ('true', '1'):
            return {'nil': True}
        xsi_type = _qname(element, element.get('{%s}type' % XSI))
        children = [c for c in element if isinstance(c.tag, str)]
        result = {'type': xsi_type} if xsi_type else {}
        array_type = element.get('{%s}arrayType' % SOAP11_ENC)
        item_type = element.get('{%s}itemType' % SOAP12_ENC)
        if array_type is not None or item_type is not None or xsi_type in ('{%s}Array' % SOAP11_ENC, '{%s}array' % SOAP12_ENC):
            result['arrayType'] = _qname(element, array_type) if array_type else None
            if item_type is not None:
                result['itemType'] = _qname(element, item_type)
            size = element.get('{%s}arraySize' % SOAP12_ENC)
            if size is not None:
                result['arraySize'] = size
            result['items'] = [value(c, stack) for c in children]
            return result
        if not children:
            text = element.text or ''
            result['text'] = '<masked>' if xsi_type in mask_types else text
            return result
        members = [(etree.QName(c).localname, value(c, stack)) for c in children]
        if xsi_type == APACHE_MAP:
            result['entries'] = sorted((json.dumps(m, sort_keys=True) for m in members))
        else:
            result['members'] = sorted(members, key=lambda m: (m[0], json.dumps(m[1], sort_keys=True)))
        return result

    roots = [c for c in body if isinstance(c.tag, str)
             and c.get('{%s}root' % SOAP11_ENC) not in ('0', 'false') and not (env == SOAP11_ENV and c.get('id') and not c.get('href') and c.getparent() is body and c.tag.endswith('multiRef'))]
    return [{'element': etree.QName(r).text, 'encodingStyle': r.get('{%s}encodingStyle' % env),
             'accessors': [(etree.QName(c).text, value(c, frozenset())) for c in r if isinstance(c.tag, str)]}
            for r in roots]


def axis_corpus(captured):
    """Builds the committed Axis corpus from AxisPeer.RecordingHandler captures; dateTime text is masked."""
    masked = ('{%s}dateTime' % XSD,)
    exchanges = {}
    for row in captured:
        if row['operation'] in exchanges:
            raise ValueError('operation %r captured twice' % row['operation'])
        exchanges[row['operation']] = {
            'request': row['request'], 'response': row['response'],
            'canonical_request': canonical(row['request'], masked),
            'canonical_response': canonical(row['response'], masked)}
    return {'copyright': 'Copyright (C) 2026 Qore Technologies, s.r.o.',
            'source': 'Apache Axis 1.4 samples/echo TestClient.executeAll() against InteropTestSoapBindingImpl '
                      '(axis-peer/contracts), captured by AxisPeer.RecordingHandler',
            'canonical_note': 'references resolved; struct and map members compared by name; array order kept; '
                              'xsd:dateTime text masked',
            'exchanges': dict(sorted(exchanges.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--write-w3c', action='store_true', help='regenerate encoded-corpus/w3c-soap12.json')
    parser.add_argument('--write-axis', metavar='CAPTURE', type=Path,
                        help='write encoded-corpus/axis-round2.json from an AxisPeer capture (JSON lines)')
    args = parser.parse_args()
    if args.write_axis:
        captured = [json.loads(line) for line in args.write_axis.read_text().splitlines()]
        (CORPUS / 'axis-round2.json').write_text(json.dumps(axis_corpus(captured), indent=1, ensure_ascii=False) + '\n')
        return 0
    tests = extract_w3c()
    document = {'copyright': 'Copyright (C) 2026 Qore Technologies, s.r.o.',
                'source': 'normative/soap12-testcollection.html',
                'source_sha256': hashlib.sha256(collection_bytes()).hexdigest(), 'tests': tests}
    target = CORPUS / 'w3c-soap12.json'
    text = json.dumps(document, indent=1, ensure_ascii=False) + '\n'
    if args.write_w3c:
        CORPUS.mkdir(exist_ok=True)
        target.write_text(text)
        return 0
    if target.read_text() != text:
        print('encoded-corpus/w3c-soap12.json is not reproducible from the pinned collection', file=sys.stderr)
        return 1
    print('w3c-soap12.json reproduces %d tests' % len(tests))
    return 0


if __name__ == '__main__':
    sys.exit(main())
