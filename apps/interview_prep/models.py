from django.db import models
from django.conf import settings


class InterviewSession(models.Model):
    """A generated interview preparation session."""

    DIFFICULTY_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_sessions'
    )
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True, default='')
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default='mid'
    )
    industry = models.CharField(max_length=100, blank=True, default='')

    behavioral_questions = models.JSONField(default=list, blank=True)
    technical_questions = models.JSONField(default=list, blank=True)
    situational_questions = models.JSONField(default=list, blank=True)
    general_tips = models.JSONField(default=list, blank=True)
    preparation_checklist = models.JSONField(default=list, blank=True)

    ai_notes = models.TextField(blank=True, default='')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Interview Session'
        verbose_name_plural = 'Interview Sessions'

    def __str__(self):
        return f"{self.user.email} - {self.job_title}"

    @property
    def total_questions(self):
        return (
            len(self.behavioral_questions) +
            len(self.technical_questions) +
            len(self.situational_questions)
        )


class MockInterviewResponse(models.Model):
    """A user's recorded answer to a mock interview question with feedback."""

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='mock_responses'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mock_interview_responses'
    )
    question_type = models.CharField(max_length=20)  # behavioral / technical / situational
    question = models.TextField()
    answer = models.TextField(blank=True, default='')
    feedback = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mock Interview Response'
        verbose_name_plural = 'Mock Interview Responses'

    def __str__(self):
        return f"{self.user.email} - {self.question_type} - {self.session.job_title}"

    @property
    def is_answered(self):
        return bool(self.answer.strip())
