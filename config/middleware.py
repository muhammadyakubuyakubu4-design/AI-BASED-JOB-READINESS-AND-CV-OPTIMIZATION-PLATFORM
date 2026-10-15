"""Maintenance mode middleware - checks SystemSetting before serving pages."""

from django.shortcuts import render
from django.conf import settings


class MaintenanceModeMiddleware:
    """If SystemSetting 'maintenance_mode' is True, block non-admin requests."""

    EXEMPT_URLS = [
        '/admin_panel/',
        '/login/',
        '/authentication/login/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for admin users, staff, and exempt paths
        if request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
            return self.get_response(request)

        path = request.path_info
        if any(path.startswith(url) for url in self.EXEMPT_URLS):
            return self.get_response(request)

        # Check maintenance mode setting (cache-friendly via DB lookup)
        try:
            from apps.admin_panel.models import SystemSetting
            setting = SystemSetting.objects.filter(key='maintenance_mode').first()
            if setting and setting.value == 'True':
                return render(request, '503.html', status=503)
        except Exception:
            pass

        return self.get_response(request)
