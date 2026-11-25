# BoxBox Builds

Public-safe static engineering blog for F1 Telemetry and GRIDLOCK. The initial four companion articles are designed to publish together so their links can be verified before the queued social posts. This source contains public-ready text and imagery only; internal evidence, raw recordings and private renderer code must stay in the private workspace. `social_date` records the corresponding social edition, not the actual blog publication date.

## One-time GitHub setup

1. Create `shivangsarat/builds-boxbox` as a **public** repository (initialize with README). Grant the existing GitHub connection access to it if repository access is restricted. Never make the private renderer public.
2. Upload/commit these source files (except `dist`, which is generated). In repository Settings → Pages → Build and deployment → Source, choose **GitHub Actions**. If the initial push predates this setting, run **Publish BoxBox Builds** manually once.
3. Verify the deployment and anonymously retrieve the home page and all four canonical article URLs before editing Buffer. If the Pages URL differs, change `BASE` in `scripts/build.py` before deployment.

## Local preview

Python 3.12 recommended. `pip install -r requirements.txt`, `python scripts/build.py`, `python scripts/check.py`, `python -m http.server 8000 --directory dist`. No JavaScript framework or backend needed.

## Future publication

Each approved article is a Markdown file and a metadata entry in `articles/index.json`, with a sanitized PNG and meaningful alt text. The agent should stage and review new articles privately, then commit only the final public-safe content to the public repository. Entries marked `approved: true` are emitted. **Unapproved material must never be committed to a public repository**, even if the builder omits it. The deployment workflow automatically rebuilds and publishes on a push to `main`. The first four articles should be made available ahead of their matching social dates, not embargoed in a public repository. Future articles should likewise be deployed and anonymously verified before queueing their social companions. No new server, token, custom domain or paid hosting required for public Pages. GitHub Actions deployment can be delayed or fail: verify the deployed page and do not attach a guessed link. Public release timing is best treated as an advance release, not a precise scheduled event.

The workflow deploys only `dist`. It grants Pages write and OIDC permissions only to the deployment job. The generator disables raw Markdown HTML, escapes metadata, and rejects common private-evidence markers; editorial sanitization remains necessary. Only approved source assets are copied. Keep all evidence and credentials outside this repository. The search is client-side across article title, description, project and tags. RSS and sitemap generated on each build. Code fences are syntax-highlighted at build time. Architecture illustrations are static and explicitly conceptual.
