# Models, web-AI runtimes, and data sources

Pin date: 2026-09-24. Before a later release, re-check official sources, security notices, model cards, and licenses. A version pin does not guarantee availability or licensing.

## WebLLM / MLC

- Runtime: `@mlc-ai/web-llm` `0.2.85`.
- Frontend import: `https://esm.run/@mlc-ai/web-llm@0.2.85`.
- Official source: <https://github.com/mlc-ai/web-llm>.
- Release: <https://github.com/mlc-ai/web-llm/releases/tag/v0.2.85>.
- Purpose: browser-side MLC models, primarily through WebGPU; the package provides the prebuilt configuration and model library mapping.
- Required data: on first use, the browser downloads the MLC artifacts for the selected model. They are not in Git.

The following WebLLM model IDs are configured in `app.js`:

- `Llama-3.2-1B-Instruct-q4f16_1-MLC`
- `SmolLM2-1.7B-Instruct-q4f16_1-MLC`
- `Llama-3.2-3B-Instruct-q4f16_1-MLC`
- `Phi-3.5-mini-instruct-q4f16_1-MLC`

Verify the actual prebuilt artifacts and usage terms in the WebLLM release and the associated model cards.

## Wllama / llama.cpp WebAssembly

- Runtime: `@wllama/wllama` `3.6.1`.
- ESM: `https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/esm/index.js`.
- WASM: `https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/src/wasm/wllama.wasm`.
- Official package source: <https://www.npmjs.com/package/@wllama/wllama>.
- Repository: <https://github.com/ngxson/wllama>.
- Package license: MIT according to the package source; loaded model weights have separate licenses.

Wllama is used for CPU/WASM and GGUF WebGPU. A GGUF URL must provide either one file or the correct split/shard layout. Large files need HTTPS, `HEAD`, range requests, and suitable browser CORS behavior.

## DOCX reading

- Runtime: Mammoth.js `1.12.3`.
- Browser file: `https://cdn.jsdelivr.net/npm/mammoth@1.12.3/mammoth.browser.min.js`.
- Package source: <https://www.npmjs.com/package/mammoth>.
- Repository: <https://github.com/mwilliamson/mammoth.js>.
- Package license: BSD-2-Clause according to the package source.

The runtime is loaded only after a DOCX file is selected. Mammoth extracts raw text; it is not a complete layout or formatting converter. Versions from 1.11.0 include the fix for external DOCX image links and disable external file access by default; this application uses 1.12.3. The content is not uploaded afterward. See [security advisory GHSA-rmjr-87wv-gf87](https://github.com/advisories/GHSA-rmjr-87wv-gf87).

## GGUF model sources in the frontend

The current frontend contains these public CPU/GGUF example sources:

| Model | Source |
| --- | --- |
| Llama 3.2 1B Instruct | <https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF> |
| SmolLM2 1.7B Instruct | <https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF> |
| Llama 3.2 3B Instruct | <https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF> |
| Phi-3.5 Mini Instruct | <https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF> |
| Qwen3.8 2B Distill GGUF | <https://huggingface.co/empero-ai/Qwen3.8-2B-Distill-GGUF> |

The code requests a `Q4_K_M.gguf` quantization. Hugging Face can change files, redirects, CDN hostnames, license text, and access requirements. Before deployment, verify the model card, license, SHA256/integrity, size, context window, and suitability for the intended users.

## Large local GGUF files

Optional large local models are not published and are not part of the public release. If privately operated, all shards must be present, filenames must match `app.js`, and the server must support range requests. Do not redistribute weights until licensing is clear.

## Python encryption

- Package: `cryptography`.
- Requirements constraint: `>=50,<51`.
- Official source: <https://pypi.org/project/cryptography/>.
- Used: `AESGCM`; no block cipher is implemented by this project.

Record the exact installed patch release for each build. Security releases take priority over keeping an old pin unchanged.

## Browser and privacy consequences

CDN and repository downloads can expose IP address, timestamp, user agent, path, range requests, and error codes. The application does not send chat prompts to those sources as model inference requests. For full offline reproducibility, self-host runtimes and model weights after license review and update the CSP/URLs.
