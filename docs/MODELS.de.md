# Modelle, Web-KI-Runtimes und Datenquellen

Stand der Pins: 24.09.2026. Vor einem späteren Release müssen offizielle Quellen, Sicherheitsmeldungen, Modellkarten und Lizenzen erneut geprüft werden. Ein Versionspin ist keine Garantie für Verfügbarkeit oder Lizenz.

## WebLLM / MLC

- Runtime: `@mlc-ai/web-llm` `0.2.85`.
- Import im Frontend: `https://esm.run/@mlc-ai/web-llm@0.2.85`.
- Offizielle Quelle: <https://github.com/mlc-ai/web-llm>.
- Releases: <https://github.com/mlc-ai/web-llm/releases/tag/v0.2.85>.
- Aufgabe: MLC-Modelle im Browser, primär über WebGPU; Prebuilt-Konfiguration und Modellbibliothek werden vom Paket bereitgestellt.
- Benötigte Daten: der Browser lädt beim ersten Einsatz die zum Modell gehörenden MLC-Artefakte. Diese liegen nicht im Git-Repository.

In `app.js` sind als WebLLM-Modell-IDs hinterlegt:

- `Llama-3.2-1B-Instruct-q4f16_1-MLC`
- `SmolLM2-1.7B-Instruct-q4f16_1-MLC`
- `Llama-3.2-3B-Instruct-q4f16_1-MLC`
- `Phi-3.5-mini-instruct-q4f16_1-MLC`

Die jeweils tatsächlich verfügbaren Prebuilt-Artefakte und Nutzungsbedingungen müssen im Release von WebLLM und den zugehörigen Modellkarten geprüft werden.

## Wllama / llama.cpp WebAssembly

- Runtime: `@wllama/wllama` `3.6.1`.
- ESM: `https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/esm/index.js`.
- WASM: `https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/src/wasm/wllama.wasm`.
- Offizielle Paketquelle: <https://www.npmjs.com/package/@wllama/wllama>.
- Repository: <https://github.com/ngxson/wllama>.
- Lizenz laut Paketquelle: MIT; die enthaltenen/geladenen Modellgewichte haben davon unabhängige Lizenzen.

Wllama wird für CPU/WASM sowie für GGUF-WebGPU verwendet. Die GGUF-URL muss entweder eine einzelne Datei oder den korrekten Split-/Shard-Aufbau liefern. Große Dateien müssen HTTPS, `HEAD`, Range-Anfragen und ausreichende Browser-CORS-Regeln unterstützen.

## DOCX-Lesen

- Runtime: Mammoth.js `1.12.3`.
- Browserdatei: `https://cdn.jsdelivr.net/npm/mammoth@1.12.3/mammoth.browser.min.js`.
- Paketquelle: <https://www.npmjs.com/package/mammoth>.
- Repository: <https://github.com/mwilliamson/mammoth.js>.
- Lizenz laut Paketquelle: BSD-2-Clause.

Die Runtime wird erst geladen, wenn eine DOCX-Datei ausgewählt wird. Mammoth extrahiert Rohtext; es ist kein vollständiger Layout- oder Formatkonverter. Versionen ab 1.11.0 enthalten die Korrektur für externe DOCX-Bildverknüpfungen und deaktivieren externen Dateizugriff standardmäßig; diese Anwendung nutzt 1.12.3. Der Inhalt wird danach nicht an den Server hochgeladen. Siehe [Sicherheitsmeldung GHSA-rmjr-87wv-gf87](https://github.com/advisories/GHSA-rmjr-87wv-gf87).

## GGUF-Modellquellen im Frontend

Die folgenden öffentlichen URLs sind im aktuellen Frontend als CPU/GGUF-Beispiele hinterlegt:

| Modell | Quelle |
| --- | --- |
| Llama 3.2 1B Instruct | <https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF> |
| SmolLM2 1.7B Instruct | <https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF> |
| Llama 3.2 3B Instruct | <https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF> |
| Phi-3.5 Mini Instruct | <https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF> |
| Qwen3.8 2B Distill GGUF | <https://huggingface.co/empero-ai/Qwen3.8-2B-Distill-GGUF> |

Die konkrete Quantisierung ist im Code als `Q4_K_M.gguf` eingetragen. Hugging Face kann Dateien, Redirects, CDN-Hostnamen, Lizenztexte und Zugriffsvoraussetzungen ändern. Vor Deployment die Modellkarte, Lizenz, SHA256/Integrität, Größe, Kontextfenster und Eignung für das eigene Nutzerprofil kontrollieren.

## Große lokale GGUF-Dateien

Die optionalen großen lokalen Modelle werden nicht veröffentlicht und stehen nicht im Public-Release. Wenn sie privat betrieben werden, müssen alle Shards vollständig bereitgestellt werden, der Dateiname muss zu `app.js` passen und der Server muss Range-Requests bedienen. Modellgewichte dürfen nur mit geklärter Lizenz weitergegeben werden.

## Python-Verschlüsselung

- Paket: `cryptography`.
- Requirements-Constraint: `>=50,<51`.
- Offizielle Quelle: <https://pypi.org/project/cryptography/>.
- Verwendet: `AESGCM` sowie keine selbst implementierten Blockchiffren.

Die konkrete installierte Patchversion ist bei jedem Build zu protokollieren. Security-Releases haben Vorrang vor einem unveränderten Pin.

## Browser- und Datenschutzfolgen

CDN- und Repository-Downloads können IP-Adresse, Zeitpunkt, User-Agent, Dateipfad, Range-Anfragen und Fehlercodes sichtbar machen. Die Anwendung sendet dort keine Chatprompts als Modellanfragen. Wer vollständige Offline-Reproduzierbarkeit braucht, muss Runtimes und Modellgewichte nach Lizenzprüfung selbst hosten und die CSP/URLs anpassen.
