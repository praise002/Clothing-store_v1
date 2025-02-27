from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

# from django.utils.translation import gettext_lazy as _
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "logout-all-devices/",
        views.LogoutAllDevices.as_view(),
        name="logout_all_devices",
    ),
    # Email verification
    path("email/verify/", views.VerifyEmail.as_view(), name="verify_email"),
    path(
        "email/verify/resend/",
        views.ResendVerificationEmail.as_view(),
        name="resend_verification_email",
    ),
    # change password urls
    path(
        "password-change/",
        views.CustomPasswordChangeView.as_view(
            template_name="accounts/password_change_form.html",
            success_url=reverse_lazy("accounts:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html",
        ),
        name="password_change_done",
    ),
    # Reset Password URLs
    path(
        "password-reset/otp/",  # Request OTP for password reset
        views.PasswordResetRequestView.as_view(),
        name="reset_password_request",
    ),
    path(
        "password-reset/otp/resend/",  # Resend OTP
        views.ResendOTPRequestView.as_view(),
        name="reset_password_resend_otp",
    ),
    path(
        "password-reset/otp/verify/",  # Verify OTP before setting new password
        views.OTPVerificationView.as_view(),
        name="reset_password_verify_otp",
    ),
    path(
        "password-reset/form/",  # Form for entering new password
        views.PasswordResetView.as_view(),
        name="reset_password_form",
    ),
    path(
        "password-reset/complete/",  # Confirmation of successful password reset
        views.CustomPasswordResetCompleteView.as_view(),
        name="reset_password_complete",
    ),
]
