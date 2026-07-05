from django.conf import settings
from django.shortcuts import render

from hamare_stambh.models import HamareStambh
from seva_prakalp.models import SevaPrakalp


def index(request):
    seva_prakalps = SevaPrakalp.objects.filter(is_active=True)
    featured_prakalp = seva_prakalps.filter(is_featured=True).first() or seva_prakalps.first()
    prakalp_count = seva_prakalps.count()
    hamare_stambh = HamareStambh.objects.filter(is_active=True)[:4]

    return render(
        request,
        "home/index.html",
        {
            "site_name": settings.SITE_NAME,
            "featured_prakalp": featured_prakalp,
            "prakalp_count": prakalp_count,
            "seva_prakalps": seva_prakalps,
            "hamare_stambh": hamare_stambh,
        },
    )


def about(request):
    return render(request, "home/about.html", {"site_name": settings.SITE_NAME})


def donate(request):
    return render(request, "home/donate.html", {"site_name": settings.SITE_NAME})


def contact(request):
    return render(request, "home/contact.html", {"site_name": settings.SITE_NAME})
