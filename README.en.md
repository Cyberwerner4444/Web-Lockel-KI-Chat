# Helmut-KI – complete chat system

Helmut-KI is a self-hostable chat application with registration, login, isolated user accounts, personal chat histories, several local browser models, and a document tool. The Python server authenticates accounts and stores chat histories encrypted in SQLite; model inference runs in the browser.

Deutsche Fassung: [README.md](README.md)

## Included

- login, invitation-gated registration, logout, and session cookie;
- per-user ownership model: an account can see only its own chats;
- create, open, rename, delete chats and persist messages;
- PBKDF2-HMAC-SHA-256 password hashes and AES-256-GCM title/message encryption;
- local browser inference through WebLLM/MLC or Wllama/llama.cpp;
- local TXT, MD, CSV, JSON, and DOCX editing with no upload endpoint;
- German chat UI plus complete German/English technical documentation.

This repository contains only the chat system and its required legal and operational documents. It does not contain the public Helmut-KI landing page, support page, mining feature, or logo download page.

## Architecture

```text
Browser
  ├─ HTML/CSS/JavaScript
  ├─ WebLLM + WebGPU for small MLC models
  ├─ Wllama + WASM/WebGPU for GGUF models
  ├─ Browser File API for local documents
  └─ HTTPS/JSON ──> server.py
                         ├─ authentication and rate limits
                         ├─ SQLite: users, sessions, chats, messages
                         └─ no server-side /api/generate endpoint
```

The server receives chat messages only because history is stored per account. The selected model source does not receive prompts as inference requests. See [docs/ARCHITECTURE.en.md](docs/ARCHITECTURE.en.md) for the data flow.

## Local quick start

Requirements: Python 3.10 or newer and a virtual environment.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

`server.py` reads environment variables from its process but does not automatically load `.env`. The `export` commands below set the required values directly. `.env.example` is a template; if you use a file based on it, replace every placeholder first and explicitly load it, for example with `set -a; . ./.env; set +a`.

Generate your own stable 32-byte key and set it in a protected environment:

```bash
export HELMUT_SESSION_SECRET="$(python -c 'import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())')"
export HELMUT_CHAT_PASSWORD='choose-a-long-registration-invitation'
python server.py
```

Open `http://127.0.0.1:8080/` or `http://127.0.0.1:8080/chat.html`.

`HELMUT_CHAT_PASSWORD` is not a user password; it only authorizes new registrations. Users then choose their own personal password. Production secrets must never be committed.

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `HELMUT_HOST` | Python server bind address | `127.0.0.1` |
| `HELMUT_PORT` | local port | `8080` |
| `HELMUT_DB_PATH` | private SQLite file; outside the web root is recommended | `./helmut.sqlite3` |
| `HELMUT_CHAT_PASSWORD` | registration invitation, at least 8 characters | empty/disabled |
| `HELMUT_SESSION_SECRET` | stable URL-safe Base64 key containing 32 bytes | required |
| `HELMUT_SESSION_SECRET_FILE` | alternative file for the 32-byte key | empty |
| `HELMUT_BROWSER_MODEL` | default frontend model ID | Llama 3.2 1B WebLLM ID |
| `HELMUT_TRUST_PROXY` | set `true` only behind a controlled reverse proxy | `false` |
| `HELMUT_COOKIE_SECURE` | `true`, `false`, or `auto` for the session cookie | `auto` |

See [.env.example](.env.example). Protect keys and the database with mode `0600` and back them up together.

## Models and required data

Model weights are not stored in this repository. On first use, the browser downloads the selected artifact from a documented source and then uses its own cache. Large GGUF shards intentionally remain outside Git.

| Purpose | Source/version in code | Required data |
| --- | --- | --- |
| WebGPU models | WebLLM `0.2.85` via `esm.run` | MLC prebuilt model libraries and browser cache |
| GGUF inference | Wllama `3.6.1` via jsDelivr | GGUF file or all shards, plus WASM |
| DOCX text | Mammoth.js `1.12.3` via jsDelivr | runtime only when a DOCX file is opened |
| CPU/GGUF sources | public Hugging Face repositories in `app.js` | model weights and their license/usage terms |
| server encryption | Python `cryptography` `>=50,<51` | installed Python package |

Current URLs, model names, approximate sizes, and license notes are in [docs/MODELS.en.md](docs/MODELS.en.md). Re-check official sources before every release.

## Production operation

1. Fill and legally review placeholders in [AGB.md](AGB.md), [DATENSCHUTZERKLAERUNG.md](DATENSCHUTZERKLAERUNG.md), and [legal.html](legal.html).
2. Configure your own domain and TLS through a reverse proxy such as Caddy. [Caddyfile](Caddyfile) intentionally uses `example.com`.
3. Bind Python only to `127.0.0.1` and store the database outside the public web root.
4. Set your own session secret and registration invitation. Never reuse example values.
5. Set `HELMUT_TRUST_PROXY=true` only when the backend port is reachable exclusively through your own proxy.
6. Protect and back up the SQLite database and session key; never put backups in Git or `assets/`.
7. Before enabling access, verify HTTPS, cookie attributes, rate limits, deletion, logs, model licenses, and legal documents.

See [docs/OPERATIONS.en.md](docs/OPERATIONS.en.md) and its [German version](docs/OPERATIONS.de.md).

## Tests and publication audit

```bash
python -m unittest discover -s tests -v
python tools/public_audit.py
python -m py_compile server.py
```

The integration tests start a temporary server and verify registration and login, account isolation, creating/renaming/deleting chats, encrypted storage, authentication and API rate limits, chat/message quotas, range requests for a large model file, and static path boundaries. They do not run real browser-model inference. `public_audit.py` also checks for known personal/production patterns, private runtime files, and oversized public files.

Complete [docs/TESTING.en.md](docs/TESTING.en.md) before every upload. Upload only after the audit is clean.

## Public anonymization

This public source intentionally contains no:

- real operator, private, or server information;
- production domains, email addresses, referral codes, or wallet addresses;
- SQLite databases, session keys, `.env` files, or model weights;
- private Git remotes or old development commit history;
- unreviewed 3D/download archives.

The public release is published as a new anonymized Git repository with a new history. Runtime data from a private instance stays separate.

## Legal and licensing

This project currently has no `LICENSE` file. Public availability alone does not grant an explicit reuse license; choose a project license before inviting reuse. WebLLM, Wllama, Mammoth.js, Python packages, and model weights have their own licenses. Review runtime/model sources and usage terms before operation. The legal Markdown/HTML files are templates, not reviewed legal advice.

## Further documents

- [Architecture and data flow (DE)](docs/ARCHITECTURE.de.md) · [English](docs/ARCHITECTURE.en.md)
- [Operations and data sources (DE)](docs/OPERATIONS.de.md) · [English](docs/OPERATIONS.en.md)
- [Models and runtime versions (DE)](docs/MODELS.de.md) · [English](docs/MODELS.en.md)
- [Security and privacy (DE)](docs/SECURITY-PRIVACY.de.md) · [English](docs/SECURITY-PRIVACY.en.md)
- [Testing and release checklist (DE)](docs/TESTING.de.md) · [English](docs/TESTING.en.md)
- [Terms (DE)](AGB.md) · [English](TERMS.en.md)
- [Privacy notice (DE)](DATENSCHUTZERKLAERUNG.md) · [English](PRIVACY.en.md)
