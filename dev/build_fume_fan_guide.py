# -*- coding: utf-8 -*-
"""Build the BSMP Laser Fume Extraction Fan spec + maintenance sheet (Huayuan 6-46-3A centrifugal blower) as a PDF.

Source: the fan's own nameplate (photo kept beside the guide in docs/equipment/laser-fume-fan/). No supplier
manual exists for this unit; everything not on the nameplate is marked as typical or to-confirm.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, Image)

HERE = os.path.dirname(os.path.abspath(__file__))
DOCDIR = os.path.join(HERE, "..", "docs", "equipment", "laser-fume-fan")
OUT = os.path.join(DOCDIR, "BSMP Laser Fume Extraction Fan - Spec and Maintenance.pdf")
PLATE = os.path.join(DOCDIR, "nameplate.jpg")
FAN = os.path.join(DOCDIR, "fan.jpg")
LOGO = r"C:/Users/info/bertsmp-site/assets/img/logo.png"

DOC_ID = "BSMP-MG-003 Rev A"
DATE = "2026-10-10"

INK = colors.HexColor("#1f2328")
MUTED = colors.HexColor("#5c6470")
RED = colors.HexColor("#c8102e")
LINE = colors.HexColor("#c9ced6")
HEAD_BG = colors.HexColor("#eef1f5")
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
    "body": st("body", spaceAfter=5),
    "small": st("small", fontSize=8, leading=10.5, textColor=MUTED),
    "cell": st("cell", fontSize=8, leading=10),
    "cellb": st("cellb", fontName="Helvetica-Bold", fontSize=8, leading=10),
    "bullet": st("bullet", leftIndent=12, bulletIndent=2, spaceAfter=2),
    "kicker": st("kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=RED),
    "cap": st("cap", fontSize=7.5, leading=9.5, textColor=MUTED),
}

def P(txt, style="body"):
    p = Paragraph(txt, S[style])
    if style == "h1":
        p.keepWithNext = True
    return p

def B(txt):
    return Paragraph(txt, S["bullet"], bulletText="\u2022")

def tbl(rows, widths, header=True, row_bg=None):
    data = [[Paragraph(c, S["cellb"] if (header and i == 0) else S["cell"]) if isinstance(c, str) else c for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    ts = [("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if header:
        ts += [("BACKGROUND", (0, 0), (-1, 0), HEAD_BG), ("LINEBELOW", (0, 0), (-1, 0), 1, INK)]
    for r_i, bg in (row_bg or {}).items():
        ts.append(("BACKGROUND", (0, r_i), (-1, r_i), bg))
    t.setStyle(TableStyle(ts))
    return t

def note(txt, kicker=None, bg=NOTE_BG, width=7.0 * inch):
    inner = ([Paragraph(kicker, S["kicker"])] if kicker else []) + [Paragraph(txt, S["body"])]
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, RED),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t

def photo(path, width):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    return Image(path, width=width, height=width * h / w)

def on_page(canv, doc):
    canv.saveState()
    w, h = letter
    canv.setStrokeColor(RED); canv.setLineWidth(1.5)
    canv.line(0.75 * inch, h - 0.62 * inch, w - 0.75 * inch, h - 0.62 * inch)
    canv.setFont("Helvetica-Bold", 8); canv.setFillColor(INK)
    canv.drawString(0.75 * inch, h - 0.55 * inch, "Bert's Sheet Metal Products, Inc.")
    canv.setFont("Helvetica", 8); canv.setFillColor(MUTED)
    canv.drawRightString(w - 0.75 * inch, h - 0.55 * inch, "Laser Fume Extraction Fan  \u00b7  Spec & Maintenance")
    canv.setStrokeColor(LINE); canv.setLineWidth(0.5)
    canv.line(0.75 * inch, 0.6 * inch, w - 0.75 * inch, 0.6 * inch)
    canv.setFont("Helvetica", 7.5); canv.setFillColor(MUTED)
    canv.drawString(0.75 * inch, 0.45 * inch, f"{DOC_ID}  \u00b7  Issued {DATE}  \u00b7  Source: fan nameplate (no supplier manual)")
    canv.drawRightString(w - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canv.restoreState()

doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                      topMargin=0.85 * inch, bottomMargin=0.8 * inch,
                      title="BSMP Laser Fume Extraction Fan - Spec and Maintenance", author="Bert's Sheet Metal Products, Inc.",
                      subject="Dongguan Huayuan 6-46-3A low-noise centrifugal fan, 3 kW 380 V: identification, spares, maintenance, troubleshooting")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])

story = []
W = 7.0 * inch

# =============== PAGE 1: what it is ===============
logo = Image(LOGO, width=1.9 * inch, height=1.9 * inch * 186 / 600)
head = Table([[logo, [P("Laser Fume Extraction Fan", "title"),
                      P("The blue centrifugal blower beside the fiber laser. It pulls smoke and dust out of the cutting-table "
                        "plenum through the flex hose and pushes it up the outlet duct.", "subtitle")]]],
             colWidths=[2.1 * inch, 4.9 * inch])
head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story += [head, Spacer(1, 4),
          P(f"Bert's Sheet Metal Products, Inc. \u00b7 9521 Irondale Ave, Chatsworth, CA 91311 \u00b7 818.775.0104 \u00b7 {DOC_ID}", "small"),
          Spacer(1, 6)]

story.append(P("Nameplate", "h1"))
story.append(P("Values marked ~ are hard to read on the plate (worn and dirty). Correct them here when someone reads them in good light."))
story.append(tbl([
    ["Field", "On the plate", "In US units / meaning"],
    ["Maker", "Dongguan Huayuan Ventilation Equipment Co., Ltd. (Dongguan, Guangdong, China)", ""],
    ["Product", "Low Noise Centrifugal Ventilator", ""],
    ["Model (Type)", "<b>6-46-3A</b> (QC sticker: 6-46 No.3A)", "See \u201cWhat the model number means\u201d below"],
    ["Power", "3 kW", "about 4 HP"],
    ["Speed", "~3455 r/min", "2-pole motor running on 60 Hz"],
    ["Flow", "~2891 m\u00b3/h", "<b>about 1,700 CFM</b>"],
    ["Total pressure", "~1452 Pa", "<b>about 5.8 in. water column</b>"],
    ["Voltage", "380 V, 3-phase", "Same supply as the laser and chiller (step-up transformer). Expect about 6\u20137 A per leg at full load."],
    ["Serial no.", "~1051", ""],
    ["Built", "~2024/01", "Arrived with the laser (Bescutter, mid-2024)"],
], [1.2 * inch, 2.9 * inch, 2.9 * inch]))
story.append(Spacer(1, 6))

story.append(P("What the model number means", "h1"))
story.append(B("<b>6-46</b> \u2014 the fan family (Chinese standard naming, like the common 4-72 and 9-19 series). 6-46 is a medium/high-pressure "
               "design: it trades some volume for suction, which is what you need to pull through a long hose and a filter."))
story.append(B("<b>No.3</b> \u2014 impeller size number. No.3 = about <b>300 mm (12 in.)</b> impeller diameter."))
story.append(B("<b>A</b> \u2014 drive type A = <b>direct drive</b>. The impeller sits on the motor shaft. No belt, no pulleys, no separate "
               "fan bearings. The only wear parts are the motor's own two bearings."))
story.append(Spacer(1, 6))

ph = Table([[[photo(PLATE, 3.4 * inch), Paragraph("Nameplate (photo 2026-10-10).", S["cap"])],
             [photo(FAN, 3.4 * inch), Paragraph("The fan: motor with fan cover in front, scroll housing, flex hose from the table (right), outlet to the duct (top).", S["cap"])]]],
           colWidths=[3.5 * inch, 3.5 * inch])
ph.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story.append(ph)

story.append(PageBreak())

# =============== PAGE 2: maintenance, troubleshooting, spares ===============
story.append(P("Maintenance schedule", "h1"))
story.append(tbl([
    ["How often", "Task", "Who"],
    ["Daily", "Listen when the laser starts: steady hum, no rattle or scraping. Check the hose is on and not crushed or kinked.", "Laser operator"],
    ["Weekly", "Blow dust off the motor fins and the fan cover grille (power off). A dusty motor runs hot. Check the hose clamps and the tape on the outlet joint.", "Laser operator"],
    ["Monthly", "Look for dust leaking out at the outlet flange and the scroll seams. Fresh dust on the housing = a leak; reseal with foil HVAC tape or gasket.", "Laser operator"],
    ["Every 6 months", "Lock out, open the inlet and look at the impeller blades. Scrape off dust/dross buildup evenly (a lopsided cake throws it out of balance). Spin by hand: it should turn free and quiet.", "Manager"],
    ["Yearly", "Electrician: amps per leg at full load (should be even, under the motor's FLA), terminal box tight and dry, insulation to ground.", "Electrician"],
    ["When needed", "Smoke hanging over the table: check the filter downstream first, then hose and joints, then the fan.", "Anyone"],
], [1.05 * inch, 4.85 * inch, 1.1 * inch], row_bg={4: WARN_BG, 5: WARN_BG}))
story.append(Spacer(1, 4))
story.append(note("Always lock out the fan's power before reaching into the inlet or outlet. A 300 mm impeller at 3,450 rpm does not stop fast, "
                  "and on a direct-drive fan the impeller IS the motor shaft.", kicker="Safety"))

story.append(P("Troubleshooting", "h1"))
story.append(tbl([
    ["Symptom", "Most likely cause", "What to do"],
    ["Weak suction, smoke at the table", "Loaded filter downstream, crushed/kinked hose, leaking joint, dampers closed", "Filter first. Then walk the hose and the outlet duct for leaks. Then the fan."],
    ["Weak suction but the fan sounds normal", "<b>Running backwards.</b> A centrifugal fan running in reverse still blows, just much weaker.", "Look at the motor fan through the cover grille at start-up; match the arrow on the scroll. Wrong = swap any two of the three motor leads (electrician)."],
    ["Vibration or new noise", "Dust caked unevenly on the impeller; loose mounting bolts; motor bearing going", "Lock out, clean the impeller, tighten the base bolts. Grinding or growling that stays = bearings."],
    ["Trips the overload / breaker", "Lost phase, low voltage from the transformer, bearings dragging, impeller rubbing", "Electrician: voltage and amps on all three legs. Spin by hand with power off."],
    ["Motor too hot to touch", "Dirty fins, blocked fan cover, one leg low", "Clean the fins and grille; have the amps checked."],
], [1.6 * inch, 2.5 * inch, 2.9 * inch], row_bg={2: FAIL_BG}))

story.append(P("Spares and replacement", "h1"))
story.append(B("<b>Motor:</b> any 3 kW (4 HP), 2-pole, 380 V 3-phase, foot-mount (B3) or foot-and-flange (B35) motor. Read the frame size "
               "(probably 100L) and the shaft diameter off the motor's own label (round sticker on the fan cover) before ordering, "
               "and the impeller bore must match the shaft."))
story.append(B("<b>Motor bearings:</b> two deep-groove ball bearings, sizes printed on the motor label or stamped on the bearings (frame 100L is usually 6206 both ends)."))
story.append(B("<b>Whole fan:</b> search \u201c6-46-3A centrifugal fan 3kW\u201d (Alibaba / Huayuan), or a US high-pressure blower rated about "
               "<b>1,700 CFM at 6 in. w.c.</b> with matching inlet/outlet sizes."))
story.append(Spacer(1, 6))

story.append(P("Fill in when known", "h1"))
story.append(tbl([
    ["Item", "Value"],
    ["Motor label: maker / frame / FLA / shaft", ""],
    ["Motor bearing numbers (front / back)", ""],
    ["Inlet hose size / outlet duct size", ""],
    ["Filter downstream: make / element part no.", ""],
    ["Amps per leg at full load (date)", ""],
], [3.0 * inch, 4.0 * inch], row_bg={}))

doc.build(story)
print("wrote", os.path.abspath(OUT))
