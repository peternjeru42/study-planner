from django.urls import path

from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("metrics/", views.metrics_json, name="metrics-json"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:pk>/read/", views.notification_read_view, name="notification-read"),
]
