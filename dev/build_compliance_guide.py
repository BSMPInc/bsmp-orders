# -*- coding: utf-8 -*-
"""Build the BSMP Material Compliance Guide (RoHS / REACH / DFARS) as a printable PDF."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, KeepTogether, Image)

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "quality", "BSMP Material Compliance Guide - RoHS REACH DFARS.pdf")
LOGO = r"C:/Users/info/bertsmp-site/assets/img/logo.png"

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

# ---- styles ----
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
    "quote": st("quote", fontName="Helvetica-Oblique", fontSize=9, leading=12, leftIndent=10, rightIndent=10),
    "kicker": st("kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=RED),
}

def P(txt, style="body"):
    p = Paragraph(txt, S[style])
    if style in ("h1", "h2"):
        p.keepWithNext = True
    return p

def B(txt):
    return Paragraph(txt, S["bullet"], bulletText="\u2022")

def tbl(rows, widths, header=True, zebra=False, row_bg=None):
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

def note(txt, bg=NOTE_BG, kicker=None):
    inner = []
    if kicker:
        inner.append(Paragraph(kicker, S["kicker"]))
    inner.append(Paragraph(txt, S["body"]))
    t = Table([[inner]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, RED),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t

# ---- page furniture ----
DOC_ID = "BSMP-QG-001 Rev A"
DATE = "2026-09-18"

def on_page(canv, doc):
    canv.saveState()
    w, h = letter
    # header
    canv.setStrokeColor(RED); canv.setLineWidth(1.5)
    canv.line(0.75 * inch, h - 0.62 * inch, w - 0.75 * inch, h - 0.62 * inch)
    canv.setFont("Helvetica-Bold", 8); canv.setFillColor(INK)
    canv.drawString(0.75 * inch, h - 0.55 * inch, "Bert's Sheet Metal Products, Inc.")
    canv.setFont("Helvetica", 8); canv.setFillColor(MUTED)
    canv.drawRightString(w - 0.75 * inch, h - 0.55 * inch, "Material Compliance Guide  \u00b7  RoHS / REACH / DFARS")
    # footer
    canv.setStrokeColor(LINE); canv.setLineWidth(0.5)
    canv.line(0.75 * inch, 0.6 * inch, w - 0.75 * inch, 0.6 * inch)
    canv.setFont("Helvetica", 7.5); canv.setFillColor(MUTED)
    canv.drawString(0.75 * inch, 0.45 * inch, f"{DOC_ID}  \u00b7  Issued {DATE}  \u00b7  Uncontrolled when printed. Verify current revision in QC.")
    canv.drawRightString(w - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canv.restoreState()

doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                      topMargin=0.85 * inch, bottomMargin=0.8 * inch,
                      title="BSMP Material Compliance Guide", author="Bert's Sheet Metal Products, Inc.",
                      subject="RoHS, REACH and DFARS as they apply to BSMP")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])

story = []
W = 7.0 * inch

# =============== PAGE 1: cover block + one-page summary ===============
logo = Image(LOGO, width=1.9 * inch, height=1.9 * inch * 186 / 600)
head = Table([[logo, [P("Material Compliance Guide", "title"),
                      P("RoHS, REACH and DFARS: what they are, when they apply to our work, and how we prove it.", "subtitle")]]],
             colWidths=[2.1 * inch, 4.9 * inch])
head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story += [head, Spacer(1, 4),
          P(f"Bert's Sheet Metal Products, Inc. \u00b7 9521 Irondale Ave, Chatsworth, CA 91311 \u00b7 818.775.0104 \u00b7 info@bertsmp.com \u00b7 {DOC_ID}", "small"),
          Spacer(1, 10)]

story.append(P("The one-minute version", "h1"))
story.append(P("None of these rules apply to us directly. They apply to our customers, who pass them down on the PO. "
               "The trigger is always paper: a PO note, a drawing note, a supplier quality clause, or a declaration form. "
               "If the PO is silent, we do nothing extra and make no claim. If the PO calls one out, we source to it and cite it on the Certificate of Conformance."))

summary = [
    ["Rule", "What it restricts", "Where it bites a sheet metal shop", "How we prove it"],
    ["<b>RoHS</b><br/>EU Directive 2011/65/EU as amended by (EU) 2015/863 (\u201cRoHS 3\u201d)",
     "10 substances in electrical products: lead, mercury, cadmium, hex chrome, PBB, PBDE, 4 phthalates. Limit 0.1% (cadmium 0.01%).",
     "Yellow zinc chromate and hex-chrome chem film (Alodine 1200). Leaded free-machining stock (12L14, 2011). Vinyl trim, rubber, foam.",
     "Mill cert that says RoHS, or a distributor RoHS letter. Finisher cert stating trivalent. Hardware maker statement."],
    ["<b>REACH</b><br/>EU Regulation (EC) 1907/2006, Article 33",
     "Disclosure, not a ban. If any SVHC on the Candidate List is above 0.1% w/w, we must name it. List grows twice a year (240+ entries).",
     "Same as RoHS plus: lead has NO alloying exemption under REACH, so 12L14 must be declared. Hex chrome baths. Cobalt and nickel compounds in some finishes.",
     "Distributor RoHS/REACH letter (usually one combined letter). Finisher statement. Refresh yearly because the list changes."],
    ["<b>DFARS</b><br/>252.225-7009 Specialty Metals",
     "Specialty metals in DoD deliverables must be melted in the USA or a qualifying country (NATO allies, Japan, Australia, Israel, others).",
     "Stainless and alloy steel, titanium. Plain carbon steel and aluminum are NOT specialty metals, so foreign-melt A1008 and 5052 are fine.",
     "Mill cert showing melt country. \u201cDFARS domestic melt\u201d written on our PO to the distributor for stainless and alloy steel."],
]
story.append(tbl(summary, [1.35 * inch, 1.9 * inch, 1.95 * inch, 1.8 * inch]))
story.append(Spacer(1, 8))

story.append(P("Our stock at a glance", "h2"))
stock = [
    ["Material we buy", "RoHS", "REACH", "DFARS specialty metal?", "Notes"],
    ["A1008 / A36 cold & hot rolled steel", "Pass", "Pass", "No", "Paperwork only. Need cert line or letter."],
    ["Galvanized / galvanneal (A653)", "Pass", "Pass", "No", "Zinc coating is fine. Any chromate passivation on the coil should be trivalent; ask if in doubt."],
    ["5052 / 6061 aluminum", "Pass", "Pass", "No", "Spec caps unlisted elements at 0.05% each, so lead cannot exceed the 0.1% limit."],
    ["304 / 316 stainless", "Pass", "Pass", "YES", "Foreign melt is a DFARS problem. Cert must show melt country."],
    ["4130 / alloy steel", "Pass", "Pass", "YES", "Same DFARS melt rule as stainless."],
    ["12L14 leaded steel", "Pass (exempt)", "DECLARE", "No", "Lead 0.15 to 0.35%. RoHS exemption 6(a) covers it. REACH requires naming lead on the declaration."],
    ["2011 aluminum", "RISK", "DECLARE", "No", "Lead 0.2 to 0.6% can exceed the 0.4% RoHS exemption limit. Avoid on RoHS jobs; use 6061."],
    ["360 brass", "Pass (exempt)", "DECLARE", "No", "Lead ~3%. RoHS exemption 6(c) allows up to 4%. REACH declaration required."],
]
story.append(tbl(stock, [1.75 * inch, 0.75 * inch, 0.75 * inch, 0.95 * inch, 2.8 * inch],
                 row_bg={1: PASS_BG, 2: PASS_BG, 3: PASS_BG, 4: WARN_BG, 5: WARN_BG, 6: WARN_BG, 7: FAIL_BG, 8: WARN_BG}))
story.append(Spacer(1, 6))
story.append(note("Bare sheet almost never fails RoHS or REACH. The outside finish and the hardware are where parts actually fail. "
                  "Stainless is where DFARS fails. Get the letters on file once and every flowdown becomes a paperwork step, not a sourcing scramble.",
                  kicker="THE PATTERN"))
story.append(PageBreak())

# =============== PAGE 2: RoHS ===============
story.append(P("RoHS in detail", "h1"))
story.append(P("<b>Restriction of Hazardous Substances.</b> A European Union product law for electrical and electronic equipment. "
               "RoHS 1 (2002/95/EC) listed six substances. RoHS 2 (2011/65/EU, 2013) widened the product scope and added CE-marking duties. "
               "RoHS 3 is the informal name for amendment (EU) 2015/863, which added four phthalates from July 2019. "
               "When a customer writes RoHS, RoHS 2, or RoHS 3 today they all mean the same ten-substance list below."))

rohs = [
    ["Substance", "Limit (w/w, per homogeneous material)", "Where it shows up in our work"],
    ["Lead (Pb)", "0.1%", "Alloying element in 12L14, 2011, 360 brass. Not in A1008, 5052, 6061, or stainless."],
    ["Cadmium (Cd)", "0.01%", "Cad plating. Trace in some old alloys. Not used on RoHS work."],
    ["Mercury (Hg)", "0.1%", "Not in metals. Ignore."],
    ["Hexavalent chromium (Cr VI)", "0.1%", "Yellow / olive zinc chromate, Alodine 1200 / 1201 chem film, some passivates. THE usual failure."],
    ["PBB, PBDE", "0.1% each", "Flame retardants in plastics. Only if we supply plastic parts."],
    ["DEHP, BBP, DBP, DIBP (phthalates)", "0.1% each", "Plasticizers in vinyl edge trim, PVC grommets, rubber bumpers, some foam tape."],
]
story.append(tbl(rohs, [1.9 * inch, 1.6 * inch, 3.5 * inch]))
story.append(Spacer(1, 6))

story.append(P("Exemptions we rely on (Annex III)", "h2"))
story.append(B("<b>6(a)</b> lead as an alloying element in steel, up to 0.35%. Covers 12L14."))
story.append(B("<b>6(b)</b> lead in aluminum, up to 0.4%. 2011 aluminum can exceed this. Use 6061 on RoHS jobs."))
story.append(B("<b>6(c)</b> lead in copper alloys, up to 4%. Covers 360 brass and most leaded bronze."))
story.append(P("Exemptions carry expiry and renewal dates. If a customer is strict, confirm the current status before quoting a leaded alloy.", "small"))
story.append(Spacer(1, 4))

story.append(P("How to read a mill cert for RoHS", "h2"))
story.append(B("<b>Best case:</b> the cert says it. Look in the Specification block for \u201cRoHS compliant\u201d next to the ASTM grade. Cite the cert number and heat on the CoC and you are done."))
story.append(B("<b>Chemistry check:</b> find Pb and Cd in the chemistry table. Lead under 0.1% and cadmium under 0.01% passes. Total chromium (Cr) on a steel cert is metallic chromium, not hexavalent; it does not count."))
story.append(B("<b>Not listed:</b> most steel and aluminum certs never report lead. For aluminum the spec\u2019s \u201cothers, each 0.05% max\u201d proves it. For steel the spec has no lead cap, so the cert alone cannot prove compliance."))
story.append(B("<b>Then:</b> ask the distributor (TYRO) for their standing RoHS/REACH letter for that alloy family, or ask them to add \u201cRoHS compliant\u201d to the cert. Check for a page 2; remarks often land there."))
story.append(Spacer(1, 4))

story.append(P("Outside finishes: what to write on the PO to the finisher", "h2"))
fin = [
    ["Process", "Fails RoHS", "Passes RoHS", "PO wording"],
    ["Chem film (chromate conversion)", "Alodine 1200 / 1201, MIL-DTL-5541 Type I", "Alodine 5200, SurTec 650, MIL-DTL-5541 Type II (trivalent)", "\u201cMIL-DTL-5541 Type II, trivalent, RoHS compliant. State on cert.\u201d"],
    ["Zinc plating", "Yellow, olive drab, black hex chromate", "Clear or blue trivalent passivate", "\u201cASTM B633, trivalent clear, RoHS compliant. State on cert.\u201d"],
    ["Anodize", "Normally fine", "Type II / III with nickel-acetate or hot-water seal", "\u201cRoHS compliant, state on cert.\u201d Dichromate seal is hex chrome; do not allow."],
    ["Passivation (stainless)", "Normally fine", "Citric or nitric per AMS 2700 / ASTM A967", "\u201cRoHS compliant, state on cert.\u201d"],
    ["Powder coat", "Normally fine", "Nearly all modern powders", "\u201cRoHS compliant, state on cert.\u201d Ask for the powder TDS if pressed."],
]
story.append(tbl(fin, [1.4 * inch, 1.7 * inch, 1.9 * inch, 2.0 * inch], row_bg={}))
story.append(Spacer(1, 6))
story.append(note("Anodize, chem film, passivate, plating and powder coat are all OUTSIDE processes for us. The finisher\u2019s cert is what proves the finish. "
                  "If their cert does not say trivalent or RoHS, the part is not proven, no matter what the mill cert says.", kicker="REMEMBER"))
story.append(Spacer(1, 10))

# =============== PAGE 3: REACH ===============
story.append(P("REACH in detail", "h1"))
story.append(P("<b>Registration, Evaluation, Authorisation and Restriction of Chemicals.</b> EU Regulation (EC) 1907/2006, in force since 2007. "
               "Where RoHS is a short fixed list with hard limits for electrical goods, REACH covers every chemical and every article sold in the EU. "
               "It works through the <b>SVHC Candidate List</b> (Substances of Very High Concern), which the European Chemicals Agency updates twice a year, typically January and June."))
story.append(P("Our only obligation is <b>Article 33</b>: if any SVHC is present above 0.1% by weight of an article, tell the customer which one. "
               "Below that, or if none is present, say so. No registration, no fee, no testing. Naming a substance is compliance. Hiding it is the violation."))

story.append(P("SVHCs that touch sheet metal work", "h2"))
reach = [
    ["Substance", "Source in our work", "What we do"],
    ["Lead (listed 2018)", "12L14, 2011 aluminum, leaded brass. No alloying exemption under REACH.", "Declare it by name on the form or CoC. Offer 1215 / 6061 / lead-free brass if the customer objects."],
    ["Chromium trioxide and other Cr(VI) compounds", "Hex chrome chem film and yellow chromate baths. Also on the Authorisation list, which is why EU platers are dropping it.", "Specify trivalent. Finisher states it on cert."],
    ["Cobalt and nickel compounds", "Some passivation and plating chemistries. Usually below threshold in the finished part.", "Ask the finisher to confirm on their letter."],
    ["Phthalates (DEHP, DBP, BBP, DIBP)", "Vinyl trim, PVC grommets, rubber bumpers, foam tape.", "Buy from suppliers with a REACH statement, or leave the plastic parts to the customer."],
    ["Cadmium and its compounds", "Cad plating.", "Not used on REACH or RoHS work."],
]
story.append(tbl(reach, [1.7 * inch, 2.7 * inch, 2.6 * inch]))
story.append(Spacer(1, 6))

story.append(P("Who asks for REACH", "h2"))
story.append(B("<b>Aerospace and defense</b> customers ask for REACH more than RoHS, because RoHS exempts their equipment and REACH does not."))
story.append(B("<b>Medical</b> customers usually ask for both."))
story.append(B("<b>Electronics</b> customers ask for RoHS first and REACH as a follow-up survey."))
story.append(Spacer(1, 4))

story.append(P("Declaration wording", "h2"))
story.append(P("When the supplier letters are on file and nothing is declarable:", "small"))
story.append(note("No substances on the current REACH SVHC Candidate List (ECHA, as of [date]) are present above 0.1% w/w in the delivered articles, per supplier declarations on file.", bg=NOTE_BG))
story.append(Spacer(1, 4))
story.append(P("When a part does contain one, for example 12L14:", "small"))
story.append(note("The delivered articles contain lead (CAS 7439-92-1), an SVHC on the REACH Candidate List, at approximately 0.15 to 0.35% w/w as an alloying element of AISI 12L14 steel. No other SVHC is present above 0.1% w/w.", bg=WARN_BG))
story.append(Spacer(1, 6))
story.append(note("The Candidate List changes twice a year, so supplier letters age. Ask TYRO and each finisher for a fresh letter every January so nothing on file is older than a year.", kicker="YEARLY"))
story.append(PageBreak())

# =============== PAGE 4: DFARS ===============
story.append(P("DFARS in detail", "h1"))
story.append(P("<b>Defense Federal Acquisition Regulation Supplement.</b> The Department of Defense\u2019s add-on to federal purchasing rules. Its clauses flow down every PO in a defense supply chain until they reach a job shop. "
               "When a customer writes \u201cDFARS compliant material\u201d they almost always mean one clause: <b>252.225-7009, Restriction on Acquisition of Certain Articles Containing Specialty Metals</b>."))
story.append(P("The rule: any specialty metal in a part delivered to DoD must be <b>melted or produced in the United States or a qualifying country</b>. "
               "Qualifying countries are mostly NATO allies plus Japan, Australia, Israel and a few others. "
               "<b>Vietnam, Thailand, China, India, Korea, Taiwan, Mexico and Brazil are not qualifying countries.</b>"))

story.append(P("What counts as a specialty metal (defined by chemistry, not by name)", "h2"))
story.append(B("<b>Steel</b> containing more than 0.25% of chromium, nickel, molybdenum, titanium, vanadium, aluminum, cobalt, niobium or tungsten; or manganese over 1.65%, silicon over 0.60%, or copper over 0.60%."))
story.append(B("<b>Nickel, iron-nickel and cobalt alloys</b> with more than 10% other alloying metals."))
story.append(B("<b>Titanium</b> and titanium alloys. <b>Zirconium</b> and zirconium alloys."))
story.append(Spacer(1, 4))

df = [
    ["Material", "Specialty metal?", "Melt restriction applies?", "Sourcing action"],
    ["A1008 / A36 plain carbon steel", "No", "No", "None. Foreign mill certs (Vietnam, Thailand) are acceptable."],
    ["Galvanized / galvanneal", "No (base steel is plain)", "No", "None."],
    ["5052 / 6061 aluminum", "No (aluminum is not on the list)", "No", "None. Customer may still ask for domestic under Buy American; read the PO."],
    ["304 / 316 stainless", "YES (Cr, Ni)", "YES", "Write \u201cDFARS 252.225-7009, domestic or qualifying-country melt\u201d on the PO to TYRO. Cert must show melt country."],
    ["4130 and other alloy steels", "YES", "YES", "Same as stainless."],
    ["Titanium", "YES", "YES", "Same as stainless."],
]
story.append(tbl(df, [1.7 * inch, 1.3 * inch, 1.2 * inch, 2.8 * inch],
                 row_bg={1: PASS_BG, 2: PASS_BG, 3: PASS_BG, 4: WARN_BG, 5: WARN_BG, 6: WARN_BG}))
story.append(Spacer(1, 6))

story.append(P("Exceptions we use", "h2"))
story.append(B("<b>Commercial fasteners.</b> PEM inserts, screws and rivets are exempt if the maker certifies it buys at least 50% of its specialty metal from domestic or qualifying sources. PEM and most fastener houses publish this. Keep it on file."))
story.append(B("<b>De minimis.</b> Non-compliant specialty metal is allowed if it is under 2% by weight of all specialty metal in the delivered item. Saves a job when one small stainless bushing turns out to be foreign."))
story.append(B("<b>COTS.</b> Commercially available off-the-shelf items are exempt. Does not cover parts made to a customer drawing."))
story.append(Spacer(1, 4))

story.append(P("Other DFARS clauses that can land on a PO to us", "h2"))
oth = [
    ["Clause", "What it is", "What it means for us"],
    ["252.204-7012 and CMMC", "Cybersecurity. Safeguarding covered defense information; NIST SP 800-171 controls.", "A much bigger lift than any material rule. Confirm scope BEFORE accepting the PO."],
    ["252.246-7007 / 7008", "Counterfeit electronic parts.", "Buy electronics only from authorized sources with traceability. Rare for sheet metal; appears on assembly work."],
    ["252.225-7052", "Magnets and tungsten from China, Russia, North Korea, Iran.", "Only if we supply assemblies containing magnets or tungsten."],
    ["252.225-7001", "Buy American.", "Domestic end product; component cost test. Read the PO for which version applies."],
]
story.append(tbl(oth, [1.5 * inch, 2.6 * inch, 2.9 * inch]))
story.append(Spacer(1, 6))
story.append(note("Specialty metals comply with DFARS 252.225-7009. Carbon steel and aluminum are not specialty metals as defined in the clause.", bg=NOTE_BG, kicker="COC WORDING"))
story.append(P("The second sentence stops a customer bouncing a Vietnamese or Thai carbon steel cert back to us.", "small"))
story.append(PageBreak())

# =============== PAGE 5: procedure + checklist ===============
story.append(P("Shop procedure", "h1"))
story.append(P("At order entry", "h2"))
story.append(B("Read the PO, drawing notes and any attached quality clauses for RoHS, REACH, DFARS, 2011/65/EU, 2015/863, 1907/2006, 252.225-7009, or \u201chazardous substance declaration\u201d."))
story.append(B("Check the customer\u2019s supplier terms we signed at onboarding. Electronics and medical customers often put the flowdown there rather than on each PO."))
story.append(B("Flag the order in Orders with the applicable rule(s) so purchasing and QC both see it."))
story.append(P("At purchasing", "h2"))
story.append(B("<b>RoHS / REACH job:</b> order bare sheet normally. Confirm the distributor letter on file covers the alloy. Specify trivalent on every finish PO with \u201cstate RoHS compliance on cert.\u201d Check hardware finish (no yellow zinc)."))
story.append(B("<b>DFARS job:</b> for stainless, alloy steel or titanium write \u201cDFARS 252.225-7009 domestic or qualifying-country melt\u201d on the PO to the distributor. Carbon steel and aluminum need nothing extra."))
story.append(B("<b>Leaded alloys</b> on a RoHS or REACH job: stop and confirm with the customer, or substitute 1215 / 6061 / lead-free brass."))
story.append(P("At receiving and QC", "h2"))
story.append(B("Match heat number on the cert to the tag on the material and to the PO."))
story.append(B("RoHS: look for the statement on the cert. If absent, attach the distributor letter. Check for a page 2."))
story.append(B("DFARS: for specialty metals, confirm the mill and country on the cert are USA or qualifying."))
story.append(B("Finish: finisher cert must state trivalent / RoHS. Reject the cert, not the parts, if the wording is missing; ask the finisher to reissue."))
story.append(P("At shipping (Certificate of Conformance)", "h2"))
story.append(B("Cite each rule by its full name and attach the supporting certs and letters. Never make a bare claim without a document behind it."))
story.append(B("If something is unproven, say so: \u201cmaterial meets ASTM A1008 CS Type B; RoHS declaration pending from supplier.\u201d"))
story.append(Spacer(1, 6))

story.append(P("Quick reference: what to write on the CoC", "h2"))
coc = [
    ["Rule", "Wording"],
    ["RoHS", "Materials and finishes are RoHS compliant per Directive 2011/65/EU as amended by (EU) 2015/863, per mill certificate [no.], heat [no.], and finisher certificate [no.]."],
    ["REACH", "No substances on the current REACH SVHC Candidate List are present above 0.1% w/w in the delivered articles, per supplier declarations on file. [Or name the substance and CAS number.]"],
    ["DFARS", "Specialty metals comply with DFARS 252.225-7009; melt country per attached mill certificate. Carbon steel and aluminum are not specialty metals as defined in the clause."],
]
story.append(tbl(coc, [0.9 * inch, 6.1 * inch]))
story.append(Spacer(1, 10))
story.append(PageBreak())
story.append(P("Documents to keep on file (refresh every January)", "h2"))
docs = [
    ["Document", "From", "Covers", "On file?", "Date"],
    ["RoHS / REACH statement, carbon steel (A1008, A36, A653)", "TYRO", "RoHS, REACH", box(), ""],
    ["RoHS / REACH statement, aluminum (5052, 6061)", "TYRO", "RoHS, REACH", box(), ""],
    ["RoHS / REACH statement, stainless (304, 316)", "TYRO", "RoHS, REACH", box(), ""],
    ["Standing instruction: DFARS melt on all stainless / alloy for flagged POs", "TYRO", "DFARS", box(), ""],
    ["RoHS / REACH statement + list of trivalent bath names", "Chem film / plating house", "RoHS, REACH", box(), ""],
    ["RoHS / REACH statement", "Anodize house", "RoHS, REACH", box(), ""],
    ["RoHS / REACH statement", "Powder coat house", "RoHS, REACH", box(), ""],
    ["RoHS statement + DFARS fastener certification", "PEM / fastener distributor", "RoHS, REACH, DFARS", box(), ""],
    ["Customer supplier-terms review (which rules each customer flows down)", "Internal", "All", box(), ""],
]
story.append(tbl(docs, [2.9 * inch, 1.3 * inch, 1.1 * inch, 0.7 * inch, 1.0 * inch]))
story.append(Spacer(1, 8))

story.append(P("Worked examples from our own certs (Sept 2026, TYRO PO 26404)", "h2"))
story.append(B("<b>20 ga A1008 CS-B, CSVC (Vietnam), cert 241025F00033, heat 4921622:</b> Specification block reads \u201cASTM A1008 CS TYPE B / ROHS COMPLIANT.\u201d RoHS proven by the cert itself. Not a specialty metal, so the Vietnamese melt is fine for DFARS."))
story.append(B("<b>16 ga A1008 CS-B, TCRSS (Thailand), cert 15444, heat K796613:</b> no RoHS line, no Pb or Cd columns, cert says page 1 of 2 and page 2 was missing. RoHS unproven until TYRO sends page 2 or a letter. Not a specialty metal, so fine for DFARS."))
story.append(Spacer(1, 8))
story.append(P("This guide is a working summary for shop use, not legal advice. Directive text, exemption expiry dates, the SVHC list and the DFARS qualifying-country list change; verify against the current source when a customer is strict.", "small"))

doc.build(story)
print("wrote", OUT)
