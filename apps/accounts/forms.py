from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordResetForm,
    SetPasswordForm,
    PasswordChangeForm,
)
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
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
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
            attrs={"placeholder": "e.g. user@domain.com", "autocomplete": "email"}
        ),
    )


class OTPVerificationForm(forms.Form):
    otp = forms.IntegerField(label="Enter OTP")

class CustomSetPasswordForm(SetPasswordForm):
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
