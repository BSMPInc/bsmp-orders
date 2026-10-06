# notes.md — Notes (`notes.html`)

> Read this together with the root `CLAUDE.md`. Deep-dive for the Notes app only.
> App accent: **warm yellow** `--accent:#f7d774` (2026-10-06, was indigo) — yellow is a FILL with dark text
> (`--on-accent`); text/borders on white use `--accent-ink:#8a5d00`. ~750 lines.

## What it does

Private per-user notes, kept **as simple as iOS Notes** (owner, 2026-10-06: the old
tags / job links / Daily Log / separate checklist + photo cards were "too much clicking").
Usable on PC and iPhone (Safari → Share → **Add to Home Screen**; the iOS metas and
icons are in the `<head>`).

- **Two panes:** note list on the left (search, grouped Pinned / Today / Yesterday /
  Previous 7 Days / Previous 30 Days / month), one full-page editor on the right.
  Under 760 px it is one pane at a time (`body.nt-editing`), with a "‹ Notes" back button.
  On desktop the newest note opens on load.
- **Everything is in the text:** a note is ONE rich-text page. Its first line is the
  title (a new note starts on a Title line).
- **Toolbar:** Aa (format strip) · checklist · photo · save status · pin · delete.
- **Aa strip** (inline under the toolbar, does not cover the text): Title (h1), Heading
  (h2), Subheading (h3), Body (div), Monospaced (pre); B I U S; bulleted / dashed /
  numbered lists; move left/right. Tab / Shift-Tab indent list lines; Ctrl/Cmd+Shift+L
  = checklist.
- **Checklists** are `<ul class="checklist"><li class="done?">` inside the text; the round
  box is the li's `::before` — a click left of the li's box toggles `done`.
- **Photos** upload (shrunk to ≤2000 px JPEG) to Storage and are inserted as `<img>` at the
  caret; pasting an image does the same. Pasted text comes in as plain text.
- Saves as you type (800 ms debounce, flush on note switch / tab hide).

**Privacy model:** every user sees ONLY their own notes. This app deliberately has
**no operator/manager split** — privacy comes from the per-uid data path plus the
matching security rules, not from roles.

## Data & storage

- **Owns RTDB:** `notes/<auth-uid>/<noteId>` (extra **per-user** level). Record (v2):
  `{id, v:2, title, body(html), pinned, createdAt, updatedAt, by}` — `title` = first
  text line of body, kept for the list/search.
- **Older notes (no `v`)** have `title`, `body`, `checklist[]`, `photos[]`, `tags[]`,
  `orderId`, `customer`. They open folded into one page (`legacyHtml()`: title as h1,
  body, checklist as a checklist, photos as images) and are **only rewritten when
  edited**: the save sets `v:2` and nulls `checklist`/`photos` (now inside body).
- Saves use **`update()`, never `set()`**: `pinned`, `tags`, `orderId`, `customer` stay.
- **Daily Log entries** (`kind:'log'`) still live under the same path; the page was
  removed 2026-10-06 and the list filters them out. Data untouched (git history has the UI:
  commits d71dfb7…3bd2e90).
- **Storage:** photo uploads go under `notes/<uid>/photos/...` (`ntUpload`).
- No reads of `orders` / `customers` any more. No localStorage keys, no AI.

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

## Structure / gotchas

- **English-only.** No `t()`/`I18N` map.
- **State:** `NOTES` mirrors `notes/<uid>`; `curId` = open note (null while a new note
  has no text — the first real text claims an id in `ntCapture()`, so empty notes are
  never written); `editing` = the editor pane holds a note.
- **Firebase listener updates only re-render the list** (`renderList()`); the editor is
  rebuilt only on open/new (`buildEditor()`), so live updates never clobber typing.
- **Paragraph separator is `div`** (`defaultParagraphSeparator`). With `p`, Chrome nested
  lists inside `<p>` and Enter stopped leaving lists (found 2026-10-06).
- **Toolbar buttons never take focus** (`keep` = preventDefault on pointerdown/mousedown).
  `restoreSel()` trusts the LIVE caret while the editor is focused; `_lastRange` is only
  for after focus was lost (photo picker). selectionchange fires late, so using
  `_lastRange` first put a fast Enter + tap back on the previous line.
- A Title/Heading tap on a list line takes the line out of the list first; a list tap on
  a heading turns it into Body first (headings can't hold lists).
- Body HTML is lightly sanitized on save (`stripDangerous`); never `esc()` the body.
- Deleting a note removes the record but not its photos in Storage (accepted, same as
  the other apps).
