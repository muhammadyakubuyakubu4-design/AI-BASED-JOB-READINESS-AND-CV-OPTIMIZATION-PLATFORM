from django.contrib import admin
from .models import CVUpload, CVAnalysis


@admin.register(CVUpload)
class CVUploadAdmin(admin.ModelAdmin):
    list_display = ['user', 'original_filename', 'file_type', 'get_file_size_kb', 'is_active', 'uploaded_at']
    list_filter = ['file_type', 'is_active', 'uploaded_at']
    search_fields = ['user__email', 'original_filename']
    readonly_fields = ['uploaded_at']
    date_hierarchy = 'uploaded_at'

    @admin.display(description='Size (KB)', ordering='file_size')
    def get_file_size_kb(self, obj):
        return f"{obj.file_size_kb} KB"


@admin.register(CVAnalysis)
class CVAnalysisAdmin(admin.ModelAdmin):
    list_display = ['cv_upload', 'get_overall_score', 'get_ats_score', 'get_grammar_score', 'analyzed_at']
    list_filter = ['analyzed_at']
    search_fields = ['cv_upload__user__email', 'cv_upload__original_filename']
    readonly_fields = ['analyzed_at', 'updated_at']
    date_hierarchy = 'analyzed_at'

    @admin.display(description='Overall Score', ordering='overall_score')
    def get_overall_score(self, obj):
        return f"{obj.overall_score:.1f}%"

    @admin.display(description='ATS Score', ordering='ats_score')
    def get_ats_score(self, obj):
        return f"{obj.ats_score:.1f}%"

    @admin.display(description='Grammar Score', ordering='grammar_score')
    def get_grammar_score(self, obj):
        return f"{obj.grammar_score:.1f}%"
