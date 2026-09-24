# Sicherheit, Datenschutz und Anonymisierung

## Public-Scope

Das öffentliche Repository ist eine Quellcodevorlage, keine produktive Instanz. Es enthält keine echte Identität, Domain, Kontaktadresse, Wallet, Referral-ID, Serveradresse, Datenbank, Session-Secret, Environment-Datei, Modellgewichte oder alte private Git-Historie.

## Kontosicherheit

- Registrierung nur mit serverseitigem Einladungspasswort.
- Benutzerpasswort wird mit PBKDF2-HMAC-SHA-256 und zufälligem Salt gehasht.
- Persönliche Daten werden über einen zufälligen 32-Byte-Datenschlüssel verschlüsselt.
- Titel und Nachrichten verwenden AES-256-GCM mit kontextgebundener Associated Data.
- Session-Tokens sind zufällig; SQLite speichert nur deren SHA-256-Hash.
- Cookie ist HttpOnly und SameSite=Lax; `Secure` muss im HTTPS-Betrieb aktiv sein.
- Login und API haben In-Memory-Sliding-Window-Limits.
- Benutzer- und Chat-Eigentümerschaft wird vor jedem Zugriff geprüft.

## Was der Server trotzdem sehen kann

Der laufende Server kann gültige Sessions bedienen und dabei Chatdaten entschlüsseln. Die Verschlüsselung schützt primär SQLite-Dateien und Backups bei fehlendem Schlüssel. Proxy-, Webserver-, Betriebssystem-, Backup- und Browserlogs können zusätzliche technische Daten enthalten. Die konkrete Instanz muss das in ihrer Datenschutzerklärung beschreiben.

## Datenfluss

- Modellinferenz: Browser lokal.
- Persistenz: Browser sendet User-/Assistant-Nachrichten an die eigene API.
- Lokale Dokumente: Browser File API, kein Upload-Endpunkt.
- Modell-/Runtime-Download: CDN/Repository kann technische Download-Metadaten sehen.
- Public Release: keine echten Betreiber- oder Zahlungsdaten.

## Anonymisierungscheck

Vor jedem Public Push:

1. `python tools/public_audit.py` ausführen.
2. `git ls-files` auf Datenbanken, Environment-Dateien, Schlüssel, Logs und große Binärdateien prüfen.
3. `git log --format='%an <%ae>'` prüfen; für den Public-Release eine neue Historie verwenden.
4. Domain-, E-Mail-, IP-, Wallet-, Referral-, Server- und Hostingmuster suchen.
5. Bild-/Archivmetadaten und Lizenzrechte prüfen.
6. Legal-Platzhalter auf Vollständigkeit und konkrete Betreiberkonfiguration prüfen.

## Sicherheitsgrenzen und offene Aufgaben

Der Server ist bewusst klein und nutzt keinen vollständigen Web-Framework-Stack. Vor einem Internetbetrieb sind TLS/Proxy, Firewall, OS-Updates, Backupverschlüsselung, Secret-Rotation, Accountlöschung, Monitoring, Alarmierung, CSRF-/Origin-Strategie, Abhängigkeitsupdates und eine fachkundige Sicherheitsprüfung festzulegen. „Verschlüsselt in SQLite“ ist kein vollständiges Sicherheits- oder Datenschutzversprechen.

Sicherheitsmeldungen gehören nicht in öffentliche Issues. Ergänze vor Veröffentlichung einen privaten Security-Kontakt in der Deployment-Instanz.
