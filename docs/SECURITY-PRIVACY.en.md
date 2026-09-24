# Security, privacy, and anonymization

## Public scope

The public repository is a source template, not a production instance. It contains no real identity, domain, contact address, wallet, referral ID, server address, database, session secret, environment file, model weights, or old private Git history.

## Account security

- Registration is gated by a server-side invitation password.
- User passwords are hashed with PBKDF2-HMAC-SHA-256 and a random salt.
- Personal data is encrypted through a random 32-byte data key.
- Titles and messages use AES-256-GCM with contextual associated data.
- Session tokens are random; SQLite stores only their SHA-256 hashes.
- The cookie is HttpOnly and SameSite=Lax; enable `Secure` for HTTPS.
- Login and API requests use in-memory sliding-window limits.
- User and chat ownership is checked before every access.

## What the server can still see

A running server can serve valid sessions and decrypt their chat data. Encryption primarily protects SQLite files and backups when the key is unavailable. Proxy, web-server, OS, backup, and browser logs may contain additional technical data. Each real deployment must describe this in its privacy notice.

## Data flow

- Model inference: local in the browser.
- Persistence: the browser sends user/assistant messages to its own API.
- Local documents: Browser File API, no upload endpoint.
- Model/runtime downloads: a CDN/repository may see technical download metadata.
- Public release: no real operator or payment data.

## Anonymization audit

Before every public push:

1. Run `python tools/public_audit.py`.
2. Inspect `git ls-files` for databases, environment files, keys, logs, and oversized binaries.
3. Inspect `git log --format='%an <%ae>'`; use a new history for the public release.
4. Search for domain, email, IP, wallet, referral, server, and hosting patterns.
5. Review image/archive metadata and licensing.
6. Review legal placeholders against the actual deployment configuration.

## Security limits and remaining work

The server is intentionally small and does not use a full web framework. Before internet operation, define TLS/proxy, firewall, OS updates, encrypted backups, secret rotation, account deletion, monitoring, alerting, CSRF/origin strategy, dependency updates, and a qualified security review. “Encrypted in SQLite” is not a complete security or privacy guarantee.

Do not put security reports in public issues. Add a private security contact to the deployment instance before release.
