# Helmut-KI – Nutzungsbedingungen (Vorlage)

> Diese Datei ist eine öffentliche Vorlage und keine Rechtsberatung. Vor einem echten Betrieb müssen alle Platzhalter ausgefüllt und die Fassung an Betreiber, Zielgruppe, Land, Domain und tatsächliche Infrastruktur angepasst werden.

## Pflichtangaben vor dem Livegang

- Betreibername oder Organisation: `[EINTRAGEN]`
- ladungsfähige Anschrift: `[EINTRAGEN]`
- Kontakt für rechtliche und sicherheitsbezogene Meldungen: `[EINTRAGEN]`
- öffentliche Domain: `[EINTRAGEN]`
- Versionsnummer und Gültigkeitsdatum: `[EINTRAGEN]`

## 1. Geltungsbereich

Diese Bedingungen regeln die Nutzung der von der Betreiberperson konfigurierten Website, des privaten Chats, der lokalen Dokumentfunktion, der Modell-Auswahl und der sonstigen dokumentierten Funktionen.

## 2. Konto und Zugang

Für persönliche Chatverläufe wird ein Konto benötigt. Die Registrierung darf durch ein serverseitiges Einladungspasswort beschränkt werden. Nutzende müssen ihre Zugangsdaten geheim halten und jeden Verdacht auf Missbrauch unverzüglich an `[KONTAKT EINTRAGEN]` melden.

Der Server speichert persönliche Passwörter nicht im Klartext. Ein Konto darf nicht für Angriffe, Umgehung von Zugriffsschutz oder die Speicherung rechtswidriger Inhalte verwendet werden.

## 3. Lokale KI und technische Grenzen

Die eigentliche Modellinferenz läuft im Browser über WebGPU oder WebAssembly. Der Server speichert im aktuellen Aufbau Authentifizierungsdaten, Chatmetadaten und Nachrichten, erzeugt aber keine Modellantworten. Antworten können falsch, unvollständig, veraltet oder halluziniert sein. Sie ersetzen keine medizinische, rechtliche, steuerliche, finanzielle oder sicherheitsrelevante Beratung.

Die Browserfunktion kann Modelle beim ersten Einsatz aus externen Repositories oder CDNs laden. Modellgewichte, Lizenzen, Nutzungsbedingungen, Verfügbarkeit und Hardwareanforderungen sind vor der eigenen Nutzung zu prüfen.

## 4. Lokale Dokumentbearbeitung

TXT-, MD-, CSV-, JSON- und DOCX-Dateien werden nach ausdrücklicher Auswahl lokal mit Browser-APIs gelesen. Der aktuelle Aufbau besitzt keinen Datei-Upload-Endpunkt. Wird Text manuell in das normale Chatfeld kopiert, wird er als Chatnachricht an den Server gesendet und im persönlichen Verlauf gespeichert.

## 5. Zulässige Nutzung

Untersagt sind insbesondere:

- Angriffe, Portscans, Path-Traversal und das Umgehen von Authentifizierung;
- Malware, Phishing, Betrug, Drohungen, Belästigung und Denial-of-Service;
- unverhältnismäßige Automatisierung, Scraping oder Lasttests ohne Zustimmung;
- die Eingabe von Passwörtern, API-Schlüsseln, Seed-Phrases, privaten Schlüsseln oder vollständigen Zahlungsdaten;
- Inhalte, deren Nutzung Rechte Dritter oder geltendes Recht verletzt.

## 6. Chatinhalte

Nutzende sind für ihre Eingaben und die dafür erforderlichen Rechte verantwortlich. Der Betreiber darf rechtswidrige oder gefährliche Inhalte im gesetzlich zulässigen Umfang sperren, löschen oder melden. Der aktuelle Quellstand verwendet Chatinhalte nicht als Trainingsdatensatz.

## 7. Verfügbarkeit und Haftungsgrenzen

Es besteht kein Anspruch auf eine bestimmte Modellversion, Antwort, Kontextgröße, Browserkompatibilität, Verfügbarkeit oder dauerhafte Speicherung. Wartungen, Browseränderungen, CDN-Ausfälle, Datenverlust, Sicherheitsmaßnahmen und Modelländerungen können Funktionen beeinträchtigen. Zwingende gesetzliche Ansprüche bleiben unberührt.

## 8. Löschung und Kontakt

Anträge auf Konto-/Chatlöschung, Auskunft oder Berichtigung: `[KONTAKT EINTRAGEN]`. Der Betreiber muss vor dem Livegang ein Verfahren für Identitätsprüfung, Fristen, Backups, Löschung und eventuelle gesetzliche Aufbewahrung festlegen.

## 9. Externe Dienste und offene Komponenten

Die Anwendung kann WebLLM, Wllama, Mammoth.js, Modell-Repositories, CDNs, Fonts und einen Reverse-Proxy verwenden. Für diese Bestandteile gelten deren eigene Lizenzen und Bedingungen. Die verwendeten Versionen und Quellen stehen in `docs/MODELS.de.md` und `docs/MODELS.en.md`.

## 10. Rechtliche Prüfung

Anwendbares Recht, Gerichtsstand, Verbraucherrechte, Datenschutz, Impressumspflichten und internationale Angebote müssen für den konkreten Betreiber geprüft werden. Diese Vorlage darf nicht unverändert als rechtlich vollständiger Text veröffentlicht werden.
