from django.urls import path
from django.contrib.auth.views import (
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views

app_name = 'authentication'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('otp/', views.otp_verify_view, name='otp_verify'),

    # Email verification
    path('verify-email/send/', views.send_verification_email_view, name='send_verification'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),

    # Password reset flow
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),
]
