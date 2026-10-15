from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/profile/', views.profile_view, name='profile'),
    path('dashboard/profile/update/', views.profile_update_view, name='profile_update'),
    path('dashboard/progress/', views.progress_view, name='progress'),
    path('dashboard/report/', views.report_view, name='report'),
    path('dashboard/report/pdf/', views.report_download_pdf_view, name='report_pdf'),
]
