from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")
        labels = {
            "username": "यूजरनेम / Username",
            "first_name": "नाम / First name",
            "last_name": "उपनाम / Last name",
            "email": "ईमेल / Email",
            "phone": "मोबाइल / Phone",
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "photo", "address", "city")
        labels = {
            "first_name": "नाम / First name",
            "last_name": "उपनाम / Last name",
            "email": "ईमेल / Email",
            "phone": "मोबाइल / Phone",
            "photo": "फोटो / Photo",
            "address": "पता / Address",
            "city": "शहर / City",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }
