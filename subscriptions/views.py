import base64
import mimetypes

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST

from .models import Certificate, MembershipSubscription, SubscriptionPlan
from .services import (
    RazorpayConfigurationError,
    RazorpayOrderError,
    create_razorpay_order,
    verify_payment_signature,
)


def plans(request):
    plan_list = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, "subscriptions/plans.html", {"plan_list": plan_list})


def delete_duplicate_active_plan_certificates(user, plan):
    now = timezone.now()
    active_subscriptions = list(
        MembershipSubscription.objects.filter(
            user=user,
            plan=plan,
            status=MembershipSubscription.ACTIVE,
        )
        .filter(Q(ends_at__gte=now) | Q(ends_at__isnull=True))
        .order_by("starts_at", "created_at", "pk")
    )

    if not active_subscriptions:
        return None, 0

    subscription_to_keep = active_subscriptions[0]
    Certificate.objects.get_or_create(user=user, subscription=subscription_to_keep)

    duplicate_subscriptions = active_subscriptions[1:]
    duplicate_count = len(duplicate_subscriptions)
    for subscription in duplicate_subscriptions:
        subscription.delete()

    return subscription_to_keep, duplicate_count


@login_required
def join(request, slug):
    plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)
    existing_subscription, duplicate_count = delete_duplicate_active_plan_certificates(request.user, plan)
    if existing_subscription:
        if duplicate_count:
            messages.info(
                request,
                f"आपकी {plan.name} सदस्यता पहले से सक्रिय है. Duplicate certificates हटा दिए गए.",
            )
        else:
            messages.info(request, f"आपकी {plan.name} सदस्यता पहले से सक्रिय है.")
        return redirect("accounts:profile")

    if plan.is_free:
        subscription = MembershipSubscription.objects.create(
            user=request.user,
            plan=plan,
            status=MembershipSubscription.PENDING,
        )
        subscription.activate()
        messages.success(request, "आपकी निशुल्क सदस्यता सक्रिय हो गई है. प्रमाणपत्र बन गया है.")
        return redirect("accounts:profile")

    subscription = MembershipSubscription.objects.create(
        user=request.user,
        plan=plan,
        status=MembershipSubscription.PENDING,
    )

    try:
        order = create_razorpay_order(
            amount_paise=plan.amount_paise,
            receipt=f"sub-{subscription.pk}",
            notes={"user_id": str(request.user.pk), "plan": plan.slug},
        )
    except (RazorpayConfigurationError, RazorpayOrderError) as exc:
        subscription.status = MembershipSubscription.FAILED
        subscription.save(update_fields=("status", "updated_at"))
        messages.error(request, f"भुगतान शुरू नहीं हो सका: {exc}")
        return redirect("subscriptions:plans")

    subscription.razorpay_order_id = order["id"]
    subscription.save(update_fields=("razorpay_order_id", "updated_at"))

    return render(
        request,
        "subscriptions/checkout.html",
        {
            "plan": plan,
            "subscription": subscription,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": order["id"],
            "amount_paise": plan.amount_paise,
        },
    )


@require_POST
@login_required
def payment_success(request):
    order_id = request.POST.get("razorpay_order_id", "")
    payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")

    subscription = get_object_or_404(
        MembershipSubscription,
        user=request.user,
        razorpay_order_id=order_id,
        status=MembershipSubscription.PENDING,
    )

    if not verify_payment_signature(order_id=order_id, payment_id=payment_id, signature=signature):
        subscription.status = MembershipSubscription.FAILED
        subscription.save(update_fields=("status", "updated_at"))
        messages.error(request, "भुगतान सत्यापन असफल रहा. यदि पैसे कट गए हैं तो admin से संपर्क करें.")
        return redirect("subscriptions:plans")

    subscription.razorpay_payment_id = payment_id
    subscription.razorpay_signature = signature
    subscription.save(update_fields=("razorpay_payment_id", "razorpay_signature", "updated_at"))
    subscription.activate()
    delete_duplicate_active_plan_certificates(request.user, subscription.plan)
    messages.success(request, "भुगतान सफल रहा. आपकी सदस्यता और प्रमाणपत्र तैयार हैं.")
    return redirect("accounts:profile")


def get_member_photo_data_uri(user):
    if not getattr(user, "photo", None):
        return ""

    try:
        with user.photo.open("rb") as photo_file:
            encoded = base64.b64encode(photo_file.read()).decode("ascii")
    except OSError:
        return ""

    mime_type = mimetypes.guess_type(user.photo.name)[0] or "image/jpeg"
    return f"data:{mime_type};base64,{encoded}"


def get_certificate_background_data_uri():
    background_path = finders.find("certificate_background/Certificate.jpg")
    if not background_path:
        background_path = settings.BASE_DIR / "static" / "certificate_background" / "Certificate.jpg"

    try:
        with open(background_path, "rb") as background_file:
            encoded = base64.b64encode(background_file.read()).decode("ascii")
    except OSError:
        return ""

    return f"data:image/jpeg;base64,{encoded}"


def get_certificate_address(user):
    state_name = user.state_obj.name if user.state_obj_id else user.state
    country_name = user.country.name if user.country_id else ""
    raw_parts = (user.address, user.city, state_name, country_name)
    parts = []
    for part in raw_parts:
        value = str(part).strip() if part else ""
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts) or "N/A"


def wrap_certificate_text(text, limit=72):
    words = text.split()
    if not words:
        return ["N/A"]

    lines = []
    current = ""
    for word in words:
        next_line = f"{current} {word}".strip()
        if current and len(next_line) > limit:
            lines.append(current)
            current = word
        else:
            current = next_line

    if current:
        lines.append(current)
    return lines


def build_address_markup(address):
    lines = wrap_certificate_text(address)
    font_size = 34 if len(lines) == 1 else 28
    line_height = 38
    start_y = 1625 - ((len(lines) - 1) * line_height // 2)
    return "\n".join(
        f'  <text x="1104" y="{start_y + index * line_height}" text-anchor="middle" font-family="Arial, Noto Sans Devanagari, sans-serif" font-size="{font_size}" fill="#5b1f0d">{escape(line)}</text>'
        for index, line in enumerate(lines)
    )


def build_certificate_svg(certificate, photo_data_uri=""):
    subscription = certificate.subscription
    user = certificate.user
    full_name = user.get_full_name() or user.get_username()
    member_type = subscription.plan.name
    address_markup = build_address_markup(get_certificate_address(user))
    background_data_uri = get_certificate_background_data_uri()
    background_markup = (
        f'<image href="{background_data_uri}" x="0" y="0" width="2208" height="2989"/>'
        if background_data_uri
        else '<rect width="2208" height="2989" fill="#fff8c7"/>'
    )

    if photo_data_uri:
        photo_markup = f"""
  <clipPath id="memberPhotoClip"><rect x="914" y="998" width="352" height="388"/></clipPath>
  <image href="{photo_data_uri}" x="914" y="998" width="352" height="388" preserveAspectRatio="xMidYMid slice" clip-path="url(#memberPhotoClip)"/>"""
    else:
        initial = escape(full_name[:1].upper() or "M")
        photo_markup = f"""
  <rect x="914" y="998" width="352" height="388" fill="#ffffff"/>
  <text x="1090" y="1245" text-anchor="middle" font-family="Arial, sans-serif" font-size="150" fill="#7b2435" font-weight="700">{initial}</text>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="2208" height="2989" viewBox="0 0 2208 2989">
  {background_markup}
  {photo_markup}
  <text x="1104" y="1550" text-anchor="middle" font-family="Arial, Noto Sans Devanagari, sans-serif" font-size="58" fill="#5b1f0d" font-weight="700">{escape(full_name)}</text>
{address_markup}
  <text x="1104" y="2048" text-anchor="middle" font-family="Arial, Noto Sans Devanagari, sans-serif" font-size="74" fill="#5b1f0d" font-weight="700">{escape(member_type)}</text>
</svg>"""


@login_required
def certificate_detail(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk, user=request.user)
    subscription = certificate.subscription
    if not subscription.is_active:
        raise Http404("प्रमाणपत्र केवल सक्रिय सदस्यता के लिए उपलब्ध है.")

    return render(
        request,
        "subscriptions/certificate_detail.html",
        {
            "certificate": certificate,
            "subscription": subscription,
            "certificate_svg": build_certificate_svg(certificate, get_member_photo_data_uri(request.user)),
        },
    )


@login_required
def certificate_download(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk, user=request.user)
    subscription = certificate.subscription
    if not subscription.is_active:
        raise Http404("प्रमाणपत्र केवल सक्रिय सदस्यता के लिए उपलब्ध है.")

    svg = build_certificate_svg(certificate, get_member_photo_data_uri(request.user))
    response = HttpResponse(svg, content_type="image/svg+xml")
    response["Content-Disposition"] = f'attachment; filename="{certificate.certificate_number}.svg"'
    return response
