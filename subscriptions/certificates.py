from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


DESIGN_WIDTH = 2208
DESIGN_HEIGHT = 2989


def _font_path():
    return Path(settings.BASE_DIR) / "static" / "fonts" / "NotoSansDevanagari-Variable.ttf"


def _image_font(size):
    return ImageFont.truetype(str(_font_path()), size=size)


def _background_path():
    return finders.find("certificate_background/Certificate.jpg") or str(
        Path(settings.BASE_DIR) / "static" / "certificate_background" / "Certificate.jpg"
    )


def _background_image():
    with Image.open(_background_path()) as source:
        return ImageOps.exif_transpose(source).convert("RGB").resize(
            (DESIGN_WIDTH, DESIGN_HEIGHT),
            Image.Resampling.LANCZOS,
        )


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


def _photo_image(user):
    if not getattr(user, "photo", None):
        return None
    try:
        with user.photo.open("rb") as source:
            image = Image.open(source)
            image = ImageOps.exif_transpose(image).convert("RGB")
            return ImageOps.fit(image, (352, 388), method=Image.Resampling.LANCZOS)
    except (OSError, ValueError):
        return None


def _draw_image_centered(draw, text, y, size, color="#5b1f0d"):
    font = _image_font(size)
    draw.text(
        (DESIGN_WIDTH / 2, y),
        str(text),
        anchor="mt",
        align="center",
        fill=color,
        font=font,
    )


def _certificate_image(certificate):
    user = certificate.user
    subscription = certificate.subscription
    full_name = user.get_full_name() or user.get_username()
    member_type = subscription.plan.certificate_member_type

    image = _background_image()
    photo = _photo_image(user)
    if photo:
        image.paste(photo, (914, 998))
    else:
        draw = ImageDraw.Draw(image)
        draw.rectangle((914, 998, 1266, 1386), fill="#ffffff")
        _draw_image_centered(draw, (full_name[:1] or "M").upper(), 1170, 150, "#7b2435")

    draw = ImageDraw.Draw(image)
    _draw_image_centered(draw, full_name, 1518, 58)

    address_lines = _wrap(_member_address(user))
    address_size = 34 if len(address_lines) == 1 else 28
    start_y = 1598 - ((len(address_lines) - 1) * 38 // 2)
    for index, line in enumerate(address_lines):
        _draw_image_centered(draw, line, start_y + index * 38, address_size)

    _draw_image_centered(draw, member_type, 2006, 74)
    return image


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
    certificate_image = _certificate_image(certificate)
    image_output = BytesIO()
    certificate_image.save(image_output, "JPEG", quality=92, optimize=True, progressive=False)
    image_output.seek(0)
    pdf.drawImage(ImageReader(image_output), 0, 0, A4[0], A4[1])
    pdf.showPage()
    pdf.save()
    return output.getvalue()
