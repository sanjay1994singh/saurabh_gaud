from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.text import slugify

from .location_data import hindi_state_name
from .models import Country, State, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="ईमेल / मोबाइल / यूजरनेम")


def _india_country():
    return Country.objects.filter(code="IN", is_active=True).first()


def _configure_location_fields(form, selected_country=None):
    form.fields["country"].queryset = Country.objects.filter(is_active=True)
    form.fields["state_obj"].queryset = State.objects.none()
    form.fields["state_obj"].required = False
    form.fields["state_obj"].widget.attrs["data-state-select"] = "true"
    form.fields["state_obj"].label_from_instance = lambda state: hindi_state_name(state.name)

    if not selected_country:
        selected_country = _india_country()
        if selected_country:
            form.fields["country"].initial = selected_country

    if selected_country:
        form.fields["state_obj"].queryset = State.objects.filter(country=selected_country, is_active=True)


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "city",
            "pin_code",
            "district",
            "state_obj",
            "country",
            "photo",
        )
        labels = {
            "first_name": "नाम",
            "last_name": "उपनाम",
            "email": "ईमेल",
            "phone": "मोबाइल",
            "photo": "फोटो",
            "address": "पूरा पता",
            "city": "शहर",
            "district": "जिला",
            "pin_code": "पिन कोड",
            "country": "देश",
            "state_obj": "राज्य",
        }
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "country": forms.Select(attrs={"data-country-select": "true"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_country = None
        if self.is_bound:
            selected_country = Country.objects.filter(pk=self.data.get("country")).first()
        _configure_location_fields(self, selected_country)

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
        user.state = hindi_state_name(user.state_obj.name) if user.state_obj else ""
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    username = forms.CharField(label="यूजरनेम", required=False, disabled=True)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "city",
            "pin_code",
            "district",
            "state_obj",
            "country",
            "photo",
        )
        labels = {
            "first_name": "नाम",
            "last_name": "उपनाम",
            "email": "ईमेल",
            "phone": "मोबाइल",
            "photo": "फोटो",
            "address": "पूरा पता",
            "city": "शहर",
            "district": "जिला",
            "pin_code": "पिन कोड",
            "country": "देश",
            "state_obj": "राज्य",
        }
        widgets = {
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "country": forms.Select(attrs={"data-country-select": "true"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_country = None
        if self.is_bound:
            selected_country = Country.objects.filter(pk=self.data.get("country")).first()
        elif self.instance and self.instance.country_id:
            selected_country = self.instance.country
        _configure_location_fields(self, selected_country)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.state = hindi_state_name(user.state_obj.name) if user.state_obj else ""
        if commit:
            user.save()
        return user
