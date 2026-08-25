from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.test import TestCase, override_settings
from django.urls import reverse

from subscriptions.models import MembershipSubscription, SubscriptionPlan

from .admin import CustomUserAdmin
from .forms import RegisterForm
from .models import User
from .views import _generate_initial_password


class GeneratedPasswordRegistrationTests(TestCase):
    def test_registration_form_has_no_password_fields(self):
        form = RegisterForm()

        self.assertNotIn("password1", form.fields)
        self.assertNotIn("password2", form.fields)
        self.assertNotIn("password", form.fields)

    def test_generated_password_is_long_and_mixed(self):
        password = _generate_initial_password()

        self.assertEqual(len(password), 20)
        self.assertTrue(any(char.islower() for char in password))
        self.assertTrue(any(char.isupper() for char in password))
        self.assertTrue(any(char.isdigit() for char in password))
        self.assertTrue(any(char in "@#$%*-_!" for char in password))

    @patch("accounts.views.send_account_welcome_email")
    def test_registration_creates_hashed_password_and_queues_credentials_email(self, send_welcome):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("accounts:register"),
                {
                    "first_name": "Test",
                    "last_name": "Member",
                    "email": "new.member@example.com",
                    "phone": "9876543210",
                    "address": "Vrindavan",
                    "city": "Mathura",
                },
            )

        self.assertRedirects(response, reverse("subscriptions:plans"))
        user = get_user_model().objects.get(email="new.member@example.com")
        self.assertTrue(user.has_usable_password())
        self.assertNotIn("new.member@example.com", user.password)
        send_welcome.assert_called_once()
        initial_password = send_welcome.call_args.kwargs["initial_password"]
        self.assertTrue(user.check_password(initial_password))

    def test_register_form_normalizes_india_phone_to_ten_digits(self):
        form = RegisterForm(data={
            "first_name": "Test",
            "last_name": "Member",
            "phone": "+91 98765-43210",
            "address": "Vrindavan",
            "city": "Mathura",
            "pin_code": "281121",
            "district": "Mathura",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["phone"], "9876543210")

    def test_register_form_rejects_short_phone(self):
        form = RegisterForm(data={
            "first_name": "Test",
            "last_name": "Member",
            "phone": "12345",
            "address": "Vrindavan",
            "city": "Mathura",
            "pin_code": "281121",
            "district": "Mathura",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)


class UserAdminWhatsAppActionTests(TestCase):
    @patch("accounts.admin.send_certificate_whatsapp")
    def test_user_admin_action_sends_active_certificates(self, send_certificate):
        user = get_user_model().objects.create_user(username="9876543210", phone="9876543210")
        plan = SubscriptionPlan.objects.create(name="हितचिंतक-सदस्य")
        membership = MembershipSubscription.objects.create(user=user, plan=plan)
        membership.activate()
        send_certificate.return_value = 1

        request = RequestFactory().post("/admin/accounts/user/")
        request.session = {}
        setattr(request, "_messages", FallbackStorage(request))
        admin_obj = CustomUserAdmin(User, AdminSite())
        admin_obj.send_active_certificates_whatsapp(request, get_user_model().objects.filter(pk=user.pk))

        send_certificate.assert_called_once_with(membership.certificate)


@override_settings(
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY="test-google-client-id",
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET="test-google-client-secret",
)
class GoogleOAuthStartTests(TestCase):
    def test_login_page_uses_post_form_for_google_oauth(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, 'method="post"')
        self.assertContains(response, f'action="{reverse("social:begin", args=["google-oauth2"])}"')

    def test_google_oauth_post_redirects_to_google_instead_of_405(self):
        response = self.client.post(reverse("social:begin", args=["google-oauth2"]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://accounts.google.com/"))
