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
    PasswordResetRequestForm,
    RegistrationForm,
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
    """Handles user registration."""
    def get(self, request):
        form = RegistrationForm()
        return render(request, "accounts/signup.html", {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            OTPService.send_otp_email(request, user)
            # store the email in session
            request.session["verification_email"] = user.email
            return redirect('accounts:verify_email')

        return render(request, "accounts/signup.html", {"form": form})


class LoginView(LogoutRequiredMixin, View):
    """Handles user login."""
    form_class = LoginForm
    
    def get(self, request):
        form = self.form_class()
        next_url = request.GET.get("next", reverse('shop:home'))
        context = {"form": form, "next": next_url}
        return render(request, "accounts/login.html", context)

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            email = cd["email"]
            password = cd["password"]
            user = authenticate(
                request, username=email, password=password
            )  # verify the identity of a user

            if not user:
                form.add_error(None, "There was a problem logging in. Check your email and password or create an account.")
                return render(request, "accounts/login.html", {"form": form})

            if not user.user_active:
                form.add_error(None, "This account is disabled.")
                return render(request, "accounts/login.html", {"form": form})

            if not user.is_email_verified:
                request.session["verification_email"] = (
                    email  # store email in session if user is not verified
                )
                OTPService.send_otp_email(request, user)
                return render(
                    request, "accounts/email_verification_otp_form.html", {"form": form}
                )

            # passes all above test, login user
            login(request, user)

            redirect_url = request.POST.get("next", reverse('shop:home'))
            if not url_has_allowed_host_and_scheme(redirect_url, allowed_hosts={request.get_host()}):
                redirect_url = reverse('shop:home')

            return redirect(redirect_url)

        context = {"form": form}
        return render(request, "accounts/login.html", context)


class VerifyEmail(LogoutRequiredMixin, View):
    """Handles email verification using OTP."""
    form_class = OtpForm
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

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
                sweetify.error(request, "We couldn't find an account associated with this email. Please try again or contact support.")
                return redirect(reverse("accounts:login"))

            # Fetch the OTP record for the user
            try:
                otp_record = Otp.objects.get(user=user_obj)

                # Check if the OTP is valid and not expired
                if otp_record.otp == otp_code and otp_record.is_valid:
                    user_obj.is_email_verified = True
                    user_obj.save()
                    sweetify.success(request, "Verification successful!")

                    # Clear OTP after verification
                    Otp.objects.filter(user=user_obj).delete()

                    # Send welcome email
                    OTPService.welcome(request, user_obj)

                    # Clear the email from the session
                    del request.session["verification_email"]

                    return redirect(reverse("accounts:login"))
                else:
                    sweetify.error(request, "Invalid or expired OTP. Please request a new one.")
            except Otp.DoesNotExist:
                sweetify.error(request, "No OTP found. Please request a new one.")

        return render(request, 'accounts/email_verification_otp_form.html', {"form": form})

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, 'accounts/email_verification_otp_form.html', {"form": form})


class ResendVerificationEmail(LogoutRequiredMixin, View):
    """Handles resending the verification email."""
    def get(self, request):
        email = request.session.get("verification_email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            sweetify.error(request, "We couldn't find an account associated with this email. Please try again or contact support.")
            return redirect(reverse("accounts:login"))

        if user.is_email_verified:
            sweetify.info(request, "Email address already verified!")
            del request.session["verification_email"]
            return redirect(reverse("accounts:login"))

        OTPService.send_otp_email(request, user)
        sweetify.success(request, "Email Sent")
        return redirect(reverse("accounts:verify_email"))


class PasswordResetRequestView(LogoutRequiredMixin, View):
    """Handles password reset requests."""
    form_class = PasswordResetRequestForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, "accounts/password_reset_form.html", {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            
            try:
                # Try to get the user by email
                user = User.objects.get(email=email)
                
                OTPService.send_password_reset_otp(request, user)
                
                # Store email in session after OTP is successfully sent
                request.session["reset_email"] = email

                return redirect(reverse("accounts:reset_password_verify_otp"))
            except User.DoesNotExist:
                sweetify.error(request, "Sorry, no account found with this email address. Please check and try again.")
                return redirect("accounts:reset_password_request")  
            except Exception:
                sweetify.error(request, "Failed to send OTP. Please try again.") 
                
        # Re-render form with errors if form is invalid
        return render(request, "accounts/password_reset_form.html", {"form": form})


class OTPVerificationView(LogoutRequiredMixin, View):
    """Handles OTP verification for password reset."""
    # if otp is less than min or gt than max the input doesn't submit or respond
    form_class = OtpForm

    def get(self, request):
        form = self.form_class()
        return render(request, "accounts/password_reset_otp_form.html", {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"]
            email = request.session.get("reset_email")
            
            if not email:
                form.add_error(None, "Session expired. Please request a new OTP.")
                return render(request, "accounts/password_reset_otp_form.html", {"form": form})
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                form.add_error(None, "No user found for the provided email.")
                return render(request, "accounts/password_reset_otp_form.html", {"form": form})
            
            try:
                otp_instance = Otp.objects.get(otp=otp, user=user)

                if otp_instance.is_valid:
                    # Invalidate/clear any previous OTPs 
                    Otp.objects.filter(user=user).delete()
                    return redirect(reverse("accounts:reset_password_form"))
                else:
                    sweetify.error(request, "The OTP is invalid or has expired. Please request a new one.")
                    return render(request, "accounts/password_reset_otp_form.html", {"form": form})
                    
            except Otp.DoesNotExist:
                sweetify.error(request, "The OTP could not be found. Please request a new one.")
                return render(request, "accounts/password_reset_otp_form.html", {"form": form})

        # Re-render form with errors if OTP is invalid or any other error occurs
        return render(request, "accounts/password_reset_otp_form.html", {"form": form})

class ResendOTPRequestView(LogoutRequiredMixin, View):
    """Handles resending the OTP for password reset."""
    def get(self, request):
        email = request.session.get("reset_email")
        
        if not email:
            sweetify.error(request, "Please request a password reset first.")
            return redirect(reverse("accounts:reset_password_request"))

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            sweetify.error(request, "We couldn't find an account associated with this email. Please try again or contact support.")
            return redirect(reverse("accounts:reset_password_request"))
        
        OTPService.send_password_reset_otp(request, user)
        sweetify.success(request, "Email Sent")
        return redirect(reverse("accounts:reset_password_verify_otp"))
        

class PasswordResetView(View):
    """Handles password reset."""
    form_class = CustomSetPasswordForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, "accounts/password_reset_confirm.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Retrieve the email from session
            email = request.session.get("reset_email")
            
            if not email:
                sweetify.error(request, "Session expired. Please request a new OTP.")
                return redirect(reverse("accounts:reset_password_request"))
        
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                sweetify.error(request, "We couldn't find an account associated with this email. Please try again or contact support.")

            # Set new password
            new_password = form.cleaned_data["new_password1"]
            user.set_password(new_password)
            user.save()

            OTPService.password_reset_success(request, user)

            # Clear session data
            del request.session["reset_email"]

            return redirect(reverse_lazy("accounts:reset_password_complete"))

        return render(request, "accounts/password_reset_confirm.html", {"form": form})


class CustomPasswordResetCompleteView(LogoutRequiredMixin, PasswordResetCompleteView):
    """Handles the password reset complete page."""
    template_name = "accounts/password_reset_complete.html"


class CustomPasswordChangeView(PasswordChangeView):
    """Handles password change."""
    form_class = CustomChangePasswordForm


class LogoutView(LoginRequiredMixin, View):
    """Handles user logout."""
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("accounts:login")


class LogoutAllDevices(LoginRequiredMixin, View):
    """Handles logging out from all devices."""
    def post(self, request):
        logout(request)
        request.session.flush()  # Clear all session data
        return redirect(
            "accounts:login"
        )  # Redirect to the home page or any other desired page

