from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.learning_view, name='index'),
    path('create/', views.create_study_plan_view, name='create'),
    path('goal/update/', views.update_goal_view, name='update_goal'),
    path('plan/<int:pk>/', views.study_plan_view, name='plan'),
    path('plan/<int:pk>/delete/', views.delete_study_plan_view, name='delete'),
    path('plan/<int:pk>/lesson/<int:lesson_pk>/', views.lesson_view, name='lesson'),
    path('plan/<int:pk>/lesson/<int:lesson_pk>/complete/', views.complete_lesson_view, name='complete_lesson'),
    path('plan/<int:pk>/quiz/', views.quiz_view, name='quiz'),
    path('plan/<int:pk>/quiz/submit/', views.quiz_submit_view, name='quiz_submit'),
    path('plan/<int:pk>/quiz/result/<int:attempt_pk>/', views.quiz_result_view, name='quiz_result'),
]
