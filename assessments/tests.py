from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assessments.models import Assessment
from planner.models import StudyPlan
from subjects.models import Subject


class AssessmentCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="testpass123")
        self.subject = Subject.objects.create(user=self.user, subject_name="Databases", color_tag="#BF4342")
        self.client.login(username="student", password="testpass123")

    def test_create_assessment_regenerates_plan(self):
        response = self.client.post(
            reverse("assessments:create"),
            {
                "subject": self.subject.pk,
                "title": "Normalization assignment",
                "assessment_type": Assessment.AssessmentType.ASSIGNMENT,
                "due_at": (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
                "weight": "20.0",
                "estimated_hours": "3.0",
                "status": Assessment.Status.PENDING,
                "notes": "Focus on 3NF and BCNF",
            },
        )
        self.assertRedirects(response, reverse("assessments:list"))
        self.assertTrue(Assessment.objects.filter(user=self.user, title="Normalization assignment").exists())
        self.assertTrue(StudyPlan.objects.filter(user=self.user, is_active=True).exists())
