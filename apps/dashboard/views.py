from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg
from .forms import UserUpdateForm, ProfileUpdateForm


def landing_view(request):
    """Public landing page."""
    if request.user.is_authenticated:
        if request.user.is_admin_user:
            return redirect('admin_panel:dashboard')
        return redirect('dashboard:dashboard')
    return render(request, 'landing.html')


@login_required
def dashboard_view(request):
    """Main user dashboard with stats and activity."""
    from apps.cv_analyzer.models import CVUpload, CVAnalysis
    from apps.job_matching.models import JobMatch
    from apps.assessment.models import Assessment, UserSkill
    from apps.interview_prep.models import InterviewSession
    from apps.career.models import CareerRecommendation
    from apps.notifications.models import Notification
    from django.db.models import Avg

    user = request.user
    profile = getattr(user, 'profile', None)

    # Counts
    cv_count = CVUpload.objects.filter(user=user, is_deleted=False).count()
    job_matches_count = JobMatch.objects.filter(user=user).count()
    assessments_count = Assessment.objects.filter(user=user).count()
    interview_count = InterviewSession.objects.filter(user=user).count()
    skill_count = UserSkill.objects.filter(user=user).count()

    # Latest entries
    recent_cvs = CVUpload.objects.filter(user=user, is_deleted=False).select_related('analysis')[:3]
    latest_assessment = Assessment.objects.filter(user=user).first()
    latest_match = JobMatch.objects.filter(user=user).select_related('job_description').first()
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]

    # Readiness & scores
    readiness_score = 0
    if latest_assessment:
        readiness_score = latest_assessment.readiness_score
    elif profile:
        readiness_score = profile.readiness_score

    avg_cv_score = CVAnalysis.objects.filter(cv_upload__user=user).aggregate(
        avg=Avg('overall_score'))['avg'] or 0
    avg_match_score = JobMatch.objects.filter(user=user).aggregate(
        avg=Avg('match_score'))['avg'] or 0

    # Score trend — last 5 CV analyses
    recent_analyses = CVAnalysis.objects.filter(cv_upload__user=user).order_by('-analyzed_at')[:5]
    score_trend = list(reversed([round(a.overall_score, 1) for a in recent_analyses]))
    trend_labels = [a.analyzed_at.strftime('%m/%d') for a in recent_analyses]

    # Activity history (last 7 days)
    from django.utils import timezone
    from datetime import timedelta
    import json

    week_ago = timezone.now() - timedelta(days=6)
    activity_data = []
    for i in range(7):
        day = week_ago + timedelta(days=i)
        day_label = day.strftime('%a')
        cv_uploads = CVUpload.objects.filter(
            user=user, uploaded_at__date=day.date()).count()
        job_matches = JobMatch.objects.filter(
            user=user, created_at__date=day.date()).count()
        assessments = Assessment.objects.filter(
            user=user, created_at__date=day.date()).count()
        activity_data.append({'day': day_label, 'cvs': cv_uploads, 'matches': job_matches, 'assessments': assessments})

    # Monthly progress data (last 6 months)
    import calendar
    monthly_scores = []
    month_labels = []
    for m in range(5, -1, -1):
        month = timezone.now().month - m
        year = timezone.now().year
        while month < 1:
            month += 12
            year -= 1
        month_labels.append(calendar.month_abbr[month])
        month_avg = CVAnalysis.objects.filter(
            cv_upload__user=user,
            analyzed_at__year=year,
            analyzed_at__month=month
        ).aggregate(avg=Avg('overall_score'))['avg'] or 0
        monthly_scores.append(round(month_avg, 1))

    # Learning data (weekly goal + active study plans)
    from apps.learning.models import StudyPlan, LearningGoal
    active_plans = StudyPlan.objects.filter(user=user).exclude(status='completed')
    learning_goal = LearningGoal.objects.filter(user=user).first()
    goal_progress = 0
    goal_remaining = 0
    goal_label = ''
    if learning_goal:
        learning_goal.refresh_progress()
        goal_progress = learning_goal.progress_percent()
        goal_remaining = max(learning_goal.target - learning_goal.achieved, 0)
        goal_label = learning_goal.get_goal_type_display()
    # Suggested skills to learn
    learning_suggestions = []
    latest_career_rec = CareerRecommendation.objects.filter(user=user).first()
    if latest_career_rec:
        rec_skills = latest_career_rec.recommended_skills if isinstance(latest_career_rec.recommended_skills, list) else []
        for s in rec_skills:
            if isinstance(s, str) and not StudyPlan.objects.filter(user=user, skill_name__iexact=s).exclude(status='completed').exists():
                learning_suggestions.append(s)
    learning_suggestions = learning_suggestions[:4]

    context = {
        'page_title': 'Dashboard',
        'cv_count': cv_count,
        'job_matches_count': job_matches_count,
        'assessments_count': assessments_count,
        'interview_count': interview_count,
        'skill_count': skill_count,
        'readiness_score': round(readiness_score, 0),
        'avg_cv_score': round(avg_cv_score, 1),
        'avg_match_score': round(avg_match_score, 1),
        'recent_cvs': recent_cvs,
        'latest_assessment': latest_assessment,
        'latest_match': latest_match,
        'notifications': notifications,
        'activity_data': json.dumps(activity_data),
        'score_trend': json.dumps(score_trend),
        'trend_labels': json.dumps(trend_labels),
        'monthly_scores': json.dumps(monthly_scores),
        'month_labels': json.dumps(month_labels),
        'profile': profile,
        # Learning
        'active_plans': active_plans,
        'learning_goal': learning_goal,
        'goal_progress': goal_progress,
        'goal_remaining': goal_remaining,
        'goal_label': goal_label,
        'learning_suggestions': learning_suggestions,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def profile_view(request):
    """View user profile."""
    return render(request, 'dashboard/profile.html', {'page_title': 'My Profile'})


@login_required
def profile_update_view(request):
    """Update user profile."""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'page_title': 'Edit Profile',
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'dashboard/profile_edit.html', context)


@login_required
def progress_view(request):
    """User progress tracking dashboard."""
    from apps.cv_analyzer.models import CVUpload, CVAnalysis
    from apps.job_matching.models import JobMatch
    from apps.assessment.models import Assessment, UserSkill
    from apps.interview_prep.models import InterviewSession
    from apps.career.models import CareerRecommendation
    from apps.notifications.models import Notification
    from django.db.models import Avg

    user = request.user

    cv_count = CVUpload.objects.filter(user=user).count()
    analysis_count = CVAnalysis.objects.filter(cv_upload__user=user).count()
    match_count = JobMatch.objects.filter(user=user).count()
    assessment_count = Assessment.objects.filter(user=user).count()
    interview_count = InterviewSession.objects.filter(user=user).count()
    skill_count = UserSkill.objects.filter(user=user).count()
    career_count = CareerRecommendation.objects.filter(user=user).count()

    avg_cv_score = CVAnalysis.objects.filter(cv_upload__user=user).aggregate(avg=Avg('overall_score'))['avg'] or 0
    avg_match_score = JobMatch.objects.filter(user=user).aggregate(avg=Avg('match_score'))['avg'] or 0

    latest_assessment = Assessment.objects.filter(user=user).first()
    readiness = latest_assessment.readiness_score if latest_assessment else 0

    completed_interviews = InterviewSession.objects.filter(user=user, is_completed=True).count()

    # Calculate profile completion %
    score = 0
    if user.first_name and user.last_name: score += 10
    if hasattr(user, 'profile'):
        p = user.profile
        if p.phone: score += 10
        if p.location: score += 10
        if p.current_role: score += 10
        if p.target_role: score += 10
        if p.bio: score += 10
        if p.linkedin_url: score += 5
        if p.github_url: score += 5
        if p.avatar: score += 5
        if p.education_level: score += 5
        if p.target_industry: score += 5
    if cv_count > 0: score += 5
    if analysis_count > 0: score += 5
    if assessment_count > 0: score += 5

    profile_completion = min(score, 100)

    # Weekly learning goal
    from apps.learning.models import LearningGoal, StudyPlan
    learning_goal = LearningGoal.objects.filter(user=user).first()
    goal_progress = 0
    goal_remaining = 0
    goal_label = ''
    if learning_goal:
        learning_goal.refresh_progress()
        goal_progress = learning_goal.progress_percent()
        goal_remaining = max(learning_goal.target - learning_goal.achieved, 0)
        goal_label = learning_goal.get_goal_type_display()
    active_plans = StudyPlan.objects.filter(user=user).exclude(status='completed')

    context = {
        'page_title': 'My Progress',
        'cv_count': cv_count,
        'analysis_count': analysis_count,
        'match_count': match_count,
        'assessment_count': assessment_count,
        'interview_count': interview_count,
        'skill_count': skill_count,
        'career_count': career_count,
        'avg_cv_score': round(avg_cv_score, 1),
        'avg_match_score': round(avg_match_score, 1),
        'readiness': round(readiness, 1),
        'completed_interviews': completed_interviews,
        'profile_completion': profile_completion,
        'learning_goal': learning_goal,
        'goal_progress': goal_progress,
        'goal_remaining': goal_remaining,
        'goal_label': goal_label,
        'active_plans': active_plans,
    }
    return render(request, 'dashboard/progress.html', context)


@login_required
def report_view(request):
    """User-facing comprehensive readiness report."""
    from apps.cv_analyzer.models import CVUpload, CVAnalysis
    from apps.job_matching.models import JobMatch
    from apps.assessment.models import Assessment
    from apps.interview_prep.models import InterviewSession
    from apps.career.models import CareerRecommendation
    from apps.assessment.models import UserSkill
    from django.db.models import Avg

    user = request.user
    cvs = CVUpload.objects.filter(user=user, is_deleted=False).select_related('analysis').order_by('-uploaded_at')[:5]
    latest_cv_analysis = CVAnalysis.objects.filter(cv_upload__user=user).order_by('-analyzed_at').first()
    latest_assessment = Assessment.objects.filter(user=user).order_by('-created_at').first()
    latest_match = JobMatch.objects.filter(user=user).select_related('job_description').order_by('-created_at').first()
    latest_interview = InterviewSession.objects.filter(user=user).order_by('-created_at').first()
    latest_career_rec = CareerRecommendation.objects.filter(user=user).order_by('-created_at').first()
    skills = UserSkill.objects.filter(user=user)

    avg_cv = CVAnalysis.objects.filter(cv_upload__user=user).aggregate(
        avg_overall=Avg('overall_score'), avg_ats=Avg('ats_score'),
        avg_format=Avg('format_score'), avg_keyword=Avg('keyword_score')
    )

    # Weekly learning goal
    from apps.learning.models import LearningGoal, StudyPlan
    learning_goal = LearningGoal.objects.filter(user=user).first()
    goal_progress = 0
    goal_remaining = 0
    goal_label = ''
    if learning_goal:
        learning_goal.refresh_progress()
        goal_progress = learning_goal.progress_percent()
        goal_remaining = max(learning_goal.target - learning_goal.achieved, 0)
        goal_label = learning_goal.get_goal_type_display()
    active_plans = StudyPlan.objects.filter(user=user).exclude(status='completed')

    context = {
        'page_title': 'My Readiness Report',
        'cvs': cvs,
        'latest_cv_analysis': latest_cv_analysis,
        'latest_assessment': latest_assessment,
        'latest_match': latest_match,
        'latest_interview': latest_interview,
        'latest_career_rec': latest_career_rec,
        'skills': skills,
        'cv_count': cvs.count(),
        'match_count': JobMatch.objects.filter(user=user).count(),
        'assessment_count': Assessment.objects.filter(user=user).count(),
        'interview_count': InterviewSession.objects.filter(user=user).count(),
        'skill_count': skills.count(),
        'avg_overall': round(avg_cv['avg_overall'] or 0, 1),
        'avg_ats': round(avg_cv['avg_ats'] or 0, 1),
        'avg_format': round(avg_cv['avg_format'] or 0, 1),
        'avg_keyword': round(avg_cv['avg_keyword'] or 0, 1),
        'readiness': round(latest_assessment.readiness_score if latest_assessment else 0, 1),
        'learning_goal': learning_goal,
        'goal_progress': goal_progress,
        'goal_remaining': goal_remaining,
        'goal_label': goal_label,
        'active_plans': active_plans,
    }
    return render(request, 'dashboard/report.html', context)


@login_required
def report_download_pdf_view(request):
    """Download comprehensive readiness report as PDF."""
    from apps.cv_analyzer.models import CVUpload, CVAnalysis
    from apps.job_matching.models import JobMatch
    from apps.assessment.models import Assessment
    from apps.interview_prep.models import InterviewSession
    from apps.career.models import CareerRecommendation
    from apps.assessment.models import UserSkill
    from django.template.loader import render_to_string
    from django.db.models import Avg
    from django.utils import timezone

    user = request.user
    cvs = CVUpload.objects.filter(user=user, is_deleted=False).select_related('analysis').order_by('-uploaded_at')[:5]
    latest_assessment = Assessment.objects.filter(user=user).order_by('-created_at').first()
    skills = UserSkill.objects.filter(user=user)
    avg_cv = CVAnalysis.objects.filter(cv_upload__user=user).aggregate(
        avg_overall=Avg('overall_score'), avg_ats=Avg('ats_score')
    )

    context = {
        'user': user,
        'profile': getattr(user, 'profile', None),
        'cvs': cvs,
        'latest_assessment': latest_assessment,
        'skills': skills,
        'avg_overall': round(avg_cv['avg_overall'] or 0, 1),
        'avg_ats': round(avg_cv['avg_ats'] or 0, 1),
        'readiness': round(latest_assessment.readiness_score if latest_assessment else 0, 1),
        'today': timezone.now(),
    }
    html = render_to_string('dashboard/report_pdf.html', context)
    try:
        from xhtml2pdf import pisa
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Readiness_Report_{user.last_name or user.first_name}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response
    except Exception:
        return render(request, 'dashboard/report.html', context)
