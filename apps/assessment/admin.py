from django.contrib import admin
from .models import UserSkill, Assessment


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill_name', 'get_proficiency', 'category', 'is_verified', 'added_at']
    list_filter = ['category', 'proficiency', 'is_verified']
    search_fields = ['user__email', 'skill_name']
    readonly_fields = ['added_at']

    @admin.display(description='Proficiency', ordering='proficiency')
    def get_proficiency(self, obj):
        return obj.get_proficiency_display()


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_readiness_score', 'career_level', 'get_technical_score', 'get_soft_skills_score', 'created_at']
    list_filter = ['career_level', 'created_at']
    search_fields = ['user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    @admin.display(description='Readiness Score', ordering='readiness_score')
    def get_readiness_score(self, obj):
        return f"{obj.readiness_score:.1f}%"

    @admin.display(description='Technical Score', ordering='technical_score')
    def get_technical_score(self, obj):
        return f"{obj.technical_score:.1f}%"

    @admin.display(description='Soft Skills Score', ordering='soft_skills_score')
    def get_soft_skills_score(self, obj):
        return f"{obj.soft_skills_score:.1f}%"
