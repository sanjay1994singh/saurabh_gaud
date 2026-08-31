# Dharm Raksha Sangh

Django project scaffold for the **Dharm Raksha Sangh** site.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The project package is named `dharm_raksha_sangh` because Python packages cannot contain spaces.

## Razorpay Payment Gateway Setup

Required production details in `.env`:

```env
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_live_key_secret
RAZORPAY_WEBHOOK_SECRET=your_32_plus_character_webhook_secret
SITE_URL=https://dharmrakshasangh.com
ALLOWED_HOSTS=dharmrakshasangh.com,www.dharmrakshasangh.com
CSRF_TRUSTED_ORIGINS=https://dharmrakshasangh.com,https://www.dharmrakshasangh.com
DEBUG=False
```

Razorpay Dashboard checklist:

- Create API keys from Razorpay Dashboard and keep `RAZORPAY_KEY_SECRET` only on the server.
- Use the webhook URL `https://dharmrakshasangh.com/subscriptions/razorpay/webhook/`.
- Set the same webhook secret in Razorpay Dashboard and `RAZORPAY_WEBHOOK_SECRET`.
- Subscribe at least to `payment.captured` and `payment.failed`.
- Keep automatic capture enabled, or ensure orders are captured before activating membership.
- Live payments require HTTPS with a valid SSL certificate.

Project payment flow:

- Server creates a Razorpay order before opening Checkout.
- Browser receives only `RAZORPAY_KEY_ID`, amount, currency, and order ID.
- Payment success is verified server-side with HMAC-SHA256 before membership activation.
- Server fetches the Razorpay payment and activates membership only when status is `captured`.
- Webhook requests are verified with `X-Razorpay-Signature`.
