from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm
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
