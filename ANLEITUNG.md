# Helmut-KI – vollständige deutsche Betriebsanleitung

Diese deutsche Anleitung ist der Einstieg für Entwicklung und Deployment. Die englische Fassung steht in [README.en.md](README.en.md); die Detaildokumente liegen paarweise unter `docs/`.

## 1. Lokale Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Der Server benötigt Python 3.10 oder neuer und `cryptography`. Für Browsermodelle ist ein aktueller Browser mit WebGPU oder CPU/WASM-Unterstützung sowie ausreichend Speicher nötig. Beim ersten Modellstart werden je nach Auswahl mehrere hundert Megabyte bis viele Gigabyte geladen.

## 2. Geheimnisse und Datenbank

Erzeuge für jede Instanz einen eigenen Schlüssel:

```bash
python -c 'import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'
```

Setze den Wert als `HELMUT_SESSION_SECRET` oder speichere ihn in einer Datei mit Modus `0600` und setze `HELMUT_SESSION_SECRET_FILE`. Zusätzlich ist ein eigenes `HELMUT_CHAT_PASSWORD` mit mindestens acht Zeichen nötig, wenn Registrierung erlaubt sein soll. Beide Werte niemals in Git, HTML, JavaScript, Issues, Screenshots oder Logs kopieren.

Wichtig: `server.py` lädt `.env` nicht automatisch. Setze Variablen mit `export`, lade eine selbst ausgefüllte Shell-Datei ausdrücklich (`set -a; . ./.env; set +a`) oder konfiguriere sie als `EnvironmentFile` im Dienstmanager. Die unveränderte `.env.example` enthält absichtlich Platzhalter und darf nicht als produktive Konfiguration gestartet werden.

Die SQLite-Datei sollte über `HELMUT_DB_PATH` außerhalb des Webverzeichnisses liegen. Sie enthält Konten, Sessions und verschlüsselte Chatdaten. Der Schlüssel und die Datenbank müssen gemeinsam und geschützt gesichert werden; ein einzelnes Backup ist nicht ausreichend.

## 3. Server starten

```bash
export HELMUT_HOST=127.0.0.1
export HELMUT_PORT=8080
export HELMUT_CHAT_PASSWORD='eigenes-einladungspasswort'
export HELMUT_SESSION_SECRET='eigener-base64-schluessel'
python server.py
```

Danach steht das Chat-System unter `http://127.0.0.1:8080/` und `http://127.0.0.1:8080/chat.html` bereit. Der Server stellt keinen KI-Generierungs-Endpunkt bereit; die Modellinferenz läuft im Browser.

## 4. Konto- und Chatablauf

1. Registrierung sendet Einladungspasswort, Benutzernamen, persönliches Passwort und Zustimmung zu den Hinweisen.
2. Der Server speichert Passwort-Hash, Benutzer-ID und einen passwortgeschützten Datenschlüssel.
3. Login erzeugt ein zufälliges Token; SQLite speichert davon nur den Hash und eine verschlüsselte Datenschlüssel-Referenz.
4. Chats gehören über `user_id` genau einem Konto.
5. Lesen, Erstellen, Umbenennen, Löschen und Nachrichtenspeicherung prüfen die Kontozugehörigkeit.
6. Titel und Nachrichten werden mit AES-256-GCM verschlüsselt.

Die API-Übersicht, Grenzen und Tabellen stehen in [docs/ARCHITECTURE.de.md](docs/ARCHITECTURE.de.md).

## 5. Browsermodelle und Datenquellen

Die kleinen WebLLM-Modelle und GGUF-Varianten werden erst im Browser geladen. `app.js` enthält nur öffentliche Quell-URLs und keine Geheimnisse. Wllama lädt die WASM-Runtime von jsDelivr; GGUF-Dateien kommen aus den eingetragenen öffentlichen Repositories oder aus der lokalen `assets/models/`-Ablage einer privaten Instanz. Die großen Gewichte gehören nicht in das Repository.

Versionsstände, URLs, ungefähre Größen, Lizenzprüfung und Cache-Verhalten: [docs/MODELS.de.md](docs/MODELS.de.md).

## 6. Lokale Dokumentfunktion

Nach Dateiauswahl liest der Browser TXT, MD, CSV, JSON oder DOCX. DOCX wird über Mammoth.js in Rohtext umgewandelt. Der Inhalt wird nicht an `server.py` gesendet. Der normale Chatweg ist davon getrennt: Wer Text in das Eingabefeld kopiert und abschickt, speichert ihn im Konto-Verlauf.

## 7. Caddy und systemd

`Caddyfile` ist eine Vorlage mit `example.com`. Ersetze den Platzhalter nur in deiner privaten Deployment-Konfiguration, konfiguriere DNS/TLS und leite ausschließlich auf `127.0.0.1:8080` weiter. Der Backend-Port soll nicht öffentlich erreichbar sein.

Für systemd gelten mindestens:

- eigener unprivilegierter Dienstbenutzer;
- `NoNewPrivileges=true`, `PrivateTmp=true`, eingeschränkte Schreibpfade;
- Environment-Datei außerhalb des Repositories mit Modus `0640` oder restriktiver;
- Session-Schlüssel und Datenbank außerhalb des Webroots;
- regelmäßige, verschlüsselte Backups und geprüfte Wiederherstellung.

Wenn ein Reverse-Proxy verwendet wird, setze `HELMUT_TRUST_PROXY=true` nur bei vollständig kontrolliertem Proxy. Dann dürfen `X-Forwarded-For` und `X-Forwarded-Proto` nicht von einem direkt erreichbaren Client fälschbar sein.

## 8. Vor dem Livegang

- Platzhalter in Legal-Dokumenten und Domainkonfiguration ausfüllen;
- tatsächlichen Betreiber, Kontakt, Hosting, Logs, Löschfristen und Drittanbieter dokumentieren;
- Modell- und Asset-Lizenzen prüfen;
- `python -m unittest discover -s tests -v` ausführen;
- `python tools/public_audit.py` ausführen;
- `python -m py_compile server.py` ausführen;
- HTTPS, Cookie `Secure`, Rate-Limits, Path-Traversal, Kontentrennung und Backups testen;
- erst danach einen anonymisierten neuen Git-Verlauf veröffentlichen.

## 9. Was nicht veröffentlicht werden darf

Keine `.env`, `.sqlite3`, Session-Schlüssel, privaten Zertifikate, Logs, echten Betreiberangaben, E-Mail-Adressen, Wallets, Referral-Codes, Serveradressen, großen Modellgewichte oder unklar lizenzierten Binärdateien hinzufügen. Der Public-Release-Check schlägt bei bekannten privaten/produktiven Mustern fehl.
