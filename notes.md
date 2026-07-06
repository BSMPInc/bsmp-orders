# notes.md — Notes (`notes.html`)

> Read this together with the root `CLAUDE.md`. Deep-dive for the Notes app only.
> App accent: **indigo** `--accent:#43397a`. ~500 lines — the newest and smallest app.

## What it does

Private per-user notes, usable on PC and iPhone (via Safari → Share → **Add to Home
Screen**, which installs it full-screen like an app — the iOS metas and icons are in
the `<head>`). A note has a title, a rich-text body, a checklist, tags, photos
(collapsible section), an optional link to an order, and a pin flag. The list view
is a card grid with search and tag filtering; pinned notes sort first.

**Privacy model:** every user sees ONLY their own notes. This app deliberately has
**no operator/manager split** (no `mgr-only`, no role logic) — privacy comes from the
per-uid data path plus the matching security rules, not from roles.

## Data & storage

- **Owns RTDB:** `notes/<auth-uid>/<noteId>` — note the extra **per-user** level
  compared to the other apps. `NT_UID` (the signed-in user's Firebase uid) is baked
  into every read/write path.
- **Reads:** `orders` (for the "Link to a job / order" dropdown) and `customers`
  (title type-ahead). **Writes `customers/<id>`** when "Add … as a new customer"
  is used — single-child set, same record shape as the Orders app
  (`{id,name,phone,email,notes,addedAt}`), so it shows up there too.
- **Storage:** photo uploads go under `notes/<uid>/photos/...` (`ntUpload`).
- **No localStorage keys of its own** (sidebar pin is per-session; it does not use AI,
  so it never touches `bsmp_proxy_url`/`bsmp_apikey`).
- **No CDN deps beyond the shared ones** (fonts + Tabler icons). No pdf.js, no i18n.

> ⚠️ **Security rules (server-side, Firebase console) are what make notes private.**
> Both must exist or saves fail silently / privacy breaks:
>
> RTDB, alongside the other app rules:
> ```json
> "notes": {
>   "$uid": {
>     ".read":  "auth != null && auth.uid === $uid",
>     ".write": "auth != null && auth.uid === $uid"
>   }
> }
> ```
> Storage, alongside the existing match blocks:
> ```
> match /notes/{uid}/{allPaths=**} {
>   allow read, write: if request.auth != null && request.auth.uid == uid;
> }
> ```

## Structure

- **English-only.** No `t()`/`I18N` map (unlike `qc.html`). If Spanish is ever needed,
  port the qc.html pattern.
- **State:** `NOTES` mirrors `notes/<uid>`; `ORDERS` mirrors `orders`. `page` is
  `'list'` or `'edit'`; `editId` is the open note (null = new). Editor scratch state
  lives in `_editChecklist`, `_editTags`, `_editPhotos`, `_pendingPhotos`,
  `_editPinned`, `_photosCollapsed` — initialized by `viewEdit()` from the record.
- **Firebase bridge:** module script exposes `ntSet` / `ntUpdate` / `ntRemove` /
  `ntUpload`; the classic script wraps them as `dbSet` / `dbRemove` / `upload` (with
  the standard sanitize + toast-on-error). The notes listener attaches per-uid on
  auth (`onValue(ref(db,'notes/'+user.uid))`).
- **Toast:** `ntToast(msg, 'ok'|'err')`.

## Pages / rendering

`render()` switches on `page`:

- **`list`** → `viewList()`: toolbar (New note + search box), tag-filter chips, and
  `gridHtml()` — the card grid. Search re-renders only the grid (`ntRenderGrid`), not
  the whole page, so the search box keeps focus. Filtering: `filterTag` (chip toggle),
  `pinnedOnly` (Pinned nav/dock). Sort: pinned first, then `updatedAt` desc.
- **`edit`** → `viewEdit()`: the editor doubles as the viewer (no read-only mode).
  `render()` early-returns if `#nt-editor` already exists so background Firebase
  refreshes don't wipe unsaved typing — **don't remove that guard.**

## Autosave (no Save button)

Every change (title, body, checklist, tags, job link, photos, pin) calls
`ntQueueSave()`, which debounces ~0.9s into `ntAutoSave()`. A `savestat` chip in
the toolbar shows Saving… / Saved / Not saved. Key invariants:

- `ntCapture()` snapshots ALL state **synchronously** — navigating away can't lose
  what was already typed. An empty NEW note is never created; the first real
  content assigns `editId` so later saves update the same record.
- Saves run one at a time on `_asChain` (a promise chain) so pending-photo uploads
  can't run twice; a failed photo upload stays in `_pendingPhotos` and retries on
  the next save.
- `ntFlushSave()` runs on Back, sidebar/dock nav (`showNtPage`), `visibilitychange`
  → hidden, and `pagehide` — the "locked the phone mid-note" path.
- `ntDelete` sets `_asDeleted` so an in-flight or queued save can't resurrect the
  note (`_ntDoSave` re-deletes if a save landed after the delete).

## Editor pieces

- **Rich text:** a `contenteditable` div (`#nt-body`) with an `execCommand` toolbar —
  Title (H2), Heading (H3), Body (P), bold, italic, bullet list. Toolbar buttons use
  `onmousedown` + `preventDefault` so the text selection isn't lost. `execCommand` is
  deprecated-but-everywhere; it's fine for this scale.
- **Sanitizing:** on save the body HTML goes through `stripDangerous()` (drops
  `<script>`/`<style>`, `on*=` handlers, `javascript:` URLs). Saved body is injected
  back with `innerHTML` when reopening — keep the sanitizer if you touch the save path.
  Plain-text derivatives use `stripHtml()` (snippets, search).
- **Checklist:** structured array (`{id,text,done}`), NOT part of the rich-text body.
  Rendered by `ntRenderChecklist()`; empty-text items are dropped on save.
- **Tags:** a FIXED set, defined in the `TAGS` constant (`Site Visit`, `Open Orders`,
  `RFQ`, `Purchasing`, `Fab Note`, `Scheduling`) — tap-to-toggle chips in the editor
  (`ntToggleTag`) and the same six as filter chips on the list. Chips are
  **icon-only** (owner prefers minimal text): `TAG_ICONS` maps tag → Tabler icon
  (`tagIcon()` falls back to `tag` for retired tags); the name lives in `title=`.
  The editor toolbar Back/Pin/Delete buttons are icon-only too (`.btn.icon`). No free-text tags;
  to change the vocabulary, edit `TAGS` (old notes keep any retired tag silently on
  the record). Tag names must stay free of quotes/backslashes — they're echoed into
  inline `onclick` attributes.
- **Title + customer:** the title input doubles as a customer type-ahead
  (`ntTitleSearch` → `#nt-title-results` → `ntPickCustomer`). Picking a match
  ATTACHES the customer to the note (`_editCustomer` / record field `customer`),
  clears the search text from the input, and shows a removable chip under the
  title (`ntRenderCustSel` / `ntClearCustomer`). If nothing matches exactly, the
  last option is `ntAddCustomer()` — creates the customer AND attaches it. List
  cards render the customer in parentheses after the title ("Title (Customer)");
  search matches it. Options use `onmousedown` + `preventDefault` so the input's
  blur doesn't eat the tap.
- **Job / order link:** a type-to-search picker (`ntOrderSearch` → `.rv-results`
  list → `ntPickOrder`; chosen job shows as a chip with an X, `ntClearOrder`), not a
  dropdown. Search matches `orderLabel()` = customer · part · Job # · PO. The main
  list search also matches the linked job via `orderSearchText()`, so a part number
  or PO finds the notes tied to it.
- **Photos:** collapsible card ("Photos (n)" header toggles `_photosCollapsed`;
  auto-expands when adding, auto-collapses when opening a note that has photos —
  that's the owner-requested "photos under the note but hideable" behavior).
  Saved photos (`_editPhotos`, have `.url`) and pending files (`_pendingPhotos`,
  not yet uploaded) render side by side; X buttons remove either. Uploads happen
  during autosave, sequentially; a failed upload stays pending and retries on the
  next save.
- **Pin:** toolbar button in the editor (`ntTogglePinEdit`), pin icon on each card
  in the list (`ntTogglePin` writes immediately).

## Record shape

```
notes/<uid>/<noteId> = {
  id, title, body (sanitized HTML), checklist:[{id,text,done}],
  tags:[string], orderId, customer (name string), photos:[{name,url,type}],
  pinned:bool, createdAt, updatedAt, by (email)
}
```

## Gotchas

- **Silent saves = missing `notes/` security rule.** Same #1 rule as the rest of the
  suite, but remember the rule is per-uid (`notes/$uid`), not a flat namespace.
- The editor's early-return guard in `render()` (see above) is what protects unsaved
  typing from the realtime listener; if you add new pages, keep that pattern in mind.
- `noteCard()`, the tag chips, and the job-picker results embed ids/tags in inline
  `onclick` strings — ids are app-generated and tags come from the fixed `TAGS` list,
  so both are safe. If you ever put a user-entered value into an inline handler,
  strip quotes/backslashes from it first.
- Deleting a note removes the RTDB record but **not** its uploaded photos from
  Storage (same behavior as the other apps — orphaned files are accepted).
- The body is HTML: never feed it through `esc()` when reopening (it would show tags
  as text), and never inject it anywhere without `stripDangerous` having run at save.

## Cross-app nav

The Notes dock chip (indigo, `ti-notes`) exists in `quote.html`, `apar.html`,
`qc.html`, and notes links back to all four. `orders.html` has no app-switcher at
all (pre-existing gap).
