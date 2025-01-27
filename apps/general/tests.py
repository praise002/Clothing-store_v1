from django.test import TestCase, Client
from django.urls import reverse
from apps.general.models import SiteDetail, TeamMember, Message
from apps.general.forms import MessageForm


class TestGeneralViews(TestCase):
    about_url = reverse("general:about")
    contact_url = reverse("general:contact")

    def setUp(self):
        self.client = Client()
        self.sitedetail = SiteDetail.objects.create()
        self.teammember = TeamMember.objects.create(
            name="John Doe",
            role="Developer",
            description="Lorem",
            avatar="/media/photos/2024/09/01/test_image.jpg",
        )

    def test_about_view_get(self):
        # Make a GET request to the about page
        response = self.client.get(self.about_url)

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "general/about.html")

        # Verify context data
        self.assertEqual(response.context["sitedetail"], self.sitedetail)
        self.assertIn(self.teammember, response.context["teammembers"])

    def test_contact_view_get(self):
        # Make a GET request to the contact page
        response = self.client.get(self.contact_url)

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "general/contact.html")

        # Verify context data
        self.assertEqual(response.context["sitedetail"], self.sitedetail)
        self.assertIn(self.teammember, response.context["teammembers"])
        self.assertIsInstance(response.context["form"], MessageForm)

    def test_contact_view_post_valid_data(self):
        # Prepare valid form data
        data = {
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "subject": "This is a test subject.",
            "text": "This is a test message.",
        }

        # Make a POST request to the contact page
        response = self.client.post(self.contact_url, data)

        # Verify the response
        self.assertRedirects(
            response,
            self.contact_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        # Verify the message was saved
        self.assertTrue(Message.objects.filter(email="jane.doe@example.com").exists())
        
    def test_contact_view_post_invalid_data(self):
        # Prepare invalid form data (missing required fields)
        data = {
            "name": "Jane Doe",
            "email": "",  
            "text": "",
        }

        # Make a POST request to the contact page
        response = self.client.post(self.contact_url, data)
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "general/contact.html")

        # Verify form errors
        print(response.context.get("form").errors)
        self.assertTrue(response.context["form"].errors)

        # Verify the message was not saved
        self.assertFalse(Message.objects.filter(name="Jane Doe").exists())
