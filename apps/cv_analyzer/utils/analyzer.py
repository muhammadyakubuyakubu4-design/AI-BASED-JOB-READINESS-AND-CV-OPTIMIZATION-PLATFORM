"""
CV Analyzer - NLP-based analysis of CV content for ATS compatibility,
grammar quality, keyword density, and formatting.
"""
import re
from typing import Optional


def calculate_ats_score(text: str, sections: dict) -> float:
    """
    Calculate an ATS (Applicant Tracking System) compatibility score.
    Checks for: standard sections, keywords, formatting, file-parsability.
    """
    score = 0.0
    max_score = 100.0
    points_per_check = 10

    # Check for essential sections (40 points)
    essential_sections = ['education', 'experience', 'skills', 'contact']
    for section in essential_sections:
        if sections.get(section, '').strip():
            score += points_per_check

    # Check for contact info completeness (20 points)
    from .parser import extract_contact_info
    contact = extract_contact_info(text)
    if contact.get('email'):
        score += 7
    if contact.get('phone'):
        score += 7
    if contact.get('linkedin') or contact.get('github'):
        score += 6

    # Check text length (10 points) - ideal 400-800 words
    word_count = len(text.split())
    if 300 <= word_count <= 1000:
        score += points_per_check
    elif 200 <= word_count < 300 or 1000 < word_count <= 1200:
        score += 5

    # Check for action verbs (10 points)
    action_verbs = [
        'developed', 'managed', 'led', 'created', 'implemented', 'designed',
        'built', 'improved', 'achieved', 'delivered', 'coordinated', 'analyzed',
        'increased', 'reduced', 'streamlined', 'collaborated', 'mentored',
    ]
    text_lower = text.lower()
    verbs_found = sum(1 for v in action_verbs if v in text_lower)
    if verbs_found >= 5:
        score += points_per_check
    elif verbs_found >= 2:
        score += 5

    # Check for quantifiable achievements (10 points)
    has_numbers = bool(re.search(r'\d+%|\$\d+|\d+\s*(million|thousand|users|clients|years)', text_lower))
    if has_numbers:
        score += points_per_check

    return min(round(score, 1), max_score)


def calculate_grammar_score(text: str) -> float:
    """
    Calculate a grammar and professionalism score based on heuristic checks.
    """
    score = 100.0
    deductions = 0

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Check for very short lines (likely formatting issues)
    short_lines = sum(1 for l in lines if 0 < len(l) < 3)
    deductions += min(short_lines * 2, 10)

    # Check for excessive capitalization
    caps_lines = sum(1 for l in lines if l.isupper() and len(l) > 10)
    deductions += min(caps_lines * 3, 15)

    # Check for common informal words
    informal_words = ['gonna', 'wanna', 'kinda', 'sorta', 'etc etc', 'stuff', 'things']
    text_lower = text.lower()
    informal_found = sum(1 for w in informal_words if w in text_lower)
    deductions += informal_found * 5

    # Check for repetition (simple check)
    words = text_lower.split()
    if len(words) > 10:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            deductions += 10

    # Bonus for professional tone indicators
    professional_terms = ['proficient', 'experienced', 'demonstrated', 'expertise', 'proven']
    professional_count = sum(1 for t in professional_terms if t in text_lower)
    bonus = min(professional_count * 2, 10)

    return max(0, min(100, score - deductions + bonus))


def calculate_keyword_score(cv_text: str, job_text: Optional[str] = None) -> float:
    """
    Calculate keyword optimization score.
    If job_text is provided, measures overlap with job description.
    Otherwise, checks against common industry keywords.
    """
    if job_text:
        return _calculate_job_keyword_match(cv_text, job_text)

    # General keyword scoring
    industry_keywords = [
        'team', 'project', 'develop', 'manage', 'implement', 'design',
        'analyze', 'lead', 'communicate', 'deliver', 'achieve', 'improve',
        'experience', 'skill', 'knowledge', 'result', 'solution',
    ]

    cv_lower = cv_text.lower()
    found = sum(1 for kw in industry_keywords if kw in cv_lower)
    return min(round((found / len(industry_keywords)) * 100, 1), 100)


def _calculate_job_keyword_match(cv_text: str, job_text: str) -> float:
    """Calculate keyword match between CV and job description."""
    # Extract meaningful words (filter stopwords)
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
        'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'we', 'you', 'he', 'she', 'it',
        'our', 'your', 'his', 'her', 'its', 'their', 'them', 'us', 'me',
    }

    def get_keywords(text):
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return {w for w in words if w not in stopwords}

    job_keywords = get_keywords(job_text)
    cv_keywords = get_keywords(cv_text)

    if not job_keywords:
        return 0.0

    overlap = job_keywords.intersection(cv_keywords)
    return min(round((len(overlap) / len(job_keywords)) * 100, 1), 100)


def calculate_format_score(text: str, sections: dict) -> float:
    """Calculate a formatting and structure score."""
    score = 0.0

    # Has all key sections
    key_sections = ['education', 'experience', 'skills']
    sections_present = sum(1 for s in key_sections if sections.get(s, '').strip())
    score += (sections_present / len(key_sections)) * 40

    # Reasonable length
    word_count = len(text.split())
    if 300 <= word_count <= 800:
        score += 30
    elif 200 <= word_count <= 1000:
        score += 20

    # Has contact section
    if sections.get('contact', '').strip() or _has_contact_info(text):
        score += 20

    # Has summary/objective
    if sections.get('summary', '').strip():
        score += 10

    return min(round(score, 1), 100)


def _has_contact_info(text: str) -> bool:
    """Check if text has any contact information."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    return bool(re.search(email_pattern, text) or re.search(phone_pattern, text))


def generate_suggestions(cv_text: str, sections: dict, scores: dict) -> list:
    """Generate actionable improvement suggestions based on analysis."""
    suggestions = []

    # ATS suggestions
    if scores.get('ats_score', 0) < 70:
        if not sections.get('summary', '').strip():
            suggestions.append({
                'category': 'Structure',
                'priority': 'high',
                'suggestion': 'Add a professional summary at the top of your CV to quickly convey your value proposition.',
                'impact': 'Significantly improves ATS compatibility and recruiter first impression.',
            })

        if not sections.get('skills', '').strip():
            suggestions.append({
                'category': 'Content',
                'priority': 'high',
                'suggestion': 'Add a dedicated Skills section listing your technical and soft skills.',
                'impact': 'ATS systems scan for keyword-rich skills sections.',
            })

    # Experience suggestions
    text_lower = cv_text.lower()
    action_verbs = ['developed', 'managed', 'led', 'implemented', 'achieved', 'delivered']
    if not any(v in text_lower for v in action_verbs):
        suggestions.append({
            'category': 'Language',
            'priority': 'medium',
            'suggestion': 'Use strong action verbs to start bullet points (e.g., Developed, Managed, Delivered).',
            'impact': 'Makes your experience sound more impactful and professional.',
        })

    # Quantification suggestion
    if not re.search(r'\d+%|\$\d+|\d+\s*(million|thousand|users)', text_lower):
        suggestions.append({
            'category': 'Impact',
            'priority': 'medium',
            'suggestion': 'Add quantifiable achievements (e.g., "Increased sales by 25%", "Managed team of 10 engineers").',
            'impact': 'Quantified results make your CV stand out to recruiters.',
        })

    # Contact suggestions
    from .parser import extract_contact_info
    contact = extract_contact_info(cv_text)
    if not contact.get('linkedin'):
        suggestions.append({
            'category': 'Contact',
            'priority': 'low',
            'suggestion': 'Add your LinkedIn profile URL to increase professional credibility.',
            'impact': 'Recruiters commonly check LinkedIn profiles.',
        })

    # Length suggestion
    word_count = len(cv_text.split())
    if word_count < 200:
        suggestions.append({
            'category': 'Length',
            'priority': 'high',
            'suggestion': 'Your CV appears too short. Expand on your experience, projects, and achievements.',
            'impact': 'A well-detailed CV increases your chances significantly.',
        })
    elif word_count > 1200:
        suggestions.append({
            'category': 'Length',
            'priority': 'medium',
            'suggestion': 'Your CV may be too long. Consider condensing to 1-2 pages focusing on most relevant experience.',
            'impact': 'Recruiters spend an average of 7 seconds on initial CV review.',
        })

    return suggestions


def get_missing_keywords(cv_text: str, job_text: str) -> dict:
    """Identify keywords present in job description but missing from CV."""
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'will', 'would', 'could', 'should', 'this', 'that',
        'we', 'you', 'he', 'she', 'it', 'our', 'your', 'its', 'their',
    }

    def get_keywords(text):
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return {w for w in words if w not in stopwords}

    job_keywords = get_keywords(job_text)
    cv_keywords = get_keywords(cv_text)

    missing = job_keywords - cv_keywords
    matching = job_keywords.intersection(cv_keywords)

    # Filter to only significant keywords (longer words more likely meaningful)
    significant_missing = sorted([w for w in missing if len(w) > 4], key=len, reverse=True)[:20]
    significant_matching = sorted([w for w in matching if len(w) > 4], key=len, reverse=True)[:20]

    return {
        'missing': significant_missing,
        'matching': significant_matching,
        'match_percentage': round(len(matching) / max(len(job_keywords), 1) * 100, 1),
    }
