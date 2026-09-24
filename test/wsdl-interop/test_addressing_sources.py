#!/usr/bin/env python3
"""Pinned sources for WS-Addressing 1.0 and the WS-Policy attachment of wsam:Addressing.

Copyright (C) 2026 Qore Technologies, s.r.o.

The WS-Addressing 1.0 Core, SOAP Binding and Metadata Recommendations, the WS-Policy 1.5 Framework and
Attachment Recommendations and the two WS-Addressing schemas are kept verbatim in normative/, and
normative/sources.json records each file's SHA-256 and size. The phrases below are the rules that the
implementation cites; each must appear verbatim in the pinned text.
"""
import hashlib
import html
import json
import re
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent / 'normative'
SOURCES = {'ws_addr_core', 'ws_addr_soap', 'ws_addr_metadata', 'ws_policy', 'ws_policy_attach', 'ws_addr_xsd',
           'ws_addr_metadata_xsd'}
XS = '{http://www.w3.org/2001/XMLSchema}'

# the rules each implementation increment follows, by pinned document
CITED = {
    'ws-addr-core.html': (
        # 3.2: defaults of the optional MAPs
        'If this element is NOT present then the value of the [destination] property is '
        '"http://www.w3.org/2005/08/addressing/anonymous".',
        'When absent, the implied value of this attribute is "http://www.w3.org/2005/08/addressing/reply".',
        # 2.1 and 3.3: the none address
        'Messages sent to EPRs whose [address] is this value MUST be discarded (i.e. not sent).',
        # 3.4: formulating a reply
        'If the reply is a normal message, select the EPR from the related message\'s [reply endpoint] message '
        'addressing property.',
        'In either of the above cases, if the related message lacks a [message id] property, the processor MUST '
        'fault.',
        # 3.2.1: IRI comparison
        'simple string comparison, as indicated in Internationalized Resource Identifiers IETF RFC 3987 section '
        '5.3.1, is sufficient to determine equivalence of these IRIs.',
    ),
    'ws-addr-soap.html': (
        # 3.2.2: cardinality
        'A message MUST NOT contain more than one wsa:To, wsa:ReplyTo, wsa:FaultTo, wsa:Action, or wsa:MessageID '
        'header targeted at a recipient;',
        # 3.4: binding MAPs to headers
        'is annotated with a wsa:IsReferenceParameter attribute',
        'MUST be serialized as an absolute IRI in the corresponding SOAP header block.',
        # 4: SOAP 1.1 SOAPAction
        'The field-value of the SOAPAction HTTP request header MUST either be the value of the [action] property '
        'enclosed in quotation marks, or the empty value "".',
        # 5.2: non-anonymous response endpoints
        'Any response message SHOULD be sent using a separate connection and using the address value specified '
        'by response endpoint.',
        # 6: faults
        'http://www.w3.org/2005/08/addressing/soap/fault',
        'Instead the value of the [Details] property is bound as the value of a new wsa:FaultDetail SOAP header '
        'block.',
        'A header representing a Message Addressing Property is not valid and the message cannot be processed',
        'A required header representing a Message Addressing Property is not present',
        'Specifies that the only address supported is the anonymous address.',
        # 7: the reason non-anonymous responses are opt-in
        'great care should be taken before honoring a [reply endpoint] or [fault endpoint] to avoid inadvertent '
        'participation in the activities of malicious SOAP message senders.',
    ),
    'ws-addr-metadata.html': (
        # 3.1: where the assertion may be attached
        'A policy expression containing the wsam:Addressing policy assertion MUST NOT be attached to a '
        'wsdl:portType or wsdl20:interface',
        'policy assertion MUST NOT be used in the same policy alternative as the wsam:AnonymousResponses policy '
        'assertion.',
        # 4.1 and 4.3: endpoint references on ports
        'the [address] property of the child EPR MUST match the {address} property of the endpoint component',
        'MUST include the contents of the wsa:ReferenceParameters element, if one exists within that EPR.',
        # 4.4.1: explicit and SOAPAction-derived actions
        'In the absence of a wsam:Action attribute on a WSDL input element where a non-empty SOAPAction value is '
        'specified, the value of the [action] property for the input message is the value of the SOAPAction '
        'specified.',
        'then the document MUST be considered invalid.',
        # 4.4.4: the WSDL 1.1 default action pattern
        '[target namespace][delimiter][port type name][delimiter][input|output name]',
        '[target namespace][delimiter][port type name][delimiter][operation name][delimiter]Fault[delimiter]'
        '[fault name]',
        'is ":" when the [target namespace] is a URN, otherwise "/".',
    ),
    'ws-policy.html': (
        'wsp:Optional',
        'wsp:ExactlyOne',
    ),
    'ws-policy-attach.html': (
        # 4.1.2 and 4.1.3: effective policy subjects in WSDL 1.1
        'The effective policy for a WSDL endpoint policy subject includes the element policy of the wsdl11:port '
        'element that defines the endpoint merged with the element policy of the referenced wsdl11:binding '
        'element and the element policy of the referenced wsdl11:portType element that defines the interface of '
        'the endpoint.',
        'includes the element policy of the wsdl11:portType/wsdl11:operation element that defines the operation '
        'merged with that of the corresponding wsdl11:binding/wsdl11:operation element.',
    ),
}


def text(name):
    """The whitespace-normalized text of a pinned HTML document."""
    data = (ROOT / name).read_text(encoding='utf-8')
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', data)).split())


class AddressingSourcesTest(unittest.TestCase):
    def entries(self):
        addressing = json.loads((ROOT / 'sources.json').read_text())['addressing']
        return {k: v for k, v in addressing.items() if isinstance(v, dict)}

    def test_pinned_sources(self):
        entries = self.entries()
        self.assertEqual(SOURCES, set(entries))
        for name, entry in entries.items():
            with self.subTest(source=name):
                data = (ROOT / entry['path']).read_bytes()
                self.assertEqual((entry['bytes'], entry['sha256']), (len(data), hashlib.sha256(data).hexdigest()))
                self.assertTrue(entry['url'].startswith('https://www.w3.org/'))
                self.assertIn('W3C', data.decode('utf-8'))

    def test_sources_state_the_rules_the_implementation_cites(self):
        for name, phrases in CITED.items():
            document = text(name)
            for phrase in phrases:
                with self.subTest(document=name, phrase=phrase[:60]):
                    self.assertIn(phrase, document)

    def test_cited_documents_are_pinned(self):
        pinned = {entry['path'] for entry in self.entries().values()}
        self.assertLessEqual(set(CITED), pinned)

    def test_schemas_declare_the_namespaces_used(self):
        # wsa:FaultDetail is defined only by the SOAP Binding (section 6.2), not by the schema
        core = ET.parse(ROOT / 'ws-addr.xsd').getroot()
        self.assertEqual('http://www.w3.org/2005/08/addressing', core.get('targetNamespace'))
        elements = {e.get('name') for e in core.findall(XS + 'element')}
        self.assertLessEqual({'EndpointReference', 'To', 'From', 'ReplyTo', 'FaultTo', 'Action', 'MessageID',
                              'RelatesTo', 'ReferenceParameters', 'ProblemHeaderQName', 'ProblemIRI',
                              'ProblemAction', 'RetryAfter'}, elements)
        faults = {e.get('value') for e in core.iter(XS + 'enumeration')}
        self.assertLessEqual({'tns:InvalidAddressingHeader', 'tns:InvalidAddress', 'tns:InvalidEPR',
                              'tns:InvalidCardinality', 'tns:MissingAddressInEPR', 'tns:DuplicateMessageID',
                              'tns:ActionMismatch', 'tns:MessageAddressingHeaderRequired',
                              'tns:DestinationUnreachable', 'tns:ActionNotSupported', 'tns:EndpointUnavailable'},
                             faults)
        metadata = ET.parse(ROOT / 'ws-addr-metadata.xsd').getroot()
        self.assertEqual('http://www.w3.org/2007/05/addressing/metadata', metadata.get('targetNamespace'))
        self.assertLessEqual({'Addressing', 'AnonymousResponses', 'NonAnonymousResponses'},
                             {e.get('name') for e in metadata.findall(XS + 'element')})
        self.assertIn('Action', {a.get('name') for a in metadata.findall(XS + 'attribute')})


if __name__ == '__main__':
    unittest.main()
