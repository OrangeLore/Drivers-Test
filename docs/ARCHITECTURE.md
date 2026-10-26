# Architecture

`index.html` contains the accessible UI. `security.js` validates imported datasets and image sources.
The built-in banks are `questions.js`, `questions_more.js` and `ontario.js`.

`tools/app_server.py` launches `tools/secure_server.py`. Public mode only serves allow-listed assets
and non-sensitive health metadata. Private mode requires a process-environment password for every
route. Shared profile storage is external to the source tree. Generation is disabled unless explicitly
configured. `tools/generator.py` is the common grounded local-model pipeline for API and CLI use.

`tools/handbook_images.py` identifies the reviewed source PDF by SHA-256 and pairs its bundled,
checksum-verified PNG crops with the curated teaching mappings in `tools/sign_assets.json`.
Known-source visual questions require no model. The result carries `imageAudit` and per-picture
provenance; Study displays the audit message. Unknown editions remain text-only with a warning.
Nearest-caption extraction in `tools/figures.py` is only an inspection aid, never a source of
automatically graded answers. Text-model output cannot add pictures or image-dependent questions.

No private deployment inventory, identities, local workstation paths or credential locations belong
in project documentation. Runtime logs and generated data must stay untracked.
