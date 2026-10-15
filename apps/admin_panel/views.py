"""
Custom Admin Panel Views — AI Job Readiness Platform
Enterprise-level admin dashboard with full analytics, management, and reporting.
"""
import json
from datetime import timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q, Max
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.conf import settings as django_settings

from .decorators import admin_required
from apps.authentication.models import CustomUser
from apps.dashboard.models import UserProfile
from apps.cv_analyzer.models import CVUpload, CVAnalysis
from apps.job_matching.models import JobDescription, JobMatch
from apps.assessment.models import UserSkill, Assessment
from apps.interview_prep.models import InterviewSession
from apps.career.models import CareerRecommendation
from apps.notifications.models import Notification

User = get_user_model()


# ─────────────────────────────────────────────────────────────
# DASHBOARD OVERVIEW
# ─────────────────────────────────────────────────────────────

@admin_required
def dashboard_view(request):
    """Main admin dashboard with KPIs, charts, and recent activity."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # ── KPI Cards ──
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    total_cvs = CVUpload.objects.count()
    total_analyses = CVAnalysis.objects.count()
    total_job_matches = JobMatch.objects.count()
    total_assessments = Assessment.objects.count()
    total_interview_sessions = InterviewSession.objects.count()
    total_career_recs = CareerRecommendation.objects.count()
    total_notifications = Notification.objects.count()
    avg_ats_score = CVAnalysis.objects.aggregate(avg=Avg('ats_score'))['avg'] or 0
    avg_overall_score = CVAnalysis.objects.aggregate(avg=Avg('overall_score'))['avg'] or 0
    avg_match_score = JobMatch.objects.aggregate(avg=Avg('match_score'))['avg'] or 0
    avg_readiness = Assessment.objects.aggregate(avg=Avg('readiness_score'))['avg'] or 0

    # ── User Growth (last 30 days) ──
    user_growth = (
        User.objects.filter(date_joined__gte=thirty_days_ago)
        .annotate(day=TruncDate('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    growth_labels = []
    growth_data = []
    growth_map = {str(r['day']): r['count'] for r in user_growth}
    for i in range(30):
        d = (now - timedelta(days=29 - i)).date()
        growth_labels.append(d.strftime('%b %d'))
        growth_data.append(growth_map.get(str(d), 0))

    # ── CV Uploads (last 30 days) ──
    cv_uploads_trend = (
        CVUpload.objects.filter(uploaded_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('uploaded_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    cv_map = {str(r['day']): r['count'] for r in cv_uploads_trend}
    cv_trend_data = [cv_map.get(str((now - timedelta(days=29 - i)).date()), 0) for i in range(30)]

    # ── Score Distribution ──
    score_ranges = {
        'Excellent (80-100)': CVAnalysis.objects.filter(overall_score__gte=80).count(),
        'Good (60-79)': CVAnalysis.objects.filter(overall_score__gte=60, overall_score__lt=80).count(),
        'Fair (40-59)': CVAnalysis.objects.filter(overall_score__gte=40, overall_score__lt=60).count(),
        'Poor (<40)': CVAnalysis.objects.filter(overall_score__lt=40).count(),
    }

    # ── Career Level Distribution ──
    career_levels = (
        Assessment.objects.values('career_level')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # ── Top Skills ──
    top_skills = (
        UserSkill.objects.values('skill_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # ── Recent Activity ──
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:8]
    recent_cvs = CVUpload.objects.select_related('user', 'analysis').order_by('-uploaded_at')[:8]
    recent_matches = JobMatch.objects.select_related('user', 'job_description').order_by('-created_at')[:6]

    # ── System Health ──
    users_with_cv = User.objects.filter(cv_uploads__isnull=False).distinct().count()
    users_with_assessment = User.objects.filter(assessments__isnull=False).distinct().count()
    unread_notifications = Notification.objects.filter(is_read=False).count()

    context = {
        'page_title': 'Admin Dashboard',
        # KPIs
        'total_users': total_users,
        'active_users': active_users,
        'new_users_30d': new_users_30d,
        'total_cvs': total_cvs,
        'total_analyses': total_analyses,
        'total_job_matches': total_job_matches,
        'total_assessments': total_assessments,
        'total_interview_sessions': total_interview_sessions,
        'total_career_recs': total_career_recs,
        'avg_ats_score': round(avg_ats_score, 1),
        'avg_overall_score': round(avg_overall_score, 1),
        'avg_match_score': round(avg_match_score, 1),
        'avg_readiness': round(avg_readiness, 1),
        # Charts
        'growth_labels': json.dumps(growth_labels),
        'growth_data': json.dumps(growth_data),
        'cv_trend_data': json.dumps(cv_trend_data),
        'score_distribution': json.dumps(score_ranges),
        'career_levels': json.dumps({r['career_level']: r['count'] for r in career_levels}),
        'top_skills': json.dumps([{'skill': r['skill_name'], 'count': r['count']} for r in top_skills]),
        # Recent activity
        'recent_users': recent_users,
        'recent_cvs': recent_cvs,
        'recent_matches': recent_matches,
        # System health
        'users_with_cv': users_with_cv,
        'users_with_assessment': users_with_assessment,
        'unread_notifications': unread_notifications,
        'cv_coverage': round(users_with_cv / max(total_users, 1) * 100, 1),
        'assessment_coverage': round(users_with_assessment / max(total_users, 1) * 100, 1),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─────────────────────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_required
def users_list_view(request):
    """List all users with search, filter, and pagination."""
    qs = User.objects.select_related('profile').order_by('-date_joined')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(email__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(username__icontains=q)
        )

    # Filters
    role_filter = request.GET.get('role', '')
    if role_filter:
        qs = qs.filter(role=role_filter)

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    # Annotate with counts
    qs = qs.annotate(
        cv_count=Count('cv_uploads', distinct=True),
        assessment_count=Count('assessments', distinct=True),
    )

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_title': 'User Management',
        'users': page,
        'total_count': qs.count(),
        'q': q,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/users/list.html', context)


@admin_required
def user_detail_view(request, pk):
    """View detailed user profile and activity."""
    user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    cvs = CVUpload.objects.filter(user=user).select_related('analysis').order_by('-uploaded_at')
    assessments = Assessment.objects.filter(user=user).order_by('-created_at')
    job_matches = JobMatch.objects.filter(user=user).select_related('job_description').order_by('-created_at')[:5]
    interview_sessions = InterviewSession.objects.filter(user=user).order_by('-created_at')[:5]
    career_recs = CareerRecommendation.objects.filter(user=user).order_by('-created_at')[:3]
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    skills = UserSkill.objects.filter(user=user).order_by('category', 'skill_name')

    from .models import ActivityLog
    activity_logs = ActivityLog.objects.filter(user=user).order_by('-created_at')[:20]

    context = {
        'page_title': f'User: {user.get_full_name() or user.email}',
        'target_user': user,
        'cvs': cvs,
        'assessments': assessments,
        'job_matches': job_matches,
        'interview_sessions': interview_sessions,
        'career_recs': career_recs,
        'notifications': notifications,
        'skills': skills,
        'activity_logs': activity_logs,
    }
    return render(request, 'admin_panel/users/detail.html', context)


@admin_required
@require_POST
def user_toggle_status_view(request, pk):
    """Toggle user active/inactive status."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('admin_panel:user_detail', pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    status = 'activated' if user.is_active else 'suspended'
    messages.success(request, f'User {user.email} has been {status}.')
    return redirect('admin_panel:user_detail', pk=pk)


@admin_required
@require_POST
def user_delete_view(request, pk):
    """Delete a user account."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_panel:users')
    email = user.email
    user.delete()
    messages.success(request, f'User {email} has been permanently deleted.')
    return redirect('admin_panel:users')


@admin_required
@require_POST
def user_make_admin_view(request, pk):
    """Grant or revoke admin role."""
    user = get_object_or_404(User, pk=pk)
    if user.role == 'admin':
        user.role = 'user'
        msg = f'{user.email} admin privileges revoked.'
    else:
        user.role = 'admin'
        msg = f'{user.email} granted admin privileges.'
    user.save(update_fields=['role'])
    messages.success(request, msg)
    return redirect('admin_panel:user_detail', pk=pk)


@admin_required
@require_POST
def user_bulk_action_view(request):
    """Bulk actions on users: activate, deactivate, delete."""
    action = request.POST.get('action', '')
    user_ids = request.POST.getlist('user_ids')
    if not user_ids:
        messages.warning(request, 'No users selected.')
        return redirect('admin_panel:users')

    users_qs = User.objects.filter(pk__in=user_ids)

    if action == 'activate':
        count = users_qs.exclude(pk=request.user.pk).update(is_active=True)
        messages.success(request, f'{count} user(s) activated.')
    elif action == 'deactivate':
        count = users_qs.exclude(pk=request.user.pk).update(is_active=False)
        messages.success(request, f'{count} user(s) deactivated.')
    elif action == 'delete':
        count = users_qs.exclude(pk=request.user.pk).count()
        users_qs.exclude(pk=request.user.pk).delete()
        messages.success(request, f'{count} user(s) deleted.')
    else:
        messages.error(request, f'Unknown action: {action}')

    from .utils import log_activity
    log_activity(request.user, 'update', f'Bulk {action} on {len(user_ids)} user(s)', 'User', None, request)
    return redirect('admin_panel:users')


# ─────────────────────────────────────────────────────────────
# CV MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_required
def cvs_list_view(request):
    """List all uploaded CVs with filters."""
    qs = CVUpload.objects.select_related('user', 'analysis').order_by('-uploaded_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(original_filename__icontains=q) | Q(user__email__icontains=q) |
            Q(user__first_name__icontains=q)
        )

    file_type = request.GET.get('file_type', '')
    if file_type:
        qs = qs.filter(file_type=file_type)

    has_analysis = request.GET.get('has_analysis', '')
    if has_analysis == 'yes':
        qs = qs.filter(analysis__isnull=False)
    elif has_analysis == 'no':
        qs = qs.filter(analysis__isnull=True)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    # Stats
    avg_score = CVAnalysis.objects.aggregate(avg=Avg('overall_score'))['avg'] or 0
    total_size = CVUpload.objects.aggregate(total=Sum('file_size'))['total'] or 0

    context = {
        'page_title': 'CV Management',
        'cvs': page,
        'total_count': qs.count(),
        'avg_score': round(avg_score, 1),
        'total_size_mb': round(total_size / (1024 * 1024), 1),
        'q': q,
        'file_type': file_type,
        'has_analysis': has_analysis,
    }
    return render(request, 'admin_panel/cvs/list.html', context)


@admin_required
def cv_detail_view(request, pk):
    """View CV details and analysis."""
    cv = get_object_or_404(CVUpload.objects.select_related('user', 'analysis'), pk=pk)
    scores_list = []
    if cv.has_analysis:
        a = cv.analysis
        scores_list = [
            ('ATS', a.ats_score, '#0d6efd'),
            ('Grammar', a.grammar_score, '#20c997'),
            ('Keywords', a.keyword_score, '#fd7e14'),
            ('Format', a.format_score, '#6f42c1'),
        ]
    context = {
        'page_title': f'CV: {cv.original_filename}',
        'cv': cv,
        'scores_list': scores_list,
    }
    return render(request, 'admin_panel/cvs/detail.html', context)


@admin_required
@require_POST
def cv_delete_view(request, pk):
    """Admin delete a CV."""
    cv = get_object_or_404(CVUpload, pk=pk)
    user_pk = cv.user.pk
    cv.delete()
    messages.success(request, 'CV deleted successfully.')
    return redirect('admin_panel:cvs')


# ─────────────────────────────────────────────────────────────
# JOB MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_required
def jobs_list_view(request):
    """List all job descriptions and matches."""
    qs = JobDescription.objects.select_related('user').annotate(
        match_count=Count('matches'),
        avg_score=Avg('matches__match_score'),
    ).order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(company__icontains=q) | Q(user__email__icontains=q))

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_title': 'Job Management',
        'jobs': page,
        'total_count': qs.count(),
        'total_matches': JobMatch.objects.count(),
        'avg_match': round(JobMatch.objects.aggregate(avg=Avg('match_score'))['avg'] or 0, 1),
        'q': q,
    }
    return render(request, 'admin_panel/jobs/list.html', context)


@admin_required
@require_POST
def job_delete_view(request, pk):
    """Admin delete a job description."""
    job = get_object_or_404(JobDescription, pk=pk)
    job.delete()
    messages.success(request, 'Job description deleted.')
    return redirect('admin_panel:jobs')


# ─────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────

@admin_required
def analytics_view(request):
    """Full analytics page with charts and trends."""
    now = timezone.now()
    ninety_days_ago = now - timedelta(days=90)

    # Monthly user registrations (last 6 months)
    monthly_users = (
        User.objects.filter(date_joined__gte=now - timedelta(days=180))
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_labels = [r['month'].strftime('%b %Y') for r in monthly_users]
    monthly_data = [r['count'] for r in monthly_users]

    # CV score distribution (histogram)
    score_buckets = []
    for low, high in [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]:
        count = CVAnalysis.objects.filter(overall_score__gte=low, overall_score__lt=high).count()
        score_buckets.append({'range': f'{low}-{high}', 'count': count})

    # Match score distribution
    match_buckets = []
    for low, high in [(0, 25), (25, 50), (50, 75), (75, 100)]:
        count = JobMatch.objects.filter(match_score__gte=low, match_score__lt=high).count()
        match_buckets.append({'range': f'{low}-{high}%', 'count': count})

    # Top job titles searched
    top_jobs = (
        JobDescription.objects.values('title')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Skill category breakdown
    skill_categories = (
        UserSkill.objects.values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Career level distribution
    career_levels = (
        Assessment.objects.values('career_level')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Assessment score averages
    score_avgs = Assessment.objects.aggregate(
        avg_readiness=Avg('readiness_score'),
        avg_technical=Avg('technical_score'),
        avg_soft=Avg('soft_skills_score'),
        avg_experience=Avg('experience_score'),
        avg_education=Avg('education_score'),
    )

    # Daily activity last 14 days
    daily_activity = []
    for i in range(14):
        d = (now - timedelta(days=13 - i)).date()
        daily_activity.append({
            'date': d.strftime('%b %d'),
            'cvs': CVUpload.objects.filter(uploaded_at__date=d).count(),
            'matches': JobMatch.objects.filter(created_at__date=d).count(),
            'assessments': Assessment.objects.filter(created_at__date=d).count(),
        })

    context = {
        'page_title': 'Analytics & Reports',
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        'score_buckets': json.dumps(score_buckets),
        'match_buckets': json.dumps(match_buckets),
        'top_jobs': json.dumps([{'title': r['title'], 'count': r['count']} for r in top_jobs]),
        'skill_categories': json.dumps({r['category']: r['count'] for r in skill_categories}),
        'career_levels': json.dumps({r['career_level']: r['count'] for r in career_levels}),
        'score_avgs': {k: round(v or 0, 1) for k, v in score_avgs.items()},
        'daily_activity': json.dumps(daily_activity),
        'daily_labels': json.dumps([d['date'] for d in daily_activity]),
        'daily_cvs': json.dumps([d['cvs'] for d in daily_activity]),
        'daily_matches': json.dumps([d['matches'] for d in daily_activity]),
        'daily_assessments': json.dumps([d['assessments'] for d in daily_activity]),
    }
    return render(request, 'admin_panel/analytics.html', context)


# ─────────────────────────────────────────────────────────────
# NOTIFICATIONS MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_required
def notifications_view(request):
    """Admin notification management — view and broadcast."""
    qs = Notification.objects.select_related('user').order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(user__email__icontains=q) | Q(message__icontains=q))

    type_filter = request.GET.get('type', '')
    if type_filter:
        qs = qs.filter(notification_type=type_filter)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_title': 'Notifications',
        'notifications': page,
        'total_count': qs.count(),
        'unread_count': Notification.objects.filter(is_read=False).count(),
        'q': q,
        'type_filter': type_filter,
        'notification_types': Notification.TYPE_CHOICES,
    }
    return render(request, 'admin_panel/notifications/list.html', context)


@admin_required
@require_POST
def broadcast_notification_view(request):
    """Send a notification to all users or a specific user, with optional email."""
    title = request.POST.get('title', '').strip()
    message = request.POST.get('message', '').strip()
    notif_type = request.POST.get('notification_type', 'info')
    target = request.POST.get('target', 'all')
    user_id = request.POST.get('user_id', '')
    send_email_too = request.POST.get('send_email') == 'on'

    if not title or not message:
        messages.error(request, 'Title and message are required.')
        return redirect('admin_panel:notifications')

    recipients = []
    if target == 'all':
        recipients = list(User.objects.filter(is_active=True))
        Notification.objects.bulk_create([
            Notification(user=u, title=title, message=message, notification_type=notif_type)
            for u in recipients
        ])
        messages.success(request, f'Notification sent to {len(recipients)} users.')
    elif target == 'user' and user_id:
        user = get_object_or_404(User, pk=user_id)
        Notification.objects.create(user=user, title=title, message=message, notification_type=notif_type)
        recipients = [user]
        messages.success(request, f'Notification sent to {user.email}.')
    else:
        messages.error(request, 'Invalid target.')
        return redirect('admin_panel:notifications')

    # Send email copies if requested
    if send_email_too and recipients:
        from django.core.mail import send_mail
        email_sent = 0
        for u in recipients:
            if u.email:
                try:
                    send_mail(
                        subject=f'[CareerAI] {title}',
                        message=message,
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[u.email],
                        fail_silently=True,
                    )
                    email_sent += 1
                except Exception:
                    pass
        if email_sent:
            messages.info(request, f'Email sent to {email_sent} recipient(s).')

    from .utils import log_activity
    log_activity(request.user, 'create', f'Broadcast notification: "{title}" to {len(recipients)} user(s)', 'Notification', None, request)
    return redirect('admin_panel:notifications')


@admin_required
@require_POST
def notification_delete_view(request, pk):
    """Delete a notification."""
    notif = get_object_or_404(Notification, pk=pk)
    notif.delete()
    messages.success(request, 'Notification deleted.')
    return redirect('admin_panel:notifications')


# ─────────────────────────────────────────────────────────────
# SKILLS MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_required
def skills_view(request):
    """Platform-wide skills overview."""
    top_skills = (
        UserSkill.objects.values('skill_name', 'category')
        .annotate(count=Count('id'), avg_prof=Avg('proficiency'))
        .order_by('-count')
    )

    q = request.GET.get('q', '').strip()
    if q:
        top_skills = top_skills.filter(skill_name__icontains=q)

    category_filter = request.GET.get('category', '')
    if category_filter:
        top_skills = top_skills.filter(category=category_filter)

    paginator = Paginator(top_skills, 30)
    page = paginator.get_page(request.GET.get('page', 1))

    skill_categories = (
        UserSkill.objects.values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    context = {
        'page_title': 'Skills Management',
        'skills': page,
        'total_count': top_skills.count(),
        'skill_categories': skill_categories,
        'categories': UserSkill.CATEGORY_CHOICES,
        'q': q,
        'category_filter': category_filter,
    }
    return render(request, 'admin_panel/skills.html', context)


# ─────────────────────────────────────────────────────────────
# ASSESSMENTS MANAGEMENT
# ─────────────────────────────────────────────────────────────

@admin_required
def assessments_view(request):
    """View all assessments with analytics."""
    qs = Assessment.objects.select_related('user').order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(user__email__icontains=q) | Q(user__first_name__icontains=q))

    level_filter = request.GET.get('level', '')
    if level_filter:
        qs = qs.filter(career_level=level_filter)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    stats = Assessment.objects.aggregate(
        avg_readiness=Avg('readiness_score'),
        avg_technical=Avg('technical_score'),
        avg_soft=Avg('soft_skills_score'),
    )

    context = {
        'page_title': 'Assessments',
        'assessments': page,
        'total_count': qs.count(),
        'stats': {k: round(v or 0, 1) for k, v in stats.items()},
        'career_levels': Assessment.CAREER_LEVEL_CHOICES,
        'q': q,
        'level_filter': level_filter,
    }
    return render(request, 'admin_panel/assessments.html', context)


# ─────────────────────────────────────────────────────────────
# INTERVIEW SESSIONS
# ─────────────────────────────────────────────────────────────

@admin_required
def interview_sessions_view(request):
    """View all interview prep sessions."""
    qs = InterviewSession.objects.select_related('user').order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(user__email__icontains=q) | Q(job_title__icontains=q))

    difficulty_filter = request.GET.get('difficulty', '')
    if difficulty_filter:
        qs = qs.filter(difficulty=difficulty_filter)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_title': 'Interview Sessions',
        'sessions': page,
        'total_count': qs.count(),
        'difficulties': InterviewSession.DIFFICULTY_CHOICES,
        'q': q,
        'difficulty_filter': difficulty_filter,
    }
    return render(request, 'admin_panel/interview_sessions.html', context)


# ─────────────────────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────

@admin_required
def recommendations_view(request):
    """View and manage career recommendations."""
    qs = CareerRecommendation.objects.select_related('user').order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(user__email__icontains=q) | Q(target_role__icontains=q))

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_title': 'Career Recommendations',
        'recommendations': page,
        'total_count': qs.count(),
        'q': q,
    }
    return render(request, 'admin_panel/recommendations.html', context)


@admin_required
@require_POST
def recommendation_delete_view(request, pk):
    """Delete a career recommendation."""
    rec = get_object_or_404(CareerRecommendation, pk=pk)
    user_email = rec.user.email
    rec.delete()
    from .utils import log_activity
    log_activity(request.user, 'delete', f'Deleted career recommendation for {user_email}', 'CareerRecommendation', pk, request)
    messages.success(request, 'Recommendation deleted.')
    return redirect('admin_panel:recommendations')


# ─────────────────────────────────────────────────────────────
# EXPORT / REPORTS
# ─────────────────────────────────────────────────────────────

@admin_required
def export_users_csv_view(request):
    """Export users list as CSV."""
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Email', 'First Name', 'Last Name', 'Role', 'Active', 'Date Joined', 'CV Count', 'Assessment Count'])
    users = User.objects.select_related('profile').annotate(
        cv_count=Count('cv_uploads', distinct=True),
        assessment_count=Count('assessments', distinct=True),
    ).order_by('-date_joined')
    for u in users:
        writer.writerow([
            u.pk, u.email, u.first_name, u.last_name, u.role,
            u.is_active, u.date_joined.strftime('%Y-%m-%d %H:%M'),
            u.cv_count, u.assessment_count,
        ])
    return response


@admin_required
def export_cvs_csv_view(request):
    """Export CV analysis data as CSV."""
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cv_analysis_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'User Email', 'Filename', 'File Type', 'Overall Score', 'ATS Score', 'Grammar Score', 'Keyword Score', 'Format Score', 'Uploaded At'])
    cvs = CVUpload.objects.select_related('user', 'analysis').order_by('-uploaded_at')
    for cv in cvs:
        analysis = getattr(cv, 'analysis', None)
        writer.writerow([
            cv.pk, cv.user.email, cv.original_filename, cv.file_type,
            round(analysis.overall_score, 1) if analysis else '',
            round(analysis.ats_score, 1) if analysis else '',
            round(analysis.grammar_score, 1) if analysis else '',
            round(analysis.keyword_score, 1) if analysis else '',
            round(analysis.format_score, 1) if analysis else '',
            cv.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


# ─────────────────────────────────────────────────────────────
# AJAX API ENDPOINTS
# ─────────────────────────────────────────────────────────────

@admin_required
def api_stats_view(request):
    """Real-time stats API for dashboard widgets."""
    return JsonResponse({
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_cvs': CVUpload.objects.count(),
        'total_analyses': CVAnalysis.objects.count(),
        'total_matches': JobMatch.objects.count(),
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    })


# ─────────────────────────────────────────────────────────────
# AI MONITORING
# ─────────────────────────────────────────────────────────────

@admin_required
def ai_monitoring_view(request):
    """Monitor AI API usage, recent calls, and errors."""
    from .models import ActivityLog
    recent_ai_logs = ActivityLog.objects.filter(
        Q(description__icontains='AI') | Q(description__icontains='analysis') |
        Q(description__icontains='assessment') | Q(description__icontains='recommendation')
    ).select_related('user').order_by('-created_at')[:30]

    from django.db.models import Count
    action_counts = ActivityLog.objects.filter(
        Q(description__icontains='AI') | Q(description__icontains='analysis') |
        Q(description__icontains='assessment') | Q(description__icontains='recommendation')
    ).values('action_type').annotate(count=Count('id'))

    context = {
        'page_title': 'AI Monitoring',
        'recent_ai_logs': recent_ai_logs,
        'action_counts': action_counts,
    }
    return render(request, 'admin_panel/ai_monitoring.html', context)


# ─────────────────────────────────────────────────────────────
# ACTIVITY LOGS
# ─────────────────────────────────────────────────────────────

@admin_required
def activity_logs_view(request):
    """View and filter activity logs."""
    from .models import ActivityLog
    qs = ActivityLog.objects.select_related('user').order_by('-created_at')

    action_filter = request.GET.get('action', '')
    if action_filter:
        qs = qs.filter(action_type=action_filter)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(description__icontains=q) |
            Q(user__email__icontains=q) |
            Q(user__first_name__icontains=q)
        )

    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_title': 'Activity Logs',
        'logs': page,
        'total_count': qs.count(),
        'action_types': ActivityLog.ACTION_TYPES,
        'action_filter': action_filter,
        'q': q,
    }
    return render(request, 'admin_panel/activity_logs.html', context)


@admin_required
def export_activity_logs_csv_view(request):
    """Export activity logs as CSV."""
    import csv
    from .models import ActivityLog
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="activity_logs_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Action', 'Description', 'Model', 'Object ID', 'IP Address', 'Timestamp'])
    logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:5000]
    for log in logs:
        writer.writerow([
            log.pk, str(log.user) if log.user else 'Anonymous',
            log.get_action_type_display(), log.description,
            log.model_name, log.object_id, log.ip_address,
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    return response


# ─────────────────────────────────────────────────────────────
# SYSTEM SETTINGS
# ─────────────────────────────────────────────────────────────

@admin_required
def settings_view(request):
    """View and manage system settings."""
    from .models import SystemSetting
    settings_qs = SystemSetting.objects.all().order_by('key')

    # Create default settings if none exist
    if not settings_qs.exists():
        defaults = [
            ('site_name', 'Site Name', 'AI Job Readiness Platform', 'text', 'The name of the platform'),
            ('max_cv_file_size', 'Max CV File Size (MB)', '5', 'number', 'Maximum upload size for CV files'),
            ('enable_registration', 'Enable Registration', 'True', 'boolean', 'Allow new user registrations'),
            ('maintenance_mode', 'Maintenance Mode', 'False', 'boolean', 'Put the site in maintenance mode'),
            ('notifications_enabled', 'Enable Notifications', 'True', 'boolean', 'Enable in-app notifications'),
            ('default_from_email', 'Default From Email', django_settings.DEFAULT_FROM_EMAIL, 'email', 'Default sender email address'),
            ('items_per_page', 'Items Per Page', '20', 'number', 'Default pagination count'),
            # Security settings
            ('password_min_length', 'Min Password Length', '8', 'number', 'Minimum password length requirement'),
            ('max_login_attempts', 'Max Login Attempts', '5', 'number', 'Failed login attempts before lockout'),
            ('session_timeout', 'Session Timeout (mins)', '120', 'number', 'Session expiry in minutes'),
            ('enforce_email_verification', 'Enforce Email Verification', 'True', 'boolean', 'Require verified email to access features'),
            # AI monitoring config
            ('ai_request_timeout', 'AI Request Timeout (sec)', '30', 'number', 'Timeout for AI API calls'),
            ('ai_model', 'AI Model', 'gpt-4o-mini', 'text', 'OpenAI model to use'),
        ]
        for key, label, value, stype, desc in defaults:
            SystemSetting.objects.create(key=key, label=label, value=value, setting_type=stype, description=desc)
        settings_qs = SystemSetting.objects.all().order_by('key')

    context = {
        'page_title': 'System Settings',
        'settings': settings_qs,
    }
    return render(request, 'admin_panel/settings.html', context)


@admin_required
@require_POST
def settings_update_view(request, pk):
    """Update a system setting."""
    from .models import SystemSetting
    setting = get_object_or_404(SystemSetting, pk=pk)
    value = request.POST.get('value', '').strip()
    setting.value = value
    setting.save()
    messages.success(request, f'"{setting.label}" updated successfully.')
    return redirect('admin_panel:settings')


# ─────────────────────────────────────────────────────────────
# ADDITIONAL EXPORTS
# ─────────────────────────────────────────────────────────────

@admin_required
def export_career_recs_csv_view(request):
    """Export career recommendations as CSV."""
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="career_recommendations_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Target Role', 'Summary', 'Created'])
    recs = CareerRecommendation.objects.select_related('user').order_by('-created_at')[:5000]
    for r in recs:
        writer.writerow([r.pk, r.user.email, r.target_role, r.ai_summary[:200] if r.ai_summary else '', r.created_at.strftime('%Y-%m-%d')])
    return response


@admin_required
def export_assessments_csv_view(request):
    """Export assessments as CSV."""
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assessments_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Readiness', 'Technical', 'Soft Skills', 'Career Level', 'Created'])
    assessments = Assessment.objects.select_related('user').order_by('-created_at')[:5000]
    for a in assessments:
        writer.writerow([a.pk, a.user.email, a.readiness_score, a.technical_score, a.soft_skills_score, a.career_level, a.created_at.strftime('%Y-%m-%d')])
    return response
