# Agent instructions

## Purpose and scope

This is an unofficial driver-knowledge study aid for adults and teens, with supervised road-safety
learning for younger children. Keep the ordinary download-and-run experience simple. Do not claim
that the app guarantees a passing test, treats a learning condition, or authorizes someone to drive.

## Read first

Read `README.md`, `SECURITY.md`, `docs/ARCHITECTURE.md` and `docs/SIGN-REVIEW.md` before editing.
Inspect `git status`, the current branch and remote head. Preserve unrelated user changes.
The UI is `index.html`; built-in data are `questions.js`, `questions_more.js` and `ontario.js`.
`security.js` validates imports. `tools/app_server.py` launches `tools/secure_server.py`.

## Privacy and security — do not regress

- Never commit real names, personal emails, real profiles/scores, passwords, tokens, internal addresses,
  absolute user-home paths, private deployment notes or credential-file locations. Use synthetic data.
- Keep anonymous mode browser-only and generation disabled by default. Shared storage must remain
  explicitly password-protected and outside the repository/source directory.
- Keep loopback binding, the static-asset allowlist, authentication before upload reads, exact-origin
  write checks, custom request headers, bounded input and the Content Security Policy.
- Do not add wildcard CORS, unauthenticated storage APIs, arbitrary model URLs, remote tracking images,
  analytics or automatic public-tunnel startup. Do not expose a generic source-directory file server.
- Do not read credentials or real user records just to test. Do not change visibility, provision cloud
  services, commit, push, delete or rewrite history without the owner's authorization.
- Use neutral project attribution for any authorized commits; never import history from an older repository.

## Content correctness

- Treat road rules as safety-relevant and jurisdiction-specific. Check the current official handbook,
  including the image, caption, selected answer, alt text and printed page number together.
- Do not use an approximate drawing or a different country's sign as an official teaching example.
  Do not apply a rule from one province to another just because the image looks similar.
- Keep school areas separate from reduced-speed school zones; a warning symbol alone does not show
  every speed/time restriction. Explain what the pictured sign actually contains.
- `tools/sign_assets.json` records official handbook crops, page numbers, source URL and hashes.
- `tools/handbook_images.py` automatically uses those crops only for the exact reviewed source PDF.
  Keep the manifest's question/answer/alt-text mappings synchronized with the built-in bank;
  JavaScript regression tests check for drift. Never turn unreviewed nearest-caption guesses into
  graded answers. Add another source profile only after reviewing its actual artwork and meaning.
  Rebuild those assets with `python tools/rebuild_sign_assets.py --pdf <official-downloaded-guide.pdf>`
  using the pinned PDF. Never invent a crop or silently accept a changed PDF checksum.
- Do not commit full downloaded handbooks, learner uploads, scratch renderings or machine-specific paths.
  Retain required source/licence attribution and avoid government logos or endorsement claims.
- The remaining diagrams are schematics, not sign specifications. Check arrows, lane direction,
  vehicle placement and the question's right-of-way scenario. Label review limits honestly.
- If a source cannot confirm a question, flag it for review rather than inventing an answer.
- Keep imported/generated questions marked for human review. A quote match alone does not verify that
  a generated answer is correct. Update the sign review when changing teaching content.

## Verification

For code/content changes, first add a narrow failing regression test when applicable, then fix it.
Run:

```sh
python -m unittest discover -s tests -v
node --test tests/security.test.cjs
python -m compileall -q tools tests
```

The complete Python suite uses `defusedxml` for SVG checks. Ordinary app use is still dependency-free.
PyMuPDF is optional and needed only to rebuild handbook pictures or process PDF figures.
Check changes in a real browser using synthetic profiles. Inspect Study and Test/Results screens,
image loading, console/CSP errors, keyboard controls, alt text and a narrow mobile viewport.
Do not stop at a syntax check. Re-run privacy/secret checks before any authorized publication.
Report what passed, what was not exercised, and whether changes were actually pushed.

If using a temporary server or Cloudflare tunnel, expose only the sanitized app with synthetic data,
stop the processes afterwards, and verify the ports are closed. A running tunnel is not proof of
private-data protection. Keep the default beginner instructions free of tunnelling/AI setup steps.
