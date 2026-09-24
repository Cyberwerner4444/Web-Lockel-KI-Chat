# Betrieb, Datenquellen und Deployment

## Welche Daten werden woher benötigt?

| Daten | Woher | Wo eintragen/ablegen | Öffentlich committen? |
| --- | --- | --- | --- |
| Python | python.org oder Distribution | System/virtuelles Environment | nein |
| Serverpaket | `requirements.txt` / PyPI | `.venv` | nur Dateiname/Constraint |
| Session-Schlüssel | lokal mit CSPRNG erzeugen | geschützte Secret-Datei oder Environment | nein |
| Registrierungseinladung | Betreiber selbst wählen | geschützte Environment | nein |
| Domain/TLS | eigene Domain und DNS-Anbieter | private Caddy-Konfiguration | nur `example.com`-Vorlage |
| SQLite-Datenbank | entsteht beim Start | außerhalb des Webroots | nein |
| Browser-Runtimes | offizielle npm/CDN-Quellen | Browser-Cache | URL/Version ja, Cache nein |
| Modellgewichte | offizielle Modellseite und Lizenz prüfen | Browser-Cache oder private `assets/models/` | normalerweise nein |
| Rechtsangaben | Betreiberperson und fachkundige Prüfung | Chat-Rechtsvorlagen | echte private Werte erst in Deployment |

## Lokales Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Erzeuge einen Schlüssel ausschließlich lokal:

```bash
python -c 'import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'
```

Setze anschließend `HELMUT_SESSION_SECRET` oder `HELMUT_SESSION_SECRET_FILE` sowie ein eigenes `HELMUT_CHAT_PASSWORD`. Die SQLite-Datei wird durch `server.py` angelegt. Für Produktion sollte `HELMUT_DB_PATH` auf ein Verzeichnis zeigen, das der Webserver nicht als statische Datei ausliefert.

`server.py` lädt `.env` nicht automatisch, sondern liest nur die Prozessumgebung. Setze die Variablen mit `export`, lade eine ausgefüllte Shell-Datei ausdrücklich (`set -a; . ./.env; set +a`) oder verwende beim Dienstbetrieb `EnvironmentFile`. Ersetze vor dem Laden sämtliche Platzhalter aus `.env.example`.

## Browserdaten und Modellablauf

1. `/` liefert direkt die Chat-Anwendung (`chat.html`) sowie CSS und JavaScript.
2. Beim Öffnen des Chats fragt der Browser `/api/auth/status` ab.
3. Nach Modellwahl lädt der Browser Runtime und Gewichte aus den in `app.js` eingetragenen Quellen.
4. Das Modell wird im Browsercache gehalten; die Größe und Lizenz stammen aus dem jeweiligen Repository.
5. Prompt und Verlauf werden lokal zur Inferenz zusammengestellt.
6. Für Persistenz sendet der Browser die User- und Assistant-Nachricht an die eigene `/api/chats/.../messages`-API.

Der Server sendet Prompts nicht an WebLLM, Wllama, Hugging Face oder einen anderen Inferenzdienst.

## Caddy mit eigener Domain

`Caddyfile` nutzt absichtlich `example.com`. Vor Verwendung:

1. eigene Domain eintragen;
2. DNS auf den Proxy zeigen lassen;
3. Backend nur an `127.0.0.1:8080` binden;
4. `HELMUT_TRUST_PROXY=true` nur hinter dem eigenen Proxy setzen;
5. `caddy validate --config /etc/caddy/Caddyfile` ausführen;
6. mit HTTPS, Cookie `Secure`, statischen Assets und API testen.

Keine produktive Domain in die Public-Quellfassung zurückschreiben, wenn das Repository anonym bleiben soll.

## Dienstbetrieb

Ein produktiver Dienst sollte unter einem unprivilegierten Benutzer laufen und nur in einem dedizierten Datenverzeichnis schreiben dürfen. Die Environment-Datei, Session-Datei und SQLite-Datei benötigen restriktive Rechte. Backups müssen die Datenbank und den Session-Schlüssel gemeinsam enthalten; der Schlüssel allein kann keine Datenbank wiederherstellen.

## Updates

Vor jedem Update:

- Release- und Sicherheitsmeldungen der Runtime-/Paketquellen lesen;
- Modell- und CDN-URLs mit `HEAD`/Browser prüfen;
- Lizenzen und Größen neu prüfen;
- temporäre Datenbankkopie und Restore testen;
- Tests und Public-Audit ausführen;
- erst danach veröffentlichen.

Versionsquellen und aktuelle Pins stehen in [MODELS.de.md](MODELS.de.md).

## Fehleranalyse

- Login funktioniert nicht: `HELMUT_SESSION_SECRET`, Datenbankpfad, Einladungspasswort und Browser-Cookies prüfen.
- Chat ist leer: Session abgelaufen oder Datenbank/Session-Schlüssel nicht gemeinsam wiederhergestellt.
- Modell lädt nicht: WebGPU, freier RAM/VRAM, Browser-Cache, Range-Requests, Modell-URL und Modelllizenz prüfen.
- DOCX funktioniert nicht: Netzverbindung zum Mammoth-CDN und Browser-Konsole prüfen.
- Proxyproblem: Caddy-Logs, Backend-Port, `HELMUT_TRUST_PROXY` und HTTPS prüfen.
