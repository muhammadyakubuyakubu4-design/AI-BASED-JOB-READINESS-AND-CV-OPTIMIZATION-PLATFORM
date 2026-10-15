# CareerAI — AI Job Readiness & CV Optimization Platform

A full-stack Django web application that helps job seekers optimize their CVs, match job descriptions, assess career readiness, prepare for interviews, and receive AI-powered career recommendations.

> **Full documentation**: [`docs/SYSTEM.md`](docs/SYSTEM.md)

---

## Quick Start

```bash
# Setup
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
copy .env.example .env   # edit with your settings

# Database
mysql -u root -p -e "CREATE DATABASE job_readiness_db CHARACTER SET utf8mb4;"

# Run
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Features

- **CV Analysis** — Upload PDF/DOCX CVs; get ATS, grammar, keyword & format scores (0-100)
- **Job Matching** — Paste any job description; AI calculates match % and missing keywords/skills
- **Readiness Assessment** — Multi-dimensional score (technical, soft skills, experience, education)
- **Interview Preparation** — AI-generated behavioral, technical & situational questions
- **Career Recommendations** — Personalized career paths, courses, certifications & job titles
- **AI Chatbot** — Real-time career guidance chatbot
- **Cover Letter Generator** — AI-generated cover letters with PDF/DOCX/TXT export
- **Resume Templates** — 3 professional designs (modern, professional, creative) with PDF export
- **CV Version Comparison** — Side-by-side diff of uploaded CV versions
- **Dark/Light Mode** — Persistent theme toggle (3 independent toggles: landing, app, admin)
- **Google OAuth** — Sign in with Google via django-allauth
- **Notifications** — In-app alerts with AJAX polling for unread count
- **PDF Export** — Download analysis reports, resume templates, and cover letters
- **Admin Dashboard** — Enterprise KPI dashboard with analytics, CSV exports, AI monitoring
- **Activity Logging** — Full audit trail of user actions

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, Django 5.2.2 |
| Database | MySQL 8.0 |
| Frontend | Bootstrap 5.3, Chart.js 4, Font Awesome 6 |
| AI | OpenAI API / Groq API (LLaMA 3.3 70B) |
| NLP (fallback) | spaCy, NLTK |
| Email | django-anymail + Mailtrap |
| Auth | Custom email + Google OAuth (django-allauth) |
| PDF | ReportLab, xhtml2pycairo |
| Document Parsing | PyPDF2, python-docx |
| Static | WhiteNoise (CompressedManifestStaticFilesStorage) |
| Container | Docker, Gunicorn, Nginx |

---

## Installation Guide

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip
- AppServ or any web server (for development: Django dev server)

### Step 1: Clone / Navigate to project

```bash
cd C:\AppServ\www\JOB
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download NLP models

```bash
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
```

### Step 5: Configure environment variables

Copy `.env.example` to `.env` and edit:

```bash
copy .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your-long-random-secret-key
DEBUG=True
DB_NAME=job_readiness_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=3306
OPENAI_API_KEY=sk-...   # optional
```

### Step 6: Create MySQL Database

```sql
CREATE DATABASE job_readiness_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 7: Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 8: Create a superuser (Admin)

```bash
python manage.py createsuperuser
```

When prompted, set the role to `admin` in the Django admin panel after creation.

### Step 9: Collect static files

```bash
python manage.py collectstatic --noinput
```

### Step 10: Start the development server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

---

## Project Structure

```
JOB/
├── apps/
│   ├── authentication/     # User registration, login, password reset
│   ├── dashboard/          # Landing page, user dashboard, profile
│   ├── cv_analyzer/        # CV upload, AI analysis, export
│   │   └── utils/
│   │       ├── parser.py   # PDF/DOCX parsing
│   │       ├── analyzer.py # NLP scoring
│   │       └── ai_service.py # OpenAI integration
│   ├── job_matching/       # Job description matching
│   ├── assessment/         # Skills & readiness assessment
│   ├── interview_prep/     # Interview question generation
│   ├── career/             # Career path recommendations
│   └── notifications/      # In-app notification system
├── config/
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL configuration
│   └── context_processors.py
├── static/
│   ├── css/main.css        # Full design system
│   ├── js/main.js          # Sidebar, dark mode, chatbot
│   └── images/
├── templates/
│   ├── base.html           # Authenticated layout
│   ├── landing.html        # Public landing page
│   ├── auth/               # Login, register, password reset
│   ├── dashboard/          # Dashboard, profile
│   ├── cv/                 # Upload, analysis, history
│   ├── job/                # Matching, results, history
│   ├── assessment/         # Assessment, skills
│   ├── interview/          # Prep sessions
│   ├── career/             # Career recommendations
│   └── notifications/
├── .env                    # Environment variables (not in git)
├── .env.example
├── manage.py
└── requirements.txt
```

---

## Project Structure

```
├── config/              # Django settings, URLs, middleware
├── apps/
│   ├── authentication/  # Custom user model, email auth, Google OAuth
│   ├── dashboard/       # Landing page, user dashboard, profile, reports
│   ├── cv_analyzer/     # CV upload, AI analysis, enhancement, resume templates
│   ├── job_matching/    # Job description matching & scoring
│   ├── assessment/      # Skills management & readiness assessment
│   ├── interview_prep/  # AI interview question generation
│   ├── career/          # Career recommendations & cover letters
│   ├── notifications/   # In-app notification system
│   ├── admin_panel/     # Custom admin dashboard with analytics
│   └── common/          # Shared utilities
├── templates/           # 56 HTML templates
├── static/              # CSS, JS, images
└── docs/SYSTEM.md       # Full system documentation
```

---

## Key URLs

| Path | Description |
|---|---|
| `/` | Landing page |
| `/auth/login/` | Login (email + Google OAuth) |
| `/auth/register/` | Registration |
| `/dashboard/` | User dashboard with charts |
| `/cv/upload/` | Upload & analyze CV |
| `/cv/history/` | CV upload history |
| `/jobs/` | Job description matching |
| `/assessment/` | Skills & readiness assessment |
| `/interview/` | Interview preparation |
| `/career/` | Career recommendations |
| `/career/cover-letter/` | Cover letter generator |
| `/notifications/` | Notification center |
| `/admin/` | Django admin |
| `/admin_panel/` | Custom admin dashboard |

---

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Django secret key |
| `DEBUG` | No | `True` | Debug mode |
| `DB_NAME` | No | `job_readiness_db` | Database name |
| `DB_USER` | No | `root` | Database user |
| `DB_PASSWORD` | No | — | Database password |
| `DB_HOST` | No | `localhost` | Database host |
| `DB_PORT` | No | `3306` | Database port |
| `OPENAI_API_KEY` | No | — | OpenAI/Groq API key |
| `MAILTRAP_API_TOKEN` | No | — | Mailtrap email API token |

---

## Docker Deployment

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py collectstatic --noinput
```

| Service | Port | Description |
|---|---|---|
| `nginx` | 80 | Reverse proxy |
| `web` | 8000 | Django + Gunicorn |
| `db` | 3306 | MySQL 8.0 |

---

## Documentation

See **[`docs/SYSTEM.md`](docs/SYSTEM.md)** for complete documentation including:

- Full architecture and tech stack details
- All 14 models with field descriptions
- All 56 URL patterns across 10 apps
- Authentication and authorization flow
- Theme system (3 independent dark/light toggles)
- Email system (Mailtrap via django-anymail)
- AI integration (OpenAI/Groq with NLP fallback)
- Template and static file inventory
- Complete setup and deployment guide
