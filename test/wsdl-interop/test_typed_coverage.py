#!/usr/bin/env python3
"""Complete typed accounting, strict selection and schema-valid loss regressions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import corpus
import coverage
import survey
from independent import SchemaJob, run_typed

ROOT = Path(__file__).resolve().parent
SUPPORTING = {'AttributeDefault', 'AttributeFixed', 'ElementDefault', 'ElementFixed',
              'GlobalElementDefault', 'NillableElement', 'NillableOptionalElement',
              'NotNillableElement', 'NotMixed', 'MixedComplexContent', 'ExtendedSequenceLaxAny',
              'ExtendedSequenceSkipAny', 'GlobalComplexTypeAbstract'}


class TypedCoverageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='wsdl-typed-coverage-')
        cls.addClassCleanup(temporary.cleanup)
        extracted = corpus.extract(Path(temporary.name) / 'complete')
        cls.root = Path(temporary.name) / 'cases'
        cls.root.mkdir()
        names = {'BooleanElement', 'AnyTypeElement', 'NillableOptionalElement',
                 'GlobalElementAbstract', 'TypeSubstitutionUsingXsiType'}
        for name in names:
            shutil.copytree(extracted / name, cls.root / name)
        cls.source = corpus.read_manifest(ROOT / 'adjudication-report.json')
        cls.source['cases'] = [c for c in cls.source['cases'] if c['case'] in names]
        cls.selection = corpus.read_manifest(ROOT / 'p5-selection.json')
        cls.selection['cases'] = {k: v for k, v in cls.selection['cases'].items() if k in names}
        cls.cases, _ = coverage.prepare(cls.root, cls.source)
        cls.rows = survey.run_worker(cls.cases, {}, preserve_types=True)

    def assess(self, rows=None, selection=None):
        with patch.object(survey, 'run_worker', return_value=deepcopy(self.rows if rows is None else rows)):
            return coverage.assess(self.root, self.source, self.selection if selection is None else selection,
                                   corpus.Catalog(), preserve_types=True)

    def test_complete_native_accounting(self):
        report = self.assess()
        self.assertEqual([], report['failures'])
        self.assertEqual([], report['selected_failures'])
        expected = {'ok': 44, 'failed': 0, 'unreachable': 0, 'unassessed': 0, 'missing': 0, 'skipped': 0}
        for name in ('values', 'typed_values'):
            self.assertEqual(expected, report['stage_accounting']['counts'][name])
        for case in report['cases']:
            for message in case['messages']:
                self.assertTrue(message['input_xerces']['ok'])
                self.assertEqual('per-name' if case['case'] == 'BooleanElement' else 'exact',
                                 message['typed_values']['order'])
                self.assertEqual({'input', 'output'}, set(message['typed_values']['observation_sha256']))
        self.assertEqual(1, report['scope']['typed_values']['format'])
        for field in ('typed_reference_sha256', 'typed_observer_sha256'):
            self.assertRegex(report['versions'][field], r'^[0-9a-f]{64}$')

    def test_schema_valid_changes_cannot_pass_with_or_without_leaf_assertions(self):
        for name, before, after in [('AnyTypeElement', '>cheese<', '>changed<'),
                                    ('BooleanElement', '>false<', '>true<')]:
            rows = deepcopy(self.rows)
            changed = next(r for r in rows if r['case'] == name and r['stage'] == 'serialize' and before in r['body'])
            changed['body'] = changed['body'].replace(before, after)
            report = self.assess(rows)
            messages = [m for c in report['cases'] for m in c['messages'] if m['failures']]
            with self.subTest(case=name):
                self.assertEqual(1, len(messages))
                row = messages[0]
                self.assertTrue(row['output_xerces']['ok'])
                self.assertTrue(row['output_lxml']['ok'])
                self.assertFalse(row['typed_values']['ok'])
                self.assertFalse(row['values']['ok'])
                self.assertEqual(['value_preservation'], row['failures'])
                self.assertEqual(1, len(report['selected_failures']))
                self.assertEqual(1, report['stage_accounting']['counts']['typed_values']['failed'])

    def test_missing_and_malformed_observations_never_count_as_success(self):
        original = coverage.run_typed
        for stage in ('input', 'output', 'malformed'):
            def altered(jobs, resources):
                result = original(jobs, resources)
                key = next(k for k in result['observations'] if k.endswith('/input') == (stage == 'input'))
                if stage == 'malformed':
                    result['observations'][key]['format'] = 0
                else:
                    del result['observations'][key]
                return result
            with self.subTest(stage=stage), patch.object(coverage, 'run_typed', side_effect=altered):
                if stage == 'malformed':
                    with self.assertRaisesRegex(ValueError, 'unsupported typed observation'):
                        self.assess()
                    continue
                report = self.assess()
                rows = [m for c in report['cases'] for m in c['messages']
                        if 'typed_reference_unavailable' in m['failures']]
                self.assertEqual(1, len(rows))
                self.assertIsNone(rows[0]['typed_values']['ok'])
                self.assertEqual(1, report['stage_accounting']['counts']['typed_values']['unassessed'])
                self.assertEqual(1, len(report['selected_failures']))

    def test_unavailable_assessment_and_explicit_order_contract(self):
        case = next(c for c in json.loads((ROOT / 'fixtures/typed-observations.json').read_text())
                    if c['name'] == 'all-order')
        reference = run_typed([SchemaJob('order', 'urn:order', case['schema'].encode(),
            {'pair/input': case['left'].encode(), 'pair': case['right'].encode()})])
        self.assertTrue(coverage.typed_value_checks(reference, 'pair', 'per-name')['ok'])
        self.assertFalse(coverage.typed_value_checks(reference, 'pair', 'exact')['ok'])
        for key in ('pair', 'pair/input'):
            unavailable = deepcopy(reference)
            unavailable['observations'][key] = None
            self.assertIsNone(coverage.typed_value_checks(unavailable, 'pair', 'exact')['ok'])

    def test_typed_selection_validation(self):
        _, records = coverage.prepare(self.root, self.source)
        for assertion in [{'datatype': 'typed', 'order': 'ignored'}, {'datatype': 'typed'},
                          {'datatype': 'typed', 'order': 'exact', 'extra': False}]:
            selection = deepcopy(self.selection)
            file = next(iter(selection['cases']['AnyTypeElement']['messages']))
            selection['cases']['AnyTypeElement']['messages'][file] = [assertion]
            with self.subTest(assertion=assertion), self.assertRaises(ValueError):
                coverage.validate_selection(selection, records)
        selection = deepcopy(self.selection)
        file = next(iter(selection['cases']['AnyTypeElement']['messages']))
        selection['cases']['AnyTypeElement']['messages'][file] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate typed'):
            coverage.validate_selection(selection, records)

    def test_legacy_projection_losses_remain_failures(self):
        report = coverage.assess(self.root, self.source, self.selection, corpus.Catalog())
        self.assertEqual(12, len(report['failures']))
        self.assertEqual(12, len(report['selected_failures']))
        self.assertEqual({'ok': 32, 'failed': 8, 'unreachable': 4, 'unassessed': 0, 'missing': 0, 'skipped': 0},
                         report['stage_accounting']['counts']['typed_values'])
        for case in report['cases']:
            for message in case['messages']:
                if message['failures']:
                    self.assertEqual(['serialize'] if case['case'] == 'TypeSubstitutionUsingXsiType'
                                     else ['value_preservation'], message['failures'])

    def test_p5_selection_preserves_existing_assertions_and_covers_requirement_families(self):
        source = corpus.read_manifest(ROOT / 'adjudication-report.json')
        selection = corpus.read_manifest(ROOT / 'p5-selection.json')
        baseline = corpus.read_manifest(ROOT / 'strict-selection.json')
        records = {c['case']: c for c in source['cases']}
        coverage.validate_selection(selection, records)
        required = {name for name, c in records.items() if c['implementation_phase'] == 'P5'} | SUPPORTING
        self.assertEqual(34, len(required))
        self.assertEqual(172, len(selection['cases']))
        self.assertEqual(set(baseline['cases']) | required, set(selection['cases']))
        self.assertEqual(1564, 2 * sum(len(c.get('messages', {})) for c in selection['cases'].values()))
        for name, entry in baseline['cases'].items():
            for file, assertions in entry.get('messages', {}).items():
                self.assertEqual(assertions, [a for a in selection['cases'][name]['messages'][file]
                                              if a.get('datatype') != 'typed'])
        for name in required:
            record, entry = records[name], selection['cases'][name]
            if not record['source_decision']['valid']:
                self.assertIn('parse_error', entry)
                continue
            self.assertEqual(set(record['messages']), set(entry['messages']))
            for file, message in record['messages'].items():
                typed = [a for a in entry['messages'][file] if a.get('datatype') == 'typed']
                self.assertEqual([{'datatype': 'typed', 'order': 'exact'}] if message['decision']['valid'] else [], typed)


if __name__ == '__main__':
    unittest.main()
