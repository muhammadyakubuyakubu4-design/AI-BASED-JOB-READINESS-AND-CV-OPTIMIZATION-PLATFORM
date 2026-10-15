from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extended user model with role-based access control."""

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, default='')
    is_deleted = models.BooleanField(default=False)
    last_active = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def full_name(self):
        return self.get_full_name() or self.username


class EmailOTP(models.Model):
    """One-time password sent by email to verify a new device."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_otps',
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    purpose = models.CharField(max_length=20, default='login')
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()
