from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ProfileForm, RegisterForm
from .models import State
from subscriptions.models import MembershipSubscription
from subscriptions.views import delete_duplicate_active_plan_certificates


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return ""


def register(request):
    next_url = _safe_next_url(request)

    if request.user.is_authenticated:
        if next_url:
            return redirect(next_url)
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "अकाउंट बन गया है. कृपया सदस्यता चुनें.")
            if next_url:
                return redirect(next_url)
            return redirect("subscriptions:plans")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form, "next_url": next_url})


def states_for_country(request):
    country_id = request.GET.get("country")
    states = State.objects.filter(country_id=country_id, is_active=True).values("id", "name").order_by("name")
    return JsonResponse({"states": list(states)})


@login_required
def profile(request):
    active_plan_ids = (
        request.user.memberships.filter(status=MembershipSubscription.ACTIVE)
        .values_list("plan_id", flat=True)
        .distinct()
    )
    for plan_id in active_plan_ids:
        membership = request.user.memberships.filter(plan_id=plan_id).select_related("plan").first()
        if membership:
            delete_duplicate_active_plan_certificates(request.user, membership.plan)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "प्रोफाइल अपडेट हो गई.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    memberships = request.user.memberships.select_related("plan", "certificate")
    certificates = request.user.certificates.select_related("subscription__plan")
    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "memberships": memberships,
            "certificates": certificates,
        },
    )
