from django import forms
from .models import InterviewSession


class InterviewSessionForm(forms.ModelForm):
    """Form to generate an interview preparation session."""

    class Meta:
        model = InterviewSession
        fields = ['job_title', 'company_name', 'industry', 'difficulty']
        widgets = {
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Data Scientist, Frontend Developer',
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name (optional)',
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Technology, Finance, Healthcare',
            }),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
        }
