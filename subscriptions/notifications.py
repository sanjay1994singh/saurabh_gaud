from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape
import json
from urllib.parse import urlencode
from urllib import request as urlrequest
from urllib.error import URLError

from .invoices import build_invoice_pdf
from .whatsapp import find_template


def _send(subject, text, recipients, *, html=None, attachments=None):
    recipients = [email for email in recipients if email]
    if not recipients or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return 0
    message = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, recipients)
    if html:
        message.attach_alternative(html, "text/html")
    for filename, content, mimetype in attachments or []:
        message.attach(filename, content, mimetype)
    return message.send(fail_silently=True)


def _digits_only(value):
    return "".join(char for char in str(value or "") if char.isdigit())


def _whatsapp_number(value):
    phone = _digits_only(value)
    if len(phone) == 10:
        return f"91{phone}"
    if len(phone) == 11 and phone.startswith("0"):
        return f"91{phone[1:]}"
    if len(phone) == 12 and phone.startswith("91"):
        return phone
    return phone


def _send_whatsapp_document(phone, document_url, filename):
    phone = _whatsapp_number(phone)
    if (
        not phone
        or not document_url
        or not settings.WHATSAPP_API_URL
        or not settings.WHATSAPP_API_KEY
        or not settings.WHATSAPP_PHONE_NUMBER_ID
    ):
        return 0

    query = urlencode({
        "authorization": settings.WHATSAPP_API_KEY,
        "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID,
        "to": phone,
        "type": "document",
        "url": document_url,
        "document_filename": filename,
    })
    separator = "&" if "?" in settings.WHATSAPP_API_URL else "?"
    request = urlrequest.Request(f"{settings.WHATSAPP_API_URL}{separator}{query}", method="GET")
    try:
        with urlrequest.urlopen(request, timeout=20) as response:
            return 1 if 200 <= response.status < 300 else 0
    except (OSError, URLError, ValueError):
        return 0


def _whatsapp_template_url():
    return (
        f"https://www.fast2sms.com/dev/whatsapp/"
        f"{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


def get_configured_certificate_template():
    return find_template(settings.WHATSAPP_TEMPLATE_CERTIFICATE_GENERATED)


def _send_whatsapp_template(phone, template_name, body_values, *, header_document_url="", header_filename=""):
    phone = _whatsapp_number(phone)
    if not phone or not template_name or not settings.WHATSAPP_API_KEY or not settings.WHATSAPP_PHONE_NUMBER_ID:
        return 0

    components = []
    if header_document_url:
        components.append({
            "type": "header",
            "parameters": [{
                "type": "document",
                "document": {
                    "link": header_document_url,
                    "filename": header_filename or "certificate.pdf",
                },
            }],
        })
    if body_values:
        components.append({
            "type": "body",
            "parameters": [
                {"type": "text", "text": str(value or "")}
                for value in body_values
            ],
        })

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": settings.WHATSAPP_LANGUAGE_CODE},
            "components": components,
        },
    }
    request = urlrequest.Request(
        _whatsapp_template_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": settings.WHATSAPP_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(request, timeout=20) as response:
            return 1 if 200 <= response.status < 300 else 0
    except (OSError, URLError, ValueError):
        return 0


def _send_fast2sms_template(phone, message_id, variables_values="", *, media_url="", document_filename=""):
    phone = _whatsapp_number(phone)
    if not phone or not message_id or not settings.WHATSAPP_API_KEY or not settings.WHATSAPP_PHONE_NUMBER_ID:
        return 0

    query = {
        "message_id": message_id,
        "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID,
        "numbers": phone,
    }
    if variables_values:
        query["variables_values"] = variables_values
    if media_url:
        query["media_url"] = media_url
    if document_filename:
        query["document_filename"] = document_filename

    request = urlrequest.Request(
        f"https://www.fast2sms.com/dev/whatsapp?{urlencode(query)}",
        headers={"Authorization": settings.WHATSAPP_API_KEY},
        method="GET",
    )
    try:
        with urlrequest.urlopen(request, timeout=20) as response:
            return 1 if 200 <= response.status < 300 else 0
    except (OSError, URLError, ValueError):
        return 0


def _email_shell(title, intro, content, *, alert="", actions=""):
    organization = escape(settings.ORGANIZATION_NAME)
    contact = escape(settings.ORGANIZATION_EMAIL)
    phone = escape(settings.ORGANIZATION_PHONE)
    alert_html = (
        f'<div style="margin:22px 0;padding:15px 18px;background:#fff3df;border-left:4px solid #d87922;color:#5a260f;line-height:1.6">{alert}</div>'
        if alert
        else ""
    )
    return f"""<!doctype html>
<html><body style="margin:0;background:#f5efe7;font-family:Arial,'Noto Sans Devanagari',sans-serif;color:#32150b">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5efe7;padding:24px 10px"><tr><td align="center">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border:1px solid #ead8c5;border-radius:14px;overflow:hidden">
<tr><td style="padding:22px 28px;background:#3a170c;color:#ffe2a6"><div style="font-size:22px;font-weight:700">{organization}</div><div style="margin-top:5px;font-size:13px">सेवा • संस्कार • समर्पण</div></td></tr>
<tr><td style="padding:30px 28px"><h1 style="margin:0 0 16px;font-size:24px;color:#7b2435">{title}</h1><p style="margin:0 0 18px;line-height:1.7">{intro}</p>{content}{alert_html}{actions}</td></tr>
<tr><td style="padding:20px 28px;background:#fff8ed;color:#6c5548;font-size:12px;line-height:1.6">यह एक स्वचालित सेवा-संदेश है। अपना Password, OTP, CVV या UPI PIN किसी से साझा न करें।<br>This is an automated service message. Never share your password, OTP, CVV or UPI PIN.<br><br>{organization} · {contact} · {phone}</td></tr>
</table></td></tr></table></body></html>"""


def _button(url, label, color="#d87922"):
    return f'<a href="{escape(url)}" style="display:inline-block;margin:6px 8px 0 0;padding:12px 18px;border-radius:8px;background:{color};color:#fff;text-decoration:none;font-weight:700">{label}</a>'


def send_membership_payment_email(invoice):
    payment = invoice.payment
    subscription = payment.subscription
    profile_url = f"{settings.SITE_URL}/accounts/profile/"
    invoice_url = f"{settings.SITE_URL}{invoice.get_absolute_url()}"
    amount = f"₹{invoice.total_rupees:,.2f}"
    safe_name = escape(payment.user_name)
    safe_plan = escape(payment.plan_name)
    safe_invoice = escape(invoice.invoice_number)
    safe_payment_id = escape(payment.razorpay_payment_id)
    validity = f"{subscription.starts_at:%d %b %Y} – {subscription.ends_at:%d %b %Y}"
    subject = f"वार्षिक सदस्यता दान प्राप्त हुआ | Annual Membership Donation Received | {invoice.invoice_number}"
    text = (
        f"नमस्ते {payment.user_name},\n\nधर्म रक्षा संघ के लिए आपका {amount} का वार्षिक सदस्यता दान सफलतापूर्वक प्राप्त हुआ है। "
        f"आपकी {payment.plan_name} सदस्यता सक्रिय है।\nसदस्यता अवधि: {validity}\nPayment ID: {payment.razorpay_payment_id}\nReceipt: {invoice.invoice_number}\n\n"
        "सफल भुगतान और सदस्यता सक्रिय होने के बाद यह स्वैच्छिक दान अंतिम एवं non-refundable है। केवल duplicate debit, failed activation या कानून द्वारा अनिवार्य स्थिति अलग होगी।\n\n"
        f"Dear {payment.user_name},\nYour yearly membership donation of {amount} to Dharm Raksha Sangh has been received successfully. "
        f"Your {payment.plan_name} membership is active.\nMembership period: {validity}\n"
        "Once payment is successful and membership is activated, this voluntary donation is final and non-refundable, except duplicate debit, failed activation, or where required by law.\n\n"
        f"Profile/Certificate: {profile_url}\nDonation receipt: {invoice_url}\n"
    )
    details = f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="8" style="margin:16px 0;border-collapse:collapse;background:#fffaf3">
<tr><td style="border-bottom:1px solid #ead8c5">दान राशि / Donation amount</td><td align="right" style="border-bottom:1px solid #ead8c5"><strong>{amount}</strong></td></tr>
<tr><td style="border-bottom:1px solid #ead8c5">सदस्यता / Membership</td><td align="right" style="border-bottom:1px solid #ead8c5"><strong>{safe_plan}</strong></td></tr>
<tr><td style="border-bottom:1px solid #ead8c5">अवधि / Validity</td><td align="right" style="border-bottom:1px solid #ead8c5">{validity}</td></tr>
<tr><td style="border-bottom:1px solid #ead8c5">Payment ID</td><td align="right" style="border-bottom:1px solid #ead8c5">{safe_payment_id}</td></tr>
<tr><td>Donation receipt</td><td align="right"><strong>{safe_invoice}</strong></td></tr></table>"""
    html = _email_shell(
        "वार्षिक सदस्यता दान प्राप्त हुआ<br><span style='font-size:17px'>Annual Membership Donation Received</span>",
        f"नमस्ते <strong>{safe_name}</strong>,<br>धर्म रक्षा संघ के प्रति आपके सहयोग के लिए धन्यवाद।<br><span style='color:#6c5548'>Dear <strong>{safe_name}</strong>, thank you for supporting Dharm Raksha Sangh.</span>",
        details,
        alert="<strong>महत्वपूर्ण / Important:</strong> सफल भुगतान और सदस्यता सक्रिय होने के बाद यह स्वैच्छिक वार्षिक दान अंतिम एवं non-refundable है। केवल duplicate debit, failed activation अथवा कानून द्वारा अनिवार्य स्थिति अपवाद होगी।<br>After successful payment and membership activation, this voluntary yearly donation is final and non-refundable, except duplicate debit, failed activation, or where required by law.",
        actions=_button(profile_url, "प्रोफाइल व प्रमाणपत्र / Profile & Certificate") + _button(invoice_url, "दान रसीद / Donation Receipt", "#21684f"),
    )
    return _send(subject, text, [payment.user_email], html=html, attachments=[(f"{invoice.invoice_number}.pdf", build_invoice_pdf(invoice), "application/pdf")])


def send_payment_failed_email(payment):
    subject = f"सदस्यता दान भुगतान असफल | Membership Donation Payment Failed | {payment.razorpay_order_id}"
    text = (
        f"नमस्ते {payment.user_name},\nआपका {payment.plan_name} सदस्यता दान भुगतान पूरा नहीं हुआ और सदस्यता सक्रिय नहीं हुई। "
        f"यदि राशि कट गई है तो Order ID {payment.razorpay_order_id} के साथ संपर्क करें।\n\n"
        f"Dear {payment.user_name},\nYour membership donation payment was not completed and no membership was activated. "
        f"If your account was debited, contact us with Order ID {payment.razorpay_order_id}."
    )
    html = _email_shell(
        "भुगतान पूरा नहीं हुआ<br><span style='font-size:17px'>Payment Was Not Completed</span>",
        f"नमस्ते <strong>{escape(payment.user_name)}</strong>,",
        f"<p style='line-height:1.7'>आपकी सदस्यता सक्रिय नहीं हुई है। यदि राशि कट गई है, तो सहायता के लिए यह Order ID भेजें:<br>Your membership was not activated. If debited, contact us with this Order ID:<br><strong>{escape(payment.razorpay_order_id)}</strong></p>",
    )
    return _send(subject, text, [payment.user_email], html=html)


def send_account_welcome_email(user, initial_password=None):
    name = user.get_full_name() or user.get_username()
    profile_url = f"{settings.SITE_URL}/accounts/profile/"
    change_url = f"{settings.SITE_URL}/accounts/password_change/"
    credentials_text = ""
    credentials_html = ""
    if initial_password:
        login_id = user.email or user.username
        credentials_text = f"\nLogin ID: {login_id}\nInitial password: {initial_password}\nपहली login के बाद password बदलें / Change after first login: {change_url}\n"
        credentials_html = f"<div style='padding:16px;background:#fff8ed;border:1px solid #ead8c5;border-radius:8px;line-height:1.8'><strong>Login ID:</strong> {escape(login_id)}<br><strong>Initial password:</strong> {escape(initial_password)}<br><a href='{escape(change_url)}'>पहली login के बाद password बदलें / Change after first login</a></div>"
    subject = f"धर्म रक्षा संघ में आपका स्वागत है | Welcome to {settings.ORGANIZATION_NAME}"
    text = f"नमस्ते {name},\nआपका धर्म रक्षा संघ account सफलतापूर्वक बन गया है।{credentials_text}\nDear {name},\nYour Dharm Raksha Sangh account has been created successfully.\nProfile: {profile_url}"
    html = _email_shell(
        "आपका स्वागत है<br><span style='font-size:17px'>Welcome to Dharm Raksha Sangh</span>",
        f"नमस्ते <strong>{escape(name)}</strong>,<br>आपका account सफलतापूर्वक बन गया है।<br><span style='color:#6c5548'>Your account has been created successfully.</span>",
        credentials_html,
        actions=_button(profile_url, "प्रोफाइल खोलें / Open Profile"),
    )
    return _send(subject, text, [user.email], html=html)


def send_account_welcome_whatsapp(user, initial_password=None):
    name = user.get_full_name() or user.get_username()
    login_id = user.phone or user.username
    return _send_whatsapp_template(
        user.phone,
        settings.WHATSAPP_TEMPLATE_ACCOUNT_CREATED,
        [name, login_id, initial_password or ""],
    )


def _signed_certificate_pdf_url(certificate):
    token = signing.dumps(
        {"certificate_id": certificate.pk},
        salt="certificate-whatsapp-document",
    )
    return f"{settings.SITE_URL}/subscriptions/certificate-whatsapp/{token}/"


def _signed_invoice_pdf_url(invoice):
    token = signing.dumps(
        {"invoice_id": invoice.pk},
        salt="invoice-whatsapp-document",
    )
    return f"{settings.SITE_URL}/subscriptions/invoice-whatsapp/{token}/"


def send_certificate_whatsapp(certificate, initial_password=None, invoice=None):
    user = certificate.user
    certificate_url = _signed_certificate_pdf_url(certificate)
    name = user.get_full_name() or user.get_username()
    sent = _send_fast2sms_template(
        user.phone,
        settings.WHATSAPP_TEMPLATE_CERTIFICATE_MESSAGE_ID,
        name,
        media_url=certificate_url,
        document_filename=f"{certificate.certificate_number}.pdf",
    )
    if invoice:
        sent += _send_whatsapp_document(
            user.phone,
            _signed_invoice_pdf_url(invoice),
            f"Dharm-Raksha-Sangh-{invoice.invoice_number}.pdf",
        )
    return sent


def send_profile_updated_email(user):
    name = user.get_full_name() or user.get_username()
    subject = "आपकी account details update हुईं | Account Details Updated"
    text = f"नमस्ते {name},\nआपकी Dharm Raksha Sangh profile details update हुई हैं। यदि यह आपने नहीं किया तो तुरंत {settings.ORGANIZATION_EMAIL} पर संपर्क करें।\n\nDear {name},\nYour profile details were updated. If this was not you, contact us immediately."
    html = _email_shell(
        "प्रोफाइल अपडेट हुई<br><span style='font-size:17px'>Profile Updated</span>",
        f"नमस्ते <strong>{escape(name)}</strong>,",
        "<p style='line-height:1.7'>आपकी Dharm Raksha Sangh profile details update हुई हैं।<br>Your Dharm Raksha Sangh profile details were updated.</p>",
        alert=f"यदि यह update आपने नहीं किया है, तो तुरंत {escape(settings.ORGANIZATION_EMAIL)} पर संपर्क करें।<br>If you did not make this change, contact us immediately.",
    )
    return _send(subject, text, [user.email], html=html)
