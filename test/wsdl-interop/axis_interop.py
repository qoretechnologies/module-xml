#!/usr/bin/env python3
"""Derivation of the live Axis interop contract.

Copyright (C) 2026 Qore Technologies, s.r.o.

The pinned SOAPBuilders InteropTest.wsdl uses xml-soap:Map, Apache SOAP's map type, without importing or
defining it; Axis treats it as built in. A schema processor cannot resolve it, so this module rejects the
original contract. The derivative adds the schema that Axis 1.4's own Java2WSDL emits for java.util.HashMap,
verbatim except for an xmlns:apachesoap declaration on its root, and imports that namespace where it is used.
"""
import argparse
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import jvm

ROOT = Path(__file__).resolve().parent
PEER = ROOT / 'axis-peer'
ORIGINAL = PEER / 'contracts' / 'InteropTest.wsdl'
DERIVED = PEER / 'derived' / 'InteropTest-map.wsdl'
MAP_SCHEMA = PEER / 'derived' / 'apachesoap-map.xsd'
MAP_ECHO = PEER / 'derived' / 'MapEcho.java'
PROVENANCE = PEER / 'derived' / 'provenance.json'
JAVA2WSDL = ['-o', 'map.wsdl', '-l', 'http://example.invalid/', '-n', 'urn:probe', '-y', 'RPC', '-u', 'ENCODED',
             'probe.MapEcho']
ANCHOR = ('<schema xmlns="http://www.w3.org/2001/XMLSchema" targetNamespace="http://soapinterop.org/xsd">\n'
          '                  <import namespace = "http://schemas.xmlsoap.org/soap/encoding/"/>')
EMITTED_ROOT = '<schema targetNamespace="http://xml.apache.org/xml-soap" xmlns="http://www.w3.org/2001/XMLSchema">'


def generate_map_schema():
    """Runs Axis 1.4's Java2WSDL on MapEcho and returns the xml-soap schema element it emits."""
    jars = sorted(glob.glob(str(PEER / 'jars' / '*.jar')))
    with tempfile.TemporaryDirectory(prefix='axis-map-') as work:
        classes = Path(work) / 'classes'
        classes.mkdir()
        subprocess.run(['javac', '--release', '17', '-Xlint:all', '-Werror', '-d', str(classes), str(MAP_ECHO)],
                       check=True, capture_output=True, text=True, timeout=300, env=jvm.environment())
        subprocess.run(['java', '-Dorg.apache.commons.logging.Log=org.apache.commons.logging.impl.NoOpLog',
                        '-cp', os.pathsep.join(jars + [str(classes)]), 'org.apache.axis.wsdl.Java2WSDL'] + JAVA2WSDL,
                       cwd=work, check=True, capture_output=True, text=True, timeout=300, env=jvm.environment())
        match = re.search(r'<schema targetNamespace="http://xml.apache.org/xml-soap".*?</schema>',
                          (Path(work) / 'map.wsdl').read_text(), re.S)
        if not match:
            raise ValueError('Java2WSDL emitted no xml-soap schema')
        return match.group(0) + '\n'


def derive(original, map_schema):
    """Returns the derived contract text from the pinned original and the emitted Map schema."""
    if original.count(ANCHOR) != 1 or not map_schema.startswith(EMITTED_ROOT):
        raise ValueError('unexpected source text')
    schema = map_schema.rstrip('\n').replace(EMITTED_ROOT, EMITTED_ROOT[:-1] + ' xmlns:apachesoap="http://xml.apache.org/xml-soap">', 1)
    return original.replace(ANCHOR, schema + '\n    ' + ANCHOR + '\n                  <import namespace="http://xml.apache.org/xml-soap"/>', 1)


def provenance():
    """Returns the provenance record of the derived contract."""
    def entry(path):
        return {'path': str(path.relative_to(PEER)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {
        'derived': entry(DERIVED),
        'source': entry(ORIGINAL),
        'map_schema': dict(entry(MAP_SCHEMA), generator={
            'tool': 'org.apache.axis.wsdl.Java2WSDL (Apache Axis 1.4, jars/axis-1.4.jar)',
            'input': entry(MAP_ECHO),
            'arguments': JAVA2WSDL,
            'extracted': 'the emitted schema element whose targetNamespace is http://xml.apache.org/xml-soap',
        }),
        'changes': [
            'inserts the emitted xml-soap schema, with an xmlns:apachesoap declaration on its root, before the '
            'http://soapinterop.org/xsd schema',
            'adds <import namespace="http://xml.apache.org/xml-soap"/> to the http://soapinterop.org/xsd schema',
        ],
        'reason': 'the published contract uses xml-soap:Map, which Axis treats as built in, without importing or '
                  'defining it',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--write', action='store_true', help='regenerate the Map schema and the derived contract')
    args = parser.parse_args()
    if args.write:
        MAP_SCHEMA.write_text(generate_map_schema())
        DERIVED.write_text(derive(ORIGINAL.read_text(), MAP_SCHEMA.read_text()))
        PROVENANCE.write_text(json.dumps(provenance(), indent=2) + '\n')
    for path in (ORIGINAL, MAP_SCHEMA, DERIVED):
        print(hashlib.sha256(path.read_bytes()).hexdigest(), path.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
