#!/usr/bin/env python3
"""Verify the SOAP assertion ledger against the pinned specifications and the real test suite.

Copyright (C) 2026 Qore Technologies, s.r.o.

The ledger records, for every assertion identifier published in the W3C SOAP 1.2 test collection,
what the *current* normative text requires, whether the requirement applies to this implementation,
and which executable cases cover it. This script is what stops that ledger from drifting into prose:

- the pinned specification texts must match their recorded digests;
- every assertion identifier must appear exactly once, with no extras;
- every quoted requirement must still appear verbatim in the section it cites, so a quote cannot be
  paraphrased, invented, or left behind when the source changes;
- every applicable assertion routed to this phase must name at least one executable case, and every
  named case must actually exist in the suite;
- every assertion excluded from testing must carry a specification-based rationale, and "the test
  collection did not test it" is explicitly not such a rationale.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soap_sections

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NORMATIVE = HERE / 'normative'
LEDGER = HERE / 'assertion-ledger.json'

# Phrases that describe the old test collection's coverage rather than the specification. An
# assertion may only be excluded on what the specification says, never on what the collection did.
COLLECTION_EXCUSES = (
    'will not be tested',
    'not tested separately',
    'the collection does not test',
    'the test collection did not test',
)


def fail(problems, message):
    problems.append(message)


def check_sources(problems):
    meta = json.loads((NORMATIVE / 'sources.json').read_text())
    sections = {}
    for name, info in meta['documents'].items():
        path = NORMATIVE / f'{name}.html'
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != info['html_sha256']:
            fail(problems, f'{path.name}: digest {digest} does not match the pinned '
                           f'{info["html_sha256"]}')
        if len(data) != info['html_bytes']:
            fail(problems, f'{path.name}: {len(data)} bytes, pinned as {info["html_bytes"]}')
        sections[name] = soap_sections.load(name)
    return meta, sections


normalize = soap_sections.normalize


def build_inventory():
    """Every executable case name in the suite, so a mapping cannot name one that does not exist."""
    inventory = {}
    for path in sorted(ROOT.glob('test/*.qtest')):
        names = re.findall(r'addTestCase\(\s*"((?:[^"\\]|\\.)*)"', path.read_text())
        inventory[str(path.relative_to(ROOT))] = set(names)
    for path in sorted(ROOT.glob('test/wsdl-interop/test_*.py')):
        names = re.findall(r'(?m)^\s*def (test_[A-Za-z0-9_]+)\s*\(', path.read_text())
        inventory[str(path.relative_to(ROOT))] = set(names)
    return inventory


def main():
    problems = []
    meta, sections = check_sources(problems)
    ledger = json.loads(LEDGER.read_text())
    rows = ledger['assertions']
    inventory = build_inventory()

    expected_ids = meta['collection']['assertion_ids']
    seen = [row['id'] for row in rows]
    duplicates = sorted({i for i in seen if seen.count(i) > 1})
    if duplicates:
        fail(problems, f'duplicate ledger rows: {duplicates}')
    for missing in sorted(set(expected_ids) - set(seen)):
        fail(problems, f'{missing}: published assertion is absent from the ledger')
    for extra in sorted(set(seen) - set(expected_ids)):
        fail(problems, f'{extra}: ledger row is not a published assertion identifier')

    for row in rows:
        rid = row['id']
        part, number = row.get('part'), row.get('section')
        found = sections.get(f'soap12-{part}', {}).get(number)
        if found is None:
            fail(problems, f'{rid}: section {part} {number} has no heading in the pinned document')
        else:
            haystack = found['text']
            for quote in row.get('normative_quotes', []):
                if normalize(quote) not in haystack:
                    fail(problems, f'{rid}: quoted requirement is not present verbatim in '
                                   f'{part} section {number}: {quote[:70]!r}')
        if (not row.get('normative_quotes') and row.get('applicability') == 'applicable'
                and row.get('phase') == 'P7'):
            # A later phase revalidates its own rows against the current text when it covers them;
            # this phase only claims the rows it is accounting for now.
            fail(problems, f'{rid}: applicable P7 assertion quotes no requirement')

        applicability = row.get('applicability')
        if applicability not in ('applicable', 'not-applicable'):
            fail(problems, f'{rid}: applicability must be applicable or not-applicable')
        rationale = (row.get('rationale') or '').strip()
        if not rationale:
            fail(problems, f'{rid}: no rationale recorded')
        if applicability == 'not-applicable':
            lowered = rationale.lower()
            for excuse in COLLECTION_EXCUSES:
                if excuse in lowered:
                    fail(problems, f'{rid}: excluded on the old collection\'s coverage rather than '
                                   f'on the specification')
        phase = row.get('phase')
        if phase not in ('P7', 'P8', 'P9'):
            fail(problems, f'{rid}: phase must be P7, P8 or P9')

        tests = row.get('tests', [])
        for entry in tests:
            path, case = entry.get('file'), entry.get('case')
            if path not in inventory:
                fail(problems, f'{rid}: mapped file {path} does not exist')
            elif case not in inventory[path]:
                fail(problems, f'{rid}: {path} has no case {case!r}')
        if applicability == 'applicable' and phase == 'P7' and not tests:
            fail(problems, f'{rid}: applicable P7 assertion has no executable case')

    counts = {}
    for row in rows:
        key = f'{row.get("phase")}/{row.get("applicability")}'
        counts[key] = counts.get(key, 0) + 1
    print(f'ledger rows: {len(rows)}')
    for key in sorted(counts):
        print(f'  {key}: {counts[key]}')
    mapped = sum(len(row.get('tests', [])) for row in rows)
    print(f'executable mappings: {mapped}')

    if problems:
        print(f'\nFAILED: {len(problems)} problem(s)')
        for problem in problems[:40]:
            print(f'  - {problem}')
        if len(problems) > 40:
            print(f'  ... and {len(problems) - 40} more')
        return 1
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
