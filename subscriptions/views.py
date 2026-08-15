import base64
import json
import mimetypes

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .invoices import build_invoice_pdf
from .certificates import build_certificate_pdf
from .models import Certificate, Invoice, MembershipSubscription, PaymentTransaction, SubscriptionPlan
from .notifications import send_membership_payment_email, send_payment_failed_email
from .services import (
    RazorpayConfigurationError,
    RazorpayOrderError,
    RazorpayPaymentError,
    create_razorpay_order,
    fetch_razorpay_payment,
    verify_payment_signature,
    verify_webhook_signature,
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
    PaymentTransaction.objects.create(
        subscription=subscription,
        user_name=request.user.get_full_name() or request.user.get_username(),
        user_email=request.user.email,
        user_phone=request.user.phone,
        user_address=get_certificate_address(request.user),
        plan_name=plan.name,
        amount_paise=plan.amount_paise,
        currency="INR",
        razorpay_order_id=order["id"],
        gateway_status=order.get("status", "created"),
        gateway_response=order,
    )

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
def _legacy_payment_success(request):
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


@require_POST
@login_required
def payment_success(request):
    order_id = request.POST.get("razorpay_order_id", "")
    payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")
    if not order_id or not payment_id or not signature:
        messages.error(request, "Payment response is incomplete. Please try again.")
        return redirect("subscriptions:plans")

    with transaction.atomic():
        subscription = get_object_or_404(
            MembershipSubscription.objects.select_for_update().select_related("plan"),
            user=request.user,
            razorpay_order_id=order_id,
        )
        payment_record = get_object_or_404(PaymentTransaction, subscription=subscription)

        if subscription.status == MembershipSubscription.ACTIVE:
            messages.success(request, "Payment was already verified and your membership is active.")
            return redirect("accounts:profile")

        if not verify_payment_signature(order_id=order_id, payment_id=payment_id, signature=signature):
            subscription.status = MembershipSubscription.FAILED
            subscription.save(update_fields=("status", "updated_at"))
            payment_record.status = PaymentTransaction.FAILED
            payment_record.failure_reason = "Razorpay signature verification failed."
            payment_record.save(update_fields=("status", "failure_reason", "updated_at"))
            messages.error(request, "Payment verification failed. If money was deducted, please contact admin.")
            return redirect("subscriptions:plans")

        try:
            gateway_payment = fetch_razorpay_payment(payment_id)
        except (RazorpayConfigurationError, RazorpayPaymentError) as exc:
            payment_record.failure_reason = f"Payment status check failed: {exc}"
            payment_record.save(update_fields=("failure_reason", "updated_at"))
            messages.error(request, "Payment status could not be confirmed. Please contact admin.")
            return redirect("subscriptions:plans")

        payment_matches = (
            gateway_payment.get("order_id") == order_id
            and gateway_payment.get("amount") == payment_record.amount_paise
            and gateway_payment.get("currency") == payment_record.currency
            and gateway_payment.get("status") == "captured"
        )
        if not payment_matches:
            subscription.status = MembershipSubscription.FAILED
            subscription.save(update_fields=("status", "updated_at"))
            payment_record.status = PaymentTransaction.FAILED
            payment_record.razorpay_payment_id = payment_id
            payment_record.razorpay_signature = signature
            payment_record.gateway_status = gateway_payment.get("status", "unknown")
            payment_record.failure_reason = "Gateway payment details did not match the membership order."
            payment_record.gateway_response = gateway_payment
            payment_record.save()
            messages.error(request, "Payment details did not match this membership order. Please contact admin.")
            return redirect("subscriptions:plans")

        subscription.razorpay_payment_id = payment_id
        subscription.razorpay_signature = signature
        subscription.save(update_fields=("razorpay_payment_id", "razorpay_signature", "updated_at"))
        subscription.activate()
        payment_record.status = PaymentTransaction.PAID
        payment_record.razorpay_payment_id = payment_id
        payment_record.razorpay_signature = signature
        payment_record.gateway_status = gateway_payment["status"]
        payment_record.gateway_response = gateway_payment
        payment_record.paid_at = timezone.now()
        payment_record.failure_reason = ""
        payment_record.save()
        invoice = Invoice.issue_for_payment(payment_record)
        transaction.on_commit(lambda: send_membership_payment_email(invoice))

    delete_duplicate_active_plan_certificates(request.user, subscription.plan)
    messages.success(request, "Payment successful. Your membership and certificate are ready.")
    return redirect("accounts:profile")


@require_POST
@login_required
def payment_failed(request):
    order_id = request.POST.get("razorpay_order_id", "")
    subscription = get_object_or_404(
        MembershipSubscription,
        user=request.user,
        razorpay_order_id=order_id,
        status=MembershipSubscription.PENDING,
    )
    payment_record = get_object_or_404(PaymentTransaction, subscription=subscription)
    payment_record.status = PaymentTransaction.FAILED
    payment_record.gateway_status = "failed"
    payment_record.failure_reason = request.POST.get(
        "error_description", "Payment failed in Razorpay checkout."
    )[:2000]
    payment_record.save(update_fields=("status", "gateway_status", "failure_reason", "updated_at"))
    subscription.status = MembershipSubscription.FAILED
    subscription.save(update_fields=("status", "updated_at"))
    transaction.on_commit(lambda: send_payment_failed_email(payment_record))
    return HttpResponse(status=204)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not verify_webhook_signature(body=request.body, signature=signature):
        return HttpResponseForbidden("Invalid webhook signature")
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid JSON")

    event = payload.get("event", "")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id", "")
    payment_id = payment_entity.get("id", "")
    if not order_id:
        return HttpResponse(status=204)

    try:
        payment_record = PaymentTransaction.objects.select_related("subscription__plan").get(
            razorpay_order_id=order_id
        )
    except PaymentTransaction.DoesNotExist:
        return HttpResponse(status=204)

    if event == "payment.failed":
        if payment_record.status != PaymentTransaction.PAID:
            payment_record.status = PaymentTransaction.FAILED
            payment_record.gateway_status = "failed"
            payment_record.razorpay_payment_id = payment_id
            payment_record.failure_reason = payment_entity.get("error_description") or "Razorpay reported payment failure."
            payment_record.gateway_response = payment_entity
            payment_record.save()
            subscription = payment_record.subscription
            subscription.status = MembershipSubscription.FAILED
            subscription.save(update_fields=("status", "updated_at"))
            transaction.on_commit(lambda: send_payment_failed_email(payment_record))
        return HttpResponse(status=204)

    if event != "payment.captured" or payment_record.status == PaymentTransaction.PAID:
        return HttpResponse(status=204)
    payment_matches = (
        payment_entity.get("amount") == payment_record.amount_paise
        and payment_entity.get("currency") == payment_record.currency
        and payment_entity.get("status") == "captured"
    )
    if not payment_matches:
        return HttpResponseBadRequest("Payment details do not match order")

    with transaction.atomic():
        payment_record = PaymentTransaction.objects.select_for_update().select_related("subscription__plan").get(pk=payment_record.pk)
        if payment_record.status == PaymentTransaction.PAID:
            return HttpResponse(status=204)
        subscription = payment_record.subscription
        subscription.razorpay_payment_id = payment_id
        subscription.save(update_fields=("razorpay_payment_id", "updated_at"))
        subscription.activate()
        payment_record.status = PaymentTransaction.PAID
        payment_record.razorpay_payment_id = payment_id
        payment_record.gateway_status = "captured"
        payment_record.gateway_response = payment_entity
        payment_record.paid_at = timezone.now()
        payment_record.failure_reason = ""
        payment_record.save()
        invoice = Invoice.issue_for_payment(payment_record)
        transaction.on_commit(lambda: send_membership_payment_email(invoice))
    return HttpResponse(status=204)


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("payment__subscription__user"),
        pk=pk,
        payment__subscription__user=request.user,
    )
    return render(request, "subscriptions/invoice_detail.html", {"invoice": invoice})


@login_required
def invoice_download(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("payment__subscription__user"),
        pk=pk,
        payment__subscription__user=request.user,
    )
    response = HttpResponse(build_invoice_pdf(invoice), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response


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
    start_y = 1603 - ((len(lines) - 1) * line_height // 2)
    return "\n".join(
        f'  <text x="1104" y="{start_y + index * line_height}" text-anchor="middle" font-family="Arial, Noto Sans Devanagari, sans-serif" font-size="{font_size}" fill="#5b1f0d">{escape(line)}</text>'
        for index, line in enumerate(lines)
    )


def build_certificate_svg(certificate, photo_data_uri=""):
    subscription = certificate.subscription
    user = certificate.user
    full_name = user.get_full_name() or user.get_username()
    member_type = subscription.plan.certificate_member_type
    address_markup = build_address_markup(get_certificate_address(user))
    background_data_uri = get_certificate_background_data_uri()
    background_markup = (
        f'<image href="{background_data_uri}" x="0" y="0" width="2208" height="2989"/>'
        if background_data_uri
        else '<rect width="2208" height="2989" fill="#fff8c7"/>'
    )

    if photo_data_uri:
        photo_markup = f"""
  <defs>
    <mask id="memberPhotoMask" maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse">
      <rect width="2208" height="2989" fill="black"/>
      <rect x="914" y="998" width="352" height="388" rx="22" ry="22" fill="white"/>
    </mask>
  </defs>
  <image href="{photo_data_uri}" x="914" y="1018" width="352" height="388" preserveAspectRatio="xMidYMid slice" mask="url(#memberPhotoMask)"/>"""
    else:
        initial = escape(full_name[:1].upper() or "M")
        photo_markup = f"""
  <rect x="914" y="998" width="352" height="388" fill="#ffffff"/>
  <text x="1090" y="1245" text-anchor="middle" font-family="Arial, sans-serif" font-size="150" fill="#7b2435" font-weight="700">{initial}</text>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2208 2989" preserveAspectRatio="xMidYMid meet" style="display:block;width:100%;max-width:2208px;height:auto;background:#fff8c7;">
  {background_markup}
  {photo_markup}
  <text x="1104" y="1528" text-anchor="middle" font-family="Arial, Noto Sans Devanagari, sans-serif" font-size="58" fill="#5b1f0d" font-weight="700">{escape(full_name)}</text>
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

    response = HttpResponse(build_certificate_pdf(certificate), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{certificate.certificate_number}.pdf"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
