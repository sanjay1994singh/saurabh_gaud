from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, RegisterForm
from subscriptions.models import MembershipSubscription
from subscriptions.views import delete_duplicate_active_plan_certificates


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "अकाउंट बन गया है. कृपया सदस्यता चुनें.")
            return redirect("subscriptions:plans")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


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
