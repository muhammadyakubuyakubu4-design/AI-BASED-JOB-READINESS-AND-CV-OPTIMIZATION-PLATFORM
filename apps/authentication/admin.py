from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, EmailOTP


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('Role & Permissions', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'purpose', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'purpose']
    search_fields = ['user__email', 'code']
    ordering = ['-created_at']
    readonly_fields = ['user', 'code', 'created_at', 'expires_at']
