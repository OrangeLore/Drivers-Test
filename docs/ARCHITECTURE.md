# Architecture

`index.html` contains the accessible UI. `security.js` validates imported datasets and image sources.
The built-in banks are `questions.js`, `questions_more.js` and `ontario.js`.

`tools/app_server.py` launches `tools/secure_server.py`. Public mode only serves allow-listed assets
and non-sensitive health metadata. Private mode requires a process-environment password for every
route. Shared profile storage is external to the source tree. Generation is disabled unless explicitly
configured. `tools/generator.py` is the common grounded local-model pipeline for API and CLI use.

No private deployment inventory, identities, local workstation paths or credential locations belong
in project documentation. Runtime logs and generated data must stay untracked.
