"""Helpers for email OTP device verification (used after Google login)."""
import logging
import secrets

from django.conf import settings
from django.core.signing import BadSignature, TimestampSigner
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from .models import EmailOTP

logger = logging.getLogger(__name__)

DEVICE_COOKIE = 'careerai_device'
DEVICE_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days
OTP_LIFETIME_SECONDS = 5 * 60  # 5 minutes


def _signer():
    return TimestampSigner(salt='careerai-device-trust')


def device_trusted(request, user):
    """Return True if this device was previously verified for the user."""
    value = request.COOKIES.get(DEVICE_COOKIE, '')
    if not value:
        return False
    try:
        signed_user_pk = _signer().unsign(value, max_age=DEVICE_COOKIE_MAX_AGE)
    except BadSignature:
        return False
    return signed_user_pk == str(user.pk)


def set_device_trust(response, user):
    """Mark the response's device cookie as verified for the user."""
    response.set_cookie(
        DEVICE_COOKIE,
        _signer().sign(str(user.pk)),
        max_age=DEVICE_COOKIE_MAX_AGE,
        httponly=True,
        samesite='Lax',
    )


def clear_device_trust(response):
    response.delete_cookie(DEVICE_COOKIE)


def mask_email(email):
    """Mask an email for display, e.g. j***@example.com."""
    if not email or '@' not in email:
        return email or ''
    local, _, domain = email.partition('@')
    if len(local) <= 1:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    return f'{masked_local}@{domain}'


def generate_otp(user):
    """Create + send a fresh OTP for the user. Returns the EmailOTP instance."""
    # Invalidate any unused codes for this user.
    EmailOTP.objects.filter(user=user, is_used=False).update(is_used=True)
    code = f'{secrets.randbelow(1000000):06d}'
    otp = EmailOTP.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timezone.timedelta(seconds=OTP_LIFETIME_SECONDS),
    )
    return otp


def send_otp_email(user, otp):
    """Send the OTP to the user's email address. Returns True if the email was sent."""
    subject = 'Your CareerAI login code'
    first_name = user.first_name or user.username or 'there'
    html_body = loader.render_to_string('emails/otp_email.html', {
        'first_name': first_name,
        'otp_code': otp.code,
        'expires_in_minutes': OTP_LIFETIME_SECONDS // 60,
    })
    text_body = (
        f'Hi {first_name},\n\n'
        f'Your CareerAI login code is: {otp.code}\n'
        f'It expires in {OTP_LIFETIME_SECONDS // 60} minutes.\n\n'
        'If you did not request this, please ignore this email.\n\nCareerAI Team'
    )
    try:
        sent = send_mail(
            subject,
            text_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_body,
        )
        if sent:
            logger.info('OTP sent to %s (user %s)', user.email, otp.user_id)
            return True
        logger.warning('OTP not sent to %s (send_mail returned 0)', user.email)
        return False
    except Exception as exc:
        logger.error('OTP email to %s FAILED: %s', user.email, exc)
        # Development fallback: leak the code to the server log so the flow
        # can still be tested when email is misconfigured or slow.
        if settings.DEBUG:
            logger.warning('DEBUG OTP for %s: %s', user.email, otp.code)
        return False
