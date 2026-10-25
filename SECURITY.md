# Security and privacy

## Boundaries

- Default: public UI, browser-local profiles and scores, no shared storage or generation API.
- Private mode: unique environment password, constant-time comparison, authentication on all routes,
  same-origin/custom-header checks for writes, bounded requests and shared storage outside source.
- Only explicit app files and top-level road-sign images are served. No directory listings,
  repository internals, documentation, scripts, credentials or runtime data are served.
- Strict script CSP with exact inline-script hashes; no inline event handlers, third-party scripts,
  analytics, remote dataset images or remote model endpoints. Inline styles remain allowed for UI controls.
- Network limits reduce accidental exposure; the bundled standard-library server is not a hardened
  internet application server. Use Cloudflare Access for private deployment. Do not expose its port directly.
- Password holders share the same dataset and profiles. This is not per-user isolation.
- Generation is opt-in for trusted operators. A malicious/oversized PDF can still exhaust a parser;
  use verified official files, keep dependencies patched, and do not offer anonymous PDF processing.
- Browser speech voices may be local or provider-backed depending on browser/OS. Do not speak secrets.

## Public-release checklist

1. Scan every tracked file and the complete reachable Git history for secrets and personal details.
2. Audit commit author/committer metadata, branches, tags, PR refs, releases, Actions logs and artifacts.
3. Keep user data, environment files, logs and tunnel credentials outside Git and deployment assets.
4. Run tests, dependency auditing and a fresh-clone verification. Inspect the actual exposed routes.
5. History rewriting removes reachable history, not copies, old clones, hidden GitHub refs or caches.
   Contact GitHub Support for cached-view/unreachable-object removal when sensitive old commits remain
   retrievable. Rotate any exposed secret rather than relying on deletion.
6. GitHub account ownership and public activity remain visible even with neutral commit attribution.
   Public source hosting under an existing account cannot provide personal anonymity.
7. Do not declare an unknown live installation clean: identify its URL, deployment source and data
   directory, then migrate deliberately without publishing or deleting personal records.

Report security problems privately to repository maintainers. Do not post secrets in issues.
