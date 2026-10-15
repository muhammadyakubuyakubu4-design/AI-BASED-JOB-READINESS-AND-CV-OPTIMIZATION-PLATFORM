from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_role', 'location', 'get_years_experience', 'get_readiness_score']
    search_fields = ['user__email', 'user__username', 'current_role', 'location']
    list_filter = ['years_experience']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Experience', ordering='years_experience')
    def get_years_experience(self, obj):
        return obj.get_years_experience_display()

    @admin.display(description='Readiness Score', ordering='readiness_score')
    def get_readiness_score(self, obj):
        return f"{obj.readiness_score:.1f}%"
