from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .location_data import hindi_country_name, hindi_state_name
from .models import Country, State, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="ईमेल / मोबाइल / यूजरनेम")


def _india_country():
    return Country.objects.filter(code="IN", is_active=True).first()


def _configure_location_fields(form, selected_country=None):
    form.fields["country"].queryset = Country.objects.filter(is_active=True)
    form.fields["country"].label_from_instance = lambda country: hindi_country_name(country.name)
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


def _configure_required_fields(form):
    for field_name, field in form.fields.items():
        field.required = field_name != "email"
    form.fields["email"].required = False


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "father_spouse_name",
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
            "father_spouse_name": "पिता / पति का नाम",
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
        _configure_required_fields(self)
        selected_country = None
        if self.is_bound:
            selected_country = Country.objects.filter(pk=self.data.get("country")).first()
        _configure_location_fields(self, selected_country)

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            raise forms.ValidationError("मोबाइल नंबर आवश्यक है.")
        if User.objects.filter(username=phone).exists() or User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("इस मोबाइल नंबर से अकाउंट पहले से बना है.")
        return phone

    def _make_username(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        return phone[:150]

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
            "father_spouse_name",
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
            "father_spouse_name": "पिता / पति का नाम",
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
        _configure_required_fields(self)
        self.fields["username"].required = False
        if self.instance and self.instance.photo:
            self.fields["photo"].required = False
        selected_country = None
        if self.is_bound:
            selected_country = Country.objects.filter(pk=self.data.get("country")).first()
        elif self.instance and self.instance.country_id:
            selected_country = self.instance.country
        _configure_location_fields(self, selected_country)

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            raise forms.ValidationError("मोबाइल नंबर आवश्यक है.")
        existing = User.objects.filter(phone=phone).exclude(pk=self.instance.pk)
        username_owner = User.objects.filter(username=phone).exclude(pk=self.instance.pk)
        if existing.exists() or username_owner.exists():
            raise forms.ValidationError("इस मोबाइल नंबर से अकाउंट पहले से बना है.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = (self.cleaned_data.get("phone") or user.username)[:150]
        user.state = hindi_state_name(user.state_obj.name) if user.state_obj else ""
        if commit:
            user.save()
        return user
