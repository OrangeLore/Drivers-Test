# Road Trip Practice — offline Android edition

## Install on a phone

1. [Download the signed **`Road-Trip-Practice-1.0.1.apk`**](https://github.com/OrangeLore/Drivers-Test/releases/download/android-v1.0.1/Road-Trip-Practice-1.0.1.apk) onto the phone.
   GitHub's **Download ZIP** is source code, not an Android installer.
2. Open it from **My Files → Downloads**.
3. If Android asks, temporarily allow **Install unknown apps** for My Files (or the browser used).
4. Tap **Install**, then **Open**. Turn that install permission off afterwards.
5. Choose whether to enable achievements. Choose Alberta or Ontario and start with Study.

The package targets Android 8.0 or newer with an up-to-date Android System WebView. It has no
CPU-specific native library, so it is not restricted to one processor architecture. The Samsung
Galaxy S20 FE is within that intended platform range, but this build has **not yet been installed
or tested on a physical S20 FE**. If Android or Play Protect blocks installation, keep the warning
and ask for help rather than turning off all phone security settings.

There is no account, Python installation, running computer, internet connection or server required.
A system Android app-install dialog is normal for an APK installed outside Google Play.

## Optional rewards

A first-start choice is saved separately for each nickname profile. **Settings → Optional achievements
& rewards** can change it later. Disabling rewards stops new awards and hides the game, without
removing earned items. The starter collection contains cars, garage themes, stickers and cards;
players choose which to unlock. There are no purchases, advertisements, random draws, streak
penalties, expiring rewards or real-world prizes.

- First correct answer to a question: **5 coins**, once.
- Correct again in another mixed session at least **6 hours later**: **8 mastery coins**, once.
- Finish a session with at least **5 different questions** and new learning progress: **5 bonus coins**.
- A perfect test with at least **10 different questions** and new learning progress: **10 extra coins**.
- Repeating already-rewarded questions quickly does not earn additional coins.
- Repairing a previous mistake earns an achievement; deliberately getting a question wrong does not
  increase its coin payout. Mistakes never remove coins, bought items or earned mastery achievements.
- The parking logic game unlocks at **60 lifetime learning coins**. Its three levels unlock in order;
  each first solution gives **5 coins**, and replays are free. There is no timer.

These are cosmetic learning incentives, not a guarantee of engagement, test success or driving
competence. The parking puzzle is entertainment, not a driving simulator. Use the official handbook
and encourage understanding rather than memorizing answer positions.

### Sarcastic achievement announcements

Version 1.0.1 adds original, playful game-announcer pop-ups headed **NEW ACHIEVEMENT!**.
They celebrate correct topic answers and learning/collection milestones, not real driving competence.
For example, **MIRROR MIRACLE** says: “You learned what mirrors are for. Congratulations. Your head
can now do more than present your beautiful face to the world.”

There are 13 achievements, including mirrors, signals, seat belts, blind spots, stop signs,
pedestrians, speed limits, completing a session, repairing mistakes, a perfect mixed test,
spaced mastery, collecting cards and solving a puzzle. Each unlock is saved once per profile.
Unlocks queue at the end of a quiz, after a qualifying purchase or after a puzzle solution; they do
not interrupt answering a question. **Dismiss all** skips the remaining announcements without
removing earned badges. **Settings → Sarcastic pop-ups** disables announcements without disabling
the reward collection. Read-aloud is optional and requires an installed offline English voice.

## What stays on the phone

Profiles, scores, reward wallets and collections remain in Android's private app storage. Nickname
profiles on a shared phone are not password-separated accounts. The app requests no permissions,
including **no INTERNET permission**, has no analytics or ads, blocks external WebView requests,
and disables cloud backup and device-transfer backup for its app data.

Read-aloud uses an installed English voice that Android reports as offline. If no suitable voice is
installed, install one through Android's system text-to-speech settings; the app cannot download it.
Other apps and the phone's operating system have their own separate network/privacy settings.

Deleting a profile removes its local settings, reward wallet and test history. Uninstalling the app
or clearing its app data removes all progress. There is no cloud recovery or progress export in this
phone edition. Install future updates signed with the **same signing key** over the existing app to
keep progress; do not uninstall first. Keep the signing key backed up securely, never in public Git.

The desktop/web edition and its optional server tools remain unchanged. Desktop handbook generation
and test-set import/export are intentionally not included in the phone package. Built-in Alberta and
Ontario sets and reviewed sign pictures are bundled in the APK.

## Build from source (developer)

`tools/build_android.py` generates an Android-only adaptation of the existing HTML; do not hand-edit
its generated assets. `rewards.js`, `parking.js`, `rewards-ui.js`, `rewards.css` and `achievement-popups.css` belong to the Android
edition. The existing desktop `index.html` and server do not load them.

Prerequisites: [Python 3.11+](https://www.python.org/downloads/), [Java 21 JDK](https://adoptium.net/temurin/releases/?version=21)
with `java`, `javac` and `keytool` on PATH, and the official Android SDK **platform 35/build-tools 35.0.0**.
No Gradle, model account, cloud build or APK signing service is needed. Node.js is needed only for
JavaScript regression tests on the build computer, never on the phone.

### 1. Get and inspect the source

Clone this repository or download/extract its source ZIP. For the published Android source, select
the `android-v1.0.1` tag. Run commands from the extracted project root (the folder containing `tools/`).
Review `android/MainActivity.java`, `android/AndroidManifest.xml`, `tools/build_android.py`, the reward
and puzzle files listed above, and `tests/`. The APK's private signing key is intentionally not public.

### 2. Install an isolated Android SDK

Download the official [Android command-line tools](https://developer.android.com/studio#command-line-tools-only)
and follow the [sdkmanager setup instructions](https://developer.android.com/tools/sdkmanager).
Use a dedicated SDK folder with **one platform and one build-tools version**; the builder rejects
ambiguous SDK folders. If using Android Studio, its SDK Manager can install the same packages.
Accept the Android SDK licences interactively. Example, after `sdkmanager` is on PATH:

```sh
sdkmanager --sdk_root=/path/to/isolated-sdk --licenses
sdkmanager --sdk_root=/path/to/isolated-sdk "platforms;android-35" "build-tools;35.0.0"
```

On Windows use `sdkmanager.bat` and replace the example paths with your own quoted paths.
Keep SDK packages, build intermediates and signing files **outside the cloned repository**.

### 3. Create your own private signing key

Create a private folder outside the repository, then run the following, replacing the placeholder
keystore path. `keytool` prompts for its password rather than exposing it in shell history:

```sh
keytool -genkeypair -storetype PKCS12 -keystore /private/roadtrip.p12 -alias roadtrip -keyalg RSA -keysize 3072 -validity 10000 -dname "CN=Road Trip Practice"
```

Keep this key and its password securely backed up. Reuse the same key for your future builds.
**Your independently signed APK cannot update over the publisher-signed APK.** Android requires
the same signing key for an in-place update. A clean install of your own build may require removing
the publisher build first, which deletes its local progress. Do not publish or send anyone a private key.

### 4. Build and verify the APK

The signer reads its password from a process environment variable. Do not put a real password into
source files, shell command arguments, CI configuration, shared logs or Git.

**Windows PowerShell** (replace every placeholder path):

```powershell
$secret = Read-Host "Keystore password" -AsSecureString
$env:ROADTRIP_SIGNING_PASSWORD = [System.Net.NetworkCredential]::new('', $secret).Password
try {
  python tools/build_android.py --sdk "D:/Android/sdk" --work "D:/Android/build-work" --keystore "D:/Private/roadtrip.p12" --store-pass-env ROADTRIP_SIGNING_PASSWORD --out "D:/Android/output/Road-Trip-Practice.apk"
} finally {
  Remove-Item Env:ROADTRIP_SIGNING_PASSWORD -ErrorAction SilentlyContinue
  Remove-Variable secret -ErrorAction SilentlyContinue
}
```

**Bash on Linux/macOS** (replace every placeholder path):

```bash
read -r -s -p "Keystore password: " ROADTRIP_SIGNING_PASSWORD
printf '\n'
export ROADTRIP_SIGNING_PASSWORD
python tools/build_android.py --sdk /path/to/isolated-sdk --work /path/to/build-work --keystore /private/roadtrip.p12 --store-pass-env ROADTRIP_SIGNING_PASSWORD --out /path/to/output/Road-Trip-Practice.apk
unset ROADTRIP_SIGNING_PASSWORD
```

Use `python3` instead of `python` if that is how Python 3 is installed. Windows builds were exercised
directly; Linux/macOS tool-name support is implemented but APK compilation on those hosts has not
been verified. The builder prints signature verification and package metadata and writes an
`.apk.sha256` file next to the output. APK archive timestamps, SDK revisions and a different signing
key can change its checksum; independent builds are not promised to be byte-identical to the release.

The builder compiles Java/D8 and Android resources with the official tools, packages only an explicit
asset allowlist, aligns the APK and verifies its Android signature. APK signing certificates identify
only the project, not a personal name/email. All signer private material remains outside the source
and APK. Do not create signing keys or store their passwords in CI logs or public repository secrets.
For an HTML-only browser check, use `--assets-only /path/to/isolated-assets`; a temporary test web
server for that folder is a development aid, **not** a component of the installed Android app.

Run regressions:

```sh
python -m pip install defusedxml==0.7.1
python -m unittest discover -s tests -v
node --test tests/security.test.cjs tests/rewards.test.cjs tests/parking.test.cjs
```

Before release, verify the APK signature, compiled permissions/backup configuration, packaged file
inventory, secrets/privacy scan, quiz → rewards → purchase → equip → puzzle behavior, reload
persistence, disabled rewards and separate profiles. A successful desktop browser run is not proof of
physical-phone installation, native read-aloud, system Back behavior or Samsung-specific layout.

Handbook artwork attribution and the software licence are included as `LICENSE.txt` and
`SIGN-REVIEW.txt` inside the APK. See the repository's `LICENSE` and `docs/SIGN-REVIEW.md`.
