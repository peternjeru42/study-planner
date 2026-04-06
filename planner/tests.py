from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from assessments.models import Assessment
from planner.models import PlannerSettings, StudyPlan
from planner.services import generate_plan, generate_prompt_plan, score_assessment
from subjects.models import Subject


class PlannerServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="planner-user", password="testpass123")
        profile = self.user.profile
        profile.preferred_study_start_time = time(hour=18)
        profile.preferred_study_end_time = time(hour=19)
        profile.daily_study_goal_hours = Decimal("1.0")
        profile.break_duration_minutes = 10
        profile.save()
        self.subject = Subject.objects.create(user=self.user, subject_name="Networks", color_tag="#1F7A8C")
        self.settings = PlannerSettings.get_solo()

    def test_urgent_task_scores_higher(self):
        urgent = Assessment.objects.create(
            user=self.user,
            subject=self.subject,
            title="Urgent CAT",
            due_at=timezone.now() + timedelta(days=1),
            weight=20,
            estimated_hours=2,
        )
        later = Assessment.objects.create(
            user=self.user,
            subject=self.subject,
            title="Later project",
            due_at=timezone.now() + timedelta(days=7),
            weight=20,
            estimated_hours=2,
        )
        urgent_score, _ = score_assessment(urgent, self.settings)
        later_score, _ = score_assessment(later, self.settings)
        self.assertGreater(urgent_score, later_score)

    def test_generate_plan_flags_unscheduled_work_when_capacity_is_too_low(self):
        Assessment.objects.create(
            user=self.user,
            subject=self.subject,
            title="Big exam prep",
            due_at=timezone.now(),
            weight=40,
            estimated_hours=4,
        )
        plan = generate_plan(self.user, trigger_reason="test")
        self.assertIn("Unscheduled work", plan.notes)
        daily_minutes = sum(session.duration_minutes for session in plan.sessions.all() if session.session_date == timezone.localdate())
        self.assertLessEqual(daily_minutes, 60)

    def test_prompt_plan_creates_draft_with_requested_hours(self):
        profile = self.user.profile
        profile.preferred_study_end_time = time(hour=21)
        profile.save()
        plan = generate_prompt_plan(
            self.user,
            "Create a study plan for Networks where I will be studying at least 10 hours a week.",
        )
        self.assertEqual(plan.status, StudyPlan.Status.DRAFT)
        total_minutes = sum(session.duration_minutes for session in plan.sessions.all())
        self.assertGreaterEqual(total_minutes, 600)


class PlannerAdminTests(TestCase):
    def test_admin_planner_settings_page_loads(self):
        admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="AdminPass123")
        PlannerSettings.get_solo()
        client = Client()
        client.login(username="admin", password="AdminPass123")
        response = client.get(reverse("admin:planner_plannersettings_changelist"))
        self.assertEqual(response.status_code, 200)
