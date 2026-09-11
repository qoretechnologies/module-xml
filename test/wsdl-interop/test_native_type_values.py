#!/usr/bin/env python3
"""Portable native type selection through saved values and independent schemas.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
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
from test_type_substitution import Case, cases as control_cases, source, payload, envelope


def cases():
    yield from control_cases()
    definitions = '''<xs:complexType name="A"><xs:sequence><xs:element name="number" type="xs:int"/>
      </xs:sequence></xs:complexType><xs:complexType name="B"><xs:complexContent><xs:extension base="t:A">
      <xs:sequence><xs:element name="description" type="xs:string"/></xs:sequence>
      </xs:extension></xs:complexContent></xs:complexType>'''
    yield Case('derived-element-content', source(definitions), 't:B',
               {'number': 17, 'description': 'Replacement part'},
               '><number>17</number><description>Replacement part</description></item>', True)


class NativeTypeValuesTest(unittest.TestCase):
    def test_saved_values_and_receiver_checks(self):
        models = list(cases())
        self.assertEqual(105, len(models))
        self.assertEqual(len(models), len({case.name for case in models}))
        jobs, inputs, compilers, declared = [], [], {}, {}
        for index, case in enumerate(models):
            schema = etree.fromstring(case.schema.encode())
            compilers[case.name] = etree.XMLSchema(schema)
            item = schema.find(f'{{{XSD}}}complexType[@name="Record"]/{{{XSD}}}sequence/{{{XSD}}}element')
            prefix, local = item.get('type').split(':')
            declared[case.name] = (item.nsmap[prefix], local)
            documents = {f'input/{index}/{int(response)}': payload(case, response).encode() for response in (False, True)}
            for xml in documents.values():
                self.assertEqual(case.valid, compilers[case.name].validate(etree.fromstring(xml)), case.name)
            jobs.append(SchemaJob(case.name, f'http://example.invalid/native-type-values/{index}.xsd', case.schema.encode(), documents))
            for version in ('11', '12'):
                inputs.append({'name': case.name + '/' + version, 'wsdl': description(version, case.schema),
                               'binding': 'Soap' + version, 'value': case.value,
                               'selected_uri': XSD if case.selected.startswith('xs:') else NS,
                               'selected_name': case.selected.split(':')[1],
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
        with tempfile.TemporaryDirectory(prefix='wsdl-native-type-values-') as directory:
            path = Path(directory) / 'cases.json'
            path.write_text(json.dumps(inputs))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                                      str(Path(__file__).with_name('native-type-values.qr')), str(path)],
                                     capture_output=True, text=True, timeout=240)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-3000:])
        self.assertEqual('', process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        outputs = {case.name: {} for case in models}
        count = rejected = 0
        for index, case in enumerate(models):
            selected = (XSD if case.selected.startswith('xs:') else NS, case.selected.split(':')[1])
            expected = case.value if selected == declared[case.name] else {
                '^type^': {'namespace_uri': selected[0], 'local_name': selected[1]}, '^val^': case.value}
            for version in ('11', '12'):
                for copy in (False, True):
                    for response in (False, True):
                        row = next(rows)
                        count += 1
                        self.assertEqual((case.name + '/' + version, copy, response),
                                         (row['case'], row['copy'], row['response']))
                        if not case.valid:
                            self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['decode_error'], row)
                            self.assertEqual('SOAP-SERIALIZATION-ERROR', row['manual_error'], row)
                            self.assertNotIn('xml', row)
                            self.assertNotIn('manual', row)
                            rejected += 1
                            continue
                        for field in ('decode_error', 'encode_error', 'manual_error'):
                            self.assertEqual('', row[field], row)
                        self.assertEqual({'item': expected}, row['native'], row)
                        self.assertEqual(row['native'], row['restored'], row)
                        self.assertEqual({'item': case.value}, row['default_native'], row)
                        for output in ('xml', 'manual'):
                            root = etree.fromstring(row[output].encode())
                            uri = 'http://www.w3.org/2003/05/soap-envelope' if version == '12' else 'http://schemas.xmlsoap.org/soap/envelope/'
                            self.assertEqual(f'{{{uri}}}Envelope', root.tag)
                            body = root.find(f'{{{uri}}}Body')
                            self.assertEqual(1, len(body))
                            content = body[0]
                            self.assertEqual(f'{{{NS}}}' + ('Reply' if response else 'Submit'), content.tag)
                            compilers[case.name].assertValid(content)
                            actual = expanded_type(content.find('item'))
                            if selected != declared[case.name] or actual is not None:
                                self.assertEqual(selected, actual, row)
                            outputs[case.name][f'output/{index}/{version}/{int(copy)}/{int(response)}/{output}'] = etree.tostring(content)
        self.assertIsNone(next(rows, None))
        self.assertEqual(len(models) * 8, count)
        self.assertEqual(sum(not case.valid for case in models) * 8, rejected)
        reference = run_independent([SchemaJob(case.name, f'http://example.invalid/native-type-values/{index}.xsd',
                    case.schema.encode(), outputs[case.name]) for index, case in enumerate(models) if case.valid])
        for name, result in reference['documents'].items():
            self.assertTrue(result['ok'], (name, result))
            self.assertEqual([], result['warnings'])
        print(f'{mode}: {len(models)} schema/type cases, {count} rows, {rejected} required rejecting rows, '
              f'{sum(map(len, outputs.values()))} independently validated outputs', flush=True)


if __name__ == '__main__':
    unittest.main()
