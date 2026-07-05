from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Event


def index(request):
    today = timezone.localdate()
    events = Event.objects.filter(is_active=True)
    featured_events = events.filter(is_featured=True)[:3]
    permanent_events = events.filter(is_permanent=True)
    dated_events = events.filter(is_permanent=False, start_date__isnull=False)
    present_events = dated_events.filter(Q(end_date__isnull=True, start_date__gte=today) | Q(end_date__gte=today))
    past_events = dated_events.exclude(pk__in=present_events.values("pk"))

    return render(
        request,
        "events/index.html",
        {
            "featured_events": featured_events,
            "permanent_events": permanent_events,
            "present_events": present_events.distinct(),
            "past_events": past_events.distinct(),
        },
    )


def detail(request, pk):
    event = get_object_or_404(Event, pk=pk, is_active=True)
    return render(request, "events/detail.html", {"event": event})
