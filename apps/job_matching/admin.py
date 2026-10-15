from django.contrib import admin
from .models import JobDescription, JobMatch


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'user', 'created_at']
    search_fields = ['title', 'company', 'user__email']
    list_filter = ['created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_description', 'get_match_score', 'get_match_label', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'job_description__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    @admin.display(description='Match Score', ordering='match_score')
    def get_match_score(self, obj):
        return f"{obj.match_score:.1f}%"

    @admin.display(description='Match Label')
    def get_match_label(self, obj):
        label, _ = obj.match_label
        return label
