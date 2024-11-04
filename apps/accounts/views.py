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
)

from .forms import RegistrationForm
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
        return render(request, 
                      'accounts/signup.html',
                      {'form': form})
        
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            OTPService.send_otp_email(request, user)
            request.session['verification_email'] = user.email
            return render(request, 
                      'accounts/email_verification_sent.html',
                      {'form': form})  # TODO: REDIRECT TO OTP VIEW
            
        return render(request, 
                      'accounts/signup.html',
                      {'form': form})

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
            email = cd['email']
            password = cd['password']
            user = authenticate(request, 
                                username=email, 
                                password=password) # verify the identity of a user
            
                
            if not user:
                sweetify.error(request, 'Invalid Credentials')
                return redirect('accounts:login')
            
            if not user.user_active:
                sweetify.error(request, 'Disabled Account')
                return redirect('accounts:login')
            
            if not user.is_email_verified:
                request.session['verification_email'] = email  # store email in session if user is not verified
                OTPService.send_otp_email(request, user)
                return render(request, 
                      'accounts/email_verification_sent.html',
                      {'form': form})
                
            # passes all above test, login user
            login(request, user)
            
            # redirect_url = request.POST.get("next", reverse('projects:projects_list'))
            # if not url_has_allowed_host_and_scheme(redirect_url, allowed_hosts={request.get_host()}):
            #     redirect_url = reverse('projects:projects_list')

            # return redirect(redirect_url)
            return redirect('/')

        
        context = {"form": form}
        return render(request, "accounts/login.html", context)

class VerifyEmail(LogoutRequiredMixin, View):
    def post(self, request, *args, **kwargs):  # TODO: fix user_id and session
        user_id = request.POST.get("user_id")  # Get user ID from the POST data
        otp_code = request.POST.get("otp")  # Get OTP code from the POST data
        
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            sweetify.error(request, 'Invalid user.')
            return redirect(reverse('accounts:login'))

        # Fetch the OTP record for the user
        try:
            otp_record = Otp.objects.get(user=user_obj)
            # Check if the OTP is valid and not expired
            if otp_record.otp == otp_code and otp_record.is_valid:
                user_obj.is_email_verified = True
                user_obj.save()
                sweetify.toast(request, 'Verification successful!')
                
                # Clean up the OTP record after successful verification
                otp_record.delete()  
                
                OTPService.welcome(request, user_obj)  
                
                return redirect(reverse('accounts:login'))
            else:
                sweetify.error(request, 'Invalid or expired OTP.')
                return redirect(reverse('accounts:login'))
            
        except Otp.DoesNotExist:
            sweetify.error(request, 'No OTP found for this user.')
            return redirect(reverse('accounts:login'))

    def get(self, request, *args, **kwargs):
        # render a form for OTP input
        return render(request, "accounts/otp_verification.html", 
                      {"user_id": kwargs["user_id"]})
    
class ResendVerificationEmail(LogoutRequiredMixin, View):
    def get(self, request) :
        email = request.session.get("verification_email")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            sweetify.error(self.request, 'Not allowed')
            return redirect(reverse('accounts:login'))
        
        if user.is_email_verified:
            sweetify.info(self.request, 'Email address already verified!')
            request.session["verification_email"] = None
            return redirect(reverse('accounts:login'))
        
        OTPService.send_otp_email(request, user)
        sweetify.toast(self.request, 'Email Sent')
        return render(request, 
                      'accounts/email_verification_sent.html')

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
    
class LogoutView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs): 
        logout(request)
        return redirect('accounts:login')

class LogoutAllDevices(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        request.session.flush()  # Clear all session data
        return redirect('accounts:login')  # Redirect to the home page or any other desired page

