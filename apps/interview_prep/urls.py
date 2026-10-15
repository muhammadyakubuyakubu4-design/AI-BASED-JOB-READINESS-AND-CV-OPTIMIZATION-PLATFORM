from django.urls import path
from . import views

app_name = 'interview_prep'

urlpatterns = [
    path('', views.interview_prep_view, name='index'),
    path('session/<int:pk>/', views.interview_session_view, name='session'),
    path('history/', views.interview_history_view, name='history'),
    path('chat/', views.interview_chat_view, name='chat'),
    path('session/<int:pk>/mock/', views.mock_interview_view, name='mock'),
    path('session/<int:pk>/mock/submit/', views.mock_interview_submit_view, name='mock_submit'),
]
