from django.urls import path

from reports import views

app_name = "reports"

urlpatterns = [
    path("", views.analytics_view, name="analytics"),
    path("data/", views.analytics_json, name="analytics-json"),
]
