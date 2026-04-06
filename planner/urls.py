from django.urls import path

from planner import views

app_name = "planner"

urlpatterns = [
    path("weekly/", views.weekly_plan_view, name="weekly"),
    path("daily/", views.daily_plan_view, name="daily"),
    path("daily/<str:plan_date>/", views.daily_plan_view, name="daily-date"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/events/", views.calendar_events_view, name="calendar-events"),
    path("generate/", views.generate_plan_view, name="generate"),
    path("prompt/", views.prompt_plan_view, name="prompt"),
    path("approve/<int:pk>/", views.approve_plan_view, name="approve"),
    path("sessions/<int:pk>/edit/", views.edit_session_view, name="edit-session"),
]
