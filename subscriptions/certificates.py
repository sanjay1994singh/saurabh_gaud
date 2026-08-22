from io import BytesIO
from html import escape
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
import fitz
from PIL import Image, ImageDraw, ImageOps
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


DESIGN_WIDTH = 1135
DESIGN_HEIGHT = 1600


def _font_path():
    return Path(settings.BASE_DIR) / "static" / "fonts" / "NotoSansDevanagari-Variable.ttf"


def _background_path():
    return finders.find("certificate_background/Certificate.jpg") or str(
        Path(settings.BASE_DIR) / "static" / "certificate_background" / "Certificate.jpg"
    )


def _jpeg_bytes(image, quality=92):
    output = BytesIO()
    image.save(output, "JPEG", quality=quality, optimize=True, progressive=False)
    return output.getvalue()


def _png_bytes(image):
    output = BytesIO()
    image.save(output, "PNG", optimize=True)
    return output.getvalue()


def _background_bytes():
    with Image.open(_background_path()) as source:
        image = ImageOps.exif_transpose(source).convert("RGB").resize(
            (DESIGN_WIDTH, DESIGN_HEIGHT),
            Image.Resampling.LANCZOS,
        )
        return _jpeg_bytes(image, quality=92)


def _member_address(user):
    state_name = user.state_obj.name if user.state_obj_id else user.state
    country_name = user.country.name if user.country_id else ""
    parts = []
    for part in (user.address, user.city, user.district, state_name, user.pin_code, country_name):
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


def _photo_image(user):
    if not getattr(user, "photo", None):
        return None
    try:
        with user.photo.open("rb") as source:
            image = Image.open(source)
            image = ImageOps.exif_transpose(image).convert("RGB")
            return ImageOps.fit(image, (210, 230), method=Image.Resampling.LANCZOS)
    except (OSError, ValueError):
        return None


def _framed_photo_image(image, radius=10):
    framed = Image.new("RGBA", (210, 230), (255, 255, 255, 0))
    framed.paste(image.convert("RGBA"), (0, 0))
    mask = Image.new("L", framed.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, framed.width, framed.height), radius=radius, fill=255)
    framed.putalpha(mask)
    return framed


def _insert_html(page, text, rect, size, color="#5b1f0d", weight=700, align="center"):
    font_dir = _font_path().parent
    css = f"""
@font-face {{
  font-family: DRSDevanagari;
  src: url("{_font_path().name}");
}}
body {{
  margin: 0;
  padding: 0;
}}
.text {{
  color: {color};
  font-family: DRSDevanagari, "Noto Sans Devanagari", sans-serif;
  font-size: {size}px;
  font-weight: {weight};
  line-height: 1.15;
  text-align: {align};
}}
"""
    html = f'<div class="text">{escape(str(text))}</div>'
    archive = fitz.Archive(str(font_dir))
    page.insert_htmlbox(rect, html, css=css, archive=archive)


def _insert_centered_html(page, text, y, width, height, size, color="#5b1f0d", weight=700):
    rect = fitz.Rect((DESIGN_WIDTH - width) / 2, y, (DESIGN_WIDTH + width) / 2, y + height)
    _insert_html(page, text, rect, size, color, weight)


def _issue_date(certificate):
    issued_at = certificate.issued_at
    if hasattr(issued_at, "day"):
        return f"{issued_at.day}-{issued_at.month}-{issued_at.year}"
    return ""


def _member_number(certificate):
    return str(certificate.pk or certificate.user_id or "")


def _certificate_page_pixmap(certificate):
    user = certificate.user
    subscription = certificate.subscription
    full_name = user.get_full_name() or user.get_username()
    member_type = subscription.plan.certificate_member_type

    document = fitz.open()
    page = document.new_page(width=DESIGN_WIDTH, height=DESIGN_HEIGHT)
    page.insert_image(page.rect, stream=_background_bytes())

    _insert_html(page, _member_number(certificate), fitz.Rect(64, 503, 190, 545), 27, "#5b1f0d", 600)
    _insert_html(page, _issue_date(certificate), fitz.Rect(918, 503, 1078, 545), 27, "#5b1f0d", 600)

    photo = _photo_image(user)
    if photo:
        page.insert_image(fitz.Rect(463, 497, 673, 727), stream=_png_bytes(_framed_photo_image(photo)))
    else:
        _insert_centered_html(page, (full_name[:1] or "M").upper(), 575, 200, 90, 72, "#7b2435")

    _insert_centered_html(page, full_name, 760, 780, 60, 40, "#111111", 700)

    address_lines = _wrap(_member_address(user))
    address_size = 30 if len(address_lines) <= 2 else 26
    start_y = 823 - ((len(address_lines) - 1) * 34 // 2)
    for index, line in enumerate(address_lines):
        _insert_centered_html(page, line, start_y + index * 34, 790, 42, address_size, "#111111", 650)

    _insert_centered_html(page, member_type, 1052, 650, 58, 34, "#111111", 700)
    return page.get_pixmap(alpha=False)


def build_certificate_pdf(certificate):
    """Create a single-page PDF 1.4 from a rendered certificate image.

    Dynamic Hindi text is rasterized before it is added to the PDF so mobile
    PDF viewers do not break Devanagari shaping.
    """
    output = BytesIO()
    pdf = canvas.Canvas(
        output,
        pagesize=A4,
        pageCompression=1,
        pdfVersion=(1, 4),
        title=f"Membership Certificate {certificate.certificate_number}",
        author=settings.ORGANIZATION_NAME,
    )
    pixmap = _certificate_page_pixmap(certificate)
    image_output = BytesIO(pixmap.tobytes("png"))
    pdf.drawImage(ImageReader(image_output), 0, 0, A4[0], A4[1])
    pdf.showPage()
    pdf.save()
    return output.getvalue()
