from django.urls import path
from . import views

app_name = 'cv_analyzer'

urlpatterns = [
    path('upload/', views.cv_upload_view, name='upload'),
    path('history/', views.cv_history_view, name='history'),
    path('<int:pk>/analysis/', views.cv_analysis_view, name='analysis'),
    path('<int:pk>/reanalyze/', views.cv_reanalyze_view, name='reanalyze'),
    path('<int:pk>/export/', views.export_report_view, name='export'),
    path('<int:pk>/delete/', views.cv_delete_view, name='delete'),
    path('<int:pk>/set-active/', views.set_active_cv_view, name='set_active'),
    path('<int:pk>/download/', views.cv_download_view, name='download'),
    path('compare/', views.cv_compare_view, name='compare'),
    path('resume-templates/', views.resume_templates_view, name='resume_templates'),
    path('resume-templates/<int:pk>/<str:template_name>/', views.resume_preview_view, name='resume_preview'),
    path('resume-templates/<int:pk>/<str:template_name>/pdf/', views.resume_download_pdf_view, name='resume_download_pdf'),
    path('<int:pk>/enhance/', views.cv_enhance_view, name='enhance'),
    path('<int:pk>/match-jd/', views.cv_match_jd_view, name='match_jd'),
    path('<int:pk>/save-profile/', views.cv_save_profile_view, name='save_profile'),
    path('<int:pk>/render/', views.cv_render_view, name='render'),
    path('<int:pk>/optimize-bullets/<int:job_match_pk>/', views.optimize_bullets_view, name='optimize_bullets'),
]
