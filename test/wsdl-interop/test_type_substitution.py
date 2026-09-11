#!/usr/bin/env python3
"""XSD instance derivation, block and abstract controls in actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
from test_type_identity import expanded_type

XSI = 'http://www.w3.org/2001/XMLSchema-instance'
BASE = '<xs:complexType name="A"><xs:attribute name="id" type="xs:int" use="required"/></xs:complexType>'
EXTENSION = '<xs:complexType name="B"><xs:complexContent><xs:extension base="t:A"><xs:attribute name="code" type="xs:int"/></xs:extension></xs:complexContent></xs:complexType>'
TRANSITIVE = '<xs:complexType name="C"><xs:complexContent><xs:extension base="t:B"/></xs:complexContent></xs:complexType>'
RESTRICTION = '<xs:complexType name="R"><xs:complexContent><xs:restriction base="t:A"><xs:attribute name="id" type="xs:int" use="required"/></xs:restriction></xs:complexContent></xs:complexType>'
MIXED = '<xs:complexType name="Q"><xs:complexContent><xs:extension base="t:R"/></xs:complexContent></xs:complexType>'
SIMPLE = '''<xs:simpleType name="I"><xs:restriction base="xs:int"/></xs:simpleType>
<xs:simpleType name="J"><xs:restriction base="t:I"><xs:minInclusive value="0"/></xs:restriction></xs:simpleType>
<xs:simpleType name="L"><xs:list itemType="xs:int"/></xs:simpleType>
<xs:simpleType name="LR"><xs:restriction base="t:L"><xs:length value="2"/></xs:restriction></xs:simpleType>
<xs:simpleType name="U"><xs:union memberTypes="xs:int xs:boolean"/></xs:simpleType>'''


@dataclass(frozen=True)
class Case:
    name: str
    schema: str
    selected: str
    value: object
    content: str
    valid: bool


def source(definitions, declared='t:A', element='', schema='', roots=''):
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}" {schema}>
      {definitions}<xs:complexType name="Record"><xs:sequence>
        <xs:element name="item" type="{declared}" {element}/></xs:sequence></xs:complexType>
      <xs:element name="Submit" type="t:Record" {roots}/><xs:element name="Reply" type="t:Record" {roots}/>
    </xs:schema>'''


def cases():
    paths = {'A': set(), 'B': {'extension'}, 'C': {'extension'}, 'R': {'restriction'},
             'Q': {'extension', 'restriction'}}
    for location in ('element', 'type', 'default'):
        for block in ('', 'extension', 'restriction', '#all', 'substitution'):
            if location == 'type' and block == 'substitution':
                continue  # Not a schema grammar production; covered by negative construction tests.
            base = BASE if location != 'type' else BASE.replace('name="A"', f'name="A" block="{block}"')
            schema = source(base + EXTENSION + TRANSITIVE + RESTRICTION + MIXED,
                            element=f'block="{block}"' if location == 'element' else '',
                            schema=f'blockDefault="{block}"' if location == 'default' else '')
            exclusions = {'extension', 'restriction'} if block == '#all' else set(block.split())
            for selected, methods in paths.items():
                yield Case(f'{location}/{block!r}/{selected}', schema, 't:' + selected,
                           {'^attributes^': {'id': 17}}, ' id="17"/>', not methods & exclusions)
    for abstract in ('A', 'B', 'C'):
        definitions = (BASE + EXTENSION + TRANSITIVE).replace(f'name="{abstract}"', f'name="{abstract}" abstract="true"')
        for selected in ('A', 'B', 'C'):
            yield Case(f'abstract-type/{abstract}/{selected}', source(definitions), 't:' + selected,
                       {'^attributes^': {'id': 17}}, ' id="17"/>', selected != abstract)
    for selected in ('A', 'B', 'C'):
        yield Case('abstract-element/' + selected, source(BASE + EXTENSION + TRANSITIVE, roots='abstract="true"'),
                   't:' + selected, {'^attributes^': {'id': 17}}, ' id="17"/>', False)
    middle = EXTENSION.replace('name="B"', 'name="B" block="extension"')
    yield Case('intermediate-block', source(BASE + middle + TRANSITIVE), 't:C',
               {'^attributes^': {'id': 17}}, ' id="17"/>', True)
    for declared, selected, value, lexical in [('xs:decimal', 't:J', 17, '17'), ('xs:integer', 'xs:short', 17, '17'),
            ('xs:anySimpleType', 't:L', [17, 18], '17 18'), ('xs:anyType', 't:LR', [17, 18], '17 18'),
            ('t:L', 't:LR', [17, 18], '17 18'), ('t:U', 't:J', 17, '17')]:
        for block in ('', 'extension', 'restriction'):
            yield Case(f'simple/{declared}/{selected}/{block!r}', source(SIMPLE, declared, f'block="{block}"'),
                       selected, value, '>' + lexical + '</item>', block != 'restriction')
    yield Case('unrelated-simple', source(SIMPLE, 't:I'), 'xs:string', '17', '>17</item>', False)
    yield Case('invalid-selected-facet', source(SIMPLE, 't:I'), 't:J', -1, '>-1</item>', False)
    yield Case('unrelated-complex', source(BASE + '<xs:complexType name="Other"/>'), 't:Other', {}, '/>', False)


def payload(case, response):
    root = 'Reply' if response else 'Submit'
    return (f'<t:{root} xmlns:t="{NS}" xmlns:i="{XSI}" xmlns:xs="{XSD}">'
            f'<item i:type="{case.selected}"{case.content}</t:{root}>')


def envelope(case, version, response):
    uri = 'http://www.w3.org/2003/05/soap-envelope' if version == '12' else 'http://schemas.xmlsoap.org/soap/envelope/'
    return f'<s:Envelope xmlns:s="{uri}"><s:Body>{payload(case, response)}</s:Body></s:Envelope>'


class TypeSubstitutionTest(unittest.TestCase):
    def test_controls_values_and_retained_types(self):
        models = list(cases())
        self.assertEqual(104, len(models))
        self.assertEqual(len(models), len({case.name for case in models}))
        jobs, inputs, compilers, declarations = [], [], {}, {}
        for index, case in enumerate(models):
            schema = etree.fromstring(case.schema.encode())
            compilers[case.name] = etree.XMLSchema(schema)
            item = schema.find(f'{{{XSD}}}complexType[@name="Record"]/{{{XSD}}}sequence/{{{XSD}}}element')
            prefix, local = item.get('type').split(':')
            declarations[case.name] = (item.nsmap[prefix], local)
            documents = {f'input/{index}/{int(response)}': payload(case, response).encode() for response in (False, True)}
            for xml in documents.values():
                self.assertEqual(case.valid, compilers[case.name].validate(etree.fromstring(xml)), case.name)
            jobs.append(SchemaJob(case.name, f'http://example.invalid/substitution/{index}.xsd', case.schema.encode(), documents))
            for version in ('11', '12'):
                inputs.append({'name': case.name + '/' + version, 'wsdl': description(version, case.schema),
                               'binding': 'Soap' + version, 'selected': case.selected, 'value': case.value,
                               'request': envelope(case, version, False), 'response': envelope(case, version, True)})
        reference = run_independent(jobs)
        for index, case in enumerate(models):
            self.assertTrue(reference['schemas'][case.name]['ok'], (case.name, reference['schemas'][case.name]))
            self.assertEqual([], reference['schemas'][case.name]['warnings'])
            for response in (False, True):
                result = reference['documents'][f'input/{index}/{int(response)}']
                self.assertEqual(case.valid, result['ok'], (case.name, result))
                self.assertEqual([], result['warnings'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        with tempfile.TemporaryDirectory(prefix='wsdl-type-substitution-') as directory:
            path = Path(directory) / 'cases.json'
            path.write_text(json.dumps(inputs))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                      str(Path(__file__).with_name('type-substitution.qr')), str(path)],
                                     capture_output=True, text=True, timeout=240)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-3000:])
        self.assertEqual('', process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        outputs = {case.name: {} for case in models}
        count = rejected = 0
        for index, case in enumerate(models):
            for version in ('11', '12'):
                for copy in (False, True):
                    for response in (False, True):
                        row = next(rows)
                        count += 1
                        self.assertEqual((case.name + '/' + version, copy, response),
                                         (row['case'], row['copy'], row['response']))
                        if not case.valid:
                            self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['decode_error'], row)
                            self.assertEqual('SOAP-SERIALIZATION-ERROR', row['encode_error'], row)
                            self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['retained_error'], row)
                            rejected += 1
                            continue
                        for field in ('decode_error', 'encode_error', 'retained_error'):
                            self.assertEqual('', row[field], row)
                        self.assertEqual({'item': case.value}, row['native'], row)
                        self.assertEqual(row['native'], row['encoded_native'], row)
                        for output in ('xml', 'retained'):
                            root = etree.fromstring(row[output].encode())
                            uri = 'http://www.w3.org/2003/05/soap-envelope' if version == '12' else 'http://schemas.xmlsoap.org/soap/envelope/'
                            self.assertEqual(f'{{{uri}}}Envelope', root.tag)
                            body = root.find(f'{{{uri}}}Body')
                            self.assertEqual(1, len(body))
                            content = body[0]
                            self.assertEqual(f'{{{NS}}}' + ('Reply' if response else 'Submit'), content.tag)
                            compilers[case.name].assertValid(content)
                            item = content.find('item')
                            # Omitted identical type annotations on native output are legal; retained XML keeps its explicit annotation.
                            expected = (XSD if case.selected.startswith('xs:') else NS, case.selected.split(':')[1])
                            actual = expanded_type(item)
                            if expected != declarations[case.name] or actual is not None or output == 'retained':
                                self.assertEqual(expected, actual, row)
                            outputs[case.name][f'output/{index}/{version}/{int(copy)}/{int(response)}/{output}'] = etree.tostring(content)
        self.assertIsNone(next(rows, None))
        self.assertEqual(len(models) * 8, count)
        self.assertEqual(sum(not case.valid for case in models) * 8, rejected)
        output_jobs = [SchemaJob(case.name, f'http://example.invalid/substitution/{index}.xsd', case.schema.encode(), outputs[case.name])
                       for index, case in enumerate(models) if case.valid]
        reference = run_independent(output_jobs)
        for name, result in reference['documents'].items():
            self.assertTrue(result['ok'], (name, result))
            self.assertEqual([], result['warnings'])
        print(f'{mode}: {len(models)} schema/type cases, {count} rows, {rejected} required rejections, '
              f'{sum(map(len, outputs.values()))} independently validated outputs', flush=True)


if __name__ == '__main__':
    unittest.main()
