from django.contrib import admin
from .models import CareerRecommendation


@admin.register(CareerRecommendation)
class CareerRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_role', 'get_skills_count', 'get_paths_count', 'created_at']
    search_fields = ['user__email', 'target_role']
    list_filter = ['created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    @admin.display(description='Recommended Skills')
    def get_skills_count(self, obj):
        return len(obj.recommended_skills)

    @admin.display(description='Career Paths')
    def get_paths_count(self, obj):
        return len(obj.career_paths)
