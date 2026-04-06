from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from assessments.models import Assessment
from notifications.models import Notification
from notifications.services import run_notification_checks
from planner.models import PlannerSettings, StudyPlan, StudySession
from subjects.models import Subject


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="notify-user", password="testpass123")
        self.subject = Subject.objects.create(user=self.user, subject_name="OS", color_tag="#6A994E")
        PlannerSettings.get_solo()
        self.assessment = Assessment.objects.create(
            user=self.user,
            subject=self.subject,
            title="Kernel assignment",
            due_at=timezone.now() + timedelta(hours=6),
            weight=15,
            estimated_hours=2,
        )
        plan = StudyPlan.objects.create(
            user=self.user,
            title="OS Draft",
            date_range_start=timezone.localdate(),
            date_range_end=timezone.localdate() + timedelta(days=6),
            trigger_reason="test",
            status=StudyPlan.Status.ACTIVE,
        )
        start = timezone.localtime(timezone.now() + timedelta(minutes=10))
        StudySession.objects.create(
            study_plan=plan,
            subject=self.subject,
            assessment=self.assessment,
            session_title="Kernel assignment focus",
            session_date=start.date(),
            start_time=start.time().replace(second=0, microsecond=0),
            end_time=(start + timedelta(minutes=60)).time().replace(second=0, microsecond=0),
            duration_minutes=60,
            priority_score="0.90",
        )

    def test_notification_generation_is_deduplicated(self):
        first_run = run_notification_checks()
        second_run = run_notification_checks()
        self.assertGreaterEqual(first_run, 1)
        self.assertEqual(second_run, 0)
        self.assertEqual(Notification.objects.count(), first_run)
