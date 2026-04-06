from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from assessments.models import Assessment
from planner.models import StudySession
from progress.models import ProgressSnapshot


def compute_metrics(user, reference_date=None):
    reference_date = reference_date or timezone.localdate()
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)

    assessments = Assessment.objects.filter(user=user)
    completed_statuses = [Assessment.Status.COMPLETED, Assessment.Status.SUBMITTED]
    completed_tasks = assessments.filter(status__in=completed_statuses).count()
    pending_tasks = assessments.exclude(status__in=completed_statuses).count()
    total_tasks = completed_tasks + pending_tasks
    completion_rate = (Decimal(completed_tasks) / Decimal(total_tasks) * Decimal("100")) if total_tasks else Decimal("0")

    weekly_sessions = StudySession.objects.filter(
        study_plan__user=user,
        session_date__range=(week_start, week_end),
        status=StudySession.Status.COMPLETED,
    )
    completed_minutes = weekly_sessions.aggregate(total=Sum("duration_minutes"))["total"] or 0
    study_hours = Decimal(completed_minutes) / Decimal("60")

    completed_assessments = assessments.filter(status__in=completed_statuses)
    on_time = completed_assessments.filter(completed_at__isnull=False, completed_at__lte=models.F("due_at")).count()
    completed_count = completed_assessments.count()
    deadline_compliance_rate = (
        Decimal(on_time) / Decimal(completed_count) * Decimal("100") if completed_count else Decimal("0")
    )

    raw_workload = assessments.values("subject__subject_name").annotate(total_hours=Sum("estimated_hours")).order_by("-total_hours")
    subject_workload = [
        {"subject__subject_name": row["subject__subject_name"], "total_hours": float(row["total_hours"] or 0)}
        for row in raw_workload
    ]
    study_consistency = []
    for index in range(7):
        current_day = week_start + timedelta(days=index)
        day_minutes = (
            StudySession.objects.filter(
                study_plan__user=user,
                session_date=current_day,
                status=StudySession.Status.COMPLETED,
            ).aggregate(total=Sum("duration_minutes"))["total"]
            or 0
        )
        study_consistency.append({"day": current_day.strftime("%a"), "hours": float(Decimal(day_minutes) / Decimal("60"))})

    return {
        "week_start": week_start,
        "week_end": week_end,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "study_hours": float(round(study_hours, 2)),
        "completion_rate": float(round(completion_rate, 2)),
        "deadline_compliance_rate": float(round(deadline_compliance_rate, 2)),
        "study_sessions_completed": weekly_sessions.count(),
        "tasks_completed_on_time": on_time,
        "subject_workload": subject_workload,
        "study_consistency": study_consistency,
    }


def refresh_progress_snapshot(user, reference_date=None):
    metrics = compute_metrics(user, reference_date=reference_date)
    snapshot, _ = ProgressSnapshot.objects.update_or_create(
        user=user,
        week_start=metrics["week_start"],
        defaults={
            "completed_tasks": metrics["completed_tasks"],
            "pending_tasks": metrics["pending_tasks"],
            "study_hours": metrics["study_hours"],
            "completion_rate": metrics["completion_rate"],
            "deadline_compliance_rate": metrics["deadline_compliance_rate"],
            "study_sessions_completed": metrics["study_sessions_completed"],
            "tasks_completed_on_time": metrics["tasks_completed_on_time"],
        },
    )
    return snapshot
