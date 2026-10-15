from django.contrib import admin
from .models import StudyPlan, StudyPlanLesson, Quiz, QuizAttempt, LearningGoal


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'skill_name', 'get_progress', 'status', 'estimated_hours', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'skill_name', 'title']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Progress', ordering='progress_percent')
    def get_progress(self, obj):
        return f"{obj.progress_percent}%"


@admin.register(StudyPlanLesson)
class StudyPlanLessonAdmin(admin.ModelAdmin):
    list_display = ['plan', 'order', 'title', 'is_completed']
    list_filter = ['is_completed']
    search_fields = ['title', 'plan__skill_name']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['plan', 'title', 'total_questions', 'created_at']
    search_fields = ['title', 'plan__skill_name']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'get_percentage', 'passed', 'created_at']
    list_filter = ['passed', 'created_at']
    search_fields = ['user__email', 'quiz__title']

    @admin.display(description='Percentage', ordering='percentage')
    def get_percentage(self, obj):
        return f"{obj.percentage:.0f}%"


@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'goal_type', 'target', 'get_achieved', 'period_start', 'is_active']
    list_filter = ['goal_type', 'is_active']
    search_fields = ['user__email']

    @admin.display(description='Achieved', ordering='achieved')
    def get_achieved(self, obj):
        return f"{obj.achieved}/{obj.target}"
