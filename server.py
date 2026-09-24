#!/usr/bin/env python3
"""Helmut-KI chat-system server.

The browser performs model inference locally. This server handles the public
files, authentication and encrypted per-user chat history.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import http.cookies
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as error:  # pragma: no cover - handled during startup
    raise RuntimeError(
        "Das Python-Paket 'cryptography' wird für die Chat-Verschlüsselung benötigt."
    ) from error


ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("HELMUT_HOST", "127.0.0.1")
PORT = int(os.environ.get("HELMUT_PORT", "8080"))
INVITE_PASSWORD = os.environ.get("HELMUT_CHAT_PASSWORD", "")
DB_PATH = Path(os.environ.get("HELMUT_DB_PATH", str(ROOT / "helmut.sqlite3")))
BROWSER_MODEL = os.environ.get(
    "HELMUT_BROWSER_MODEL", "Llama-3.2-1B-Instruct-q4f16_1-MLC"
)
TRUST_PROXY = os.environ.get("HELMUT_TRUST_PROXY", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
COOKIE_SECURE = os.environ.get("HELMUT_COOKIE_SECURE", "auto").lower()
SESSION_TTL = 30 * 24 * 60 * 60
PBKDF2_ITERATIONS = 310_000
MAX_REQUEST_BYTES = 1_048_576
MAX_MESSAGE_CHARS = 40_000
MAX_CHATS_PER_USER = 100
MAX_MESSAGES_PER_CHAT = 1_000
MAX_MESSAGES_PER_USER = 10_000
USERNAME_RE = re.compile(r"^[a-zA-Z0-9._+@-]{3,64}$")

# Only these root files and directories are public. In particular, source
# code, Git metadata, environment files and project documentation are not.
PUBLIC_ROOT_FILES = frozenset(
    {
        "chat.html",
        "legal.html",
        "AGB.md",
        "DATENSCHUTZERKLAERUNG.md",
        "TERMS.en.md",
        "PRIVACY.en.md",
        "styles.css",
        "app.js",
    }
)
PUBLIC_ROOT_DIRS = frozenset({("assets", "models")})


def decode_key_text(value: str) -> bytes | None:
    if not value:
        return None
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (ValueError, TypeError):
        return None
    return decoded if len(decoded) == 32 else None


def load_session_secret() -> bytes | None:
    configured = decode_key_text(os.environ.get("HELMUT_SESSION_SECRET", ""))
    if configured is not None:
        return configured
    secret_file = os.environ.get("HELMUT_SESSION_SECRET_FILE", "")
    if not secret_file:
        return None
    try:
        return decode_key_text(Path(secret_file).read_text(encoding="ascii").strip())
    except (OSError, UnicodeError):
        return None


SESSION_SECRET = load_session_secret()


def password_configured() -> bool:
    return len(INVITE_PASSWORD) >= 8


def db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    try:
        os.chmod(DB_PATH, 0o600)
    except OSError:
        pass
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def now() -> int:
    return int(time.time())


def encode_blob(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def decode_blob(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def encrypt_blob(key: bytes, plaintext: bytes, associated_data: bytes) -> str:
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return encode_blob(nonce + ciphertext)


def decrypt_blob(key: bytes, encoded: str, associated_data: bytes) -> bytes:
    raw = decode_blob(encoded)
    if len(raw) <= 12:
        raise ValueError("Ungültiger verschlüsselter Wert.")
    return AESGCM(key).decrypt(raw[:12], raw[12:], associated_data)


def password_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, 32
    )


def legacy_storage_key() -> bytes:
    if SESSION_SECRET is None:
        raise RuntimeError("HELMUT_SESSION_SECRET ist nicht eingerichtet.")
    return hmac.new(
        SESSION_SECRET, b"helmut-ki-legacy-storage-key:v1", hashlib.sha256
    ).digest()


def user_key_aad(user_id: str) -> bytes:
    return f"helmut-ki:user-key:v1:{user_id}".encode("utf-8")


def session_key_aad(user_id: str) -> bytes:
    return f"helmut-ki:session-key:v1:{user_id}".encode("utf-8")


def title_aad(user_id: str, chat_id: str) -> bytes:
    return f"helmut-ki:title:v1:{user_id}:{chat_id}".encode("utf-8")


def message_aad(user_id: str, chat_id: str, message_id: int) -> bytes:
    return f"helmut-ki:message:v1:{user_id}:{chat_id}:{message_id}".encode("utf-8")


def make_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = password_key(password, salt)
    return "$".join(
        [str(PBKDF2_ITERATIONS), encode_blob(salt), encode_blob(digest)]
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        iterations_text, salt_text, digest_text = encoded.split("$", 2)
        iterations = int(iterations_text)
        salt = decode_blob(salt_text)
        expected = decode_blob(digest_text)
    except (ValueError, TypeError):
        return False
    if not 100_000 <= iterations <= 2_000_000:
        return False
    if len(salt) != 16 or len(expected) != 32:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def user_data_key_for_password(
    connection: sqlite3.Connection, user_id: str, password: str
) -> bytes:
    row = connection.execute(
        "SELECT encryption_salt, wrapped_data_key FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        raise ValueError("Benutzerkonto nicht gefunden.")

    if not row["encryption_salt"] or not row["wrapped_data_key"]:
        salt = secrets.token_bytes(16)
        data_key = secrets.token_bytes(32)
        wrapped = encrypt_blob(
            password_key(password, salt), data_key, user_key_aad(user_id)
        )
        connection.execute(
            "UPDATE users SET encryption_salt = ?, wrapped_data_key = ? WHERE id = ?",
            (encode_blob(salt), wrapped, user_id),
        )
    else:
        salt = decode_blob(row["encryption_salt"])
        data_key = decrypt_blob(
            password_key(password, salt),
            row["wrapped_data_key"],
            user_key_aad(user_id),
        )
        if len(data_key) != 32:
            raise ValueError("Ungültiger Datenschlüssel.")

    reencrypt_legacy_user_data(connection, user_id, data_key)
    return data_key


def decrypt_stored_text(
    value: str,
    encrypted: int,
    key_scope: str,
    user_key: bytes,
    associated_data: bytes,
) -> str:
    if not encrypted or key_scope == "plain":
        return value
    key = user_key if key_scope == "user" else legacy_storage_key()
    return decrypt_blob(key, value, associated_data).decode("utf-8")


def reencrypt_legacy_user_data(
    connection: sqlite3.Connection, user_id: str, user_key: bytes
) -> None:
    chats = connection.execute(
        "SELECT id, title, title_encrypted, title_key_scope FROM chats "
        "WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    for chat in chats:
        if chat["title_encrypted"] and chat["title_key_scope"] == "user":
            continue
        title = decrypt_stored_text(
            chat["title"],
            chat["title_encrypted"],
            chat["title_key_scope"],
            user_key,
            title_aad(user_id, chat["id"]),
        )
        connection.execute(
            "UPDATE chats SET title = ?, title_encrypted = 1, title_key_scope = 'user' "
            "WHERE id = ?",
            (
                encrypt_blob(user_key, title.encode("utf-8"), title_aad(user_id, chat["id"])),
                chat["id"],
            ),
        )

    messages = connection.execute(
        "SELECT id, chat_id, content, content_encrypted, content_key_scope "
        "FROM messages WHERE chat_id IN (SELECT id FROM chats WHERE user_id = ?)",
        (user_id,),
    ).fetchall()
    for message in messages:
        if message["content_encrypted"] and message["content_key_scope"] == "user":
            continue
        content = decrypt_stored_text(
            message["content"],
            message["content_encrypted"],
            message["content_key_scope"],
            user_key,
            message_aad(user_id, message["chat_id"], message["id"]),
        )
        connection.execute(
            "UPDATE messages SET content = ?, content_encrypted = 1, "
            "content_key_scope = 'user' WHERE id = ?",
            (
                encrypt_blob(
                    user_key,
                    content.encode("utf-8"),
                    message_aad(user_id, message["chat_id"], message["id"]),
                ),
                message["id"],
            ),
        )


def encrypt_legacy_storage(connection: sqlite3.Connection) -> None:
    """Encrypt old plaintext rows before the first user login.

    Those rows are first protected with a key derived from the server secret.
    At the next successful login they are re-encrypted with the user's data
    key, which is itself protected by the user's password.
    """
    legacy_key = legacy_storage_key()
    chats = connection.execute(
        "SELECT id, user_id, title FROM chats WHERE title_encrypted = 0"
    ).fetchall()
    for chat in chats:
        connection.execute(
            "UPDATE chats SET title = ?, title_encrypted = 1, title_key_scope = 'server' "
            "WHERE id = ?",
            (
                encrypt_blob(
                    legacy_key,
                    str(chat["title"]).encode("utf-8"),
                    title_aad(chat["user_id"], chat["id"]),
                ),
                chat["id"],
            ),
        )

    messages = connection.execute(
        "SELECT messages.id, messages.chat_id, messages.content, chats.user_id "
        "FROM messages JOIN chats ON chats.id = messages.chat_id "
        "WHERE messages.content_encrypted = 0"
    ).fetchall()
    for message in messages:
        connection.execute(
            "UPDATE messages SET content = ?, content_encrypted = 1, "
            "content_key_scope = 'server' WHERE id = ?",
            (
                encrypt_blob(
                    legacy_key,
                    str(message["content"]).encode("utf-8"),
                    message_aad(message["user_id"], message["chat_id"], message["id"]),
                ),
                message["id"],
            ),
        )


def init_database() -> None:
    with db_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                encryption_salt TEXT,
                wrapped_data_key TEXT
            );

            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT 'Neuer Chat',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                title_encrypted INTEGER NOT NULL DEFAULT 0,
                title_key_scope TEXT NOT NULL DEFAULT 'plain'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                content_encrypted INTEGER NOT NULL DEFAULT 0,
                content_key_scope TEXT NOT NULL DEFAULT 'plain'
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                wrapped_data_key TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS chats_user_updated
                ON chats(user_id, updated_at DESC);
            CREATE INDEX IF NOT EXISTS messages_chat_created
                ON messages(chat_id, created_at ASC);
            CREATE INDEX IF NOT EXISTS sessions_expires
                ON sessions(expires_at);
            """
        )

        migrations = {
            "users": {
                "encryption_salt": "TEXT",
                "wrapped_data_key": "TEXT",
            },
            "chats": {
                "title_encrypted": "INTEGER NOT NULL DEFAULT 0",
                "title_key_scope": "TEXT NOT NULL DEFAULT 'plain'",
            },
            "messages": {
                "content_encrypted": "INTEGER NOT NULL DEFAULT 0",
                "content_key_scope": "TEXT NOT NULL DEFAULT 'plain'",
            },
        }
        for table, columns in migrations.items():
            existing = {
                row["name"] for row in connection.execute(f"PRAGMA table_info({table})")
            }
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(
                        f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                    )

        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now(),))
        encrypt_legacy_storage(connection)


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        current = time.monotonic()
        cutoff = current - window_seconds
        with self._lock:
            events = [event for event in self._events.get(key, []) if event > cutoff]
            allowed = len(events) < limit
            if allowed:
                events.append(current)
            self._events[key] = events
            if len(self._events) > 10_000:
                self._events = {
                    event_key: event_values
                    for event_key, event_values in self._events.items()
                    if event_values and event_values[-1] > current - 900
                }
            return allowed


API_LIMITER = SlidingWindowLimiter()
AUTH_LIMITER = SlidingWindowLimiter()


def cookie_value(handler: BaseHTTPRequestHandler, name: str) -> str | None:
    raw = handler.headers.get("Cookie", "")
    cookies = http.cookies.SimpleCookie()
    try:
        cookies.load(raw)
    except http.cookies.CookieError:
        return None
    morsel = cookies.get(name)
    return morsel.value if morsel else None


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def client_identifier(handler: BaseHTTPRequestHandler) -> str:
    if TRUST_PROXY:
        forwarded = handler.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()[:128] or "unknown"
    return handler.client_address[0]


def user_payload(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {"id": row["id"], "username": row["username"]}


class Handler(BaseHTTPRequestHandler):
    server_version = "HelmutKI/2.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_json(
        self,
        payload: dict,
        status: int = HTTPStatus.OK,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int) -> None:
        self.send_json({"error": message}, status)

    def read_json(self, max_bytes: int = MAX_REQUEST_BYTES) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Ungültige Anfrage.") from error
        if content_length < 0 or content_length > max_bytes:
            raise ValueError("Anfrage ist zu groß.")
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError as error:
            raise ValueError("Ungültige Anfrage.") from error
        if not isinstance(payload, dict):
            raise ValueError("Ungültige Anfrage.")
        return payload

    def auth_cookie(self, token: str, expires: int | None = None) -> str:
        cookie = http.cookies.SimpleCookie()
        cookie["helmut_auth"] = token
        cookie["helmut_auth"]["path"] = "/"
        cookie["helmut_auth"]["httponly"] = True
        cookie["helmut_auth"]["samesite"] = "Lax"
        cookie["helmut_auth"]["max-age"] = "0" if expires is not None else str(SESSION_TTL)
        forwarded_https = self.headers.get("X-Forwarded-Proto", "").lower() == "https"
        if COOKIE_SECURE == "true" or (COOKIE_SECURE == "auto" and TRUST_PROXY and forwarded_https):
            cookie["helmut_auth"]["secure"] = True
        if expires is not None:
            cookie["helmut_auth"]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
        return cookie.output(header="").strip()

    def create_session(
        self, connection: sqlite3.Connection, user_id: str, data_key: bytes
    ) -> str:
        if SESSION_SECRET is None:
            raise RuntimeError("HELMUT_SESSION_SECRET ist nicht eingerichtet.")
        token = secrets.token_urlsafe(32)
        timestamp = now()
        connection.execute(
            "INSERT INTO sessions(token_hash, user_id, wrapped_data_key, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                token_hash(token),
                user_id,
                encrypt_blob(SESSION_SECRET, data_key, session_key_aad(user_id)),
                timestamp,
                timestamp + SESSION_TTL,
            ),
        )
        return token

    def current_context(
        self, connection: sqlite3.Connection
    ) -> tuple[sqlite3.Row, bytes] | None:
        token = cookie_value(self, "helmut_auth")
        if not token or SESSION_SECRET is None:
            return None
        row = connection.execute(
            "SELECT users.id, users.username, users.password_hash, "
            "sessions.wrapped_data_key, sessions.expires_at "
            "FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ?",
            (token_hash(token),),
        ).fetchone()
        if row is None:
            return None
        if row["expires_at"] <= now():
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))
            return None
        try:
            data_key = decrypt_blob(
                SESSION_SECRET,
                row["wrapped_data_key"],
                session_key_aad(row["id"]),
            )
        except (ValueError, TypeError):
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))
            return None
        return row, data_key

    def require_context(
        self, connection: sqlite3.Connection
    ) -> tuple[sqlite3.Row, bytes] | None:
        context = self.current_context(connection)
        if context is None:
            self.send_error_json("Bitte zuerst anmelden.", HTTPStatus.UNAUTHORIZED)
        return context

    def apply_api_limit(self, route: str) -> bool:
        if not route.startswith("/api/"):
            return True
        if API_LIMITER.allow(f"api:{client_identifier(self)}", 180, 60):
            return True
        self.send_json(
            {"error": "Zu viele Anfragen. Bitte kurz warten."},
            HTTPStatus.TOO_MANY_REQUESTS,
            {"Retry-After": "60"},
        )
        return False

    def apply_auth_limit(self, route: str) -> bool:
        if route not in {"/api/auth/login", "/api/auth/register"}:
            return True
        key = f"auth:{route}:{client_identifier(self)}"
        if AUTH_LIMITER.allow(key, 20, 600):
            return True
        self.send_json(
            {"error": "Zu viele Anmeldeversuche. Bitte in einigen Minuten erneut versuchen."},
            HTTPStatus.TOO_MANY_REQUESTS,
            {"Retry-After": "600"},
        )
        return False

    def do_GET(self) -> None:  # noqa: N802
        route = urlsplit(self.path).path
        if not self.apply_api_limit(route):
            return
        if route == "/api/auth/status":
            with db_connection() as connection:
                context = self.current_context(connection)
                user = context[0] if context else None
                self.send_json(
                    {
                        "authenticated": user is not None,
                        "user": user_payload(user),
                        "registration_enabled": password_configured(),
                        "model": BROWSER_MODEL,
                    }
                )
            return

        if route == "/api/chats":
            with db_connection() as connection:
                context = self.require_context(connection)
                if context is None:
                    return
                user, data_key = context
                chats = connection.execute(
                    "SELECT id, user_id, title, created_at, updated_at, "
                    "title_encrypted, title_key_scope FROM chats "
                    "WHERE user_id = ? ORDER BY updated_at DESC",
                    (user["id"],),
                ).fetchall()
                self.send_json(
                    {"chats": [self.chat_payload(chat, user["id"], data_key) for chat in chats]}
                )
            return

        chat_id = self.chat_route(route, "GET")
        if chat_id is not None:
            with db_connection() as connection:
                context = self.require_context(connection)
                if context is None:
                    return
                user, data_key = context
                chat = self.owned_chat(connection, chat_id, user["id"])
                if chat is None:
                    self.send_error_json("Chat nicht gefunden.", HTTPStatus.NOT_FOUND)
                    return
                messages = connection.execute(
                    "SELECT id, chat_id, role, content, created_at, "
                    "content_encrypted, content_key_scope FROM messages "
                    "WHERE chat_id = ? ORDER BY created_at ASC, id ASC",
                    (chat_id,),
                ).fetchall()
                try:
                    message_payloads = [
                        self.message_payload(message, user["id"], data_key)
                        for message in messages
                    ]
                    chat_payload = self.chat_payload(chat, user["id"], data_key)
                except (ValueError, TypeError):
                    self.send_error_json("Chat konnte nicht entschlüsselt werden.", HTTPStatus.INTERNAL_SERVER_ERROR)
                    return
                self.send_json({"chat": chat_payload, "messages": message_payloads})
            return

        if route.startswith("/api/"):
            self.send_error_json("Nicht gefunden.", HTTPStatus.NOT_FOUND)
            return
        self.serve_static()

    def do_HEAD(self) -> None:  # noqa: N802
        self.serve_static(head_only=True)

    def do_POST(self) -> None:  # noqa: N802
        route = urlsplit(self.path).path
        if not self.apply_api_limit(route) or not self.apply_auth_limit(route):
            return
        try:
            payload = self.read_json()
        except ValueError as error:
            self.send_error_json(str(error), HTTPStatus.BAD_REQUEST)
            return

        if route == "/api/auth/register":
            self.register(payload)
            return
        if route == "/api/auth/login":
            self.login(payload)
            return
        if route == "/api/auth/logout":
            token = cookie_value(self, "helmut_auth")
            with db_connection() as connection:
                if token:
                    connection.execute(
                        "DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),)
                    )
            self.send_json(
                {"ok": True},
                extra_headers={"Set-Cookie": self.auth_cookie("", expires=0)},
            )
            return
        if route == "/api/chats":
            self.create_chat(payload)
            return

        chat_id = self.chat_route(route, "POST")
        if chat_id is not None and route.endswith("/messages"):
            self.create_message(chat_id, payload)
            return
        self.send_error_json("Nicht gefunden.", HTTPStatus.NOT_FOUND)

    def do_PATCH(self) -> None:  # noqa: N802
        route = urlsplit(self.path).path
        if not self.apply_api_limit(route):
            return
        try:
            payload = self.read_json()
        except ValueError as error:
            self.send_error_json(str(error), HTTPStatus.BAD_REQUEST)
            return
        chat_id = self.chat_route(route, "PATCH")
        if chat_id is None:
            self.send_error_json("Nicht gefunden.", HTTPStatus.NOT_FOUND)
            return
        with db_connection() as connection:
            context = self.require_context(connection)
            if context is None:
                return
            user, data_key = context
            if self.owned_chat(connection, chat_id, user["id"]) is None:
                self.send_error_json("Chat nicht gefunden.", HTTPStatus.NOT_FOUND)
                return
            title = str(payload.get("title", "")).strip()[:120]
            if not title:
                self.send_error_json("Titel fehlt.", HTTPStatus.BAD_REQUEST)
                return
            connection.execute(
                "UPDATE chats SET title = ?, title_encrypted = 1, title_key_scope = 'user', "
                "updated_at = ? WHERE id = ?",
                (
                    encrypt_blob(data_key, title.encode("utf-8"), title_aad(user["id"], chat_id)),
                    now(),
                    chat_id,
                ),
            )
            self.send_json({"ok": True, "title": title})

    def do_DELETE(self) -> None:  # noqa: N802
        route = urlsplit(self.path).path
        if not self.apply_api_limit(route):
            return
        chat_id = self.chat_route(route, "DELETE")
        if chat_id is None:
            self.send_error_json("Nicht gefunden.", HTTPStatus.NOT_FOUND)
            return
        with db_connection() as connection:
            context = self.require_context(connection)
            if context is None:
                return
            user, _data_key = context
            if self.owned_chat(connection, chat_id, user["id"]) is None:
                self.send_error_json("Chat nicht gefunden.", HTTPStatus.NOT_FOUND)
                return
            connection.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            self.send_json({"ok": True})

    @staticmethod
    def chat_route(route: str, method: str) -> str | None:
        parts = [part for part in route.split("/") if part]
        if len(parts) < 3 or parts[:2] != ["api", "chats"]:
            return None
        if method in {"GET", "PATCH", "DELETE"} and len(parts) == 3:
            return parts[2]
        if method == "POST" and len(parts) == 4 and parts[3] == "messages":
            return parts[2]
        return None

    @staticmethod
    def owned_chat(
        connection: sqlite3.Connection, chat_id: str, user_id: str
    ) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT id, user_id, title, created_at, updated_at, title_encrypted, "
            "title_key_scope FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, user_id),
        ).fetchone()

    @staticmethod
    def chat_payload(row: sqlite3.Row, user_id: str, data_key: bytes) -> dict:
        title = decrypt_stored_text(
            row["title"],
            row["title_encrypted"],
            row["title_key_scope"],
            data_key,
            title_aad(user_id, row["id"]),
        )
        return {
            "id": row["id"],
            "title": title,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def message_payload(row: sqlite3.Row, user_id: str, data_key: bytes) -> dict:
        content = decrypt_stored_text(
            row["content"],
            row["content_encrypted"],
            row["content_key_scope"],
            data_key,
            message_aad(user_id, row["chat_id"], row["id"]),
        )
        return {
            "id": row["id"],
            "role": row["role"],
            "content": content,
            "created_at": row["created_at"],
        }

    def register(self, payload: dict) -> None:
        if not password_configured():
            self.send_error_json(
                "Die Registrierung ist noch nicht eingerichtet.",
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        invite_password = str(payload.get("invite_password", ""))
        username = str(payload.get("username", "")).strip().lower()
        password = str(payload.get("password", ""))
        password_confirm = str(payload.get("password_confirm", ""))
        terms_accepted = str(payload.get("terms_accepted", "")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not hmac.compare_digest(
            invite_password.encode("utf-8"), INVITE_PASSWORD.encode("utf-8")
        ):
            self.send_error_json("Einladungspasswort ist falsch.", HTTPStatus.UNAUTHORIZED)
            return
        if not terms_accepted:
            self.send_error_json(
                "Bitte AGB und Datenschutzerklärung akzeptieren.", HTTPStatus.BAD_REQUEST
            )
            return
        if not USERNAME_RE.fullmatch(username):
            self.send_error_json(
                "Benutzername: 3–64 Zeichen, nur Buchstaben, Zahlen und . _ + @ -.",
                HTTPStatus.BAD_REQUEST,
            )
            return
        if len(password) < 8 or len(password) > 128:
            self.send_error_json(
                "Das persönliche Passwort muss 8–128 Zeichen lang sein.",
                HTTPStatus.BAD_REQUEST,
            )
            return
        if password != password_confirm:
            self.send_error_json("Die Passwörter stimmen nicht überein.", HTTPStatus.BAD_REQUEST)
            return

        user_id = secrets.token_urlsafe(18)
        salt = secrets.token_bytes(16)
        data_key = secrets.token_bytes(32)
        wrapped_data_key = encrypt_blob(
            password_key(password, salt), data_key, user_key_aad(user_id)
        )
        try:
            with db_connection() as connection:
                connection.execute(
                    "INSERT INTO users(id, username, password_hash, created_at, "
                    "encryption_salt, wrapped_data_key) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        user_id,
                        username,
                        make_password_hash(password),
                        now(),
                        encode_blob(salt),
                        wrapped_data_key,
                    ),
                )
                token = self.create_session(connection, user_id, data_key)
        except sqlite3.IntegrityError:
            self.send_error_json("Dieser Benutzername ist bereits vergeben.", HTTPStatus.CONFLICT)
            return
        self.send_json(
            {"ok": True, "user": {"id": user_id, "username": username}},
            extra_headers={"Set-Cookie": self.auth_cookie(token)},
        )

    def login(self, payload: dict) -> None:
        username = str(payload.get("username", "")).strip().lower()
        password = str(payload.get("password", ""))
        try:
            with db_connection() as connection:
                user = connection.execute(
                    "SELECT id, username, password_hash, encryption_salt, wrapped_data_key "
                    "FROM users WHERE username = ? COLLATE NOCASE",
                    (username,),
                ).fetchone()
                if user is None or not verify_password(password, user["password_hash"]):
                    self.send_error_json(
                        "Benutzername oder Passwort ist falsch.", HTTPStatus.UNAUTHORIZED
                    )
                    return
                data_key = user_data_key_for_password(connection, user["id"], password)
                token = self.create_session(connection, user["id"], data_key)
        except (ValueError, TypeError, RuntimeError):
            self.send_error_json(
                "Das Konto konnte nicht sicher geöffnet werden.",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return
        self.send_json(
            {"ok": True, "user": {"id": user["id"], "username": user["username"]}},
            extra_headers={"Set-Cookie": self.auth_cookie(token)},
        )

    def create_chat(self, payload: dict) -> None:
        with db_connection() as connection:
            context = self.require_context(connection)
            if context is None:
                return
            user, data_key = context
            chat_count = connection.execute(
                "SELECT COUNT(*) AS count FROM chats WHERE user_id = ?", (user["id"],)
            ).fetchone()["count"]
            if chat_count >= MAX_CHATS_PER_USER:
                self.send_error_json(
                    "Das Chatlimit dieses Kontos ist erreicht.",
                    HTTPStatus.INSUFFICIENT_STORAGE,
                )
                return
            title = str(payload.get("title", "Neuer Chat")).strip()[:120] or "Neuer Chat"
            chat_id = secrets.token_urlsafe(18)
            timestamp = now()
            connection.execute(
                "INSERT INTO chats(id, user_id, title, created_at, updated_at, "
                "title_encrypted, title_key_scope) VALUES (?, ?, ?, ?, ?, 1, 'user')",
                (
                    chat_id,
                    user["id"],
                    encrypt_blob(data_key, title.encode("utf-8"), title_aad(user["id"], chat_id)),
                    timestamp,
                    timestamp,
                ),
            )
            self.send_json(
                {
                    "chat": {
                        "id": chat_id,
                        "title": title,
                        "created_at": timestamp,
                        "updated_at": timestamp,
                    }
                },
                HTTPStatus.CREATED,
            )

    def create_message(self, chat_id: str, payload: dict) -> None:
        role = str(payload.get("role", ""))
        content = str(payload.get("content", "")).strip()
        if role not in {"user", "assistant"}:
            self.send_error_json("Ungültige Nachrichtenrolle.", HTTPStatus.BAD_REQUEST)
            return
        if not content or len(content) > MAX_MESSAGE_CHARS:
            self.send_error_json("Nachricht fehlt oder ist zu lang.", HTTPStatus.BAD_REQUEST)
            return
        with db_connection() as connection:
            context = self.require_context(connection)
            if context is None:
                return
            user, data_key = context
            chat = self.owned_chat(connection, chat_id, user["id"])
            if chat is None:
                self.send_error_json("Chat nicht gefunden.", HTTPStatus.NOT_FOUND)
                return
            chat_message_count = connection.execute(
                "SELECT COUNT(*) AS count FROM messages WHERE chat_id = ?", (chat_id,)
            ).fetchone()["count"]
            user_message_count = connection.execute(
                "SELECT COUNT(*) AS count FROM messages "
                "WHERE chat_id IN (SELECT id FROM chats WHERE user_id = ?)",
                (user["id"],),
            ).fetchone()["count"]
            if chat_message_count >= MAX_MESSAGES_PER_CHAT or user_message_count >= MAX_MESSAGES_PER_USER:
                self.send_error_json(
                    "Das Nachrichtenlimit dieses Kontos ist erreicht.",
                    HTTPStatus.INSUFFICIENT_STORAGE,
                )
                return

            try:
                current_title = self.chat_payload(chat, user["id"], data_key)["title"]
            except (ValueError, TypeError):
                self.send_error_json(
                    "Chat konnte nicht entschlüsselt werden.",
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            generated_title = None
            if role == "user" and current_title == "Neuer Chat":
                generated_title = " ".join(content.split())[:54] or "Neuer Chat"

            timestamp = now()
            cursor = connection.execute(
                "INSERT INTO messages(chat_id, role, content, created_at, "
                "content_encrypted, content_key_scope) VALUES (?, ?, '', ?, 1, 'user')",
                (chat_id, role, timestamp),
            )
            message_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE messages SET content = ? WHERE id = ?",
                (
                    encrypt_blob(
                        data_key,
                        content.encode("utf-8"),
                        message_aad(user["id"], chat_id, message_id),
                    ),
                    message_id,
                ),
            )
            if generated_title is not None:
                connection.execute(
                    "UPDATE chats SET title = ?, title_encrypted = 1, title_key_scope = 'user', "
                    "updated_at = ? WHERE id = ?",
                    (
                        encrypt_blob(
                            data_key,
                            generated_title.encode("utf-8"),
                            title_aad(user["id"], chat_id),
                        ),
                        timestamp,
                        chat_id,
                    ),
                )
            else:
                connection.execute(
                    "UPDATE chats SET updated_at = ? WHERE id = ?", (timestamp, chat_id)
                )
            self.send_json(
                {
                    "message": {
                        "id": message_id,
                        "role": role,
                        "content": content,
                        "created_at": timestamp,
                    }
                },
                HTTPStatus.CREATED,
            )

    def serve_static(self, head_only: bool = False) -> None:
        request_path = unquote(urlsplit(self.path).path)
        relative_text = request_path.lstrip("/") or "chat.html"
        relative_path = Path(relative_text)
        parts = relative_path.parts
        if (
            not parts
            or any(part in {"", ".", ".."} or part.startswith(".") for part in parts)
            or (len(parts) == 1 and parts[0] not in PUBLIC_ROOT_FILES)
            or (len(parts) > 1 and tuple(parts[:2]) not in PUBLIC_ROOT_DIRS)
        ):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        candidate = (ROOT / relative_path).resolve()
        if ROOT not in candidate.parents and candidate != ROOT:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if candidate.is_dir() or not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        file_size = candidate.stat().st_size
        start = 0
        end = file_size - 1
        status = HTTPStatus.OK
        range_header = self.headers.get("Range", "")
        if range_header.startswith("bytes=") and "," not in range_header:
            range_value = range_header.removeprefix("bytes=").strip()
            range_start, separator, range_end = range_value.partition("-")
            try:
                if not separator:
                    raise ValueError
                if range_start:
                    start = int(range_start)
                    end = int(range_end) if range_end else end
                elif range_end:
                    suffix_length = int(range_end)
                    start = max(file_size - suffix_length, 0)
                else:
                    raise ValueError
                if start < 0 or start >= file_size or end < start:
                    raise ValueError
                end = min(end, file_size - 1)
                status = HTTPStatus.PARTIAL_CONTENT
            except ValueError:
                self.send_response(HTTPStatus.RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return
        content_length = end - start + 1
        self.send_response(status)
        self.send_header(
            "Content-Type",
            f"{content_type}; charset=utf-8"
            if content_type.startswith(("text/", "application/javascript", "application/json"))
            else content_type,
        )
        self.send_header("Content-Length", str(content_length))
        self.send_header("Accept-Ranges", "bytes")
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header(
            "Cache-Control",
            "public, max-age=31536000, immutable"
            if candidate.suffix == ".gguf"
            else "no-cache",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'wasm-unsafe-eval' 'unsafe-eval' "
            "https://esm.run https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com; img-src 'self' data:; connect-src 'self' "
            "https://esm.run https://cdn.jsdelivr.net https://huggingface.co https://*.hf.co "
            "https://cdn-lfs.huggingface.co https://raw.githubusercontent.com; worker-src 'self' blob:; "
            "font-src 'self' https://fonts.gstatic.com; frame-ancestors 'self'",
        )
        self.end_headers()
        if head_only:
            return
        with candidate.open("rb") as file_handle:
            file_handle.seek(start)
            remaining = content_length
            while remaining:
                chunk = file_handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)


if __name__ == "__main__":
    if SESSION_SECRET is None:
        raise SystemExit(
            "HELMUT_SESSION_SECRET fehlt oder ist ungültig. "
            "Erzeuge einen stabilen 32-Byte-Schlüssel und hinterlege ihn in der Environment-Datei."
        )
    init_database()
    if not password_configured():
        print("WARNUNG: Setze HELMUT_CHAT_PASSWORD auf ein Einladungspasswort mit mindestens 8 Zeichen.")
    print(f"Helmut-KI läuft auf http://{HOST}:{PORT}")
    print(f"Browser-Modell: {BROWSER_MODEL}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
