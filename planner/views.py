from collections import OrderedDict
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from assessments.models import Assessment
from planner.forms import DraftSessionForm, PlanPromptForm
from planner.models import StudyPlan, StudySession
from planner.services import approve_plan, generate_plan, generate_prompt_plan


def _group_sessions(plan):
    grouped = OrderedDict()
    if not plan:
        return grouped
    for session in plan.sessions.select_related("subject", "assessment"):
        grouped.setdefault(session.session_date, []).append(session)
    return grouped


@login_required
def weekly_plan_view(request):
    plan = (
        StudyPlan.objects.filter(user=request.user, status=StudyPlan.Status.ACTIVE)
        .prefetch_related("sessions__subject", "sessions__assessment")
        .first()
    )
    draft_plan = (
        StudyPlan.objects.filter(user=request.user, status=StudyPlan.Status.DRAFT)
        .prefetch_related("sessions__subject", "sessions__assessment")
        .first()
    )
    prompt_form = PlanPromptForm(request.user)
    return render(
        request,
        "planner/weekly_plan.html",
        {
            "plan": plan,
            "draft_plan": draft_plan,
            "grouped_sessions": _group_sessions(plan),
            "grouped_draft_sessions": _group_sessions(draft_plan),
            "prompt_form": prompt_form,
        },
    )


@login_required
def daily_plan_view(request, plan_date=None):
    current_date = datetime.strptime(plan_date, "%Y-%m-%d").date() if plan_date else None
    current_date = current_date or timezone.localdate()
    sessions = StudySession.objects.filter(
        study_plan__user=request.user,
        study_plan__status=StudyPlan.Status.ACTIVE,
        session_date=current_date,
    ).select_related("subject", "assessment")
    return render(request, "planner/daily_plan.html", {"plan_date": current_date, "sessions": sessions})


@login_required
def calendar_view(request):
    return render(request, "planner/calendar.html")


@login_required
def calendar_events_view(request):
    user = request.user
    assessment_events = [
        {
            "title": f"Deadline: {assessment.title}",
            "start": assessment.due_at.isoformat(),
            "url": f"/assessments/{assessment.pk}/edit/",
            "color": assessment.subject.color_tag,
        }
        for assessment in Assessment.objects.filter(user=user).select_related("subject")
    ]
    session_events = [
        {
            "title": f"Study: {session.session_title or (session.assessment.title if session.assessment else 'Study session')}",
            "start": datetime.combine(session.session_date, session.start_time).isoformat(),
            "end": datetime.combine(session.session_date, session.end_time).isoformat(),
            "color": session.subject.color_tag,
        }
        for session in StudySession.objects.filter(study_plan__user=user).select_related("subject", "assessment")
    ]
    return JsonResponse(assessment_events + session_events, safe=False)


@login_required
@require_POST
def generate_plan_view(request):
    plan = generate_plan(request.user, trigger_reason="manual_regeneration")
    messages.success(request, "Study plan generated.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "ok", "plan_id": plan.pk, "notes": plan.notes})
    return redirect("planner:weekly")


@login_required
@require_POST
def prompt_plan_view(request):
    if not request.user.subjects.exists():
        messages.error(request, "Add at least one unit before generating an AI study plan.")
        return redirect("subjects:create")

    form = PlanPromptForm(request.user, request.POST)
    if not form.is_valid():
        plan = StudyPlan.objects.filter(user=request.user, status=StudyPlan.Status.ACTIVE).first()
        draft_plan = StudyPlan.objects.filter(user=request.user, status=StudyPlan.Status.DRAFT).first()
        return render(
            request,
            "planner/weekly_plan.html",
            {
                "plan": plan,
                "draft_plan": draft_plan,
                "grouped_sessions": _group_sessions(plan),
                "grouped_draft_sessions": _group_sessions(draft_plan),
                "prompt_form": form,
            },
            status=400,
        )

    draft_plan = generate_prompt_plan(request.user, form.cleaned_data["prompt"])
    messages.success(request, "Draft AI study plan created. Review it, edit any session, then approve it.")
    return redirect("planner:weekly")


@login_required
@require_POST
def approve_plan_view(request, pk):
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user, status=StudyPlan.Status.DRAFT)
    approve_plan(plan)
    messages.success(request, "Study plan approved and added to your active plans.")
    return redirect("planner:weekly")


@login_required
def edit_session_view(request, pk):
    session = get_object_or_404(
        StudySession.objects.select_related("study_plan", "subject", "assessment"),
        pk=pk,
        study_plan__user=request.user,
        study_plan__status=StudyPlan.Status.DRAFT,
    )
    form = DraftSessionForm(request.POST or None, instance=session)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        start_dt = datetime.combine(updated.session_date, updated.start_time)
        updated.end_time = (start_dt + timedelta(minutes=updated.duration_minutes)).time()
        updated.save()
        messages.success(request, "Draft session updated.")
        return redirect("planner:weekly")
    return render(request, "planner/edit_session.html", {"form": form, "session": session})
