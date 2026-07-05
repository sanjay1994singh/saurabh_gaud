from hashlib import sha1
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from .models import PatrikaPage


def pdf_digest(pdf_path):
    digest = sha1()
    with pdf_path.open("rb") as pdf_file:
        for chunk in iter(lambda: pdf_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def delete_page_files(patrika):
    for page in patrika.pages.all():
        if page.image and default_storage.exists(page.image.name):
            default_storage.delete(page.image.name)
    patrika.pages.all().delete()


def convert_patrika_pdf_to_pages(patrika, zoom=2):
    import fitz

    delete_page_files(patrika)

    pdf_path = Path(patrika.pdf.path)
    version = pdf_digest(pdf_path)
    document = fitz.open(pdf_path)
    matrix = fitz.Matrix(zoom, zoom)

    try:
        for index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_name = f"patrika-{patrika.pk}-{version}-page-{index:02d}.png"
            page_image = ContentFile(pixmap.tobytes("png"), name=image_name)
            PatrikaPage.objects.create(
                patrika=patrika,
                number=index,
                image=page_image,
            )
    finally:
        document.close()

    return patrika.pages.count()
