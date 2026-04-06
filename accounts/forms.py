from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from accounts.models import StudentProfile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"placeholder": "you@example.com", "autocomplete": "email"})
        self.fields["first_name"].widget.attrs.update({"placeholder": "First name", "autocomplete": "given-name"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "Last name", "autocomplete": "family-name"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Create a password", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm your password", "autocomplete": "new-password"})
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"placeholder": "First name"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "Last name"})
        self.fields["email"].widget.attrs.update({"placeholder": "you@example.com"})
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError("This email is already used by another account.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})

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


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email address")

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "you@example.com", "autocomplete": "email"})
        self.fields["password"].widget.attrs.update({"placeholder": "Enter your password", "autocomplete": "current-password"})
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
