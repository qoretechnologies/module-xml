"""Independent ordinal/Fraction cases for native calendar ownership and values.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import random
import sys

# This generator uses only the standard-library references, not a schema engine.
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'test/wsdl-interop'))
from calendar_reference import value as calendar_value
from temporal_reference import value as temporal_value


def value(builtin, lexical):
    return (temporal_value if builtin in ('time', 'dateTime') else calendar_value)(builtin, lexical)


def cases():
    rows = []

    def add(builtin, lexical, peer=None, canonical=None):
        row = dict(builtin=builtin, lexical=lexical, peer=peer, canonical=canonical)
        try:
            actual = value(builtin, lexical)
        except ValueError:
            row['valid'] = False
        else:
            row['valid'] = True
            if peer is not None:
                try:
                    other = value(builtin, peer)
                except ValueError:
                    row['comparison'] = 99
                else:
                    relation = actual.compare(other)
                    row['comparison'] = 2 if relation is None else relation
        rows.append(row)

    for row in json.loads((REPO / 'test/wsdl-interop/fixtures/calendar-constraint-boundaries.json').read_text()):
        add(row['builtin'], row['source'], row['canonical'], row['canonical'])
    samples = {'dateTime':'2000-01-01T00:00:00', 'time':'00:00:00', 'date':'2000-01-01',
               'gYear':'2000', 'gYearMonth':'2000-01', 'gMonth':'--01', 'gMonthDay':'--01-01', 'gDay':'---01'}
    for builtin, sample in samples.items():
        for zone in ('', 'Z', '-00:00', '+00:01', '-00:01', '+14:00', '-14:00', '+14:01', '-14:01',
                     '+00:60', '+15:00', 'z', 'Ztail', '\u00a0'):
            add(builtin, sample + zone, sample)
        for text in ('', ' ', 'junk', sample + ' ' + sample):
            add(builtin, text)
    for builtin, text in [('date','0000-01-01'), ('date','-0000-01-01'), ('date','02000-01-01'),
                          ('date','-0001-02-29'), ('date','1900-02-29'), ('time','24:00:00.0001'),
                          ('time','23:59:61'), ('time','01:00:00.'), ('gMonth','--01--')]:
        add(builtin, text)
    for builtin, prefix in [('time',''), ('dateTime','2000-03-31T'), ('dateTime','2000-04-01T')]:
        for clock in ('00:11:60.56', '09:39:60.22', '23:59:60.1234567890123456789'):
            for zone in ('+14:00', '-14:00'):
                add(builtin, prefix + clock, prefix + clock + zone)
                add(builtin, prefix + clock + zone, prefix + clock)
    rng = random.Random(20260913)
    for builtin in samples:
        for _ in range(1200):
            year = rng.choice(['0001','-0001','1900','2000','-0400','10000','9'*1000,'-1'+'0'*1000])
            month, day = rng.randint(1,12), rng.randint(1,31)
            seconds = rng.choice(['00','59','60','61']) + '.' + ''.join(
                str(rng.randrange(10)) for _ in range(rng.choice([1,2,19,200])))
            clock = f'{rng.randint(0,24):02}:{rng.randint(0,59):02}:{seconds}'
            date = f'{year}-{month:02}-{day:02}'
            lexical = {'dateTime':date+'T'+clock, 'time':clock, 'date':date, 'gYear':year,
                       'gYearMonth':f'{year}-{month:02}', 'gMonth':f'--{month:02}',
                       'gMonthDay':f'--{month:02}-{day:02}', 'gDay':f'---{day:02}'}[builtin]
            zone = rng.choice(['','Z','+14:00','-14:00','+00:00','-00:00','+14:01','+01:00','-01:00'])
            add(builtin, lexical + zone, lexical + rng.choice(['','Z','+14:00','-14:00','+00:01','-00:01']))
    return rows


def wire(rows):
    return ''.join(row['builtin'] + '\t' + row['lexical'] +
                   ('' if row['peer'] is None else '\t' + row['peer']) + '\n' for row in rows)


def check(rows, output):
    records = output.splitlines()
    assert len(rows) == len(records), (len(rows), len(records))
    for index, (row, record) in enumerate(zip(rows, records, strict=True)):
        lexical, formatted, comparison, canonical = record.split('\t')
        assert (int(lexical) == 0) == row['valid'], (index, row, record)
        if not row['valid']:
            assert int(lexical) > 0, (index, row, record)
        if row['valid']:
            assert formatted == '0', (index, row, record)
            assert value(row['builtin'], row['lexical']) == value(row['builtin'], canonical), (index, row, record)
            if row['canonical'] is not None:
                assert row['canonical'] == canonical, (index, row, record)
            if row['peer'] is not None:
                assert row['comparison'] == int(comparison), (index, row, record)
