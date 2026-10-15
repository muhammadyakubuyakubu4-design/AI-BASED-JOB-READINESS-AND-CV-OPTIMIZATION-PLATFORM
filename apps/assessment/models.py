from django.db import models
from django.conf import settings


class UserSkill(models.Model):
    """Skills that a user has self-assessed or been assessed on."""

    PROFICIENCY_CHOICES = [
        (1, 'Beginner'),
        (2, 'Elementary'),
        (3, 'Intermediate'),
        (4, 'Advanced'),
        (5, 'Expert'),
    ]

    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('soft', 'Soft Skills'),
        ('language', 'Language'),
        ('tool', 'Tools & Software'),
        ('certification', 'Certification'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    skill_name = models.CharField(max_length=100)
    proficiency = models.IntegerField(choices=PROFICIENCY_CHOICES, default=1)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_skills'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'skill_name']
        ordering = ['category', 'skill_name']

    def __str__(self):
        return f"{self.skill_name} ({self.get_proficiency_display()})"


class Assessment(models.Model):
    """Job readiness assessment result for a user."""

    CAREER_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead/Manager'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessments'
    )

    readiness_score = models.FloatField(default=0.0)
    technical_score = models.FloatField(default=0.0)
    soft_skills_score = models.FloatField(default=0.0)
    experience_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)

    career_level = models.CharField(
        max_length=10, choices=CAREER_LEVEL_CHOICES, default='entry'
    )

    skill_gaps = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    action_plan = models.JSONField(default=list, blank=True)

    ai_summary = models.TextField(blank=True, default='')
    is_current = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'

    def __str__(self):
        return f"Assessment for {self.user.email} - Score: {self.readiness_score}"

    @property
    def readiness_label(self):
        if self.readiness_score >= 80:
            return ('Job Ready', 'success')
        elif self.readiness_score >= 60:
            return ('Nearly Ready', 'primary')
        elif self.readiness_score >= 40:
            return ('Developing', 'warning')
        else:
            return ('Early Stage', 'danger')
