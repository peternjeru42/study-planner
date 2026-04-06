from django import forms

from planner.models import StudySession


class PlanPromptForm(forms.Form):
    prompt = forms.CharField(
        label="Describe the plan you want",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Create a study plan for Database Systems where I will be studying at least 10 hours a week.",
            }
        ),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["prompt"].widget.attrs.update({"class": "form-control planner-prompt-input"})

    def clean_prompt(self):
        prompt = self.cleaned_data["prompt"].strip()
        if len(prompt) < 20:
            raise forms.ValidationError("Describe the unit and weekly study goal in a bit more detail.")
        return prompt


class DraftSessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ("session_date", "start_time", "duration_minutes", "notes")
        widgets = {
            "session_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 30, "step": 30}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional notes"}),
        }
