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
- every assertion states its coverage explicitly as covered, routed to a later phase, a recorded gap,
  or not applicable, and each of those carries what it needs: a covered assertion names executable
  cases that exist, a routed one names a later phase, a gap states the capability that is missing;
- every assertion excluded from testing must carry a specification-based rationale, and "the test
  collection did not test it" is explicitly not such a rationale.

A recorded gap is the point of the coverage field. Where a profile requires a capability this
implementation does not provide, the honest entry is a gap, not an exclusion: calling it "not
applicable" would quietly convert a conformance shortfall into an accounting success.
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

    profiles = {}
    for name in ('wsi12', 'wsi20'):
        pinned = json.loads((NORMATIVE / f'{name}-requirements.json').read_text())
        profiles[name] = pinned['requirements']
        if len(profiles[name]) != pinned['requirement_count']:
            fail(problems, f'{name}: {len(profiles[name])} requirements, pinned as '
                           f'{pinned["requirement_count"]}')

    expected = {'w3c-soap12': set(meta['collection']['assertion_ids'])}
    for name in profiles:
        expected[name] = set(profiles[name])
    for source, ids in expected.items():
        seen = [row['id'] for row in rows if row.get('source') == source]
        duplicates = sorted({i for i in seen if seen.count(i) > 1})
        if duplicates:
            fail(problems, f'{source}: duplicate ledger rows: {duplicates}')
        for missing in sorted(ids - set(seen)):
            fail(problems, f'{source} {missing}: published requirement is absent from the ledger')
        for extra in sorted(set(seen) - ids):
            fail(problems, f'{source} {extra}: ledger row is not a published requirement identifier')
    for row in rows:
        if row.get('source') not in expected:
            fail(problems, f'{row.get("id")}: unknown source {row.get("source")!r}')

    for row in rows:
        rid = row['id']
        source = row.get('source')
        if source == 'w3c-soap12':
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
        elif source in profiles:
            pinned = profiles[source].get(rid)
            if pinned is None:
                continue
            for quote in row.get('normative_quotes', []):
                if normalize(quote) not in normalize(pinned['statement']):
                    fail(problems, f'{rid}: quoted requirement is not present verbatim in the pinned '
                                   f'{source} statement: {quote[:70]!r}')
            if not row.get('normative_quotes'):
                fail(problems, f'{rid}: quotes no part of its requirement statement')
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

        coverage = row.get('coverage')
        if coverage not in ('covered', 'routed', 'gap', 'not-applicable'):
            fail(problems, f'{rid}: coverage must be covered, routed, gap or not-applicable')
        if (coverage == 'not-applicable') != (applicability == 'not-applicable'):
            fail(problems, f'{rid}: coverage and applicability disagree about whether it applies')

        tests = row.get('tests', [])
        for entry in tests:
            path, case = entry.get('file'), entry.get('case')
            if path not in inventory:
                fail(problems, f'{rid}: mapped file {path} does not exist')
            elif case not in inventory[path]:
                fail(problems, f'{rid}: {path} has no case {case!r}')
        if coverage == 'covered' and not tests:
            fail(problems, f'{rid}: recorded as covered but names no executable case')
        if coverage == 'routed' and phase == 'P7':
            fail(problems, f'{rid}: routed to a later phase but still recorded against P7')
        if coverage == 'gap' and not (row.get('gap') or '').strip():
            fail(problems, f'{rid}: recorded as a gap without saying what is missing')
        if coverage != 'gap' and row.get('gap'):
            fail(problems, f'{rid}: records a gap but is not marked as one')

    counts = {}
    for row in rows:
        key = row.get('coverage') if row.get('coverage') != 'routed' else f'routed to {row.get("phase")}'
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
