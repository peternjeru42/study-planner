from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from accounts.models import StudentProfile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = (
            "course",
            "year_of_study",
            "preferred_study_start_time",
            "preferred_study_end_time",
            "daily_study_goal_hours",
            "break_duration_minutes",
            "reminder_enabled",
            "reminder_lead_minutes",
            "deadline_reminder_hours",
            "timezone",
        )
        widgets = {
            "preferred_study_start_time": forms.TimeInput(attrs={"type": "time"}),
            "preferred_study_end_time": forms.TimeInput(attrs={"type": "time"}),
        }
