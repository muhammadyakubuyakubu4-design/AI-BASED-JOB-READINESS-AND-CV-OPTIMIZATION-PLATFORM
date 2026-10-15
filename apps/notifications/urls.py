from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_view, name='index'),
    path('<int:pk>/read/', views.mark_read_view, name='mark_read'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('api/count/', views.notification_count_api, name='count_api'),
]
