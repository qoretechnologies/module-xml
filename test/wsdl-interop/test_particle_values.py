#!/usr/bin/env python3
"""Independent ordered-value checks through actual SOAP bindings in both directions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from collections import defaultdict

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS
from test_compositor_context import schema
import survey


def element(name):
    return f'<xs:element name="{name}" type="xs:int"/>'


class ParticleValuesTest(unittest.TestCase):
    def test_ordered_values_original_and_reconstructed_both_bindings(self):
        models = {
            "repeated-sequence": ('<xs:sequence minOccurs="0" maxOccurs="2">' + element('a') + element('b')
                + '</xs:sequence>', ['', 'ab', 'abab'], ['a', 'b', 'ba', 'aabb', 'aba', 'ababab'], ['a', 'b']),
            "repeated-choice": ('<xs:choice minOccurs="2" maxOccurs="3">' + element('a') + element('b')
                + '</xs:choice>', ['aa', 'ab', 'ba', 'aba', 'bab'], ['', 'a', 'abab', 'ac'], []),
            "nested-choice": ('<xs:sequence><xs:choice minOccurs="2" maxOccurs="3"><xs:sequence>'
                + element('a') + element('b') + '</xs:sequence>' + element('c') + '</xs:choice>'
                + element('d') + '</xs:sequence>', ['cabd', 'abccd', 'cccd'], ['cd', 'acbd', 'abcccd', 'cab'], ['d']),
            "all": ('<xs:all minOccurs="0">' + element('a') + element('b') + '</xs:all>',
                ['', 'ab', 'ba'], ['a', 'b', 'aba'], ['a', 'b']),
        }
        cases, expected, jobs, compilers = [], {}, [], {}
        for name, (model, valid_words, invalid_words, absent_fields) in models.items():
            source = schema(model)
            compiled = etree.XMLSchema(etree.fromstring(source.encode()))
            compilers[name] = compiled
            documents = {}
            for version, envelope_ns in zip(('11', '12'), survey.SOAP_NAMESPACES):
                case = {'name': name + '/' + version, 'wsdl': description(version, source),
                        'binding': 'Soap' + version, 'messages': []}
                for valid, words in ((True, valid_words), (False, invalid_words)):
                    for word in words:
                        content = ''.join(f'<{ch}>{index:03}</{ch}>' for index, ch in enumerate(word, 1))
                        for response, wrapper in ((False, 'Submit'), (True, 'Reply')):
                            label = ('response/' if response else 'request/') + (word or 'empty')
                            payload = f'<t:{wrapper} xmlns:t="{NS}">{content}</t:{wrapper}>'
                            parsed = etree.fromstring(payload.encode())
                            self.assertEqual(valid, compiled.validate(parsed), (case['name'], label, str(compiled.error_log)))
                            document_key = case['name'] + '/' + label
                            documents[document_key] = payload.encode()
                            native = {field: None for field in absent_fields}
                            values = {}
                            for index, ch in enumerate(word, 1):
                                values.setdefault(ch, []).append(index)
                            native.update({ch: items[0] if len(items) == 1 else items for ch, items in values.items()})
                            expected[(case['name'], label)] = (valid, native, parsed, envelope_ns)
                            case['messages'].append({'name': label, 'response': response, 'payload': payload,
                                'envelope': f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{payload}</s:Body></s:Envelope>'})
                cases.append(case)
            jobs.append(SchemaJob(name, f'http://example.invalid/{name}.xsd', source.encode(), documents))
        oracle = run_independent(jobs)
        self.assertEqual(len(expected), len(oracle['documents']))
        for (case, label), (valid, _, _, _) in expected.items():
            self.assertEqual(valid, oracle['documents'][case + '/' + label]['ok'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        with tempfile.TemporaryDirectory(prefix='particle-values-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(cases), encoding='utf-8')
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                str(Path(__file__).with_name('particle-values.qr')), str(path)],
                text=True, capture_output=True, timeout=120)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual('', process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        wanted = [(case['name'], copy, message['name']) for case in cases for copy in (False, True)
                  for message in case['messages']]
        self.assertEqual(wanted, [(row['case'], row['copy'], row['message']) for row in rows])
        outputs = {name: {} for name in models}
        for row in rows:
            valid, native, before, envelope_ns = expected[(row['case'], row['message'])]
            if not valid:
                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['decode_error'], row)
                self.assertEqual('SOAP-SERIALIZATION-ERROR', row['encode_error'], row)
                self.assertFalse(row['native_attempted'], row)
                continue
            self.assertEqual('', row['decode_error'], row)
            self.assertEqual('', row['encode_error'], row)
            self.assertEqual(native, row['native'], row)
            envelope = etree.fromstring(row['xml'].encode())
            self.assertEqual('{' + envelope_ns + '}Envelope', envelope.tag)
            after = envelope.find('{*}Body')[0]
            retained = etree.fromstring(row['retained'].encode())
            for value in (after, retained):
                self.assertEqual(before.tag, value.tag)
                self.assertEqual([(child.tag, child.text) for child in before],
                                 [(child.tag, child.text) for child in value])
            name = row['case'].split('/')[0]
            self.assertTrue(compilers[name].validate(after), str(compilers[name].error_log))
            outputs[name][f"{row['case']}/{row['copy']}/{row['message']}"] = etree.tostring(after)
            self.assertTrue(row['native_attempted'], row)
            self.assertEqual('', row['native_error'], row)
            native_envelope = etree.fromstring(row['native_xml'].encode())
            self.assertEqual('{' + envelope_ns + '}Envelope', native_envelope.tag)
            native_payload = native_envelope.find('{*}Body')[0]
            self.assertEqual(before.tag, native_payload.tag)
            self.assertTrue(compilers[name].validate(native_payload), str(compilers[name].error_log))
            values_before, values_after = defaultdict(list), defaultdict(list)
            for child in before:
                values_before[child.tag].append(int(child.text))
            for child in native_payload:
                values_after[child.tag].append(int(child.text))
            self.assertEqual(dict(values_before), dict(values_after), row)
            outputs[name][f"{row['case']}/{row['copy']}/{row['message']}/native"] = etree.tostring(native_payload)
        emitted_jobs = [SchemaJob(job.name, job.uri, job.schema, outputs[job.name]) for job in jobs]
        emitted = run_independent(emitted_jobs)
        self.assertEqual(sum(len(value) for value in outputs.values()), len(emitted['documents']))
        for key, result in emitted['documents'].items():
            self.assertTrue(result['ok'], (key, result))
        print(f'{mode}: {len(rows)} rows; {len(expected)} independent input verdicts; '
              f"{len(emitted['documents'])} independently validated outputs", flush=True)


if __name__ == '__main__':
    unittest.main()
