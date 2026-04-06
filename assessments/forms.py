from django import forms

from assessments.models import Assessment


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = (
            "subject",
            "title",
            "assessment_type",
            "due_at",
            "weight",
            "estimated_hours",
            "status",
            "notes",
        )
        widgets = {
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["subject"].queryset = user.subjects.all()
        if self.instance.pk and self.instance.due_at:
            self.initial["due_at"] = self.instance.due_at.strftime("%Y-%m-%dT%H:%M")
