# Helmut-KI – Privacy notice (template)

> This describes the reference implementation and is a fillable template, not legal advice. Before launch, document the actual operator, hosting, logs, third parties, retention, deletion, and applicable law.

## Required details before launch

- Controller/operator: `[NAME / ORGANIZATION]`
- address: `[ENTER]`
- privacy contact: `[EMAIL]`
- domain and hosting: `[ENTER]`
- server location and log retention: `[ENTER]`
- version and effective date: `[ENTER]`

## 1. Service access

Depending on Python, the reverse proxy, operating system, hosting, and monitoring, a request may involve an IP/network identifier, timestamp, URL, HTTP method, status, data size, user agent, referrer, and error/security records. The actual logging and deletion period must be reviewed and specified before launch.

## 2. Accounts and sign-in

The application processes a chosen username, random account ID, password hash, and timestamps. Personal passwords are not stored in plaintext. The registration invitation is checked server-side and must be kept in a protected environment variable.

Successful sign-in creates a random session token. SQLite stores its hash and an encrypted reference to the user data key. The `helmut_auth` cookie is HttpOnly and SameSite=Lax; it is Secure under HTTPS. Its default lifetime is 30 days or until logout/expiry.

## 3. Chat data

Chat IDs, account IDs, titles, roles, messages, and timestamps are stored to provide account-specific history. Every access checks ownership. Titles and messages are encrypted with AES-256-GCM; the personal data key is protected using the account password. Server-side encryption does not replace a tested backup, deletion, and access-control process.

## 4. Local AI and documents

Model inference runs in the browser. The reference application has no server-side generation endpoint. Browser runtimes, WASM files, and model weights may be downloaded from the third parties listed in the model documentation. Those providers may observe technical download data such as IP address, time, user agent, requested file, and range requests; prompts are not sent to them as inference requests.

TXT, MD, CSV, and DOCX files are read using browser file APIs only after user selection. File contents are not uploaded to the chat server. Manually copying text into the normal chat subjects it to chat processing and storage.

## 5. Browser storage

Model selection, context limit, and local style preference may be stored in `localStorage`. These are not account settings. The reference code does not store document contents, document prompts, or local document output in `localStorage`, SQLite, or chat history.

## 6. Third parties

The public source lists runtime, font, and model sources in `docs/MODELS.en.md`. Before launch, assess each provider’s purpose, recipients, countries, legal basis, transfer mechanism, license, and retention. Any analytics, support, backup, payment, or other services added later must be documented.

## 7. Retention, rights, and deletion

Before launch, specify retention periods for sessions, accounts, chats, backups, server logs, and browser caches. Contact for access, correction, deletion, restriction, objection, portability, and security reports: `[CONTACT]`. Define identity checks, deadlines, and statutory retention.

## 8. Security measures

The implementation uses PBKDF2-HMAC-SHA-256 password hashes, AES-256-GCM chat encryption, random tokens, ownership checks, request/message limits, a static-file allowlist, path-traversal protection, restrictive SQLite permissions, and safe DOM output. HTTPS, key management, backups, updates, monitoring, and operating-system access remain deployment responsibilities.

## 9. Do not submit secrets

Do not enter passwords, API keys, seed phrases, private keys, complete payment details, or highly sensitive personal data into the app, issues, logs, or Git. The application is not certified as a high-security or compliance system.

## 10. Review and updates

Update this notice when code, hosting, logs, cookies, models, CDNs, third parties, purposes, laws, or deletion procedures change. Obtain qualified review for the service’s actual jurisdiction before publication.
