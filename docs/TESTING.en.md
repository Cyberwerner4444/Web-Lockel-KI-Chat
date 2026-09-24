# Testing and public-release checklist

## Automated checks

Run in the repository:

```bash
python -m unittest discover -s tests -v
python tools/public_audit.py
python -m py_compile server.py
```

The tests use a temporary SQLite file and a random local session key. They do not modify a production database.

## Functional checks

- `/` opens the chat; `/chat.html`, `/legal.html`, and the explicitly allowed legal texts return HTTP 200.
- Former landing, support, mining, logo, and legacy legal pages return 404 and are absent from the repository.
- Disallowed paths, `..`, hidden files, and unlisted root files return 404.
- Range requests for large static files return `206` with the correct `Content-Range`.
- Status without a cookie reports `authenticated: false`.
- Registration requires invitation, valid username, matching password, and consent.
- Login sets a cookie; logout deletes the session and expires the cookie.
- User A can create, rename, message, and delete a chat.
- User B receives 404 and no messages for User A’s chats.
- SQLite does not contain the plaintext test message.
- Rate and message/chat limits cannot be bypassed.
- Model URLs, Mammoth URL, CSP, and runtime pins are reachable and match `docs/MODELS.en.md`.

## Browser checks

In a current browser test:

1. Registration and login.
2. Load a model, generate a response, and reload history.
3. Rename, create, and delete chats.
4. Logout and access without a session.
5. Toggle WebGPU and CPU/WASM fallback.
6. Change context size and unload/reload a model.
7. Open TXT, MD, CSV, JSON, and DOCX locally.
8. Do not accidentally paste document content into the normal chat.
9. Test responsive layout and keyboard interaction on desktop/mobile.

## Anonymization checks

- No real names, emails, addresses, domains, IPs, or hostnames.
- No personal links or production infrastructure values.
- No `.env`, database, session file, certificates, logs, or private keys.
- No old commit email addresses in public history.
- No large local models or unreviewed binary assets.
- No private remote URL in the public repository’s `.git/config`.
- Legal files contain only deliberate placeholders.

## Upload gate

Upload only when:

- all automated checks pass;
- the browser smoke test passes;
- every public document has been read and reconciled with code/deployment;
- licenses and images have been reviewed;
- a new anonymized Git history has been created;
- the target repository and push permission are confirmed.

After pushing: create a fresh clone without local legacy files, rerun the audit, and check GitHub visibility, file list, Actions/secrets, and default branch.
