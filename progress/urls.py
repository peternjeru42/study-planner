from django.urls import path

from progress import views

app_name = "progress"

urlpatterns = [
    path("sessions/<int:pk>/status/", views.session_status_update_view, name="session-status"),
    path("assessments/<int:pk>/status/", views.assessment_status_update_view, name="assessment-status"),
]
