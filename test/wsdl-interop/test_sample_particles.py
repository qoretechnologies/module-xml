#!/usr/bin/env python3
"""Validate generated particle examples through both SOAP bindings and directions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS
from test_compositor_context import schema
from test_particle_values import element
import survey


class SampleParticlesTest(unittest.TestCase):
    def test_complete_samples_in_both_bindings(self):
        pair = element('a') + element('b')
        models = {
            'pairs': (schema('<xs:sequence minOccurs="2" maxOccurs="3">' + pair + '</xs:sequence>'),
                      'ababab', [('budget', {'max_elements': 5}, 'abab'),
                                  ('too-small', {'max_elements': 4}, None),
                                  ('too-few', {'max_items': 1}, None)]),
            'optional': (schema('<xs:sequence minOccurs="0" maxOccurs="3">' + pair + '</xs:sequence>'),
                         'ababab', [('empty', {'max_elements': 1}, '')]),
            'choice': (schema('<xs:choice minOccurs="2" maxOccurs="3">' + pair + '</xs:choice>'), 'aaa', []),
            'nested-choice': (schema('<xs:sequence><xs:choice minOccurs="2" maxOccurs="3"><xs:sequence>'
                + pair + '</xs:sequence>' + element('c') + '</xs:choice>' + element('d') + '</xs:sequence>'),
                'abababd', []),
            'nested-counts': (schema('<xs:sequence minOccurs="2" maxOccurs="3">'
                '<xs:element name="a" type="xs:int" minOccurs="2" maxOccurs="2"/>' + element('b')
                + '</xs:sequence>'), 'aabaabaab', []),
            'all': (schema('<xs:all>' + element('b') + '<xs:element name="a" type="xs:int" minOccurs="0"/>'
                '</xs:all>'), 'ba', [('required-only', {'max_elements': 2}, 'b')]),
            'empty': (schema('<xs:sequence/>'), '', []),
        }
        group = '<xs:group name="Pair"><xs:sequence>' + pair + '</xs:sequence></xs:group>'
        source = schema('<xs:sequence><xs:group ref="t:Pair" minOccurs="2" maxOccurs="2"/>'
            + element('c') + '<xs:group ref="t:Pair"/></xs:sequence>')
        source = source.replace('<xs:complexType name="Record">', group + '<xs:complexType name="Record">')
        models['shared'] = source, 'ababcab', []
        cases, expected, compilers = [], {}, {}
        for name, (source, preferred, budgets) in models.items():
            compilers[name] = etree.XMLSchema(etree.fromstring(source.encode()))
            choices = [('default', {}, preferred)] + budgets
            for version in ('11', '12'):
                options = []
                for label, settings, word in choices:
                    for comments in (False, True):
                        opts = dict(settings, comments=comments)
                        options.append(opts)
                        expected[(name + '/' + version, json.dumps(opts, sort_keys=True))] = word
                cases.append({'name': name + '/' + version, 'wsdl': description(version, source),
                    'binding': 'Soap' + version, 'options': options})
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        with tempfile.TemporaryDirectory(prefix='sample-particles-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(cases), encoding='utf-8')
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                str(Path(__file__).with_name('sample-particles.qr')), str(path)],
                capture_output=True, text=True, timeout=180)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual('', process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        identities = [(case['name'], copy, response, opts) for case in cases for copy in (False, True)
                      for response in (False, True) for opts in case['options']]
        self.assertEqual(identities, [(r['case'], r['copy'], r['response'], r['options']) for r in rows])
        documents = {name: {} for name in models}
        rejected = 0
        for index, row in enumerate(rows):
            word = expected[(row['case'], json.dumps(row['options'], sort_keys=True))]
            self.assertEqual('XSD-SAMPLE-ERROR' if word is None else '', row['error'], row)
            if word is None:
                self.assertNotIn('xml', row)
                rejected += 1
                continue
            name, version = row['case'].split('/')
            envelope = etree.fromstring(row['xml'].encode())
            self.assertEqual('{' + survey.SOAP_NAMESPACES[int(version == '12')] + '}Envelope', envelope.tag)
            payload = envelope.find('{*}Body')[0]
            retained = etree.fromstring(row['retained'].encode())
            for label, output in (('soap', payload), ('retained', retained)):
                self.assertEqual('{' + NS + '}' + ('Reply' if row['response'] else 'Submit'), output.tag)
                self.assertEqual(list(word), [child.tag for child in output], row)
                self.assertEqual(['123'] * len(word), [''.join(child.itertext()) for child in output], row)
                self.assertTrue(compilers[name].validate(output), str(compilers[name].error_log))
                documents[name][f'{index}/{label}'] = etree.tostring(output)
            # Independent native value check: occurrence counts and exact integers survive decoding.
            if row['native'] is None:
                self.assertEqual('', word, row)
                native = {}
            else:
                native = {key: value for key, value in row['native'].items() if value is not None}
            self.assertEqual(set(word), set(native), row)
            for letter, count in Counter(word).items():
                self.assertEqual([123] * count, native[letter] if isinstance(native[letter], list)
                                 else [native[letter]], row)
        jobs = [SchemaJob(name, f'http://example.invalid/{name}.xsd', models[name][0].encode(), outputs)
                for name, outputs in documents.items()]
        oracle = run_independent(jobs)
        self.assertEqual(sum(len(outputs) for outputs in documents.values()), len(oracle['documents']))
        for name, result in oracle['documents'].items():
            self.assertTrue(result['ok'], (name, result))
        self.assertEqual(208, len(rows))
        self.assertEqual(32, rejected)
        self.assertEqual(352, len(oracle['documents']))
        print(f'{mode}: {len(rows)} rows; {rejected} required generation errors; '
              f"{len(oracle['documents'])} independently validated outputs", flush=True)


if __name__ == '__main__':
    unittest.main()
