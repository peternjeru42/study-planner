from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from assessments.forms import AssessmentForm
from assessments.models import Assessment
from planner.services import generate_plan
from progress.services import refresh_progress_snapshot


class AssessmentListView(LoginRequiredMixin, ListView):
    model = Assessment
    template_name = "assessments/assessment_list.html"
    context_object_name = "assessments"

    def get_queryset(self):
        return Assessment.objects.filter(user=self.request.user).select_related("subject")


class AssessmentCreateView(LoginRequiredMixin, CreateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = "assessments/assessment_form.html"
    success_url = reverse_lazy("assessments:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        generate_plan(self.request.user, trigger_reason="assessment_created")
        refresh_progress_snapshot(self.request.user)
        messages.success(self.request, "Assessment added and plan refreshed.")
        return response


class AssessmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = "assessments/assessment_form.html"
    success_url = reverse_lazy("assessments:list")

    def get_queryset(self):
        return Assessment.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        generate_plan(self.request.user, trigger_reason="assessment_updated")
        refresh_progress_snapshot(self.request.user)
        messages.success(self.request, "Assessment updated and plan refreshed.")
        return response


class AssessmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Assessment
    template_name = "assessments/assessment_confirm_delete.html"
    success_url = reverse_lazy("assessments:list")

    def get_queryset(self):
        return Assessment.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        generate_plan(self.request.user, trigger_reason="assessment_deleted")
        refresh_progress_snapshot(self.request.user)
        messages.success(self.request, "Assessment removed and plan refreshed.")
        return response
