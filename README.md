# Helmut-KI – vollständiges Chat-System

Helmut-KI ist eine selbst hostbare Chat-Anwendung mit Registrierung, Login, getrennten Benutzerkonten, persönlichen Chatverläufen, mehreren lokalen Browsermodellen und einem Dokumentenwerkzeug. Der Python-Server authentifiziert Konten und speichert Chatverläufe verschlüsselt in SQLite; die Modellinferenz läuft im Browser.

English version: [README.en.md](README.en.md)

## Was enthalten ist

- Login, Registrierung mit Einladungspasswort, Logout und Session-Cookie;
- Benutzer- und Eigentümermodell: ein Konto sieht nur die eigenen Chats;
- Chat anlegen, öffnen, umbenennen, löschen und Nachrichten speichern;
- PBKDF2-HMAC-SHA-256 für Passwort-Hashes und AES-256-GCM für Titel/Nachrichten;
- lokale Browser-Inferenz über WebLLM/MLC oder Wllama/llama.cpp;
- lokale Dokumentbearbeitung für TXT, MD, CSV, JSON und DOCX ohne Upload-Endpunkt;
- deutsche Chat-Oberfläche sowie vollständige deutsche/englische technische Dokumentation.

Dieses Repository enthält ausschließlich das Chat-System und die dafür erforderlichen Rechts- und Betriebsdokumente. Es enthält keine öffentliche Helmut-KI-Startseite, Supportseite, Miningfunktion oder Logo-Downloadseite.

## Architektur

```text
Browser
  ├─ HTML/CSS/JavaScript
  ├─ WebLLM + WebGPU für kleine MLC-Modelle
  ├─ Wllama + WASM/WebGPU für GGUF-Modelle
  ├─ Browser-File-API für lokale Dokumente
  └─ HTTPS/JSON ──> server.py
                         ├─ Authentifizierung und Rate-Limits
                         ├─ SQLite: Konten, Sessions, Chats, Nachrichten
                         └─ kein serverseitiger /api/generate-Endpunkt
```

Der Server erhält Chatnachrichten nur, weil der Verlauf kontobezogen gespeichert wird. Die ausgewählte Modellquelle erhält keine Prompts als Inferenzanfragen. Details und Datenflüsse stehen in [docs/ARCHITECTURE.de.md](docs/ARCHITECTURE.de.md).

## Schnellstart lokal

Voraussetzung: Python 3.10 oder neuer und ein virtuelles Environment.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Erzeuge einen eigenen 32-Byte-Schlüssel und trage ihn in einer geschützten Umgebung ein:

```bash
export HELMUT_SESSION_SECRET="$(python -c 'import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())')"
export HELMUT_CHAT_PASSWORD='ein-eigenes-langes-einladungspasswort'
python server.py
```

Öffne danach `http://127.0.0.1:8080/` oder `http://127.0.0.1:8080/chat.html`.

`HELMUT_CHAT_PASSWORD` ist kein Benutzerpasswort, sondern nur die serverseitige Freigabe für neue Registrierungen. Benutzer legen danach ein eigenes Passwort fest. Produktive Geheimnisse gehören nie in `.env`-Dateien, die committed werden könnten.

## Umgebungsvariablen

| Variable | Zweck | Standard |
| --- | --- | --- |
| `HELMUT_HOST` | Bind-Adresse des Python-Servers | `127.0.0.1` |
| `HELMUT_PORT` | lokaler Port | `8080` |
| `HELMUT_DB_PATH` | private SQLite-Datei außerhalb des Webverzeichnisses empfohlen | `./helmut.sqlite3` |
| `HELMUT_CHAT_PASSWORD` | Registrierungseinladung, mindestens 8 Zeichen | leer/deaktiviert |
| `HELMUT_SESSION_SECRET` | stabiler URL-safe Base64-Schlüssel mit 32 Byte | erforderlich |
| `HELMUT_SESSION_SECRET_FILE` | alternative Datei für den 32-Byte-Schlüssel | leer |
| `HELMUT_BROWSER_MODEL` | Standardmodell-ID im Frontend | Llama 3.2 1B WebLLM-ID |
| `HELMUT_TRUST_PROXY` | `true` nur hinter einem kontrollierten Reverse-Proxy | `false` |
| `HELMUT_COOKIE_SECURE` | `true`, `false` oder `auto` für das Session-Cookie | `auto` |

Eine ausfüllbare Vorlage liegt in [.env.example](.env.example). Schlüssel und Datenbank müssen mit Dateirechten `0600` geschützt und gemeinsam gesichert werden.

## Modelle und benötigte Daten

Die Anwendung lädt Modellgewichte nicht aus diesem Repository. Beim ersten Modellstart lädt der Browser die ausgewählte Datei aus einer dokumentierten Quelle und verwendet danach seinen eigenen Cache. Große lokale GGUF-Shards liegen absichtlich außerhalb von Git.

| Zweck | Quelle/Version im Code | Benötigte Daten |
| --- | --- | --- |
| WebGPU-Modelle | WebLLM `0.2.85` über `esm.run` | MLC-Prebuilt-Modellbibliotheken, Browser-Cache |
| GGUF-Inferenz | Wllama `3.6.1` über jsDelivr | GGUF-Datei oder alle Shards, WASM-Datei |
| DOCX-Text | Mammoth.js `1.12.3` über jsDelivr | nur die Runtime beim Öffnen einer DOCX-Datei |
| CPU/GGUF-Quellen | öffentliche Hugging-Face-Repositories in `app.js` | Modellgewichte und jeweilige Lizenz-/Nutzungsbedingungen |
| Server-Verschlüsselung | Python `cryptography` `>=50,<51` | installiertes Python-Paket |

Aktuelle URLs, Modellnamen, ungefähre Größen und Lizenzhinweise stehen in [docs/MODELS.de.md](docs/MODELS.de.md). Versionsstände können sich ändern; die dort angegebenen offiziellen Quellen sind vor jedem Release erneut zu prüfen.

## Produktionsbetrieb

1. Platzhalter in [AGB.md](AGB.md), [DATENSCHUTZERKLAERUNG.md](DATENSCHUTZERKLAERUNG.md) und [legal.html](legal.html) ausfüllen und rechtlich prüfen.
2. Eine eigene Domain und TLS über einen Reverse-Proxy wie Caddy konfigurieren. [Caddyfile](Caddyfile) verwendet absichtlich `example.com`.
3. Python nur an `127.0.0.1` binden und die Datenbank außerhalb des öffentlichen Verzeichnisses ablegen.
4. Einen eigenen Session-Schlüssel sowie ein eigenes Einladungspasswort setzen. Niemals Werte aus Beispielen wiederverwenden.
5. `HELMUT_TRUST_PROXY=true` nur setzen, wenn ausschließlich der eigene Proxy den Backend-Port erreicht.
6. SQLite und Session-Schlüssel verschlüsselt/zugriffsbeschränkt sichern; Backups niemals in Git oder `assets/` legen.
7. Vor Freischaltung HTTPS, Cookie-Attribute, Rate-Limits, Löschung, Logs, Modelllizenzen und Rechtsdokumente prüfen.

Die zweisprachige Betriebsanleitung steht in [docs/OPERATIONS.de.md](docs/OPERATIONS.de.md) und [docs/OPERATIONS.en.md](docs/OPERATIONS.en.md).

## Tests und Veröffentlichungskontrolle

```bash
python -m unittest discover -s tests -v
python tools/public_audit.py
python -m py_compile server.py
```

Die Tests starten einen temporären Server, prüfen Registrierung/Login, Kontentrennung, Chatabläufe, Verschlüsselung, Rate-Limits, Range-Requests und statische Pfadgrenzen. `public_audit.py` prüft zusätzlich verbotene persönliche/produktive Muster, private Laufzeitdateien und zu große Public-Dateien.

Vor jedem Upload muss [docs/TESTING.de.md](docs/TESTING.de.md) vollständig abgearbeitet werden. Ein Upload ist erst nach einem sauberen Audit zulässig.

## Public-Anonymisierung

Diese öffentliche Quellfassung enthält absichtlich keine:

- realen Betreiber-, Privat- oder Serverangaben;
- produktiven Domains, E-Mail-Adressen, Referral-Codes oder Wallet-Adressen;
- SQLite-Datenbanken, Session-Schlüssel, `.env`-Dateien oder Modellgewichte;
- privaten Git-Remotes oder alten Entwicklungs-Commit-Historien;
- nicht geprüften 3D-/Downloadarchive.

Die Public-Fassung wird als neues, anonymisiertes Git-Repository mit einer neuen Historie veröffentlicht. Lokale Laufzeitdaten aus einer privaten Instanz bleiben davon getrennt.

## Recht und Lizenzen

WebLLM, Wllama, Mammoth.js, Python-Pakete und Modellgewichte haben eigene Lizenzen. Vor dem Betrieb müssen Runtime-/Modellquellen sowie Nutzungsbedingungen geprüft werden. Die rechtlichen Markdown-/HTML-Dateien sind Vorlagen, keine geprüfte Rechtsberatung.

## Weiterführende Dokumente

- [Architektur und Datenfluss (DE)](docs/ARCHITECTURE.de.md) · [English](docs/ARCHITECTURE.en.md)
- [Betrieb und Datenquellen (DE)](docs/OPERATIONS.de.md) · [English](docs/OPERATIONS.en.md)
- [Modelle und Runtime-Versionen (DE)](docs/MODELS.de.md) · [English](docs/MODELS.en.md)
- [Sicherheit und Datenschutz (DE)](docs/SECURITY-PRIVACY.de.md) · [English](docs/SECURITY-PRIVACY.en.md)
- [Test- und Releasecheckliste (DE)](docs/TESTING.de.md) · [English](docs/TESTING.en.md)
- [Nutzungsbedingungen (DE)](AGB.md) · [Terms (EN)](TERMS.en.md)
- [Datenschutz (DE)](DATENSCHUTZERKLAERUNG.md) · [Privacy (EN)](PRIVACY.en.md)
