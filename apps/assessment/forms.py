from django import forms
from .models import UserSkill


class UserSkillForm(forms.ModelForm):
    """Form to add or update a user skill."""

    class Meta:
        model = UserSkill
        fields = ['skill_name', 'proficiency', 'category']
        widgets = {
            'skill_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Python, Project Management',
            }),
            'proficiency': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class SkillBulkForm(forms.Form):
    """Form to add multiple skills at once from a text input."""

    skills_text = forms.CharField(
        label='Skills (comma-separated)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Python, Django, SQL, Machine Learning, ...',
        }),
        help_text='Enter skills separated by commas'
    )
    default_category = forms.ChoiceField(
        choices=UserSkill.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='technical'
    )
