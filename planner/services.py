from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from assessments.models import Assessment
from notifications.models import Notification
from planner.models import PlannerLog, PlannerSettings, StudyPlan, StudySession
from progress.services import refresh_progress_snapshot


def _combine(date_value, time_value):
    return datetime.combine(date_value, time_value)


def _normalize_fraction(value, max_value):
    if max_value <= 0:
        return Decimal("0")
    return min(Decimal(value) / Decimal(max_value), Decimal("1"))


def score_assessment(assessment, settings_obj, reference_date=None):
    reference_date = reference_date or timezone.localdate()
    completed_minutes = (
        StudySession.objects.filter(assessment=assessment, status=StudySession.Status.COMPLETED).aggregate(total=Sum("duration_minutes"))[
            "total"
        ]
        or 0
    )
    estimated_minutes = max(int(Decimal(assessment.estimated_hours) * Decimal("60")), settings_obj.default_session_minutes)
    remaining_minutes = max(estimated_minutes - completed_minutes, 0)
    days_left = (assessment.due_at.date() - reference_date).days
    urgency = Decimal("1") if days_left <= 0 else Decimal("1") / Decimal(days_left + 1)
    weight_component = _normalize_fraction(assessment.weight, 100)
    effort_component = _normalize_fraction(remaining_minutes, settings_obj.overload_threshold_minutes * 2)
    progress_gap = _normalize_fraction(remaining_minutes, estimated_minutes)

    score = (
        urgency * Decimal(settings_obj.urgency_weight)
        + weight_component * Decimal(settings_obj.assessment_weight)
        + effort_component * Decimal(settings_obj.effort_weight)
        + progress_gap * Decimal(settings_obj.progress_gap_weight)
    )
    return score.quantize(Decimal("0.01")), remaining_minutes


@transaction.atomic
def generate_plan(user, trigger_reason="manual", reference_date=None):
    reference_date = reference_date or timezone.localdate()
    horizon_end = reference_date + timedelta(days=6)
    settings_obj = PlannerSettings.get_solo()
    profile = user.profile
    day_start = profile.preferred_study_start_time or time(hour=18)
    day_end = profile.preferred_study_end_time or time(hour=21)
    session_minutes = settings_obj.default_session_minutes
    daily_goal_minutes = max(int(Decimal(profile.daily_study_goal_hours) * Decimal("60")), session_minutes)
    break_minutes = profile.break_duration_minutes

    StudyPlan.objects.filter(user=user, is_active=True).update(is_active=False)
    Notification.objects.filter(study_session__study_plan__user=user, study_session__study_plan__is_active=False, is_read=False).delete()

    plan = StudyPlan.objects.create(
        user=user,
        date_range_start=reference_date,
        date_range_end=horizon_end,
        trigger_reason=trigger_reason,
    )

    dates = [reference_date + timedelta(days=index) for index in range(7)]
    day_slots = {
        current_date: {"next_start": day_start, "used_minutes": 0, "order_index": 0}
        for current_date in dates
    }

    assessments = (
        Assessment.objects.filter(user=user)
        .exclude(status__in=[Assessment.Status.SUBMITTED, Assessment.Status.COMPLETED])
        .select_related("subject")
        .order_by("due_at")
    )

    scored_tasks = []
    for assessment in assessments:
        score, remaining_minutes = score_assessment(assessment, settings_obj, reference_date=reference_date)
        if remaining_minutes > 0:
            scored_tasks.append({"assessment": assessment, "score": score, "remaining_minutes": remaining_minutes})
    scored_tasks.sort(key=lambda item: (item["score"], -item["remaining_minutes"]), reverse=True)

    unscheduled = []
    for item in scored_tasks:
        assessment = item["assessment"]
        remaining_minutes = item["remaining_minutes"]
        due_date = max(reference_date, assessment.due_at.date())
        eligible_days = [current_date for current_date in dates if current_date <= min(due_date, horizon_end)] or dates

        while remaining_minutes > 0:
            allocation_made = False
            for current_date in eligible_days:
                slot = day_slots[current_date]
                proposed_duration = min(session_minutes, remaining_minutes, daily_goal_minutes - slot["used_minutes"])
                if proposed_duration <= 0:
                    continue
                session_start_dt = _combine(current_date, slot["next_start"])
                session_end_dt = session_start_dt + timedelta(minutes=proposed_duration)
                if session_end_dt > _combine(current_date, day_end):
                    continue

                StudySession.objects.create(
                    study_plan=plan,
                    subject=assessment.subject,
                    assessment=assessment,
                    session_date=current_date,
                    start_time=session_start_dt.time().replace(second=0, microsecond=0),
                    end_time=session_end_dt.time().replace(second=0, microsecond=0),
                    duration_minutes=proposed_duration,
                    priority_score=item["score"],
                    order_index=slot["order_index"],
                )
                slot["used_minutes"] += proposed_duration
                slot["order_index"] += 1
                slot["next_start"] = (session_end_dt + timedelta(minutes=break_minutes)).time().replace(second=0, microsecond=0)
                remaining_minutes -= proposed_duration
                allocation_made = True
                if remaining_minutes <= 0:
                    break
            if not allocation_made:
                unscheduled.append(f"{assessment.title} ({remaining_minutes} mins left)")
                break

    notes = "All tasks scheduled." if not unscheduled else "Unscheduled work: " + ", ".join(unscheduled)
    plan.notes = notes
    plan.save(update_fields=["notes"])

    PlannerLog.objects.create(user=user, trigger_reason=trigger_reason, success_status=True, notes=notes)
    refresh_progress_snapshot(user, reference_date=reference_date)
    return plan
