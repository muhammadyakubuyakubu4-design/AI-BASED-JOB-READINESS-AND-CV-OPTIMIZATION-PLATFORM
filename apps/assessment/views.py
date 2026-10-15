from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Assessment, UserSkill
from .forms import UserSkillForm, SkillBulkForm
from apps.cv_analyzer.utils.ai_service import assess_career_readiness


@login_required
def assessment_view(request):
    """Job readiness assessment overview."""
    skills = UserSkill.objects.filter(user=request.user)
    latest_assessment = Assessment.objects.filter(user=request.user).first()

    context = {
        'page_title': 'Job Readiness Assessment',
        'skills': skills,
        'latest_assessment': latest_assessment,
        'skill_form': UserSkillForm(),
        'bulk_form': SkillBulkForm(),
    }
    return render(request, 'assessment/index.html', context)


@login_required
def run_assessment_view(request):
    """Run a new job readiness assessment."""
    if request.method == 'POST':
        skills = list(UserSkill.objects.filter(user=request.user).values(
            'skill_name', 'proficiency', 'category'
        ))

        # Get the user's active CV text
        cv_text = ''
        try:
            from apps.cv_analyzer.models import CVUpload
            active_cv = CVUpload.objects.filter(user=request.user, is_active=True).first()
            if not active_cv:
                active_cv = CVUpload.objects.filter(user=request.user).first()
            if active_cv:
                cv_text = active_cv.parsed_text
        except Exception:
            pass

        result = assess_career_readiness(cv_text, skills)

        # Save assessment
        assessment = Assessment.objects.create(
            user=request.user,
            readiness_score=result['readiness_score'],
            technical_score=result['technical_score'],
            soft_skills_score=result['soft_skills_score'],
            experience_score=result['experience_score'],
            education_score=result['education_score'],
            career_level=result['career_level'],
            skill_gaps=result['skill_gaps'],
            strengths=result['strengths'],
            recommendations=result['recommendations'],
            action_plan=result['action_plan'],
            ai_summary=result['ai_summary'],
        )

        # Update profile readiness score
        if hasattr(request.user, 'profile'):
            request.user.profile.readiness_score = result['readiness_score']
            request.user.profile.save()

        # Create notification
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=request.user,
                title='Assessment Complete',
                message=f'Your job readiness score is {result["readiness_score"]}/100 ({result["career_level"].title()} level).',
                notification_type='assessment',
                link=f'/assessment/result/{assessment.pk}/',
            )
        except Exception:
            pass

        try:
            from apps.admin_panel.utils import log_activity
            log_activity(request.user, 'create', f'Completed readiness assessment — score: {result["readiness_score"]}/100', 'Assessment', assessment.pk, request)
        except Exception:
            pass

        messages.success(request, f'Assessment complete! Your readiness score: {result["readiness_score"]}/100')
        return redirect('assessment:result', pk=assessment.pk)

    return redirect('assessment:index')


@login_required
def assessment_result_view(request, pk):
    """Display assessment result."""
    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)
    context = {
        'page_title': 'Assessment Results',
        'assessment': assessment,
        'readiness_label': assessment.readiness_label,
    }
    return render(request, 'assessment/result.html', context)


@login_required
def skills_view(request):
    """Manage user skills."""
    skills = UserSkill.objects.filter(user=request.user)
    form = UserSkillForm()
    context = {
        'page_title': 'My Skills',
        'skills': skills,
        'form': form,
    }
    return render(request, 'assessment/skills.html', context)


@login_required
def skill_add_view(request):
    """Add a new skill."""
    if request.method == 'POST':
        # Handle bulk add
        if 'skills_text' in request.POST:
            bulk_form = SkillBulkForm(request.POST)
            if bulk_form.is_valid():
                skills_text = bulk_form.cleaned_data['skills_text']
                category = bulk_form.cleaned_data['default_category']
                skill_names = [s.strip() for s in skills_text.split(',') if s.strip()]
                added = 0
                for name in skill_names[:20]:  # Limit to 20 at once
                    _, created = UserSkill.objects.get_or_create(
                        user=request.user,
                        skill_name=name,
                        defaults={'category': category, 'proficiency': 2}
                    )
                    if created:
                        added += 1
                messages.success(request, f'{added} skill(s) added successfully.')
        else:
            form = UserSkillForm(request.POST)
            if form.is_valid():
                skill = form.save(commit=False)
                skill.user = request.user
                try:
                    from django.db import IntegrityError
                    skill.save()
                    messages.success(request, f'Skill "{skill.skill_name}" added.')
                except IntegrityError:
                    messages.warning(request, f'You already have the skill "{skill.skill_name}".')
            else:
                messages.error(request, 'Failed to add skill. Please check your inputs.')

    return redirect('assessment:skills')


@login_required
def skill_delete_view(request, pk):
    """Delete a skill."""
    skill = get_object_or_404(UserSkill, pk=pk, user=request.user)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, f'Skill "{skill.skill_name}" removed.')
    return redirect('assessment:skills')
