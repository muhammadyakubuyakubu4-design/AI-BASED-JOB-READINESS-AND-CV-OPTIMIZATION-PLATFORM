import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import JobDescription, JobMatch
from .forms import JobDescriptionForm
from .ats_detector import detect_ats
from apps.cv_analyzer.models import CVUpload
from apps.cv_analyzer.utils.ai_service import match_cv_to_job


@login_required
def job_matching_view(request):
    """Job description input page for CV matching."""
    active_cv = CVUpload.objects.filter(user=request.user, is_active=True).first()
    if not active_cv:
        active_cv = CVUpload.objects.filter(user=request.user).first()

    if request.method == 'POST':
        form = JobDescriptionForm(request.POST)
        if form.is_valid():
            if not active_cv:
                messages.error(request, 'Please upload a CV first before matching against job descriptions.')
                return redirect('cv_analyzer:upload')

            job_desc = form.save(commit=False)
            job_desc.user = request.user
            job_desc.save()

            try:
                cv_text = active_cv.parsed_text
                job_text = job_desc.description
                match_result = match_cv_to_job(cv_text, job_text)

                # ATS Platform Detection
                job_url = request.POST.get('job_url', '').strip()
                ats_info = detect_ats(job_desc.company, job_url)

                job_match = JobMatch.objects.create(
                    user=request.user,
                    cv_upload=active_cv,
                    job_description=job_desc,
                    match_score=match_result['match_score'],
                    matching_keywords=match_result['matching_keywords'],
                    missing_keywords=match_result['missing_keywords'],
                    matching_skills=match_result['matching_skills'],
                    missing_skills=match_result['missing_skills'],
                    suggestions=match_result['suggestions'],
                    strength_areas=match_result['strength_areas'],
                    gap_areas=match_result['gap_areas'],
                    section_analysis=match_result['section_analysis'],
                    optimize_plan=match_result['optimize_plan'],
                    ai_summary=match_result['ai_summary'],
                    ats_platform=ats_info['platform'],
                    ats_tips=ats_info['tips'],
                )

                _create_match_notification(request.user, job_desc, match_result['match_score'])

                messages.success(request, f'Job match analysis complete! Match score: {match_result["match_score"]}%')
                return redirect('job_matching:result', pk=job_match.pk)

            except Exception as e:
                job_desc.delete()
                messages.error(request, f'Matching failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = JobDescriptionForm()

    context = {
        'page_title': 'Job Matching',
        'form': form,
        'active_cv': active_cv,
        'recent_matches': JobMatch.objects.filter(user=request.user).select_related('job_description')[:3],
    }
    return render(request, 'job/matching.html', context)


@login_required
def job_match_result_view(request, pk):
    """Display job match result."""
    job_match = get_object_or_404(JobMatch, pk=pk, user=request.user)
    # Build ATS info dict for template
    ats_info = None
    if job_match.ats_platform:
        from .ats_detector import ATS_TIPS, DEFAULT_ATS_TIPS
        tip_data = ATS_TIPS.get(job_match.ats_platform, DEFAULT_ATS_TIPS)
        ats_info = {
            'platform': job_match.ats_platform,
            'color': tip_data['color'],
            'icon': tip_data['icon'],
            'description': tip_data['description'],
            'tips': job_match.ats_tips,
        }
    context = {
        'page_title': 'Match Result',
        'job_match': job_match,
        'match_label': job_match.match_label,
        'ats_info': ats_info,
    }
    return render(request, 'job/result.html', context)


@login_required
def job_match_history_view(request):
    """List all job match results."""
    matches = JobMatch.objects.filter(user=request.user).select_related('job_description', 'cv_upload')
    context = {
        'page_title': 'Match History',
        'matches': matches,
    }
    return render(request, 'job/history.html', context)


@login_required
def job_match_delete_view(request, pk):
    """Delete a job match entry."""
    job_match = get_object_or_404(JobMatch, pk=pk, user=request.user)
    if request.method == 'POST':
        job_match.delete()
        messages.success(request, 'Job match deleted.')
    return redirect('job_matching:history')


# ---------------------------------------------------------------------------
# Feature 1: Job Application Tracker (Kanban Board)
# ---------------------------------------------------------------------------

@login_required
def job_tracker_view(request):
    """Kanban-style job application tracker grouped by application_status."""
    STATUS_COLUMNS = [
        ('', 'Saved', 'secondary', 'fa-bookmark'),
        ('applied', 'Applied', 'primary', 'fa-paper-plane'),
        ('interviewing', 'Interviewing', 'info', 'fa-comments'),
        ('offered', 'Offered', 'warning', 'fa-handshake'),
        ('accepted', 'Accepted', 'success', 'fa-check-circle'),
        ('rejected', 'Rejected', 'danger', 'fa-times-circle'),
    ]

    all_matches = (
        JobMatch.objects
        .filter(user=request.user)
        .select_related('job_description')
        .order_by('-updated_at')
    )

    columns = []
    for status_key, label, color, icon in STATUS_COLUMNS:
        columns.append({
            'key': status_key,
            'label': label,
            'color': color,
            'icon': icon,
            'items': [m for m in all_matches if m.application_status == status_key],
        })

    context = {
        'page_title': 'Job Tracker',
        'columns': columns,
        'total': all_matches.count(),
    }
    return render(request, 'job/tracker.html', context)


@login_required
@require_POST
def update_job_status_view(request):
    """AJAX endpoint — update application_status, notes, or follow_up_date on a JobMatch."""
    try:
        data = json.loads(request.body)
        pk = data.get('pk')
        job_match = get_object_or_404(JobMatch, pk=pk, user=request.user)

        if 'status' in data:
            valid = ['', 'applied', 'interviewing', 'offered', 'rejected', 'accepted']
            if data['status'] in valid:
                job_match.application_status = data['status']

        if 'notes' in data:
            job_match.notes = data['notes']

        if 'follow_up_date' in data:
            job_match.follow_up_date = data['follow_up_date'] or None

        job_match.save()
        return JsonResponse({'ok': True, 'status': job_match.application_status})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def _create_match_notification(user, job_desc, score):
    """Create an in-app notification after a job match completes."""
    try:
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=user,
            title='Job Match Complete',
            message=f'Your CV matched {score}% against "{job_desc.title}" at {job_desc.company or "the company"}.',
            notification_type='job',
            link='/jobs/history/',
        )
    except Exception:
        pass
