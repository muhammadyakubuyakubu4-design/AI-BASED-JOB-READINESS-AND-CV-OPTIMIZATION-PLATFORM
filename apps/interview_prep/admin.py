from django.contrib import admin
from .models import InterviewSession, MockInterviewResponse


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_title', 'company_name', 'difficulty', 'get_total_questions', 'created_at']
    list_filter = ['difficulty', 'created_at']
    search_fields = ['user__email', 'job_title', 'company_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    @admin.display(description='Total Questions', ordering='job_title')
    def get_total_questions(self, obj):
        return obj.total_questions


@admin.register(MockInterviewResponse)
class MockInterviewResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'session', 'question_type', 'is_answered', 'created_at']
    list_filter = ['question_type', 'created_at']
    search_fields = ['user__email', 'question']
    readonly_fields = ['created_at']

    @admin.display(description='Answered', boolean=True)
    def is_answered(self, obj):
        return obj.is_answered
