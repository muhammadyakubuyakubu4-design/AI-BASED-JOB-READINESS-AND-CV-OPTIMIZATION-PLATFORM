from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    """Audit log for tracking all significant platform actions."""

    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('upload', 'Upload'),
        ('analyze', 'Analyze'),
        ('export', 'Export'),
        ('generate', 'Generate'),
        ('send', 'Send'),
        ('view', 'View'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    model_name = models.CharField(max_length=100, blank=True, default='')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"[{self.get_action_type_display()}] {self.user or 'Anonymous'} - {self.description[:50]}"


class SystemSetting(models.Model):
    """Key-value store for system-wide configuration."""

    SETTING_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('email', 'Email'),
    ]

    key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    value = models.TextField(blank=True, default='')
    setting_type = models.CharField(max_length=10, choices=SETTING_TYPES, default='text')
    description = models.TextField(blank=True, default='')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return self.key

    @classmethod
    def get_value(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key)
            if setting.setting_type == 'boolean':
                return setting.value.lower() in ('true', '1', 'yes')
            if setting.setting_type == 'number':
                try:
                    return float(setting.value)
                except ValueError:
                    return default
            return setting.value
        except cls.DoesNotExist:
            return default
