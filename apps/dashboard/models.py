from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended profile information for each user."""

    EXPERIENCE_CHOICES = [
        ('0', 'No Experience'),
        ('1', '0-1 years'),
        ('2', '1-3 years'),
        ('3', '3-5 years'),
        ('5', '5-10 years'),
        ('10', '10+ years'),
    ]

    EDUCATION_CHOICES = [
        ('high_school', 'High School'),
        ('associate', 'Associate Degree'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    current_role = models.CharField(max_length=100, blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    github_url = models.URLField(blank=True, default='')
    portfolio_url = models.URLField(blank=True, default='')
    years_experience = models.CharField(
        max_length=5, choices=EXPERIENCE_CHOICES, default='0'
    )
    target_role = models.CharField(max_length=100, blank=True, default='')
    target_industry = models.CharField(max_length=100, blank=True, default='')
    education_level = models.CharField(
        max_length=20, choices=EDUCATION_CHOICES, blank=True, default=''
    )
    field_of_study = models.CharField(max_length=100, blank=True, default='')
    institution = models.CharField(max_length=200, blank=True, default='')
    graduation_year = models.IntegerField(null=True, blank=True)
    readiness_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.svg'

    @property
    def readiness_label(self):
        if self.readiness_score >= 80:
            return ('Excellent', 'success')
        elif self.readiness_score >= 60:
            return ('Good', 'primary')
        elif self.readiness_score >= 40:
            return ('Moderate', 'warning')
        else:
            return ('Needs Work', 'danger')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile when a new user is registered."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile whenever the User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
