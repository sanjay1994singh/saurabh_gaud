from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse

from hamare_stambh.models import HamareStambh
from patrika.models import Patrika
from seva_prakalp.models import SevaPrakalp

from .language import LANGUAGE_COOKIE_NAME, LANGUAGE_SESSION_KEY, SUPPORTED_LANGUAGES


def index(request):
    seva_prakalps = SevaPrakalp.objects.filter(is_active=True)
    featured_prakalp = seva_prakalps.filter(is_featured=True).first() or seva_prakalps.first()
    prakalp_count = seva_prakalps.count()
    hamare_stambh = HamareStambh.objects.filter(is_active=True)[:4]
    patrikas = Patrika.objects.filter(is_active=True)
    featured_patrika = patrikas.filter(is_featured=True).first() or patrikas.first()

    return render(
        request,
        "home/index.html",
        {
            "site_name": settings.SITE_NAME,
            "featured_prakalp": featured_prakalp,
            "prakalp_count": prakalp_count,
            "seva_prakalps": seva_prakalps,
            "hamare_stambh": hamare_stambh,
            "featured_patrika": featured_patrika,
        },
    )


def about(request):
    return render(request, "home/about.html", {"site_name": settings.SITE_NAME})


def donate(request):
    return render(request, "home/donate.html", {"site_name": settings.SITE_NAME})


def contact(request):
    return render(request, "home/contact.html", {"site_name": settings.SITE_NAME})


def set_language(request):
    language = request.POST.get("language") or request.GET.get("language")
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("home:index")
    response = redirect(next_url)
    if language in SUPPORTED_LANGUAGES:
        request.session[LANGUAGE_SESSION_KEY] = language
        response.set_cookie(LANGUAGE_COOKIE_NAME, language, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response
