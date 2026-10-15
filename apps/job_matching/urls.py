from django.urls import path
from . import views

app_name = 'job_matching'

urlpatterns = [
    path('', views.job_matching_view, name='matching'),
    path('result/<int:pk>/', views.job_match_result_view, name='result'),
    path('history/', views.job_match_history_view, name='history'),
    path('delete/<int:pk>/', views.job_match_delete_view, name='delete'),
    path('tracker/', views.job_tracker_view, name='tracker'),
    path('update-status/', views.update_job_status_view, name='update_status'),
]
