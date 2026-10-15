# CareerAI — AI Job Readiness & CV Optimization Platform

## Overview

CareerAI is a Django-based web platform that helps job seekers optimize their CVs, match job descriptions, assess career readiness, prepare for interviews, and get AI-powered career recommendations.

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Apps & Modules](#4-apps--modules)
5. [Models](#5-models)
6. [URLs & Routes](#6-urls--routes)
7. [Authentication & Authorization](#7-authentication--authorization)
8. [Theme System](#8-theme-system)
9. [Email System](#9-email-system)
10. [AI Integration](#10-ai-integration)
11. [File Uploads](#11-file-uploads)
12. [Templates](#12-templates)
13. [Static Assets](#13-static-assets)
14. [Setup & Deployment](#14-setup--deployment)
15. [Environment Variables](#15-environment-variables)

---

## 1. Architecture

```
Browser ──► Django ──► MySQL
                │
                ├── OpenAI / Groq API (AI)
                ├── Mailtrap (Email)
                └── Google OAuth
```

- **Framework**: Django 5.2.2
- **Database**: MySQL 8.0 (via PyMySQL driver)
- **Frontend**: Bootstrap 5.3, Chart.js, Font Awesome 6
- **Static Files**: WhiteNoise with compressed manifest storage
- **Containerization**: Docker (Nginx + Gunicorn + MySQL)

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, Django 5.2.2 |
| Database | MySQL 8.0 |
| ORM | Django ORM + PyMySQL |
| Authentication | django-allauth (email + Google OAuth) |
| AI | OpenAI API / Groq API (LLaMA 3.3 70B) |
| Email | django-anymail + Mailtrap |
| PDF | ReportLab, xhtml2pdf |
| Document Parsing | PyPDF2, python-docx |
| NLP (fallback) | spaCy, NLTK |
| Frontend | Bootstrap 5.3, Chart.js, Font Awesome 6 |
| Static Files | WhiteNoise |
| Container | Docker, Gunicorn, Nginx |

---

## 3. Project Structure

```
├── config/                 # Django project configuration
│   ├── settings.py         # Main settings
│   ├── urls.py             # Root URL configuration
│   ├── middleware.py       # Maintenance mode middleware
│   └── context_processors.py  # Global template context
│
├── apps/
│   ├── admin_panel/        # Custom admin dashboard
│   ├── authentication/     # User auth (email + Google OAuth)
│   ├── dashboard/          # Landing page & user dashboard
│   ├── cv_analyzer/        # CV upload, parsing, AI analysis
│   ├── job_matching/       # Job description matching
│   ├── assessment/         # Skills & readiness assessment
│   ├── interview_prep/     # Interview preparation
│   ├── career/             # Career recommendations & cover letters
│   ├── notifications/      # In-app notifications
│   └── common/             # Shared utilities
│
├── templates/              # 56 HTML templates
├── static/                 # CSS, JS, images
├── media/                  # User uploads
└── docs/                   # Documentation
```

---

## 4. Apps & Modules

### 4.1 `authentication`
Custom email-based auth extending Django's `AbstractUser`. Integrates Google OAuth via django-allauth.

- **Model**: `CustomUser` (email as USERNAME_FIELD, role-based: admin/user)
- **Key Views**: register, login, logout, verify email, password reset
- **Adapters**: `CustomAccountAdapter` (blocks email signup — allows social signup), `CustomSocialAccountAdapter` (sets email_verified=True)

### 4.2 `dashboard`
Public landing page and authenticated user dashboard.

- **Model**: `UserProfile` (auto-created via signal on user creation)
- **Key Views**: landing, dashboard (stats/charts), profile (view/edit), progress, report (PDF)
- **Features**: Activity chart, score trends, monthly progress, profile completion tracker

### 4.3 `cv_analyzer`
Core module — handles CV upload, parsing, AI analysis, and enhancement.

- **Models**: `CVUpload`, `CVAnalysis`, `CoverLetter`
- **Key Views**: upload, analysis (scores/sections/skills/suggestions), enhance (AI rewrite), match_jd, render (inline preview), compare (version diff), resume_templates (3 designs)
- **Analysis Scores**: ATS (0-100), Grammar, Keyword, Format, Overall
- **File Types**: PDF (PyPDF2) and DOCX (python-docx)

### 4.4 `job_matching`
Matches user CV against job descriptions and provides an integrated Job Application Tracker (Kanban CRM).

- **Models**:
  - `JobDescription`: `title`, `company`, `location`, `job_type`, `salary_range`, `description`, `job_url`, `is_archived`
  - `JobMatch`: `user`, `cv_upload`, `job_description`, `match_score`, `matching_keywords`, `missing_keywords`, `matching_skills`, `missing_skills`, `suggestions`, `strength_areas`, `gap_areas`, `section_analysis`, `optimize_plan`, `ai_summary`, `is_saved`, `application_status` (Saved, Applied, Interview, Offered, Rejected), `notes`, `follow_up_date`, `ats_platform`, `ats_tips`
- **Key Views**:
  - `matching` (`/jobs/`): Input job description, detect ATS platform, run matching analysis
  - `result` (`/jobs/result/<id>/`): Match scores, keyword gaps, section breakdown, ATS optimization tips
  - `history` (`/jobs/history/`): Past job matches and scores
  - `tracker` (`/jobs/tracker/`): Visual Kanban board tracking application pipeline statuses, follow-up dates, notes, and ATS-specific advice
  - `update_status` (`/jobs/update-status/`): Endpoint to update application status, follow-up dates, and notes dynamically
- **ATS Detection**: Built-in `ats_detector.py` identifies major ATS platforms (Workday, Taleo, Greenhouse, Lever, iCIMS) from job URLs or descriptions and provides tailored formatting guidance.

### 4.5 `assessment`
Multi-dimensional career readiness assessment.

- **Models**: `UserSkill`, `Assessment`
- **Dimensions**: Technical, Soft Skills, Experience, Education
- **Output**: Readiness score (0-100), career level, skill gaps, strengths, action plan

### 4.6 `interview_prep`
AI-generated interview question sessions.

- **Model**: `InterviewSession`
- **Question Types**: Behavioral, Technical, Situational
- **Features**: General tips, preparation checklist, career chatbot

### 4.7 `career`
Career path recommendations and cover letter generator.

- **Model**: `CareerRecommendation`
- **Output**: Recommended skills, courses, career paths, certifications, job titles
- **Cover Letters**: Generate, delete, export (PDF/DOCX/TXT)

### 4.8 `notifications`
In-app notification system with AJAX polling.

- **Model**: `Notification` (types: info/success/warning/error/cv/job/assessment/career/system)
- **Features**: Read/unread tracking, priority levels, auto-expire, count API

### 4.9 `admin_panel`
Enterprise admin dashboard (separate from Django admin).

- **Models**: `ActivityLog`, `SystemSetting`
- **26 Views**: KPI dashboard, user/CV/job/skill/assessment/interview management, AI monitoring, activity logs, notifications/broadcast, CSV exports, system settings
- **Features**: Chart.js analytics, bulk actions, real-time API stats

---

## 5. Models

| App | Model | Key Fields |
|-----|-------|------------|
| authentication | `CustomUser` | email, role, email_verified, email_verification_token, is_deleted |
| dashboard | `UserProfile` | user, bio, avatar, phone, location, current_role, linkedin_url, years_experience, target_role, education_level, readiness_score |
| cv_analyzer | `CVUpload` | user, file, original_filename, file_type, file_size, parsed_text, is_active |
| cv_analyzer | `CVAnalysis` | cv_upload, ats_score, grammar_score, keyword_score, format_score, overall_score, extracted_sections, extracted_skills, suggestions (JSON) |
| cv_analyzer | `CoverLetter` | user, job_title, company_name, content, tone |
| job_matching | `JobDescription` | user, title, company, description, job_type, is_archived |
| job_matching | `JobMatch` | user, cv_upload, job_description, match_score, matching/missing keywords/skills (JSON) |
| assessment | `UserSkill` | user, skill_name, proficiency (1-5), category |
| assessment | `Assessment` | user, readiness_score, technical_score, soft_skills_score, career_level, skill_gaps (JSON) |
| interview_prep | `InterviewSession` | user, job_title, difficulty, behavioral/technical/situational questions (JSON) |
| career | `CareerRecommendation` | user, target_role, recommended_skills/courses/paths/certifications (JSON) |
| admin_panel | `ActivityLog` | user, action_type, description, model_name, ip_address |
| admin_panel | `SystemSetting` | key, label, value, setting_type |
| notifications | `Notification` | user, title, message, notification_type, priority, link, is_read |

---

## 6. URLs & Routes

### Root Routes (`/`)

| Path | App | Purpose |
|------|-----|---------|
| `/` | dashboard | Landing page |
| `/dashboard/` | dashboard | User dashboard |
| `/auth/` | authentication | Login, register, password reset |
| `/accounts/` | allauth | Google OAuth callbacks |
| `/cv/` | cv_analyzer | CV management |
| `/jobs/` | job_matching | Job matching |
| `/assessment/` | assessment | Skills & assessment |
| `/interview/` | interview_prep | Interview preparation |
| `/career/` | career | Career recommendations |
| `/notifications/` | notifications | Notification center |
| `/admin/` | Django admin | Django admin panel |
| `/admin_panel/` | admin_panel | Custom admin dashboard |

---

## 7. Authentication & Authorization

### Login Methods
1. **Email + Password** — Custom `LoginForm`, handled by `login_view`
2. **Google OAuth** — django-allauth via `/accounts/google/login/`

### User Roles
- `admin` — Full access to admin panel
- `user` — Standard user access

### Guards
- `@login_required` on all authenticated views
- `@admin_required` decorator on admin_panel views

### Password Reset Flow
1. User submits email on `/auth/password-reset/`
2. HTML email sent via Mailtrap
3. User clicks link with uidb64 + token
4. Enters new password on confirmation page
5. Redirect to completion page

---

## 8. Theme System

Dual theme system using CSS custom properties and two independent toggle mechanisms:

### Landing Page (`landing.html`)
- `data-landing-theme` attribute on `<html>`
- Toggle button `#landingThemeToggle`
- Persisted in `localStorage` key `landing_theme`
- Separate CSS variable sets for dark/light

### Authenticated Pages (`base.html`, admin)
- `data-bs-theme` attribute on `<html>` (Bootstrap 5.3 convention)
- Toggle button `#themeToggle`
- Persisted in `localStorage` key `theme`
- Defined in `main.css` with `--bg-body`, `--bg-card`, etc.

### Admin Panel
- Uses separate `data-ap-theme` attribute
- Separate localStorage key `ap_theme`
- Defined in `admin_panel.css` with `--ap-` prefix variables

---

## 9. Email System

### Provider: Mailtrap (via django-anymail)
- Config in `config/settings.py`: `ANYMAIL_MAILTRAP_API_TOKEN`
- Default from: `hello@demomailtrap.co`
- Backend: `anymail.backends.mailtrap.EmailBackend`

### Transactional Emails
1. **Email Verification** — Sent on registration, includes verification link with token
2. **Password Reset** — Custom HTML template with reset link

### Templates
- `templates/emails/verify_email.html`
- `templates/emails/password_reset.html`

---

## 10. AI Integration

### Provider Selection
The `OPENAI_API_KEY` environment variable determines the provider:
- **Starts with `gsk_`** → Routes to Groq API (`https://api.groq.com/openai/v1`)
- **Otherwise** → Routes to OpenAI API

### AI Features
| Feature | File | Description |
|---------|------|-------------|
| CV Analysis | `apps/cv_analyzer/utils/ai_service.py` | Parses CV, generates scores and suggestions |
| CV Enhancement | `apps/cv_analyzer/views.py` | 7 rewrite actions: improve/grammar/tone/clarity/impact/bullet/summary |
| Job Matching | `apps/cv_analyzer/views.py` | Compares CV against job description |
| Interview Questions | `apps/interview_prep/views.py` | Generates behavioral/technical/situational questions |
| Career Recommendations | `apps/career/views.py` | Generates career paths, skills, courses |
| Career Chatbot | `apps/career/views.py`, `apps/interview_prep/views.py` | AI-powered career guidance |
| Readiness Assessment | `apps/assessment/views.py` | Multi-dimensional career readiness scoring |

### Fallback
When AI is unavailable, NLP-based analysis (spaCy + NLTK) provides basic keyword extraction and scoring.

---

## 11. File Uploads

| Type | Location | Validation |
|------|----------|------------|
| CV Files | `media/cv_uploads/` | 5MB max, pdf/docx only, content-header validation |
| Avatars | `media/avatars/` | Image files via Pillow |

### Allowed CV Extensions
```python
ALLOWED_CV_EXTENSIONS = ['pdf', 'docx']
```

### Byte-Level Validation
Checks file header bytes:
- PDF: starts with `%PDF-`
- DOCX: starts with `PK\x03\x04` (ZIP format)

---

## 12. Templates

56 template files across the project:

| Directory | Count | Description |
|-----------|-------|-------------|
| `templates/` | 3 root | base.html, landing.html, 503.html |
| `templates/auth/` | 7 | Login, register, password reset flow |
| `templates/dashboard/` | 6 | Dashboard, profile, progress, report |
| `templates/cv/` | 6 | Upload, analysis, history, compare, templates |
| `templates/job/` | 3 | Matching, result, history |
| `templates/assessment/` | 3 | Assessment, skills, result |
| `templates/interview/` | 3 | Generate, session, history |
| `templates/career/` | 4 | Recommendations, cover letters |
| `templates/notifications/` | 1 | Notification list |
| `templates/admin_panel/` | 15 | Admin dashboard, management views |
| `templates/emails/` | 2 | HTML email templates |
| `templates/resume_templates/` | 3 | Resume design templates |

---

## 13. Static Assets

### Source (`static/`)
```
static/
├── css/
│   ├── main.css             # 1802 lines — Design system + light/dark theme
│   └── admin_panel.css      # 308 lines — Admin panel theme
├── js/
│   ├── main.js              # 285 lines — Sidebar, theme, chatbot, notifications
│   └── admin_panel.js       # 158 lines — Admin panel functionality
└── images/
    ├── jimage.jpg            # Hero background image
    └── default-avatar.svg    # Default user avatar
```

### CDN Dependencies
- Bootstrap 5.3.3 (CSS + JS)
- Font Awesome 6.5.0
- Chart.js 4.x
- Google Fonts (Poppins)

---

## 14. Setup & Deployment

### Development

```bash
# 1. Clone and enter project
cd JOB

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download spaCy model
python -m spacy download en_core_web_sm

# 5. Configure .env (copy from .env.example)
# Set: SECRET_KEY, DATABASE_URL or DB_*, OPENAI_API_KEY, MAILTRAP_API_TOKEN

# 6. Create MySQL database
mysql -u root -p -e "CREATE DATABASE job_readiness_db CHARACTER SET utf8mb4;"

# 7. Run migrations
python manage.py migrate

# 8. Create site record (for allauth)
python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.update_or_create(id=1, defaults={'domain':'127.0.0.1:8000','name':'127.0.0.1:8000'})"

# 9. Create superuser
python manage.py createsuperuser

# 10. Run server
python manage.py runserver
```

### Docker

```bash
docker-compose up -d
```

The Docker setup includes:
- **nginx**: Reverse proxy (port 80 → Gunicorn 8000)
- **web**: Gunicorn with Django
- **db**: MySQL 8.0

---

## 15. Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SECRET_KEY` | Yes | — | Django secret key |
| `DEBUG` | No | `True` | Debug mode |
| `DB_NAME` | No | `job_readiness_db` | Database name |
| `DB_USER` | No | `root` | Database user |
| `DB_PASSWORD` | No | — | Database password |
| `DB_HOST` | No | `localhost` | Database host |
| `DB_PORT` | No | `3306` | Database port |
| `OPENAI_API_KEY` | No | — | OpenAI or Groq API key |
| `MAILTRAP_API_TOKEN` | No | — | Mailtrap email API token |
| `RESEND_API_KEY` | No | — | Resend email API key (alternative) |

---

## Security Notes

- Session cookie age: 7 days
- Session saved on every request
- CSRF protection enabled
- X-Frame-Options: DENY
- Content-Type sniffing disabled
- CV uploads validated by content (not just extension)
- Soft delete used for CVs and users
- Admin panel protected by `@admin_required` decorator
- All-AI features are opt-in (user triggers analysis)
