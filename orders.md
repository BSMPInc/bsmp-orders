# orders.md — Order Tracker (`orders.html`)

> Read this together with the root `CLAUDE.md`. Deep-dive for the Order Tracker only.
> App accent: **maroon** `--accent:#6a1f2e`. ~5,900 lines.

## What it does

Tracks orders from received to shipped with an on-time-delivery system: backward scheduling from the due date, a Daily Dispatch board, an AI daily stand-up, and a Team Load view. Reads quotes to seed orders and links back to purchasing.

## Data & storage

- **Owns RTDB:** `orders/`, plus `team`, `customers`, `durations`, `jobCounter`, `trash/`, `backups/` + `backupIndex`.
- **Reads:** `quotes` (to pull a quote into an order).
- **Storage:** uploads under `orders/` prefix; also handles Google-Drive-style drawing links (`driveDirectView`, `isImageUrl`).
- **localStorage:** `bsmp_daily_brief`, `bsmp_dash_brief`, `bsmp_cutlist_def`, `bsmp_sidebar_pinned`.
- **CDN dep unique to this app:** `html2canvas` (for snapshotting boards/briefs).
- **Daily auto-backup:** `maybeAutoBackup` / `scheduleAutoBackups` write to `backups/` with a `backupIndex`; `pruneSnapshots` trims old ones. Soft-delete goes to `trash/` with an undo toast (`showUndoToast`).

## Pages (left nav → `showPage(...)`)

`dashboard`, `orders`, `schedule`, `dispatch`, `queues`, `ready`, `needpo`, `issuedpos`, `team`, `customers`, `cutlist`, `stats`, `archive`, `trash`, `settings`. Each has a `render*` function (e.g. `renderDashboard`, `renderDispatch`, `renderSchedule`, `renderQueues`, `renderTeam`, `renderTeamLoad`, `renderArchive`, `renderTrash`).

## Core areas (where to work)

- **Scheduling engine (the heart of the app):** `computeGlobalSchedule`, `computeStepDates`, `computeMustStart`, `ensureSchedule` / `getSched` / `invalidateSched`. Working-time math: `addWorkingDays`, `addWorkingHours`, `addBusinessDays`, `bizDaysBetween`, `nextBusinessDayStart`, `atWorkStart`, `workEnd`, `isWeekend`, `usHolidays`-style checks. Steps can be internal or external/outsourced (`isExternal`, `gatherExternalSteps`, `firstExtStep`).
- **Dispatch board:** `renderDispatch`, `dispatchRow`, `dispatchItems` / `dispatchAllItems`, grouping/sorting (`dispGroupKey`, `dispGroupsSorted`, `dispCmp`, `dispDayCmp`, `dispSeqBadge`, `dispMoveCtl`).
- **Order cards & detail:** `renderCards`, `condensedCard`, `cardDaysLabel`, `openEdit`, `detailInner` / `detailRow`, `lineRow`, `rowTotal`, `partChipHtml`. Condensed card shows part number as the main label with description in a tooltip; MM/DD/YY date fields; alternating tile colors.
- **Health/status:** `jobHealth`, `groupHealth`, `healthBadge`, `healthTip`, `autoAdvanceStatus`, `stepStatus`, `procState`.
- **PO / purchasing:** `renderNeedPO` / `renderNeedPOByVendor`, `renderIssuedPOs`, `poGroups`, `poDetailHtml`, `vendorPOsHtml`, outsource strip (`outsourceStripHtml`).
- **Team & load:** `renderTeam`, `renderTeamLoad`, `teamLoad`, `personById` / `personChip` / `personInitials`, `assigneeOptions`, per-person process checkboxes.
- **Cut list / nesting:** `cutlist` page (`clInit`, `clPack`, `clRowHtml`, `clAiExtract`, `clSaveDefaults`, `clWireDrop`).
- **AI stand-up / briefs:** `aiNarrate`, `renderDailyBrief`, `buildDashSnapshot` / `buildDispatchSnapshot`, `fmtBrief`.
- **Job numbering:** `jobCounter` with `advanceJobCounter`, `maybeAdvanceCounter`, `suggestJobNumber`, `nextLetter`, `autoIndexCustomer`.

## Order record (rough shape)

Common fields: `customer`, `part`, `job`, `po`, `ordered`, `due`, `status`, `qty`, `priority`, and a `lines` array of line items (each with part/qty/price). Line items support a condensed view with a price column.

## Gotchas

- **The schedule is derived, not stored raw** — many views call `ensureSchedule`/`getSched`, and edits call `invalidateSched`. If dates look stale after a change, check that the schedule was invalidated/recomputed.
- Backward scheduling depends on working-time helpers and holidays; off-by-one bugs usually live in `addWorkingDays` / `nextBusinessDayStart`.
- There's a known **scroll-reset** concern and **schedule column alignment** on the production view — both were fixed before; re-test them after layout edits.
- Soft-delete/restore uses `trash/`; don't hard-delete without the undo path.
