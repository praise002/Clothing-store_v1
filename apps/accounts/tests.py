from django.conf import settings
from apps.accounts.forms import CustomSetPasswordForm, OtpForm, PasswordResetRequestForm, RegistrationForm, LoginForm
from apps.accounts.models import Otp, User
from apps.common.utils import TestUtil
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
import json
import uuid

valid_data = {
    "first_name": "Test",
    "last_name": "User",
    "email": "testuser@example.com",
    "password1": "strong_password",
    "password2": "strong_password",
}

invalid_data = {
    "first_name": "Test",
    "last_name": "User",
    "email": "invalid_email",
    "password1": "short",
    "password2": "short",
}


class TestAccounts(TestCase):
    register_url = reverse("accounts:register")
    verify_email_url = reverse("accounts:verify_email")
    login_url = reverse("accounts:login")
    logout_url = reverse("accounts:logout")
    logout_all_url = reverse("accounts:logout_all_devices")
    resend_verification_email_url = reverse("accounts:resend_verification_email")
    password_reset_request_url = reverse("accounts:reset_password_request")
    password_reset_verify_otp_url = reverse("accounts:reset_password_verify_otp")
    password_reset_form_url = reverse("accounts:reset_password_form")
    password_reset_resend_otp_url = reverse("accounts:reset_password_resend_otp")
    

    def setUp(self):
        """Set up the test client and initial data."""
        self.client = Client()
        self.new_user = TestUtil.new_user()
        self.other_user = TestUtil.other_user()
        self.verified_user = TestUtil.verified_user()
        self.inactive_user = TestUtil.inactive_user()
        self.valid_data = valid_data
        self.invalid_data = invalid_data

    @patch("apps.accounts.otp_utils.OTPService.send_otp_email")
    def test_register(self, mock_verification):
        # GET
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/signup.html")
        self.assertIsInstance(response.context["form"], RegistrationForm)

        # POST
        # Verify that a new user can be registered successfully
        response = self.client.post(self.register_url, self.valid_data)

        user = User.objects.get(email=self.valid_data["email"])
        self.assertEqual(self.client.session["verification_email"], user.email)
        mock_verification.assert_called_once_with(response.wsgi_request, user)

        # Verify that a user with the same email cannot be registered again
        response = self.client.post(self.register_url, self.valid_data)
        self.assertIsNotNone(response.context.get("form").errors)

        # Verify that a invalid registration data renders the signup template again
        response = self.client.post(self.register_url, self.invalid_data)
        self.assertTemplateUsed(response, "accounts/signup.html")
        self.assertIsInstance(response.context["form"], RegistrationForm)

    @patch("apps.accounts.otp_utils.OTPService.welcome")
    def test_verify_email(self, mock_welcome):
        # Create a new user and store their email in the session
        new_user = self.new_user
        other_user = self.other_user
        session = self.client.session  # Get the session
        session["verification_email"] = new_user.email  # Set the session variable
        session.save()  # Explicitly save the session

        session = self.client.session  # Get the session
        session["verification_email"] = other_user.email  # Set the session variable
        session.save() 
        
        # --- Test GET Request ---
        response = self.client.get(self.verify_email_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/email_verification_otp_form.html")
        self.assertIsInstance(response.context["form"], OtpForm)

        # --- Test POST Request with Expired OTP ---
        # Create a valid OTP for the user
        otp_record = Otp.objects.create(
            user=new_user,
            otp="123456",
            created_at=timezone.now()
            - timedelta(minutes=settings.EMAIL_OTP_EXPIRE_MINUTES + 5),
        )
        # Verify that the OTP is expired
        self.assertFalse(otp_record.is_valid)
        response = self.client.post(self.verify_email_url, {"otp": "123456"})

        # Verify that the user's email is not verified
        new_user.refresh_from_db()
        self.assertFalse(new_user.is_email_verified)

        # Verify that the OTP record still exists
        self.assertTrue(Otp.objects.filter(user=new_user).exists())
        
        # Verify that the OTP is invalid
        response = self.client.post(self.verify_email_url, {"otp": "invalid_otp"})
        self.assertTrue(response.context["form"], True)

        # --- Test POST Request with Valid OTP ---
        otp_record_recent = Otp.objects.create(
            user=other_user,
            otp=654321,
        )
        
        # Verify that the OTP is valid
        self.assertTrue(otp_record_recent.is_valid)
        
        response = self.client.post(self.verify_email_url, {"otp": "654321"})
        
        # Check for sweetify success in session
        session_sweetify = json.loads(self.client.session.get('sweetify'))
        self.assertEqual(session_sweetify['title'], "Verification successful!")
        # Verify redirection to the login page
        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        # Refresh the user object from the database and check if email is verified
        other_user.refresh_from_db()
        self.assertTrue(other_user.is_email_verified)

        # Verify that the welcome email was sent
        mock_welcome.assert_called_once_with(response.wsgi_request, other_user)

        # Verify that the OTP record was deleted after successful verification
        with self.assertRaises(Otp.DoesNotExist):
            Otp.objects.get(user=other_user)

        # --- Test POST Request with No OTP Record ---
        session = self.client.session  
        session["verification_email"] = new_user.email  
        session.save()
        Otp.objects.filter(user=new_user).delete()  # Ensure no OTP exists
        response = self.client.post(self.verify_email_url, {'otp': '123456'})

        # Verify that the user's email is not verified
        new_user.refresh_from_db()
        self.assertFalse(new_user.is_email_verified)

        # --- Test POST Request with No Email in Session ---
        session = self.client.session  
        del session["verification_email"]
        session.save()
        
        response = self.client.post(self.verify_email_url, {'otp': '123456'})
        
        # Check for sweetify error message in session
        session_sweetify = json.loads(self.client.session.get('sweetify'))
        self.assertEqual(session_sweetify.get('title'), "Not allowed.")

        # Verify redirection to the login page
        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    @patch("apps.accounts.otp_utils.OTPService.send_otp_email")
    def test_resend_verification_email(self, mock_send_otp_email):
        # --- Test GET Request with Valid Email in Session ---
        unverified_user = self.new_user
        session = self.client.session
        session["verification_email"] = unverified_user.email
        session.save()

        response = self.client.get(self.resend_verification_email_url)
        
        self.assertRedirects(
            response,
            self.verify_email_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        mock_send_otp_email.assert_called_once()
        
        # --- Test GET Request with No Email in Session ---
        session = self.client.session
        session["verification_email"] = None
        session.save()

        response = self.client.get(self.resend_verification_email_url)
        
        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        
        # --- Test GET Request with Already Verified Email ---
        verified_user = self.verified_user
        session = self.client.session
        session["verification_email"] = verified_user.email
        session.save()

        response = self.client.get(self.resend_verification_email_url)
        
        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        
    @patch("apps.accounts.otp_utils.OTPService.send_password_reset_otp")
    def test_password_reset_request(self, mock_send_otp):
        # --- Test GET Request ---
        response = self.client.get(self.password_reset_request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_form.html")
        self.assertIsInstance(response.context["form"], PasswordResetRequestForm)
        
        # --- Test POST Request with Valid Email ---
        verified_user = self.verified_user
        response = self.client.post(
            self.password_reset_request_url,
            {"email": verified_user.email},
        )
        self.assertRedirects(
            response,
            self.password_reset_verify_otp_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        mock_send_otp.assert_called_once()
        
        # --- Test POST Request with Invalid Email ---
        response = self.client.post(
            self.password_reset_request_url,
            {"email": "invalid@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            self.password_reset_request_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        
    def test_otp_verification(self):
        # --- Test GET Request ---
        response = self.client.get(self.password_reset_verify_otp_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_otp_form.html")
        self.assertIsInstance(response.context["form"], OtpForm)
        
        # --- Test POST Request with Valid OTP ---
        verified_user = self.verified_user
        otp_record = Otp.objects.create(user=verified_user, otp="123456")
        session = self.client.session
        session["reset_email"] = verified_user.email
        session.save()

        response = self.client.post(
            self.password_reset_verify_otp_url, {"otp": "123456"}
        )
        
        self.assertRedirects(
            response,
            self.password_reset_form_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        
        # --- Test POST Request with Invalid OTP ---
        response = self.client.post(
            self.password_reset_verify_otp_url, {"otp": "654321"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_otp_form.html")
        self.assertIsNotNone(response.context.get("form").errors)
        
         # --- Test POST Request with Expired OTP ---
        otp_record.created_at = timezone.now() - timedelta(minutes=settings.EMAIL_OTP_EXPIRE_MINUTES + 5)
        otp_record.save()
        response = self.client.post(
            self.password_reset_verify_otp_url, {"otp": "123456"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_otp_form.html")
        self.assertIsNotNone(response.context.get("form").errors)

    @patch("apps.accounts.otp_utils.OTPService.send_password_reset_otp")
    def test_resend_otp_request(self, mock_send_otp):
        # --- Test GET Request with Valid Email in Session ---
        verified_user = self.verified_user
        session = self.client.session
        session["reset_email"] = verified_user.email
        session.save()

        response = self.client.get(self.password_reset_resend_otp_url)
        self.assertRedirects(
            response,
            self.password_reset_verify_otp_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        mock_send_otp.assert_called_once()
        
        # --- Test GET Request with No Email in Session ---
        session = self.client.session
        del session["reset_email"]
        session.save()

        response = self.client.get(self.password_reset_resend_otp_url)
        
        self.assertRedirects(
            response,
            self.password_reset_request_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        
    def test_password_reset(self):
        # --- Test GET Request ---
        response = self.client.get(reverse("accounts:reset_password_form"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_confirm.html")
        self.assertIsInstance(response.context["form"], CustomSetPasswordForm)

        # --- Test POST Request with Valid Data ---
        verified_user = self.verified_user
        session = self.client.session
        session["reset_email"] = verified_user.email
        session.save()

        response = self.client.post(
            reverse("accounts:reset_password_form"),
            {"new_password1": "newpassword123", "new_password2": "newpassword123"},
        )
        self.assertRedirects(
            response,
            reverse("accounts:reset_password_complete"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        
        # --- Test POST Request with Invalid Data ---
        response = self.client.post(
            reverse("accounts:reset_password_form"),
            {"new_password1": "newpassword123", "new_password2": "mismatch"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_confirm.html")
        self.assertIsNotNone(response.context.get("form").errors)
        
    def test_login(self):
        # GET #
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertIsInstance(response.context["form"], LoginForm)
        
        # --- Test POST Request with Invalid Credentials ---
        response = self.client.post(
            self.login_url,
            {"email": "invalid@example.com", "password": "wrongpassword"},
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertIsNotNone(response.context.get("form").errors)
        
        # --- Test POST Request with Unverified Email ---
        unverified_user = self.new_user
        response = self.client.post(
            self.login_url,
            {"email": unverified_user.email, "password": "testpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/email_verification_otp_form.html")
        self.assertEqual(self.client.session["verification_email"], unverified_user.email)
        
        # --- Test POST Request with Inactive User ---
        response = self.client.post(
            self.login_url,
            {"email": self.inactive_user.email, "password": "testpassword"},
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertIsNotNone(response.context.get("form").errors)

        # --- Test POST Request with Valid Credentials ---
        # Create a verified user
        verified_user = self.verified_user
        response = self.client.post(
            self.login_url,
            {"email": verified_user.email, "password": "testpassword"},
        )
        
        self.assertRedirects(
            response,
            reverse("shop:home"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        

    def test_logout(self):
        verified_user = self.verified_user

        # Ensures A user logs out successfully
        self.client.login(email=verified_user.email, password="testpassword")
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_logout_all_devices(self):
        verified_user = self.verified_user

        self.client.login(email=verified_user.email, password="testpassword")
        response = self.client.post(reverse("accounts:logout_all_devices"))
        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )
        session = self.client.session
        self.assertFalse(session.keys(), "Session was not flushed as expected.")
        self.assertEqual(len(session.items()), 0) 
