import secrets
import string

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ProfileForm, RegisterForm
from .location_data import hindi_state_name
from .models import State
from subscriptions.models import Invoice, MembershipSubscription
from subscriptions.notifications import send_account_welcome_email, send_profile_updated_email
from subscriptions.views import delete_duplicate_active_plan_certificates

def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return ""


def _is_membership_join_url(next_url):
    return next_url.startswith("/subscriptions/join/")


def _generate_initial_password(length=20):
    """Return a cryptographically strong password with mixed character classes."""
    alphabet = string.ascii_letters + string.digits + "@#$%*-_!"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in "@#$%*-_!" for char in password)
        ):
            return password


def register(request):
    next_url = _safe_next_url(request)
    is_membership_join = _is_membership_join_url(next_url)

    if request.user.is_authenticated:
        if next_url:
            return redirect(next_url)
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            initial_password = _generate_initial_password()
            user = form.save(commit=False)
            user.set_password(initial_password)
            user.save()
            login(request, user, backend="accounts.backends.EmailPhoneUsernameBackend")
            transaction.on_commit(
                lambda: send_account_welcome_email(user, initial_password=initial_password)
            )
            messages.success(request, "अकाउंट बन गया है. कृपया सदस्यता चुनें.")
            if next_url:
                return redirect(next_url)
            return redirect("subscriptions:plans")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
            "next_url": next_url,
            "is_membership_join": is_membership_join,
        },
    )


def states_for_country(request):
    country_id = request.GET.get("country")
    states = State.objects.filter(country_id=country_id, is_active=True).order_by("name")
    return JsonResponse({
        "states": [
            {"id": state.id, "name": hindi_state_name(state.name)}
            for state in states
        ]
    })


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
            user = form.save()
            transaction.on_commit(lambda: send_profile_updated_email(user))
            messages.success(request, "प्रोफाइल अपडेट हो गई.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    memberships = request.user.memberships.select_related("plan", "certificate")
    certificates = request.user.certificates.select_related("subscription__plan")
    invoices = Invoice.objects.filter(payment__subscription__user=request.user).select_related("payment")
    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "memberships": memberships,
            "certificates": certificates,
            "invoices": invoices,
        },
    )
