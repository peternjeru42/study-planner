from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from subjects.models import Subject


class SubjectCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="testpass123")
        self.client.login(username="student", password="testpass123")

    def test_create_subject(self):
        response = self.client.post(
            reverse("subjects:create"),
            {
                "subject_name": "Algorithms",
                "subject_code": "CSC301",
                "instructor_name": "Dr. Doe",
                "semester": "Semester 1",
                "class_schedule": "Mon 08:00",
                "color_tag": "#1F7A8C",
            },
        )
        self.assertRedirects(response, reverse("subjects:list"))
        self.assertTrue(Subject.objects.filter(user=self.user, subject_name="Algorithms").exists())
