from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.views import View
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordResetDoneView,
    PasswordChangeView
)

from .forms import CustomChangePasswordForm, OtpForm, RegistrationForm
from .mixins import LoginRequiredMixin, LogoutRequiredMixin
from .models import User, Otp
from .otp_utils import OTPService
from .forms import (
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    LoginForm,
    RegistrationForm,
)

import sweetify


class RegisterView(LogoutRequiredMixin, View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, "accounts/signup.html", {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            OTPService.send_otp_email(request, user)
            request.session["verification_email"] = user.email
            return render(
                request, "accounts/otp_form.html", {"form": form}
            )  # REDIRECT TO OTP VIEW
            # TODO: WRITE CHECK YOUR EMAIL FOR A VERIFICATION LINK IN THE BEFORE THE FORM

        return render(request, "accounts/signup.html", {"form": form})


class LoginView(LogoutRequiredMixin, View):
    def get(self, request):
        form = LoginForm()
        # next_url = request.GET.get("next", reverse('projects:projects_list'))
        # context = {"form": form, "next": next_url}
        context = {"form": form}
        return render(request, "accounts/login.html", context)

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            email = cd["email"]
            password = cd["password"]
            user = authenticate(
                request, username=email, password=password
            )  # verify the identity of a user

            if not user:
                sweetify.error(request, "Invalid Credentials")
                return redirect("accounts:login")

            if not user.user_active:
                sweetify.error(request, "Disabled Account")
                return redirect("accounts:login")

            if not user.is_email_verified:
                request.session["verification_email"] = (
                    email  # store email in session if user is not verified
                )
                OTPService.send_otp_email(request, user)
                return render(
                    request, "accounts/email_verification_sent.html", {"form": form}
                )

            # passes all above test, login user
            login(request, user)

            # redirect_url = request.POST.get("next", reverse('projects:projects_list'))
            # if not url_has_allowed_host_and_scheme(redirect_url, allowed_hosts={request.get_host()}):
            #     redirect_url = reverse('projects:projects_list')

            # return redirect(redirect_url)
            return redirect("/")

        context = {"form": form}
        return render(request, "accounts/login.html", context)


class VerifyEmail(LogoutRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = OtpForm(request.POST)

        if form.is_valid():
            otp_code = form.cleaned_data["otp"]

            # Get the email from the session
            email = request.session.get("verification_email")

            # Check if the email exists in the session
            if not email:
                sweetify.error(request, "Not allowed.")
                return redirect(reverse("accounts:login"))

            try:
                # Get the user by email
                user_obj = User.objects.get(email=email)

            except User.DoesNotExist:
                sweetify.error(request, "Invalid user.")
                return redirect(reverse("accounts:login"))

            # Fetch the OTP record for the user
            try:
                otp_record = Otp.objects.get(user=user_obj)

                # Check if the OTP is valid and not expired
                if otp_record.otp == otp_code and otp_record.is_valid:
                    user_obj.is_email_verified = True
                    user_obj.save()
                    sweetify.toast(request, "Verification successful!")

                    # Clear OTP after verification
                    Otp.objects.filter(user=user_obj).delete()

                    # Send welcome email
                    OTPService.welcome(request, user_obj)

                    # Clear the email from the session
                    request.session["verification_email"] = None

                    return redirect(reverse("accounts:login"))
                else:
                    sweetify.error(request, "Invalid or expired OTP.")
            except Otp.DoesNotExist:
                sweetify.error(request, "No OTP found for this user.")

        return redirect(reverse("accounts:login"))

    def get(self, request, *args, **kwargs):
        form = OtpForm()
        return render(request, "accounts/otp_form.html", {"form": form})


class ResendVerificationEmail(LogoutRequiredMixin, View):
    def get(self, request):
        email = request.session.get("verification_email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            sweetify.error(request, "Not allowed")
            return redirect(reverse("accounts:login"))

        if user.is_email_verified:
            sweetify.info(request, "Email address already verified!")
            request.session["verification_email"] = None
            return redirect(reverse("accounts:login"))

        OTPService.send_otp_email(request, user)
        sweetify.toast(self.request, "Email Sent")
        return render(request, "accounts/email_verification_sent.html")


class CustomPasswordResetView(LogoutRequiredMixin, PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = "accounts/password_reset_form.html"


class CustomPasswordResetConfirmView(LogoutRequiredMixin, PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = "accounts/password_reset_confirm.html"


class CustomPasswordResetDoneView(LogoutRequiredMixin, PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetCompleteView(LogoutRequiredMixin, PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomChangePasswordForm
    
class LogoutView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("accounts:login")


class LogoutAllDevices(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        request.session.flush()  # Clear all session data
        return redirect(
            "accounts:login"
        )  # Redirect to the home page or any other desired page
