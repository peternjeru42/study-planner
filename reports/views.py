from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from progress.services import compute_metrics, refresh_progress_snapshot


@login_required
def analytics_view(request):
    metrics = compute_metrics(request.user)
    return render(request, "reports/analytics.html", {"metrics": metrics})


@login_required
def analytics_json(request):
    refresh_progress_snapshot(request.user)
    return JsonResponse(compute_metrics(request.user))
