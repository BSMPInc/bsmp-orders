# BSMP Internal App Suite

Internal business apps for **Bert's Sheet Metal Products (BSMP)** — a sheet metal fabrication shop in Chatsworth, CA. Four self-contained web apps that run the shop's quoting, order tracking, accounts, and quality control, backed by a shared Firebase project and served as static files from GitHub Pages.

## The apps

| App | File | What it does |
|-----|------|--------------|
| **Quote Tool** | [`quote.html`](quote.html) | Laser/fab quoting with a full pricing engine (material weight, bend complexity, nesting, laser speeds, job tiers), customer-facing printable PDFs with auto-incrementing quote numbers, and a quote archive. |
| **Order Tracker** | [`orders.html`](orders.html) | On-time delivery: backward scheduling from the due date, a Daily Dispatch board, an AI daily stand-up, Team Load, PO tracking, and soft-delete/recovery. |
| **AP / AR Tracker** | [`apar.html`](apar.html) | Accounts payable & receivable: bills and invoices, vendor/customer parties, pay runs, aging, deposits, recurring items, cash view, and a calendar. |
| **Inspection / QC** | [`qc.html`](qc.html) | Quality control: operator self-checks, First Article Inspection (Simple FAR + AS9102), an NCR tracker, and a material-cert archive with traceability. Full English/Spanish toggle. |

Each app links to the other three from its in-app navigation, so they work together as one suite.

## How it's built

- **One file per app.** Each app is a single `.html` file containing all its HTML, CSS, and JavaScript. No build step, no bundler, no framework — plain vanilla JavaScript with a few libraries loaded from CDN.
- **Shared Firebase backend.** All four apps use the same Firebase project (`bsmp-orders`): Realtime Database for data, Cloud Storage for uploaded files (drawings, cert PDFs, invoices), and email/password auth.
- **Namespaced data.** Each app owns its own database area — `quotes/`, `orders/`, `apar/*`, `qc/*` — and some apps read across namespaces (for example, QC links inspections to orders).
- **Two roles.** Users sign in as either an **operator** (restricted view) or a **manager** (full access).
- **AI features.** The Quote and QC apps use Claude (via a Cloudflare Worker proxy that keeps the API key server-side) to read drawings, certs, and invoices.

## Design

A shared design system keeps the suite consistent while giving each app its own identity:

- **Type & canvas:** Hanken Grotesk on a warm "oat" background with square corners and subtle shadows.
- **Per-app accent color** (so you always know which app you're in):
  - Quote — **blue**
  - Orders — **maroon**
  - AP/AR — **green**
  - QC — **graphite**
- Shared shell: a collapsible/pinnable sidebar, a topbar with a red accent underline, and a bottom dock that switches between the apps.

## Deploying

There's no build or publish step. **Committing a change to this repo updates the live app** via GitHub Pages.

> **Note:** Firebase security rules (which control what each database and storage path allows) are configured in the Firebase console, **not** in this repo. They take effect immediately without a redeploy. If a save appears to do nothing, a missing security rule for that path is the most common cause.

## Working on the code

If you're using Claude Code (or another AI assistant) in this repo, start with the guidance files:

- **[`CLAUDE.md`](CLAUDE.md)** — the shared overview: architecture, conventions, the role model, the design system, and the gotchas that apply across all four apps.
- **Per-app deep dives** — read the one matching the app you're editing:
  - [`quote.md`](quote.md) · [`orders.md`](orders.md) · [`apar.md`](apar.md) · [`qc.md`](qc.md)

## Business context

BSMP does laser cutting, forming/bending, and welding of sheet metal (including stainless like 304/316L). The apps replaced spreadsheet-based tracking and cover the shop's workflow end to end: quote a job, track it through production and delivery, manage the money in and out, and document quality. A prior review found **AS9100 certification feasible** for this stack; **ITAR is intentionally out of scope** for the current architecture.
