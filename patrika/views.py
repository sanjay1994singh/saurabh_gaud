from django.shortcuts import get_object_or_404, render

from .models import Patrika


def index(request):
    patrikas = Patrika.objects.filter(is_active=True)
    featured_patrika = patrikas.filter(is_featured=True).first() or patrikas.first()
    return render(
        request,
        "patrika/index.html",
        {
            "patrikas": patrikas,
            "featured_patrika": featured_patrika,
        },
    )


def detail(request, pk):
    patrika = get_object_or_404(Patrika, pk=pk, is_active=True)
    more_patrikas = Patrika.objects.filter(is_active=True).exclude(pk=patrika.pk)[:4]
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
        },
    )
