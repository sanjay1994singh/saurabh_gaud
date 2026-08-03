from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from PIL import Image, ImageOps
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


DESIGN_WIDTH = 2208
DESIGN_HEIGHT = 2989


def _font_name():
    name = "NotoSansDevanagariCertificate"
    path = Path(settings.BASE_DIR) / "static" / "fonts" / "NotoSansDevanagari-Variable.ttf"
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(path)))
    return name


def _background_path():
    return finders.find("certificate_background/Certificate.jpg") or str(
        Path(settings.BASE_DIR) / "static" / "certificate_background" / "Certificate.jpg"
    )


def _background_reader():
    with Image.open(_background_path()) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        output = BytesIO()
        image.save(output, "JPEG", quality=82, optimize=True, progressive=False)
        output.seek(0)
        return ImageReader(output)


def _member_address(user):
    state_name = user.state_obj.name if user.state_obj_id else user.state
    country_name = user.country.name if user.country_id else ""
    parts = []
    for part in (user.address, user.city, state_name, country_name):
        value = str(part).strip() if part else ""
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts) or "N/A"


def _wrap(text, limit=72):
    words, lines, current = str(text).split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or ["N/A"]


def _draw_centered(pdf, text, y, size, font, color="#5b1f0d"):
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    pdf.drawCentredString(DESIGN_WIDTH / 2, DESIGN_HEIGHT - y, str(text))


def _photo_reader(user):
    if not getattr(user, "photo", None):
        return None
    try:
        with user.photo.open("rb") as source:
            image = Image.open(source)
            image = ImageOps.exif_transpose(image).convert("RGB")
            image = ImageOps.fit(image, (352, 388), method=Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, "JPEG", quality=88, optimize=True)
            output.seek(0)
            return ImageReader(output)
    except (OSError, ValueError):
        return None


def build_certificate_pdf(certificate):
    """Create a single-page PDF 1.4 using embedded fonts and standard JPEG images."""
    user = certificate.user
    subscription = certificate.subscription
    full_name = user.get_full_name() or user.get_username()
    member_type = subscription.plan.certificate_member_type
    font = _font_name()
    output = BytesIO()
    pdf = canvas.Canvas(
        output,
        pagesize=A4,
        pageCompression=1,
        pdfVersion=(1, 4),
        title=f"Membership Certificate {certificate.certificate_number}",
        author=settings.ORGANIZATION_NAME,
    )
    pdf.scale(A4[0] / DESIGN_WIDTH, A4[1] / DESIGN_HEIGHT)
    pdf.drawImage(_background_reader(), 0, 0, DESIGN_WIDTH, DESIGN_HEIGHT)

    photo = _photo_reader(user)
    if photo:
        pdf.drawImage(photo, 914, DESIGN_HEIGHT - 998 - 388, 352, 388, mask="auto")
    else:
        pdf.setFillColor("#ffffff")
        pdf.rect(914, DESIGN_HEIGHT - 998 - 388, 352, 388, fill=1, stroke=0)
        _draw_centered(pdf, (full_name[:1] or "M").upper(), 1245, 150, font, "#7b2435")

    _draw_centered(pdf, full_name, 1550, 58, font)
    address_lines = _wrap(_member_address(user))
    address_size = 34 if len(address_lines) == 1 else 28
    start_y = 1625 - ((len(address_lines) - 1) * 38 // 2)
    for index, line in enumerate(address_lines):
        _draw_centered(pdf, line, start_y + index * 38, address_size, font)
    _draw_centered(pdf, member_type, 2048, 74, font)

    pdf.setFillColor("#5b1f0d")
    pdf.setFont(font, 18)
    metadata_y = DESIGN_HEIGHT - 1668
    pdf.drawString(150, metadata_y, f"Certificate: {certificate.certificate_number}")
    pdf.drawRightString(DESIGN_WIDTH - 150, metadata_y, f"Issued: {certificate.issued_at:%d %b %Y}")
    pdf.showPage()
    pdf.save()
    return output.getvalue()
