from apps.accounts.forms import UserEditForm
from apps.common.utils import TestUtil
from django.test import TestCase, Client
from django.urls import reverse

from apps.profiles.forms import ProfileEditForm


class TestProfileViews(TestCase):
    login_url = reverse("accounts:login")
    profile_view_url = reverse("profiles:profile")
    profile_edit_url = reverse("profiles:profile_edit")

    def setUp(self):
        self.client = Client()
        self.user = TestUtil.verified_user()
        self.profile = self.user.profile

    def test_my_profile_view_get(self):
        # Log in the user
        self.client.force_login(self.user)

        # Make a GET request to the profile page
        response = self.client.get(self.profile_view_url)

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/profile.html")

    def test_profile_edit_view_get(self):
        # Log in the user
        self.client.force_login(self.user)

        # Make a GET request to the profile edit page
        response = self.client.get(self.profile_edit_url)

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/edit.html")
        self.assertIsInstance(response.context["user_form"], UserEditForm)
        self.assertIsInstance(response.context["profile_form"], ProfileEditForm)

    def test_profile_edit_view_post_valid_data(self):
        # Log in the user
        self.client.force_login(self.user)

        # Prepare valid form data
        data = {
            "first_name": "Tems",
            "last_name": "Verified",
            "email": "testverifieduser@example.com",
            "is_email_verified": True,
            "shipping_address": "VA",
            "postal_code": "456",
            "password": "testpassword",
            "city": "Los Angeles",
            "avatar": "/media/photos/2024/09/01/test_image.jpg",
            "phone": "12345"
        }
        

        # Make a POST request to the profile edit page
        response = self.client.post(self.profile_edit_url, data)

        # Verify the response
        self.assertRedirects(
            response,
            self.profile_view_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        # Verify the updated user and profile data
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.city, "Los Angeles")
        
    def test_profile_edit_view_post_invalid_data(self):
        # Log in the user
        self.client.force_login(self.user)

        # Prepare invalid form data (missing required fields)
        data = {
            "first_name": "Tems",
            "last_name": "Verified",
            "email": "testverifieduser@example.com",
            "is_email_verified": True,
            "shipping_address": "VA",
            "postal_code": "456",
            "password": "testpassword",
            "city": "Los Angeles",
            "avatar": "/media/photos/2024/09/01/test_image.jpg",
            "phone": ""
        }
        

        # Make a POST request to the profile edit page
        response = self.client.post(self.profile_edit_url, data)
        # print(response)
        # print(response.context.get("user_form").errors)
        # print(response.context.get("profile_form").errors)

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/edit.html")

        # Verify form errors
        self.assertIsNotNone(response.context.get("user_form").errors)
        self.assertIsNotNone(response.context.get("profile_form").errors)
        
        # Verify the profile data is not updated
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Test")  # Original value
        