from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notifications_view(request):
    """List all notifications for the user."""
    notifications = Notification.objects.filter(user=request.user)
    # Mark all as read when viewing
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    context = {
        'page_title': 'Notifications',
        'notifications': notifications,
    }
    return render(request, 'notifications/index.html', context)


@login_required
def mark_read_view(request, pk):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:index')


@login_required
def mark_all_read_view(request):
    """Mark all notifications as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('notifications:index')


@login_required
def notification_count_api(request):
    """API endpoint for unread notification count (for AJAX polling)."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
