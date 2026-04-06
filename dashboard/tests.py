from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assessments.models import Assessment
from planner.services import generate_plan
from subjects.models import Subject


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dash-user", password="testpass123")
        self.subject = Subject.objects.create(user=self.user, subject_name="AI", color_tag="#1F7A8C")
        self.assessment = Assessment.objects.create(
            user=self.user,
            subject=self.subject,
            title="Neural nets quiz",
            due_at=timezone.now() + timedelta(days=2),
            weight=10,
            estimated_hours=1.5,
        )
        generate_plan(self.user, trigger_reason="test")
        self.client.login(username="dash-user", password="testpass123")

    def test_dashboard_and_metrics_endpoint_load(self):
        dashboard_response = self.client.get(reverse("dashboard:home"))
        metrics_response = self.client.get(reverse("dashboard:metrics-json"))
        calendar_response = self.client.get(reverse("planner:calendar-events"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(metrics_response.status_code, 200)
        self.assertIn("completed_tasks", metrics_response.json())
        self.assertEqual(calendar_response.status_code, 200)
