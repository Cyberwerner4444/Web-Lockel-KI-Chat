# Helmut-KI – Datenschutzerklärung (Vorlage)

> Diese Datei beschreibt die technische Standardimplementierung und ist eine ausfüllbare Vorlage. Sie ist keine Rechtsberatung. Vor dem Livegang müssen Betreiber, Hosting, Logs, Drittanbieter, Aufbewahrung, Löschung und anwendbares Recht konkret eingetragen werden.

## Pflichtangaben vor dem Livegang

- Verantwortliche Stelle: `[NAME / ORGANISATION EINTRAGEN]`
- Anschrift: `[EINTRAGEN]`
- Datenschutzkontakt: `[E-MAIL EINTRAGEN]`
- Domain und Hosting: `[EINTRAGEN]`
- Serverstandort und Logfristen: `[EINTRAGEN]`
- Version und Gültigkeitsdatum: `[EINTRAGEN]`

## 1. Öffentliche Website

Beim Aufruf können – abhängig von Python, Reverse-Proxy, Betriebssystem, Hosting und Monitoring – IP-Adresse oder Netzwerkkennung, Zeitpunkt, URL, HTTP-Methode, Statuscode, Datenmenge, User-Agent, Referrer sowie Fehler- und Sicherheitsdaten verarbeitet werden. Die konkrete Protokollierung und Löschfrist muss vor dem Livegang geprüft und hier ergänzt werden.

## 2. Konto und Anmeldung

Die Anwendung verarbeitet einen frei gewählten Benutzernamen, eine zufällige Benutzer-ID, einen Passwort-Hash und Zeitstempel. Das persönliche Passwort wird nicht im Klartext gespeichert. Das Einladungspasswort dient nur zur serverseitigen Prüfung und gehört ausschließlich in eine geschützte Umgebungsvariable.

Bei erfolgreicher Anmeldung wird ein zufälliges Session-Token erzeugt. SQLite speichert nur den Token-Hash und eine verschlüsselte Referenz auf den Benutzerdatenschlüssel. Das Cookie `helmut_auth` ist HttpOnly, SameSite=Lax und unter HTTPS Secure. Die Standardlaufzeit beträgt 30 Tage oder endet früher durch Logout beziehungsweise Ablauf.

## 3. Chatdaten

Chat-ID, Benutzer-ID, Titel, Rollen, Nachrichten und Zeitstempel werden gespeichert, damit der persönliche Verlauf angezeigt werden kann. Jeder Zugriff prüft die Eigentümerschaft. Chat-Titel und Nachrichten werden mit AES-256-GCM verschlüsselt; der persönliche Datenschlüssel wird passwortgeschützt gespeichert. Die serverseitige Verschlüsselung ist kein Ersatz für eine geprüfte Backup-, Lösch- und Zugriffsschutzstrategie.

## 4. Lokale KI und Dokumente

Die Modellinferenz läuft im Browser. Es gibt im aktuellen Aufbau keinen serverseitigen Generierungs-Endpunkt. Browser-Runtimes, WASM-Dateien und Modellgewichte können von den in der Modelldokumentation genannten Drittanbietern geladen werden. Diese Anbieter können technische Downloaddaten wie IP-Adresse, Zeitpunkt, User-Agent, angeforderte Datei und Range-Anfragen sehen; Prompts werden nicht als Inferenzanfragen an diese Quellen gesendet.

TXT-, MD-, CSV-, JSON- und DOCX-Dateien werden erst nach Dateiauswahl mit der Browser-File-API gelesen. Der Inhalt wird nicht als Upload an den Chatserver gesendet. Eine manuelle Kopie in das normale Chatfeld fällt dagegen unter die Chatverarbeitung und wird gespeichert.

## 5. Browser-Speicher

Die Modellwahl, Kontextgrenze und lokale Stilpräferenz können in `localStorage` gespeichert werden. Diese Werte sind keine Kontoeinstellungen. Dokumentinhalte, Dokument-Prompts und lokale Dokumentausgaben werden vom aktuellen Code nicht in `localStorage`, SQLite oder dem Chatverlauf gespeichert.

## 6. Drittanbieter

Die Public-Fassung nennt externe Runtime-, Font- und Modellquellen in `docs/MODELS.de.md`. Vor dem Livegang müssen je Anbieter Zweck, Empfänger, Länder, Rechtsgrundlage, Übermittlungsmechanismus, Lizenz und Aufbewahrung geprüft werden. Werden Analytics, Supportsysteme, Backups, Zahlungsdienste oder weitere Anbieter ergänzt, müssen sie hier nachgetragen werden.

## 7. Aufbewahrung, Rechte und Löschung

Vor dem Livegang sind konkrete Fristen für Sessions, Benutzerkonten, Chats, Backups, Serverlogs und Browsercaches einzutragen. Kontakt für Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch, Datenübertragbarkeit und Sicherheitsmeldungen: `[KONTAKT EINTRAGEN]`. Das Verfahren muss Identitätsprüfung, Bearbeitungsfristen und gesetzliche Aufbewahrung berücksichtigen.

## 8. Sicherheitsmaßnahmen

Die Implementierung nutzt PBKDF2-HMAC-SHA-256 für Passwort-Hashes, AES-256-GCM für Chatdaten, zufällige Tokens, Eigentümerprüfungen, Anfrage- und Nachrichtenlimits, eine statische Auslieferungs-Allowlist, Path-Traversal-Schutz, restriktive SQLite-Dateirechte und sichere DOM-Ausgabe. HTTPS, Schlüsselverwaltung, Backups, Updates, Monitoring und Zugriff auf das Betriebssystem bleiben Deploymentaufgaben.

## 9. Keine sensiblen Geheimnisse

Passwörter, API-Schlüssel, Seed-Phrases, private Schlüssel, vollständige Zahlungsdaten und besonders schützenswerte Personendaten dürfen nicht in Website, Chat, Issues, Logs oder Git eingegeben werden. Die Anwendung ist nicht als Hochsicherheits- oder Compliance-System zertifiziert.

## 10. Änderungsprüfung

Diese Erklärung muss aktualisiert werden, wenn Code, Hosting, Logs, Cookies, Modelle, CDNs, externe Dienste, Zwecke, Rechtslage oder Löschprozesse geändert werden. Vor der Veröffentlichung ist eine fachkundige Prüfung für die konkrete Jurisdiktion erforderlich.
