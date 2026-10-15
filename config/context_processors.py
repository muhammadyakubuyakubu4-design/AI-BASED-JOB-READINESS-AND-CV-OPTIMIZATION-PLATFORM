"""
Global context processors for templates.
"""


def notifications_processor(request):
    """Inject unread notification count and recent notifications into all templates."""
    if request.user.is_authenticated:
        try:
            from apps.notifications.models import Notification
            unread_count = Notification.objects.filter(
                user=request.user, is_read=False
            ).count()
            recent_notifications = Notification.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
        except Exception:
            unread_count = 0
            recent_notifications = []
    else:
        unread_count = 0
        recent_notifications = []

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifications,
    }
