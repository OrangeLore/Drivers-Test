# Android 1.0.1 — verification and limitations

## Published installer

- File: `Road-Trip-Practice-1.0.1.apk`
- Package: `org.driverpractice.roadtrip`
- Version: `1.0.1` / Android version code `2`
- Minimum Android API: `26` (Android 8.0); target API: `35`
- SHA-256: `3428f8ddc060f0aed63fada5a00c6e0d58e07906eeb53de1e955c5d6028065d1`
- APK v2/v3 signatures verified. Certificate subject: `CN=Road Trip Practice`.
- Signing certificate SHA-256: `f940fcd4b082e4b7127ddc17d5a306323e1c16285d74e4747d9788a9b9df62fd`.

The signing certificate/public fingerprint is not a private signing key. Private signing material
and passwords are deliberately excluded from this repository and release assets.

## Android acceptance

The app was installed and updated through ADB on an Android 11 Redroid emulator with WebView 118.
It launched successfully. The installed `base.apk` checksum was read back and matched the installer
listed above. Tests used only synthetic nickname profiles and practice records.

Exercised installation/update, full quizzes/results, coin awards, sarcastic announcements,
acknowledgement/dismissal, card purchases/collector badge, a solved parking puzzle/parking badge,
profile creation, announcement opt-out while still earning badges, Android Back dismissal,
update/restart persistence and settings persistence. Native testing identified and led to fixes for
initially clipped/scrolled popup headings, Back handling and the stale coin header after a quiz.
Earlier acceptance quizzes recorded 30/30; the final APK test also exercised the unanswered-question
confirmation, recording 29/30 with one blank answer. App-scoped runtime log checks found no fatal
or JavaScript/CSP execution errors.

## Regression and package checks

- 35 Python and 22 JavaScript tests passed; syntax and whitespace checks passed.
- Reward tests cover opt-in/out, replay prevention, spaced mastery, mistake recovery, purchases,
  equipment, saved-state migration and one-time topic achievement triggers.
- Every shipped puzzle has a legal solution verified by an independent breadth-first search test.
- Compiled manifest requests no permissions, including no INTERNET permission; debugging,
  cleartext traffic and app backup are disabled. Backup/device-transfer exclusion rules are included.
- Exactly 60 approved learning/game/licence assets are included. Each was compared byte-for-byte
  against output from the published asset builder. No server/Python runtime is inside the APK.
- Source and extracted assets were scanned for secrets; source and decompressed APK entries were
  separately reviewed for personal identifiers, local paths and private addresses. No findings detected.
- No local learner records, emulator connection details, signing key or credential files are bundled.

## What has NOT been verified

- Physical Samsung Galaxy S20 FE installation, Samsung-specific behavior and physical-device audio.
- Audible read-aloud: the test emulator has no installed text-to-speech engine. The app provides an
  offline-English-voice hint; it cannot download a voice and does not claim audio succeeded.
- APK compilation on Linux/macOS. The build script supports the corresponding SDK executable names,
  but the exercised compilation host was Windows with Java 21 and Android SDK 35 tools.
- A fresh legal/content audit of every text-only road-rule question. Use current official handbooks.

These are specific test results, not a guarantee against all vulnerabilities or complete anonymity.
GitHub ownership remains visible. No reward system guarantees engagement, perfect scores or driving
competence. See [the Android guide](README.md), [security notes](../SECURITY.md) and
[handbook-artwork review](../docs/SIGN-REVIEW.md).
