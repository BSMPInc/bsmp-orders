# qc.md — Inspection / QC (`qc.html`)

> Read this together with the root `CLAUDE.md`. Deep-dive for the Inspection / QC app only.
> App accent: **graphite** `--accent:#3a4049`. ~2,100 lines — the newest and smallest app.

## What it does

Quality control: operator self-checks, First Article Inspection reports (Simple FAR and full AS9102), a Nonconformance (NCR) tracker, and a material-cert archive with traceability. Has a full EN/ES language toggle.

## Data & storage

- **Owns RTDB:** `qc/inspections`, `qc/ncr`, `qc/certs`.
- **Reads:** `orders` and `quotes` (to link a self-check / FAR / cert to an order).
- **Storage:** uploads under `qc/` prefix (`qcUpload` → `qc/<subfolder>/...`). Cert packages, part photos, and ballooned drawings all live here.
- **localStorage:** `bsmp_qc_lang` (EN/ES), plus it *reads* `bsmp_proxy_url` / `bsmp_apikey` set by quote.html for AI.
- **CDN deps unique to this app:** `pdf-lib` (splitting cert PDFs) and `pdf.js` (rendering drawing/cert pages).

> ⚠️ **The classic silent-save bug lives here.** RTDB + Storage security rules must include the `qc/` path (and a matching Storage rule) or saves to certs/inspections fail silently. Rules are server-side (Firebase console), not in this repo, and take effect immediately with no redeploy. If a QC save does nothing, check rules first.

## Structure

- **i18n:** `t()` + `I18N` map with `en`/`es`. Static text uses `data-t` / `data-tph`; `applyStatic()` swaps it; `qcSetLang()` toggles. **When adding user-facing text, add both the English key and the Spanish translation and wrap in `t(...)`.** Spanish nav labels are tuned to fit the collapsed rail.
- **State:** `INSPECTIONS`, `NCRS`, `CERTS`, `ORDERS`, `QUOTES` mirror Firebase; `render()` rebuilds the page from `page` + `editId`.
- **Roles:** operator vs manager as in the root guide; `isMgr()`, `mgr-only` class, operators default to the self-check page.
- **Firebase bridge:** module script exposes `qcSet` / `qcUpdate` / `qcRemove` / `qcUpload`; UI calls go through `dbSet` (which sanitizes `undefined`→`null` and surfaces errors via `qcToast`). Don't call raw `set()` from the UI.

## Pages (`showPage(...)`)

`inspections` (list), `selfcheck` (form), `fairs` (First Article list), `fair` (First Article form), `ncr`, `certs`.

## Core areas (where to work)

- **Self-checks:** `viewSelfCheck`, `qcSaveSelf`, `qcPickResult`. Flagging a self-check auto-creates a linked NCR.
- **First Articles (FAR):** `viewFair`, `qcSaveFair`, characteristics table (`charRow`, `qcCharAdd/Del`, `qcCharCompute`, `syncChars`). Deviation math: `parseNum`, `parseTol`, `qcDev`, `charStatus`. Modes: Simple FAR vs AS9102 (`qcFairMode`).
- **Drawing viewer (`fdv*`):** pan/zoom viewer used on the FAR form — `fdvInit`, `fdvFit`, `fdvZoom`, `fdvApply`, marker positioning (`fdvPositionMarkers`, `fdvRenderMarkers`). `fdv` is the state object. Balloons here are read-only markers you tap to enter a measurement (`qcMeas*`).
- **Balloon workspace (`bws*` + `qcWs*`):** the editable ballooning surface (place / drag / box dimensions). Has its own pan/zoom (`bws` state, `bwsInit`/`bwsFit`/`bwsZoom`/`bwsApply`), a "Hide/Show drawing" toggle (`qcToggleDrawPreview`, `_fairDrawMin`), and a full-screen mode (`qcFairFull`). Balloon positions are stored **normalized 0–1** (`bx`,`by`) against the image, so they survive zoom. Place mode vs Box mode via `_wsMode`.
- **AI features (`claude-sonnet-4-6` via proxy):** auto-bubble (`qcFairAutoBubble`, `FAIR_BUBBLE_PROMPT`), read placed balloons (`qcFairReadBubbles`, composites numbered balloons onto the image via `qcCompositeBalloonsDataUrl`), box-a-dimension crop read (`qcReadBox`, `CROP_PROMPT`, `cropRegion`), re-read a saved ballooned image (`qcFairReadBallooned`). Balloon sorting/hierarchy: `qcSortByHierarchy`, `qcSortBubbles`, `qcSpreadBubbles`, `qcBubblesLineUp`.
- **Save ballooned drawing:** `qcFairSaveBallooned` composites balloons and uploads a flat JPG; the button shows a spinner while saving. The URL is stored on the report as `ballooned`.
- **NCRs:** `viewNcr`, `ncrDetail`, `qcSaveNcr`, dispositions (`DISPOSITIONS`), open → dispositioned → closed. Operators raise; managers disposition/close.
- **Material certs:** `viewCerts`, `certForm`, cert review flow (`certReviewForm`), AI cert intake with multi-cert detection, PDF splitting via `pdf-lib`, cert viewer modal (`qcViewCert`, `qcvRender`), printable order sheet (`qcOrderSheet`). Duplicate heat/lot detection is built in.

## Record shapes (rough)

- **Inspection (self-check or FAR):** `id`, `type` (`self`|`fair`), `partNum`, `customer`, `job`, `po`, `rev`, `qty`, `result`/`fairStatus`, `characteristics[]`, `bubbles[]`, `ballooned`, `drawing`, `photos[]`, timestamps, `createdBy`. FAR bubbles persist as `{no,bx,by,value,tol,category,group,box}`.
- **NCR:** `id`, `status` (`open`|`dispositioned`|`closed`), `partNum`, `customer`, `job`, `qtyAffected`, `description`, `disposition`, `correctiveAction`, links back to the inspection.
- **Cert:** `material`, `spec`, `heatLot`, `supplier`/`mill`, `certNo`, `certDate`, `linkedOrders[]`, `files[]`, optional `invoice`.

## Gotchas

- **Silent saves = missing `qc/` security rule** (see warning above). This is the #1 thing to check.
- Balloon coordinates are normalized 0–1 against the image — when touching the viewer or workspace, keep click/drag math relative to the **image** element (not the padded stage), or balloons drift under zoom.
- The `fdv` (read-only, on the form) and `bws` (editable workspace) viewers are **separate** engines with separate state — don't cross their handlers.
- AI reads need the proxy/key that quote.html sets; if AI "does nothing," check `bsmp_proxy_url` is present.
- Adding UI text without a Spanish `I18N` entry leaves Spanish users seeing the English key — always add both.

## AS9100 / ITAR note

AS9100 is feasible for this app with an immutable audit trail, named-user stamping, and software-validation docs as the main gaps. **ITAR is out of scope** for the current Firebase/Cloudflare/Anthropic architecture — keep any ITAR-restricted handling conservative and don't build features that would put ITAR-controlled technical data into this stack.
