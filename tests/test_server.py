import http.client
import http.cookiejar
import json
import secrets
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch

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
        cls.old_api_limiter = server.API_LIMITER
        cls.old_auth_limiter = server.AUTH_LIMITER
        cls.old_root = server.ROOT
        server.DB_PATH = Path(cls.temp_dir.name) / "test.sqlite3"
        server.SESSION_SECRET = secrets.token_bytes(32)
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
        server.API_LIMITER = cls.old_api_limiter
        server.AUTH_LIMITER = cls.old_auth_limiter
        server.ROOT = cls.old_root
        cls.temp_dir.cleanup()

    def setUp(self):
        server.API_LIMITER = server.SlidingWindowLimiter()
        server.AUTH_LIMITER = server.SlidingWindowLimiter()

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

    def test_registration_rejects_invalid_inputs(self):
        client = self.make_client()
        payload = {
            "invite_password": server.INVITE_PASSWORD,
            "username": "validation-user",
            "password": "personal-test-password",
            "password_confirm": "personal-test-password",
            "terms_accepted": True,
        }

        invalid_cases = (
            ({**payload, "invite_password": "wrong-invitation"}, 401),
            ({**payload, "terms_accepted": False}, 400),
            ({**payload, "username": "x"}, 400),
            ({**payload, "password": "short", "password_confirm": "short"}, 400),
            ({**payload, "password_confirm": "different-password"}, 400),
        )
        for invalid_payload, expected_status in invalid_cases:
            with self.subTest(expected_status=expected_status, payload=invalid_payload):
                status, _, _ = self.request(
                    client, "/api/auth/register", "POST", invalid_payload
                )
                self.assertEqual(status, expected_status)

    def test_http_login_sets_session_and_rejects_wrong_password(self):
        client = self.make_client()
        status, _, _ = self.register(client, "login-user")
        self.assertEqual(status, 200)
        self.request(client, "/api/auth/logout", "POST", {})

        status, _, _ = self.request(
            client,
            "/api/auth/login",
            "POST",
            {"username": "login-user", "password": "incorrect-password"},
        )
        self.assertEqual(status, 401)

        status, headers, response = self.request(
            client,
            "/api/auth/login",
            "POST",
            {"username": "login-user", "password": "personal-test-password"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["ok"])
        cookie = headers.get("Set-Cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        status, _, response = self.request(client, "/api/auth/status")
        self.assertEqual(status, 200)
        self.assertTrue(response["authenticated"])

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

        status, _, response = self.request(
            client_a,
            f"/api/chats/{chat_id}",
            "PATCH",
            {"title": "Renamed private chat"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["title"], "Renamed private chat")

        client_b = self.make_client()
        status, _, _ = self.register(client_b, "user-b")
        self.assertEqual(status, 200)
        status, _, _ = self.request(client_b, f"/api/chats/{chat_id}")
        self.assertEqual(status, 404)
        status, _, response = self.request(client_b, "/api/chats")
        self.assertEqual(status, 200)
        self.assertNotIn(chat_id, [chat["id"] for chat in response["chats"]])

        status, _, response = self.request(
            client_a, f"/api/chats/{chat_id}", "DELETE", {}
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["ok"])
        status, _, _ = self.request(client_a, f"/api/chats/{chat_id}")
        self.assertEqual(status, 404)

        status, headers, response = self.request(
            client_a, "/api/auth/logout", "POST", {}
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["ok"])
        self.assertIn("Max-Age=0", headers.get("Set-Cookie", ""))
        status, _, response = self.request(client_a, "/api/auth/status")
        self.assertEqual(status, 200)
        self.assertFalse(response["authenticated"])

    def test_delete_json_body_preserves_keep_alive_connection(self):
        client = self.make_client()
        status, headers, _ = self.register(client, "delete-body-user")
        self.assertEqual(status, 200)
        cookie = headers.get("Set-Cookie", "").split(";", 1)[0]
        self.assertTrue(cookie.startswith("helmut_auth="))

        address = urlsplit(self.base_url)
        connection = http.client.HTTPConnection(address.hostname, address.port, timeout=5)
        try:
            connection.request(
                "POST",
                "/api/chats",
                body=json.dumps({"title": "DELETE body regression"}),
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 201)
            chat_id = json.loads(response.read())["chat"]["id"]

            connection.request(
                "DELETE",
                f"/api/chats/{chat_id}",
                body="{}",
                headers={"Content-Type": "application/json", "Cookie": cookie},
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertTrue(json.loads(response.read())["ok"])

            connection.request(
                "GET", f"/api/chats/{chat_id}", headers={"Cookie": cookie}
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 404)
            response.read()
        finally:
            connection.close()

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

        previous_root = server.ROOT
        try:
            with tempfile.TemporaryDirectory(prefix="helmut-ki-model-range-") as asset_dir:
                test_root = Path(asset_dir)
                model_path = test_root / "assets" / "models" / "range-test.gguf"
                model_path.parent.mkdir(parents=True)
                model_path.write_bytes(b"m" * (2 * 1024 * 1024))
                server.ROOT = test_root
                range_request = urllib.request.Request(
                    self.base_url + "/assets/models/range-test.gguf",
                    headers={"Range": "bytes=1048576-1048583"},
                )
                with client.open(range_request, timeout=5) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(
                        response.headers["Content-Range"],
                        "bytes 1048576-1048583/2097152",
                    )
                    self.assertEqual(response.read(), b"m" * 8)
        finally:
            server.ROOT = previous_root

    def test_authentication_and_api_rate_limits(self):
        client = self.make_client()
        for attempt in range(20):
            status, _, _ = self.request(
                client,
                "/api/auth/login",
                "POST",
                {"username": "missing-user", "password": "wrong-password"},
            )
            self.assertEqual(status, 401, f"auth attempt {attempt + 1}")

        status, headers, _ = self.request(
            client,
            "/api/auth/login",
            "POST",
            {"username": "missing-user", "password": "wrong-password"},
        )
        self.assertEqual(status, 429)
        self.assertEqual(headers.get("Retry-After"), "600")

        server.API_LIMITER = server.SlidingWindowLimiter()
        with patch.object(
            server.Handler,
            "log_message",
            lambda _self, _format, *_args: None,
        ):
            for attempt in range(180):
                status, _, _ = self.request(client, "/api/auth/status")
                self.assertEqual(status, 200, f"API request {attempt + 1}")
            status, headers, _ = self.request(client, "/api/auth/status")
        self.assertEqual(status, 429)
        self.assertEqual(headers.get("Retry-After"), "60")

        limiter = server.SlidingWindowLimiter()
        with patch("server.time.monotonic", side_effect=[1.0, 1.1, 1.2, 2.2]):
            self.assertTrue(limiter.allow("test-client", 2, 1))
            self.assertTrue(limiter.allow("test-client", 2, 1))
            self.assertFalse(limiter.allow("test-client", 2, 1))
            self.assertTrue(limiter.allow("test-client", 2, 1))

    def test_chat_and_message_quotas(self):
        client = self.make_client()
        status, _, _ = self.register(client, "quota-user")
        self.assertEqual(status, 200)

        with (
            patch.object(server, "MAX_CHATS_PER_USER", 2),
            patch.object(server, "MAX_MESSAGES_PER_CHAT", 2),
            patch.object(server, "MAX_MESSAGES_PER_USER", 3),
        ):
            status, _, first = self.request(
                client, "/api/chats", "POST", {"title": "First"}
            )
            self.assertEqual(status, 201)
            first_chat_id = first["chat"]["id"]
            status, _, second = self.request(
                client, "/api/chats", "POST", {"title": "Second"}
            )
            self.assertEqual(status, 201)
            second_chat_id = second["chat"]["id"]
            status, _, _ = self.request(
                client, "/api/chats", "POST", {"title": "Over limit"}
            )
            self.assertEqual(status, 507)

            for role, content in (("user", "one"), ("assistant", "two")):
                status, _, _ = self.request(
                    client,
                    f"/api/chats/{first_chat_id}/messages",
                    "POST",
                    {"role": role, "content": content},
                )
                self.assertEqual(status, 201)
            status, _, _ = self.request(
                client,
                f"/api/chats/{first_chat_id}/messages",
                "POST",
                {"role": "user", "content": "chat quota exceeded"},
            )
            self.assertEqual(status, 507)

            status, _, _ = self.request(
                client,
                f"/api/chats/{second_chat_id}/messages",
                "POST",
                {"role": "user", "content": "user quota reached"},
            )
            self.assertEqual(status, 201)
            status, _, _ = self.request(
                client,
                f"/api/chats/{second_chat_id}/messages",
                "POST",
                {"role": "assistant", "content": "user quota exceeded"},
            )
            self.assertEqual(status, 507)


if __name__ == "__main__":
    unittest.main()
