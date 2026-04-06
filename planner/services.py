import math
import re
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from assessments.models import Assessment
from notifications.models import Notification
from planner.models import PlannerLog, PlannerSettings, StudyPlan, StudySession
from progress.services import refresh_progress_snapshot
from subjects.models import Subject


def _combine(date_value, time_value):
    return datetime.combine(date_value, time_value)


def _normalize_fraction(value, max_value):
    if max_value <= 0:
        return Decimal("0")
    return min(Decimal(value) / Decimal(max_value), Decimal("1"))


def _study_minutes_in_window(day_start, day_end):
    return int((_combine(timezone.localdate(), day_end) - _combine(timezone.localdate(), day_start)).total_seconds() // 60)


def _plan_label(subject, prompt):
    if subject:
        return f"{subject.subject_name} Study Plan"
    return "AI Study Plan"


def _session_title(subject, assessment):
    if assessment:
        return assessment.title
    if subject:
        return f"{subject.subject_name} focused study"
    return "Focused study session"


def parse_plan_prompt(user, prompt):
    prompt_lower = prompt.lower()
    hours_match = re.search(r"(\d+(?:\.\d+)?)\s*hours?", prompt_lower)
    weekly_hours = Decimal(hours_match.group(1)) if hours_match else Decimal("10")
    matched_subject = None
    subjects = list(user.subjects.all())
    if len(subjects) == 1:
        matched_subject = subjects[0]
    else:
        for subject in subjects:
            tokens = [subject.subject_name.lower(), subject.subject_code.lower() if subject.subject_code else ""]
            if any(token and token in prompt_lower for token in tokens):
                matched_subject = subject
                break
    return {
        "subject": matched_subject,
        "weekly_hours": weekly_hours,
        "prompt": prompt,
    }


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

    StudyPlan.objects.filter(user=user, status=StudyPlan.Status.ACTIVE).update(status=StudyPlan.Status.ARCHIVED)
    Notification.objects.filter(
        study_session__study_plan__user=user,
        study_session__study_plan__status=StudyPlan.Status.ARCHIVED,
        is_read=False,
    ).delete()

    plan = StudyPlan.objects.create(
        user=user,
        title="Assessment Plan",
        date_range_start=reference_date,
        date_range_end=horizon_end,
        trigger_reason=trigger_reason,
        status=StudyPlan.Status.ACTIVE,
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
                    session_title=assessment.title,
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


@transaction.atomic
def generate_prompt_plan(user, prompt, trigger_reason="prompt_generation", reference_date=None):
    reference_date = reference_date or timezone.localdate()
    horizon_end = reference_date + timedelta(days=6)
    settings_obj = PlannerSettings.get_solo()
    profile = user.profile
    parsed = parse_plan_prompt(user, prompt)
    subject = parsed["subject"]
    weekly_hours = parsed["weekly_hours"]
    total_minutes = int(weekly_hours * Decimal("60"))
    day_start = profile.preferred_study_start_time or time(hour=18)
    day_end = profile.preferred_study_end_time or time(hour=21)
    break_minutes = profile.break_duration_minutes
    session_minutes = settings_obj.default_session_minutes
    day_capacity = _study_minutes_in_window(day_start, day_end)

    StudyPlan.objects.filter(user=user, status=StudyPlan.Status.DRAFT).update(status=StudyPlan.Status.ARCHIVED)
    plan = StudyPlan.objects.create(
        user=user,
        title=_plan_label(subject, prompt),
        prompt_text=prompt,
        weekly_hours_goal=weekly_hours,
        focus_subject=subject,
        date_range_start=reference_date,
        date_range_end=horizon_end,
        trigger_reason=trigger_reason,
        status=StudyPlan.Status.DRAFT,
        notes="Review this draft, edit any session that needs adjustment, then approve it.",
    )

    relevant_assessments = Assessment.objects.filter(user=user)
    if subject:
        relevant_assessments = relevant_assessments.filter(subject=subject)
    relevant_assessments = relevant_assessments.exclude(status__in=[Assessment.Status.SUBMITTED, Assessment.Status.COMPLETED]).order_by("due_at")
    prioritized_assessments = list(relevant_assessments[:10])

    days = [reference_date + timedelta(days=index) for index in range(7)]
    day_target = max(session_minutes, math.ceil(total_minutes / max(len(days), 1) / 30) * 30)
    remaining = total_minutes
    assessment_index = 0

    for current_day in days:
        if remaining <= 0:
            break
        allocated = 0
        next_start = day_start
        while remaining > 0 and allocated < min(day_target, day_capacity):
            duration = min(session_minutes, remaining, day_capacity - allocated)
            if duration <= 0:
                break
            start_dt = _combine(current_day, next_start)
            end_dt = start_dt + timedelta(minutes=duration)
            if end_dt > _combine(current_day, day_end):
                break
            assessment = prioritized_assessments[assessment_index % len(prioritized_assessments)] if prioritized_assessments else None
            StudySession.objects.create(
                study_plan=plan,
                subject=subject or (assessment.subject if assessment else user.subjects.first()),
                assessment=assessment,
                session_title=_session_title(subject or (assessment.subject if assessment else None), assessment),
                session_date=current_day,
                start_time=start_dt.time().replace(second=0, microsecond=0),
                end_time=end_dt.time().replace(second=0, microsecond=0),
                duration_minutes=duration,
                priority_score=Decimal("0.75"),
                order_index=allocated // session_minutes,
            )
            remaining -= duration
            allocated += duration
            next_start = (end_dt + timedelta(minutes=break_minutes)).time().replace(second=0, microsecond=0)
            assessment_index += 1
        if remaining <= 0:
            break

    if remaining > 0:
        plan.notes = f"{plan.notes} Remaining unscheduled time: {remaining} minutes because your preferred study window is too short."
        plan.save(update_fields=["notes"])

    PlannerLog.objects.create(
        user=user,
        trigger_reason=trigger_reason,
        success_status=True,
        notes=f"Draft plan created from prompt: {prompt}",
    )
    return plan


@transaction.atomic
def approve_plan(plan):
    StudyPlan.objects.filter(user=plan.user, status=StudyPlan.Status.ACTIVE).update(status=StudyPlan.Status.ARCHIVED)
    plan.status = StudyPlan.Status.ACTIVE
    plan.save(update_fields=["status"])
    PlannerLog.objects.create(user=plan.user, trigger_reason="plan_approved", success_status=True, notes=plan.title)
    refresh_progress_snapshot(plan.user)
    return plan
