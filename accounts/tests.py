from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RegistrationViewTests(TestCase):
    def test_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "password1": "SafePassword123",
                "password2": "SafePassword123",
            },
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        user = User.objects.get(username="ada@example.com")
        self.assertEqual(user.email, "ada@example.com")
