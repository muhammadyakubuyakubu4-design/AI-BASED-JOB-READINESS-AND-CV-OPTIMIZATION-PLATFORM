from django.db import models
from django.conf import settings


class CareerRecommendation(models.Model):
    """AI-generated career recommendation for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='career_recommendations'
    )

    recommended_skills = models.JSONField(default=list, blank=True)
    recommended_courses = models.JSONField(default=list, blank=True)
    career_paths = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    job_titles = models.JSONField(default=list, blank=True)
    target_companies = models.JSONField(default=list, blank=True, help_text="List of recommended companies and URLs")
    learning_resources = models.JSONField(default=list, blank=True)

    current_skills_snapshot = models.JSONField(default=list, blank=True)
    target_role = models.CharField(max_length=200, blank=True, default='')

    ai_summary = models.TextField(blank=True, default='')
    is_current = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Career Recommendation'
        verbose_name_plural = 'Career Recommendations'

    def __str__(self):
        return f"Career recommendation for {self.user.email}"
