import json
from urllib import request as urlrequest
from urllib.error import URLError
from urllib.parse import urlencode

from django.conf import settings


class WhatsAppConfigurationError(Exception):
    pass


class WhatsAppAPIError(Exception):
    pass


def get_waba_template_details(detail_type="template", phone_number_id=None):
    if detail_type not in {"number", "template"}:
        raise ValueError("detail_type must be 'number' or 'template'")
    if not settings.WHATSAPP_API_KEY:
        raise WhatsAppConfigurationError("WHATSAPP_API_KEY is not configured.")

    query = {"type": detail_type}
    phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
    if phone_number_id:
        query["phone_number_id"] = phone_number_id

    separator = "&" if "?" in settings.WHATSAPP_DLT_MANAGER_URL else "?"
    api_request = urlrequest.Request(
        f"{settings.WHATSAPP_DLT_MANAGER_URL}{separator}{urlencode(query)}",
        headers={"Authorization": settings.WHATSAPP_API_KEY},
        method="GET",
    )
    try:
        with urlrequest.urlopen(api_request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
        raise WhatsAppAPIError(f"Fast2SMS WABA details request failed: {exc}") from exc

    if not payload.get("success"):
        raise WhatsAppAPIError(f"Fast2SMS returned an unsuccessful response: {payload}")
    return payload.get("data", [])


def find_template(template_name, phone_number_id=None):
    for account in get_waba_template_details("template", phone_number_id=phone_number_id):
        for template in account.get("templates", []):
            if template.get("template_name") == template_name:
                return template
    return None
