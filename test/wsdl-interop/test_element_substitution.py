#!/usr/bin/env python3
"""XSD 1.0 element affiliation constraints and inherited message element types.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import os
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
import test_type_final as matrix
from test_attribute_values import NS, XSD

# Supporting-oracle defects retained explicitly; these are rejected by the normative
# membership expectation and the corrected module dependency, not counted as valid inputs.
# See element-substitution-evidence.md for the derivation rules and source root causes.
ORACLE_DIFFERENCES = {
    "element-block-False-'restriction'-Head/Restricted": {'lxml': True},
    "element-block-True-'restriction'-Head/Restricted": {'lxml': True},
    "type-block-restriction-extension-'extension'/Member": {'lxml': True},
    "union-head-'restriction'/Member": {'lxml': True, 'xerces': True},
}


def element(name, datatype='xs:int', attributes=''):
    typed = f' type="{datatype}"' if datatype else ''
    return f'<xs:element name="{name}"{typed} {attributes}/>'


def source(body, defaults='', inherited=False):
    roots = (element('Submit', '', 'substitutionGroup="t:Payload"')
             + element('Reply', '', 'substitutionGroup="t:Payload"') if inherited else
             element('Submit', 't:Record', 'final=""') + element('Reply', 't:Record', 'final=""'))
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}" {defaults}>
      {body}<xs:complexType name="Record" final="" block=""><xs:sequence>
        <xs:element name="item" type="xs:int"/></xs:sequence></xs:complexType>{roots}</xs:schema>'''


def definitions():
    for control in ('', 'extension', 'restriction', '#all', ' extension restriction extension '):
        for datatype, relation in (('xs:decimal', 'identity'), ('xs:int', 'restriction'), ('xs:string', 'unrelated')):
            body = element('Head', 'xs:decimal', f'final="{control}"')
            body += element('Member', datatype, 'substitutionGroup="t:Head"')
            valid = relation == 'identity' or relation == 'restriction' and control not in (
                'restriction', '#all', ' extension restriction extension ')
            yield matrix.Case(f'final-{control!r}-{relation}', source(body), valid)
    for default in ('', 'restriction', 'extension', '#all', 'list union', 'list union extension'):
        for override in (None, ''):
            control = '' if override is None else 'final=""'
            body = element('Head', 'xs:decimal', control) + element('Member', 'xs:int', 'substitutionGroup="t:Head"')
            yield matrix.Case(f'default-{default!r}-{override!r}', source(body, f'finalDefault="{default}"'),
                              override == '' or default not in ('restriction', '#all'))
    for method in ('extension', 'restriction'):
        for control in ('', 'extension', 'restriction', '#all'):
            for content in ('complexContent', 'simpleContent'):
                base = '' if content == 'complexContent' else '<xs:simpleContent><xs:extension base="xs:int"/></xs:simpleContent>'
                body = f'<xs:complexType name="B">{base}</xs:complexType><xs:complexType name="D">'
                body += f'<xs:{content}><xs:{method} base="t:B"/></xs:{content}></xs:complexType>'
                body += element('Head', 't:B', f'final="{control}"') + element('Member', 't:D', 'substitutionGroup="t:Head"')
                yield matrix.Case(f'{content}-{method}-{control!r}', source(body), control not in (method, '#all'))
    for datatype, definitions_text in (
        ('xs:int', ''),
        ('t:L', '<xs:simpleType name="L"><xs:list itemType="xs:int"/></xs:simpleType>'),
        ('t:U', '<xs:simpleType name="U"><xs:union memberTypes="xs:int xs:boolean"/></xs:simpleType>'),
    ):
        for control in ('', '#all'):
            body = element('Member', '', 'substitutionGroup="t:Middle"')
            body += element('Middle', '', 'substitutionGroup="t:Head"')
            body += element('Head', datatype, f'final="{control}"') + definitions_text
            yield matrix.Case(f'type-inheritance-{datatype}-{control!r}', source(body), True)
    for control in ('', '#all', 'restriction', 'extension'):
        yield matrix.Case(f'message-root-inheritance-{control!r}', source(
            element('Payload', 't:Record', f'final="{control}"'), inherited=True), True)
    for control in ('list', 'union', 'substitution', 'bad', '#ALL', '#all restriction',
                    'restriction #all', 'extension,restriction', 'extension&#160;restriction'):
        yield matrix.Case('invalid-final-' + control, source(element('Head', attributes=f'final="{control}"')), False)
    for kind, body in (
        ('self', element('Head', attributes='substitutionGroup="t:Head"')),
        ('cycle', element('Head', attributes='substitutionGroup="t:Member"')
                  + element('Member', attributes='substitutionGroup="t:Head"')),
        ('untyped-cycle', element('Head', '', 'substitutionGroup="t:Member"')
                  + element('Member', '', 'substitutionGroup="t:Head"')),
        ('missing', element('Member', attributes='substitutionGroup="t:Missing"')),
        ('inherited-id-default', element('Head', 'xs:ID')
                  + element('Member', '', 'substitutionGroup="t:Head" default="id"')),
    ):
        yield matrix.Case(kind, source(body), False)
    for control in ('substitution', '#all', 'restriction', 'extension'):
        # Block constrains instance substitution, not affiliation validity.
        yield matrix.Case('blocked-but-valid-' + control, source(element('Head', 'xs:decimal', f'block="{control}"')
            + element('Member', 'xs:int', 'substitutionGroup="t:Head"')), True)
    yield matrix.Case('abstract-member-type', source('<xs:complexType name="B" abstract="true"/>'
        '<xs:complexType name="D" abstract="true"><xs:complexContent><xs:extension base="t:B"/>'
        '</xs:complexContent></xs:complexType>' + element('Head', 't:B')
        + element('Member', 't:D', 'substitutionGroup="t:Head"')), True)


def membership_models():
    for abstract in (False, True):
        for control in ('', 'extension', 'restriction', 'substitution', '#all'):
            for head in ('Head', 'Middle'):
                body = element('Head', 'xs:decimal', f'abstract="{str(abstract).lower()}" block="{control}"')
                body += element('Middle', 'xs:decimal', 'abstract="true" block="substitution" substitutionGroup="t:Head"')
                body += element('Same', 'xs:decimal', 'substitutionGroup="t:Middle"')
                body += element('Restricted', 'xs:int', 'substitutionGroup="t:Middle"')
                members = set()
                if head == 'Head':
                    if not abstract:
                        members.add('Head')
                    if control not in ('substitution', '#all'):
                        members.add('Same')
                        if control != 'restriction':
                            members.add('Restricted')
                yield f'element-block-{abstract}-{control!r}-{head}', body, head, members, '17'
    for lower, upper in (('extension', 'restriction'), ('restriction', 'extension')):
        for control in ('', 'extension', 'restriction', '#all'):
            body = '<xs:complexType name="B"/><xs:complexType name="M" block="' + control + '">'
            body += f'<xs:complexContent><xs:{upper} base="t:B"/></xs:complexContent></xs:complexType>'
            body += f'<xs:complexType name="D" block="#all"><xs:complexContent><xs:{lower} base="t:M"/>'
            body += '</xs:complexContent></xs:complexType>'
            body += element('Head', 't:B') + element('Member', 't:D', 'substitutionGroup="t:Head"')
            yield f'type-block-{lower}-{upper}-{control!r}', body, 'Head', {'Head'} if control else {'Head', 'Member'}, ''
    for control in ('', 'restriction', '#all'):
        body = '<xs:simpleType name="U"><xs:union memberTypes="xs:int xs:boolean"/></xs:simpleType>'
        body += element('Head', 't:U', f'block="{control}"')
        body += element('Member', 'xs:int', 'substitutionGroup="t:Head"')
        yield f'union-head-{control!r}', body, 'Head', {'Head'} if control else {'Head', 'Member'}, '17'


class ElementSubstitutionTest(matrix.TypeFinalTest):
    case_factory = staticmethod(definitions)
    expected_counts = (72, 40, 384, 64, 320)
    worker = os.environ.get('WSDL_ELEMENT_SUBSTITUTION_WORKER', 'type-final.qr')

    def test_actual_membership_matches_independent_particle_validation(self):
        cases, jobs = [], []
        count = 0
        for index, (name, body, head, members, value) in enumerate(membership_models()):
            text = source(body + '<xs:element name="Container"><xs:complexType><xs:sequence>'
                f'<xs:element ref="t:{head}"/></xs:sequence></xs:complexType></xs:element>')
            compiled = etree.XMLSchema(etree.fromstring(text.encode()))
            candidates = sorted({node.get('name') for node in etree.fromstring(text.encode()).findall(f'{{{XSD}}}element')}
                                - {'Container', 'Submit', 'Reply'})
            documents = []
            for candidate in candidates:
                xml = f'<t:Container xmlns:t="{NS}"><t:{candidate}>{value}</t:{candidate}></t:Container>'
                key = name + '/' + candidate
                self.assertEqual(ORACLE_DIFFERENCES.get(key, {}).get('lxml', candidate in members),
                                 compiled.validate(etree.fromstring(xml.encode())),
                                 (name, candidate, str(compiled.error_log)))
                documents.append({'name': key, 'xml': xml, 'valid': candidate in members})
            count += len(documents)
            cases.append({'name': name, 'schema': text, 'uri': NS, 'head': head,
                          'members': sorted(f'{{{NS}}}{member}' for member in members), 'documents': documents})
            jobs.append(SchemaJob(name, f'http://example.invalid/substitution/{index}.xsd', text.encode(),
                                  {document['name']: document['xml'].encode() for document in documents}))
        self.assertEqual(31, len(cases))
        self.assertEqual(102, count)
        document_names = {document['name'] for case in cases for document in case['documents']}
        self.assertEqual(set(), set(ORACLE_DIFFERENCES) - document_names)
        oracle = run_independent(jobs)
        for case in cases:
            self.assertTrue(oracle['schemas'][case['name']]['ok'])
            self.assertEqual([], oracle['schemas'][case['name']]['warnings'])
            for document in case['documents']:
                result = oracle['documents'][document['name']]
                self.assertEqual(ORACLE_DIFFERENCES.get(document['name'], {}).get('xerces', document['valid']),
                                 result['ok'], (document, result))
                self.assertEqual([], result['warnings'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        worker = os.environ.get('WSDL_ELEMENT_GROUP_WORKER', 'element-substitution-groups.qr')
        with tempfile.TemporaryDirectory(prefix='wsdl-element-groups-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(cases))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                      str(Path(__file__).parent / worker), str(path)],
                                     capture_output=True, text=True, timeout=180)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual('', process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        for case in cases:
            for copy in (False, True):
                self.assertEqual({'name': case['name'], 'copy': copy, 'members': case['members']}, next(rows))
            for document in case['documents']:
                row = next(rows)
                self.assertEqual((case['name'], document['name']), (row['name'], row['document']))
                self.assertEqual('' if document['valid'] else 'PARSE-XML-EXCEPTION', row['error'], row)
        self.assertIsNone(next(rows, None))
        print(f'{mode}: {len(cases)} substitution groups, {count} independent particle documents, '
              f'{len(cases) * 2} original/reconstructed membership maps', flush=True)


if __name__ == '__main__':
    unittest.main()
