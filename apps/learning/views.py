from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import StudyPlan, StudyPlanLesson, Quiz, QuizAttempt, LearningGoal
from .forms import StudyPlanForm
from apps.cv_analyzer.utils.ai_service import generate_study_plan


@login_required
def learning_view(request):
    """Learning dashboard showing all study plans."""
    plans = StudyPlan.objects.filter(user=request.user)
    active_plans = plans.exclude(status='completed')
    completed_plans = plans.filter(status='completed')

    suggestions = _skill_suggestions(request.user)

    # Weekly goal
    goal = LearningGoal.objects.filter(user=request.user).first()
    if goal:
        goal.refresh_progress()

    context = {
        'page_title': 'Learn Skills',
        'plans': plans,
        'active_plans': active_plans,
        'completed_plans': completed_plans,
        'suggestions': suggestions,
        'goal': goal,
        'goal_remaining': max(goal.target - goal.achieved, 0) if goal else 0,
        'form': StudyPlanForm(),
    }
    return render(request, 'learning/index.html', context)


@login_required
@require_POST
def update_goal_view(request):
    """Create or update the user's weekly learning goal."""
    goal = LearningGoal.objects.filter(user=request.user).first()
    goal_type = request.POST.get('goal_type', 'lessons')
    try:
        target = int(request.POST.get('target', 5))
    except (TypeError, ValueError):
        target = 5
    target = max(1, min(target, 50))

    from django.utils import timezone
    if goal:
        goal.goal_type = goal_type
        goal.target = target
        goal.period_start = timezone.localdate()
        goal.achieved = 0
        goal.is_active = True
        goal.save()
    else:
        goal = LearningGoal.objects.create(
            user=request.user,
            goal_type=goal_type,
            target=target,
        )
    goal.refresh_progress()

    messages.success(request, f'Weekly goal updated: complete {goal.target} {goal.get_goal_type_display().lower()} per week.')
    return redirect('learning:index')


def _skill_suggestions(user):
    """Suggest skills worth learning based on career recommendations / skill gaps."""
    suggestions = []
    try:
        from apps.career.models import CareerRecommendation
        rec = CareerRecommendation.objects.filter(user=user).first()
        if rec:
            recommendations = rec.recommended_skills if isinstance(rec.recommended_skills, list) else []
            for skill in recommendations[:6]:
                if isinstance(skill, str):
                    suggestions.append(skill)
    except Exception:
        pass

    try:
        from apps.assessment.models import Assessment
        assessment = Assessment.objects.filter(user=user).first()
        if assessment and isinstance(assessment.skill_gaps, list):
            for gap in assessment.skill_gaps[:4]:
                if isinstance(gap, dict) and gap.get('skill'):
                    suggestions.append(gap['skill'])
                elif isinstance(gap, str):
                    suggestions.append(gap)
    except Exception:
        pass

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique[:8]


@login_required
@require_POST
def create_study_plan_view(request):
    """Generate and save a new study plan for a skill."""
    form = StudyPlanForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please provide a valid skill name.')
        return redirect('learning:index')

    skill_name = form.cleaned_data['skill_name'].strip()
    target_level = form.cleaned_data.get('target_level', '')

    # Avoid duplicate active plans for the same skill
    existing = StudyPlan.objects.filter(user=request.user, skill_name__iexact=skill_name).exclude(status='completed').first()
    if existing:
        messages.info(request, f'You already have an active study plan for "{skill_name}".')
        return redirect('learning:plan', pk=existing.pk)

    result = generate_study_plan(skill_name, target_level)

    plan = StudyPlan.objects.create(
        user=request.user,
        skill_name=skill_name,
        title=result.get('title', f'Master {skill_name}'),
        description=result.get('description', ''),
        target_level=target_level,
        estimated_hours=result.get('estimated_hours', 0),
        ai_summary='',
    )

    # Create lessons
    lessons = result.get('lessons', [])
    for idx, lesson_data in enumerate(lessons, start=1):
        StudyPlanLesson.objects.create(
            plan=plan,
            order=idx,
            title=lesson_data.get('title', f'Lesson {idx}'),
            content=lesson_data.get('content', ''),
            key_points=lesson_data.get('key_points', []),
            resources=result.get('resources', []),
        )

    # Create quiz
    Quiz.objects.create(
        plan=plan,
        title=result.get('quiz_title', f'{skill_name} Mastery Check'),
        questions=result.get('questions', []),
    )

    try:
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=request.user,
            title='Study Plan Created',
            message=f'Your learning plan for "{skill_name}" is ready. Start your first lesson!',
            notification_type='career',
            link=f'/learning/plan/{plan.pk}/',
        )
    except Exception:
        pass

    try:
        from apps.admin_panel.utils import log_activity
        log_activity(request.user, 'create', f'Created study plan for {skill_name}', 'StudyPlan', plan.pk, request)
    except Exception:
        pass

    messages.success(request, f'Study plan for "{skill_name}" created with {len(lessons)} lessons!')
    return redirect('learning:plan', pk=plan.pk)


@login_required
def study_plan_view(request, pk):
    """View a study plan with its lessons and quiz."""
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    lessons = plan.lessons.all()
    quiz = plan.quizzes.first()
    completed_count = lessons.filter(is_completed=True).count()
    total_lessons = lessons.count()

    passes = 0
    if quiz:
        passes = QuizAttempt.objects.filter(user=request.user, quiz=quiz, passed=True).count()

    context = {
        'page_title': plan.title,
        'plan': plan,
        'lessons': lessons,
        'quiz': quiz,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
        'quiz_passes': passes,
    }
    return render(request, 'learning/plan.html', context)


@login_required
def lesson_view(request, pk, lesson_pk):
    """View a single lesson."""
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    lesson = get_object_or_404(StudyPlanLesson, pk=lesson_pk, plan=plan)

    prev_lesson = plan.lessons.filter(order__lt=lesson.order).last()
    next_lesson = plan.lessons.filter(order__gt=lesson.order).first()

    context = {
        'page_title': lesson.title,
        'plan': plan,
        'lesson': lesson,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    }
    return render(request, 'learning/lesson.html', context)


@login_required
@require_POST
@csrf_exempt
def complete_lesson_view(request, pk, lesson_pk):
    """Mark a lesson as complete."""
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    lesson = get_object_or_404(StudyPlanLesson, pk=lesson_pk, plan=plan)

    if not lesson.is_completed:
        from django.utils import timezone
        lesson.is_completed = True
        lesson.completed_at = timezone.now()
        lesson.save(update_fields=['is_completed', 'completed_at'])
        plan.update_progress()

    return JsonResponse({'ok': True, 'progress': plan.progress_percent})


@login_required
def quiz_view(request, pk):
    """Take the quiz for a study plan."""
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    quiz = plan.quizzes.first()
    if not quiz or not quiz.questions:
        messages.error(request, 'No quiz available for this plan.')
        return redirect('learning:plan', pk=plan.pk)

    context = {
        'page_title': quiz.title,
        'plan': plan,
        'quiz': quiz,
    }
    return render(request, 'learning/quiz.html', context)


@login_required
@require_POST
def quiz_submit_view(request, pk):
    """Grade a submitted quiz."""
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    quiz = plan.quizzes.first()
    if not quiz:
        messages.error(request, 'No quiz available for this plan.')
        return redirect('learning:plan', pk=plan.pk)

    questions = quiz.questions
    score = 0
    total = len(questions)
    answers = []

    for idx, q in enumerate(questions, start=1):
        selected = request.POST.get(f'q{idx}')
        try:
            selected_idx = int(selected) - 1
        except (TypeError, ValueError):
            selected_idx = -1

        correct = (selected_idx == q.get('correct_index'))
        if correct:
            score += 1

        options = q.get('options', [])
        correct_index = q.get('correct_index', -1)
        correct_answer = options[correct_index] if 0 <= correct_index < len(options) else ''

        answers.append({
            'question': q.get('question'),
            'selected': selected_idx,
            'correct': correct,
            'correct_index': correct_index,
            'correct_answer': correct_answer,
            'explanation': q.get('explanation', ''),
        })

    percentage = (score / total * 100) if total else 0
    passed = percentage >= 60

    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        user=request.user,
        answers=answers,
        score=score,
        total=total,
        percentage=percentage,
        passed=passed,
    )

    # Update user skill proficiency if they passed
    if passed:
        try:
            from apps.assessment.models import UserSkill
            skill = UserSkill.objects.filter(user=request.user, skill_name__iexact=plan.skill_name).first()
            if skill:
                if skill.proficiency < 4:
                    skill.proficiency += 1
                    skill.save(update_fields=['proficiency', 'updated_at'])
        except Exception:
            pass

    return redirect('learning:quiz_result', pk=plan.pk, attempt_pk=attempt.pk)


@login_required
def quiz_result_view(request, pk, attempt_pk):
    """Show the result of a quiz attempt."""
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    attempt = get_object_or_404(QuizAttempt, pk=attempt_pk, user=request.user, quiz__plan=plan)

    context = {
        'page_title': f'Quiz Result - {plan.skill_name}',
        'plan': plan,
        'attempt': attempt,
    }
    return render(request, 'learning/quiz_result.html', context)


@login_required
@require_POST
def delete_study_plan_view(request, pk):
    """Delete a study plan."""
    plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    skill_name = plan.skill_name
    plan.delete()
    messages.success(request, f'Study plan for "{skill_name}" deleted.')
    return redirect('learning:index')
