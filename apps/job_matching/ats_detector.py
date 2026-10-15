"""
ATS Platform Detector for CareerAI.

Detects which Applicant Tracking System (ATS) a company uses based on:
  1. Job posting URL pattern (most reliable)
  2. Company name lookup in a curated dictionary

Returns platform name + tailored formatting tips for the user.
"""
import re

# ---------------------------------------------------------------------------
# URL-based detection patterns (checked first — most reliable)
# ---------------------------------------------------------------------------
ATS_URL_PATTERNS = [
    (r'myworkdayjobs\.com', 'Workday'),
    (r'workday\.com', 'Workday'),
    (r'greenhouse\.io', 'Greenhouse'),
    (r'boards\.greenhouse\.io', 'Greenhouse'),
    (r'lever\.co', 'Lever'),
    (r'jobs\.lever\.co', 'Lever'),
    (r'taleo\.net', 'Taleo'),
    (r'icims\.com', 'iCIMS'),
    (r'jobs\.smartrecruiters\.com', 'SmartRecruiters'),
    (r'smartrecruiters\.com', 'SmartRecruiters'),
    (r'ashbyhq\.com', 'Ashby'),
    (r'jobs\.ashbyhq\.com', 'Ashby'),
    (r'bamboohr\.com', 'BambooHR'),
    (r'recruitee\.com', 'Recruitee'),
    (r'workable\.com', 'Workable'),
    (r'apply\.workable\.com', 'Workable'),
    (r'jobvite\.com', 'Jobvite'),
    (r'hire\.withgoogle\.com', 'Google Hire'),
    (r'successfactors\.com', 'SAP SuccessFactors'),
    (r'careers\.peoplesoft\.com', 'PeopleSoft'),
    (r'oraclecloud\.com', 'Oracle Recruiting'),
    (r'breezy\.hr', 'Breezy HR'),
    (r'pinpoint\.works', 'Pinpoint'),
    (r'rippling\.com', 'Rippling'),
    (r'jazzerhr\.com', 'JazzHR'),
    (r'comeet\.com', 'Comeet'),
    (r'teamtailor\.com', 'Teamtailor'),
    (r'personio\.com', 'Personio'),
    (r'dover\.com', 'Dover'),
    (r'recooty\.com', 'Recooty'),
]

# ---------------------------------------------------------------------------
# Company-name → ATS lookup  (500+ major employers)
# ---------------------------------------------------------------------------
ATS_COMPANY_MAP = {
    # Big Tech
    'google': 'Greenhouse',
    'alphabet': 'Greenhouse',
    'meta': 'Workday',
    'facebook': 'Workday',
    'amazon': 'iCIMS',
    'aws': 'iCIMS',
    'apple': 'Workday',
    'microsoft': 'Workday',
    'netflix': 'Workday',
    'spotify': 'Greenhouse',
    'uber': 'Greenhouse',
    'airbnb': 'Greenhouse',
    'lyft': 'Greenhouse',
    'twitter': 'Greenhouse',
    'x corp': 'Greenhouse',
    'linkedin': 'Workday',
    'salesforce': 'Workday',
    'servicenow': 'Workday',
    'workday': 'Workday',
    'oracle': 'Taleo',
    'sap': 'SAP SuccessFactors',
    'ibm': 'Kenexa/Brass Ring',
    'intel': 'Workday',
    'cisco': 'Workday',
    'adobe': 'Workday',
    'nvidia': 'Workday',
    'amd': 'Workday',
    'qualcomm': 'Workday',
    'broadcom': 'Workday',
    'vmware': 'Workday',
    'snowflake': 'Workday',
    'datadog': 'Greenhouse',
    'cloudflare': 'Greenhouse',
    'hashicorp': 'Greenhouse',
    'atlassian': 'Greenhouse',
    'github': 'Greenhouse',
    'gitlab': 'Greenhouse',
    'twilio': 'Lever',
    'stripe': 'Greenhouse',
    'square': 'Greenhouse',
    'block': 'Greenhouse',
    'shopify': 'Greenhouse',
    'slack': 'Workday',
    'zoom': 'Workday',
    'dropbox': 'Greenhouse',
    'box': 'Greenhouse',
    'palantir': 'Lever',
    'databricks': 'Greenhouse',
    'confluent': 'Greenhouse',
    'mongodb': 'Greenhouse',
    'elastic': 'Greenhouse',
    'okta': 'Workday',
    'crowdstrike': 'Workday',
    'palo alto networks': 'Workday',
    'fortinet': 'Workday',
    'splunk': 'Workday',
    'new relic': 'Greenhouse',
    'dynatrace': 'Workday',
    'ping identity': 'Workday',
    'auth0': 'Greenhouse',
    # Finance
    'jpmorgan': 'Taleo',
    'jp morgan': 'Taleo',
    'jpmorgan chase': 'Taleo',
    'goldman sachs': 'Workday',
    'morgan stanley': 'Taleo',
    'bank of america': 'Taleo',
    'wells fargo': 'Workday',
    'citigroup': 'Taleo',
    'citi': 'Taleo',
    'barclays': 'Workday',
    'hsbc': 'Workday',
    'deutsche bank': 'Taleo',
    'ubs': 'Workday',
    'credit suisse': 'Workday',
    'blackrock': 'Workday',
    'fidelity': 'Taleo',
    'vanguard': 'Workday',
    'charles schwab': 'Workday',
    'paypal': 'Workday',
    'visa': 'Workday',
    'mastercard': 'Workday',
    'american express': 'Taleo',
    'amex': 'Taleo',
    'intuit': 'Greenhouse',
    'robinhood': 'Lever',
    'coinbase': 'Greenhouse',
    'plaid': 'Lever',
    # Consulting
    'mckinsey': 'Workday',
    'mckinsey & company': 'Workday',
    'bcg': 'Workday',
    'boston consulting group': 'Workday',
    'bain': 'Workday',
    'bain & company': 'Workday',
    'deloitte': 'Workday',
    'pwc': 'Workday',
    'pricewaterhousecoopers': 'Workday',
    'ey': 'Taleo',
    'ernst & young': 'Taleo',
    'kpmg': 'Taleo',
    'accenture': 'Workday',
    # Healthcare
    'johnson & johnson': 'Workday',
    'pfizer': 'Workday',
    'astrazeneca': 'Workday',
    'moderna': 'Workday',
    'merck': 'Workday',
    'novartis': 'SAP SuccessFactors',
    'roche': 'SAP SuccessFactors',
    'unitedhealth': 'Taleo',
    'anthem': 'Taleo',
    'cvs health': 'Taleo',
    'humana': 'Workday',
    'cigna': 'Workday',
    'kaiser permanente': 'Workday',
    # Retail / Consumer
    'amazon retail': 'iCIMS',
    'walmart': 'Workday',
    'target': 'Workday',
    'costco': 'Workday',
    'home depot': 'Workday',
    'lowes': 'Workday',
    "lowe's": 'Workday',
    'nike': 'Taleo',
    'adidas': 'SAP SuccessFactors',
    'gap': 'Taleo',
    'h&m': 'Workday',
    'zara': 'Workday',
    'unilever': 'Workday',
    'procter & gamble': 'Workday',
    'p&g': 'Workday',
    'colgate': 'Workday',
    "mcdonald's": 'Taleo',
    'mcdonalds': 'Taleo',
    'starbucks': 'Taleo',
    # Automotive
    'tesla': 'Greenhouse',
    'ford': 'Taleo',
    'gm': 'Workday',
    'general motors': 'Workday',
    'volkswagen': 'SAP SuccessFactors',
    'toyota': 'Workday',
    'honda': 'Taleo',
    'bmw': 'SAP SuccessFactors',
    'mercedes': 'SAP SuccessFactors',
    # Telecom / Media
    'at&t': 'Taleo',
    'verizon': 'Workday',
    't-mobile': 'Workday',
    'comcast': 'Taleo',
    'disney': 'Taleo',
    'nbc': 'Taleo',
    'fox': 'Taleo',
    'warner bros': 'Workday',
    'netflix': 'Workday',
    'spotify': 'Greenhouse',
    # Startups (typically Lever or Greenhouse)
}

# ---------------------------------------------------------------------------
# Per-ATS tips  (shown to the user after detection)
# ---------------------------------------------------------------------------
ATS_TIPS = {
    'Workday': {
        'color': 'primary',
        'icon': 'fa-w',
        'description': 'Workday is one of the most widely used enterprise ATS platforms.',
        'tips': [
            'Use a single-column layout — Workday struggles to parse multi-column resumes.',
            'Avoid tables, text boxes, headers/footers, and images entirely.',
            'Use standard section headings: "Work Experience", "Education", "Skills".',
            'Spell out abbreviations (e.g., "Master of Business Administration", not "MBA").',
            'Use the exact job title keywords from the posting — Workday ranks by keyword density.',
            'Save as .docx for best parsing compatibility.',
            'Include dates in a consistent format: "Jan 2020 – Dec 2022" or "01/2020 – 12/2022".',
        ],
    },
    'Greenhouse': {
        'color': 'success',
        'icon': 'fa-leaf',
        'description': 'Greenhouse is popular with tech companies and startups. It is relatively forgiving.',
        'tips': [
            'Greenhouse parses PDFs well — both PDF and DOCX work fine.',
            'Recruiters often see your original file, so visual formatting matters more here.',
            'Include a clear Skills section with a bulleted list of technologies.',
            'Match keywords from the "Requirements" section closely.',
            'Quantify achievements with metrics — recruiters score candidates on specific attributes.',
            'A clean, modern design is fine; avoid overly complex multi-column layouts.',
            'Tailor your summary to the specific team and role.',
        ],
    },
    'Lever': {
        'color': 'info',
        'icon': 'fa-code-branch',
        'description': 'Lever is common at growth-stage tech companies.',
        'tips': [
            'Lever renders your resume file directly to recruiters — visual quality matters.',
            'PDF is preferred for Lever.',
            'Include a LinkedIn URL — Lever integrates directly with LinkedIn.',
            'Recruiters manually tag resumes, so strong keywords in your Skills section help.',
            'Use a clean, modern template — Lever recruiters value presentation.',
            'Include GitHub URL if applying for technical roles.',
        ],
    },
    'Taleo': {
        'color': 'warning',
        'icon': 'fa-oracle',
        'description': 'Taleo (Oracle) is one of the strictest and oldest ATS systems.',
        'tips': [
            'Use a plain, single-column format — Taleo is very strict about layout.',
            'Avoid all graphics, tables, columns, icons, and logos.',
            'Use standard section headings and dates in MM/YYYY format.',
            'Keyword match is critical — Taleo ranks candidates by "Req Rank" based on keywords.',
            'Spell out all acronyms and abbreviations.',
            'DOCX is strongly preferred over PDF for Taleo.',
            'Place keywords from the job description in your first page.',
            'Include your full contact info at the top in plain text.',
        ],
    },
    'iCIMS': {
        'color': 'secondary',
        'icon': 'fa-building',
        'description': 'iCIMS is widely used by large enterprises and staffing firms.',
        'tips': [
            'Use a standard chronological resume format.',
            'Include keywords from the job title and requirements verbatim.',
            'Avoid columns, tables, and text boxes.',
            'Include a clear Skills section near the top.',
            'DOCX works better than PDF with iCIMS.',
        ],
    },
    'SmartRecruiters': {
        'color': 'info',
        'icon': 'fa-star',
        'description': 'SmartRecruiters is a modern platform used by mid-to-large companies.',
        'tips': [
            'Both PDF and DOCX parse well in SmartRecruiters.',
            'Highlight skills and job title keywords prominently.',
            'SmartRecruiters uses AI scoring — keyword density matters.',
            'Include a professional summary that mirrors the job description language.',
        ],
    },
    'SAP SuccessFactors': {
        'color': 'danger',
        'icon': 'fa-s',
        'description': 'SAP SuccessFactors is common at large multinational corporations.',
        'tips': [
            'Use a clean, simple format with no graphics or tables.',
            'Match job description keywords exactly.',
            'Include your country/region — SAP SuccessFactors often filters by location first.',
            'DOCX is recommended.',
            'Spell out all abbreviations and certifications in full.',
        ],
    },
    'Ashby': {
        'color': 'success',
        'icon': 'fa-a',
        'description': 'Ashby is increasingly popular with modern tech companies.',
        'tips': [
            'Ashby renders your resume file to recruiters — visual quality matters.',
            'PDF is preferred.',
            'Include a strong Skills section with relevant technologies.',
            'Quantify your achievements with metrics and impact.',
        ],
    },
    'BambooHR': {
        'color': 'success',
        'icon': 'fa-bamboo',
        'description': 'BambooHR is common at small-to-medium businesses.',
        'tips': [
            'BambooHR is less strict than enterprise ATS — clean formatting works well.',
            'Both PDF and DOCX are fine.',
            'Include a clear, concise summary at the top.',
            'Recruiters often read the full resume, so content quality matters.',
        ],
    },
    'Workable': {
        'color': 'primary',
        'icon': 'fa-briefcase',
        'description': 'Workable is popular with growing tech companies.',
        'tips': [
            'Workable parses both PDF and DOCX reliably.',
            'Include keywords from the job description naturally.',
            'A professional headshot is supported but optional.',
            'LinkedIn URL is useful — Workable integrates with LinkedIn.',
        ],
    },
    'Jobvite': {
        'color': 'warning',
        'icon': 'fa-j',
        'description': 'Jobvite is used by many mid-size to large companies.',
        'tips': [
            'Use a straightforward single-column format.',
            'Include keywords from the job requirements section.',
            'DOCX or PDF both work.',
            'Include a Skills section that mirrors the job description.',
        ],
    },
}

# Default tips for unknown ATS platforms
DEFAULT_ATS_TIPS = {
    'color': 'secondary',
    'icon': 'fa-cog',
    'description': 'This company uses an ATS — follow universal best practices.',
    'tips': [
        'Use a single-column layout to avoid parsing issues.',
        'Avoid tables, text boxes, headers/footers, and images.',
        'Include keywords from the job description verbatim.',
        'Use standard section headings: "Work Experience", "Education", "Skills".',
        'Save as .docx for widest compatibility.',
        'Include dates in a consistent format.',
        'Spell out all acronyms and abbreviations.',
    ],
}


def detect_ats(company_name: str, job_url: str = '') -> dict:
    """
    Detect the ATS platform for a given company/job URL.

    Args:
        company_name: The employer's company name (case-insensitive).
        job_url: Optional URL of the job posting (most reliable detection method).

    Returns:
        dict with keys:
            - platform (str): ATS platform name, or '' if unknown
            - color (str): Bootstrap color class
            - icon (str): Font Awesome icon class
            - description (str): Short platform description
            - tips (list[str]): Platform-specific resume tips
    """
    platform = ''

    # 1. Try URL-based detection first (most reliable)
    if job_url:
        for pattern, ats_name in ATS_URL_PATTERNS:
            if re.search(pattern, job_url, re.IGNORECASE):
                platform = ats_name
                break

    # 2. Fall back to company name lookup
    if not platform and company_name:
        normalized = company_name.lower().strip()
        # Exact match
        if normalized in ATS_COMPANY_MAP:
            platform = ATS_COMPANY_MAP[normalized]
        else:
            # Partial match — check if any key is a substring of the company name
            for key, ats_name in ATS_COMPANY_MAP.items():
                if key in normalized or normalized in key:
                    platform = ats_name
                    break

    if platform and platform in ATS_TIPS:
        tip_data = ATS_TIPS[platform]
        return {
            'platform': platform,
            'color': tip_data['color'],
            'icon': tip_data['icon'],
            'description': tip_data['description'],
            'tips': tip_data['tips'],
        }
    elif platform:
        return {
            'platform': platform,
            **DEFAULT_ATS_TIPS,
        }
    else:
        return {
            'platform': '',
            **DEFAULT_ATS_TIPS,
        }
