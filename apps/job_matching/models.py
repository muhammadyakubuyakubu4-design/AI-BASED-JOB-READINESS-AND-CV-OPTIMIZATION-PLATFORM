from django.db import models
from django.conf import settings


class JobDescription(models.Model):
    """A job description pasted by the user for matching."""

    JOB_TYPE_CHOICES = [
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('internship', 'Internship'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_descriptions'
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, blank=True, default='')
    salary_range = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField()
    is_archived = models.BooleanField(default=False)
    job_url = models.URLField(blank=True, default='', help_text='Original job posting URL for ATS detection')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Description'
        verbose_name_plural = 'Job Descriptions'

    def __str__(self):
        return f"{self.title} at {self.company}"


class JobMatch(models.Model):
    """Stores the result of matching a CV against a job description."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_matches'
    )
    cv_upload = models.ForeignKey(
        'cv_analyzer.CVUpload',
        on_delete=models.CASCADE,
        related_name='job_matches'
    )
    job_description = models.ForeignKey(
        JobDescription,
        on_delete=models.CASCADE,
        related_name='matches'
    )

    match_score = models.FloatField(default=0.0)

    matching_keywords = models.JSONField(default=list, blank=True)
    missing_keywords = models.JSONField(default=list, blank=True)
    matching_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    strength_areas = models.JSONField(default=list, blank=True)
    gap_areas = models.JSONField(default=list, blank=True)
    section_analysis = models.JSONField(default=list, blank=True)
    optimize_plan = models.JSONField(default=list, blank=True)

    ai_summary = models.TextField(blank=True, default='')
    is_saved = models.BooleanField(default=False)
    application_status = models.CharField(max_length=20, blank=True, default='', choices=[
        ('', 'Not Applied'),
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ])
    notes = models.TextField(blank=True, default='', help_text='Personal notes about this application')
    follow_up_date = models.DateField(null=True, blank=True, help_text='Date to follow up')
    ats_platform = models.CharField(max_length=50, blank=True, default='', help_text='Detected ATS platform')
    ats_tips = models.JSONField(default=list, blank=True, help_text='ATS-specific formatting tips')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Match'
        verbose_name_plural = 'Job Matches'

    def __str__(self):
        return f"{self.user.email} | {self.job_description.title} | {self.match_score}%"

    @property
    def match_label(self):
        if self.match_score >= 80:
            return ('Excellent Match', 'success')
        elif self.match_score >= 60:
            return ('Good Match', 'primary')
        elif self.match_score >= 40:
            return ('Partial Match', 'warning')
        else:
            return ('Low Match', 'danger')
