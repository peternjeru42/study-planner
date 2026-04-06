from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from assessments.models import Assessment
from planner.services import generate_plan
from subjects.models import Subject


class Command(BaseCommand):
    help = "Create a minimal demo student with sample subjects and assessments."

    def handle(self, *args, **options):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="demo_student",
            defaults={
                "email": "demo@student.local",
                "first_name": "Demo",
                "last_name": "Student",
            },
        )
        if created:
            user.set_password("demo12345")
            user.save()

        profile = user.profile
        profile.course = "BSc Computer Science"
        profile.year_of_study = 2
        profile.daily_study_goal_hours = Decimal("3.0")
        profile.break_duration_minutes = 15
        profile.save()

        subjects = [
            ("Data Structures", "CSC210", "#1F7A8C"),
            ("Database Systems", "CSC220", "#BF4342"),
            ("Statistics", "STA201", "#6A994E"),
        ]
        created_subjects = {}
        for name, code, color in subjects:
            subject, _ = Subject.objects.get_or_create(
                user=user,
                subject_name=name,
                defaults={"subject_code": code, "color_tag": color, "semester": "Semester 1"},
            )
            created_subjects[name] = subject

        base_due = timezone.now() + timedelta(days=1)
        sample_assessments = [
            ("Linked List Quiz", "Data Structures", Assessment.AssessmentType.QUIZ, 15, Decimal("2.0"), 1),
            ("Normalization Assignment", "Database Systems", Assessment.AssessmentType.ASSIGNMENT, 25, Decimal("4.0"), 3),
            ("Probability CAT", "Statistics", Assessment.AssessmentType.CAT, 20, Decimal("3.0"), 5),
        ]
        for title, subject_name, assessment_type, weight, estimated_hours, days in sample_assessments:
            Assessment.objects.get_or_create(
                user=user,
                subject=created_subjects[subject_name],
                title=title,
                defaults={
                    "assessment_type": assessment_type,
                    "due_at": base_due + timedelta(days=days),
                    "weight": weight,
                    "estimated_hours": estimated_hours,
                },
            )

        plan = generate_plan(user, trigger_reason="seed_demo_data")
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready for {user.username}. Password: demo12345. Active plan {plan.date_range_start} to {plan.date_range_end}."
            )
        )
