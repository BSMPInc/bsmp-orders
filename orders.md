# orders.md — Order Tracker (`orders.html`)

> Read this together with the root `CLAUDE.md`. Deep-dive for the Order Tracker only.
> App accent: **maroon** `--accent:#6a1f2e`. ~5,900 lines.

## What it does

Tracks orders from received to shipped with an on-time-delivery system: backward scheduling from the due date, a Daily Dispatch board, an AI daily stand-up, and a Team Load view. Reads quotes to seed orders and links back to purchasing.

## Data & storage

- **Owns RTDB:** `orders/`, plus `team`, `customers`, `durations`, `jobCounter`, `inventory`, `trash/`, `backups/` + `backupIndex`.
- **Reads:** `quotes` (to pull a quote into an order).
- **Storage:** uploads under `orders/` prefix; also handles Google-Drive-style drawing links (`driveDirectView`, `isImageUrl`).
- **localStorage:** `bsmp_daily_brief`, `bsmp_dash_brief`, `bsmp_cutlist_def`, `bsmp_sidebar_pinned`.
- **CDN dep unique to this app:** `html2canvas` (for snapshotting boards/briefs).
- **Daily auto-backup:** `maybeAutoBackup` / `scheduleAutoBackups` write to `backups/` with a `backupIndex`; `pruneSnapshots` trims old ones. Soft-delete goes to `trash/` with an undo toast (`showUndoToast`).

## Pages (left nav → `showPage(...)`)

`dashboard`, `orders`, `schedule`, `dispatch`, `queues`, `inventory`, `ready`, `needpo`, `issuedpos`, `team`, `customers`, `cutlist`, `stats`, `archive`, `trash`, `settings`. Each has a `render*` function (e.g. `renderDashboard`, `renderDispatch`, `renderSchedule`, `renderQueues`, `renderInventory`, `renderTeam`, `renderTeamLoad`, `renderArchive`, `renderTrash`).

## Inventory (added 2026-07-06)

Tracks **hardware and customer-supplied parts** at RTDB `inventory/<id>` =
`{id, name, partNum, kind:'hardware'|'customer', customer, location, qty, unit,
minQty, notes, lastAiCount:{count,at,confidence}, createdAt, updatedAt, updatedBy}`.
Writes are per-child (`set(ref(db,'inventory/'+id))`), listener via
`startInventoryListener()` inside `startDataListeners()`. **Operators can use this
page** (added to the operator page allowlist alongside `queues`/`dispatch`).

- Filters: All / Hardware / Customer parts / **Low stock** (`invIsLow`: `qty <= minQty`
  when `minQty > 0`); low items sort first, get an amber row + "reorder" badge, and
  drive the red `badge-inventory` nav count — that's the purchasing/sourcing list.
- Inline qty edits save immediately; full edits via `inv-modal` (`_invAdd`/`_invEdit`
  /`_invSave`); delete is a confirm + hard `remove()` (no trash/undo — new node).
- **Received/used ledger** (replaces the paper ID tag on each hardware bag): each
  item carries `log:[{id,t:'in'|'out'|'count',n,d,date,by,note,at}]` (newest first,
  capped at 300; `d` is the signed delta). The +/− buttons beside the qty open
  `inv-log-modal` preset to Received/Used (`_invLog`/`_invLogAdd`); the history
  button shows the full ledger with a computed running balance (`renderInvLog`,
  walks back from current qty). Manual qty corrections and confirmed AI counts
  append `t:'count'` entries, so every change is attributed. Entries can **link to
  an open order** (added 2026-07-06): type-to-search picker over non-archived,
  non-Invoiced orders (`_invJobSearch`/`_invJobPick`, matches `invJobLbl` = job/PO/
  customer/part); the entry stores `orderId` + snapshot `orderLbl` (so history
  reads fine after the order is archived/deleted), and the history renders the
  label as a link that closes the modal and opens the order (`openEditFromSchedule`,
  which no-ops if the order is gone). `invLogEntry` takes an optional `extra`
  object merged into the entry. Note: the whole item
  (log included) is saved with one `set()` — two people logging the same item at
  the same instant could clobber each other (accepted, consistent with the suite).
- **Count by weight** (`_invWeigh` → `inv-weigh-modal`, added 2026-07-06): the
  RELIABLE counter — owner confirmed AI photo counts miscount and don't repeat on
  small touching hardware, which no prompt tuning fixes (touching parts have no
  visual boundary). Piece weight is stored per item as `pieceWtG` (always grams)
  with preferred display unit `wtUnit` ('g'|'oz'|'lb'; `WT_G` conversion map).
  Calibrate once by weighing a known sample (`_invWeighCal` — persists immediately)
  or type the piece weight directly; then a count = batch weight ÷ piece weight
  (`_invWeighCalc` live math, `_invWeighSet` logs a `t:'count'` ledger entry with a
  "weight count — 2.4 lb @ 0.006 lb/pc" note). Unit switch converts the shown value
  (`_invWeighUnit`). Needs a counting scale or any scale at the shop.
- **AI photo estimate** (`_invAiCount` → `invRunAiCount`; button relabeled from
  "Count" to "Estimate" 2026-07-06 — treat as estimate ONLY, never source of
  truth): camera-capture file input →
  `invCropB64` (canvas crop/downscale to ≤2576px JPEG — also converts iPhone HEIC) →
  the same `AI_WORKER` Cloudflare proxy the cut-list uses, model `claude-opus-4-8`
  with adaptive thinking → JSON `{count, confidence, note}` → user confirms before
  qty updates. **Big batches tile automatically**: if the first whole-photo pass
  counts > 60, the photo is re-counted as a 3×3 grid of sections (4×4 above 250),
  counted in parallel with a more-than-half-visible edge rule so seam pieces are
  counted once, then summed — one-shot counting drifts badly above ~100 pieces
  (observed: 407 real parts → 420/430 one-shot; tiling fixes this).
- **AI tag scan** (`_invScanTag` → `invRunTagScan`): "Scan tag" toolbar button →
  photograph the supplier tag that arrives with a bag/box of hardware → same
  `AI_WORKER` + `invCropB64` pipeline → JSON `{name, partNum, qty, unit, vendor,
  notes}` (prompt forbids guessing part numbers). If the part matches an existing
  item (exact part # or name, normalized), a confirm offers to log the qty as a
  `t:'in'` ledger entry (note: "Tag scan · vendor · extras"); otherwise — or if the
  match is declined — the `inv-modal` opens pre-filled for review before saving.
- ⚠️ The `inventory` node needs its own RTDB security rule (server-side, Firebase
  console) or saves fail — same gotcha as every new path in this suite. (Rule was
  added and verified 2026-07-06.)

## Work Queues board (added 2026-10-05)

The Work Queues page has a **Board / List** toggle (`setQueueView`, remembered in
localStorage `bsmp_queue_view`; Board is the default). List = the old per-process
tabs + table, unchanged.

- **Board:** three columns Now / Next / Waiting (`QB_COLS`). One card per part (order
  row): drawing thumbnail, customer, part/desc, job, qty, due, the part's current
  operation (`qbCurStep` = first enabled, not-done step in run order), who has it
  (`qbWhoHtml` → `.qb-who`: that step's assignee chip; an outside step with no
  assignee shows its vendor; otherwise an amber "Unassigned"; Today cards show the
  same line) and an ops progress bar. Filter chips above the columns by current operation.
- **Data:** placement lives on the order itself as `r.qb = {col, seq, by, at, since}`,
  saved through `saveDB()` like any other order edit, so **no new RTDB path or rule**.
  `qbPlace` renumbers `seq` (10, 20, …) in the target column; `_qbRemove` deletes `r.qb`.
  Archived orders drop off automatically (`qbOnBoard`).
- **Who does what:** managers add parts (`_qbAddOpen` picker, hides Invoiced /
  Completed / Ready for Invoice), drag cards between/within columns (HTML5 DnD, mouse
  only), or use the Now/Next/Waiting, up/down and "Take off board" buttons in the card
  dialog. Operators only open cards and enter qty / check steps off.
- **Card dialog** (`_qbOpen` → `renderQbDialog`, `#qb-modal`, z-index 60 so the
  confirm-done modal (70) and full drawing viewer (90) sit above it): big drawing on
  the left (image, or PDF/Drive in an iframe; rebuilt only when the drawing changes,
  `_qbDrawKey`), the part's enabled steps on the right using the List view's own
  handlers (`_stepQty`, `_toggleStepDone`). Outsource steps are read-only there;
  Purchasing- steps are checkable like in the Purchasing queue.
- **Thumbnails:** images as-is; PDFs get page 1 rendered by pdf.js 3.11.174 (loaded in
  `<head>`), cached in memory + localStorage (`bsmp_qbt_*`, newest 60). Needs Storage
  CORS for the page's origin (github.io), so on localhost PDFs show an icon.
- **Live refresh:** the orders listener calls `queuesLiveRefresh()`, so Work Queues
  (board or list) and Today follow other devices' changes; it waits while someone is
  typing in an input or dragging a card.

### Today feeds the board (added 2026-10-05)

Today is the planning screen, the board is what the shop works from:
- **Board chip** on every production row (managers only, `dispQbChip`): shows the
  part's column, or "+ Board". Tapping opens a small fixed menu (`_dispQbMenu`,
  `#dqb-menu`, created on first use) to place / move / take off; `_dispQbPick` →
  `qbPlace` (joins the end of the column) or `_qbRemove`. Picking the column it's
  already in does nothing.
- **One order:** Today's own drag-to-reorder is gone. `dispDayCmp` sorts each
  person's list: held last; then Now (board seq) → Next (board seq) → off-board work
  (weekly Board "Publish to Today" `daySeq`, then urgency `dispCmp`) → Waiting.
- **Rows open the card dialog** (`_qbOpen`) in place, for operators too; `renderDispatch`
  repaints it while open. `_openInQueue` was removed.
- **Cards, not rows:** each person's tasks are a grid of cards (`.disp-cards`,
  auto-fill min 340px) styled like the board cards: `dispCardTop` (thumbnail,
  customer, part, job/qty/due/start-by, step chip + health + notes + hold chip), seq
  badge top-left, HOT top-right, and an actions bar: check + "Done [qty] / N"
  (operators see only this), then managers' board chip / assignee / hold / open in
  `.dc-mgr` (stops the click so it doesn't open the dialog). Office Get PO / Invoice
  tasks are cards too (`dc-office`). The old fixed-column row grid and its
  phone/narrow-panel fallbacks were removed.
- `qbPlace` / `qbNudge` / `_qbRemove` now call `refreshActivePage()`, so they repaint
  whichever of Today / Work Queues is showing.

### Today declutter (added 2026-10-05)

Each person's group body is built by `dispGroupBody(k, arr)` (inside `.disp-gbody`,
which is what collapses):
- **Office strip** (`k+':office'`): the office Get PO / Invoice tasks as slim lines
  (`dispMiniRow`), summary "N invoices · N POs to get". No past-due count (an invoice
  past the part's due date means nothing).
- **Outside work strip** (`k+':out'`): every task whose current step is external
  (send-out and Purchasing- buy steps), summary by process ("Paint 2 · Material 1"),
  each line shows the vendor. Strip open/closed is per device (`bsmp_disp_strips`).
- **Shop cards:** every card in the Now column, plus the next `DISP_SHOW_EXTRA` (3);
  the rest sit behind a "Show N more" tile (`_dispMore`, per session; "Show fewer").
- **Find a job** (`#dispatch-search`, static markup so re-renders never wipe what's
  typed): `dsMatches` searches every non-archived, non-invoiced order by customer /
  part / desc / job / PO (all words must match), jobs with work left first, then due;
  shows the current step + who has it + board column. Arrow keys + Enter, or tap,
  open the card dialog. Esc clears.
- **Operators:** `dispMyKey()` matches the signed-in email's name (ops.oziel@ →
  "Oziel", via `chatAuthorName`) to the ONE team member with that first name (team
  records have no email; no unique match = normal behaviour). Their group sorts first
  and stays open; other groups start collapsed (`_dispOpened` / `bsmp_disp_opened`
  remembers the ones they open). Managers keep `_dispCollapsed` as before.

## App update check (added 2026-10-05)

A classic `<script>` just before `</body>`, the SAME block in orders.html and qc.html
(keep them identical; search "App update check"). Shop tablets stay open for days and
only get new app code on reload, so:
- Every 5 min, on wake (`visibilitychange`) and on `online`, it sends a HEAD request (no-store) for
  the page; if ETag / Last-Modified / size changed since its last look, it GETs the
  page and fingerprints every inline `<style>` + `<script>` (FNV hash). The running
  page's fingerprint is taken when the block runs, before any app code. Different =
  a new version. GitHub Pages redeploys bump every file's ETag, so the content check
  is what decides; no version number to bump by hand.
- New version → green "A new version of this app is ready · Update / Later" bar at the
  top (Later hides it 30 min; Spanish in QC via the classic-script `LANG`). After 3 min
  with no pointer/key/touch/wheel input it reloads by itself, unless an input has focus
  or anything `position:fixed` covers the middle of the screen (any dialog, viewer,
  sign-in, QC full-screen FAR).
- `window.bsmpAppVersion()` = `document.lastModified` formatted (= when GitHub Pages
  published the loaded page). Shown in orders' Help modal (`[data-app-version]`) and
  QC Settings. `window.bsmpCheckForUpdate()` runs a check now (handy for testing:
  edit a local file, call it, the bar appears).
- A change that touches ONLY static body markup (no CSS/JS) isn't detected.

## Core areas (where to work)

- **Scheduling engine (the heart of the app):** `computeGlobalSchedule`, `computeStepDates`, `computeMustStart`, `ensureSchedule` / `getSched` / `invalidateSched`. Working-time math: `addWorkingDays`, `addWorkingHours`, `addBusinessDays`, `bizDaysBetween`, `nextBusinessDayStart`, `atWorkStart`, `workEnd`, `isWeekend`, `usHolidays`-style checks. Steps can be internal or external/outsourced (`isExternal`, `gatherExternalSteps`, `firstExtStep`).
- **Dispatch board:** `renderDispatch`, `dispatchRow`, `dispatchItems` / `dispatchAllItems`, grouping/sorting (`dispGroupKey`, `dispGroupsSorted`, `dispCmp`, `dispDayCmp` (follows the Work Queues board, see above), `dispSeqBadge`), board chip `dispQbChip`.
- **Tasks on hold (added 2026-09-02):** a task can be parked with a reason and an optional "hold until" date, which takes it off the Today board without touching the schedule. Records live on the order at `holds[<slot>]` (`holdSlot` swaps out characters Firebase won't take in a key, so `Shear/Sawing` → `Shear_Sawing`; office tasks use `__po__` / `__invoice__`). `holdActive` is the only read that matters — it returns null once the until date arrives, so holds release themselves. `dispVisibleItems` filters the board, `_dispShowHeld` (localStorage `bsmp_disp_showheld`) flips the "N on hold" chip, and held work is excluded from the Today nav badge, `teamLoad` and `buildDispatchSnapshot`. Marking the step done clears its hold. Chips also show in Work Queues and on the schedule step row; the hold button is manager-only. Harnesses: `dev/build_hold_test.py`, `dev/build_hold_layout.py`, `dev/build_hold_steprow.py`.
- **Order cards & detail:** `renderCards`, `condensedCard`, `cardDaysLabel`, `openEdit`, `detailInner` / `detailRow`, `lineRow`, `rowTotal`, `partChipHtml`. Condensed card shows part number as the main label with description in a tooltip; MM/DD/YY date fields; alternating tile colors.
- **Health/status:** `jobHealth`, `groupHealth`, `healthBadge`, `healthTip`, `autoAdvanceStatus`, `stepStatus`, `procState`.
- **PO / purchasing:** `renderNeedPO` / `renderNeedPOByVendor`, `renderIssuedPOs`, `poGroups`, `poDetailHtml`, `vendorPOsHtml`, outsource strip (`outsourceStripHtml`).
- **Team notes (per-task threads, added 2026-09-02):** `orderChat/<thread>` still holds one thread per Customer+PO (`chatKey`), and now also one per TASK — `chatKeyStep(order, step)` = job key + `~<orderId>~<squashed step>`, plus a reserved `__shop__` thread for the whole-shop board on Today (`renderShopNote`). Buttons: `chatBtnAt` (the renderer), `chatBtnHtml` (job), `chatBtnStep` (task row), `chatBtnJob` (PO card, rolls `stepThreadKeys` up so a reply on a step lights the card). Unread is per person per device in `localStorage` under `bsmp_chatseen_<uid>` — `chatUnread` / `markChatRead` / `primeChatSeen` (a new device starts quiet instead of flagging every old note); no rule change, the published `$thread` wildcard already covers the new keys. The popup's thread picker (`_renderChatSwitch` / `_chatSwitch`) lists the whole job plus every step, so a note written in the wrong place is one tap away. Marking read happens in `_renderChatThread`, so draw the thread BEFORE the tabs.
- **Team & load:** `renderTeam`, `renderTeamLoad`, `teamLoad`, `personById` / `personChip` / `personInitials`, `assigneeOptions`, per-person process checkboxes.
- **Cut list / nesting:** `cutlist` page (`clInit`, `clPack`, `clRowHtml`, `clAiExtract`, `clSaveDefaults`, `clWireDrop`).
- **AI stand-up / briefs:** `aiNarrate`, `renderDailyBrief`, `buildDashSnapshot` / `buildDispatchSnapshot`, `fmtBrief`.
- **Job numbering:** `jobCounter` with `advanceJobCounter`, `maybeAdvanceCounter`, `suggestJobNumber`, `nextLetter`, `autoIndexCustomer`.
- **Delivery Tags (`printOrderTags`):** tag-icon button in the detail actions (next to Customer confirmation). Prints one **4x6 landscape sticky label per part number on the PO** (`@page size:6in 4in`; same customer+po grouping as the confirmation). Prefills customer / PO / invoice # / today's date / part (+desc) / qty; Revision prints blank (orders don't track rev). Packaging Type (Boxes/Pallet/Bagged-Wrapped), Number of Packages, Via (Drop Off/Pick Up/Shipping), and Package By are hand-fill checkboxes/blanks. Black/gray header bands rely on `print-color-adjust:exact`; set the printer to 4x6 stock.

## Order record (rough shape)

Common fields: `customer`, `part`, `job`, `po`, `ordered`, `due`, `status`, `qty`, `priority`, and a `lines` array of line items (each with part/qty/price). Line items support a condensed view with a price column.

## Gotchas

- **The schedule is derived, not stored raw** — many views call `ensureSchedule`/`getSched`, and edits call `invalidateSched`. If dates look stale after a change, check that the schedule was invalidated/recomputed.
- Backward scheduling depends on working-time helpers and holidays; off-by-one bugs usually live in `addWorkingDays` / `nextBusinessDayStart`.
- There's a known **scroll-reset** concern and **schedule column alignment** on the production view — both were fixed before; re-test them after layout edits.
- Soft-delete/restore uses `trash/`; don't hard-delete without the undo path.
