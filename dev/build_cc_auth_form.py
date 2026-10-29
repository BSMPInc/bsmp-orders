# -*- coding: utf-8 -*-
"""Build PF-001, the one-time credit card authorization BSMP hands a vendor, as a one-page PDF.

Source: the Claude Docs draft "Credit Card Authorization Form" (2026-10-29). Blank form only: the card
number is written in by hand after printing, so nothing sensitive ever lands in the (public) repo.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, Image)

HERE = os.path.dirname(os.path.abspath(__file__))
DOCDIR = os.path.join(HERE, "..", "docs", "purchasing")
OUT = os.path.join(DOCDIR, "PF-001 Credit Card Authorization.pdf")
LOGO = r"C:/Users/info/bertsmp-site/assets/img/logo.png"

DOC_ID = "PF-001 Rev A"
DATE = "2026-10-29"

INK = colors.HexColor("#1f2328")
MUTED = colors.HexColor("#5c6470")
RED = colors.HexColor("#c8102e")
LINE = colors.HexColor("#c9ced6")
HEAD_BG = colors.HexColor("#eef1f5")
NOTE_BG = colors.HexColor("#f6f7f9")

def st(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=INK, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
    "title": st("title", fontName="Helvetica-Bold", fontSize=20, leading=24),
    "subtitle": st("subtitle", fontSize=10.5, leading=13.5, textColor=MUTED),
    "h1": st("h1", fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=7, spaceAfter=3),
    "body": st("body", spaceAfter=4),
    "small": st("small", fontSize=8, leading=10.5, textColor=MUTED),
    "label": st("label", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5),
    "hint": st("hint", fontSize=7, leading=8.5, textColor=MUTED),
    "fill": st("fill", fontSize=9.5, leading=12),
    "num": st("num", leftIndent=14, bulletIndent=2, spaceAfter=2),
    "kicker": st("kicker", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=RED),
}

def P(txt, style="body"):
    p = Paragraph(txt, S[style])
    if style == "h1":
        p.keepWithNext = True
    return p

W = 7.0 * inch
pdfmetrics.registerFont(TTFont("SegoeSym", r"C:/Windows/Fonts/seguisym.ttf"))
BOX = '<font name="SegoeSym" size="12">\u2610</font>'  # empty ballot box; Helvetica has no U+2610
ROW_H = 0.28 * inch

def fields(rows, label_w=2.2 * inch):
    """Two-column fill-in table: bold label (+ optional hint) on the left, a tall blank box on the right."""
    data = []
    for r in rows:
        label, hint, value = (r + ("", ""))[:3] if isinstance(r, tuple) else (r, "", "")
        cell = [P(label, "label")] + ([P(hint, "hint")] if hint else [])
        data.append([cell, P(value, "fill") if value else ""])
    t = Table(data, colWidths=[label_w, W - label_w], rowHeights=[ROW_H] * len(data))
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (0, -1), HEAD_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return t

def note(txt, kicker=None):
    inner = ([Paragraph(kicker, S["kicker"])] if kicker else []) + [Paragraph(txt, S["body"])]
    t = Table([[inner]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NOTE_BG), ("LINEBEFORE", (0, 0), (0, -1), 3, RED),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t

def on_page(canv, doc):
    canv.saveState()
    w, h = letter
    canv.setStrokeColor(RED); canv.setLineWidth(1.5)
    canv.line(0.75 * inch, h - 0.62 * inch, w - 0.75 * inch, h - 0.62 * inch)
    canv.setFont("Helvetica-Bold", 8); canv.setFillColor(INK)
    canv.drawString(0.75 * inch, h - 0.55 * inch, "Bert's Sheet Metal Products, Inc.")
    canv.setFont("Helvetica", 8); canv.setFillColor(MUTED)
    canv.drawRightString(w - 0.75 * inch, h - 0.55 * inch, "Credit Card Authorization  \u00b7  One-Time Charge")
    canv.setStrokeColor(LINE); canv.setLineWidth(0.5)
    canv.line(0.75 * inch, 0.6 * inch, w - 0.75 * inch, 0.6 * inch)
    canv.setFont("Helvetica", 7.5); canv.setFillColor(MUTED)
    canv.drawString(0.75 * inch, 0.45 * inch, f"{DOC_ID}  \u00b7  Issued {DATE}  \u00b7  Confidential once filled in")
    canv.drawRightString(w - 0.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canv.restoreState()

doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                      topMargin=0.85 * inch, bottomMargin=0.8 * inch,
                      title="PF-001 Credit Card Authorization", author="Bert's Sheet Metal Products, Inc.",
                      subject="One-time credit card charge authorization for a vendor")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])

story = []
logo = Image(LOGO, width=1.9 * inch, height=1.9 * inch * 186 / 600)
head = Table([[logo, [P("Credit Card Authorization", "title"),
                      P("Authorizes the vendor below to make <b>one single charge</b> to the card shown, for the "
                        "amount stated. It is not a standing authorization.", "subtitle")]]],
             colWidths=[2.1 * inch, 4.9 * inch])
head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story += [head, Spacer(1, 4),
          P("Bert's Sheet Metal Products, Inc. \u00b7 9521 Irondale Ave, Chatsworth, CA 91311 \u00b7 818.775.0104 "
            "\u00b7 info@bertsmp.com", "small")]

story.append(P("Vendor and charge", "h1"))
story.append(fields([
    ("Vendor / company name",),
    ("Vendor contact name",),
    ("Vendor phone / email",),
    ("BSMP PO number",),
    ("Vendor quote / invoice no.",),
    ("Description", "Goods or services being paid for"),
    ("Charge amount (USD)", "Including tax and freight", "$"),
    ("Date of charge",),
]))

story.append(P("Card information", "h1"))
story.append(fields([
    ("Card type", "", " &nbsp;&nbsp;&nbsp; ".join(f"{BOX} {c}" for c in ("Visa", "Mastercard", "American Express", "Discover"))),
    ("Name as shown on card",),
    ("Card number",),
    ("Expiration (MM/YY)",),
    ("Security code (CVV)",),
    ("Billing address", "", "9521 Irondale Ave"),
    ("City, state, ZIP", "", "Chatsworth, CA 91311"),
]))
story.append(Spacer(1, 3))
story.append(note("Write the card number by hand after printing. Hand the form over in person or by fax; "
                  "do not email it with the card number on it.", "FILL IN BY HAND"))

story.append(P("Authorization", "h1"))
story.append(P("I authorize the vendor above to charge the card above <b>one time only</b>, for no more than the "
               "amount stated. By accepting this form, the vendor agrees to:"))
for i, line in enumerate([
        "Charge only the amount stated. Any change in price needs a new signed form.",
        "Not keep the card on file or use it for any later charge.",
        "Send a receipt or paid invoice to info@bertsmp.com, referencing the BSMP PO number.",
        "Destroy this form, or black out the card number and CVV, once the charge has gone through."], 1):
    story.append(Paragraph(line, S["num"], bulletText=f"{i}."))
story.append(Spacer(1, 3))
sig = Table([[P("Authorized signature", "label"), "", P("Date", "label"), ""],
             [P("Printed name", "label"), "", P("Title", "label"), ""]],
            colWidths=[1.5 * inch, 2.6 * inch, 0.7 * inch, 2.2 * inch], rowHeights=[0.42 * inch, ROW_H])
sig.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (0, -1), HEAD_BG),
    ("BACKGROUND", (2, 0), (2, -1), HEAD_BG), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
story.append(sig)

os.makedirs(DOCDIR, exist_ok=True)
doc.build(story)
print("wrote", os.path.normpath(OUT))
