from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import CareerRecommendation
from apps.cv_analyzer.utils.ai_service import get_career_recommendations, career_chat_response


@login_required
def career_view(request):
    """Career recommendations overview page."""
    latest_recommendation = CareerRecommendation.objects.filter(user=request.user).first()
    context = {
        'page_title': 'Career Recommendations',
        'latest_recommendation': latest_recommendation,
    }
    return render(request, 'career/index.html', context)


@login_required
def generate_recommendations_view(request):
    """Generate new career recommendations."""
    if request.method == 'POST':
        # Get user skills
        from apps.assessment.models import UserSkill
        skills = list(UserSkill.objects.filter(user=request.user).values(
            'skill_name', 'proficiency', 'category'
        ))

        target_role = ''
        experience = '0'
        if hasattr(request.user, 'profile'):
            target_role = request.user.profile.target_role
            experience = request.user.profile.years_experience

        result = get_career_recommendations(skills, target_role, experience)

        # Save recommendation
        recommendation = CareerRecommendation.objects.create(
            user=request.user,
            recommended_skills=result['recommended_skills'],
            recommended_courses=result['recommended_courses'],
            career_paths=result.get('career_paths', []),
            certifications=result.get('certifications', []),
            job_titles=result.get('job_titles', []),
            target_companies=result.get('target_companies', []),
            learning_resources=result.get('learning_resources', []),
            current_skills_snapshot=[s['skill_name'] for s in skills],
            target_role=target_role,
            ai_summary=result['ai_summary'],
        )

        # Notification
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=request.user,
                title='Career Recommendations Ready',
                message='Your personalized career recommendations have been generated.',
                notification_type='career',
                link='/career/',
            )
        except Exception:
            pass

        try:
            from apps.admin_panel.utils import log_activity
            log_activity(request.user, 'create', f'Generated career recommendation targeting {recommendation.target_role}', 'CareerRecommendation', recommendation.pk, request)
        except Exception:
            pass

        messages.success(request, 'Career recommendations generated successfully!')
        return redirect('career:recommendations')

    return redirect('career:index')


@login_required
def career_recommendations_view(request):
    """Display detailed career recommendations."""
    recommendation = CareerRecommendation.objects.filter(user=request.user).first()
    if not recommendation:
        messages.info(request, 'Generate your first career recommendation to get started.')
        return redirect('career:index')

    context = {
        'page_title': 'Career Recommendations',
        'recommendation': recommendation,
    }
    return render(request, 'career/recommendations.html', context)


@require_POST
@csrf_exempt
def career_chatbot_view(request):
    """AJAX endpoint for career guidance chatbot."""
    import json
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        history = data.get('history', [])

        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        user_context = {'name': request.user.first_name}
        if hasattr(request.user, 'profile'):
            user_context['target_role'] = request.user.profile.target_role

        response = career_chat_response(user_message, user_context, history)
        return JsonResponse({'response': response})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def cover_letter_view(request):
    """Cover letter generator page."""
    from apps.cv_analyzer.models import CoverLetter
    letters = CoverLetter.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'page_title': 'Cover Letter Generator',
        'letters': letters,
    }
    return render(request, 'career/cover_letter.html', context)


@login_required
def cover_letter_create_view(request):
    """Generate a new cover letter."""
    from apps.cv_analyzer.models import CoverLetter
    if request.method == 'POST':
        job_title = request.POST.get('job_title', '').strip()
        company_name = request.POST.get('company_name', '').strip()
        recipient_name = request.POST.get('recipient_name', '').strip()
        job_description = request.POST.get('job_description', '').strip()
        tone = request.POST.get('tone', 'professional')

        if not job_title:
            messages.error(request, 'Job title is required.')
            return redirect('career:cover_letter')

        # Generate cover letter content using AI
        content = _generate_cover_letter_content(request.user, job_title, company_name, recipient_name, job_description, tone)

        letter = CoverLetter.objects.create(
            user=request.user,
            job_title=job_title,
            company_name=company_name,
            recipient_name=recipient_name,
            job_description=job_description,
            content=content,
            tone=tone,
        )
        try:
            from apps.admin_panel.utils import log_activity
            log_activity(request.user, 'create', f'Generated cover letter for {job_title} at {company_name or "unknown company"}', 'CoverLetter', letter.pk, request)
        except Exception:
            pass
        messages.success(request, 'Cover letter generated successfully!')
        return redirect('career:cover_letter')

    return redirect('career:cover_letter')


@login_required
def cover_letter_delete_view(request, pk):
    """Delete a cover letter."""
    from apps.cv_analyzer.models import CoverLetter
    letter = get_object_or_404(CoverLetter, pk=pk, user=request.user)
    if request.method == 'POST':
        letter.delete()
        messages.success(request, 'Cover letter deleted.')
    return redirect('career:cover_letter')


@login_required
def cover_letter_export_view(request, pk):
    """Export cover letter as PDF, DOCX, or TXT."""
    from apps.cv_analyzer.models import CoverLetter
    letter = get_object_or_404(CoverLetter, pk=pk, user=request.user)
    fmt = request.GET.get('format', 'docx')

    safe_title = letter.job_title.replace(' ', '_').replace('/', '_') or 'cover_letter'

    if fmt == 'pdf':
        try:
            from io import BytesIO
            from django.template.loader import render_to_string
            from xhtml2pdf import pisa
            html = render_to_string('career/cover_letter_pdf.html', {
                'letter': letter,
                'user': request.user,
            })
            result = BytesIO()
            pisa_status = pisa.CreatePDF(html, dest=result)
            if pisa_status.err:
                raise ValueError('PDF generation failed')
            result.seek(0)
            response = HttpResponse(result.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{safe_title}.pdf"'
            return response
        except Exception:
            messages.error(request, 'PDF generation failed. Downloading as DOCX instead.')
            fmt = 'docx'

    if fmt == 'docx':
        try:
            from docx import Document
            from docx.shared import Pt, Inches
            doc = Document()
            style = doc.styles['Normal']
            font = style.font
            font.name = 'Calibri'
            font.size = Pt(11)
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)
            p = doc.add_paragraph()
            run = p.add_run(f'Cover Letter — {letter.job_title}')
            run.bold = True
            run.font.size = Pt(16)
            if letter.company_name:
                sub = doc.add_paragraph()
                sub_run = sub.add_run(f'{letter.company_name}')
                sub_run.font.size = Pt(12)
                sub_run.font.color.rgb = None
            doc.add_paragraph()
            for line in letter.content.split('\n'):
                doc.add_paragraph(line)
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename="{safe_title}.docx"'
            doc.save(response)
            return response
        except Exception:
            messages.error(request, 'DOCX generation failed. Downloading as TXT instead.')
            fmt = 'txt'

    response = HttpResponse(letter.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{safe_title}.txt"'
    return response


def _generate_cover_letter_content(user, job_title, company, recipient, job_description, tone):
    """Generate cover letter content using AI or template."""
    user_name = user.get_full_name() or user.username
    user_email = user.email
    profile = getattr(user, 'profile', None)
    current_role = profile.current_role if profile else ''
    skills_list = []
    try:
        from apps.assessment.models import UserSkill
        skills_list = list(UserSkill.objects.filter(user=user).values_list('skill_name', flat=True)[:5])
    except Exception:
        pass

    tone_adjectives = {
        'professional': 'professional and confident',
        'enthusiastic': 'enthusiastic and passionate',
        'formal': 'formal and respectful',
        'concise': 'concise and direct',
    }
    tone_desc = tone_adjectives.get(tone, 'professional and confident')

    content = f"""Dear {recipient or 'Hiring Manager'},

I am writing to express my strong interest in the {job_title} position at {company}. As a dedicated {current_role or 'professional'} with a passion for delivering results, I am confident that my skills and experience make me an ideal candidate for this role.

Throughout my career, I have developed expertise in {', '.join(skills_list) if skills_list else 'key areas relevant to this position'}. My ability to combine technical knowledge with strong interpersonal skills has consistently enabled me to exceed expectations and drive meaningful outcomes.

I am particularly drawn to {company} because of its reputation for innovation and excellence. I am eager to contribute to your team and help achieve your organization's goals.

I would welcome the opportunity to discuss how my background and skills align with the needs of your team. Thank you for considering my application.

Best regards,
{user_name}
{user_email}
"""
    return content


# ---------------------------------------------------------------------------
# Feature 4: Cover Letter Scanner
# ---------------------------------------------------------------------------

@login_required
@require_POST
def cover_letter_scan_view(request, pk):
    """
    Scan an existing cover letter against a user-selected job description.
    Returns JSON with match score, keyword analysis, strengths and improvements.
    """
    from apps.cv_analyzer.models import CoverLetter
    from apps.cv_analyzer.utils.ai_service import scan_cover_letter
    from apps.job_matching.models import JobDescription

    letter = get_object_or_404(CoverLetter, pk=pk, user=request.user)

    import json as _json
    try:
        data = _json.loads(request.body)
        job_desc_id = data.get('job_description_id')
    except Exception:
        job_desc_id = request.POST.get('job_description_id')

    if not job_desc_id:
        return JsonResponse({'error': 'No job description selected.'}, status=400)

    job_desc = get_object_or_404(JobDescription, pk=job_desc_id, user=request.user)

    result = scan_cover_letter(letter.content, job_desc.description)

    # Persist results on the cover letter
    letter.match_score = result.get('match_score', 0.0)
    letter.keyword_analysis = result
    letter.scan_job_description = job_desc
    letter.save(update_fields=['match_score', 'keyword_analysis', 'scan_job_description'])

    return JsonResponse({'ok': True, 'result': result, 'job_title': job_desc.title})
