#!/usr/bin/env python3
"""Independent typed observer values, scope, protocol and resource regressions.

Copyright (C) 2026 Qore Technologies, s.r.o.
These tests qualify the oracle harness; corpus integration has a separate gate.
"""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import independent
from independent import SchemaJob, run_typed, check_results
from typed_reference import compare, validate_observation, MAX_DEPTH

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / 'fixtures' / 'typed-observations.json'


class TypedReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(FIXTURE.read_text())
        cls.jobs = [SchemaJob(c['name'], f'http://example.invalid/{c["name"]}.xsd', c['schema'].encode(),
                             {c['name'] + '/' + side: c[side].encode() for side in ('left', 'right')})
                    for c in cls.cases]
        cls.report = run_typed(cls.jobs)

    def test_complete_value_matrix(self):
        self.assertEqual(57, len(self.cases))
        self.assertEqual(57, len({c['name'] for c in self.cases}))
        expected = {name for job in self.jobs for name in job.documents}
        self.assertEqual(114, len(expected))
        self.assertEqual(expected, set(self.report['documents']))
        self.assertEqual(expected, set(self.report['observations']))
        self.assertEqual({c['name'] for c in self.cases}, set(self.report['schemas']))
        for row in [*self.report['schemas'].values(), *self.report['documents'].values()]:
            self.assertTrue(row['ok'], row)
            self.assertEqual([], row['warnings'])
        for case in self.cases:
            with self.subTest(case=case['name']):
                left = self.report['observations'][case['name'] + '/left']
                right = self.report['observations'][case['name'] + '/right']
                self.assertEqual(case['same'], compare(left, right, order='per-name'))
                self.assertEqual(case['same'] and case['name'] != 'all-order', compare(left, right, order='exact'))

    def test_exact_observed_values_and_selected_members(self):
        values = self.report['observations']
        self.assertEqual({'kind': 'float', 'bits': '2147483648'}, values['float-zero-sign/left']['root']['psvi']['value'])
        self.assertEqual({'kind': 'double', 'bits': '9223372036854775808'}, values['double-zero-sign/left']['root']['psvi']['value'])
        self.assertEqual({'kind': 'binary', 'base64': 'AAH/'}, values['binary-hex/left']['root']['psvi']['value'])
        self.assertEqual('1.00000000000000000000000000001', values['decimal-distinct/left']['root']['psvi']['value']['value'])
        left = values['list-selected-member/left']['root']['psvi']
        right = values['list-selected-member/right']['root']['psvi']
        self.assertEqual(left['value'], right['value'])
        self.assertEqual([34, 34], left['list_types'])
        self.assertEqual('{}Padded', left['list_members'][0])
        self.assertEqual('{http://www.w3.org/2001/XMLSchema}int', right['list_members'][0])
        self.assertEqual([None, None], values['qname-list-prefix/left']['root']['psvi']['list_members'])
        self.assertTrue(values['attribute-default/left']['root']['attributes']['{}number']['schema_specified'])
        self.assertFalse(values['attribute-default/right']['root']['attributes']['{}number']['schema_specified'])

    def test_invalid_observations_fail_even_when_both_sides_match(self):
        original = self.report['observations']['float-zero-sign/left']
        variants = []
        for key, value in [('bits', str(1 << 32)), ('bits', '-1'), ('bits', 'NaN'), ('kind', 'double')]:
            item = deepcopy(original)
            item['root']['psvi']['value'][key] = value
            variants.append(item)
        for key, value in [('nil', 1), ('validity', 1), ('validity', 0), ('attempted', 0),
                           ('attempted', True), ('value_type', 46),
                           ('schema_specified', None), ('list_types', [5]), ('type', 'not-expanded')]:
            item = deepcopy(original)
            item['root']['psvi'][key] = value
            variants.append(item)
        for key in original['root']:
            item = deepcopy(original)
            del item['root'][key]
            variants.append(item)
        item = deepcopy(original)
        item['root']['namespace_declarations']['xml'] = 'urn:wrong'
        variants.append(item)
        item = deepcopy(original)
        item['root']['unknown'] = 'field'
        variants.append(item)
        for value in [None, {}, {'format': True, 'root': original['root']}, *variants]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                compare(value, value, order='exact')
        with self.assertRaisesRegex(ValueError, 'ordering contract'):
            compare(original, original, order='ignored')
        # Lists carry one actual value and selected member/type entry per item.
        for field in ('list_members', 'list_types', 'value'):
            item = deepcopy(self.report['observations']['list-selected-member/left'])
            item['root']['psvi'][field].pop()
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_observation(item)

        item = deepcopy(self.report['observations']['date-zone/left'])
        item['root']['psvi']['value']['lexical'] = '2026-02-30'
        with self.assertRaisesRegex(ValueError, 'invalid Gregorian date'):
            validate_observation(item)

    def test_observation_protocol_completeness(self):
        observation = self.report['observations']['decimal-equivalent/left']
        enc = independent._encode
        jobs = [SchemaJob('schema', 'urn:schema', b'schema', {'good': b'good', 'bad': b'bad'}),
                SchemaJob('broken', 'urn:broken', b'broken', {'unreachable': b'xml'})]
        record = 'T\tgood\t' + enc(json.dumps(observation).encode())
        lines = ['version\t' + enc(b'Xerces-J 2.12.2') + '\t' + enc(b'JDK'), 'S\tschema\tvalid\t\t',
                 record, 'V\tgood\tvalid\t\t', 'V\tbad\tinvalid\t' + enc(b'bad value') + '\t',
                 'S\tbroken\tinvalid\t' + enc(b'bad schema') + '\t',
                 'V\tunreachable\tunreachable\t' + enc(b'schema failed') + '\t']
        report = check_results(jobs, '\n'.join(lines), typed=True)
        self.assertEqual(observation, report['observations']['good'])
        self.assertIsNone(report['observations']['bad'])
        self.assertIsNone(report['observations']['unreachable'])
        variants = [lines[:2] + lines[3:], lines[:3] + lines[2:], lines + [record],
                    lines[:4] + [record.replace('good', 'bad')] + lines[4:],
                    lines[:-1] + [record.replace('good', 'unreachable'), lines[-1]]]
        for record in ['T\twrong\t' + enc(json.dumps(observation).encode()), 'T\tgood\t%%%',
                       'T\tgood\t' + enc(b'null'), 'T\tgood\t' + enc(b'{broken'),
                       'T\tgood\t' + enc(b'{"format":1,"format":1,"root":{}}'),
                       'T\tgood\t' + enc(b'{"format":NaN,"root":{}}')]:
            variants.append(lines[:2] + [record] + lines[3:])
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(RuntimeError):
                check_results(jobs, '\n'.join(variant), typed=True)
        with self.assertRaises(RuntimeError):
            check_results(jobs, '\n'.join(lines))
        with self.assertRaises(ValueError):
            check_results(jobs, '\n'.join(lines), typed=1)

    def test_invalid_documents_and_offline_dependencies_recover(self):
        schema = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="v" type="xs:int"/></xs:schema>'
        parent = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:include schemaLocation="child.xsd"/></xs:schema>'
        jobs = [SchemaJob('valid', 'https://example.invalid/root.xsd', parent,
                         {'first': b'<v>1</v>', 'bad': b'<v>bad</v>', 'trailing': b'<v>1</v><v>2</v>',
                          'dtd': b'<!DOCTYPE v [<!ENTITY e "1">]><v>&e;</v>', 'last': b'<v>2</v>'}),
                SchemaJob('missing', 'https://missing.invalid/root.xsd', parent, {'unreachable': b'<v>1</v>'})]
        report = run_typed(jobs, {'https://example.invalid/child.xsd': schema})
        for name in ['first', 'last']:
            self.assertTrue(report['documents'][name]['ok'])
            self.assertIsNotNone(report['observations'][name])
        for name in ['bad', 'trailing', 'dtd']:
            self.assertFalse(report['documents'][name]['ok'])
            self.assertIsNone(report['observations'][name])
        self.assertIn('DOCTYPE', report['documents']['dtd']['desc'])
        self.assertIn('resource unavailable offline', report['schemas']['missing']['desc'])
        self.assertIsNone(report['documents']['unreachable']['ok'])
        self.assertIsNone(report['observations']['unreachable'])
        self.assertEqual('2', report['observations']['last']['root']['psvi']['value']['value'])

    def test_depth_namespace_storage_and_fragmented_text(self):
        schema = next(c['schema'].encode() for c in self.cases if c['name'] == 'generic-binding')
        documents = {}
        for depth in (16, 32, 64, 128, MAX_DEPTH):
            start = '<root>' + ''.join(f'<a xmlns:p{i}="urn:{i}">' for i in range(depth - 1))
            end = '</a>' * (depth - 1) + '</root>'
            documents[str(depth)] = (start + 'p0:Part' + end).encode()
        text = ''.join(chr(65 + i % 26) for i in range(8192))
        documents['text'] = ('<root>' + ''.join(f'&#{ord(c)};' for c in text) + '</root>').encode()
        report = run_typed([SchemaJob('resources', 'urn:resources', schema, documents)])
        for depth in (16, 32, 64, 128, MAX_DEPTH):
            observation = report['observations'][str(depth)]
            count = declarations = 0
            pending = [observation['root']]
            while pending:
                node = pending.pop()
                count += 1
                declarations += len(node['namespace_declarations'])
                pending.extend(c for c in node['content'] if isinstance(c, dict))
            self.assertEqual(depth, count)
            self.assertEqual(depth - 1, declarations)
            # Only the root declarations change; copying this path avoids the
            # unrelated recursion limit in Python's generic deepcopy helper.
            equivalent = {**observation, 'root': {**observation['root'],
                'namespace_declarations': {**observation['root']['namespace_declarations'],
                                           'unused': 'urn:unused'}}}
            self.assertTrue(compare(observation, equivalent, order='exact'))
        self.assertEqual([text], report['observations']['text']['root']['content'])
        too_deep = b'<root>' + b'<a>' * MAX_DEPTH + b'</a>' * MAX_DEPTH + b'</root>'
        with self.assertRaisesRegex(RuntimeError, 'depth limit'):
            run_typed([SchemaJob('deep', 'urn:deep', schema, {'deep': too_deep})])

    def test_typed_worker_failure_and_cleanup(self):
        job = self.jobs[0]
        for error in [KeyboardInterrupt(), subprocess.TimeoutExpired('java', 60),
                      subprocess.CalledProcessError(1, 'java', '', 'observer failed')]:
            temporary = []
            def process(command, **kwargs):
                if command[0] == 'javac':
                    temporary.append(Path(command[command.index('-d') + 1]))
                    self.assertIn(str(ROOT / 'oracle' / 'TypedXmlObserver.java'), command)
                    return subprocess.CompletedProcess(command, 0, '', '')
                self.assertIn('--typed', command)
                raise error
            with patch.object(independent.subprocess, 'run', side_effect=process), self.assertRaises(type(error)):
                run_typed([job])
            self.assertEqual(1, len(temporary))
            self.assertFalse(temporary[0].exists())


if __name__ == '__main__':
    unittest.main()
