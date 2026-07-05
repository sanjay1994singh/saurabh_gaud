from django.shortcuts import get_object_or_404, redirect, render

from .models import Patrika
from .services import convert_patrika_pdf_to_pages


def index(request):
    patrikas = Patrika.objects.filter(is_active=True)
    featured_patrika = patrikas.filter(is_featured=True).first() or patrikas.first()
    if featured_patrika:
        return redirect(featured_patrika.get_absolute_url())

    return render(
        request,
        "patrika/index.html",
        {
            "patrikas": patrikas,
            "featured_patrika": featured_patrika,
        },
    )


def archive(request):
    return redirect("patrika:index")


def detail(request, pk):
    patrika = get_object_or_404(Patrika, pk=pk, is_active=True)
    more_patrikas = Patrika.objects.filter(is_active=True).exclude(pk=patrika.pk)[:4]
    yearly_patrikas = Patrika.objects.filter(
        is_active=True,
        published_date__isnull=False,
    )
    year_options_by_year = {}
    for item in yearly_patrikas:
        year = str(item.published_date.year)
        year_options_by_year.setdefault(year, {
            "year": year,
            "title": item.title,
            "url": item.get_absolute_url(),
        })
    year_options = sorted(
        year_options_by_year.values(),
        key=lambda option: option["year"],
        reverse=True,
    )
    conversion_error = ""

    if not patrika.pages.exists() and patrika.pdf:
        try:
            convert_patrika_pdf_to_pages(patrika)
        except Exception as error:
            conversion_error = str(error)

    page_records = list(patrika.pages.all())
    pages = [
        {
            "number": page.number,
            "title": f"Page {page.number:02d}",
            "image": page.image.url,
        }
        for page in page_records
    ]
    return render(
        request,
        "patrika/detail.html",
        {
            "patrika": patrika,
            "more_patrikas": more_patrikas,
            "pages": pages,
            "initial_page": pages[0] if pages else None,
            "current_year": patrika.published_date.year if patrika.published_date else "",
            "year_options": year_options,
            "conversion_error": conversion_error,
        },
    )
