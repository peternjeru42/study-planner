from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from subjects.forms import SubjectForm
from subjects.models import Subject


class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = "subjects/subject_list.html"
    context_object_name = "subjects"

    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user)


class SubjectCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
    success_url = reverse_lazy("subjects:list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Subject added.")
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
    success_url = reverse_lazy("subjects:list")

    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Subject updated.")
        return super().form_valid(form)


class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = "subjects/subject_confirm_delete.html"
    success_url = reverse_lazy("subjects:list")

    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Subject removed.")
        return super().form_valid(form)
