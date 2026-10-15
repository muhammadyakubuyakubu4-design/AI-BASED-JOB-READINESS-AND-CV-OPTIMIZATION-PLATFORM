from django import forms
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserUpdateForm(forms.ModelForm):
    """Form to update basic user account info."""

    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    """Form to update the extended user profile."""

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar', 'phone', 'location',
            'current_role', 'target_role', 'years_experience',
            'linkedin_url', 'github_url', 'portfolio_url',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell us about yourself...',
            }),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 234 567 8900',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country',
            }),
            'current_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Software Developer',
            }),
            'target_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Senior Data Scientist',
            }),
            'years_experience': forms.Select(attrs={'class': 'form-select'}),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/yourprofile',
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/yourusername',
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourportfolio.com',
            }),
        }
