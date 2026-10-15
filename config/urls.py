"""
Root URL Configuration for AI Job Readiness Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Custom Admin Panel
    path('admin_panel/', include('apps.admin_panel.urls')),

    # Landing page + dashboard routes (all paths handled within dashboard.urls)
    path('', include('apps.dashboard.urls')),

    # Authentication
    path('auth/', include('apps.authentication.urls')),

    # CV Analyzer
    path('cv/', include('apps.cv_analyzer.urls')),

    # Job Matching
    path('jobs/', include('apps.job_matching.urls')),

    # Assessment
    path('assessment/', include('apps.assessment.urls')),

    # Interview Preparation
    path('interview/', include('apps.interview_prep.urls')),

    # Career Recommendations
    path('career/', include('apps.career.urls')),

    # Learning
    path('learning/', include('apps.learning.urls')),

    # Notifications
    path('notifications/', include('apps.notifications.urls')),

    # Allauth (Google OAuth, etc.)
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site headers
admin.site.site_header = 'AI Job Readiness Admin'
admin.site.site_title = 'Job Readiness Portal'
admin.site.index_title = 'Administration Panel'
