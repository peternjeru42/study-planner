from django import forms

from subjects.models import Subject


class SubjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Subject
        fields = (
            "subject_name",
            "subject_code",
            "instructor_name",
            "semester",
            "class_schedule",
            "color_tag",
        )
        widgets = {"color_tag": forms.TextInput(attrs={"type": "color"})}
