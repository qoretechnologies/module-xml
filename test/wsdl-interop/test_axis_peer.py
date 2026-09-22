#!/usr/bin/env python3
"""Pinned Apache Axis 1.4 rpc/encoded peer and the independent encoded-message corpora.

Copyright (C) 2026 Qore Technologies, s.r.o.

Verifies every pinned artifact, builds the SOAPBuilders round 2 interop client and service from the
pinned Axis sources, runs Axis's own client against Axis's own implementation, and compares the
captured exchanges with the committed corpus in canonical form. Java 17 or later is required.
"""
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from lxml import etree

import encoded_corpus
from test_cxf_peer import endpoint

ROOT = Path(__file__).resolve().parent
PEER = ROOT / 'axis-peer'
CORPUS = ROOT / 'encoded-corpus' / 'axis-round2.json'
XSD_DATETIME = '{http://www.w3.org/2001/XMLSchema}dateTime'
CLIENT_CONFIG = '''<deployment xmlns="http://xml.apache.org/axis/wsdd/" xmlns:java="http://xml.apache.org/axis/wsdd/providers/java">
 <globalConfiguration>
  <parameter name="disablePrettyXML" value="true"/>
  <parameter name="enableNamespacePrefixOptimization" value="false"/>
  <responseFlow><handler type="java:AxisPeer$RecordingHandler"/></responseFlow>
 </globalConfiguration>
 <transport name="http" pivot="java:org.apache.axis.transport.http.HTTPSender"/>
</deployment>
'''


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classpath(extra):
    return os.pathsep.join(sorted(glob.glob(str(PEER / 'jars' / '*.jar'))) + [str(extra)])


class AxisPeer:
    """Builds the peer once per test class in an owned temporary directory."""

    def __init__(self, work):
        self.work = Path(work)
        generated = self.work / 'generated'
        self.classes = self.work / 'classes'
        self.classes.mkdir()
        # The same options as the Axis 1.4 samples/echo build (contracts/build.xml): client-side classes
        # with type mapping version 1.1 and both interop namespaces mapped to samples.echo.
        subprocess.run(['java', '-cp', classpath(self.classes), 'org.apache.axis.wsdl.WSDL2Java', '-o', str(generated),
                        '-T', '1.1', '-Nhttp://soapinterop.org/=samples.echo', '-Nhttp://soapinterop.org/xsd=samples.echo',
                        str(PEER / 'contracts' / 'InteropTest.wsdl')], check=True, capture_output=True, text=True, timeout=300)
        package = generated / 'samples' / 'echo'
        for name in ('InteropTestSoapBindingImpl.java', 'TestClient.java', 'echoHeaderStringHandler.java',
                     'echoHeaderStructHandler.java'):
            shutil.copyfile(PEER / 'contracts' / name, package / name)
        # Third-party generated and sample sources are compiled unchanged; warnings in them are not ours to fix.
        subprocess.run(['javac', '--release', '17', '-nowarn', '-cp', classpath(self.classes), '-d', str(self.classes)]
                       + sorted(str(p) for p in generated.rglob('*.java')), check=True, capture_output=True, text=True,
                       timeout=600)
        self.harness = subprocess.run(['javac', '--release', '17', '-Xlint:all', '-Werror', '-cp', classpath(self.classes),
                                       '-d', str(self.classes), str(PEER / 'AxisPeer.java')],
                                      capture_output=True, text=True, timeout=300)
        (self.work / 'client-config.wsdd').write_text(CLIENT_CONFIG)

    def exchange(self, capture):
        """Runs Axis's interop client against the Axis service; returns the client result and the captures."""
        # Axis logs through commons-logging; the no-op log keeps both processes silent, so any diagnostic fails.
        java = ['java', '-Dorg.apache.commons.logging.Log=org.apache.commons.logging.impl.NoOpLog', '-cp', classpath(self.classes)]
        with endpoint(java + ['AxisPeer', 'server', str(PEER / 'contracts' / 'deploy.wsdd')]) as (_, port):
            client = subprocess.run(java + ['-Daxis.ClientConfigFile=%s' % (self.work / 'client-config.wsdd'),
                                            '-Dqore.axis.capture=%s' % capture, 'AxisPeer', 'client',
                                            'http://127.0.0.1:%d/axis/services/echo' % port],
                                    cwd=self.work, capture_output=True, text=True, timeout=300)
        return client, [json.loads(line) for line in Path(capture).read_text().splitlines()]


class AxisPeerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='axis-peer-')
        # Registered first, so the directory is removed even when building the peer fails.
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.peer = AxisPeer(cls.temporary.name)

    def test_pinned_artifacts(self):
        manifest = json.loads((PEER / 'manifest.json').read_text())
        self.assertEqual(('Apache Axis', '1.4'), (manifest['implementation'], manifest['version']))
        listed = {a['path'] for a in manifest['artifacts']}
        self.assertEqual({'jars/' + p.name for p in (PEER / 'jars').iterdir()}, listed)
        for entry in manifest['artifacts'] + manifest['notices'] + manifest['contracts']:
            with self.subTest(path=entry['path']):
                data = (PEER / entry['path']).read_bytes()
                self.assertEqual((entry['size'], entry['sha256']), (len(data), hashlib.sha256(data).hexdigest()))
        self.assertEqual(listed, set(manifest['notice_coverage']))
        for coverage in manifest['notice_coverage'].values():
            for path in re.findall(r'(?:notices/|\.\./oracle/)[\w.-]+', coverage):
                self.assertTrue((PEER / path).is_file(), path)
        release = manifest['source_release']
        self.assertTrue(release['md5_matches'])
        self.assertEqual('good signature', release['signature']['result'])
        for contract in manifest['contracts']:
            self.assertEqual(release['url'], contract['source']['archive'])

    def test_peer_harness_compiles_without_warnings(self):
        self.assertEqual(0, self.peer.harness.returncode, self.peer.harness.stderr)
        self.assertEqual('', self.peer.harness.stdout + self.peer.harness.stderr)

    def test_round2_interop_and_corpus(self):
        wsdl = etree.parse(str(PEER / 'contracts' / 'InteropTest.wsdl'))
        operations = sorted(set(wsdl.xpath('//w:portType/w:operation/@name', namespaces={'w': 'http://schemas.xmlsoap.org/wsdl/'})))
        client, captured = self.peer.exchange(Path(self.temporary.name) / 'capture.jsonl')
        self.assertEqual(0, client.returncode, client.stdout + client.stderr)
        self.assertEqual(('VERIFIED %d FAILURES 0\n' % len(operations), ''), (client.stdout, client.stderr))
        self.assertEqual(operations, sorted(c['operation'] for c in captured))
        corpus = json.loads(CORPUS.read_text())
        self.assertEqual(operations, sorted(corpus['exchanges']))
        for row in captured:
            with self.subTest(operation=row['operation']):
                expected = corpus['exchanges'][row['operation']]
                for direction in ('request', 'response'):
                    envelope = etree.fromstring(row[direction].encode())
                    self.assertEqual('{%s}Envelope' % encoded_corpus.SOAP11_ENV, envelope.tag)
                    wrapper = envelope.find('{%s}Body' % encoded_corpus.SOAP11_ENV)[0]
                    self.assertEqual(encoded_corpus.SOAP11_ENC, wrapper.get('{%s}encodingStyle' % encoded_corpus.SOAP11_ENV))
                    self.assertEqual(expected['canonical_' + direction],
                                     json.loads(json.dumps(encoded_corpus.canonical(row[direction], (XSD_DATETIME,)))))
                    # The committed raw message itself reduces to the same canonical form.
                    self.assertEqual(expected['canonical_' + direction],
                                     json.loads(json.dumps(encoded_corpus.canonical(expected[direction], (XSD_DATETIME,)))))

    def test_w3c_collection_extraction_is_reproducible(self):
        committed = json.loads((ROOT / 'encoded-corpus' / 'w3c-soap12.json').read_text())
        self.assertEqual(sha256(encoded_corpus.COLLECTION), committed['source_sha256'])
        self.assertEqual(committed['tests'], json.loads(json.dumps(encoded_corpus.extract_w3c())))
        malformed = sorted((t['id'], m['from']) for t in committed['tests'] for m in t['messages'] if m.get('well_formed') is False)
        # Errata in the published collection, reproduced verbatim rather than corrected.
        self.assertEqual([('SBR1-echoBase64', 'Node A'), ('SBR1-echoDate', 'Node A'), ('T76', 'Node C'), ('T76', 'Node C'),
                          ('XMLP-14', 'Node C'), ('XMLP-15', 'Node A'), ('XMLP-9', 'Node C')], malformed)


if __name__ == '__main__':
    unittest.main()
