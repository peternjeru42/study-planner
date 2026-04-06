from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RegistrationViewTests(TestCase):
    def test_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "student1",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "password1": "SafePassword123",
                "password2": "SafePassword123",
                "course": "Computer Science",
                "year_of_study": 2,
                "preferred_study_start_time": "18:00",
                "preferred_study_end_time": "21:00",
                "daily_study_goal_hours": "2.0",
                "break_duration_minutes": 15,
                "reminder_enabled": "on",
                "reminder_lead_minutes": 30,
                "deadline_reminder_hours": 24,
                "timezone": "Africa/Nairobi",
            },
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        user = User.objects.get(username="student1")
        self.assertEqual(user.profile.course, "Computer Science")
