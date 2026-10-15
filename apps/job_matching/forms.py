from django import forms
from .models import JobDescription


class JobDescriptionForm(forms.ModelForm):
    """Form for entering a job description to match against CV."""

    class Meta:
        model = JobDescription
        fields = ['title', 'company', 'location', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Senior Software Engineer',
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Google, Microsoft (optional)',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Remote, New York (optional)',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Paste the full job description here...',
            }),
        }
