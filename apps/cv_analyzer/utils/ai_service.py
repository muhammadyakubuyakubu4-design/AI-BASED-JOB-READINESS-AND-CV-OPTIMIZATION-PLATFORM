"""
AI Service - Provides AI-powered analysis using OpenAI API with NLP fallback.
All functions return structured data regardless of which backend is used.
"""
import json
import random
from django.conf import settings
from .analyzer import (
    calculate_ats_score,
    calculate_grammar_score,
    calculate_keyword_score,
    calculate_format_score,
    generate_suggestions,
    get_missing_keywords,
)
from .parser import extract_sections, extract_contact_info, extract_skills_from_text


import socket

def _is_connected():
    """Check for active internet connection to avoid long timeouts."""
    try:
        # Connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        pass
    return False

def _get_openai_client():
    """Get OpenAI/Groq client if API key is configured."""
    if not settings.OPENAI_API_KEY or not _is_connected():
        return None
    try:
        from openai import OpenAI
        kwargs = {'api_key': settings.OPENAI_API_KEY, 'timeout': 10.0}
        if settings.OPENAI_API_KEY.startswith('gsk_'):
            kwargs['base_url'] = 'https://api.groq.com/openai/v1'
        return OpenAI(**kwargs)
    except ImportError:
        return None

def _get_gemini_model():
    """Get Gemini AI GenerativeModel if configured."""
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or not _is_connected():
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-3.6-flash')
    except ImportError:
        return None


def analyze_cv(cv_text: str) -> dict:
    """
    Perform complete CV analysis.
    Returns comprehensive analysis including scores, sections, skills, and suggestions.
    """
    # Always run NLP analysis (fast, no API needed)
    sections = extract_sections(cv_text)
    contact_info = extract_contact_info(cv_text)
    extracted_skills = extract_skills_from_text(cv_text)

    ats_score = calculate_ats_score(cv_text, sections)
    grammar_score = calculate_grammar_score(cv_text)
    keyword_score = calculate_keyword_score(cv_text)
    format_score = calculate_format_score(cv_text, sections)
    overall_score = round((ats_score * 0.35 + grammar_score * 0.25 + keyword_score * 0.20 + format_score * 0.20), 1)

    suggestions = generate_suggestions(cv_text, sections, {
        'ats_score': ats_score,
        'grammar_score': grammar_score,
        'keyword_score': keyword_score,
        'format_score': format_score,
    })

    missing_sections = [
        s for s in ['summary', 'education', 'experience', 'skills', 'certifications']
        if not sections.get(s, '').strip()
    ]

    result = {
        'ats_score': ats_score,
        'grammar_score': grammar_score,
        'keyword_score': keyword_score,
        'format_score': format_score,
        'overall_score': overall_score,
        'extracted_sections': sections,
        'extracted_skills': extracted_skills,
        'contact_info': contact_info,
        'suggestions': suggestions,
        'missing_sections': missing_sections,
        'improvements': [],
        'ai_feedback': '',
    }

    # Enhance with OpenAI if available
    client = _get_openai_client()
    if client:
        try:
            ai_result = _openai_analyze_cv(client, cv_text)
            result['ai_feedback'] = ai_result.get('feedback', '')
            result['improvements'] = ai_result.get('improvements', [])
            if ai_result.get('extracted_skills'):
                result['extracted_skills'] = ai_result['extracted_skills']
            # Blend AI scores with NLP scores
            if ai_result.get('overall_score'):
                ai_overall = ai_result['overall_score']
                result['overall_score'] = round((overall_score + ai_overall) / 2, 1)
        except Exception:
            pass  # Fall back gracefully

    return result


def _openai_analyze_cv(client, cv_text: str) -> dict:
    """Call OpenAI to get enhanced CV feedback."""
    prompt = f"""Analyze this CV professionally. Provide:
1. An overall quality score (0-100)
2. 3-5 specific improvement points
3. A brief professional feedback paragraph (2-3 sentences)
4. A list of the top 5 to 10 professional skills explicitly mentioned or implied in this CV (works for any industry, e.g., Accounting, Nursing, Engineering).

CV Text:
{cv_text[:3000]}

Respond in JSON format:
{{
  "overall_score": <number>,
  "improvements": ["improvement 1", "improvement 2", ...],
  "feedback": "feedback paragraph",
  "extracted_skills": ["Skill 1", "Skill 2", "Skill 3"]
}}"""

    gemini = _get_gemini_model()
    if gemini:
        full_prompt = f"You are a professional HR expert and CV coach. Output only valid JSON.\n\n{prompt}"
        response = gemini.generate_content(full_prompt)
        content = response.text
    else:
        response = client.chat.completions.create(
            model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': 'You are a professional HR expert and CV coach. Output only valid JSON.'},
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        content = response.choices[0].message.content
    
    # Safely extract JSON from the response
    import re
    import json
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        content = match.group(0)
    
    try:
        return json.loads(content.strip())
    except Exception:
        return {'overall_score': 70, 'improvements': [], 'feedback': '', 'extracted_skills': []}


def _split_job_sections(job_text: str) -> dict:
    """
    Split a job description into logical sections (Requirements, Responsibilities,
    Qualifications, Nice-to-have, About, etc.) for per-section keyword analysis.
    Returns an ordered dict of {section_name: section_text}.
    """
    import re

    # Header patterns: a line that is short, title-cased, and either ends with ':' 
    # or matches a known JobScan-style section heading.
    header_pattern = re.compile(r'^\s*([A-Z][A-Za-z &/\'-]{2,40})\s*:\s*$|^\s*(Requirements|Responsibilities|Qualifications|About the Role|About Us|Nice to Have|Nice to Have[s]?|Must Have|What You Will Do|What You will do|Key Responsibilities|Job Summary|Description|Benefits|Skills Required)\s*$', re.IGNORECASE)

    lines = job_text.splitlines()
    sections = {}
    current = 'Job Overview'
    current_lines = []

    def flush():
        text = ' '.join(current_lines).strip()
        if text:
            sections[current] = text

    for raw in lines:
        line = raw.strip()
        m = header_pattern.match(line)
        if m and len(line) <= 60:
            flush()
            current = (m.group(1) or m.group(2)).strip().rstrip(':')
            current_lines = []
        else:
            current_lines.append(line)

    flush()
    return sections


def _analyze_job_sections(cv_text: str, job_text: str) -> list:
    """
    Per-section keyword analysis (JobScan-style).
    For each JD section, compute matched/missing keywords and a mini match score.
    """
    sections = _split_job_sections(job_text)
    breakdown = []
    cv_lower = cv_text.lower()

    for name, section_text in sections.items():
        if len(section_text) < 10:
            continue
        kw = get_missing_keywords(cv_text, section_text)
        matched = kw.get('matching', [])
        missing = kw.get('missing', [])
        score = round(kw.get('match_percentage', 0.0), 1)
        breakdown.append({
            'section': name,
            'score': score,
            'matching': matched,
            'missing': missing,
            'label': _score_label(score),
        })

    # Fall back to a single section if nothing was split out
    if not breakdown:
        kw = get_missing_keywords(cv_text, job_text)
        breakdown.append({
            'section': 'Job Overview',
            'score': round(kw.get('match_percentage', 0.0), 1),
            'matching': kw.get('matching', []),
            'missing': kw.get('missing', []),
            'label': _score_label(kw.get('match_percentage', 0.0)),
        })
    return breakdown


def _score_label(score: float) -> str:
    if score >= 80:
        return 'Excellent'
    elif score >= 60:
        return 'Good'
    elif score >= 40:
        return 'Partial'
    return 'Weak'


def _build_optimize_plan(cv_text: str, job_text: str, keyword_analysis: dict, missing_skills: list) -> list:
    """
    JobScan-style 'Optimize My CV' action checklist.
    Returns actionable, prioritized steps to close keyword/skill gaps.
    """
    plan = []
    seen = set()

    def add(action, target, priority):
        key = action
        if key in seen:
            return
        seen.add(key)
        plan.append({'action': action, 'target': target, 'priority': priority})

    # Skill gaps -> add skill line items
    for skill in missing_skills[:6]:
        add(
            action=f"Add '{skill}' to your Skills section (front-office keywords recruiters scan for).",
            target='Skills section',
            priority='High' if len(missing_skills) <= 4 else 'Medium',
        )

    # Keyword gaps -> rewrite achievement bullets to include them
    for kw in keyword_analysis['missing'][:6]:
        add(
            action=f"Mention '{kw}' in your work-experience bullets (mirror the phrasing used in the job posting).",
            target='Experience section',
            priority='High',
        )

    total_missing = len(keyword_analysis['missing']) + len(missing_skills)
    if total_missing == 0:
        add(
            action="No urgent gaps found - your CV already covers this posting well.",
            target='-',
            priority='Low',
        )
    if total_missing >= 10:
        add(
            action="Rewrite your professional summary to lead with the 3 most-in-demand skills from this posting.",
            target='Summary section',
            priority='Medium',
        )
    if keyword_analysis.get('match_percentage', 0) < 60:
        add(
            action="Create a tailored version of this CV just for this application - do not submit a generic one.",
            target='Whole CV',
            priority='High',
        )

    return plan[:8]


def match_cv_to_job(cv_text: str, job_text: str) -> dict:
    """
    Match a CV against a job description.
    Returns match percentage, missing/matching keywords, JobScan-style per-section
    breakdown, and an 'Optimize My CV' action plan.
    """
    keyword_analysis = get_missing_keywords(cv_text, job_text)
    match_score = keyword_analysis['match_percentage']

    cv_skills = extract_skills_from_text(cv_text)
    job_skills = extract_skills_from_text(job_text)
    missing_skills = [s for s in job_skills if s not in cv_skills]
    matching_skills = [s for s in job_skills if s in cv_skills]

    # JobScan-style per-section breakdown
    section_analysis = _analyze_job_sections(cv_text, job_text)

    # Generate match-specific suggestions
    suggestions = []
    if missing_skills:
        suggestions.append(
            f"Consider adding these skills to your CV: {', '.join(missing_skills[:5])}"
        )
    if keyword_analysis['missing']:
        suggestions.append(
            f"Include these keywords from the job posting: {', '.join(keyword_analysis['missing'][:5])}"
        )
    if match_score < 60:
        suggestions.append(
            "Tailor your CV more specifically to this job description to improve your chances."
        )
    if match_score >= 70:
        suggestions.append(
            "Good match! Focus on the missing keywords to make your application even stronger."
        )

    optimize_plan = _build_optimize_plan(cv_text, job_text, keyword_analysis, missing_skills)

    result = {
        'match_score': round(match_score, 1),
        'matching_keywords': keyword_analysis['matching'],
        'missing_keywords': keyword_analysis['missing'],
        'matching_skills': matching_skills,
        'missing_skills': missing_skills,
        'suggestions': suggestions,
        'strength_areas': _identify_strengths(cv_text, job_text),
        'gap_areas': _identify_gaps(cv_text, job_text, missing_skills),
        'section_analysis': section_analysis,
        'optimize_plan': optimize_plan,
        'ai_summary': '',
    }

    # Enhance with OpenAI if available
    client = _get_openai_client()
    if client:
        try:
            ai_result = _openai_match_job(client, cv_text, job_text)
            result['ai_summary'] = ai_result.get('summary', '')
            result['match_score'] = round((match_score + ai_result.get('match_score', match_score)) / 2, 1)
        except Exception:
            pass

    return result


def _openai_match_job(client, cv_text: str, job_text: str) -> dict:
    """Use OpenAI to enhance job matching analysis."""
    prompt = f"""Compare this CV against the job description and provide:
1. A match score (0-100)
2. A brief summary of the match quality (2-3 sentences)

CV: {cv_text[:2000]}

Job Description: {job_text[:1500]}

Respond in JSON:
{{
  "match_score": <number>,
  "summary": "summary text"
}}"""

    response = client.chat.completions.create(
        model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are a professional recruiter.'},
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=300,
        temperature=0.5,
    )
    return json.loads(response.choices[0].message.content)


def _identify_strengths(cv_text: str, job_text: str) -> list:
    """Identify strength areas where CV aligns well with job."""
    import re
    strengths = []
    cv_lower = cv_text.lower()

    categories = {
        'Technical Skills': ['python', 'java', 'javascript', 'sql', 'react', 'django', 'aws'],
        'Leadership': ['led', 'managed', 'supervised', 'coordinated', 'directed'],
        'Communication': ['presented', 'communicated', 'collaborated', 'wrote', 'reported'],
        'Problem Solving': ['solved', 'analyzed', 'debugged', 'optimized', 'improved'],
        'Project Delivery': ['delivered', 'completed', 'launched', 'deployed', 'released'],
    }

    for category, keywords in categories.items():
        matches = sum(1 for kw in keywords if kw in cv_lower)
        if matches >= 2:
            strengths.append(category)

    return strengths[:4]


def _identify_gaps(cv_text: str, job_text: str, missing_skills: list) -> list:
    """Identify gap areas that need improvement."""
    gaps = []
    if missing_skills:
        gaps.append(f"Missing skills: {', '.join(missing_skills[:3])}")

    job_lower = job_text.lower()
    cv_lower = cv_text.lower()

    if 'degree' in job_lower and 'bachelor' not in cv_lower and 'master' not in cv_lower:
        gaps.append("Education credentials not clearly stated")

    if 'years' in job_lower and not any(str(n) in cv_lower for n in range(1, 10)):
        gaps.append("Years of experience not explicitly mentioned")

    return gaps[:4]


def generate_interview_questions(job_title: str, difficulty: str = 'mid', industry: str = '') -> dict:
    """
    Generate interview questions for a given job title.
    Returns behavioral, technical, and situational questions.
    """
    # Default NLP-based questions
    behavioral_questions = _get_behavioral_questions(job_title)
    technical_questions = _get_technical_questions(job_title, difficulty)
    situational_questions = _get_situational_questions()
    tips = _get_interview_tips()
    checklist = _get_preparation_checklist()

    result = {
        'behavioral_questions': behavioral_questions,
        'technical_questions': technical_questions,
        'situational_questions': situational_questions,
        'general_tips': tips,
        'preparation_checklist': checklist,
    }

    # Enhance with OpenAI if available
    client = _get_openai_client()
    if client:
        try:
            ai_result = _openai_generate_questions(client, job_title, difficulty, industry)
            if ai_result.get('technical_questions'):
                result['technical_questions'] = ai_result['technical_questions']
            if ai_result.get('behavioral_questions'):
                result['behavioral_questions'] = ai_result['behavioral_questions']
        except Exception:
            pass

    return result


def _openai_generate_questions(client, job_title: str, difficulty: str, industry: str) -> dict:
    """Use OpenAI to generate targeted interview questions."""
    prompt = f"""Generate interview questions for a {difficulty}-level {job_title} position{' in ' + industry if industry else ''}.

Provide:
- 5 behavioral questions (STAR format)
- 5 technical questions specific to this role

Respond in JSON:
{{
  "behavioral_questions": ["q1", "q2", "q3", "q4", "q5"],
  "technical_questions": ["q1", "q2", "q3", "q4", "q5"]
}}"""

    response = client.chat.completions.create(
        model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are an expert interviewer and HR specialist.'},
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=700,
        temperature=0.7,
    )
    return json.loads(response.choices[0].message.content)


def _get_behavioral_questions(job_title: str) -> list:
    questions = [
        f"Tell me about yourself and why you're interested in this {job_title} role.",
        "Describe a challenging project you worked on. How did you overcome the obstacles?",
        "Tell me about a time you had to work under pressure and tight deadlines. How did you handle it?",
        "Describe a situation where you had a conflict with a teammate. How was it resolved?",
        "Give an example of a time you demonstrated leadership, even if you weren't in a leadership role.",
        "Tell me about your greatest professional achievement and how you accomplished it.",
        "Describe a time you had to learn something quickly. How did you approach it?",
        "Tell me about a time you received difficult feedback. How did you respond?",
    ]
    return questions[:6]


def _get_technical_questions(job_title: str, difficulty: str) -> list:
    title_lower = job_title.lower()

    if any(kw in title_lower for kw in ['developer', 'engineer', 'programmer', 'software']):
        return [
            "Explain the difference between object-oriented and functional programming.",
            "What is the difference between synchronous and asynchronous programming?",
            "How do you ensure code quality and maintainability in your projects?",
            "Describe your experience with version control systems like Git.",
            "How would you optimize a slow database query?",
            "Explain the concept of REST APIs and how you've used them.",
        ]
    elif any(kw in title_lower for kw in ['data', 'analyst', 'scientist']):
        return [
            "Explain the difference between supervised and unsupervised learning.",
            "How do you handle missing data in a dataset?",
            "Describe your experience with SQL and data querying.",
            "What tools and libraries do you use for data analysis?",
            "How do you validate a machine learning model?",
            "Explain the bias-variance tradeoff in machine learning.",
        ]
    elif any(kw in title_lower for kw in ['manager', 'lead', 'director']):
        return [
            "How do you prioritize tasks and manage your team's workload?",
            "What project management methodologies have you used?",
            "How do you measure team performance and set KPIs?",
            "Describe your experience with budget management.",
            "How do you handle underperforming team members?",
            "What is your approach to stakeholder communication?",
        ]
    else:
        return [
            "What relevant skills and experience do you bring to this role?",
            "How do you stay updated with the latest trends in your field?",
            "Describe your problem-solving approach when facing a complex challenge.",
            "What tools and technologies are you proficient in?",
            "How do you ensure quality in your work?",
            "Where do you see yourself professionally in 5 years?",
        ]


def _get_situational_questions() -> list:
    return [
        "If you were given a project with an unclear brief, how would you proceed?",
        "Imagine your team is behind schedule on a critical deliverable. What do you do?",
        "How would you handle a disagreement with your manager about the best approach to a task?",
        "If you discovered a colleague was not following company policies, what would you do?",
        "How would you prioritize if you had multiple urgent tasks from different stakeholders?",
    ]


def _get_interview_tips() -> list:
    return [
        "Research the company thoroughly before your interview — understand their mission, products, and recent news.",
        "Prepare specific examples using the STAR method (Situation, Task, Action, Result).",
        "Dress professionally and arrive 10-15 minutes early for in-person interviews.",
        "Prepare thoughtful questions to ask your interviewer about the role and company culture.",
        "Follow up with a thank-you email within 24 hours of your interview.",
        "Practice your answers out loud to build confidence and reduce nervousness.",
        "Bring multiple copies of your CV and any relevant portfolio work.",
        "Maintain positive body language — eye contact, firm handshake, upright posture.",
    ]


def _get_preparation_checklist() -> list:
    return [
        {"item": "Research the company and understand their business", "done": False},
        {"item": "Review the job description and match your experience", "done": False},
        {"item": "Prepare 5-7 STAR-format behavioral examples", "done": False},
        {"item": "Practice answering common interview questions", "done": False},
        {"item": "Prepare questions to ask the interviewer", "done": False},
        {"item": "Review your CV and be ready to discuss every point", "done": False},
        {"item": "Plan your outfit and ensure it's interview-ready", "done": False},
        {"item": "Confirm interview details (time, location/link)", "done": False},
    ]


def assess_career_readiness(cv_text: str, skills: list) -> dict:
    """
    Assess overall career readiness based on CV and skill profile.
    Returns readiness score, skill gaps, strengths, and recommendations.
    """
    # Calculate component scores
    sections = extract_sections(cv_text)
    ats_score = calculate_ats_score(cv_text, sections)
    skill_count = len(skills)

    # Technical score based on skills
    technical_skills = [s for s in skills if s.get('category') == 'technical']
    soft_skills = [s for s in skills if s.get('category') == 'soft']

    technical_score = min(len(technical_skills) * 8, 100)
    soft_skills_score = min(len(soft_skills) * 12, 100)

    # Experience score
    has_experience = bool(sections.get('experience', '').strip())
    experience_score = 70 if has_experience else 30

    # Education score
    has_education = bool(sections.get('education', '').strip())
    education_score = 80 if has_education else 40

    # Overall readiness
    readiness_score = round(
        (technical_score * 0.30 + soft_skills_score * 0.20 +
         experience_score * 0.25 + education_score * 0.15 + ats_score * 0.10),
        1
    )

    # Determine career level
    if readiness_score >= 80:
        career_level = 'senior'
    elif readiness_score >= 65:
        career_level = 'mid'
    elif readiness_score >= 45:
        career_level = 'junior'
    else:
        career_level = 'entry'

    # Identify gaps
    skill_gaps = []
    in_demand_skills = ['Python', 'SQL', 'Communication', 'Project Management', 'Data Analysis']
    skill_names = [s.get('skill_name', '') for s in skills]
    for skill in in_demand_skills:
        if skill not in skill_names:
            skill_gaps.append({
                'skill': skill,
                'importance': 'high',
                'recommendation': f'Consider learning {skill} to boost your employability',
            })

    # Identify strengths
    strengths = []
    if technical_skills:
        top_tech = [s['skill_name'] for s in technical_skills[:3]]
        strengths.append(f"Technical expertise in {', '.join(top_tech)}")
    if has_experience:
        strengths.append("Demonstrated work experience")
    if has_education:
        strengths.append("Strong educational background")

    # Action plan
    action_plan = _generate_action_plan(readiness_score, skill_gaps, sections)

    result = {
        'readiness_score': readiness_score,
        'technical_score': technical_score,
        'soft_skills_score': soft_skills_score,
        'experience_score': experience_score,
        'education_score': education_score,
        'career_level': career_level,
        'skill_gaps': skill_gaps[:5],
        'strengths': strengths,
        'recommendations': _get_readiness_recommendations(readiness_score, career_level),
        'action_plan': action_plan,
        'ai_summary': '',
    }

    # Enhance with OpenAI if available
    client = _get_openai_client()
    if client:
        try:
            skill_list = ', '.join([s.get('skill_name', '') for s in skills[:10]])
            ai_summary = _openai_readiness_summary(client, readiness_score, career_level, skill_list)
            result['ai_summary'] = ai_summary
        except Exception:
            pass

    return result


def _openai_readiness_summary(client, score: float, level: str, skills: str) -> str:
    """Generate AI summary for career readiness."""
    prompt = f"""Write a 2-3 sentence career readiness summary for a {level}-level candidate with score {score}/100 and skills: {skills}. Be encouraging and specific."""

    response = client.chat.completions.create(
        model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are a career coach.'},
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=200,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _get_readiness_recommendations(score: float, career_level: str) -> list:
    if score >= 80:
        return [
            "You are highly job-ready. Focus on senior-level positions.",
            "Consider adding leadership or management experience to advance further.",
            "Build your personal brand through LinkedIn and professional networking.",
        ]
    elif score >= 60:
        return [
            "You have a good foundation. Work on filling skill gaps to reach senior level.",
            "Seek mentorship from experienced professionals in your field.",
            "Complete industry certifications to validate your skills.",
        ]
    elif score >= 40:
        return [
            "Focus on building core technical skills for your target role.",
            "Work on personal projects to build a portfolio.",
            "Consider internships or volunteer work to gain practical experience.",
        ]
    else:
        return [
            "Start with foundational courses in your target field.",
            "Build a portfolio of small projects to demonstrate your capabilities.",
            "Network actively and attend industry events and meetups.",
        ]


def _generate_action_plan(score: float, skill_gaps: list, sections: dict) -> list:
    plan = []

    if not sections.get('summary', '').strip():
        plan.append({
            'step': 1,
            'action': 'Write a compelling professional summary',
            'timeline': '1-2 days',
            'priority': 'high',
        })

    if skill_gaps:
        plan.append({
            'step': 2,
            'action': f"Learn in-demand skill: {skill_gaps[0]['skill']}",
            'timeline': '2-4 weeks',
            'priority': 'high',
        })

    plan.append({
        'step': 3,
        'action': 'Update and optimize your LinkedIn profile',
        'timeline': '1 week',
        'priority': 'medium',
    })

    plan.append({
        'step': 4,
        'action': 'Apply to 5-10 relevant positions per week',
        'timeline': 'Ongoing',
        'priority': 'high',
    })

    return plan


def get_career_recommendations(skills: list, target_role: str = '', experience: str = '0') -> dict:
    """
    Generate career path recommendations based on current skills and target role.
    """
    skill_names = [s.get('skill_name', '') if isinstance(s, dict) else str(s) for s in skills]

    recommended_skills = _recommend_skills(skill_names, target_role)
    career_paths = _recommend_career_paths(skill_names, target_role)
    recommended_courses = _recommend_courses(skill_names, target_role)
    certifications = _recommend_certifications(skill_names, target_role)

    result = {
        'recommended_skills': recommended_skills,
        'recommended_courses': recommended_courses,
        'career_paths': career_paths,
        'certifications': certifications,
        'job_titles': _suggest_job_titles(skill_names, target_role),
        'learning_resources': _get_learning_resources(skill_names),
        'target_companies': [],
        'ai_summary': '',
    }

    # Enhance with OpenAI if available
    client = _get_openai_client()
    if client:
        try:
            ai_result = _openai_career_recommendations(client, skill_names, target_role)
            if ai_result.get('summary'):
                result['ai_summary'] = ai_result['summary']
            if ai_result.get('job_titles'):
                result['job_titles'] = ai_result['job_titles']
            if ai_result.get('target_companies'):
                result['target_companies'] = ai_result['target_companies']
            if ai_result.get('career_paths'):
                result['career_paths'] = ai_result['career_paths']
            if ai_result.get('recommended_skills'):
                result['recommended_skills'] = ai_result['recommended_skills']
            if ai_result.get('recommended_courses'):
                result['recommended_courses'] = ai_result['recommended_courses']
            if ai_result.get('certifications'):
                result['certifications'] = ai_result['certifications']
        except Exception:
            pass

    return result


def _openai_career_recommendations(client, skills: list, target_role: str) -> dict:
    """Use OpenAI to enhance career recommendations."""
    prompt = f"""Based on skills: {', '.join(skills[:10])} and target role: {target_role or 'not specified'}, provide:
1. A 2-3 sentence career advice summary.
2. A list of 4 highly relevant job titles based on their specific skills.
3. A list of 5 real companies that frequently hire for these roles, along with their careers page URL.
4. A list of 3 specific career paths (each with 'title', 'description', 'avg_salary', 'growth', and 'required_skills' array).
5. A list of 5 specific skills to learn next (strings).
6. A list of 3 specific online courses to take (each with 'title', 'provider', and 'url').
7. A list of 3 specific professional certifications to aim for (strings).

Format your response exactly as JSON:
{{
  "summary": "...",
  "job_titles": ["...", "..."],
  "target_companies": [{{"name": "...", "url": "..."}}],
  "career_paths": [{{"title": "...", "description": "...", "avg_salary": "...", "growth": "...", "required_skills": ["..."]}}],
  "recommended_skills": ["...", "..."],
  "recommended_courses": [{{"title": "...", "provider": "...", "url": "..."}}],
  "certifications": ["...", "..."]
}}
"""

    gemini = _get_gemini_model()
    if gemini:
        full_prompt = f"You are a career development expert. Output only valid JSON.\n\n{prompt}"
        response = gemini.generate_content(full_prompt)
        content = response.text
    else:
        response = client.chat.completions.create(
            model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': 'You are a career development expert. Output only valid JSON.'},
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        content = response.choices[0].message.content
    import re
    import json
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        content = match.group(0)
        
    try:
        return json.loads(content.strip())
    except Exception:
        return {'summary': content, 'target_companies': []}


def _recommend_skills(current_skills: list, target_role: str) -> list:
    skills_map = {
        'data': ['Python', 'SQL', 'Machine Learning', 'Tableau', 'Statistics', 'Pandas', 'NumPy'],
        'web': ['React', 'Node.js', 'TypeScript', 'Docker', 'AWS', 'PostgreSQL', 'GraphQL'],
        'mobile': ['React Native', 'Flutter', 'Swift', 'Kotlin', 'Firebase', 'Redux'],
        'devops': ['Docker', 'Kubernetes', 'CI/CD', 'Terraform', 'AWS', 'Linux', 'Monitoring'],
        'management': ['Agile', 'Scrum', 'JIRA', 'Stakeholder Management', 'Risk Management'],
    }

    role_lower = target_role.lower()
    recommendations = []

    for category, skills in skills_map.items():
        if category in role_lower or not target_role:
            new_skills = [s for s in skills if s not in current_skills]
            recommendations.extend(new_skills[:3])

    if not recommendations:
        all_skills = ['Python', 'SQL', 'Communication', 'Project Management', 'Data Analysis']
        recommendations = [s for s in all_skills if s not in current_skills]

    return recommendations[:8]


def _recommend_career_paths(skills: list, target_role: str) -> list:
    paths = [
        {
            'title': 'Software Engineer',
            'description': 'Build scalable software applications and systems',
            'avg_salary': '$95,000 - $145,000',
            'growth': 'High',
            'required_skills': ['Python/Java/JavaScript', 'Data Structures', 'Algorithms', 'Git'],
        },
        {
            'title': 'Data Scientist',
            'description': 'Extract insights from complex datasets using ML and statistics',
            'avg_salary': '$100,000 - $150,000',
            'growth': 'Very High',
            'required_skills': ['Python', 'Machine Learning', 'SQL', 'Statistics'],
        },
        {
            'title': 'Product Manager',
            'description': 'Lead product strategy and cross-functional teams',
            'avg_salary': '$110,000 - $160,000',
            'growth': 'High',
            'required_skills': ['Agile', 'Communication', 'Analytics', 'Leadership'],
        },
        {
            'title': 'DevOps Engineer',
            'description': 'Bridge development and operations through automation',
            'avg_salary': '$105,000 - $145,000',
            'growth': 'Very High',
            'required_skills': ['Docker', 'Kubernetes', 'CI/CD', 'Cloud Platforms'],
        },
    ]
    return paths[:3]


def _recommend_courses(skills: list, target_role: str) -> list:
    return [
        {
            'title': 'Complete Python Bootcamp',
            'platform': 'Udemy',
            'duration': '22 hours',
            'level': 'Beginner to Advanced',
            'url': 'https://udemy.com',
        },
        {
            'title': 'Machine Learning Specialization',
            'platform': 'Coursera (Stanford)',
            'duration': '3 months',
            'level': 'Intermediate',
            'url': 'https://coursera.org',
        },
        {
            'title': 'AWS Certified Solutions Architect',
            'platform': 'AWS Training',
            'duration': '40+ hours',
            'level': 'Intermediate',
            'url': 'https://aws.amazon.com/training',
        },
        {
            'title': 'Professional Communication Skills',
            'platform': 'LinkedIn Learning',
            'duration': '10 hours',
            'level': 'All Levels',
            'url': 'https://linkedin.com/learning',
        },
    ]


def _recommend_certifications(skills: list, target_role: str) -> list:
    return [
        {'name': 'AWS Certified Cloud Practitioner', 'provider': 'Amazon Web Services', 'level': 'Foundational'},
        {'name': 'Google Professional Data Engineer', 'provider': 'Google Cloud', 'level': 'Professional'},
        {'name': 'PMP - Project Management Professional', 'provider': 'PMI', 'level': 'Professional'},
        {'name': 'Certified Scrum Master (CSM)', 'provider': 'Scrum Alliance', 'level': 'Practitioner'},
        {'name': 'Microsoft Azure Fundamentals', 'provider': 'Microsoft', 'level': 'Foundational'},
    ]


def _suggest_job_titles(skills: list, target_role: str) -> list:
    skills_lower = [s.lower() for s in skills]

    if any(kw in skills_lower for kw in ['machine learning', 'tensorflow', 'pytorch']):
        return ['ML Engineer', 'Data Scientist', 'AI Engineer', 'Research Scientist']
    elif any(kw in skills_lower for kw in ['react', 'vue', 'angular']):
        return ['Frontend Developer', 'UI Developer', 'Full Stack Developer', 'React Developer']
    elif any(kw in skills_lower for kw in ['django', 'flask', 'fastapi', 'node.js']):
        return ['Backend Developer', 'API Developer', 'Full Stack Developer', 'Web Developer']
    elif any(kw in skills_lower for kw in ['docker', 'kubernetes', 'aws', 'terraform']):
        return ['DevOps Engineer', 'Cloud Engineer', 'Site Reliability Engineer', 'Platform Engineer']
    else:
        return ['Software Developer', 'Technical Analyst', 'Solutions Architect', 'Technical Consultant']


def _get_learning_resources(skills: list) -> list:
    return [
        {'name': 'freeCodeCamp', 'url': 'https://freecodecamp.org', 'type': 'Free', 'description': 'Full-stack web development'},
        {'name': 'Khan Academy', 'url': 'https://khanacademy.org', 'type': 'Free', 'description': 'Math, science, and computing'},
        {'name': 'MIT OpenCourseWare', 'url': 'https://ocw.mit.edu', 'type': 'Free', 'description': 'University-level courses'},
        {'name': 'Kaggle', 'url': 'https://kaggle.com', 'type': 'Free', 'description': 'Data science practice and competitions'},
        {'name': 'GitHub Learning Lab', 'url': 'https://lab.github.com', 'type': 'Free', 'description': 'Git and open source'},
    ]


def generate_study_plan(skill_name: str, target_level: str = '') -> dict:
    """
    Generate a structured study plan for learning a skill.
    Returns topic-based lessons, key points, resources, and a quiz.
    """
    base_result = _default_study_plan(skill_name, target_level)

    client = _get_openai_client()
    if client:
        try:
            ai_result = _openai_study_plan(client, skill_name, target_level)
            if ai_result.get('lessons'):
                base_result = ai_result
        except Exception:
            pass

    return base_result


def _openai_study_plan(client, skill_name: str, target_level: str) -> dict:
    """Use OpenAI to generate a detailed study plan."""
    prompt = f"""Create a comprehensive study plan for learning the skill "{skill_name}"{' at the ' + target_level + ' level' if target_level else ''}.

Return JSON with:
- title: a short, motivating plan title
- description: 2 sentence overview
- estimated_hours: integer total estimated learning hours
- lessons: array of exactly 6 lessons. Each lesson has:
  {{"title": string, "content": 2-3 paragraph learning content (60-150 words), "key_points": [4-6 short bullet strings]}}
- resources: array of 3-4 helpful learning resource strings (name + url)
- quiz_title: string
- questions: array of exactly 5 multiple choice questions. Each:
  {{"question": string, "options": ["A","B","C","D"], "correct_index": 0-3, "explanation": string}}

Respond ONLY with valid JSON."""

    response = client.chat.completions.create(
        model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are an expert curriculum designer and educator.'},
            {'role': 'user', 'content': prompt},
        ],
        max_tokens=2000,
        temperature=0.7,
    )
    content = response.choices[0].message.content.strip()
    # Remove any code fences if present
    if content.startswith('```'):
        content = content.strip('`')
        if content.startswith('json'):
            content = content[4:]
        content = content.strip()
    return json.loads(content)


def _default_study_plan(skill_name: str, target_level: str) -> dict:
    """NLP/fallback study plan used when no API available."""
    skill = skill_name or 'the Skill'
    lessons = [
        {
            'title': f'Introduction to {skill}',
            'content': (
                f'Welcome to your learning journey for {skill}! This lesson introduces the core concepts '
                f'and the overall landscape of {skill}. You will learn what {skill} is, why it matters, '
                f'and how it fits into real-world projects and career paths.\n\n'
                f'Start by building a mental model of the topic. Explore how professionals use {skill} daily '
                f'and set clear, measurable learning goals for yourself. Take notes and identify areas where '
                f'you are least confident so you can focus your practice.\n\n'
                f'By the end of this lesson, articulate the value of {skill} in your own words.'
            ),
            'key_points': [
                f'Understand what {skill} is and its purpose',
                'Identify real-world applications of the skill',
                'Set clear learning goals and a study schedule',
                'Recognize the prerequisites needed to begin',
            ],
        },
        {
            'title': f'Core Concepts of {skill}',
            'content': (
                f'This lesson dives into the fundamental building blocks of {skill}. Master the terminology, '
                f'key principles, and foundational techniques that everything else builds upon.\n\n'
                f'Work through examples step by step and practice applying each concept to simple problems. '
                f'Repetition and hands-on practice are essential to internalize these fundamentals.\n\n'
                f'Aim to explain each core concept without referring to notes.'
            ),
            'key_points': [
                f'Learn the essential terminology of {skill}',
                'Understand foundational principles and techniques',
                'Practice with simple examples and exercises',
                'Explain each concept in your own words',
            ],
        },
        {
            'title': f'Practical {skill} Skills',
            'content': (
                f'Now it is time to apply what you have learned. This lesson focuses on hands-on exercises and '
                f'realistic scenarios so you can translate theory into practical ability with {skill}.\n\n'
                f'Work on small projects or drills, review your mistakes, and iterate. Seek feedback from '
                f'peers or mentors and compare your approach to best practices.\n\n'
                f'Focus on doing, not just reading, for this lesson.'
            ),
            'key_points': [
                'Complete hands-on exercises and drills',
                'Build a small practice project',
                'Debug and fix errors independently',
                'Review and refine your work',
            ],
        },
        {
            'title': f'Advanced {skill} Techniques',
            'content': (
                f'Once comfortable with the basics, explore more advanced techniques and edge cases in {skill}. '
                f'This is where you differentiate yourself by going deeper than the average learner.\n\n'
                f'Study how experienced professionals approach complex problems in {skill}. Learn best practices, '
                f'common pitfalls, and techniques for optimizing your work.\n\n'
                f'Challenge yourself with harder problems and document your solutions.'
            ),
            'key_points': [
                'Explore advanced techniques and best practices',
                'Study how experts approach complex problems',
                'Recognize common pitfalls and avoid them',
                'Tackle challenging practice problems',
            ],
        },
        {
            'title': f'Building a {skill} Portfolio Project',
            'content': (
                f'Demonstrate your knowledge by building a portfolio-worthy project that showcases your {skill} '
                f'abilities. A real project is the strongest proof of your skill to employers.\n\n'
                f'Plan the project, define requirements, build it incrementally, and polish the final result. '
                f'Document your process and decisions as you go.\n\n'
                f'This project will become a key asset on your CV and in interviews.'
            ),
            'key_points': [
                'Plan and scope a portfolio project',
                'Build the project incrementally',
                'Polish the result and document decisions',
                'Prepare to present the project in interviews',
            ],
        },
        {
            'title': f'Final Review & Assessment of {skill}',
            'content': (
                f'In this final lesson, consolidate everything you have learned about {skill}. Review all key '
                f'concepts, revisit your notes, and test yourself to identify any remaining gaps.\n\n'
                f'Complete the attached quiz to assess your understanding. This step cements your learning and '
                f'prepares you to use {skill} confidently in practice.\n\n'
                f'Celebrate your progress and plan your ongoing practice.'
            ),
            'key_points': [
                'Review all lessons and key concepts',
                'Identify and close remaining gaps',
                'Complete the assessment quiz',
                'Plan ongoing practice and further learning',
            ],
        },
    ]

    resources = [
        {'name': f'freeCodeCamp - {skill}', 'url': 'https://freecodecamp.org', 'type': 'Free', 'description': f'Hands-on tutorials for {skill}'},
        {'name': 'Documentation & Knowledge Base', 'url': 'https://developer.mozilla.org', 'type': 'Free', 'description': f'Official references for {skill}'},
        {'name': 'YouTube Tutorials', 'url': 'https://youtube.com', 'type': 'Free', 'description': f'Video walkthroughs for {skill}'},
        {'name': 'Practice Platforms', 'url': 'https://leetcode.com', 'type': 'Free', 'description': f'Exercises to master {skill}'},
    ]

    questions = [
        {'question': f'What is the main purpose of learning {skill}?', 'options': ['To improve career prospects', 'To memorize facts', 'To avoid practice', 'To skip fundamentals'], 'correct_index': 0, 'explanation': f'{skill} is a sought-after ability that boosts employability and career growth.'},
        {'question': 'What is the best way to internalize new concepts?', 'options': ['Passive reading only', 'Repetition and hands-on practice', 'Memorization without practice', 'Skipping exercises'], 'correct_index': 1, 'explanation': 'Active practice and repetition are proven to internalize learning.'},
        {'question': 'Why build a portfolio project?', 'options': ['To impress employers with proof of skill', 'It is required for every job', 'To replace studying entirely', 'There is no benefit'], 'correct_index': 0, 'explanation': 'A real project is the strongest evidence of your ability to employers.'},
        {'question': 'How should you handle mistakes while learning?', 'options': ['Give up', 'Review and learn from them', 'Ignore them', 'Blame others'], 'correct_index': 1, 'explanation': 'Reviewing mistakes is a key part of skill development.'},
        {'question': 'What should you do in the final review lesson?', 'options': ['Consolidate learning and take an assessment', 'Start over completely', 'Stop learning', 'Only read notes once'], 'correct_index': 0, 'explanation': 'A final review and self-assessment cements your learning.'},
    ]

    return {
        'title': f'Master {skill}',
        'description': f'A structured, step-by-step plan to learn {skill} from foundations to portfolio-ready proficiency.',
        'estimated_hours': 20,
        'lessons': lessons,
        'resources': resources,
        'quiz_title': f'{skill} Mastery Check',
        'questions': questions,
    }


def generate_mock_interview_feedback(question: str, answer: str, job_title: str) -> str:
    """Generate AI feedback for a mock interview answer."""
    client = _get_openai_client()
    if client:
        try:
            response = client.chat.completions.create(
                model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': 'You are a professional interview coach. Give concise, constructive, actionable feedback on the candidate\'s answer. Include 1 strength and 1 improvement suggestion, and note if they used the STAR method effectively.'},
                    {'role': 'user', 'content': f"Question: {question}\n\nCandidate answer: {answer}\n\nJob: {job_title if job_title else 'General'}"},
                ],
                max_tokens=300,
                temperature=0.6,
            )
            return response.choices[0].message.content
        except Exception:
            pass

    # Fallback feedback
    word_count = len(answer.split())
    if word_count < 20:
        return (
            f"Your answer is quite brief ({word_count} words). Expand it using the STAR method "
            "(Situation, Task, Action, Result) to give a fully structured example with more detail and impact."
        )
    elif word_count > 200:
        return (
            f"Your answer is detailed ({word_count} words), which is great, but try to keep it focused. "
            "Aim for a clear STAR structure in 1-2 minutes and avoid going off on tangents."
        )
    else:
        return (
            "Good length and detail! Make sure your answer follows the STAR method (Situation, Task, Action, Result) "
            "and ends with a clear, quantifiable outcome. Keep practicing to sound confident and natural."
        )


def career_chat_response(user_message: str, user_context: dict = None, history: list = None) -> str:
    """
    Generate a career guidance chatbot response.
    Uses OpenAI if available, otherwise uses rule-based responses.
    """
    client = _get_openai_client()
    if client:
        try:
            context_str = ""
            if user_context:
                context_str = f"User context: {json.dumps(user_context)[:500]}"

            messages = [
                {
                    'role': 'system',
                    'content': (
                        f'You are CareerBot, a friendly AI career assistant. '
                        f'You help job seekers improve their employability. '
                        f'Understand natural language, handle greetings, follow-ups, '
                        f'and context from previous messages. Be concise, practical, '
                        f'and encouraging. {context_str}'
                    )
                },
            ]

            if history:
                for msg in history[-10:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role in ('user', 'assistant'):
                        messages.append({'role': role, 'content': content})

            messages.append({'role': 'user', 'content': user_message})

            response = client.chat.completions.create(
                model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception:
            pass

    # Rule-based fallback
    return _rule_based_chat(user_message)


def _rule_based_chat(message: str) -> str:
    """Simple rule-based career chatbot fallback."""
    message_lower = message.lower().strip()

    if any(kw in message_lower for kw in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', 'yo', 'sup']):
        return ("Hello! I'm CareerBot, your AI career assistant. I can help with CV optimization, "
                "interview preparation, skill development, job search strategies, and salary negotiation. "
                "What would you like help with today?")

    elif any(kw in message_lower for kw in ['thanks', 'thank you', 'thankyou', 'appreciate', 'grateful']):
        return ("You're welcome! I'm glad I could help. If you have any more questions about your "
                "career journey, feel free to ask. Good luck!")

    elif any(kw in message_lower for kw in ['bye', 'goodbye', 'see you', 'see ya', 'talk later', 'cya']):
        return ("Goodbye! Best of luck with your career journey. Remember, I'm always here if you "
                "need guidance with CVs, interviews, or job searching. Come back anytime!")

    elif any(kw in message_lower for kw in ['how are you', 'how are you doing', "what's up", 'how do you do']):
        return ("I'm doing great, thanks for asking! I'm here to help you with your career. "
                "Whether it's CV optimization, interview prep, or job search strategies, just let me know what you need!")

    elif any(kw in message_lower for kw in ['what can you do', 'help', 'capabilities', 'features', 'what do you do']):
        return ("I can help you with:\n"
                "1. CV/Resume optimization and analysis\n"
                "2. Interview preparation with tailored questions\n"
                "3. Job matching and application strategies\n"
                "4. Skill development recommendations\n"
                "5. Salary negotiation tips\n\nJust tell me what you'd like to work on!")

    elif any(kw in message_lower for kw in ['cv', 'resume', 'curriculum']):
        return ("To optimize your CV: 1) Use a clean, ATS-friendly format. 2) Include a strong professional summary. "
                "3) Quantify your achievements. 4) Match keywords from job descriptions. "
                "5) Keep it to 1-2 pages. Would you like to upload your CV for a full analysis?")

    elif any(kw in message_lower for kw in ['interview', 'prepare', 'questions']):
        return ("For interview success: 1) Research the company thoroughly. 2) Prepare STAR-method examples. "
                "3) Practice out loud. 4) Prepare thoughtful questions. 5) Send a thank-you note afterward. "
                "Use our Interview Prep module to generate tailored questions!")

    elif any(kw in message_lower for kw in ['salary', 'pay', 'compensation', 'negotiate', 'raise']):
        return ("For salary negotiation: 1) Research market rates on Glassdoor and LinkedIn. "
                "2) Know your worth based on experience and location. 3) Let the employer make the first offer when possible. "
                "4) Negotiate the whole package (benefits, flexibility, growth). Always be professional and positive!")

    elif any(kw in message_lower for kw in ['skill', 'learn', 'course', 'training', 'certification']):
        return ("Top in-demand skills: Python, AI/ML, Cloud (AWS/Azure), Data Analysis, React. "
                "Check our Career module for personalized course recommendations based on your profile!")

    elif any(kw in message_lower for kw in ['job', 'apply', 'application', 'search', 'hiring', 'vacancy']):
        return ("Job search tips: 1) Tailor your CV for each application. 2) Use LinkedIn actively. "
                "3) Network — 85% of jobs are filled through connections. 4) Apply consistently (10+ per week). "
                "5) Follow up after applications. Use our Job Matching feature to check how well you match!")

    elif any(kw in message_lower for kw in ['portfolio', 'linkedin', 'github', 'online presence']):
        return ("Building your online presence: 1) Keep your LinkedIn profile updated with achievements. "
                "2) Showcase projects on GitHub. 3) Create a personal portfolio website. "
                "4) Share industry insights on social media. 5) Engage with professionals in your field.")

    elif any(kw in message_lower for kw in ['networking', 'network', 'connect', 'referral']):
        return ("Networking tips: 1) Attend industry events and webinars. 2) Join professional groups on LinkedIn. "
                "3) Reach out to alumni from your school. 4) Offer value before asking for help. "
                "5) Follow up meaningfully after connecting. Remember, 85% of jobs are filled through networks!")

    elif any(kw in message_lower for kw in ['cover letter', 'application letter']):
        return ("Cover letter tips: 1) Address it to a specific person when possible. 2) Hook them in the first paragraph. "
                "3) Highlight achievements, not just duties. 4) Show you researched the company. "
                "5) Keep it to one page. Tailor each letter to the specific role!")

    elif any(kw in message_lower for kw in ['career change', 'switch career', 'change industry', 'new field']):
        return ("Changing careers: 1) Identify transferable skills from your current role. "
                "2) Consider certifications or short courses. 3) Start with side projects or freelance work. "
                "4) Network with people in your target industry. 5) Be patient — career changes take time. "
                "You've got this!")

    elif any(kw in message_lower for kw in ['freelance', 'freelancing', 'self employed', 'gig', 'contract']):
        return ("Freelancing tips: 1) Start on platforms like Upwork or Fiverr. 2) Build a strong portfolio. "
                "3) Set clear rates and contracts. 4) Network with other freelancers. "
                "5) Manage your finances carefully (taxes, savings). Starting small is perfectly okay!")

    elif any(kw in message_lower for kw in ['yes', 'sure', 'okay', 'ok', 'alright', 'yeah', 'yep']):
        return ("Great! What specific area would you like to focus on? I can help with:\n"
                "- CV/Resume optimization\n"
                "- Interview preparation\n"
                "- Job search strategies\n"
                "- Skill development\n"
                "- Salary negotiation\n\nJust let me know!")

    elif any(kw in message_lower for kw in ['no', 'nah', 'nope', 'not now', 'nothing', "that's all", "that is all"]):
        return ("No problem at all! If you ever need career advice or have questions, "
                "I'm just a message away. Best of luck with your career journey!")

    elif any(kw in message_lower for kw in ['who are you', 'what are you', 'your name', 'introduce']):
        return ("I'm CareerBot! I'm an AI career assistant designed to help job seekers like you. "
                "I can provide guidance on CVs, interviews, job searching, skills, and career planning. "
                "Think of me as your personal career coach, available 24/7!")

    else:
        return ("Hi! I'm CareerBot. I can help you with CV optimization, interview preparation, "
                "skill development, and career guidance. What would you like to work on today?")


# ==============================================================================
# FEATURE: One-Click CV Bullet Optimizer
# ==============================================================================

def _extract_bullets(cv_text: str) -> list:
    """Extract bullet point lines from CV text."""
    lines = cv_text.split('\n')
    bullets = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('•', '-', '–', '→', '*', '▸', '○', '●')):
            content = stripped.lstrip('•-–→*▸○● ').strip()
            if len(content) > 20:
                bullets.append(content)
        elif (
            len(stripped) > 30
            and stripped[0].isupper()
            and not stripped.endswith(':')
            and any(stripped.lower().startswith(verb) for verb in [
                'led', 'built', 'developed', 'designed', 'managed', 'created', 'implemented',
                'increased', 'reduced', 'improved', 'delivered', 'launched', 'achieved',
                'optimized', 'automated', 'mentored', 'collaborated', 'drove', 'spearheaded',
                'established', 'coordinated', 'negotiated', 'analyzed', 'resolved', 'migrated',
                'integrated', 'deployed', 'maintained', 'supported', 'trained', 'generated',
            ])
        ):
            bullets.append(stripped)
    return bullets


def optimize_cv_bullets(cv_text: str, missing_keywords: list, job_title: str) -> dict:
    """
    Rewrite CV bullet points to naturally incorporate missing keywords from a job description.

    Returns:
        dict with keys:
            - bullets: list of {original, optimized, keywords_added, change_reason, accepted}
            - summary: str
            - keywords_added: int
    """
    bullet_lines = _extract_bullets(cv_text)

    if not bullet_lines:
        return {'bullets': [], 'summary': 'No bullet points found in CV.', 'keywords_added': 0}

    keywords_str = ', '.join(missing_keywords[:20]) if missing_keywords else 'none'

    client = _get_openai_client()
    if client:
        try:
            bullets_block = '\n'.join(f'{i + 1}. {b}' for i, b in enumerate(bullet_lines[:20]))
            prompt = f"""You are a professional CV writer and career coach.

Target job: {job_title}
Missing keywords to incorporate: {keywords_str}

For each bullet point below, rewrite it to:
1. Naturally incorporate 1-2 of the missing keywords where relevant
2. Strengthen impact with stronger action verbs
3. Add quantifiable metrics where missing (use realistic placeholders like [X%], [N users])
4. Keep it concise (1-2 lines max)
If a bullet is already strong and no keyword fits naturally, keep it unchanged.

CV Bullets:
{bullets_block}

Respond with a JSON array ONLY. Each element:
{{"original": "...", "optimized": "...", "keywords_added": ["kw1"], "change_reason": "brief reason"}}"""

            response = client.chat.completions.create(
                model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.4,
                max_tokens=3000,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith('```'):
                import re as _re2
                raw = _re2.sub(r'^```[a-z]*\n?', '', raw)
                raw = _re2.sub(r'\n?```$', '', raw)
            data = json.loads(raw)
            kw_total = sum(len(item.get('keywords_added', [])) for item in data)
            bullets = [
                {
                    'original': item.get('original', ''),
                    'optimized': item.get('optimized', ''),
                    'keywords_added': item.get('keywords_added', []),
                    'change_reason': item.get('change_reason', ''),
                    'accepted': False,
                }
                for item in data
            ]
            summary = (
                f'Optimized {len(bullets)} bullet points, weaving in {kw_total} keywords '
                f'for the {job_title} role. Review and accept the suggestions you like.'
            )
            return {'bullets': bullets, 'summary': summary, 'keywords_added': kw_total}
        except Exception:
            pass

    # NLP fallback
    bullets = []
    kw_total = 0
    for bullet in bullet_lines[:20]:
        optimized = bullet
        added = []
        for kw in missing_keywords[:3]:
            if kw.lower() not in bullet.lower():
                optimized = f'{optimized} (with {kw})'
                added.append(kw)
                kw_total += 1
                break
        bullets.append({
            'original': bullet,
            'optimized': optimized,
            'keywords_added': added,
            'change_reason': 'Keyword added to improve ATS match.',
            'accepted': False,
        })
    return {
        'bullets': bullets,
        'summary': f'Basic optimization applied. Enable AI for smarter rewrites.',
        'keywords_added': kw_total,
    }


# ==============================================================================
# FEATURE: Cover Letter Scanner
# ==============================================================================

def scan_cover_letter(cover_letter_text: str, job_description_text: str) -> dict:
    """
    Score an existing cover letter against a job description.

    Returns:
        dict with match_score, matching_keywords, missing_keywords,
        tone_score, tone_label, strengths, improvements, overall_feedback.
    """
    client = _get_openai_client()
    if client:
        try:
            prompt = f"""You are an expert career coach and ATS specialist.

Analyse this cover letter against the job description and return a JSON evaluation.

JOB DESCRIPTION:
{job_description_text[:2000]}

COVER LETTER:
{cover_letter_text[:2000]}

Return ONLY valid JSON:
{{
  "match_score": 72,
  "matching_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["missing1", "missing2"],
  "tone_score": 85,
  "tone_label": "Professional",
  "strengths": ["Clearly addresses the role requirements"],
  "improvements": ["Add specific metrics", "Mention the company by name"],
  "overall_feedback": "Your cover letter is well-structured but..."
}}"""

            response = client.chat.completions.create(
                model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.3,
                max_tokens=1500,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith('```'):
                import re as _re3
                raw = _re3.sub(r'^```[a-z]*\n?', '', raw)
                raw = _re3.sub(r'\n?```$', '', raw)
            return json.loads(raw)
        except Exception:
            pass

    # NLP fallback
    import re as _re4
    jd_words = set(_re4.findall(r'\b[a-zA-Z]{4,}\b', job_description_text.lower()))
    cl_words = set(_re4.findall(r'\b[a-zA-Z]{4,}\b', cover_letter_text.lower()))
    common = jd_words & cl_words
    missing = list(jd_words - cl_words)[:10]
    score = round(min(100, len(common) / max(len(jd_words), 1) * 200), 1)
    return {
        'match_score': score,
        'matching_keywords': list(common)[:15],
        'missing_keywords': missing,
        'tone_score': 70.0,
        'tone_label': 'Professional',
        'strengths': ['Contains relevant keywords from the job description.'],
        'improvements': [f'Consider adding: {", ".join(missing[:5])}'] if missing else [],
        'overall_feedback': f'Your cover letter matches {score}% of the job description keywords.',
    }


# ==============================================================================
# FEATURE: Line-by-Line Bullet Point Feedback
# ==============================================================================

def analyze_bullet_points(cv_text: str) -> list:
    """
    Analyse each CV bullet point for quality: action verb, metrics, impact, length.

    Returns:
        list of dicts: {text, score, has_action_verb, has_metric, feedback, suggested_rewrite, level}
    """
    bullet_lines = _extract_bullets(cv_text)
    if not bullet_lines:
        return []

    client = _get_openai_client()
    if client:
        try:
            bullets_block = '\n'.join(f'{i + 1}. {b}' for i, b in enumerate(bullet_lines[:25]))
            prompt = f"""You are a professional CV reviewer.

For each bullet point below, evaluate quality and return feedback.

Bullet Points:
{bullets_block}

Respond with ONLY a JSON array. Each element:
{{
  "text": "original bullet text",
  "score": 75,
  "has_action_verb": true,
  "has_metric": false,
  "feedback": "Good action verb but lacks quantifiable result.",
  "suggested_rewrite": "Led development of X, reducing load time by 40%",
  "level": "good"
}}

Score: 80-100=strong, 60-79=good, 0-59=weak. level must be "strong", "good", or "weak"."""

            response = client.chat.completions.create(
                model='qwen/qwen3.8-27b' if settings.OPENAI_API_KEY.startswith('gsk_') else 'gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.3,
                max_tokens=3000,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith('```'):
                raw = re.sub(r'^```[a-z]*\n?', '', raw)
                raw = re.sub(r'\n?```$', '', raw)
            return json.loads(raw)
        except Exception:
            pass

    # NLP fallback
    strong_verbs = {
        'led', 'built', 'developed', 'designed', 'managed', 'created', 'implemented',
        'increased', 'reduced', 'improved', 'delivered', 'launched', 'achieved',
        'optimized', 'automated', 'mentored', 'drove', 'spearheaded', 'established',
    }
    metric_pat = re.compile(r'\d+[%$km]?|\d+\s*(percent|users|clients|million|thousand)', re.I)
    results = []
    for bullet in bullet_lines[:25]:
        first_word = bullet.split()[0].lower().rstrip('s') if bullet.split() else ''
        has_action_verb = first_word in strong_verbs
        has_metric = bool(metric_pat.search(bullet))
        score = 40
        if has_action_verb:
            score += 30
        if has_metric:
            score += 25
        if len(bullet) > 60:
            score += 5
        score = min(score, 100)
        level = 'strong' if score >= 80 else ('good' if score >= 60 else 'weak')
        fb = []
        if not has_action_verb:
            fb.append('Start with a strong action verb (e.g., Led, Built, Delivered).')
        if not has_metric:
            fb.append('Add a quantifiable result (e.g., reduced costs by 30%).')
        if not fb:
            fb.append('Good bullet! Consider adding more specific impact.')
        results.append({
            'text': bullet,
            'score': score,
            'has_action_verb': has_action_verb,
            'has_metric': has_metric,
            'feedback': ' '.join(fb),
            'suggested_rewrite': bullet,
            'level': level,
        })
    return results
