# Helmut-KI – Terms of Use (template)

> This public template is not legal advice. Before operating the service, complete every placeholder and adapt it to the operator, audience, jurisdiction, hosting, and actual configuration.

## Required details before launch

- Operator or organization: `[ENTER]`
- service address: `[ENTER]`
- legal and security contact: `[ENTER]`
- public service domain: `[ENTER]`
- version and effective date: `[ENTER]`

## 1. Scope

These terms govern use of the operator-configured Helmut-KI chat application, accounts, personal chat histories, local document tool, model selection, and documented features.

## 2. Accounts and access

A personal account is required for chat histories. Registration may be restricted by a server-side invitation password. Users must protect their credentials and promptly report suspected misuse to `[CONTACT]`.

The server does not store personal passwords in plaintext. Accounts must not be used to attack systems, bypass access controls, or store unlawful content.

## 3. Local AI and technical limits

Model inference runs in the browser through WebGPU or WebAssembly. The server stores authentication data, chat metadata, and messages but does not generate model responses. Responses may be wrong, incomplete, outdated, or hallucinated and are not medical, legal, tax, financial, or safety advice.

The browser may download runtimes and model weights from external repositories or CDNs. Users and operators must review model licenses, terms, availability, and hardware requirements.

## 4. Local document processing

TXT, MD, CSV, JSON, and DOCX files are read locally only after the user selects them. The current application has no file-upload endpoint. Text manually copied into the normal chat is sent to the server and stored in the account history.

## 5. Acceptable use

Users must not:

- attack systems, scan ports, exploit path traversal, or bypass authentication;
- create malware, phishing, fraud, threats, harassment, or denial of service;
- automate, scrape, or load-test the service excessively without permission;
- submit passwords, API keys, seed phrases, private keys, or complete payment credentials;
- submit content that violates third-party rights or applicable law.

## 6. Chat content

Users are responsible for their input and the rights required to submit it. To the extent permitted by law, the operator may restrict, delete, or report unlawful or dangerous content. The current source does not use chat content as a training dataset.

## 7. Availability and liability

No particular model version, response, context size, browser compatibility, availability, or permanent storage is guaranteed. Maintenance, browser changes, CDN outages, data loss, security measures, and model changes can affect features. Mandatory statutory rights remain unaffected.

## 8. Deletion and contact

Requests concerning account/chat deletion, access, or correction: `[CONTACT]`. Before launch, the operator must define identity verification, deadlines, backups, deletion, and any statutory retention.

## 9. Third-party components

The application may use WebLLM, Wllama, Mammoth.js, model repositories, CDNs, fonts, and a reverse proxy. Their own licenses and terms apply. Versions and sources are listed in `docs/MODELS.en.md`.

## 10. Legal review

Applicable law, jurisdiction, consumer rights, privacy, operator disclosures, and international availability must be reviewed for the actual operator and service. Do not publish this template as a complete legal notice without that review.
