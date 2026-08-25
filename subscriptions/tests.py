import hashlib
import hmac
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Invoice, MembershipSubscription, PaymentTransaction, SubscriptionPlan
from .notifications import _whatsapp_number


class SubscriptionPlanSlugTests(TestCase):
    def test_hindi_slug_is_generated_automatically(self):
        plan = SubscriptionPlan.objects.create(name="सक्रिय सदस्य", plan_type=SubscriptionPlan.PAID, amount=251)
        self.assertRegex(plan.slug, r"^plan-[0-9a-f]{8}$")

    def test_duplicate_slug_gets_unique_suffix(self):
        first = SubscriptionPlan.objects.create(name="Codex Annual Member")
        second = SubscriptionPlan.objects.create(name="Codex Annual Member")
        self.assertEqual(first.slug, "codex-annual-member")
        self.assertEqual(second.slug, "codex-annual-member-2")


class WhatsAppNumberTests(TestCase):
    def test_india_phone_numbers_are_normalized_for_whatsapp(self):
        self.assertEqual(_whatsapp_number("9876543210"), "919876543210")
        self.assertEqual(_whatsapp_number("09876543210"), "919876543210")
        self.assertEqual(_whatsapp_number("+91 98765 43210"), "919876543210")


@override_settings(
    RAZORPAY_KEY_ID="rzp_test_example",
    RAZORPAY_KEY_SECRET="test_secret",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_HOST_USER="sender@example.com",
    EMAIL_HOST_PASSWORD="test-app-password",
    DEFAULT_FROM_EMAIL="sender@example.com",
)
class PaidMembershipTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="member",
            password="password123",
            first_name="Test",
            last_name="Member",
            email="member@example.com",
            phone="9876543210",
            address="Vrindavan",
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Paid Member",
            plan_type=SubscriptionPlan.PAID,
            amount=251,
        )
        self.subscription = MembershipSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            razorpay_order_id="order_test123",
        )
        self.payment = PaymentTransaction.objects.create(
            subscription=self.subscription,
            user_name="Test Member",
            user_email=self.user.email,
            user_phone=self.user.phone,
            user_address=self.user.address,
            plan_name=self.plan.name,
            amount_paise=25100,
            razorpay_order_id="order_test123",
        )
        self.client.force_login(self.user)

    @patch("subscriptions.views.fetch_razorpay_payment")
    def test_captured_matching_payment_activates_membership(self, fetch_payment):
        fetch_payment.return_value = {
            "id": "pay_test123",
            "order_id": "order_test123",
            "amount": 25100,
            "currency": "INR",
            "status": "captured",
        }
        signature = hmac.new(
            b"test_secret", b"order_test123|pay_test123", hashlib.sha256
        ).hexdigest()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("subscriptions:payment_success"),
                {
                    "razorpay_order_id": "order_test123",
                    "razorpay_payment_id": "pay_test123",
                    "razorpay_signature": signature,
                },
            )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.subscription.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.subscription.status, MembershipSubscription.ACTIVE)
        self.assertEqual(self.payment.status, PaymentTransaction.PAID)
        self.assertEqual(self.payment.razorpay_payment_id, "pay_test123")
        self.assertTrue(hasattr(self.subscription, "certificate"))
        invoice = Invoice.objects.get(payment=self.payment)
        self.assertRegex(invoice.invoice_number, r"^DRS\d{2}-\d{6}$")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0][2], "application/pdf")
        self.assertIn("Annual Membership Donation Received", mail.outbox[0].subject)
        self.assertIn("वार्षिक सदस्यता दान", mail.outbox[0].body)
        self.assertIn("yearly membership donation", mail.outbox[0].body)
        self.assertIn("non-refundable", mail.outbox[0].body)
        self.assertIn("₹251.00", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        self.assertIn("Donation Receipt", mail.outbox[0].alternatives[0].content)

        pdf_response = self.client.get(reverse("subscriptions:invoice_download", args=[invoice.pk]))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

        certificate_response = self.client.get(
            reverse("subscriptions:certificate_download", args=[self.subscription.certificate.pk])
        )
        self.assertEqual(certificate_response.status_code, 200)
        self.assertEqual(certificate_response["Content-Type"], "application/pdf")
        self.assertIn("inline", certificate_response["Content-Disposition"])
        self.assertTrue(certificate_response.content.startswith(b"%PDF-1.4"))

    @patch("subscriptions.views.fetch_razorpay_payment")
    def test_amount_mismatch_does_not_activate_membership(self, fetch_payment):
        fetch_payment.return_value = {
            "id": "pay_test123",
            "order_id": "order_test123",
            "amount": 100,
            "currency": "INR",
            "status": "captured",
        }
        signature = hmac.new(
            b"test_secret", b"order_test123|pay_test123", hashlib.sha256
        ).hexdigest()

        self.client.post(
            reverse("subscriptions:payment_success"),
            {
                "razorpay_order_id": "order_test123",
                "razorpay_payment_id": "pay_test123",
                "razorpay_signature": signature,
            },
        )

        self.subscription.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.subscription.status, MembershipSubscription.FAILED)
        self.assertEqual(self.payment.status, PaymentTransaction.FAILED)
