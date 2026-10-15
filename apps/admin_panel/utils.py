"""Utility functions for the admin panel."""


def log_activity(user, action_type, description, model_name='', object_id=None, request=None, metadata=None):
    """Create an activity log entry."""
    from .models import ActivityLog
    kwargs = {
        'user': user,
        'action_type': action_type,
        'description': description,
        'model_name': model_name,
        'object_id': object_id,
        'metadata': metadata or {},
    }
    if request:
        kwargs['ip_address'] = _get_client_ip(request)
        kwargs['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
    ActivityLog.objects.create(**kwargs)


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
