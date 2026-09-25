# quote.md — Quote Tool (`quote.html`)

> Read this together with the root `CLAUDE.md`. This is the deep-dive for the Quote Tool only.
> App accent: **blue** `--accent:#1e3a5f`. ~8,600 lines — the largest app. Edit surgically.

## What it does

Estimates and prices sheet-metal jobs, produces a customer-facing printable PDF quote with an auto-incrementing quote number, and keeps an archive. It's the pricing brain of the shop.

## Data & storage

- **Owns RTDB path:** `quotes/`. Quotes sync to the cloud via `_qCloudSyncQuote` / `_qCloudRemoveQuote`; `_qSyncAll` / `_qSyncList` reconcile local and cloud.
- **Also owns `quoteSnaps/<id>`** (added 2026-09-24, rule published): the FULL quote record (minus the `img` thumbnail). `quotes/<id>` stays the trimmed copy the Order Tracker / QC import. On sign-in `_qListenHistory()` merges cloud quotes DOWN into `HISTORY` (live `onValue` on `quoteSnaps`, one-time `get` of `quotes` for ids with no full copy -> added as `_cloudLite` records). Rules in `_qMergeDown`: additive only; a cloud copy replaces a local one only if its `savedAt` is newer AND `_qSig()` content differs (RTDB drops empty arrays/strings, so compare normalised); ids deleted/cleared locally go in `bsmp_quote_tombstones` and are never pulled back; `_cloudLite` records are never pushed as snaps; unknown customer names are added to the per-browser customer list (30/7). `savedAt` is stamped in `_qCloudSyncQuote` (the "just changed" path) only. Harness: `dev/build_quote_sync_test.py` (38 checks; serve on :8123, it backs up/restores the shared localStorage keys - do not load the app in another tab while it runs).
- **Storage:** drawings upload under the `quotes/` prefix (`_qUploadDrawing`).
- **Heavy localStorage use** (this app holds most of the shop's tunable settings):
  - Pricing/config: `bsmp_prices`, `bsmp_rates`, `bsmp_laser_speeds`, `bsmp_tier_markups`, `bsmp_min_sheet`, `bsmp_assumptions`, `bsmp_customers`
  - Quote numbering/archive: `bsmp_quote_counter`, `bsmp_archive`, `bsmp_history`, `bsmp_quote_synced`, `bsmp_quote_snapped`, `bsmp_quote_tombstones`
  - Shop identity: `bsmp_shopname`, `bsmp_shoploc`
  - AI connection (shared with qc.html): `bsmp_proxy_url`, `bsmp_apikey`
  - One-off UI flags: `bsmp_*_shown`, `bsmp_restore_msg`, `bsmp_thumbs_v2`, `bsmp_sidebar_pinned`

> Because quote.html is where `bsmp_proxy_url` / `bsmp_apikey` get set, it's effectively the "settings hub" for AI across the suite. qc.html reads these same keys.

## Core areas (where to work)

- **Main estimate:** `calculate()` is the top-level pricing entry. Supporting math: `calcSheetLoading`, `billableSheets`, `bestPartsPerSheet`, `calcQtyBreaks` / `calcBreakForQty`, `roundPrice`, `tierMarkup` / `getAsmMarkupForQty`.
- **Materials & weight pricing:** `densityForMaterialType`, `setMatMode` / `setMatPriceMode`, `convertUnitsToInch`, `syncMaterialSelects`, material break rows (`addMatBreakRow`, `toggleMatBreaks`).
- **Assemblies:** `calcAssembly`, `showAssemblyPanel`, `addAsmPart` / `addAsmOp`, `calcAsmQtyBreaks`, `copyAssembly`.
- **Process/time models:** CNC (`computeCnc`, `applyCncEstimate`, `cncStockVolume`), welding (`computeWelding`, `weldArea`, `weldPasses`), bar stock (`calcBarStock`, `getBarDimensions`, `getBarPriceFromIndex`), programming (`calcProgramming`), inspection (`calcInspection`), orbital (`calcOrbital`, `applyOrbitalTime`), batch deburr/tap.
- **Gang / shared nesting:** `calcGangMaterial`, `addGangPart`, `toggleGangNest`, `renderGangParts`.
- **Job tiers:** Commodity / Standard / Precision / Rush — `selectTier`, `renderTierButtons`, `renderTierSettings`, `resetTierMarkups`, win-rate tracking in history.
- **Drawing viewer (`dv*`):** `dvInit`, `dvFit`, `dvZoomAt`, `setDrawingViewer`, `showFullDrawing`, PDF isometric render (`renderPdfIsometric`). Has its own pan/zoom (`dv` state object) — this is the pattern the qc.html balloon viewer was later modeled on.
- **AI extraction:** `analyzeDrawing`, `applyExtracted`, `renderExtractedPreview`, `callAnthropic` (model `claude-sonnet-4-6`), `toBase64`, `shrinkDataUrl` / `shrinkCanvas`. Connection tested via `testProxyConnection` / `testApiKey`.
- **Archive / history / insights:** `archivePrintedQuote`, `renderArchive`, `renderHistory`, `renderArchiveInsights`, `renderLaserInsights`, `exportArchiveCSV`.
- **PDF output & numbering:** `consumeQuoteNumber` / `saveNextQuoteNumber`, `reprintArchived`, `tbPrint`.

## Claude's decisions (added 2026-09-24)

Quotes Claude builds carry `claudeReview: { by, at, summary, decisions:[{area, question, options[], choice, because, check, source}], reviewedAt, reviewedBy }`. `check:true` = an estimate / judgement call the owner should confirm. Shown as a chip under the part number in History (`claudeChip`), a banner above Job Info when that quote is loaded (`renderClaudeReviewBar`, kept in step by wrapping reloadQuote/resetForm/saveQuote/renderHistory), and a pop-up decision tree (`showClaudeReview`) with **Mark reviewed** (`markClaudeReviewed`, stamps who/when and syncs). `saveQuote` attaches `window._pendingClaudeReview` to a NEW quote (then clears it) and keeps `existing.claudeReview` on re-save. The record travels in the `quoteSnaps` full copy, so it shows in every browser. Status changes (`setQuoteStatus`) now also sync to the cloud (they used to stay in one browser).

## Quote record (rough shape)

Fields commonly present: `id`, `customer`, `part`, `qty`, `material`, `tier`, `status`, `total`, and timestamps. Status is managed via `setQuoteStatus` / `statusDropdown` (quote status tracker).

## Gotchas

- Pricing is spread across many `calc*` helpers that feed `calculate()`. When changing one number (a rate, a speed, a markup), trace where it's read — several inputs come from localStorage config, not the form.
- The drawing viewer and AI extraction share canvas/base64 helpers; `shrinkDataUrl` exists to keep image payloads small for the API — don't remove size-limiting when touching AI calls.
- Quote numbers auto-increment and are consumed on print/archive — be careful not to double-consume when refactoring the print path.
