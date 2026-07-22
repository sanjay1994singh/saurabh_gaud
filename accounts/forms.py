from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify

from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "photo",
            "address",
            "city",
            "state",
            "password1",
            "password2",
        )
        labels = {
            "first_name": "नाम / First name",
            "last_name": "उपनाम / Last name",
            "email": "ईमेल / Email",
            "phone": "मोबाइल / Phone",
            "photo": "फोटो / Photo",
            "address": "पूरा पता / Complete address",
            "city": "शहर / City",
            "state": "राज्य / State",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
        }

    def _make_username(self):
        email = (self.cleaned_data.get("email") or "").strip()
        phone = (self.cleaned_data.get("phone") or "").strip()
        first_name = (self.cleaned_data.get("first_name") or "").strip()
        last_name = (self.cleaned_data.get("last_name") or "").strip()

        base_source = email.split("@", 1)[0] or phone or f"{first_name} {last_name}".strip() or "member"
        base = slugify(base_source) or "member"
        username = base[:140]
        counter = 1
        while User.objects.filter(username=username).exists():
            suffix = f"-{counter}"
            username = f"{base[:150 - len(suffix)]}{suffix}"
            counter += 1
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._make_username()
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "photo", "address", "city", "state")
        labels = {
            "first_name": "नाम / First name",
            "last_name": "उपनाम / Last name",
            "email": "ईमेल / Email",
            "phone": "मोबाइल / Phone",
            "photo": "फोटो / Photo",
            "address": "पूरा पता / Complete address",
            "city": "शहर / City",
            "state": "राज्य / State",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }
