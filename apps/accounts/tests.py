from django.conf import settings
from apps.accounts.forms import OtpForm, RegistrationForm, LoginForm
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
    login_url = reverse("accounts:login")
    logout_url = reverse("accounts:logout")
    logout_all_url = reverse("accounts:logout_all_devices")
    resend_verification_email_url = reverse("accounts:resend_verification_email")

    def setUp(self):
        """Set up the test client and initial data."""
        self.client = Client()
        self.new_user = TestUtil.new_user()
        self.other_user = TestUtil.other_user()
        self.verified_user = TestUtil.verified_user()
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
        response = self.client.get(reverse("accounts:verify_email"))
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
        response = self.client.post(reverse("accounts:verify_email"), {"otp": "123456"})

        # Verify that the user's email is not verified
        new_user.refresh_from_db()
        self.assertFalse(new_user.is_email_verified)

        # Verify that the OTP record still exists
        self.assertTrue(Otp.objects.filter(user=new_user).exists())
        
        # Verify that the OTP is invalid
        response = self.client.post(reverse("accounts:verify_email"), {"otp": "invalid_otp"})
        self.assertTrue(response.context["form"], True)

        # --- Test POST Request with Valid OTP ---
        otp_record_recent = Otp.objects.create(
            user=other_user,
            otp=654321,
        )
        
        # Verify that the OTP is valid
        self.assertTrue(otp_record_recent.is_valid)
        
        response = self.client.post(reverse("accounts:verify_email"), {"otp": "654321"})
        
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
        response = self.client.post(reverse('accounts:verify_email'), {'otp': '123456'})

        # Verify that the user's email is not verified
        new_user.refresh_from_db()
        self.assertFalse(new_user.is_email_verified)

        # --- Test POST Request with No Email in Session ---
        session = self.client.session  
        session["verification_email"] = None
        session.save()
        
        response = self.client.post(reverse('accounts:verify_email'), {'otp': '123456'})
        
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

    @patch("apps.accounts.senders.SendEmail.verification")
    def test_resend_verification_email(self, mock_verification):
        new_user = self.new_user

        # Verify that an unverified user can get a new email
        session = self.client.session  # Get the session
        session["verification_email"] = new_user.email  # Set the session variable
        session.save()  # Explicitly save the session

        # Then, attempt to resend the activation email
        response = self.client.get(
            self.resend_verification_email_url,
        )
        self.assertTemplateUsed(response, "accounts/email_verification_sent.html")

        # Verify the mock function was called with the correct arguments
        mock_verification.assert_called_once_with(response.wsgi_request, new_user)

        # Verify that a verified user cannot get a new email
        new_user.is_email_verified = True
        new_user.save()

        response = self.client.get(
            self.resend_verification_email_url,
        )
        session_sweetify = json.loads(self.client.session.get("sweetify"))
        self.assertEqual(
            session_sweetify.get("title"), "Email address already verified!"
        )

        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        # Verify that an error is raised when attempting to resend the activation email for a user that doesn't exist
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email="invalid_email@example.com")

        response = self.client.get(
            self.resend_verification_email_url,
        )

        session_sweetify = json.loads(self.client.session.get("sweetify"))
        self.assertEqual(session_sweetify.get("title"), "Not allowed")

        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_login(self):
        # GET #
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertIsInstance(response.context["form"], LoginForm)

        # POST
        new_user = self.new_user

        # Test for invalid credentials
        response = self.client.post(
            self.login_url,
            {"email": "invalid@email.com", "password": "invalidpassword"},
        )

        # Check for sweetify error in session
        session_sweetify = json.loads(self.client.session.get("sweetify"))
        self.assertEqual(session_sweetify["title"], "Invalid Credentials")

        self.assertRedirects(
            response,
            self.login_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        # Test for unverified credentials (email)
        response = self.client.post(
            self.login_url,
            {"email": new_user.email, "password": "testpassword"},
        )
        self.assertTemplateUsed(response, "accounts/email_verification_sent.html")

        # Test for valid credentials and verified email address
        new_user.is_email_verified = True
        new_user.save()
        response = self.client.post(
            self.login_url,
            {"email": new_user.email, "password": "testpassword"},
        )
        self.assertRedirects(
            response,
            reverse("projects:projects_list"),
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
