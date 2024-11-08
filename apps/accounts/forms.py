from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordChangeForm,
)
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import password_validation
from django.template.loader import render_to_string

from .models import User
from .otp_utils import EmailThread
from .validators import validate_name


class RegistrationForm(UserCreationForm):
    error_messages = {
        "password_mismatch": _("Password Mismatch."),
    }
    first_name = forms.CharField(
        validators=[validate_name],
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Amina"}),
    )
    last_name = forms.CharField(
        validators=[validate_name],
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Smith"}),
    )
    email = forms.EmailField(
        error_messages={"unique": _("Email already registered")},
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "e.g. user@domain.com"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "autocomplete": "new-password",}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "autocomplete": "new-password",}),
    )

    usable_password = None

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def _post_clean(self):
        super(RegistrationForm, self)._post_clean()
        password1 = self.cleaned_data["password1"]
        if len(password1) < 8:
            self.add_error("password1", "Password too short")

class OtpForm(forms.Form):
    otp = forms.IntegerField(
        min_value=100000,
        max_value=999999,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter OTP"}
        ),
        label="OTP Code",
    )


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": _("Enter your email address..."),
            }
        ),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )


class OTPRequestForm(forms.Form):
    email = forms.EmailField(
        label="Enter your registered email",
        max_length=254,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "e.g. user@domain.com", }
        ),
    )


class OTPVerificationForm(forms.Form):
    otp = forms.IntegerField(
        min_value=100000,
        max_value=999999,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter OTP"}
        ),
        label="OTP Code",
    )

class CustomSetPasswordForm(forms.ModelForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Confirm"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
    )
    
    class Meta:
        model = User
        fields = []  # We don't need other fields here, only password reset

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2:
            if password1 != password2:
                self.add_error("new_password2", "The two password fields must match.")
            else:
                # Validate the password
                validate_password(password1, self.instance)

        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        user = self.instance
        user.set_password(password)  # Set the password using hashing
        if commit:
            user.save()
        return user

class CustomChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "form-control",
            }
        ),
    )
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Confirm"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
            }
        ),
    )


class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(
        validators=[validate_name],
        max_length=50,
        # widget=forms.TextInput(attrs={"class": "input input--text"})
    )
    last_name = forms.CharField(
        validators=[validate_name],
        max_length=50,
        # widget=forms.TextInput(attrs={"class": "input input--text"})
    )  # TODO: FIX CLASSES NAME

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


