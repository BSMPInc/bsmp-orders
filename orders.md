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

## Core areas (where to work)

- **Scheduling engine (the heart of the app):** `computeGlobalSchedule`, `computeStepDates`, `computeMustStart`, `ensureSchedule` / `getSched` / `invalidateSched`. Working-time math: `addWorkingDays`, `addWorkingHours`, `addBusinessDays`, `bizDaysBetween`, `nextBusinessDayStart`, `atWorkStart`, `workEnd`, `isWeekend`, `usHolidays`-style checks. Steps can be internal or external/outsourced (`isExternal`, `gatherExternalSteps`, `firstExtStep`).
- **Dispatch board:** `renderDispatch`, `dispatchRow`, `dispatchItems` / `dispatchAllItems`, grouping/sorting (`dispGroupKey`, `dispGroupsSorted`, `dispCmp`, `dispDayCmp`, `dispSeqBadge`, `dispMoveCtl`).
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
