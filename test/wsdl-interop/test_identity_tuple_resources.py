#!/usr/bin/env python3
"""Structural bounds for the actual private WSDL instance-table implementation.

Copyright (C) 2026 Qore Technologies, s.r.o.
The temporary module adds inspection only; it never changes the production API.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROBE = r'''
thread_local int TupleProbeVisits;
public hash<string, int> sub tuple_resource_probe(int depth, bool chain) {
    *XsdIdentityTupleNode previous;
    list<XsdIdentityTupleNode> nodes();
    TupleProbeVisits = 0;
    for (int i = 0; i < depth; ++i) {
        XsdIdentityTupleNode node("", "item");
        if (!chain) {
            node.tables{"{}key"}{string(i)} = node.uniqueHash();
        } else if (!i) {
            for (int j = 0; j < depth; ++j) {
                node.tables{"{}key"}{string(j)} = node.uniqueHash();
            }
        }
        if (previous) {
            node.children += previous;
        }
        node.validate("TEST-IDENTITY");
        nodes += node;
        previous = node;
    }
    int retained = 0;
    foreach XsdIdentityTupleNode node in (nodes) {
        foreach hash<string, string> table in (node.tables.iterator()) {
            retained += table.size();
        }
    }
    return {"entries":previous.tables{"{}key"}.size(), "retained":retained, "visits":TupleProbeVisits};
}
'''
SCRIPT = '''%modern
%requires ./WSDL.qm
foreach int depth in (16, 32, 64, 128) {
    foreach bool chain in (False, True) {
        hash<string, int> result = tuple_resource_probe(depth, chain);
        @assert(result.entries == depth);
        @assert(result.retained == depth);
        if (chain) {
            @assert(result.visits == 0);
        }
        printf("%d %d %d %d %d\\n", depth, chain, result.entries, result.retained, result.visits);
    }
}
'''


class IdentityTupleResourcesTest(unittest.TestCase):
    def test_retention_and_inherited_table_work(self):
        source = (Path(__file__).resolve().parents[2] / 'qlib/WSDL.qm').read_text()
        start = source.index('class XsdIdentityTupleNode {')
        end = source.index('thread_local *XsdIdentityTupleNode IdentityTupleNode;', start)
        implementation = source[start:end]
        # Count each actual tuple-loop body, including any future full-table scan.
        lines = implementation.splitlines(keepends=True)
        loops = 0
        for i, line in enumerate(lines):
            if 'foreach string tuple in (keys ' in line:
                lines[i] += '                    ++TupleProbeVisits;\n'
                loops += 1
        self.assertGreaterEqual(loops, 2)
        instrumented = source[:start] + ''.join(lines) + source[end:]
        close = instrumented.rfind('}')
        instrumented = instrumented[:close] + PROBE + instrumented[close:]
        with tempfile.TemporaryDirectory(prefix='wsdl-tuple-resources-') as directory:
            root = Path(directory)
            (root / 'WSDL.qm').write_text(instrumented)
            (root / 'probe.qr').write_text(SCRIPT)
            result = subprocess.run([os.environ.get('QORE', shutil.which('qore') or 'qore'),
                '-b', '--enable-debug', str(root / 'probe.qr')], capture_output=True,
                text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual('', result.stderr)
        rows = [list(map(int, row.split())) for row in result.stdout.splitlines()]
        self.assertEqual(8, len(rows), result.stdout)
        self.assertEqual([(d, c) for d in (16, 32, 64, 128) for c in (0, 1)],
                         [(row[0], row[1]) for row in rows])
        for depth, chain, entries, retained, visits in rows:
            self.assertEqual(depth, entries)
            self.assertEqual(depth, retained)
            if chain:
                self.assertEqual(0, visits)


if __name__ == '__main__':
    unittest.main()
