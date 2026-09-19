# -*- coding: utf-8 -*-
"""Build the BSMP Laser Air Compressor Maintenance Guide (Hoverr / Haoweier PM VSD unit) as a printable PDF.

Source: "HOVERR Operating Guide for Permanent Magnet Variable Frequency Air Compressor", Taike Machinery
Technology (Dongguan) Co., Ltd, 2025 edition, stored beside this guide in docs/equipment/air-compressor/.
Photos are pulled straight out of that PDF at build time (pypdf), so nothing is copied by hand.
"""
import io, os
from pypdf import PdfReader
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, KeepTogether, Image)

HERE = os.path.dirname(os.path.abspath(__file__))
DOCDIR = os.path.join(HERE, "..", "docs", "equipment", "air-compressor")
MANUAL = os.path.join(DOCDIR, "Hoverr PM VSD Air Compressor - Operating Guide (2025).pdf")
OUT = os.path.join(DOCDIR, "BSMP Laser Air Compressor - Maintenance Guide.pdf")
LOGO = r"C:/Users/info/bertsmp-site/assets/img/logo.png"

DOC_ID = "BSMP-MG-001 Rev B"
DATE = "2026-09-19"

# ---- palette (BSMP app design language: dark ink, red rule) ----
INK = colors.HexColor("#1f2328")
MUTED = colors.HexColor("#5c6470")
RED = colors.HexColor("#c8102e")
LINE = colors.HexColor("#c9ced6")
HEAD_BG = colors.HexColor("#eef1f5")
PASS_BG = colors.HexColor("#e6f4ea")
WARN_BG = colors.HexColor("#fff4e0")
FAIL_BG = colors.HexColor("#fde8e8")
NOTE_BG = colors.HexColor("#f6f7f9")

def st(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=INK, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
    "title": st("title", fontName="Helvetica-Bold", fontSize=20, leading=24),
    "subtitle": st("subtitle", fontSize=11, leading=14, textColor=MUTED),
    "h1": st("h1", fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=8, spaceAfter=3),
    "h2": st("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=2),
    "body": st("body", spaceAfter=5),
    "small": st("small", fontSize=8, leading=10.5, textColor=MUTED),
    "cell": st("cell", fontSize=8, leading=10),
    "cellb": st("cellb", fontName="Helvetica-Bold", fontSize=8, leading=10),
    "bullet": st("bullet", leftIndent=12, bulletIndent=2, spaceAfter=2),
    "num": st("num", leftIndent=16, bulletIndent=2, spaceAfter=2),
    "kicker": st("kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=RED),
    "cap": st("cap", fontSize=7.5, leading=9.5, textColor=MUTED),
}

def P(txt, style="body"):
    p = Paragraph(txt, S[style])
    if style in ("h1", "h2"):
        p.keepWithNext = True
    return p

def B(txt):
    return Paragraph(txt, S["bullet"], bulletText="\u2022")

def N(i, txt):
    return Paragraph(txt, S["num"], bulletText=f"{i}.")

def tbl(rows, widths, header=True, row_bg=None, col_bg=None):
    data = []
    for r_i, r in enumerate(rows):
        data.append([Paragraph(c, S["cellb"] if (header and r_i == 0) else S["cell"]) if isinstance(c, str) else c for c in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    ts = [
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if header:
        ts += [("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("LINEBELOW", (0, 0), (-1, 0), 1, INK)]
    if row_bg:
        for r_i, bg in row_bg.items():
            ts.append(("BACKGROUND", (0, r_i), (-1, r_i), bg))
    t.setStyle(TableStyle(ts))
    return t

def box():
    t = Table([[""]], colWidths=[10], rowHeights=[10])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, INK)]))
    return t

def note(txt, bg=NOTE_BG, kicker=None, width=7.0 * inch):
    inner = []
    if kicker:
        inner.append(Paragraph(kicker, S["kicker"]))
    if isinstance(txt, str):
        inner.append(Paragraph(txt, S["body"]))
    else:
        inner += txt
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, RED),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t

# ---- photos straight from the manual ----
_reader = PdfReader(MANUAL)
def manual_img(page_no, name, width):
    """Pull image `name` from manual page `page_no` (1-based) and return a reportlab Image at `width`."""
    for im in _reader.pages[page_no - 1].images:
        if im.name == name:
            pil = PILImage.open(io.BytesIO(im.data)).convert("RGB")
            buf = io.BytesIO(); pil.save(buf, "JPEG", quality=80); buf.seek(0)
            w, h = pil.size
            return Image(buf, width=width, height=width * h / w)
    raise KeyError(f"{name} not on page {page_no}")

def fig(img, caption):
    return [img, Paragraph(caption, S["cap"]), Spacer(1, 4)]

# ---- page furniture ----
def on_page(canv, doc):
    canv.saveState()
    w, h = letter
    canv.setStrokeColor(RED); canv.setLineWidth(1.5)
    canv.line(0.75 * inch, h - 0.62 * inch, w - 0.75 * inch, h - 0.62 * inch)
    canv.setFont("Helvetica-Bold", 8); canv.setFillColor(INK)
    canv.drawString(0.75 * inch, h - 0.55 * inch, "Bert's Sheet Metal Products, Inc.")
    canv.setFont("Helvetica", 8); canv.setFillColor(MUTED)
    canv.drawRightString(w - 0.75 * inch, h - 0.55 * inch, "Laser Air Compressor  \u00b7  Maintenance Guide")
    canv.setStrokeColor(LINE); canv.setLineWidth(0.5)
    canv.line(0.75 * inch, 0.6 * inch, w - 0.75 * inch, 0.6 * inch)
    canv.setFont("Helvetica", 7.5); canv.setFillColor(MUTED)
    canv.drawString(0.75 * inch, 0.45 * inch, f"{DOC_ID}  \u00b7  Issued {DATE}  \u00b7  Source: Hoverr operating guide, 2025 edition (kept with this guide)")
    canv.drawRightString(w - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canv.restoreState()

doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                      topMargin=0.85 * inch, bottomMargin=0.8 * inch,
                      title="BSMP Laser Air Compressor Maintenance Guide", author="Bert's Sheet Metal Products, Inc.",
                      subject="Hoverr / Haoweier permanent-magnet VSD integrated screw compressor: service schedule, procedures, parts, alarms")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])

story = []
W = 7.0 * inch

# =============== PAGE 1: cover + the alarm we have right now ===============
logo = Image(LOGO, width=1.9 * inch, height=1.9 * inch * 186 / 600)
head = Table([[logo, [P("Laser Air Compressor Maintenance Guide", "title"),
                      P("Hoverr / Haoweier permanent-magnet variable-speed screw compressor with tank, dryer and filters. "
                        "What to do daily, weekly, at 500 hours and every 3,000 hours, and how to clear the service alarms.", "subtitle")]]],
             colWidths=[2.1 * inch, 4.9 * inch])
head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story += [head, Spacer(1, 4),
          P(f"Bert's Sheet Metal Products, Inc. \u00b7 9521 Irondale Ave, Chatsworth, CA 91311 \u00b7 818.775.0104 \u00b7 {DOC_ID}", "small"),
          Spacer(1, 8)]

story.append(P("Rev B (2026-09-19) adds page 6: troubleshooting an overload fault or a compressor that cannot keep up, and whether a second compressor helps.", "small"))
story.append(P("Right now: the GREASE service alarm", "h1"))
story.append(P("The controller keeps five service-hour counters (air filter, oil filter, oil-air separator, lube oil, grease). "
               "When a counter reaches its preset limit the screen raises a maintenance warning for that item. "
               "The compressor keeps running on a warning; it is a reminder, not a fault. "
               "A <b>GREASE</b> warning means the grease counter has reached its limit (factory preset 3,000 hours)."))
story.append(note([
    Paragraph("What the manual does and does not say", S["kicker"]),
    Paragraph("The manual shows the GREASE counter and how to reset it, but it gives <b>no grease point, quantity or grease type</b> anywhere in its 41 pages. "
              "On this class of machine the grease interval is for the <b>permanent-magnet motor bearings</b>. The motor on our unit is a fully enclosed can with a fan grille on the back "
              "(see photo on page 3). Before anyone puts a grease gun on it, confirm with the supplier whether our motor has grease fittings at all; many of these motors use sealed bearings "
              "and the counter is only a reminder to inspect.", S["body"]),
], bg=WARN_BG))
story.append(Spacer(1, 4))
story.append(P("Do this, in order", "h2"))
story += [
    N(1, "Write down the hours. Home screen, bottom left: <b>TOTAL TIME</b>. Then Menu &rarr; Consumable Parameters: note all five RUN TIME values. Put them in the service log on the last page."),
    N(2, "Call or message the supplier (contact on page 4). Ask three things: (a) is the grease alarm the motor bearings, and where are the fittings; "
         "(b) what grease and how much per fitting; (c) the consumable-parameters password so we can reset timers ourselves. Ask for it in writing so it goes in this binder."),
    N(3, "If the supplier confirms grease fittings: stop the unit, isolate power, wait for the VFD charge light to go out, then add the specified grease sparingly (a few strokes). "
         "Over-greasing a motor bearing does more harm than under-greasing. Wipe the excess. Never mix grease types."),
    N(4, "If the supplier says sealed bearings: open the rear panel, blow the motor intake vents and grille clean from the outside in with shop air, listen for bearing noise on restart, and log it as \u201cinspected, no fittings\u201d."),
    N(5, "Reset the counter: Menu &rarr; Consumable Parameters &rarr; enter password &rarr; set <b>GREASE RUN TIME</b> to 0 &rarr; check <b>GREASE MAX TIME</b> still reads 3000 &rarr; Menu. "
         "On the home screen press and hold <b>RESET</b> for 3 seconds to clear the warning."),
    N(6, "While the panels are open, check the other four counters against their limits. If any are close, do that service now rather than opening the machine twice."),
]
story.append(Spacer(1, 6))
story.append(P("Counters and what they mean", "h2"))
story.append(tbl([
    ["Counter on screen", "Service item", "Factory limit", "Then"],
    ["AIR RUN TIME", "Intake air filter element", "500 h (first)", "3,000 h or 6 months"],
    ["OIL RUN TIME", "Oil filter element (spin-on)", "500 h (first)", "3,000 h or 6 months"],
    ["O-A RUN TIME", "Oil-air separator element (inside the tank)", "3,000 h", "3,000 h or 6 months"],
    ["LUBE RUN TIME", "Screw compressor oil (change)", "500 h (first)", "3,000 h or 6 months, sooner if oil looks dark or milky"],
    ["GREASE RUN TIME", "Grease (motor bearings; confirm with supplier)", "3,000 h", "3,000 h"],
], [1.5 * inch, 2.6 * inch, 1.1 * inch, 1.8 * inch]))
story.append(Spacer(1, 3))
story.append(P("After the first 500-hour service the manual says to set every MAX TIME to 3000 hours and every RUN TIME to 0. "
               "\u201cWhichever comes first\u201d is the rule: at our duty cycle six months will usually arrive before 3,000 hours.", "small"))

story.append(PageBreak())

# =============== PAGE 2: controller screens ===============
story.append(P("The controller: where the timers live", "h1"))
story.append(P("The touch screen has a home page and a menu. <b>Consumable Parameters</b> is the only page you need for service alarms. "
               "Do not go into Factory Parameters, VFD Parameters or Fan Settings; those are preset and a wrong entry can damage the unit."))
scr = Table([[fig(manual_img(12, "IM79.jpg", 3.35 * inch), "Home screen. TOTAL TIME bottom left. RESET clears a warning (hold 3 s). START is hold 3 s; STOP is one tap."),
              fig(manual_img(19, "IM101.jpg", 3.35 * inch), "Consumable Parameters, page 1: hours run since last reset on each item. The alarm fires when RUN TIME reaches MAX TIME.")],
             [fig(manual_img(20, "IM104.jpg", 3.35 * inch), "Consumable Parameters, page 2 (DOWN): the limits. 500 h on air, oil and lube for a new machine; 3,000 h on separator and grease."),
              fig(manual_img(29, "IM98.jpg", 3.35 * inch), "Factory Parameters (password). LOAD RUN TIME here is loaded hours; the manual\u2019s reset page sits behind the same PASSWORD button.")]],
            colWidths=[3.5 * inch, 3.5 * inch])
scr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
story.append(scr)
story.append(P("Home-screen buttons", "h2"))
story.append(tbl([
    ["Button", "What it does"],
    ["MENU", "Opens the secondary menu: Operating Parameters, User Parameters, Factory Parameters, Consumable Parameters, Fault Log."],
    ["RESET", "Press and hold 3 seconds after a warning or fault has been dealt with. Clears the message."],
    ["LOAD", "Manual mode only: tap to load, tap again to unload."],
    ["START", "Press and hold 3 seconds to start."],
    ["STOP", "Tap once. Normal shutdown (unload, then stop after the shutdown delay). Use the red mushroom E-stop only in an emergency."],
], [1.0 * inch, 6.0 * inch]))
story.append(P("Reading the home screen while it runs", "h2"))
story += [
    B("<b>PRES</b> in MPa. 1.6 MPa = 232 psi is the working pressure. Load and unload setpoints live in User Parameters."),
    B("<b>TEMP</b> is discharge temperature. Normal is roughly 75 to 95 \u00b0C. Warning at 105 \u00b0C, trip at 110 \u00b0C. A rising trend means a dirty cooler, low oil, or a room over 40 \u00b0C."),
    B("<b>FREQ</b> and <b>CURR</b> show how hard the VFD is working. Running at full frequency all day means the laser is drawing more air than the unit makes, or there is a leak."),
    B("<b>STATE</b> reads LOAD RUN, UNLOAD RUN or STOP. Long stretches of UNLOAD RUN waste power; the no-load delay in User Parameters (90 to 360 s) controls how long it idles before stopping."),
]
story.append(PageBreak())

# =============== PAGE 3: safety, machine map, supplier ===============
story.append(P("Before opening the cabinet", "h1"))
story.append(note([
    Paragraph("Every time, no exceptions", S["kicker"]),
    Paragraph("1. Press STOP and let it wind down. 2. Open the disconnect and lock it. 3. Wait until the VFD charge light is out; the drive holds a lethal charge after power-off. "
              "4. Vent the system to 0 on the internal pressure gauge before touching any filter housing, the separator cover or the pressure sensor. "
              "5. Power off the electronic drain valve before pulling the multi-stage filter housings. 6. Cooler fins, the airend and the motor are hot for a long time after a run. "
              "7. No watches or rings near the drive; insulated tools only. Only someone trained on this unit does electrical work.", S["body"]),
], bg=FAIL_BG))
story.append(Spacer(1, 4))
story.append(P("What is inside", "h2"))
mp = Table([[fig(manual_img(27, "IM134.jpg", 3.4 * inch), "Permanent-magnet motor coupled straight to the airend. The grille on the end is the motor\u2019s own cooling intake: blow it clean weekly."),
             fig(manual_img(25, "IM124.jpg", 2.75 * inch), "Oil-air separator tank cover with the minimum-pressure valve on top. The separator element is under this plate; the oil fill port and drain are on the tank.")]],
           colWidths=[3.5 * inch, 3.5 * inch])
mp.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
story.append(mp)
story.append(tbl([
    ["Part", "Where", "Why you care"],
    ["Intake air filter (paper element)", "Behind the intake grille at the back", "Dirty element starves the airend and drives up temperature"],
    ["Oil filter (spin-on can)", "On the airend / oil circuit", "Changed at 500 h then every 3,000 h"],
    ["Oil sight glass and fill port", "On the separator tank", "Idle oil level must sit between the two red lines"],
    ["Oil-air separator element", "Inside the tank, under the bolted cover", "Worn element = oil carry-over into the laser air"],
    ["Minimum-pressure valve, safety valve", "Top of the separator tank", "Do not adjust"],
    ["Pressure sensor", "On the discharge line", "Condensate in its probe hole gives false pressure readings (page 5)"],
    ["Refrigerated dryer", "Separate box on the tank", "Must run whenever the compressor runs; evaporator gauge on its front"],
    ["Multi-stage filters (AO / AA / AX / AAR / ACS)", "Row of housings after the dryer", "The laser\u2019s clean-air guarantee; change as a set every 3,000 h or 6 months"],
    ["Primary filter cartridge + electronic drain", "Base of the first housing", "Drain must be powered off before the housing comes apart"],
    ["Air receiver manual drain", "Bottom of the tank", "Open 2 to 3 times a day"],
], [2.2 * inch, 2.2 * inch, 2.6 * inch]))
story.append(PageBreak())
story.append(P("Supplier", "h1"))
story.append(P("Taike Machinery Technology (Dongguan) Co., Ltd, brand names Hoverr and Haoweier. Contact printed in the manual: Meng Hui, mobile +86 136 0266 7790 (WeChat works on that number). "
               "Have the model and the hour reading ready. The consumable-parameters password and the grease specification both have to come from them; write the answers on the log page."))
story.append(P("Our model", "h1"))
story.append(P("The manual covers the whole range. Circle ours from the nameplate on the front panel so the right parts list on page 7 gets used:"))
story.append(tbl([
    ["Model", "Motor", "Air delivery", "Laser it is sized for", "Tank", "Parts list"],
    ["HB11PM-16-300", "11 kW", "1.0 m\u00b3/min", "1 to 3 kW", "350 L", "List A"],
    ["HB15PM-16-300", "15 kW", "1.35 m\u00b3/min", "4 to 6 kW", "350 L", "List A"],
    ["HB22PM-16-300", "22 kW", "2.0 m\u00b3/min", "6 to 12 kW", "single", "List B"],
    ["TGJ-30VSD-16-500", "22 kW", "2.0 m\u00b3/min", "10 to 15 kW", "twin 560 L", "List C"],
    ["TGJ-50VSD-16-500", "37 kW", "3.7 m\u00b3/min", "15 to 20 kW", "twin 560 L", "List D"],
    ["TGX-50VSD-16-2600", "37 kW", "3.7 m\u00b3/min", "22 to 50 kW", "dual 600 L skid", "List E"],
], [1.4 * inch, 0.7 * inch, 1.0 * inch, 1.3 * inch, 1.2 * inch, 1.4 * inch]))
story.append(P("All models: 1.6 MPa (232 psi) working pressure, air cooled, 380 V 3-phase (dryer on 220 V), continuous duty. Ambient 10 to 40 \u00b0C, at least 70 cm clear on every side.", "small"))

story.append(P("User Parameters you are allowed to touch", "h1"))
story.append(tbl([
    ["Setting", "What it is", "Manual\u2019s guidance"],
    ["Load / Unload pressure", "Where the compressor starts and stops making air", "Set for the laser; keep unload below the 1.6 MPa high limit"],
    ["No-load delay", "Idle time before it shuts down after unloading", "90 to 360 seconds"],
    ["Restart delay", "Wait before it may restart after a stop", "5 to 10 seconds"],
    ["Shutdown delay", "Wind-down after STOP is pressed", "10 to 30 seconds"],
    ["Language", "Toggles English / Chinese", "One tap"],
], [1.5 * inch, 2.9 * inch, 2.6 * inch]))

story.append(PageBreak())

# =============== PAGE 4: schedule + procedures ===============
story.append(P("Service schedule", "h1"))
story.append(tbl([
    ["When", "Do", "Who"],
    ["2 to 3 times a day", "Open the manual drain on the air receiver until it blows dry air. Glance at PRES and TEMP on the screen.", "Laser operator"],
    ["Weekly", "Blow out the intake filter screen from the inside out. Blow the motor\u2019s side intake vents inward. Blow the cooler fins clean. "
               "Wipe dust off the VFD and inside the electrical box (power off). Check the electronic drain valve actually cycles. Check the oil level in the sight glass with the unit stopped.", "Laser operator"],
    ["First 500 hours (new machine)", "Change the air filter, the oil filter and the oil. Then set the three 500-hour limits to 3000 and zero the counters.", "Manager + supplier password"],
    ["Every 3,000 hours or 6 months, whichever first", "Air filter, oil filter, oil, oil-air separator element, every multi-stage filter element, primary filter cartridge. Grease per supplier. Zero all counters.", "Manager"],
    ["Any time TEMP creeps up", "Cooler fins, intake filter, oil level, room temperature, in that order.", "Anyone"],
    ["Any time the pressure reading looks wrong", "Pressure-sensor condensate procedure on this page.", "Manager"],
], [1.6 * inch, 4.2 * inch, 1.2 * inch]))
story.append(P("Oil", "h2"))
story += [
    B("Use only the supplier\u2019s screw-compressor oil (kit item 11020004, 10 L bucket; 22 kW units take one, 37 kW take two). <b>Never mix brands.</b> If the oil type is unknown, drain and refill, do not top up."),
    B("Fill only to the <b>upper red line</b> on the sight glass. Overfilling pushes oil into the air and into the laser."),
    B("Check the level with the unit stopped and pressure released. Running level reads low; that is normal."),
    B("Waste oil comes out of the drain valve at the bottom of the separator tank."),
]
story.append(P("Oil-air separator element (manual, page 25)", "h2"))
story += [
    N(1, "Stop, isolate, vent to 0. Drain the oil completely."),
    N(2, "Disconnect the external pipes from the separator cover (oil return line and the minimum-pressure valve line)."),
    N(3, "Loosen all perimeter bolts and lift the cover. Pull the old element."),
    N(4, "Look inside the tank for sludge or rust; clean if needed."),
    N(5, "Fit the new element. Keep the staple on the gasket (it grounds the element against static). Smear a thin film of oil on the gasket."),
    N(6, "Refit the cover, align the holes, tighten the bolts diagonally and evenly. Reconnect the pipes. Refill oil to the upper red line."),
]
story.append(P("Multi-stage filters and primary cartridge (manual, page 26)", "h2"))
story += [
    N(1, "Vent to 0. Power off the electronic drain valve. Remove the drain valve from the base of the first housing."),
    N(2, "Unscrew each bowl, swap the element, check the seal ring is seated, refit."),
    N(3, "Keep the grades in order (AO, then AA, then AX and so on). Never put a fine element where a coarse one goes."),
    N(4, "Filters made before May 2023 used the 034 / 015 series; later units use 035 / 018. <b>Read the label on the lower housing before ordering.</b>"),
]
story.append(P("Pressure reads wrong or the safety valve pops (manual, page 28)", "h2"))
story.append(P("Cause: condensate collects in the probe hole under the pressure sensor when the room is humid, the machine stopped hot, or it sat idle. "
               "Fix: stop, isolate, vent to 0. Unscrew the sensor, blow the hole at its base dry with an air gun, refit, restore power, restart."))
story.append(P("Air filter and oil filter", "h2"))
story.append(P("Air element: open the back panel, unclip the housing, swap the paper element, refit. Oil filter: spin off the old can, wet the new gasket with oil, spin on hand-tight plus a quarter turn. "
               "Both are 500 hours on a new machine, then 3,000 hours or 6 months."))

story.append(PageBreak())

# =============== PAGE 6: troubleshooting ===============
story.append(P("Troubleshooting: overload faults and running out of air", "h1"))
story.append(P("\u201cThe compressor keeps overloading\u201d covers three different problems with three different fixes. Work out which one you have before spending money. "
               "The fault log (Menu \u2192 Fault Log) tells you in one tap: a stored fault code means problem 1; no fault, just low pressure at the laser, means 2 or 3."))
story.append(tbl([
    ["What you see", "What it is", "What fixes it"],
    ["Screen shows an overload / overcurrent fault or an E-code and the unit stops",
     "Motor or VFD drawing too much current. Almost always heat or supply voltage, not a small compressor.",
     "Clean the cooler, intake screen and motor vents. Check oil. Check the supply voltage (below). A second compressor does nothing here."],
    ["No fault, but STATE reads LOAD RUN all day and pressure sags during cuts; the laser complains about low gas pressure",
     "Demand is higher than the unit makes. Leaks and a clogged intake filter look exactly the same as a too-small compressor.",
     "Soap-test every fitting from the outlet to the cutting head. Change the intake filter. Then, if it still sags, add capacity."],
    ["Fine on most cuts; drops out only on a pierce or a long high-pressure cut in thick material",
     "Peak demand, not average demand. The receiver empties faster than the airend refills it.",
     "More tank volume on the receiver\u2019s auxiliary port. Cheaper than a compressor and does not touch air quality."],
], [2.2 * inch, 2.3 * inch, 2.5 * inch]))
story.append(P("Supply voltage: the first thing to check on an overload fault", "h2"))
story.append(P("This unit is built for 380 V three-phase. US shops run 208, 240 or 480 V. If it was wired to 240 V without a step-up transformer, the motor pulls about 60 percent more current for the same air, "
               "and it trips on hot days and long cuts. Read <b>VOLT</b> and <b>CURR</b> on the home screen while the laser is cutting and compare with the nameplate on the motor. Rough full-load figures at 380 V:"))
story.append(tbl([
    ["Motor", "Full-load current at 380 V", "Same load at 240 V"],
    ["11 kW", "about 20 A", "about 32 A"],
    ["15 kW", "about 27 A", "about 43 A"],
    ["22 kW", "about 40 A", "about 63 A"],
    ["37 kW", "about 67 A", "about 106 A"],
], [1.2 * inch, 2.6 * inch, 3.2 * inch]))
story.append(P("The nameplate wins over this table. If CURR sits above the nameplate figure at normal pressure, the supply is wrong or the airend is dragging (low oil, wrong oil, or a failing bearing).", "small"))
story.append(P("Order of checks", "h2"))
story += [
    N(1, "Photograph the fault log and the home screen under load (PRES, TEMP, FREQ, CURR, VOLT, STATE)."),
    N(2, "Confirm the wiring voltage at the disconnect and whether a transformer is fitted."),
    N(3, "Clean the cooler fins, the intake screen and the motor vents. Confirm oil is between the red lines with the unit stopped."),
    N(4, "Soap-test fittings from the compressor outlet to the cutting head. Listen for leaks with the shop quiet. Check the intake filter element."),
    N(5, "Pressure still sags on cuts: add receiver volume on the auxiliary port."),
    N(6, "Only then: a second 16-bar compressor, a bigger unit, or nitrogen instead of air on the thick material that causes the sag."),
]
story.append(P("Feeding the tank from a second compressor: three catches", "h2"))
story.append(note([
    Paragraph("Read before plumbing anything in", S["kicker"]),
    Paragraph("<b>1. Pressure.</b> The receiver runs up to 232 psi (1.6 MPa). A normal shop compressor tops out at 125 to 175 psi; its check valve stays shut against the tank and it contributes nothing. "
              "It helps only if it is also a 16-bar unit, or if the laser is cutting at a pressure the shop compressor can hold.", S["body"]),
    Paragraph("<b>2. Air quality.</b> The tank feeds the dryer and the multi-stage filters, so any second feed must enter the tank (auxiliary port), never downstream of the filters. "
              "A piston compressor carries far more oil and water than the screw unit, and the dryer and filters are sized for this unit\u2019s flow alone. Overrun them and the elements die early and the cutting lens fogs, which costs more than the compressor.", S["body"]),
    Paragraph("<b>3. Control.</b> The two compressors do not talk to each other. Set the helper\u2019s cut-in a little below this unit\u2019s load setpoint so it runs only during a shortfall and shuts off when this unit has caught up.", S["body"]),
], bg=WARN_BG))

story.append(PageBreak())

# =============== PAGE 7: parts lists ===============
story.append(P("Parts lists (from the manual, pages 31 to 35)", "h1"))
story.append(P("Quote the material code when ordering. Every list: first service at 500 h is air filter, oil filter and oil; after that everything below every 3,000 h or 6 months."))

def parts(title, rows):
    return KeepTogether([P(title, "h2"), tbl([["Code", "Spec", "Item", "Qty", "Note"]] + rows, [0.9 * inch, 1.3 * inch, 2.0 * inch, 0.5 * inch, 2.3 * inch])])

story.append(parts("List A: HB11PM-16-300 / HB15PM-16-300 (11 to 15 kW)", [
    ["68082909", "11-15KW", "Air filter", "1", "500 h first, then 3,000 h"],
    ["68083506", "11-15KW", "Oil filter", "1", "500 h first, then 3,000 h"],
    ["11020004", "10 L", "Screw compressor oil", "1", "500 h first, then 3,000 h"],
    ["68083501", "11-15KW", "Oil-gas separator", "1", ""],
    ["10020401 / 402 / 403", "GNY-015-AO / AA / AX", "Filter elements", "1 ea", "Units built before May 2023"],
    ["10020421 / 422 / 423", "GNY-018-AO / AA / AX", "Filter elements", "1 ea", "Units built from June 2023"],
    ["13020370", "11-15KW", "Primary filter cartridge", "1", "Old and new styles exist; check the housing label"],
]))
story.append(parts("List B: HB22PM-16-300 (22 kW, single tank)", [
    ["68082910", "22-37KW", "Air filter", "1", "500 h first, then 3,000 h"],
    ["68083504", "22-37KW", "Oil filter", "1", "500 h first, then 3,000 h"],
    ["11020004", "10 L bucket", "Screw compressor oil", "1", "500 h first, then 3,000 h"],
    ["68083502", "22KW built-in", "Oil-gas separator", "1", ""],
    ["10020431 / 432 / 433", "GNY-034-AO / AA / AX", "Filter elements", "1 ea", "Units built before May 2023"],
    ["10020441 / 442 / 443", "GNY-035-AO / AA / AX", "Filter elements", "1 ea", "Units built from June 2023"],
    ["13020371", "22KW", "Primary filter element", "1", ""],
]))
story.append(parts("List C: TGJ-30VSD-16-500 (22 kW, twin tank)", [
    ["68082910", "22-37KW", "Air filter", "1", "500 h first, then 3,000 h"],
    ["68083504", "22-37KW", "Oil filter", "1", "500 h first, then 3,000 h"],
    ["11020004", "10 L bucket", "Screw compressor oil", "1", "500 h first, then 3,000 h"],
    ["68083502", "22KW built-in", "Oil-gas separator", "1", ""],
    ["10020441", "GNY-035-AO", "Filter element", "1", ""],
    ["10020442", "GNY-035-AA", "Filter element", "1", ""],
    ["10020443", "GNY-035-AX", "Filter element", "2", ""],
    ["10020445", "GNY-035-AAR", "Filter element", "1", ""],
    ["10020444", "GNY-035-ACS", "Filter element", "1", ""],
    ["13020371", "22-37KW", "Primary filter element", "1", ""],
    ["12053208", "GNY-16KG", "Electronic drain valve", "1", "Spare"],
]))
story.append(parts("List D: TGJ-50VSD-16-500 (37 kW, twin tank)", [
    ["68082910", "22-37KW", "Air filter", "1", "500 h first, then 3,000 h"],
    ["68083504", "22-37KW", "Oil filter", "1", "500 h first, then 3,000 h"],
    ["11020004", "10 L bucket", "Screw compressor oil", "2", "500 h first, then 3,000 h"],
    ["13020374", "37KW built-in", "Oil-gas separator", "1", ""],
    ["10020441", "GNY-035-AO", "Filter element", "1", ""],
    ["10020442", "GNY-035-AA", "Filter element", "1", ""],
    ["10020443", "GNY-035-AX", "Filter element", "2", ""],
    ["10020445", "GNY-035-AAR", "Filter element", "1", ""],
    ["10020444", "GNY-035-ACS", "Filter element", "1", ""],
    ["13020371", "22-37KW", "Primary filter element", "1", ""],
    ["12053208", "GNY-16KG", "Electronic drain valve", "1", "Spare"],
]))
story.append(parts("List E: TGX-50VSD-16-2600 (37 kW, skid)", [
    ["68082910", "22-37KW", "Air filter", "1", "500 h first, then 3,000 h"],
    ["68083504", "22-37KW", "Oil filter", "1", "500 h first, then 3,000 h"],
    ["11020004", "10 L bucket", "Screw compressor oil", "2", "500 h first, then 3,000 h"],
    ["13020374", "37KW built-in", "Oil-gas separator", "1", ""],
    ["10020446 / 447", "GNY-065-AO / AA", "Filter elements", "1 ea", ""],
    ["10020448", "GNY-065-AX", "Filter element", "2", ""],
    ["10020449 / 450", "GNY-065-AAR / ACS", "Filter elements", "1 ea", ""],
    ["13020371", "22-37KW", "Primary filter element", "1", ""],
    ["09080404 / 405 / 406", "GNY-CM5.0 /A /T /H", "High-precision filter sets", "1 ea", "Optional high-precision air option"],
    ["09120110 + 10080111", "GNY-026-AX", "Cutting-head protection filter + element", "1", "Optional"],
    ["12053208", "GNY-16KG", "Electronic drain valve", "1", "Spare"],
]))

story.append(PageBreak())

# =============== PAGE 6: log ===============
story.append(P("Service log", "h1"))
story.append(P("One line per visit. Hours are the TOTAL TIME on the home screen. Tick the counters you zeroed. Keep this page in the binder by the laser; photograph it into the QC app when it fills."))
story.append(tbl([
    ["Supplier answers (fill in once)", ""],
    ["Consumable-parameters password", ""],
    ["Grease point(s) and quantity", ""],
    ["Grease type / part number", ""],
    ["Oil type / part number", "11020004 (10 L)"],
    ["Our model and serial", ""],
    ["Date installed / first start", ""],
], [2.6 * inch, 4.4 * inch], header=True))
story.append(Spacer(1, 6))
story.append(P("Air / Oil / O-A / Lube / Grease columns: tick when that counter was zeroed on the controller at this visit.", "small"))
hdr = ["Date", "Total hours", "Work done", "Air", "Oil", "O-A", "Lube", "Grease", "By"]
rows = [hdr] + [["", "", "", "", "", "", "", "", ""] for _ in range(22)]
t = Table([[Paragraph(c, S["cellb"]) for c in hdr]] + [[Paragraph("", S["cell"]) for _ in hdr] for _ in range(20)],
          colWidths=[0.75 * inch, 0.75 * inch, 2.7 * inch, 0.4 * inch, 0.4 * inch, 0.4 * inch, 0.45 * inch, 0.5 * inch, 0.65 * inch],
          rowHeights=[16] + [22] * 20, repeatRows=1)
t.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("LINEBELOW", (0, 0), (-1, 0), 1, INK),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t)

doc.build(story)
print("wrote", os.path.abspath(OUT))
