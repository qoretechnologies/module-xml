#!/usr/bin/env python3
"""Independent HTTP form part presence and XSD lexical validation.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import unittest
from urllib.parse import parse_qs
from xml.sax.saxutils import escape

from independent import SchemaJob, run

ROOT = Path(__file__).resolve().parent


class HttpPartPresenceTest(unittest.TestCase):
    def test_form_parts_and_types(self):
        models = json.loads((ROOT / 'regressions/wsdl-http-part-presence/cases.json').read_text())['models']
        self.assertEqual(5, len(models))
        self.assertEqual(31, sum(len(model['rows']) for model in models))
        jobs = []
        for model in models:
            elements = ''.join(f'<xs:element name="{name}" type="xs:{kind}"/>'
                               for name, kind in model['parts'].items())
            schema = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                      '<xs:element name="args"><xs:complexType><xs:sequence>' + elements
                      + '</xs:sequence></xs:complexType></xs:element></xs:schema>')
            documents = {}
            for index, row in enumerate(model['rows']):
                name = f'{model["name"]}/{index}'
                fields = parse_qs(row['form'], keep_blank_values=True, encoding='utf-8', errors='strict')
                missing = next((part for part in model['parts'] if part not in fields), None)
                self.assertEqual(row['missing'], missing, name)
                # Preserve present empty values and repetitions for the independent
                # XSD validator. Unbound query names keep the API's existing tolerance.
                documents[name] = ('<args>' + ''.join(
                    f'<{part}>{escape(value)}</{part}>' for part in model['parts']
                    for value in fields.get(part, [])) + '</args>').encode()
                if row['valid']:
                    value = {}
                    for part, kind in model['parts'].items():
                        self.assertEqual(1, len(fields[part]), name)
                        lexical = fields[part][0]
                        value[part] = (int(lexical) if kind == 'int' else
                                       {'true': True, 'false': False, '1': True, '0': False}[lexical]
                                       if kind == 'boolean' else lexical)
                    self.assertEqual(row['value'], value, name)
            jobs.append(SchemaJob(model['name'], f'urn:form:{model["name"]}', schema.encode(), documents))
        report = run(jobs)
        for model in models:
            result = report['schemas'][model['name']]
            self.assertTrue(result['ok'], result)
            self.assertEqual([], result['warnings'])
            for index, row in enumerate(model['rows']):
                result = report['documents'][f'{model["name"]}/{index}']
                self.assertEqual(row['valid'], result['ok'], result)
                self.assertEqual([], result['warnings'])


if __name__ == '__main__':
    unittest.main()
