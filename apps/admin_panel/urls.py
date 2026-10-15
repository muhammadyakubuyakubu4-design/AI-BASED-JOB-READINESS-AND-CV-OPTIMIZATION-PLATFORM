from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    # Users
    path('users/', views.users_list_view, name='users'),
    path('users/<int:pk>/', views.user_detail_view, name='user_detail'),
    path('users/<int:pk>/toggle-status/', views.user_toggle_status_view, name='user_toggle_status'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
    path('users/<int:pk>/make-admin/', views.user_make_admin_view, name='user_make_admin'),
    path('users/bulk-action/', views.user_bulk_action_view, name='user_bulk_action'),

    # CVs
    path('cvs/', views.cvs_list_view, name='cvs'),
    path('cvs/<int:pk>/', views.cv_detail_view, name='cv_detail'),
    path('cvs/<int:pk>/delete/', views.cv_delete_view, name='cv_delete'),

    # Jobs
    path('jobs/', views.jobs_list_view, name='jobs'),
    path('jobs/<int:pk>/delete/', views.job_delete_view, name='job_delete'),

    # Analytics
    path('analytics/', views.analytics_view, name='analytics'),

    # Skills
    path('skills/', views.skills_view, name='skills'),

    # Assessments
    path('assessments/', views.assessments_view, name='assessments'),

    # Interview Sessions
    path('interviews/', views.interview_sessions_view, name='interviews'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/broadcast/', views.broadcast_notification_view, name='broadcast'),
    path('notifications/<int:pk>/delete/', views.notification_delete_view, name='notification_delete'),

    # Recommendations
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('recommendations/<int:pk>/delete/', views.recommendation_delete_view, name='recommendation_delete'),

    # AI Monitoring
    path('ai-monitoring/', views.ai_monitoring_view, name='ai_monitoring'),

    # Activity Logs
    path('activity-logs/', views.activity_logs_view, name='activity_logs'),
    path('activity-logs/export/', views.export_activity_logs_csv_view, name='export_activity_logs'),

    # System Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/<int:pk>/update/', views.settings_update_view, name='settings_update'),

    # Exports
    path('export/users/', views.export_users_csv_view, name='export_users'),
    path('export/cvs/', views.export_cvs_csv_view, name='export_cvs'),
    path('export/career-recommendations/', views.export_career_recs_csv_view, name='export_career_recs'),
    path('export/assessments/', views.export_assessments_csv_view, name='export_assessments'),

    # API
    path('api/stats/', views.api_stats_view, name='api_stats'),
]
