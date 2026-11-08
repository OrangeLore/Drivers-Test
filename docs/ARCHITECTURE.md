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

## Offline Android edition

`android/MainActivity.java` hosts only bundled allowlisted assets through an intercepted virtual HTTPS
origin; it is not a server and opens no listening socket. There is no INTERNET permission. External
requests, file/content navigation, mixed content and automatic app-data backups are disabled.
Its narrow `NativeSpeech` bridge supports only installed offline text-to-speech and Stop; it cannot
open files, URLs or intents. Release WebView debugging is off.

`tools/build_android.py` adapts the existing page for Android, removes all server/API/generation
controls, and adds opt-in per-profile rewards. It leaves the desktop UI/server unchanged. Cosmetic
reward state is local, not an anti-cheat or authorization boundary. `rewards.js` owns the deterministic
coin/mastery rules; `parking.js` owns legal puzzle moves; `rewards-ui.js` supplies the phone UI.
The signed APK contains only the explicit learning/game assets and native activity, never Python,
private stores, source history or signing keys. See `android/README.md` for build and verification limits.
