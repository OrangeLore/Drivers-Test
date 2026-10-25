# Driver's Knowledge Practice Test

Accessible practice tests with built-in Alberta and Ontario question banks, study mode,
adaptive practice, keyboard controls, text-to-speech, profiles and progress history.
This is an unofficial study aid. Verify answers against current official handbooks.

## Run locally

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
