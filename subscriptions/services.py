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


def get_razorpay_credentials():
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        raise RazorpayConfigurationError("Razorpay keys are not configured.")
    return key_id, key_secret


def create_razorpay_order(*, amount_paise, receipt, notes=None):
    key_id, key_secret = get_razorpay_credentials()
    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt[:40],
        "payment_capture": 1,
        "notes": notes or {},
    }
    token = base64.b64encode(f"{key_id}:{key_secret}".encode("utf-8")).decode("ascii")
    request = Request(
        "https://api.razorpay.com/v1/orders",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RazorpayOrderError(detail or str(exc)) from exc
    except URLError as exc:
        raise RazorpayOrderError(str(exc)) from exc


def verify_payment_signature(*, order_id, payment_id, signature):
    _, key_secret = get_razorpay_credentials()
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(key_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")
