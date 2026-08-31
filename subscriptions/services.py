import base64
import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class RazorpayConfigurationError(RuntimeError):
    pass


class RazorpayOrderError(RuntimeError):
    pass


class RazorpayPaymentError(RuntimeError):
    pass


def get_razorpay_credentials():
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        raise RazorpayConfigurationError("Razorpay keys are not configured.")
    return key_id, key_secret


def razorpay_request(path, *, method="GET", payload=None):
    key_id, key_secret = get_razorpay_credentials()
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    token = base64.b64encode(f"{key_id}:{key_secret}".encode("utf-8")).decode("ascii")
    request = Request(
        f"https://api.razorpay.com/v1/{path.lstrip('/')}",
        data=data,
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RazorpayPaymentError(detail or str(exc)) from exc
    except (URLError, TimeoutError) as exc:
        raise RazorpayPaymentError(str(exc)) from exc


def create_razorpay_order(*, amount_paise, receipt, notes=None):
    if amount_paise <= 0:
        raise RazorpayOrderError("Razorpay order amount must be greater than zero.")
    if not receipt:
        raise RazorpayOrderError("Razorpay order receipt is required.")

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt[:40],
        "payment_capture": 1,
        "notes": notes or {},
    }
    try:
        order = razorpay_request("orders", method="POST", payload=payload)
    except RazorpayPaymentError as exc:
        raise RazorpayOrderError(str(exc)) from exc

    if not order.get("id") or order.get("amount") != amount_paise or order.get("currency") != "INR":
        raise RazorpayOrderError("Razorpay returned an invalid order response.")
    return order


def fetch_razorpay_payment(payment_id):
    if not payment_id:
        raise RazorpayPaymentError("Missing Razorpay payment ID.")
    return razorpay_request(f"payments/{payment_id}")


def verify_payment_signature(*, order_id, payment_id, signature):
    _, key_secret = get_razorpay_credentials()
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(key_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def verify_webhook_signature(*, body, signature):
    webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "")
    if not webhook_secret or not signature:
        return False
    expected = hmac.new(webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
