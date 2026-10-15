from xhtml2pdf import pisa
import os

html_content = '''
<html>
<head>
<style>
    body { font-family: Helvetica, sans-serif; font-size: 14px; line-height: 1.5; color: #333; }
    h1 { color: #2c3e50; font-size: 24px; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-bottom: 15px;}
    h2 { color: #2980b9; font-size: 18px; margin-top: 20px;}
    h3 { color: #16a085; font-size: 16px; margin-top: 15px;}
    p { margin-bottom: 10px; }
    ul { margin-bottom: 15px; }
    li { margin-bottom: 5px; }
    .highlight { background-color: #f1f8ff; padding: 10px; border-left: 4px solid #3498db; }
</style>
</head>
<body>
    <h1>CareerAI (JOB) - Project Defense Guide</h1>
    <p>A comprehensive overview of the system architecture, features, and underlying logic for your project defense.</p>
    
    <h2>1. System Overview (The Big Picture)</h2>
    <p>CareerAI is a comprehensive, AI-powered career development platform that acts as a personal career coach. The system is divided into several core modules:</p>
    <ul>
        <li><strong>CV Analyzer & Editor:</strong> Uploads resumes, extracts text, calculates performance scores, provides AI-driven suggestions, and dynamically edits the user's MS Word document in real-time.</li>
        <li><strong>Job Matching Engine:</strong> Compares the user's CV against a specific Job Description to calculate a targeted match percentage.</li>
        <li><strong>AI Career Advisor:</strong> Analyzes the user's skills to recommend career paths, generate study plans, suggest job titles, and link directly to real-world hiring companies.</li>
        <li><strong>Learning & Assessment Hub:</strong> Provides AI-generated lessons, quizzes, and study plans to help users upskill.</li>
    </ul>

    <h2>2. How the CV Analysis Works (Step-by-Step)</h2>
    <p>When a user uploads a CV, the system follows a complex pipeline to analyze it:</p>
    <ul>
        <li><strong>Step 1: Document Parsing:</strong> The system takes the PDF or DOCX file and uses backend libraries (<code>pdfplumber</code> for PDFs, <code>python-docx</code> for Word docs) to extract the raw text.</li>
        <li><strong>Step 2: NLP Section Extraction:</strong> The system uses regular expressions (Regex) and Natural Language Processing (NLP) to break the document down into logical categories (Contact, Summary, Experience, Education, Skills, etc.).</li>
        <li><strong>Step 3: Algorithmic Scoring:</strong> The system passes the text through mathematical heuristic engines to calculate the ATS, Grammar, Format, and Keyword scores out of 100.</li>
        <li><strong>Step 4: AI Feedback Generation:</strong> The parsed text is securely sent to a Large Language Model (Groq / Qwen AI). The AI generates a qualitative summary and high-priority improvement suggestions.</li>
        <li><strong>Step 5: Dynamic DOCX Updating:</strong> If the user clicks 'Enhance' on a specific section, the AI rewrites it. The backend Python server then physically opens the user's uploaded <code>.docx</code> file, locates the exact paragraph, replaces it with the newly enhanced text, saves the file, and forces the browser to refresh the document viewer.</li>
    </ul>

    <h2>3. How the Keyword Engine Works</h2>
    <p>The Keyword Checker operates in two different modes depending on what the user is doing:</p>
    <ul>
        <li><strong>General Mode (No Job Description):</strong> If the user just uploads a CV, the system scans the text against a hardcoded dictionary of high-value industry action verbs and nouns. The specific keywords checked include: <em>'team', 'project', 'develop', 'manage', 'implement', 'design', 'analyze', 'lead', 'communicate', 'deliver', 'achieve', 'improve', 'experience', 'skill', 'knowledge', 'result', 'solution'</em>.</li>
        <li><strong>Targeted Mode (Job Match Tab):</strong> When the user pastes a Job Description into the 'Match' tab, the system strips out all 'stopwords' (meaningless words like <em>the, a, and, but, with</em>). It then calculates the exact mathematical overlap/intersection of the remaining meaningful words between the CV and the Job Description to generate a targeted match percentage.</li>
    </ul>

    <h2>4. How the Grammar & Professionalism Check Works</h2>
    <p>Rather than just doing basic spell-check, the system runs a <strong>Heuristic Professionalism Algorithm</strong>. The system starts with a score of 100 and applies deductions based on specific unprofessional traits:</p>
    <ul>
        <li><strong>Formatting Anomalies:</strong> It scans for highly fragmented sentences or very short, broken lines that indicate poor formatting or copy-paste errors.</li>
        <li><strong>Excessive Capitalization:</strong> It searches for long lines of text that are entirely uppercase and penalizes them (to prevent the CV from 'shouting' at the recruiter).</li>
        <li><strong>Informal Vocabulary Check:</strong> It scans the text for colloquial or unprofessional slang words that do not belong on a CV. Specifically, it checks for words like: <em>'gonna', 'wanna', 'kinda', 'sorta', 'etc etc', 'stuff', 'things'</em>.</li>
        <li><strong>Vocabulary Diversity (Repetition):</strong> The system calculates a Unique Word Ratio. If the user repeats the exact same words too frequently (e.g., using 'responsible for' over and over), the unique ratio drops below 40%, and the system deducts 10 points for lacking descriptive variety.</li>
    </ul>

    <div class="highlight">
        <h3>Pro Tip for Your Defense:</h3>
        <p>If the panel asks you why you didn't just use AI for everything, tell them: <em>"Relying entirely on AI is slow and expensive. I designed a hybrid architecture. I use fast, mathematical Python algorithms for the quantitative scoring (Keywords, Grammar, ATS), and I reserve the heavy AI processing strictly for qualitative tasks like rewriting text and giving career advice. This makes the system incredibly fast, cost-effective, and scalable."</em></p>
    </div>
</body>
</html>
'''

output_path = r'C:\Users\HP\Desktop\CareerAI_Project_Defense.pdf'
with open(output_path, 'w+b') as result_file:
    pisa_status = pisa.CreatePDF(html_content, dest=result_file)

if pisa_status.err:
    print('Error creating PDF')
else:
    print(f'PDF successfully created at: {output_path}')
