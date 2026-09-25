#!/usr/bin/env python3
"""Independent MIME content defaults, media patterns and WSDL grammar checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from independent import SchemaJob, run
from test_media_types import read
import jvm

ROOT = Path(__file__).resolve().parent
WSDL = 'http://schemas.xmlsoap.org/wsdl/'
MIME = WSDL + 'mime/'
FIXTURES = ROOT / 'regressions/wsdl-mime-content-defaults/cases.json'


def rows():
    return json.loads(FIXTURES.read_text())['cases']


class MimeContentDefaultsTest(unittest.TestCase):
    def test_normative_defaults_and_patterns(self):
        cases = rows()
        self.assertEqual(70, len(cases))
        self.assertEqual(38, sum(row['valid'] for row in cases))
        for row in cases:
            document = ET.fromstring(row['xml'])
            message = document.find(f'{{{WSDL}}}message')
            parts = {node.attrib['name'] for node in message}
            contents = document.findall(f'.//{{{MIME}}}content')
            self.assertEqual(2 * len(row.get('alternatives', [row['media']])), len(contents))
            accepted = True
            for content in contents:
                part = content.get('part')
                if part is None and len(parts) == 1:
                    part = next(iter(parts))
                accepted = accepted and part in parts and read(content.get('type'), pattern=True) is not None
                if row['valid']:
                    self.assertEqual('payload', part)
                    expected = row['expected'] if isinstance(row['expected'], list) else [row['expected']]
                    self.assertIn(content.get('type', '*/*'), expected)
            with self.subTest(case=row['name']):
                self.assertEqual(row['valid'], accepted)

    def test_published_grammar(self):
        # The corrected 2004 schema makes content/@part required for WS-I.
        # General WSDL 1.1 5.3 permits omission with one abstract part, so keep
        # this observable oracle disagreement separate from semantic assessment.
        imports = []
        resources = {}
        sources = []
        core = ROOT / 'regressions/wsdl-grammar'
        data = json.loads((core / 'cases.json').read_text())
        sources.append((core, dict(file=data['schema_file'], sha256=data['schema_sha256'], url=WSDL), WSDL))
        soap = ROOT / 'regressions/wsdl-soap-grammar'
        for source in json.loads((soap / 'cases.json').read_text())['schemas']:
            sources.append((soap, source, WSDL + ('soap12/' if source['file'] == 'soap12.xsd' else 'soap/')))
        http = ROOT / 'regressions/wsdl-http-mime-grammar'
        for source in json.loads((http / 'cases.json').read_text())['schemas']:
            if source['file'] == 'http.xsd':
                sources.append((http, source, WSDL + 'http/'))
        mime = ROOT / 'regressions/wsdl-mime-part-grammar'
        sources.append((mime, json.loads((mime / 'cases.json').read_text())['schema'], MIME))
        for directory, source, namespace in sources:
            content = (directory / source['file']).read_bytes()
            self.assertEqual(source['sha256'], hashlib.sha256(content).hexdigest())
            resources[source['url']] = content
            imports.append(f'<x:import namespace="{namespace}" schemaLocation="{source["url"]}"/>')
        schema = ('<x:schema xmlns:x="http://www.w3.org/2001/XMLSchema">' + ''.join(imports) + '</x:schema>').encode()
        result = run([SchemaJob('mime', 'urn:mime:defaults', schema,
                                {row['name']: row['xml'].encode() for row in rows()})], resources)
        self.assertTrue(result['schemas']['mime']['ok'], result['schemas'])
        self.assertEqual([], result['schemas']['mime']['warnings'])
        for row in rows():
            with self.subTest(case=row['name']):
                actual = result['documents'][row['name']]
                self.assertEqual(row['schema_valid'], actual['ok'], actual)
                self.assertEqual([], actual['warnings'])

    def test_wsdl4j_observations(self):
        oracle = ROOT / 'oracle'
        manifest = json.loads((oracle / 'wsdl4j-manifest.json').read_text())
        for artifact in manifest['artifacts']:
            content = (oracle / artifact['path']).read_bytes()
            self.assertEqual(artifact['sha256'], hashlib.sha256(content).hexdigest())
        with tempfile.TemporaryDirectory(prefix='wsdl-mime-defaults-') as directory:
            jar = oracle / 'wsdl4j-1.6.3.jar'
            compiled = subprocess.run(['javac', '-Xlint:all', '-Werror', '-cp', str(jar), '-d', directory,
                                       str(oracle / 'WsdlMimePartsOracle.java')], capture_output=True,
                                      text=True, timeout=60, check=True, env=jvm.environment())
            self.assertEqual('', compiled.stdout + compiled.stderr)
            path = Path(directory) / 'contract.wsdl'
            for row in rows():
                if not row['valid']:
                    continue
                with self.subTest(case=row['name']):
                    path.write_text(row['xml'])
                    result = subprocess.run(['java', '-cp', directory + os.pathsep + str(jar),
                                             'WsdlMimePartsOracle', str(path)], capture_output=True,
                                            text=True, timeout=30, check=True, env=jvm.environment())
                    self.assertEqual('', result.stderr)
                    observed = [line.split('\t') for line in result.stdout.splitlines()]
                    contents = [fields for fields in observed if fields[1] == 'CONTENT']
                    self.assertEqual([[direction, 'CONTENT', 'null' if row['single'] else 'payload',
                                       'null' if media is None else media]
                                      for direction in ('input', 'output')
                                      for media in row.get('alternatives', [row['media']])], contents)


if __name__ == '__main__':
    unittest.main()
