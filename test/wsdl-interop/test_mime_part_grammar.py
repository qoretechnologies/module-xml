#!/usr/bin/env python3
"""MIME multipart grammar and independently observed SOAP header/body metadata.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from independent import SchemaJob, run
import jvm

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'regressions/wsdl-mime-part-grammar'
WSDL = 'http://schemas.xmlsoap.org/wsdl/'


def manifest():
    return json.loads((FIXTURES / 'cases.json').read_text())


def normalized(value):
    # WSDL4J exposes some raw attribute/list spellings. XSD collapse uses exactly
    # XML space, tab, CR and LF; normalization here is separate from native code.
    text = base64.b64decode(value).decode().replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')
    return ' '.join(token for token in text.split(' ') if token)


class MimePartGrammarTest(unittest.TestCase):
    def test_corrected_grammar(self):
        data = manifest()
        rows = data['cases']
        self.assertEqual(118, len(rows))
        self.assertEqual(38, sum(row['valid'] for row in rows))
        self.assertEqual(2, len(data['metadata_cases']))
        rows += [dict(row, valid=True, schema_valid=True) for row in data['metadata_cases']]
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        resources = {'urn:mime:vendor': data['vendor_schema'].encode()}
        imports = ['<x:import namespace="urn:vendor" schemaLocation="urn:mime:vendor"/>']
        core = ROOT / 'regressions/wsdl-grammar'
        core_manifest = json.loads((core / 'cases.json').read_text())
        content = (core / core_manifest['schema_file']).read_bytes()
        self.assertEqual(core_manifest['schema_sha256'], hashlib.sha256(content).hexdigest())
        resources[WSDL] = content
        imports.append(f'<x:import namespace="{WSDL}" schemaLocation="{WSDL}"/>')
        soap = ROOT / 'regressions/wsdl-soap-grammar'
        for source in json.loads((soap / 'cases.json').read_text())['schemas']:
            content = (soap / source['file']).read_bytes()
            self.assertEqual(source['sha256'], hashlib.sha256(content).hexdigest())
            resources[source['url']] = content
            ns = WSDL + ('soap12/' if source['file'] == 'soap12.xsd' else 'soap/')
            imports.append(f'<x:import namespace="{ns}" schemaLocation="{source["url"]}"/>')
        source = data['schema']
        content = (FIXTURES / source['file']).read_bytes()
        self.assertEqual(source['sha256'], hashlib.sha256(content).hexdigest())
        self.assertEqual(source['size'], len(content))
        resources[source['url']] = content
        imports.append(f'<x:import namespace="{WSDL}mime/" schemaLocation="{source["url"]}"/>')
        schema = ('<x:schema xmlns:x="http://www.w3.org/2001/XMLSchema">' + ''.join(imports) + '</x:schema>').encode()
        report = run([SchemaJob('mime', 'urn:mime:grammar', schema,
                               {row['name']: row['xml'].encode() for row in rows})], resources)
        self.assertTrue(report['schemas']['mime']['ok'], report['schemas'])
        self.assertEqual([], report['schemas']['mime']['warnings'])
        for row in rows:
            with self.subTest(case=row['name']):
                result = report['documents'][row['name']]
                self.assertEqual(row['schema_valid'], result['ok'], result)
                self.assertEqual([], result['warnings'])
                self.assertEqual(row['valid'] != row['schema_valid'], bool(row.get('adjudication')))

    def test_wsdl4j_nested_metadata(self):
        oracle = ROOT / 'oracle'
        pinned = json.loads((oracle / 'wsdl4j-manifest.json').read_text())
        self.assertEqual(('WSDL4J', '1.6.3'), (pinned['implementation'], pinned['version']))
        for artifact in pinned['artifacts']:
            content = (oracle / artifact['path']).read_bytes()
            self.assertEqual(artifact['sha256'], hashlib.sha256(content).hexdigest())
            self.assertEqual(artifact['size'], len(content))
        with tempfile.TemporaryDirectory(prefix='wsdl-mime-parts-oracle-') as directory:
            jar = oracle / 'wsdl4j-1.6.3.jar'
            compiled = subprocess.run(['javac', '-Xlint:all', '-Werror', '-cp', str(jar), '-d', directory,
                                       str(oracle / 'WsdlMimePartsOracle.java')], capture_output=True,
                                      text=True, timeout=60, check=True, env=jvm.environment())
            self.assertEqual('', compiled.stdout + compiled.stderr)
            path = Path(directory) / 'contract.wsdl'
            for row in manifest()['cases']:
                if not row['valid']:
                    continue
                with self.subTest(case=row['name']):
                    path.write_text(row['xml'])
                    result = subprocess.run(['java', '-cp', directory + os.pathsep + str(jar),
                                             'WsdlMimePartsOracle', str(path)], capture_output=True,
                                            text=True, timeout=30, check=True, env=jvm.environment())
                    self.assertEqual('', result.stderr)
                    observations = [line.split('\t') for line in result.stdout.splitlines()]
                    self.assertEqual(6, len(observations), observations)
                    for index, direction in enumerate(('input', 'output')):
                        multipart, body, header = observations[index * 3:index * 3 + 3]
                        self.assertEqual([direction, 'MULTIPART', '1'], multipart)
                        self.assertEqual([direction, 'BODY', '{' + WSDL
                                          + ('soap12/' if row['soap12'] else 'soap/') + '}body', 'literal'], body[:4])
                        self.assertEqual(['urn:body-hint', 'urn:format-hint', 'body'],
                                         [normalized(value) for value in body[4:]])
                        self.assertEqual([direction, 'HEADER', '{urn:mime-grammar}H'], header[:3])
                        self.assertEqual('token', normalized(header[3]))
                        self.assertEqual(str(row['headerfaults']), header[4])
            for row in manifest()['metadata_cases']:
                with self.subTest(case=row['name']):
                    path.write_text(row['xml'])
                    result = subprocess.run(['java', '-cp', directory + os.pathsep + str(jar),
                                             'WsdlMimePartsOracle', str(path)], capture_output=True,
                                            text=True, timeout=30, check=True, env=jvm.environment())
                    self.assertEqual('', result.stderr)
                    observations = [line.split('\t') for line in result.stdout.splitlines()]
                    self.assertEqual(14, len(observations), observations)
                    for index, direction in enumerate(('input', 'output')):
                        self.assertEqual([direction, 'MULTIPART', '3'], observations[index * 7])
                        self.assertEqual([[direction, 'CONTENT', part, mime]
                                          for part in ('first', 'second')
                                          for mime in ('application/octet-stream', 'application/pdf')],
                                         observations[index * 7 + 3:index * 7 + 7])


if __name__ == '__main__':
    unittest.main()
