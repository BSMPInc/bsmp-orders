# qc.md — Inspection / QC (`qc.html`)

> Read this together with the root `CLAUDE.md`. Deep-dive for the Inspection / QC app only.
> App accent: **graphite** `--accent:#3a4049`. ~2,100 lines — the newest and smallest app.

## What it does

Quality control: operator self-checks, First Article Inspection reports (Simple FAR and full AS9102), a Nonconformance (NCR) tracker, and a material-cert archive with traceability. Has a full EN/ES language toggle.

## Data & storage

- **Owns RTDB:** `qc/inspections`, `qc/ncr`, `qc/certs`, `qc/audit`.
- **`qc/audit` = append-only change history.** Each entry is written under its own `qc/audit/<id>` and never edited (immutable trail, an AS9100 building block). FAR result changes (`{charNo, from, to, wasOot, nowOot, user, ts, action}`) and NCR raise/correct events are logged here on every `qcSaveFair`. Loaded into the `AUDIT` state mirror; `farHistoryCard()` renders it on the First Article form. **Needs its own security rule** (see warning below) or the writes are swallowed — the code intentionally wraps `qcLogAudit` in try/catch so a missing rule can't block the main save.
- **Out-of-tolerance → NCR:** when a saved FAR has any characteristic whose result busts its tolerance (`charIsOot`), `qcSaveFair` auto-raises a linked NCR (`source:'fair'`, `farId`/`inspectionId`, `rec.ncrId`), mirroring the self-check Flag path. When every dimension is corrected it stamps `correctedAt`/`correctedBy` on that NCR and leaves the final close to a manager. The FAR list shows an "Open NCR" badge until it's closed.
- **Reads:** `orders` and `quotes` (to link a self-check / FAR / cert to an order).
- **Storage:** uploads under `qc/` prefix (`qcUpload` → `qc/<subfolder>/...`). Cert packages, part photos, and ballooned drawings all live here.
- **localStorage:** `bsmp_qc_lang` (EN/ES), plus `bsmp_proxy_url` / `bsmp_apikey` for AI — shared with quote.html; either app's Settings reads/writes the same keys (here: Settings page → `viewSettings`, `qcSaveProxy`/`qcTestProxy`/`qcSaveKey`/`qcClearKey`).
- **CDN deps unique to this app:** `pdf-lib` (splitting cert PDFs) and `pdf.js` (rendering drawing/cert pages).

> ⚠️ **The classic silent-save bug lives here.** RTDB + Storage security rules must include the `qc/` path (and a matching Storage rule) or saves to certs/inspections fail silently. Rules are server-side (Firebase console), not in this repo, and take effect immediately with no redeploy. If a QC save does nothing, check rules first.
>
> ⚠️ **`qc/audit` needs its own rule.** Add it under the `qc` node in the Firebase console. Recommended append-only/immutable form (create-once, no overwrite/delete):
> ```json
> "audit": { ".read": "auth != null", "$e": { ".write": "auth != null && !data.exists()" } }
> ```
> Without it, change-history entries silently don't persist (the FAR still saves fine).

## Structure

- **i18n:** `t()` + `I18N` map with `en`/`es`. Static text uses `data-t` / `data-tph`; `applyStatic()` swaps it; `qcSetLang()` toggles. **When adding user-facing text, add both the English key and the Spanish translation and wrap in `t(...)`.** Spanish nav labels are tuned to fit the collapsed rail.
- **State:** `INSPECTIONS`, `NCRS`, `CERTS`, `ORDERS`, `QUOTES` mirror Firebase; `render()` rebuilds the page from `page` + `editId`.
- **Roles:** operator vs manager as in the root guide; `isMgr()`, `mgr-only` class, operators default to the self-check page.
- **Firebase bridge:** module script exposes `qcSet` / `qcUpdate` / `qcRemove` / `qcUpload`; UI calls go through `dbSet` (which sanitizes `undefined`→`null` and surfaces errors via `qcToast`). Don't call raw `set()` from the UI.

## Pages (`showPage(...)`)

`inspections` (list), `selfcheck` (form), `fairs` (First Article list), `fair` (First Article form), `ncr`, `certs`, `drawings` (drawing library), `settings` (AI connection — per-device, all roles).

## Core areas (where to work)

- **Self-checks:** `viewSelfCheck`, `qcSaveSelf`, `qcPickResult`. Flagging a self-check auto-creates a linked NCR.
- **First Articles (FAR):** `viewFair`, `qcSaveFair`, characteristics table (`charRow`, `qcCharAdd/Del`, `qcCharCompute`, `syncChars`). Deviation math: `parseNum`, `parseTol`, `qcDev`, `charStatus`. Modes: Simple FAR vs AS9102 (`qcFairMode`).
- **Tolerance resolution (`resolveTol`):** every OOT check runs through `qcDev` → `resolveTol(req,tol)`, which picks the band in priority order: (1) the explicit **Tolerance Range** field, (2) a ± embedded in the requirement callout text (`parseEmbeddedTol`), (3) a **title-block default** by fraction / decimal place / angle (`defaultTolBand`). Nominal parsing (`nominalOf`) understands both decimals and inch fractions (`isFractionReq` requires a real 2/4/8/16/32/64 denominator so material notes like `304/304L` aren't mistaken for fractions; `parseFractionNum` handles `1-1/2`, `3/8`, etc.). Defaults live in `_fairTolDefaults` (`{frac,p1,p2,p3,ang}`) and match BSMP's title block: **frac ±1/16 (.0625), 2-place ±.020, 3-place ±.005, angular ±1°, and no 1-place rule** (`p1` blank → 1-place dims aren't auto-checked). They're editable on the FAR form (`qcSetTolDefault`, manager-only), persist on the record as `tolDefaults`, and are marked with a `*` in the tolerance column. `charRow` computes row status live so changing a default (or opening an older record) reflects immediately. The measurement dialog's tolerance field is **editable for managers** (read-only for operators) and shows which tolerance is being applied.
- **Drawing viewer (`fdv*`):** pan/zoom viewer used on the FAR form — `fdvInit`, `fdvFit`, `fdvZoom`, `fdvApply`, marker positioning (`fdvPositionMarkers`, `fdvRenderMarkers`). `fdv` is the state object. Balloons here are read-only markers you tap to enter a measurement (`qcMeas*`).
- **Balloon workspace (`bws*` + `qcWs*`):** the editable ballooning surface (place / drag / box dimensions). Has its own pan/zoom (`bws` state, `bwsInit`/`bwsFit`/`bwsZoom`/`bwsApply`), a "Hide/Show drawing" toggle (`qcToggleDrawPreview`, `_fairDrawMin`), and a full-screen mode (`qcFairFull`). Balloon positions are stored **normalized 0–1** (`bx`,`by`) against the image, so they survive zoom. Place mode vs Box mode via `_wsMode`.
- **AI features (`claude-sonnet-4-6` via proxy):** auto-bubble (`qcFairAutoBubble`, `FAIR_BUBBLE_PROMPT`), read placed balloons (`qcFairReadBubbles`, composites numbered balloons onto the image via `qcCompositeBalloonsDataUrl`), box-a-dimension crop read (`qcReadBox`, `CROP_PROMPT`, `cropRegion`), re-read a saved ballooned image (`qcFairReadBallooned`). Balloon sorting/hierarchy: `qcSortByHierarchy`, `qcSortBubbles`, `qcSpreadBubbles`, `qcBubblesLineUp`.
- **Save ballooned drawing:** `qcFairSaveBallooned` composites balloons and uploads a flat JPG; the button shows a spinner while saving. The URL is stored on the report as `ballooned`.
- **Hand-write FAI sheet (`qcFairPrintBlank`):** print button on the FAR form (top + bottom toolbars, all roles). Prints a BSMP-letterhead blank First Article report: a characteristics table with balloon #, requirement, and the **resolved** tolerance (`resolveTol`, `*` = title-block default) filled in — ACTUAL / ACC-REJ / NOTES left blank for the inspector to hand-write, TOOL as tick-boxes matched to the characteristic type (`TOOL_OPTS`: Linear→Caliper/Mic/Tape, Diameter→Pin gauge/Caliper, Radius→Rad gauge/Caliper, Angular→Protractor/Visual, Note→Visual, always +Other), plus 3 spare rows, an ACCEPT/REJECT result box, and inspector/manager signature lines. The **ballooned drawing prints on its own last sheet** (`page-break-before:always`; sourced live workspace composite → saved `ballooned` URL → fresh composite from saved `bubbles` → plain drawing, in that order) with the repeating letterhead as its title block. Landscape drawings are **rotated 90° CCW to portrait** (`qcRotateForPortrait` — turn the sheet clockwise to read; falls back unrotated on CORS failure) and sized `max-height:min(76vh,13.5in)` so the page-relative `vh` keeps scaling when the user picks 11x17 in the print dialog for just that page. `qcCompositeBalloonsDataUrl(img, bubbles, scale)` takes optional args (defaults to the live `_fairImg`/`_fairBubbles`); the print passes `scale` `PRINT_BALLOON_SCALE=0.4` — **print balloons are 60% smaller** (opaque fill, oversized digit) so they don't cover dimension text, while the AI-read and save-ballooned paths keep full-size balloons the model can read. The print **prefers a fresh composite from the current `bubbles` positions** (drag balloons in the workspace to relocate; positions persist as `bx`/`by`) — the saved `ballooned` image is only the fallback for legacy records with no stored bubbles. Opens the popup synchronously (blocker-safe), fills it async, and waits for images to load before `print()`.
- **NCRs:** `viewNcr`, `ncrDetail`, `qcSaveNcr`, dispositions (`DISPOSITIONS`), open → dispositioned → closed. Operators raise; managers disposition/close.
- **Material certs:** `viewCerts`, `certForm`, cert review flow (`certReviewForm`), AI cert intake with multi-cert detection, PDF splitting via `pdf-lib`, cert viewer modal (`qcViewCert`, `qcvRender`), printable order sheet (`qcOrderSheet`). Duplicate heat/lot detection is built in. Linked orders are editable after save (manager-only): link icon on the row → `qcEditCertLinks` / `certLinksForm` / `qcSaveCertLinks`, reusing the add-form chip/search widgets (`_certLinks`, `certLinkChips`, `qcCertSearch`).

## Record shapes (rough)

- **Inspection (self-check or FAR):** `id`, `type` (`self`|`fair`), `partNum`, `customer`, `job`, `po`, `rev`, `qty`, `result`/`fairStatus`, `characteristics[]`, `bubbles[]`, `ballooned`, `drawing`, `photos[]`, timestamps, `createdBy`. FAR bubbles persist as `{no,bx,by,value,tol,category,group,box}`.
- **NCR:** `id`, `status` (`open`|`dispositioned`|`closed`), `partNum`, `customer`, `job`, `qtyAffected`, `description`, `disposition`, `correctiveAction`, links back to the inspection.
- **Cert:** `material`, `spec`, `heatLot`, `supplier`/`mill`, `certNo`, `certDate`, `linkedOrders[]`, `files[]`, optional `invoice`.

## Gotchas

- **Silent saves = missing `qc/` security rule** (see warning above). This is the #1 thing to check.
- Balloon coordinates are normalized 0–1 against the image — when touching the viewer or workspace, keep click/drag math relative to the **image** element (not the padded stage), or balloons drift under zoom.
- The `fdv` (read-only, on the form) and `bws` (editable workspace) viewers are **separate** engines with separate state — don't cross their handlers.
- AI reads need the proxy/key — set it in this app's Settings page (or quote.html Settings; same storage). If AI "does nothing," check `bsmp_proxy_url` is present.
- Adding UI text without a Spanish `I18N` entry leaves Spanish users seeing the English key — always add both.

## AS9100 / ITAR note

AS9100 is feasible for this app with an immutable audit trail, named-user stamping, and software-validation docs as the main gaps. **ITAR is out of scope** for the current Firebase/Cloudflare/Anthropic architecture — keep any ITAR-restricted handling conservative and don't build features that would put ITAR-controlled technical data into this stack.
