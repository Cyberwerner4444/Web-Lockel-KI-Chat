# Architektur und Datenfluss

## Überblick

Helmut-KI trennt lokale Browser-Inferenz, Chat-Anwendung und private Verlaufsspeicherung:

```text
Browser
  ├── chat.html + rechtliche Chat-Vorlagen
  ├── app.js + styles.css
  ├── WebLLM 0.2.85 oder Wllama 3.6.1
  ├── Browser File API + Mammoth.js 1.12.3
  └── JSON über HTTPS
          ↓
      server.py
  ├── statische Allowlist
  ├── Authentifizierung + Rate-Limits
  ├── SQLite mit Benutzern, Sessions, Chats, Nachrichten
  └── keine serverseitige Modellinferenz
```

## Frontend

- `chat.html`: Registrierung, Login, Chatliste, Nachrichten, Modell- und Kontextauswahl.
- `app.js`: UI-Zustand, API-Aufrufe, lokale Modellruntime, lokale Dokumente und sichere DOM-Ausgabe.
- `styles.css`: Layout, Farben, Responsive-Verhalten und Animationen.
- `legal.html`, `AGB.md`, `DATENSCHUTZERKLAERUNG.md`: Chat-spezifische Rechtsvorlagen.

## Server und API

`server.py` verwendet die Python-Standardbibliothek `http.server` und `sqlite3`. `cryptography` wird für AES-GCM und die übrigen kryptografischen Bausteine benötigt.

| Route | Zweck | Authentifizierung |
| --- | --- | --- |
| `GET /api/auth/status` | Sessionstatus, Modellstandard, Registrierungsstatus | nein |
| `POST /api/auth/register` | Konto erstellen und Session setzen | Einladungspasswort im Body |
| `POST /api/auth/login` | Konto öffnen und Session setzen | Benutzerpasswort |
| `POST /api/auth/logout` | Session löschen und Cookie ablaufen lassen | Cookie optional |
| `GET /api/chats` | eigene Chats auflisten | ja |
| `POST /api/chats` | eigenen Chat erstellen | ja |
| `GET /api/chats/{id}` | eigenen Chat mit Nachrichten lesen | ja + Eigentümerprüfung |
| `PATCH /api/chats/{id}` | eigenen Titel ändern | ja + Eigentümerprüfung |
| `DELETE /api/chats/{id}` | eigenen Chat löschen | ja + Eigentümerprüfung |
| `POST /api/chats/{id}/messages` | eigene User-/Assistant-Nachricht speichern | ja + Eigentümerprüfung |

Es gibt absichtlich keinen `/api/generate`- oder `/api/completions`-Endpunkt.

## Datenbank

- `users`: zufällige ID, Benutzername, Passwort-Hash, Erstellungszeit, Salt und verschlüsselter Datenschlüssel.
- `sessions`: Hash des Session-Tokens, Benutzer-ID, verschlüsselte Datenschlüssel-Referenz, Erstellungs- und Ablaufzeit.
- `chats`: Chat-ID, Eigentümer-ID, verschlüsselter Titel, Erstellungs-/Änderungszeit.
- `messages`: Nachrichten-ID, Chat-ID, Rolle, verschlüsselter Inhalt und Zeitstempel.

Der persönliche Datenschlüssel wird vom Benutzerpasswort abgeleitet verpackt. Sessions verpacken denselben Schlüssel zusätzlich mit `HELMUT_SESSION_SECRET`, damit ein Neustart die laufende Sitzung nicht beendet. Die Datenbank ist dadurch nicht automatisch „zero knowledge“: Ein laufender Server kann Daten bei gültiger Session entschlüsseln.

## Anmeldeablauf

1. Registrierung prüft Einladung, Benutzername, Passwortlänge und Zustimmung.
2. Der Server erzeugt Benutzer-ID, Salt und Datenschlüssel.
3. Das persönliche Passwort wird als PBKDF2-Hash gespeichert.
4. Der Datenschlüssel wird mit einem aus dem Passwort abgeleiteten Schlüssel verschlüsselt.
5. Eine zufällige Session wird erzeugt; gespeichert werden nur Token-Hash und verschlüsselte Schlüsselreferenz.
6. Jeder geschützte Endpunkt lädt die Session, prüft TTL und entschlüsselt den Datenschlüssel.

## Lokale Dokumente

Dateien werden nur nach Auswahl gelesen. TXT, MD, CSV und JSON werden direkt als Text gelesen; DOCX wird mit Mammoth.js in Rohtext umgewandelt. Der Inhalt wird nicht über die Chat-API gesendet. Das normale Nachrichtenformular ist davon getrennt und speichert absichtlich gesendete Nachrichten im Serververlauf.

## Schutzgrenzen

Die Implementierung setzt Anfragegrößen, Nachrichten-/Chatlimits, Rate-Limits, Path-Traversal-Schutz und eine statische Datei-Allowlist. `HELMUT_TRUST_PROXY` muss `false` bleiben, wenn Clients den Backend-Port direkt erreichen können. Für produktive Nutzung gehören TLS, Firewall, Betriebssystemupdates, Backupverschlüsselung, Monitoring und rechtliche Prozesse in die Deploymentverantwortung.
