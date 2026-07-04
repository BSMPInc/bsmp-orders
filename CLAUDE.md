# CLAUDE.md — BSMP Internal App Suite

Instructions for Claude Code when working in this repository. Read this before editing any file.

## What this repo is

`bsmp-orders` (GitHub org `BSMPInc`) holds the internal business apps for **Bert's Sheet Metal Products (BSMP)**, a sheet metal fabrication shop in Chatsworth, CA. The apps are maintained by the shop owner/operator, who is hands-on but is **not a trained software developer** — explain what you're doing in plain terms, and favor small, reviewable changes over large rewrites.

The suite is four self-contained apps plus supporting files:

| File | App | Purpose |
|------|-----|---------|
| `quote.html` | Quote Tool | Laser/fab quoting, printable PDFs, quote archive, pricing engine |
| `orders.html` | Order Tracker | On-time delivery, scheduling, dispatch board, team load |
| `apar.html` | AP / AR Tracker | Accounts payable/receivable, bills, pay runs, aging |
| `qc.html` | Inspection / QC | Self-checks, First Articles, NCRs, material certs |

All four are deployed as static files on **GitHub Pages** from this repo. There is no build step and no server — see "Architecture" below.

## Per-app deep-dive guides — READ THE MATCHING ONE

This root file is the shared overview. Each app also has a focused guide with its
pages, functions, data shapes, and gotchas. **Before doing real work on an app,
open its guide:**

- Working on `quote.html`  → read **`quote.md`**
- Working on `orders.html` → read **`orders.md`**
- Working on `apar.html`   → read **`apar.md`**
- Working on `qc.html`     → read **`qc.md`**

(These live in the repo root alongside the apps. They don't auto-load — read the
one that matches the file you're about to edit. If a task spans two apps, read both.)

## Golden rules

1. **One file per app.** Each app is a single self-contained `.html` file: all HTML, CSS, and JS live inside it. Do **not** split an app into separate `.js`/`.css` files or add a bundler, framework, or npm build. This is a deliberate constraint — it keeps deployment to "commit the file and it's live."
2. **No build tooling.** No React/Vue/webpack/vite. Plain HTML + vanilla JS + inline `<style>`. Libraries come only from CDN `<script>` tags.
3. **Edit surgically.** Prefer targeted edits (find the function, change it) over regenerating whole files. These files are large (see sizes below); rewriting them wholesale risks losing working features.
4. **Validate before finishing.** After editing an app's JavaScript, run a syntax check (see "Validating changes"). A broken app deploys just as fast as a working one.
5. **Preserve the shared conventions.** The four apps intentionally share an auth model, a Firebase backend, a design system, and a cross-app nav. Keep them consistent — a change to the pattern in one app usually should be mirrored in the others.

### File sizes (approximate — expect large files)

- `quote.html` ~8,600 lines
- `orders.html` ~5,900 lines
- `apar.html` ~4,400 lines
- `qc.html` ~2,100 lines

## Architecture (shared across all four apps)

### Single Firebase backend

Every app points at the **same** Firebase project:

- projectId: `bsmp-orders`
- databaseURL: `https://bsmp-orders-default-rtdb.firebaseio.com` (Realtime Database)
- storageBucket: `bsmp-orders.firebasestorage.app` (Cloud Storage, for uploaded files/drawings)
- authDomain: `bsmp-orders.firebaseapp.com` (Email/password auth)

Firebase is loaded as ES modules from `gstatic.com` inside a `<script type="module">` block at the bottom of each file. That module does the Firebase I/O and exposes a small set of `window.*` bridge functions (e.g. `window.qcSet`, `window.saveOrder`, `window.saveQuote`) so the "classic" (non-module) UI script can call them. The classic script renders the UI and holds app state; the module script talks to Firebase. Keep that split when adding features.

### Realtime Database layout (namespaced per app)

Each app owns a top-level namespace, and some apps read across namespaces:

- **quote.html** → owns `quotes/`
- **orders.html** → owns `orders/`, plus `team`, `customers`, `durations`, `jobCounter`, `trash/`, `backups/`, `backupIndex`; also reads `quotes`
- **apar.html** → owns `apar/*` (`apar/entries`, `apar/accounts`, `apar/vendorAccounts`, `apar/vendorAliases`, `apar/recurring`, `apar/audit`, `apar/depositLog`, `apar/apSplit`, etc.); also reads `orders`
- **qc.html** → owns `qc/*` (`qc/inspections`, `qc/ncr`, `qc/certs`, `qc/audit` — append-only change history); also reads `orders` and `quotes`

**When adding a new data path, keep it under the app's own namespace** (e.g. new QC data goes under `qc/…`, new AP/AR data under `apar/…`). Cross-app reads are fine; cross-app writes should be rare and intentional.

> ⚠️ **RTDB + Storage security rules live server-side, not in this repo.** If you add a new path (e.g. `qc/firstArticles`), the database and storage rules must be updated in the Firebase console to allow it, or saves will fail *silently*. This is a known past gotcha in `qc.html`. Rule changes take effect immediately and do **not** require a GitHub Pages redeploy. If a save mysteriously does nothing, suspect missing rules first.

### Cloud Storage upload prefixes

Uploaded files (drawings, cert PDFs, invoices) are stored under the owning app's prefix: `quotes/…`, `orders/…`, `apar/…`, `qc/…`. Follow the existing prefix when adding uploads.

### Auth + role model (operator vs manager)

- Email/password sign-in via Firebase Auth.
- **Two roles: `operator` and `manager`.** An email is treated as operator if it's in `OPERATOR_EMAILS` (currently `['operator@bertsmp.com']`) or the local-part starts with `operator`; everyone else is a manager.
- Operators get a restricted view. UI that is manager-only is hidden with the `mgr-only` CSS class (`body.role-operator .mgr-only{display:none}`) — reuse that pattern rather than inventing new gating.
- Keep this model identical across apps.

### AI features (Claude via a proxy)

`quote.html` and `qc.html` call the Anthropic API for AI extraction (reading drawings, certs, invoices, dimension "ballooning").

- Model string in use: **`claude-sonnet-4-6`**.
- Preferred path is a **Cloudflare Worker proxy** (`bsmp-ai-extract`, a `*.workers.dev` URL) so the API key is never shipped in client code. The proxy URL is read from `localStorage['bsmp_proxy_url']`.
- There is a fallback to a direct browser call using `localStorage['bsmp_apikey']` — this exposes the key in the browser and is only for local testing. **Do not hardcode an API key in any `.html` file**, and don't remove the proxy path.
- `qc.html` reuses the same proxy/key that `quote.html` sets, since they run on the same origin.

## Design system (shared)

- **Font:** `Hanken Grotesk` (Google Fonts), with system-ui fallbacks.
- **Canvas:** warm "oat" background `--bg:#f5f2ea`, white cards, a dot-grid texture. Square corners (`--radius:0`). Subtle shadows.
- **Shared neutrals:** text `#1e2227`/`#23262b`, `--text2` ~`#5b6675`, `--text3` ~`#8a93a5`, borders `--border ~#e7e5df` / `--border2 ~#d7d2c1`.
- **Shared "spark" accent:** `--spark:#d42b2b` (the red used for the logo flag underline / active indicators).
- **Per-app accent family** (this is how you tell the apps apart at a glance — keep each app's accent consistent):
  - `quote.html` → **blue** `--accent:#1e3a5f`
  - `orders.html` → **maroon** `--accent:#6a1f2e`
  - `apar.html` → **green** `--accent:#1f4d38` (AR green `#2f8f6b`, AP red `#a8443a`)
  - `qc.html` → **graphite** `--accent:#3a4049`
- **Shell pattern:** fixed left sidebar with a "logo flag," a collapsible/pinnable rail (`bsmp_sidebar_pinned` in localStorage), a sticky topbar with the spark underline, and a bottom **dock** that also holds the cross-app switcher.

### Cross-app navigation

Each app's dock/sidebar links to the other three by relative filename (`quote.html`, `orders.html`, `apar.html`, `qc.html`). If you rename a file or add an app, update the nav in **all** apps.

## Coding conventions

- **Vanilla JS**, no framework. State is held in module-level variables in the classic script; the UI re-renders by rebuilding `innerHTML` from `render()`-style functions.
- **Curly apostrophe:** inside user-facing strings in template literals, use the curly apostrophe `’` (U+2019), not a straight `'`, since straight apostrophes would break the surrounding template literal. (Present in `orders.html`/`apar.html`; follow it when adding UI text.)
- **i18n:** `qc.html` has a full EN/ES toggle via a `t()` function and an `I18N` map, with `data-t` / `data-tph` attributes for static text. If you add user-facing strings to `qc.html`, add both the English key and the Spanish translation, and wrap them in `t(...)`. The other apps are currently English-only.
- **Escape user content** with the existing `esc()` helper before putting it into `innerHTML`.
- **Firebase writes** go through the app's existing helper (e.g. `dbSet`/`qcSet`/`saveOrder`), which already sanitize `undefined` → `null` and surface errors via a toast. Don't call the raw Firebase `set()` directly from the UI script.
- **IDs and toasts:** reuse the app's existing toast/notification helper for save feedback rather than `alert()` where a toast pattern already exists.

## Validating changes

There is no automated test suite. Before considering a change done:

1. **Syntax-check the JavaScript.** The reliable way, given the module + classic split, is to confirm the classic script block parses. If you have Node available, extracting the non-module `<script>` blocks and running them through `new Function(src)` (or `node --check` on an extracted `.js`) will catch syntax errors. At minimum, do a careful read of the edited function and its braces/parens.
2. **Open the file in a browser** (or the Code preview) and click through the affected feature while signed in. Watch the console for errors.
3. **Check Firebase actually saved** — if you touched a data path, confirm the write lands in the RTDB and that a matching security rule exists for any new path.

## Deploying

- Deployment = **commit to the repo**; GitHub Pages serves the updated file. There is no separate build/publish step.
- Server-side Firebase **security-rule** changes are made in the Firebase console and are **not** in this repo; they take effect immediately without a Pages redeploy.
- Make small commits with clear messages describing the user-facing change (e.g. "qc: add zoom to balloon workspace").

## Business/domain context (helps when reading the apps)

- BSMP does laser cutting, forming/bending, and welding of sheet metal (incl. stainless like 304/316L). Quoting math involves material weight, bend complexity, nesting efficiency, laser speeds, and job tiers (Commodity / Standard / Precision / Rush).
- QC covers operator self-checks, First Article Inspection (Simple FAR and AS9102 modes, with drawing "ballooning"), Nonconformance Reports (NCRs), and mill/material certs with traceability.
- A prior architecture review concluded **AS9100 is feasible** for this stack (needs immutable audit trail, named-user stamping, software-validation docs) but **ITAR is out of scope** for the current Firebase/Cloudflare/Anthropic setup. Keep ITAR-restricted data handling conservative.

## Quick "where do I start" for common tasks

- **Change quoting math / pricing / laser speeds** → `quote.html`
- **Scheduling, dispatch board, team load, order cards** → `orders.html`
- **Bills, vendors, pay runs, AR/AP aging, invoices** → `apar.html`
- **Self-checks, First Articles, balloons, NCRs, certs** → `qc.html`
- **A save silently does nothing** → check the Firebase security rules for that path first, then the write helper, then the console.
