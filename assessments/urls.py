from django.urls import path

from assessments.views import AssessmentCreateView, AssessmentDeleteView, AssessmentListView, AssessmentUpdateView

app_name = "assessments"

urlpatterns = [
    path("", AssessmentListView.as_view(), name="list"),
    path("new/", AssessmentCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", AssessmentUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", AssessmentDeleteView.as_view(), name="delete"),
]
