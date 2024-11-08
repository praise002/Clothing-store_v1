from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.views import View
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordChangeView,
)

from .forms import (
    CustomChangePasswordForm,
    OtpForm,
    RegistrationForm,
    OTPRequestForm,
    OTPVerificationForm,
)
from .mixins import LoginRequiredMixin, LogoutRequiredMixin
from .models import User, Otp
from .otp_utils import OTPService
from .forms import (
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
            return redirect('accounts:verify_email')

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
                    request, "accounts/otp_form_verification.html", {"form": form}
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
        return render(request, "accounts/otp_form_verification.html", {"form": form})


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
        return render(request, "accounts/otp_form_verification.html")


class OTPRequestView(View):
    template_name = "accounts/password_reset_form.html"
    
    def get(self, request):
        form = OTPRequestForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = OTPRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = get_object_or_404(User, email=email)

            # Send OTP using utility function
            if OTPService.send_password_reset_otp(request, user):
                # Store email in session after OTP is successfully sent
                request.session["reset_email"] = email

                sweetify.success(request, "An OTP has been sent to your email.")
                return redirect(reverse_lazy("accounts:reset_password_verify_otp"))
            else:
                sweetify.error(request, "Failed to send OTP. Please try again.")

        # Re-render form with errors if form is invalid
        return render(request, self.template_name, {"form": form})


class OTPVerificationView(LogoutRequiredMixin, View):
    form_class = OTPVerificationForm
    template_name = "accounts/password_reset_otp_form.html"

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"]
            otp_instance = get_object_or_404(Otp, otp=otp, user=request.user)

            # Check if the OTP matches and is not expired
            if otp_instance.is_valid():
                return redirect(reverse_lazy("accounts:reset_password_form"))
            else:
                sweetify.error(request, "Invalid OTP or OTP has expired.")

        # Re-render form with errors if OTP is invalid or any other error occurs
        return render(request, self.template_name, {"form": form})


class PasswordResetView(View):
    template_name = "accounts/password_reset_confirm.html"
    form_class = CustomSetPasswordForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Retrieve the email from session
            email = request.session.get("reset_email")
            user = get_object_or_404(User, email=email)

            # Set new password
            new_password = form.cleaned_data["new_password1"]
            user.set_password(new_password)
            user.save()

            # Update session to keep user logged in
            update_session_auth_hash(request, user)

            # Clear session data
            request.session.pop("reset_email", None)

            return redirect(reverse_lazy("accounts:password_reset_complete"))

        return render(request, self.template_name, {"form": form})


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


# TODO: CHECK ALL THE SWEETIFY.INFO & SUCCESS
