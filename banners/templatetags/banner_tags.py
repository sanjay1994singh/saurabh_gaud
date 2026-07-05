from django import template
from django.db.models import Q
from django.utils import timezone

from banners.models import Banner

register = template.Library()


BANNER_SLOT_INFO = {
    Banner.HEADER_TOP: {
        "label": "Header top banner",
        "size": "1200 x 180 px",
        "note": "wide horizontal image",
    },
    Banner.HOME_AFTER_HERO: {
        "label": "Home after hero banner",
        "size": "1200 x 250 px",
        "note": "large homepage horizontal image",
    },
    Banner.HOME_MIDDLE: {
        "label": "Home middle banner",
        "size": "1200 x 250 px",
        "note": "wide homepage ad image",
    },
    Banner.FOOTER_TOP: {
        "label": "Footer top banner",
        "size": "1200 x 180 px",
        "note": "wide horizontal image",
    },
    Banner.SIDEBAR: {
        "label": "Detail sidebar ad",
        "size": "300 x 250 px",
        "note": "compact sidebar ad image",
    },
}


@register.inclusion_tag("banners/banner_slot.html", takes_context=True)
def render_banner_slot(context, placement, limit=1):
    now = timezone.now()
    user = context.get("request").user if context.get("request") else None
    slot_info = BANNER_SLOT_INFO.get(
        placement,
        {
            "label": "Banner slot",
            "size": "1200 x 180 px",
            "note": "recommended banner image",
        },
    )
    banners = (
        Banner.objects.filter(is_active=True)
        .filter(Q(placement=placement) | Q(show_everywhere=True))
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        .order_by("-created_at", "display_order")[:limit]
    )
    return {
        "banners": banners,
        "placement": placement,
        "show_placeholder": bool(user and user.is_staff),
        "slot_info": slot_info,
    }
