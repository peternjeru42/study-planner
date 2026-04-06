from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from planner.services import generate_plan


class Command(BaseCommand):
    help = "Simulate the daily planner refresh for all students."

    def handle(self, *args, **options):
        count = 0
        for user in get_user_model().objects.filter(is_staff=False):
            generate_plan(user, trigger_reason="daily_refresh")
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Refreshed {count} study plan(s)."))
