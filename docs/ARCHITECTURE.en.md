# Architecture and data flow

## Overview

Helmut-KI separates local browser inference, the chat application, and private history storage:

```text
Browser
  ├── chat.html + chat legal templates
  ├── app.js + styles.css
  ├── WebLLM 0.2.85 or Wllama 3.6.1
  ├── Browser File API + Mammoth.js 1.12.3
  └── JSON over HTTPS
          ↓
      server.py
  ├── static allowlist
  ├── authentication + rate limits
  ├── SQLite users, sessions, chats, messages
  └── no server-side model inference
```

## Frontend

- `chat.html`: registration, login, chat list, messages, model and context controls.
- `app.js`: UI state, API calls, local model runtimes, local documents, and safe DOM output.
- `styles.css`: layout, colors, responsive behavior, and animation.
- `legal.html`, `TERMS.en.md`, `PRIVACY.en.md`: chat-specific legal templates.

## Server and API

`server.py` uses Python’s standard `http.server` and `sqlite3`. The `cryptography` package provides AES-GCM and the other cryptographic primitives.

| Route | Purpose | Authentication |
| --- | --- | --- |
| `GET /api/auth/status` | session state, default model, registration state | no |
| `POST /api/auth/register` | create account and session | invitation in body |
| `POST /api/auth/login` | open account and session | user password |
| `POST /api/auth/logout` | delete session and expire cookie | optional cookie |
| `GET /api/chats` | list own chats | yes |
| `POST /api/chats` | create own chat | yes |
| `GET /api/chats/{id}` | read own chat and messages | yes + ownership check |
| `PATCH /api/chats/{id}` | rename own chat | yes + ownership check |
| `DELETE /api/chats/{id}` | delete own chat | yes + ownership check |
| `POST /api/chats/{id}/messages` | store own user/assistant message | yes + ownership check |

There is intentionally no `/api/generate` or `/api/completions` endpoint.

## Database

- `users`: random ID, username, password hash, creation time, salt, and wrapped data key.
- `sessions`: session-token hash, user ID, wrapped data-key reference, creation and expiry times.
- `chats`: chat ID, owner ID, encrypted title, creation/update times.
- `messages`: message ID, chat ID, role, encrypted content, and timestamp.

The personal data key is wrapped using a key derived from the user password. Sessions wrap the same key with `HELMUT_SESSION_SECRET`, so a restart does not invalidate the session. This is not automatically zero-knowledge: a running server can decrypt data for a valid session.

## Authentication flow

1. Registration checks invitation, username, password length, and consent.
2. The server creates a user ID, salt, and data key.
3. The personal password is stored as a PBKDF2 hash.
4. The data key is encrypted with a password-derived key.
5. A random session is created; only the token hash and wrapped key reference are stored.
6. Each protected endpoint loads the session, checks TTL, and unwraps the data key.

## Local documents

Files are read only after user selection. TXT, MD, CSV, and JSON are read as text; DOCX is converted to raw text with Mammoth.js. Content is not sent through the chat API. The normal message form is separate and intentionally stores messages that the user submits.

## Security boundaries

The implementation limits request sizes, messages/chats, and API/authentication rates, and adds path-traversal protection plus a static-file allowlist. Keep `HELMUT_TRUST_PROXY=false` if clients can reach the backend directly. Production TLS, firewalling, OS updates, encrypted backups, monitoring, and legal processes remain deployment responsibilities.
