from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from hamare_stambh.models import HamareStambh
from patrika.models import Patrika
from seva_prakalp.models import SevaPrakalp
from subscriptions.models import MembershipSubscription

from .language import LANGUAGE_COOKIE_NAME, LANGUAGE_SESSION_KEY, SUPPORTED_LANGUAGES


SERVICE_ICON_ORDER = ("cow", "education", "health", "environment", "women", "relief")


def get_service_icon_key(prakalp, index):
    text = f"{prakalp.name} {prakalp.short_description} {prakalp.content}".lower()
    icon_matches = (
        ("cow", ("गौ", "गो ", "cow", "gaushala", "गौशाला")),
        ("education", ("शिक्षा", "संस्कार", "education", "school", "student")),
        ("health", ("स्वास्थ्य", "चिकित्सा", "health", "medical", "clinic")),
        ("environment", ("पर्यावरण", "वृक्ष", "जल", "environment", "tree", "plant")),
        ("women", ("महिला", "नारी", "women", "woman")),
        ("relief", ("आपदा", "राहत", "relief", "help", "सहायता")),
    )
    for key, words in icon_matches:
        if any(word in text for word in words):
            return key
    return SERVICE_ICON_ORDER[index % len(SERVICE_ICON_ORDER)]


def get_home_message_stambh(stambh_queryset):
    president_match = stambh_queryset.filter(
        Q(name__icontains="saurabh")
        | Q(name__icontains="gaur")
        | Q(name__icontains="gaud")
        | Q(name__icontains="सौरभ")
        | Q(name__icontains="गौड़")
        | Q(designation__icontains="राष्ट्रीय अध्यक्ष")
        | Q(designation__icontains="national president")
    ).first()
    return president_match or stambh_queryset.filter(is_featured=True).first() or stambh_queryset.first()


def index(request):
    today = timezone.localdate()
    seva_prakalps = SevaPrakalp.objects.filter(is_active=True)
    featured_prakalp = seva_prakalps.filter(is_featured=True).first() or seva_prakalps.first()
    prakalp_count = seva_prakalps.count()
    home_prakalps = seva_prakalps[:6]
    hamare_stambh = HamareStambh.objects.filter(is_active=True)
    featured_stambh = get_home_message_stambh(hamare_stambh)
    stambh_list = hamare_stambh[:4]
    patrikas = Patrika.objects.filter(is_active=True)
    featured_patrika = patrikas.filter(is_featured=True).first() or patrikas.first()
    events = Event.objects.filter(is_active=True)
    upcoming_events = (
        events.filter(
            Q(is_permanent=True)
            | Q(start_date__gte=today)
            | Q(end_date__gte=today)
        )
        .distinct()[:3]
    )
    latest_events = events[:4]
    latest_updates = list(upcoming_events) or list(latest_events)
    active_members = MembershipSubscription.objects.filter(status=MembershipSubscription.ACTIVE).values("user_id").distinct().count()
    member_count = max(active_members, get_user_model().objects.filter(is_active=True).count())
    service_tiles = [
        {
            "prakalp": prakalp,
            "icon_key": get_service_icon_key(prakalp, index),
        }
        for index, prakalp in enumerate(home_prakalps)
    ]

    return render(
        request,
        "home/index.html",
        {
            "site_name": settings.SITE_NAME,
            "featured_prakalp": featured_prakalp,
            "prakalp_count": prakalp_count,
            "seva_prakalps": home_prakalps,
            "service_tiles": service_tiles,
            "hamare_stambh": stambh_list,
            "featured_stambh": featured_stambh,
            "featured_patrika": featured_patrika,
            "latest_updates": latest_updates,
            "stats": {
                "prakalp": prakalp_count,
                "events": events.count(),
                "members": member_count,
                "stambh": hamare_stambh.count(),
                "patrika": patrikas.count(),
            },
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
