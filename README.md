# Driver's Knowledge Practice Test

Accessible practice tests with built-in Alberta and Ontario question banks, study mode,
adaptive practice, keyboard controls, text-to-speech, profiles and progress history.
This is an unofficial study aid. Verify answers against current official handbooks.

## Start here — no Git experience needed

1. On this GitHub page, click the green **Code** button, then **Download ZIP**.
2. Extract the ZIP into a normal folder. Do not run it from inside the ZIP.
3. Install **Python 3.11 or newer** from [python.org](https://www.python.org/downloads/).
   On Windows, select **Add Python to PATH** during installation.
4. **Windows:** open the extracted folder and double-click **`run.bat`**.
   **Mac/Linux:** open a terminal in the folder and run **`bash run.sh`**.
5. Your browser should open the app. If it does not, open **http://127.0.0.1:5600**.
6. Choose **Alberta** or **Ontario**. Try **Study** first, then **Start a Practice Test**.

Keep the server window open while practising. Close that window to stop the app.
If you see “Python not found,” install Python, then close and reopen the launcher.
You do **not** need Git, Node.js, an AI model, a paid account or a Cloudflare tunnel for ordinary practice.
Making this GitHub repository public does not create a hosted website: download it and run it locally.

## What it does

- Built-in Alberta Class 7 and Ontario G1 practice questions.
- One question at a time, with large answer buttons and no countdown timer.
- Road-sign pictures, traffic diagrams and text descriptions of pictures.
- **Study:** browse answers, search questions and filter by topic.
- **Practice Test:** try a random test, then review your answers and handbook references.
- **Learner Mode:** give extra practice to questions and topics missed previously.
- Easy, standard and hard difficulty choices.
- **Read aloud:** hear questions and answers using your browser's speech voices.
- Larger text, high-contrast colours and an optional easier-reading font.
- Keyboard controls: **1–4** to choose, **Enter** for next, **R** to read aloud.
- Separate nickname profiles, scores and progress history.
- Flag questions for later review, and import/export additional JSON question sets.
- Optional, advanced local-AI handbook generation and password-protected cross-device storage.

## For adults, teens and younger learners

- **Adults and teens preparing for a knowledge test:** practise in short sessions, review mistakes,
  and use the official handbook alongside the app. Beginners and returning drivers can work at their own pace.
- **People who prefer listening or less text at once:** read-aloud, one-question screens, large controls
  and display settings offer different ways to practise. These are convenience/accessibility features,
  not a diagnosis, treatment or a guarantee of a passing score.
- **Parents, tutors and instructors:** discuss why an answer is right; start with Study, then try a short
  session together. Use nicknames rather than real names.
- **Younger children:** use the pictures for supervised conversations about road signs, pedestrians
  and road safety. Some licence-test content is intended for older learners. The app does not qualify
  anyone to drive or replace legal age requirements, lessons or adult supervision.

**Privacy:** by default, profiles and scores stay in this browser on this computer. They are not
automatically shared with another device. People sharing the same browser can see them. A different
browser, private-browsing session, or clearing browser data may remove access to that progress.

**Sign accuracy:** the reported sign drawings were checked against the official guides. See
[the illustrated sign review](docs/SIGN-REVIEW.md) for sources, corrections and remaining scope limits.
This is an unofficial study aid, not a government test or a substitute for the current official handbook.

<details>
<summary><strong>Advanced setup, handbook generation, private sharing and developer tests</strong></summary>

## Run locally from a terminal

Python 3.11+ is required. The built-in app needs no third-party packages.

```sh
python tools/app_server.py 5600
```

Open http://127.0.0.1:5600, or use `run.bat` / `run.sh`.
**Default mode is browser-only:** no shared profiles, no uploads and no generation API.
Use nicknames; browser storage is not encrypted and people sharing a browser can see its data.
The server binds only to loopback, not your LAN. Do not run `python -m http.server` in this source tree.

## Optional private shared mode

Set `AC7_PASSWORD` to a unique randomly generated password of at least 16 characters in
your process environment before starting. Do not put it in source, commands saved to shared logs,
or Git. Your browser prompts for username `user` and this password. All routes require it.
Everyone sharing the password can access every profile: this is not multi-tenant authorization.
Use only loopback HTTP or HTTPS through a trusted tunnel. Browser Basic-auth sessions may remain
cached until you close the browser; do not use shared/public machines for private data.

Shared data is saved **outside the source tree**, by default in the operating-system user-data
folder under `driver-practice/store/`. `AC7_DATA_DIR` can override this with a private external directory.
Protect that directory with OS permissions. Existing data is not automatically migrated or deleted.

## Optional handbook generation

Install optional packages in a virtual environment using `requirements.lock`.
Run a local OpenAI-compatible model, set `AC7_LLM_URL` (default http://localhost:1234/v1)
and `AC7_MODEL` to its model ID. Only loopback HTTP model endpoints are supported.
Set `AC7_ENABLE_GENERATION=1` **and** `AC7_PASSWORD` for in-app generation.
Use trusted official PDFs only: PDF parsers are not a security sandbox. Uploads are limited to 10 MB.
The public mode deliberately disables generation to prevent strangers consuming local resources.
Generated questions require review; grounding checks do not prove the selected answer is correct.

### Automatic sign pictures — no AI drawing

- Upload the exact **Alberta Driver’s Guide, Spring 2026** linked in [SIGN-REVIEW.md](docs/SIGN-REVIEW.md).
  The app recognizes its checksum and automatically pairs **36 reviewed handbook pictures** with
  the checked questions, answers and picture descriptions. You do not need to match them yourself.
- These are the verified source crops bundled with the app, not new AI drawings or approximate matches.
  The result embeds the pictures, source-page references and licence attribution in its JSON.
- For a **picture-only set**, request **36 questions** with automatic test format. This path does
  not need a running AI model, although PDF text extraction still needs the optional packages.
  Requesting more questions uses the local model for additional **text-only** questions.
- A different PDF or changed handbook edition gets a visible **unreviewed-source warning**, not
  guessed sign pictures. Other provinces/editions need their own reviewed source profile first.
- Study shows the picture-review status. Continue to review generated text questions yourself.

CLI: `python tools/generate_dataset.py --pdf handbook.pdf --key sample --name Sample --n 30 --out sample-testset.json`.
Imported JSON is limited and validated. Remote tracking images and executable content are rejected.
Cropped handbook images are embedded in the private result rather than saved into public assets.

## Cloudflare quick-tunnel test

Install `cloudflared` separately. Start the app with `AC7_ALLOW_TUNNEL=1`, then in a separate terminal:

```sh
cloudflared tunnel --url http://127.0.0.1:5600 --no-autoupdate
```

This creates a temporary public HTTPS URL. It is **not** Cloudflare Access protection.
Public mode is suitable only for a demo with browser-local data. Private shared mode still requires
the app password. For shared-mode writes through any tunnel, set `AC7_ALLOWED_ORIGINS` to its exact
HTTPS origin (scheme and hostname, no trailing slash), then restart the app. For a named tunnel
set `AC7_ALLOWED_HOSTS` to its exact hostname and configure
Cloudflare Access separately. Never tunnel a source-directory file server or model endpoint.
Stop both processes after testing. Quick tunnels are not a production uptime guarantee.

## Verification

```sh
python -m unittest discover -s tests -v
node --test tests/security.test.cjs
```

See `SECURITY.md` for the threat model and public-release checklist. MIT software license;
see `LICENSE` for separate bundled-data ownership notes.

</details>
