from django.urls import path

from subjects.views import SubjectCreateView, SubjectDeleteView, SubjectListView, SubjectUpdateView

app_name = "subjects"

urlpatterns = [
    path("", SubjectListView.as_view(), name="list"),
    path("new/", SubjectCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", SubjectUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", SubjectDeleteView.as_view(), name="delete"),
]
