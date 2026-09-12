#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Inherited wildcard content through schema, providers, saved graphs and SOAP bindings."""
import unittest

import test_mixed_values as mixed
from test_attribute_values import description, NS, XSD
import survey


def schemas():
    bodies = []
    for label, particle in [('absent', ''), ('sequence', '<xs:sequence/>'), ('all', '<xs:all/>'),
                            ('choice', '<xs:choice minOccurs="0"/>'),
                            ('zero-sequence', '<xs:sequence minOccurs="0" maxOccurs="0">'
                             '<xs:element name="tail"/></xs:sequence>'),
                            ('zero-choice', '<xs:choice minOccurs="0" maxOccurs="0">'
                             '<xs:element name="tail"/></xs:choice>')]:
        for mixed_content in (False, True):
            bodies.append((f'{label}-{mixed_content}', particle, 'xs:anyType', '', mixed_content))
    bodies.append(('empty-group', '<xs:group ref="t:Empty"/>', 'xs:anyType',
                   '<xs:group name="Empty"><xs:sequence/></xs:group>', True))
    for mixed_content in (False, True):
        bodies.append((f'zero-group-{mixed_content}', '<xs:group ref="t:Populated" minOccurs="0" maxOccurs="0"/>',
                       'xs:anyType', '<xs:group name="Populated"><xs:sequence><xs:element name="tail"/>'
                       '</xs:sequence></xs:group>', mixed_content))
    base = ('<xs:complexType name="Base"><xs:complexContent><xs:extension base="xs:anyType"/>'
            '</xs:complexContent></xs:complexType>')
    for label, particle in [('absent', ''), ('all', '<xs:all/>')]:
        bodies.append(('transitive-' + label, particle, 't:Base', base, False))
    for name, particle, parent, declarations, is_mixed in bodies:
        schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">'
                  '<xs:element name="known" type="xs:int"/>' + declarations
                  + '<xs:complexType name="Record"><xs:complexContent'
                  + (' mixed="true"' if is_mixed else '') + f'><xs:extension base="{parent}">{particle}'
                  '</xs:extension></xs:complexContent></xs:complexType>'
                  + ''.join(f'<xs:element name="{root}" type="t:Record"/>' for root in ['value', 'Submit', 'Reply'])
                  + '</xs:schema>')
        yield name, schema


def fixtures():
    for name, schema in schemas():
        documents = []
        for label, content, valid in [
            ('empty', '', True), ('text', 'p:Only', True),
            ('mixed', 'p:Before<t:known>+0017</t:known><!--between-->'
             '<p:unknown>007</p:unknown>p:After', True),
            ('cdata', '<![CDATA[p:Before]]><t:known>17</t:known><t:known>29</t:known><![CDATA[p:After]]>', True),
            ('nested', '<p:unknown><t:known>17</t:known></p:unknown>', True),
            ('invalid', '<t:known>bad</t:known>', False),
            ('invalid-nested', '<p:unknown><t:known>bad</t:known></p:unknown>', False)]:
            def payload(root):
                return f'<t:{root} xmlns:t="{NS}" xmlns:p="urn:partner">{content}</t:{root}>'
            messages = []
            for version, envelope in zip(['11', '12'], survey.SOAP_NAMESPACES):
                for direction, root in [('request', 'Submit'), ('response', 'Reply')]:
                    messages.append({'binding': 'Soap' + version, 'direction': direction,
                                     'xml': f'<s:Envelope xmlns:s="{envelope}"><s:Body>'
                                     + payload(root) + '</s:Body></s:Envelope>'})
            documents.append({'name': name + '/' + label, 'xml': payload('value'),
                              'valid': valid, 'messages': messages})
        yield {'name': name, 'schema': schema, 'selected': False,
               'bindings': {'Soap' + version: description(version, schema) for version in ['11', '12']},
               'documents': documents}


def meaning(node, model, root=True):
    # Wildcard child values stay XML data: compare lexical text as well as names,
    # order and every QName-like token's namespace, without integer normalization.
    attributes = tuple(sorted((key, mixed.qname(node, value) if key == '{' + mixed.XSI + '}type' else value)
                              for key, value in node.attrib.items()))
    events = []
    if node.text:
        events.append(('text', mixed.text_value(node, node.text)))
    for child in node:
        events.append(('element', meaning(child, model, False)) if isinstance(child.tag, str)
                      else ('comment', child.text or ''))
        if child.tail:
            events.append(('text', mixed.text_value(node, child.tail)))
    return None if root else node.tag, attributes, tuple(events)


class AnyTypeInheritanceTest(unittest.TestCase):
    def test_inherited_values_and_bindings(self):
        models = list(fixtures())
        self.assertEqual(17, len(models))
        self.assertEqual(119, sum(len(model['documents']) for model in models))
        mixed.MixedValuesTest.check_models(self, models, meaning)


if __name__ == '__main__':
    unittest.main()
