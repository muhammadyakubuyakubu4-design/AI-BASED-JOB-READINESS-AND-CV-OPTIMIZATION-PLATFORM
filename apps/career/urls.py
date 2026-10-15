from django.urls import path
from . import views

app_name = 'career'

urlpatterns = [
    path('', views.career_view, name='index'),
    path('recommendations/', views.career_recommendations_view, name='recommendations'),
    path('generate/', views.generate_recommendations_view, name='generate'),
    path('chatbot/', views.career_chatbot_view, name='chatbot'),
    path('cover-letter/', views.cover_letter_view, name='cover_letter'),
    path('cover-letter/create/', views.cover_letter_create_view, name='cover_letter_create'),
    path('cover-letter/<int:pk>/delete/', views.cover_letter_delete_view, name='cover_letter_delete'),
    path('cover-letter/<int:pk>/export/', views.cover_letter_export_view, name='cover_letter_export'),
    path('cover-letter/<int:pk>/scan/', views.cover_letter_scan_view, name='cover_letter_scan'),
]
