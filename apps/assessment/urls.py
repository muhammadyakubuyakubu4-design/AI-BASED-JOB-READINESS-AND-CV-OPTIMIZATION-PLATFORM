from django.urls import path
from . import views

app_name = 'assessment'

urlpatterns = [
    path('', views.assessment_view, name='index'),
    path('result/<int:pk>/', views.assessment_result_view, name='result'),
    path('skills/', views.skills_view, name='skills'),
    path('skills/add/', views.skill_add_view, name='skill_add'),
    path('skills/<int:pk>/delete/', views.skill_delete_view, name='skill_delete'),
    path('run/', views.run_assessment_view, name='run'),
]
