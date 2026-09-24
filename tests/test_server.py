import http.cookiejar
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import server


class ServerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory(prefix="helmut-ki-test-")
        cls.old_db_path = server.DB_PATH
        cls.old_session_secret = server.SESSION_SECRET
        cls.old_invite_password = server.INVITE_PASSWORD
        cls.old_cookie_secure = server.COOKIE_SECURE
        cls.old_trust_proxy = server.TRUST_PROXY
        server.DB_PATH = Path(cls.temp_dir.name) / "test.sqlite3"
        server.SESSION_SECRET = b"T" * 32
        server.INVITE_PASSWORD = "test-invitation-password"
        server.COOKIE_SECURE = "false"
        server.TRUST_PROXY = False
        server.init_database()
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)
        server.DB_PATH = cls.old_db_path
        server.SESSION_SECRET = cls.old_session_secret
        server.INVITE_PASSWORD = cls.old_invite_password
        server.COOKIE_SECURE = cls.old_cookie_secure
        server.TRUST_PROXY = cls.old_trust_proxy
        cls.temp_dir.cleanup()

    def make_client(self):
        cookie_jar = http.cookiejar.CookieJar()
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    def request(self, client, path, method="GET", payload=None):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path, data=data, headers=headers, method=method
        )
        try:
            with client.open(request, timeout=5) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
                return response.status, response.headers, (
                    json.loads(body) if "application/json" in content_type else body
                )
        except urllib.error.HTTPError as error:
            body = error.read()
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body
            error.close()
            return error.code, error.headers, parsed

    def register(self, client, username):
        return self.request(
            client,
            "/api/auth/register",
            "POST",
            {
                "invite_password": server.INVITE_PASSWORD,
                "username": username,
                "password": "personal-test-password",
                "password_confirm": "personal-test-password",
                "terms_accepted": True,
            },
        )

    def test_public_pages_and_path_allowlist(self):
        client = self.make_client()
        for path in (
            "/", "/chat.html", "/legal.html", "/AGB.md",
            "/DATENSCHUTZERKLAERUNG.md", "/TERMS.en.md", "/PRIVACY.en.md",
        ):
            status, _, body = self.request(client, path)
            self.assertEqual(status, 200, path)
        self.assertIn(b"<!doctype html>", self.request(client, "/")[2].lower())
        for path in (
            "/index.html", "/support.html", "/live-mining.html", "/live-mining.js",
            "/logos.html", "/rechtliches.html", "/assets/helmut-logo.jpg",
            "/web-upload/helmut-logo-kombiniert.jpg",
            "/server.py", "/README.md", "/.git/config", "/../server.py",
            "/api/stats",
        ):
            status, _, _ = self.request(client, path)
            self.assertEqual(status, 404, path)

    def test_register_chat_isolation_encryption_and_logout(self):
        client_a = self.make_client()
        status, _, response = self.register(client_a, "user-a")
        self.assertEqual(status, 200)
        self.assertTrue(response["ok"])

        status, _, response = self.request(client_a, "/api/auth/status")
        self.assertEqual(status, 200)
        self.assertTrue(response["authenticated"])
        self.assertEqual(response["user"]["username"], "user-a")

        status, _, response = self.request(
            client_a, "/api/chats", "POST", {"title": "Private test chat"}
        )
        self.assertEqual(status, 201)
        chat_id = response["chat"]["id"]

        secret_message = "private-message-that-must-not-be-plaintext"
        status, _, response = self.request(
            client_a,
            f"/api/chats/{chat_id}/messages",
            "POST",
            {"role": "user", "content": secret_message},
        )
        self.assertEqual(status, 201)
        self.assertEqual(response["message"]["content"], secret_message)

        status, _, response = self.request(client_a, f"/api/chats/{chat_id}")
        self.assertEqual(status, 200)
        self.assertEqual(response["messages"][0]["content"], secret_message)
        self.assertNotIn(secret_message.encode("utf-8"), server.DB_PATH.read_bytes())

        client_b = self.make_client()
        status, _, _ = self.register(client_b, "user-b")
        self.assertEqual(status, 200)
        status, _, _ = self.request(client_b, f"/api/chats/{chat_id}")
        self.assertEqual(status, 404)

        status, _, response = self.request(client_a, "/api/auth/logout", "POST", {})
        self.assertEqual(status, 200)
        self.assertTrue(response["ok"])
        status, _, response = self.request(client_a, "/api/auth/status")
        self.assertEqual(status, 200)
        self.assertFalse(response["authenticated"])

    def test_password_validation_and_range_requests(self):
        password_hash = server.make_password_hash("correct-password")
        self.assertTrue(server.verify_password("correct-password", password_hash))
        self.assertFalse(server.verify_password("wrong-password", password_hash))
        self.assertFalse(server.verify_password("correct-password", "1$bad$bad"))

        client = self.make_client()
        status, headers, body = self.request(client, "/styles.css")
        self.assertEqual(status, 200)
        self.assertGreater(len(body), 100)
        self.assertIn("text/css", headers.get("Content-Type", ""))
        status, _, _ = self.request(client, "/assets/helmut-logo.jpg")
        self.assertEqual(status, 404)

        request = urllib.request.Request(
            self.base_url + "/styles.css",
            headers={"Range": "bytes=0-9"},
        )
        with client.open(request, timeout=5) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.headers["Content-Range"].split()[1].split("/")[0], "0-9")
            self.assertEqual(len(response.read()), 10)


if __name__ == "__main__":
    unittest.main()
