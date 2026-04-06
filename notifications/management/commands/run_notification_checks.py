from django.core.management.base import BaseCommand

from notifications.services import run_notification_checks


class Command(BaseCommand):
    help = "Simulate in-app reminder generation."

    def handle(self, *args, **options):
        created = run_notification_checks()
        self.stdout.write(self.style.SUCCESS(f"Created {created} notification(s)."))
