from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from .forms import RegisterForm, LoginForm, CustomPasswordResetForm
from .models import EmailOTP
from . import otp as otp_helpers


def _send_verification_email(request, user):
    """Send verification email to user with HTML template."""
    verify_url = request.build_absolute_uri(
        reverse('authentication:verify_email', kwargs={'token': user.email_verification_token})
    )
    subject = 'Verify Your Email — CareerAI'
    text_body = f'Hi {user.first_name},\n\nPlease verify your email by clicking the link below:\n\n{verify_url}\n\nThis link expires after 24 hours.\n\nBest,\nCareerAI Team'
    try:
        html_body = loader.render_to_string('emails/verify_email.html', {
            'first_name': user.first_name,
            'verify_url': verify_url,
        })
        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
    except Exception:
        try:
            from django.core.mail import send_mail
            send_mail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        except Exception:
            pass


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Remove OTP flow; login immediately
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome, {user.first_name}! Registration successful.')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        if request.user.is_admin_user:
            return redirect('admin_panel:dashboard')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember_me = request.POST.get('remember_me')
            
            if not remember_me:
                request.session.set_expiry(0)  # Session expires on browser close
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            # Admin users go straight to the admin panel
            if user.is_admin_user:
                return redirect('admin_panel:dashboard')
            next_url = request.GET.get('next', 'dashboard:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('dashboard:landing')
    return redirect('dashboard:landing')


def password_reset_view(request):
    """Handle password reset request."""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='auth/password_reset_email.html',
                subject_template_name='auth/password_reset_subject.txt',
                html_email_template_name='emails/password_reset.html',
            )
            return redirect('authentication:password_reset_done')
    else:
        form = CustomPasswordResetForm()

    return render(request, 'auth/password_reset.html', {'form': form})


@login_required
def send_verification_email_view(request):
    """Generate and send email verification token."""
    user = request.user
    if user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('dashboard:dashboard')

    user.email_verification_token = get_random_string(48)
    user.save(update_fields=['email_verification_token'])

    try:
        _send_verification_email(request, user)
        messages.success(request, 'Verification email sent! Check your inbox.')
    except Exception:
        messages.error(request, 'Could not send verification email. Please try again later.')

    return redirect('dashboard:dashboard')


def verify_email_view(request, token):
    """Verify user email via token."""
    user = get_object_or_404(settings.AUTH_USER_MODEL, email_verification_token=token)
    if user.email_verified:
        messages.info(request, 'Email already verified.')
    else:
        user.email_verified = True
        user.email_verification_token = ''
        user.save(update_fields=['email_verified', 'email_verification_token'])
        messages.success(request, 'Email verified successfully!')
    return redirect('dashboard:dashboard')


def otp_verify_view(request):
    """Verify an emailed OTP to finish sign-in or sign-up on a new device."""
    pending_user_id = request.session.get('otp_pending_user_id')
    if not pending_user_id:
        messages.error(request, 'No pending sign-in found. Please sign in again.')
        return redirect('authentication:login')

    user = get_user_model()._default_manager.filter(pk=pending_user_id).first()
    if user is None:
        request.session.pop('otp_pending_user_id', None)
        messages.error(request, 'That account no longer exists. Please sign in again.')
        return redirect('authentication:login')

    latest = EmailOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()

    if request.method == 'POST':
        action = request.POST.get('action')
        code = request.POST.get('code', '').strip()

        if action == 'resend':
            otp = otp_helpers.generate_otp(user)
            otp_helpers.send_otp_email(user, otp)
            messages.success(request, 'A new code has been sent to your email.')
        else:
            if not latest or not latest.is_valid():
                messages.error(request, 'Your code has expired. Please request a new one.')
            elif code == latest.code:
                latest.is_used = True
                latest.save(update_fields=['is_used'])
                # OTP proves ownership of the email address
                if not user.email_verified:
                    user.email_verified = True
                    user.save(update_fields=['email_verified'])
                # Honor "remember me" from the login form
                remember_me = request.session.pop('otp_remember_me', None)
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires on browser close
                user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(request, user)
                request.session.pop('otp_pending_user_id', None)
                request.session.pop('otp_flow', None)
                # Trust this device for 30 days
                response = redirect('admin_panel:dashboard' if user.is_admin_user else 'dashboard:dashboard')
                otp_helpers.set_device_trust(response, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return response
            else:
                messages.error(request, 'Incorrect code. Please try again.')

    otp = EmailOTP.objects.filter(user=user, is_used=False).order_by('-created_at').first()
    if otp is None:
        otp = otp_helpers.generate_otp(user)
        otp_helpers.send_otp_email(user, otp)
        messages.info(request, 'We sent a sign-in code to your email.')
    elif not otp.is_valid():
        otp = otp_helpers.generate_otp(user)
        otp_helpers.send_otp_email(user, otp)
        messages.info(request, 'A new sign-in code has been sent to your email.')

    return render(request, 'auth/otp_verify.html', {
        'email_masked': otp_helpers.mask_email(user.email),
    })
