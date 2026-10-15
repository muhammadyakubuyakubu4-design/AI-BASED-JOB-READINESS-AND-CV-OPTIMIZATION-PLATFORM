from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import InterviewSession, MockInterviewResponse
from .forms import InterviewSessionForm
from apps.cv_analyzer.utils.ai_service import generate_interview_questions, career_chat_response, generate_mock_interview_feedback


@login_required
def mock_interview_view(request, pk):
    """Mock interview practice page: answer the session's questions and get feedback."""
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)

    # Gather all questions with their type labels
    questions = []
    for qtype, qlist, icon, title in [
        ('behavioral', session.behavioral_questions, 'fas fa-user', 'Behavioral'),
        ('technical', session.technical_questions, 'fas fa-code', 'Technical'),
        ('situational', session.situational_questions, 'fas fa-scenarios', 'Situational'),
    ]:
        for q in qlist:
            questions.append({'type': qtype, 'text': q, 'type_label': title, 'icon': icon})

    # Load existing responses for this session
    existing = {r.question: r for r in session.mock_responses.filter(user=request.user)}
    answered_questions = set(r.question for r in session.mock_responses.filter(user=request.user))

    context = {
        'page_title': f'Mock Interview: {session.job_title}',
        'session': session,
        'questions': questions,
        'existing': existing,
        'answered': answered_questions,
        'total': len(questions),
    }
    return render(request, 'interview/mock_interview.html', context)


@login_required
@require_POST
@csrf_exempt
def mock_interview_submit_view(request, pk):
    """Submit an answer to a mock interview question and get AI feedback."""
    import json
    import traceback
    try:
        session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        question_type = data.get('question_type', 'behavioral')
        answer = data.get('answer', '').strip()

        if not question or not answer:
            return JsonResponse({'error': 'Question and answer are required'}, status=400)

        feedback = generate_mock_interview_feedback(question, answer, session.job_title)

        response, created = MockInterviewResponse.objects.update_or_create(
            session=session,
            user=request.user,
            question=question,
            defaults={'question_type': question_type, 'answer': answer, 'feedback': feedback},
        )

        return JsonResponse({'ok': True, 'feedback': feedback})
    except Exception as e:
        tb = traceback.format_exc()
        with open(r'C:\Users\HP\AppData\Local\Temp\opencode\mock_interview_error.log', 'a') as f:
            f.write(f"=== mock_interview_submit_view ===\nError: {e}\n\nTraceback:\n{tb}\n\n")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def interview_prep_view(request):
    """Interview preparation page with session generator."""
    if request.method == 'POST':
        form = InterviewSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user

            # Generate questions using AI service
            questions_result = generate_interview_questions(
                job_title=session.job_title,
                difficulty=session.difficulty,
                industry=session.industry,
            )

            session.behavioral_questions = questions_result['behavioral_questions']
            session.technical_questions = questions_result['technical_questions']
            session.situational_questions = questions_result['situational_questions']
            session.general_tips = questions_result['general_tips']
            session.preparation_checklist = questions_result['preparation_checklist']
            session.save()

            try:
                from apps.admin_panel.utils import log_activity
                log_activity(request.user, 'create', f'Started interview prep for {session.job_title} ({session.difficulty})', 'InterviewSession', session.pk, request)
            except Exception:
                pass

            messages.success(request, f'Interview prep for "{session.job_title}" generated!')
            return redirect('interview_prep:session', pk=session.pk)
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = InterviewSessionForm()

    recent_sessions = InterviewSession.objects.filter(user=request.user)[:5]
    context = {
        'page_title': 'Interview Preparation',
        'form': form,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'interview/index.html', context)


@login_required
def interview_session_view(request, pk):
    """View a specific interview prep session."""
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
    context = {
        'page_title': f'Interview Prep: {session.job_title}',
        'session': session,
    }
    return render(request, 'interview/session.html', context)


@login_required
def interview_history_view(request):
    """List all interview sessions."""
    sessions = InterviewSession.objects.filter(user=request.user)
    context = {
        'page_title': 'Interview History',
        'sessions': sessions,
    }
    return render(request, 'interview/history.html', context)


@login_required
@require_POST
@csrf_exempt
def interview_chat_view(request):
    """AJAX endpoint for AI career chatbot."""
    import json
    import traceback
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        history = data.get('history', [])

        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        # Build user context
        user_context = {
            'name': request.user.first_name,
        }
        if hasattr(request.user, 'profile'):
            user_context['role'] = request.user.profile.current_role
            user_context['target'] = request.user.profile.target_role

        response_text = career_chat_response(user_message, user_context, history)
        return JsonResponse({'response': response_text})

    except Exception as e:
        tb = traceback.format_exc()
        with open(r'C:\Users\HP\AppData\Local\Temp\opencode\chatbot_error.log', 'a') as f:
            f.write(f"=== interview_chat_view ===\nError: {e}\n\nTraceback:\n{tb}\n\n")
        return JsonResponse({'error': str(e)}, status=500)
