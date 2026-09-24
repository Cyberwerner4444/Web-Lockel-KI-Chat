# Operations, data sources, and deployment

## Which data is needed and where does it come from?

| Data | Source | Where to configure/store | Commit publicly? |
| --- | --- | --- | --- |
| Python | python.org or OS distribution | system/virtual environment | no |
| server package | `requirements.txt` / PyPI | `.venv` | filename/constraint only |
| session key | generate locally with a CSPRNG | protected secret file or environment | no |
| registration invitation | choose privately as operator | protected environment | no |
| domain/TLS | your domain and DNS provider | private Caddy configuration | only the `example.com` template |
| SQLite database | created at startup | outside the web root | no |
| browser runtimes | official npm/CDN sources | browser cache | URL/version yes, cache no |
| model weights | official model page and license review | browser cache or private `assets/models/` | normally no |
| legal details | operator and qualified review | chat legal templates | real private values only in deployment |

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Generate a key locally only:

```bash
python -c 'import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'
```

Set `HELMUT_SESSION_SECRET` or `HELMUT_SESSION_SECRET_FILE` and choose a private `HELMUT_CHAT_PASSWORD`. `server.py` creates the SQLite database. In production, set `HELMUT_DB_PATH` to a directory that the static server cannot serve.

`server.py` does not load `.env` automatically; it reads only the process environment. Set variables with `export`, explicitly load a completed shell file (`set -a; . ./.env; set +a`), or use the service manager’s `EnvironmentFile`. Replace every `.env.example` placeholder before loading it.

## Browser data and model flow

1. `/` serves the chat application (`chat.html`) along with CSS and JavaScript.
2. Opening chat calls `/api/auth/status`.
3. After model selection, the browser loads the runtime and weights from the sources listed in `app.js`.
4. The model remains in the browser cache; its size and license come from its repository.
5. Prompt and history are assembled locally for inference.
6. For persistence, the browser sends user and assistant messages to its own `/api/chats/.../messages` API.

The server does not send prompts to WebLLM, Wllama, Hugging Face, or another inference service.

## Caddy with your own domain

`Caddyfile` intentionally uses `example.com`. Before use:

1. replace it with your own domain;
2. point DNS at the proxy;
3. bind the backend only to `127.0.0.1:8080`;
4. set `HELMUT_TRUST_PROXY=true` only behind your own proxy;
5. run `caddy validate --config /etc/caddy/Caddyfile`;
6. test HTTPS, the `Secure` cookie, static assets, and the API.

Do not write a production domain back into the public source if the repository is intended to stay anonymous.

## Service operation

Run production under an unprivileged user with a dedicated writable data directory. The environment file, session file, and SQLite database need restrictive permissions. Backups must contain both database and session key; a key alone cannot restore a database.

## Updates

Before each update:

- read security and release notices for runtimes and packages;
- verify model/CDN URLs with `HEAD` or a browser;
- re-check licenses and sizes;
- test a temporary database copy and restore;
- run tests and the public audit;
- publish only afterward.

Version sources and current pins are in [MODELS.en.md](MODELS.en.md).

## Troubleshooting

- Login fails: check `HELMUT_SESSION_SECRET`, database path, invitation, and browser cookies.
- Chat is empty: the session expired or the database and session key were not restored together.
- Model fails to load: check WebGPU, free RAM/VRAM, browser cache, range requests, model URL, and model license.
- DOCX fails: check network access to the Mammoth CDN and the browser console.
- Proxy failure: check Caddy logs, backend port, `HELMUT_TRUST_PROXY`, and HTTPS.
