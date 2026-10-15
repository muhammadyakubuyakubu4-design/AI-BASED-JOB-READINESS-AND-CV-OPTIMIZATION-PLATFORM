import logging

from django.http import HttpResponseRedirect
from django.urls import reverse
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_field

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        return True

    def pre_login(self, request, user, **kwargs):
        """Intercept login (skipped OTP for development)."""
        return super().pre_login(request, user, **kwargs)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Google login: if the provider has already verified the incoming email
        and a local user owns that email but is not yet linked to this Google
        account, auto-connect. This skips allauth's "sign up to connect" form
        (which would bypass the OTP flow) and keeps the user on the OTP page.
        """
        if not sociallogin.is_existing:
            email_addresses = sociallogin.email_addresses or []
            for email_address in email_addresses:
                if not email_address.verified:
                    continue
                existing = self._find_existing_by_email(email_address.email)
                if existing is None:
                    continue
                sociallogin.connect(request, existing)
                break
        return super().pre_social_login(request, sociallogin)

    @staticmethod
    def _find_existing_by_email(email):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            try:
                from allauth.account.models import EmailAddress

                email_address = EmailAddress.objects.filter(
                    email__iexact=email
                ).select_related('user').first()
                return email_address.user if email_address else None
            except Exception:
                return None

    def pre_social_login2(self, request, sociallogin):
        return super().pre_social_login(request, sociallogin)

    def on_authentication_error(
        self, request, provider, error=None, exception=None, extra_context=None
    ):
        logger.error(
            "Social login failed: provider=%s error=%s",
            getattr(provider, 'id', '?') if provider is not None else '?',
            error,
            exc_info=exception,
        )
        return super().on_authentication_error(
            request, provider, error=error, exception=exception, extra_context=extra_context
        )

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        user.email_verified = True
        user.save(update_fields=['email_verified'])
        return user

    def get_redirect_url(self, request, sociallogin):
        user = sociallogin.user
        if hasattr(user, 'is_admin_user') and user.is_admin_user:
            return '/admin_panel/'
        return super().get_redirect_url(request, sociallogin)
