#!/usr/bin/env python3
"""Pinned independent SOAP-encoded message corpora and their canonical comparison.

Copyright (C) 2026 Qore Technologies, s.r.o.

Three sources are independent of this module:

- the W3C "SOAP Version 1.2 Specification Assertions and Test Collection", pinned at
  normative/soap12-testcollection.html; the tests whose messages use the SOAP 1.2 encoding or RPC
  namespaces are extracted verbatim;
- the section 5 examples of the SOAP 1.1 W3C Note, quoted verbatim from the document whose digest
  normative/sources.json records; the document itself carries its submitters' copyright without
  redistribution terms, so only the examples are kept, and --write-note regenerates them from a copy;
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
# The examples leave their prefixes undeclared. The Note's own bindings are used to check well-formedness;
# e, m, n and xyz are the Note's placeholder prefixes and get placeholder namespaces.
NOTE_NAMESPACES = {
    'SOAP-ENC': SOAP11_ENC,
    'xsi': 'http://www.w3.org/1999/XMLSchema-instance',
    'xsd': 'http://www.w3.org/1999/XMLSchema',
    'e': 'urn:soap11-note:e', 'm': 'urn:soap11-note:m', 'n': 'urn:soap11-note:n', 'xyz': 'urn:soap11-note:xyz',
}


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


def _render(fragment):
    """Renders a preformatted HTML paragraph as a browser does: <br> ends a line and &nbsp; indents it."""
    fragment = re.sub(r'[ \t\r\n]+', ' ', fragment)
    lines = [html.unescape(re.sub(r'<[^>]+>', '', line)).lstrip(' ').replace('\xa0', ' ').rstrip()
             for line in re.split(r'<br\s*/?>', fragment, flags=re.I)]
    return '\n'.join(lines).strip('\n')


def _top_elements(text):
    """Returns the verbatim text of each top-level element of a well-formed fragment, in order."""
    elements = []
    depth = 0
    start = None
    for tag in re.finditer(r'<!--.*?-->|<(/?)[^\s>/!?]+[^>]*?(/?)>', text, re.S):
        if tag.group(0).startswith('<!--'):
            continue
        if tag.group(1):
            depth -= 1
            if not depth:
                elements.append(text[start:tag.end()])
        elif tag.group(2):
            if not depth:
                elements.append(tag.group(0))
        else:
            if not depth:
                start = tag.start()
            depth += 1
    return elements


def extract_note(data):
    """Returns the section 5 examples of the SOAP 1.1 Note in document order; errata are recorded, not corrected."""
    expected = json.loads(SOURCES.read_text())['soap11_note']['html_sha256']
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('SOAP 1.1 Note copy does not match normative/sources.json')
    text = data.decode('iso-8859-1')
    declarations = ' '.join('xmlns:%s="%s"' % item for item in NOTE_NAMESPACES.items())
    section = None
    number = 0
    examples = []
    for match in re.finditer(r'<h[1-4][^>]*>(.*?)</h[1-4]>|<p class=preformatted>(.*?)</p>', text, re.S | re.I):
        if match.group(1) is not None:
            section = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', match.group(1))).split())
            continue
        number += 1
        if not section.startswith('5'):
            continue
        example = {'number': number, 'section': section, 'text': _render(match.group(2))}
        try:
            root = etree.fromstring(('<examples %s>%s</examples>' % (declarations, example['text'])).encode())
            example['well_formed'] = True
            # the top-level elements, verbatim, so a test can place accessors and independent elements
            example['elements'] = _top_elements(example['text'])
            if len(example['elements']) != len(root):
                raise ValueError('example %d: top-level element split disagrees with the parser' % number)
        except etree.XMLSyntaxError as error:
            example['well_formed'] = False
            example['parse_error'] = str(error)
        examples.append(example)
    return examples


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


def note_corpus(data):
    """Returns the SOAP 1.1 Note example corpus document for a verified copy of the Note."""
    source = json.loads(SOURCES.read_text())['soap11_note']
    return {'copyright': 'Examples quoted from the SOAP 1.1 W3C Note, Copyright (C) 2000 DevelopMentor, International '
                         'Business Machines Corporation, Lotus Development Corporation, Microsoft, UserLand Software',
            'source': source['url'], 'source_sha256': source['html_sha256'], 'namespaces': NOTE_NAMESPACES,
            'examples': extract_note(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--write-w3c', action='store_true', help='regenerate encoded-corpus/w3c-soap12.json')
    parser.add_argument('--write-axis', metavar='CAPTURE', type=Path,
                        help='write encoded-corpus/axis-round2.json from an AxisPeer capture (JSON lines)')
    parser.add_argument('--write-note', metavar='HTML', type=Path,
                        help='write encoded-corpus/soap11-note.json from a copy of the SOAP 1.1 Note')
    args = parser.parse_args()
    if args.write_note:
        (CORPUS / 'soap11-note.json').write_text(json.dumps(note_corpus(args.write_note.read_bytes()), indent=1,
                                                            ensure_ascii=False) + '\n')
        return 0
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
