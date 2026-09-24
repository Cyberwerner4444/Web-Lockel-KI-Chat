# Test- und Public-Release-Checkliste

## Automatische Prüfungen

Im Repository ausführen:

```bash
python -m unittest discover -s tests -v
python tools/public_audit.py
python -m py_compile server.py
```

Die Tests verwenden eine temporäre SQLite-Datei und einen lokalen zufälligen Session-Schlüssel. Sie verändern keine produktive Datenbank.

## Funktionsprüfung

- `/` öffnet den Chat; `/chat.html`, `/legal.html` und die freigegebenen Rechtstexte liefern HTTP 200.
- Frühere Website-, Support-, Mining-, Logo- und Rechtsseiten liefern 404 und sind nicht im Repository enthalten.
- Nicht erlaubte Pfade, `..`, versteckte Dateien und unfreigegebene Root-Dateien liefern 404.
- Range-Requests für große statische Dateien liefern `206` und korrekten `Content-Range`.
- Status ohne Cookie meldet `authenticated: false`.
- Registrierung funktioniert nur mit Einladung, gültigem Benutzernamen, passendem Passwort und Zustimmung.
- Login setzt Cookie; Logout löscht Session und Cookie.
- Benutzer A kann Chat anlegen, Titel ändern, Nachrichten speichern und löschen.
- Benutzer B erhält auf Benutzer-A-Chats 404 und keine Nachrichten.
- SQLite enthält den Klartext eines Testnachrichtentexts nicht.
- Rate-Limits und Nachrichten-/Chatlimits werden nicht umgangen.
- Modell-URLs, Mammoth-URL, CSP und Runtime-Pins sind erreichbar und stimmen mit `docs/MODELS.de.md` überein.

## Browserprüfung

In einem aktuellen Browser testen:

1. Registrierung und Login.
2. Modell laden, Antwort erzeugen und Verlauf neu laden.
3. Chat umbenennen, neuen Chat anlegen und löschen.
4. Logout und Zugriff ohne Session.
5. WebGPU ein/aus; CPU/WASM-Fallback.
6. Kontextlimit ändern und Modell entladen/laden.
7. TXT, MD, CSV, JSON und DOCX lokal öffnen.
8. Dokumentinhalt nicht versehentlich in den normalen Chat kopieren.
9. Responsive Darstellung und Tastaturbedienung auf Desktop/Mobilgerät.

## Anonymisierungsprüfung

- Keine echten Namen, E-Mails, Anschriften, Domains, IPs oder Hostnamen.
- Keine persönlichen Links oder produktiven Infrastrukturwerte.
- Keine `.env`, Datenbank, Session-Datei, Zertifikate, Logs oder privaten Schlüssel.
- Keine alten Commit-E-Mail-Adressen in der öffentlichen Historie.
- Keine großen lokalen Modelle oder unklar lizenzierten Binärdateien.
- Keine private Remote-URL in `.git/config` des Public-Repositories.
- Legaltexte enthalten nur bewusst auszufüllende Platzhalter.

## Upload-Gate

Erst hochladen, wenn:

- alle automatischen Prüfungen grün sind;
- Browser-Smoke-Test erfolgreich ist;
- jedes öffentliche Dokument gelesen und gegen Code/Deployment abgeglichen wurde;
- Lizenzen und Bilder geprüft sind;
- ein neuer, anonymisierter Git-Verlauf erzeugt wurde;
- das Zielrepository und die Push-Berechtigung bestätigt sind.

Nach dem Push: frischen Clone ohne lokale Altdateien anlegen, Audit erneut ausführen und GitHub-Dateiliste, Repository-Sichtbarkeit, Actions/Secrets und Default-Branch kontrollieren.
