from django.db import models
from django.conf import settings


class Notification(models.Model):
    """In-app notifications for users."""

    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('cv', 'CV Analysis'),
        ('job', 'Job Match'),
        ('assessment', 'Assessment'),
        ('career', 'Career'),
        ('system', 'System'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='info'
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='normal'
    )
    link = models.CharField(max_length=500, blank=True, default='')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    @property
    def icon_class(self):
        icons = {
            'info': 'fa-info-circle text-info',
            'success': 'fa-check-circle text-success',
            'warning': 'fa-exclamation-triangle text-warning',
            'error': 'fa-times-circle text-danger',
            'cv': 'fa-file-alt text-primary',
            'job': 'fa-briefcase text-success',
            'assessment': 'fa-chart-bar text-info',
            'career': 'fa-road text-warning',
            'system': 'fa-cog text-secondary',
        }
        return icons.get(self.notification_type, 'fa-bell text-secondary')
