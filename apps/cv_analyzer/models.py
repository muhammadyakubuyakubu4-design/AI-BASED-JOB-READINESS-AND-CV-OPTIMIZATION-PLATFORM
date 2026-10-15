from django.db import models
from django.conf import settings


class CVUpload(models.Model):
    """Represents an uploaded CV file."""

    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cv_uploads'
    )
    file = models.FileField(upload_to='cv_uploads/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField(default=0, help_text='File size in bytes')
    parsed_text = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True, help_text='Currently selected CV')
    is_deleted = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'CV Upload'
        verbose_name_plural = 'CV Uploads'

    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    @property
    def file_size_kb(self):
        return round(self.file_size / 1024, 1)

    @property
    def has_analysis(self):
        return hasattr(self, 'analysis')


class CVAnalysis(models.Model):
    """Stores the AI analysis results for a CV."""

    cv_upload = models.OneToOneField(
        CVUpload,
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    ats_score = models.FloatField(default=0.0)
    grammar_score = models.FloatField(default=0.0)
    keyword_score = models.FloatField(default=0.0)
    format_score = models.FloatField(default=0.0)
    overall_score = models.FloatField(default=0.0)

    extracted_sections = models.JSONField(default=dict, blank=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    detected_keywords = models.JSONField(default=list, blank=True)
    contact_info = models.JSONField(default=dict, blank=True)

    suggestions = models.JSONField(default=list, blank=True)
    missing_sections = models.JSONField(default=list, blank=True)
    improvements = models.JSONField(default=list, blank=True)

    ai_feedback = models.TextField(blank=True, default='')
    bullet_feedback = models.JSONField(default=list, blank=True, help_text='Per-bullet-point AI feedback')

    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CV Analysis'
        verbose_name_plural = 'CV Analyses'

    def __str__(self):
        return f"Analysis for {self.cv_upload.original_filename}"

    @property
    def score_label(self):
        if self.overall_score >= 80:
            return ('Excellent', 'success')
        elif self.overall_score >= 60:
            return ('Good', 'primary')
        elif self.overall_score >= 40:
            return ('Fair', 'warning')
        else:
            return ('Poor', 'danger')


class CoverLetter(models.Model):
    """AI-generated cover letter for a job application."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cover_letters'
    )
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, default='')
    recipient_name = models.CharField(max_length=200, blank=True, default='')
    job_description = models.TextField(blank=True, default='')
    content = models.TextField(blank=True, default='')
    tone = models.CharField(max_length=20, default='professional', choices=[
        ('professional', 'Professional'),
        ('enthusiastic', 'Enthusiastic'),
        ('formal', 'Formal'),
        ('concise', 'Concise'),
    ])
    is_favorite = models.BooleanField(default=False)
    match_score = models.FloatField(default=0.0, help_text='Match score against a job description')
    keyword_analysis = models.JSONField(default=dict, blank=True, help_text='Keyword analysis vs job description')
    scan_job_description = models.ForeignKey(
        'job_matching.JobDescription',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cover_letter_scans',
        help_text='Job description this cover letter was scanned against'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cover Letter'
        verbose_name_plural = 'Cover Letters'

    def __str__(self):
        return f"Cover letter for {self.job_title} at {self.company_name}"
