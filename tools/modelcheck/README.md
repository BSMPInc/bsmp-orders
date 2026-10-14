# BSMP Model Check helper

Lets the QC app's **Model Check** page compare the customer's 3D model (STEP / IGES / SLDPRT / Parasolid)
with the SolidWorks model we built. The browser can't drive SolidWorks, so this small program runs on the
SolidWorks PC and does the geometry there.

- `helper.py` — local web service on `http://127.0.0.1:8767` (this PC only). Endpoints: `/status`, `/parts`
  (parts open in SolidWorks), `/check` (run a compare). Accepts calls only from the QC app's own sites.
- `compare.py` — the compare itself (also runs from the command line:
  `python compare.py <ours.sldprt> <theirs.step>` prints the findings as JSON).
- `Start Model Check helper.bat` — starts the helper in the background (no window). Starting it twice is harmless.

Starts with Windows on the office PC: shortcut `BSMP Model Check helper.lnk` in the user's Startup folder
(`pythonw.exe helper.py`, no window). Delete that shortcut to stop it auto-starting.

Needs: SolidWorks open, Python with `pywin32`. Log: `%LOCALAPPDATA%\BSMP\ModelCheck.log`.

## How the compare works
1. Both solids are **copied in memory** — nothing is saved, documents you already have open are never closed.
2. The customer copy is turned (best of the 24 proper axis rotations, scored by matching hole centres;
   mirror images are never tried, a mirror is a real difference) and moved onto ours using the big flat faces.
3. Each copy is subtracted from the other. Leftover pieces = real differences: red = only in our model,
   blue = only in theirs. Pieces under 0.0002 in³ or thinner than 0.004" on average are hairline slivers
   (e.g. a .001 bend-radius difference) and are only counted.
4. Suggested labels: a customer-only pad ≤ .010" thick = **paint masking**; customer material inside one of
   our holes = **turret form** (half shear etc.). The user still signs every difference off with a reason.

First proven on Absolute 11207-001 (2026-10-14): found the owner's flattening clearances, a .005" paint-masking
disc and 9 half shears — nothing else.
