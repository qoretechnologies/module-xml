#!/usr/bin/env python3
"""Generated multipart SOAP messages are read as an independent MIME parser reads them.

Copyright (C) 2026 Qore Technologies, s.r.o.

SOAP messages with attachments are MIME multipart/related entities (RFC 2045, RFC 2046, RFC 2387), which SOAP clients
and handlers read with WSDLLib::parseMultiPartSOAPMessage(). A seeded generator writes messages with boundaries drawn
from the RFC 2046 boundary characters, preambles and epilogues, the root part at any position with and without a
start parameter, and attachments whose binary payloads contain CR, LF and near-delimiter byte sequences, in the
binary, base64, quoted-printable and 7bit transfer encodings, with and without Content-IDs. The expected root and
attachments come from Python's email parser, independent of the module, and must equal the generated payloads.
Mutations break one rule each; the module must reject them with SOAP-MESSAGE-ERROR. The seed and a digest of the
generated cases are pinned.
"""
import base64
import binascii
from email import policy
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SEED = 20260927
COUNT = 200
# RFC 2046 section 5.1.1: bcharsnospace, plus space when not last
BCHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'()+_,-./:=?"
ENCODINGS = ("binary", "base64", "quoted-printable", "7bit")
MUTATIONS = {
    "missing-root": "RFC 2387 section 3.2: the start parameter names the root part",
    "duplicate-content-id": "RFC 2045 section 7: Content-IDs are unique",
    "invalid-media-type": "RFC 2045 section 5.1: a Content-Type is a type/subtype",
    "unknown-transfer-encoding": "RFC 2045 section 6.4: an unrecognized encoding cannot be interpreted",
    "missing-close-delimiter": "RFC 2046 section 5.1.1: the last body part is followed by a close-delimiter",
    "mismatched-boundary": "RFC 2046 section 5.1.1: body parts are delimited by the boundary parameter",
}
# the SHA-256 of the generated cases; see test_generator_is_pinned
CASES_SHA256 = "becf3642bcbd4170d743876c38260f6199b8cdca425c6fd52de886d421c37482"


def envelope(index):
    return (f'<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>'
            f'<p:item xmlns:p="urn:mime">{index}</p:item></s:Body></s:Envelope>').encode()


class Message:
    def __init__(self, rng, index):
        self.rng, self.index = rng, index
        length = rng.choice((1, 8, 30, 70))
        boundary = "".join(rng.choice(BCHARS + " ") for _ in range(length - 1)) + rng.choice(BCHARS)
        self.boundary = boundary
        self.quoted = rng.random() < 0.5 or any(c in boundary for c in " ()+,/:=?'")
        self.preamble = rng.choice((b"", b"This is a MIME message.\r\n", b"preamble \r\n\r\n"))
        self.epilogue = rng.choice((b"", b"\r\n", b"epilogue text\r\n"))
        attachments = []
        for position in range(rng.choice((0, 1, 1, 2, 3, 4))):
            payload = self.payload()
            encoding = rng.choice(ENCODINGS)
            if encoding == "7bit" and not self.seven_bit(payload):
                encoding = "binary"
            content_id = f"part{position}.{index}@example.test" if rng.random() < 0.85 else None
            attachments.append({"payload": payload, "encoding": encoding, "content_id": content_id,
                                "media": rng.choice(("application/octet-stream", "image/png", "text/plain"))})
        self.root = {"payload": envelope(index), "encoding": rng.choice(("8bit", "binary")),
                     "content_id": f"root.{index}@example.test", "media": "text/xml", "root": True}
        self.parts = attachments
        self.parts.insert(rng.randrange(len(attachments) + 1), self.root)
        self.start = self.parts[0] is not self.root or rng.random() < 0.5
        self.header_case = rng.choice((str, str.lower, str.upper))
        self.mutation = None

    def payload(self):
        rng = self.rng
        kind = rng.random()
        if kind < 0.1:
            return b""
        data = bytes(rng.randrange(256) for _ in range(rng.choice((1, 2, 17, 100, 1000))))
        if kind < 0.5:
            # sequences resembling a delimiter that are not one
            near = rng.choice((b"\r\n--" + self.boundary.encode()[:-1] + b"#", b"--" + self.boundary.encode(),
                               b"\r\n-" + self.boundary.encode(), b"\r\r\n\n--", b"\r\n\r\n"))
            cut = rng.randrange(len(data) + 1)
            data = data[:cut] + near + data[cut:]
        return data

    @staticmethod
    def seven_bit(payload):
        return all(byte < 128 and byte not in (0, 13, 10) for byte in payload) and len(payload) < 998

    def header(self, name, value):
        return f"{self.header_case(name)}: {value}\r\n".encode()

    def encode(self, part):
        payload, encoding = part["payload"], part["encoding"]
        if encoding == "base64":
            text = base64.encodebytes(payload).replace(b"\n", b"\r\n")
            return text
        if encoding == "quoted-printable":
            # binary data: CR and LF are encoded as =0D and =0A; only soft line breaks end lines
            return binascii.b2a_qp(payload, quotetabs=True, istext=False).replace(b"=\n", b"=\r\n")
        return payload

    def render(self):
        m = self.mutation
        body = self.preamble
        identified = [part for part in self.parts if part["content_id"]]
        # the last identified attachment repeats the Content-ID of another identified part
        duplicate = next((part for part in reversed(identified) if part is not self.root), None) \
            if m == "duplicate-content-id" else None
        for position, part in enumerate(self.parts):
            body += b"\r\n" if position or self.preamble else b""
            body += b"--" + self.boundary.encode() + b"\r\n"
            media = "not a type" if m == "invalid-media-type" and part is not self.root else part["media"]
            body += self.header("Content-Type", media + ("; charset=utf-8" if part is self.root else ""))
            content_id = part["content_id"]
            if part is duplicate:
                content_id = next(other["content_id"] for other in identified if other is not part)
            if content_id:
                body += self.header("Content-ID", f"<{content_id}>")
            encoding = "x-gzip" if m == "unknown-transfer-encoding" and part is not self.root else part["encoding"]
            body += self.header("Content-Transfer-Encoding", encoding)
            body += b"\r\n" + self.encode(part)
        if m != "missing-close-delimiter":
            body += b"\r\n--" + self.boundary.encode() + b"--\r\n" + self.epilogue
        declared = "mismatch-" + self.boundary if m == "mismatched-boundary" else self.boundary
        boundary = f'"{declared}"' if self.quoted or " " in declared else declared
        start = "missing.root@example.test" if m == "missing-root" else self.root["content_id"]
        media = f'multipart/related; boundary={boundary}; type="text/xml"'
        if self.start or m == "missing-root":
            media += f'; start="<{start}>"'
        return media, body

    def eligible(self, kind):
        attachments = [part for part in self.parts if part is not self.root]
        if kind == "duplicate-content-id":
            return any(part["content_id"] for part in attachments)
        if kind in ("invalid-media-type", "unknown-transfer-encoding"):
            return bool(attachments)
        return True


def generate():
    rng = random.Random(SEED)
    messages = [Message(rng, index) for index in range(COUNT)]
    cases = []
    for message in messages:
        media, body = message.render()
        cases.append({"id": f"valid-{message.index}", "kind": "valid", "content_type": media,
                      "body": base64.b64encode(body).decode(),
                      "root": base64.b64encode(message.root["payload"]).decode(),
                      "parts": {part["content_id"]: base64.b64encode(part["payload"]).decode()
                                for part in message.parts if part is not message.root and part["content_id"]},
                      "unidentified": sum(1 for part in message.parts
                                          if part is not message.root and not part["content_id"])})
    for kind in MUTATIONS:
        for message in [message for message in messages if message.eligible(kind)][:20]:
            message.mutation = kind
            media, body = message.render()
            message.mutation = None
            cases.append({"id": f"{kind}-{message.index}", "kind": kind, "content_type": media,
                          "body": base64.b64encode(body).decode()})
    return cases


def email_view(case):
    """Returns the root part and identified and unidentified attachments as Python's email parser reads them."""
    wire = base64.b64decode(case["body"])
    message = BytesParser(policy=policy.default).parsebytes(
        ("Content-Type: " + case["content_type"] + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + wire)
    parts = list(message.iter_parts())
    start = message.get_param("start")
    root = next(part for part in parts if str(part["Content-ID"]).strip() == start) if start else parts[0]
    return {"defects": [type(defect).__name__ for defect in message.defects]
                       + [type(defect).__name__ for part in parts for defect in part.defects],
            "root": base64.b64encode(root.get_payload(decode=True)).decode(),
            "parts": {str(part["Content-ID"]).strip()[1:-1]: base64.b64encode(part.get_payload(decode=True)).decode()
                      for part in parts if part is not root and part["Content-ID"]},
            "unidentified": sum(1 for part in parts if part is not root and not part["Content-ID"])}


def run_module(cases):
    with tempfile.TemporaryDirectory(prefix="mime-generation-") as temp:
        path = Path(temp) / "cases.json"
        path.write_text(json.dumps([{"id": case["id"], "content_type": case["content_type"], "body": case["body"]}
                                    for case in cases]))
        env = dict(os.environ, QORE_MODULE_DIR=os.pathsep.join(
            (str(REPO / "build-debug"), str(REPO / "qlib"), os.environ.get("QORE_MODULE_DIR", ""))))
        result = subprocess.run([os.environ.get("QORE", "qore"), "-b", "--enable-debug",
                                 str(HERE / "mime-parts.qr"), str(path)],
                                capture_output=True, text=True, env=env, timeout=300)
    if result.returncode or result.stderr:
        raise AssertionError(f"worker exit {result.returncode}: {result.stderr}")
    return [json.loads(line) for line in result.stdout.splitlines()]


class MimeGenerationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = generate()
        cls.results = run_module(cls.cases)

    def test_generator_is_pinned(self):
        digest = hashlib.sha256(json.dumps(self.cases, sort_keys=True).encode()).hexdigest()
        self.assertEqual(CASES_SHA256, digest)
        self.assertEqual(COUNT + 20 * len(MUTATIONS), len(self.cases))
        self.assertEqual(len(self.cases), len({case["id"] for case in self.cases}))
        self.assertEqual([case["id"] for case in self.cases], [result["id"] for result in self.results])

    def test_generated_messages_cover_the_constructs(self):
        valid = [case for case in self.cases if case["kind"] == "valid"]
        self.assertTrue(any('boundary="' in case["content_type"] and " " in case["content_type"].split('"')[1]
                            for case in valid))
        self.assertTrue(any("start=" not in case["content_type"] for case in valid))
        self.assertTrue(any(case["unidentified"] for case in valid))
        self.assertTrue(any(len(case["parts"]) >= 3 for case in valid))
        bodies = [base64.b64decode(case["body"]) for case in valid]
        for encoding in ENCODINGS:
            self.assertTrue(any(f"Transfer-Encoding: {encoding}".encode().lower() in body.lower() for body in bodies),
                            encoding)
        self.assertTrue(any(not base64.b64decode(value) for case in valid for value in case["parts"].values()))

    def test_valid_messages_read_as_the_email_parser_reads_them(self):
        for case, result in zip(self.cases, self.results):
            if case["kind"] != "valid":
                continue
            with self.subTest(case=case["id"]):
                view = email_view(case)
                # the independent parser reads the generated payloads without defects
                self.assertEqual([], view["defects"])
                self.assertEqual((case["root"], case["parts"], case["unidentified"]),
                                 (view["root"], view["parts"], view["unidentified"]))
                self.assertNotIn("error", result, result)
                self.assertEqual("text/xml", result["root_type"].split(";")[0].strip())
                self.assertEqual((view["root"], view["parts"], view["unidentified"]),
                                 (result["root"], result["parts"], result["unidentified"]))

    def test_invalid_messages_are_rejected(self):
        for case, result in zip(self.cases, self.results):
            if case["kind"] == "valid":
                continue
            with self.subTest(case=case["id"], rule=MUTATIONS[case["kind"]]):
                self.assertEqual("SOAP-MESSAGE-ERROR", result.get("error"), result)


if __name__ == "__main__":
    unittest.main()
