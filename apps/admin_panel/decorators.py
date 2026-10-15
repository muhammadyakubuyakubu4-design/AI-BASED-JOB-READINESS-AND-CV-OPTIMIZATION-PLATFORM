"""
Admin panel access control decorators.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Restrict view to admin/superuser only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/auth/login/?next=' + request.path)
        if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
