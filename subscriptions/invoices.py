from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _invoice_font():
    font_path = Path(settings.BASE_DIR) / "static" / "fonts" / "NotoSansDevanagari-Variable.ttf"
    if font_path.exists():
        font_name = "NotoSansDevanagari"
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
        return font_name
    return "Helvetica"


def build_invoice_pdf(invoice):
    payment = invoice.payment
    buffer = BytesIO()
    font = _invoice_font()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Invoice {invoice.invoice_number}",
        author=settings.ORGANIZATION_NAME,
    )
    styles = getSampleStyleSheet()
    for style_name in ("Normal", "Title", "Heading2"):
        styles[style_name].fontName = font
    small = ParagraphStyle("InvoiceSmall", parent=styles["Normal"], fontName=font, fontSize=8.5, leading=12)
    right = ParagraphStyle("InvoiceRight", parent=styles["Normal"], fontName=font, alignment=TA_RIGHT)
    title = ParagraphStyle("InvoiceTitle", parent=styles["Title"], fontName=font, textColor=colors.HexColor("#7b2435"))
    story = [
        Table(
            [[
                Paragraph(f"<b>{escape(settings.ORGANIZATION_NAME)}</b><br/>{escape(settings.ORGANIZATION_ADDRESS)}<br/>{escape(settings.ORGANIZATION_EMAIL)}<br/>{escape(settings.ORGANIZATION_PHONE)}", small),
                Paragraph(f"<b>ANNUAL MEMBERSHIP DONATION RECEIPT</b><br/><br/>Receipt: {invoice.invoice_number}<br/>Date: {invoice.issued_at:%d %b %Y}", right),
            ]],
            colWidths=[105 * mm, 50 * mm],
        ),
        Spacer(1, 9 * mm),
        Paragraph("Bill To", title),
        Paragraph(
            f"<b>{escape(payment.user_name)}</b><br/>{escape(payment.user_email)}<br/>{escape(payment.user_phone)}<br/>{escape(payment.user_address)}",
            styles["Normal"],
        ),
        Spacer(1, 8 * mm),
    ]
    item_table = Table(
        [
            ["Description", "Qty", "Amount"],
            [invoice.description, "1", f"INR {invoice.subtotal_paise / 100:,.2f}"],
            ["Tax", "", f"INR {invoice.tax_paise / 100:,.2f}"],
            ["Total Paid", "", f"INR {invoice.total_paise / 100:,.2f}"],
        ],
        colWidths=[100 * mm, 18 * mm, 37 * mm],
    )
    item_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7b2435")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8c9b8")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), font),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff0d8")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([
        item_table,
        Spacer(1, 8 * mm),
        Paragraph(f"Razorpay Order ID: {escape(payment.razorpay_order_id)}<br/>Razorpay Payment ID: {escape(payment.razorpay_payment_id)}", small),
        Spacer(1, 12 * mm),
        Paragraph("Yearly membership donation received by Dharm Raksha Sangh. This document is electronically generated and does not require a signature.", small),
    ])
    if settings.ORGANIZATION_GSTIN:
        story.append(Paragraph(f"Supplier GSTIN: {escape(settings.ORGANIZATION_GSTIN)}", small))
    else:
        story.append(Paragraph("GST has not been charged. This is a membership donation receipt, not a GST tax invoice. A successfully processed voluntary donation is non-refundable except duplicate debit, failed activation, or where required by law.", small))
    document.build(story)
    return buffer.getvalue()
