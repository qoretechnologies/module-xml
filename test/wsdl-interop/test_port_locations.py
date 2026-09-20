#!/usr/bin/env python3
"""Independent WSDL port URI resolution. Copyright (C) 2026 Qore Technologies, s.r.o."""
import queue
import unittest
from urllib.parse import quote, urljoin, urlsplit

from test_http_request_url import contract, origin, run


class PortLocationTests(unittest.TestCase):
    def test_containing_document_and_overrides(self):
        received = queue.Queue()
        with origin("A", received) as a, origin("B", received) as b:
            base = a + "/contracts/service.wsdl?old=1"
            references = ["../api/", "nested/", "/root/", "?rev=2", "?", "", "../č/a b/", b + "/other/"]
            jobs = []
            expected = []
            for state in ("source", "saved", "data"):
                for reference in references:
                    # Preserve escapes while converting Unicode and spaces to a URI, then use an independent resolver.
                    address = urljoin(base, quote(reference, safe="/:?&=%#"))
                    if reference == "?":
                        address = base.split("?", 1)[0] + "?"
                    target = urljoin(address, "send?id=hello")
                    jobs.append({"xml": contract(reference, "send"), "state": state,
                                 "wsdl_options": {"document_location": base},
                                 "calls": [{"value": {"id": "hello"}}]})
                    expected.append((address, target, "B" if target.startswith(b + "/") else "A"))
            jobs.append({"xml": contract("../api/", "send"), "wsdl_options": {"document_location": base},
                         "options": {"url": b + "/override/"}, "calls": [{"value": {"id": "hello"}}]})
            expected.append((b + "/override/", b + "/override/send?id=hello", "B"))
            for result, (address, target, name) in zip(run(jobs), expected, strict=True):
                request = received.get_nowait()
                parsed = urlsplit(target)
                self.assertEqual(address, result["url"])
                self.assertEqual(parsed.path + "?" + parsed.query, request["path"])
                self.assertEqual(name, request["origin"])
                self.assertEqual({"result": name}, result["calls"][0]["value"])
                self.assertEqual(target, result["calls"][0]["info"]["effective-url"])
                self.assertTrue(result["unchanged"])
            self.assertTrue(received.empty())

    def test_imported_service_and_saved_context(self):
        received = queue.Queue()
        with origin("A", received) as a:
            root = a + "/catalog/root.wsdl"
            imported = a + "/imports/v2/service.wsdl"
            source = ('<w:definitions xmlns:w="http://schemas.xmlsoap.org/wsdl/" targetNamespace="urn:root">'
                      '<w:import namespace="urn:request-url" location="../imports/v2/service.wsdl"/></w:definitions>')
            jobs = [{"xml": source, "state": state, "wsdl_options": {"document_location": root,
                     "async_only": True, "xsd_cache": {imported: contract("../api/", "send")}},
                     "calls": [{"value": {"id": "hello"}}]} for state in ("source", "saved", "data")]
            for result in run(jobs):
                self.assertEqual(a + "/imports/api/", result["url"])
                self.assertEqual("/imports/api/send?id=hello", received.get_nowait()["path"])
                self.assertEqual({"result": "A"}, result["calls"][0]["value"])
                self.assertTrue(result["unchanged"])
            self.assertTrue(received.empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)
