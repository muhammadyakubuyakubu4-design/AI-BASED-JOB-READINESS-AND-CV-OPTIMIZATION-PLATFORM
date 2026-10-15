from django import forms


class StudyPlanForm(forms.Form):
    skill_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Data Analysis, Public Speaking'}),
        label='Skill to learn'
    )
    target_level = forms.ChoiceField(
        choices=[
            ('', 'Beginner (no experience)'),
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Your current level'
    )
