-- Auto-generated Database Schema from Current Django Models & Migrations

-- ==========================================
-- App: authentication
-- ==========================================
-- Model: CustomUser (Table: authentication_customuser)
CREATE TABLE IF NOT EXISTS authentication_customuser (
-- Error exporting authentication: 'OneToOneRel' object has no attribute 'column'
-- ==========================================
-- App: cv_analyzer
-- ==========================================
-- Model: CVUpload (Table: cv_analyzer_cvupload)
CREATE TABLE IF NOT EXISTS cv_analyzer_cvupload (
-- Error exporting cv_analyzer: 'OneToOneRel' object has no attribute 'column'
-- ==========================================
-- App: job_matching
-- ==========================================
-- Model: JobDescription (Table: job_matching_jobdescription)
CREATE TABLE IF NOT EXISTS job_matching_jobdescription (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    title varchar(200) NOT NULL,
    company varchar(200) NOT NULL,
    location varchar(200) NOT NULL,
    job_type varchar(20) NOT NULL,
    salary_range varchar(100) NOT NULL,
    description longtext NOT NULL,
    is_archived bool NOT NULL,
    job_url varchar(200) NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- Model: JobMatch (Table: job_matching_jobmatch)
CREATE TABLE IF NOT EXISTS job_matching_jobmatch (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    cv_upload_id bigint AUTO_INCREMENT NOT NULL,
    job_description_id bigint AUTO_INCREMENT NOT NULL,
    match_score double precision NOT NULL,
    matching_keywords json NOT NULL,
    missing_keywords json NOT NULL,
    matching_skills json NOT NULL,
    missing_skills json NOT NULL,
    suggestions json NOT NULL,
    strength_areas json NOT NULL,
    gap_areas json NOT NULL,
    section_analysis json NOT NULL,
    optimize_plan json NOT NULL,
    ai_summary longtext NOT NULL,
    is_saved bool NOT NULL,
    application_status varchar(20) NOT NULL,
    notes longtext NOT NULL,
    follow_up_date date NULL,
    ats_platform varchar(50) NOT NULL,
    ats_tips json NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- ==========================================
-- App: assessment
-- ==========================================
-- Model: UserSkill (Table: assessment_userskill)
CREATE TABLE IF NOT EXISTS assessment_userskill (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    skill_name varchar(100) NOT NULL,
    proficiency integer NOT NULL,
    category varchar(20) NOT NULL,
    is_verified bool NOT NULL,
    verified_by_id bigint AUTO_INCREMENT NULL,
    added_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- Model: Assessment (Table: assessment_assessment)
CREATE TABLE IF NOT EXISTS assessment_assessment (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    readiness_score double precision NOT NULL,
    technical_score double precision NOT NULL,
    soft_skills_score double precision NOT NULL,
    experience_score double precision NOT NULL,
    education_score double precision NOT NULL,
    career_level varchar(10) NOT NULL,
    skill_gaps json NOT NULL,
    strengths json NOT NULL,
    recommendations json NOT NULL,
    action_plan json NOT NULL,
    ai_summary longtext NOT NULL,
    is_current bool NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- ==========================================
-- App: career
-- ==========================================
-- Model: CareerRecommendation (Table: career_careerrecommendation)
CREATE TABLE IF NOT EXISTS career_careerrecommendation (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    recommended_skills json NOT NULL,
    recommended_courses json NOT NULL,
    career_paths json NOT NULL,
    certifications json NOT NULL,
    job_titles json NOT NULL,
    target_companies json NOT NULL,
    learning_resources json NOT NULL,
    current_skills_snapshot json NOT NULL,
    target_role varchar(200) NOT NULL,
    ai_summary longtext NOT NULL,
    is_current bool NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- ==========================================
-- App: interview_prep
-- ==========================================
-- Model: InterviewSession (Table: interview_prep_interviewsession)
CREATE TABLE IF NOT EXISTS interview_prep_interviewsession (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    job_title varchar(200) NOT NULL,
    company_name varchar(200) NOT NULL,
    difficulty varchar(10) NOT NULL,
    industry varchar(100) NOT NULL,
    behavioral_questions json NOT NULL,
    technical_questions json NOT NULL,
    situational_questions json NOT NULL,
    general_tips json NOT NULL,
    preparation_checklist json NOT NULL,
    ai_notes longtext NOT NULL,
    is_completed bool NOT NULL,
    completed_at datetime(6) NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- Model: MockInterviewResponse (Table: interview_prep_mockinterviewresponse)
CREATE TABLE IF NOT EXISTS interview_prep_mockinterviewresponse (
    id bigint AUTO_INCREMENT NOT NULL,
    session_id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    question_type varchar(20) NOT NULL,
    question longtext NOT NULL,
    answer longtext NOT NULL,
    feedback longtext NOT NULL,
    created_at datetime(6) NOT NULL
);

-- ==========================================
-- App: learning
-- ==========================================
-- Model: StudyPlan (Table: learning_studyplan)
CREATE TABLE IF NOT EXISTS learning_studyplan (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    skill_name varchar(100) NOT NULL,
    title varchar(300) NOT NULL,
    description longtext NOT NULL,
    target_level varchar(50) NOT NULL,
    status varchar(10) NOT NULL,
    estimated_hours integer NOT NULL,
    progress_percent integer NOT NULL,
    ai_summary longtext NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- Model: StudyPlanLesson (Table: learning_studyplanlesson)
CREATE TABLE IF NOT EXISTS learning_studyplanlesson (
    id bigint AUTO_INCREMENT NOT NULL,
    plan_id bigint AUTO_INCREMENT NOT NULL,
    order integer UNSIGNED NOT NULL,
    title varchar(300) NOT NULL,
    content longtext NOT NULL,
    key_points json NOT NULL,
    resources json NOT NULL,
    is_completed bool NOT NULL,
    completed_at datetime(6) NULL
);

-- Model: Quiz (Table: learning_quiz)
CREATE TABLE IF NOT EXISTS learning_quiz (
    id bigint AUTO_INCREMENT NOT NULL,
    plan_id bigint AUTO_INCREMENT NOT NULL,
    title varchar(300) NOT NULL,
    questions json NOT NULL,
    created_at datetime(6) NOT NULL
);

-- Model: QuizAttempt (Table: learning_quizattempt)
CREATE TABLE IF NOT EXISTS learning_quizattempt (
    id bigint AUTO_INCREMENT NOT NULL,
    quiz_id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    answers json NOT NULL,
    score integer NOT NULL,
    total integer NOT NULL,
    percentage double precision NOT NULL,
    passed bool NOT NULL,
    created_at datetime(6) NOT NULL
);

-- Model: LearningGoal (Table: learning_learninggoal)
CREATE TABLE IF NOT EXISTS learning_learninggoal (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    goal_type varchar(10) NOT NULL,
    target integer UNSIGNED NOT NULL,
    period_start date NOT NULL,
    achieved integer UNSIGNED NOT NULL,
    is_active bool NOT NULL,
    achievement_notified bool NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- ==========================================
-- App: notifications
-- ==========================================
-- Model: Notification (Table: notifications_notification)
CREATE TABLE IF NOT EXISTS notifications_notification (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    title varchar(200) NOT NULL,
    message longtext NOT NULL,
    notification_type varchar(20) NOT NULL,
    priority varchar(10) NOT NULL,
    link varchar(500) NOT NULL,
    is_read bool NOT NULL,
    read_at datetime(6) NULL,
    expires_at datetime(6) NULL,
    created_at datetime(6) NOT NULL
);

-- ==========================================
-- App: dashboard
-- ==========================================
-- Model: UserProfile (Table: dashboard_userprofile)
CREATE TABLE IF NOT EXISTS dashboard_userprofile (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NOT NULL,
    bio longtext NOT NULL,
    avatar varchar(100) NULL,
    phone varchar(20) NOT NULL,
    location varchar(100) NOT NULL,
    current_role varchar(100) NOT NULL,
    linkedin_url varchar(200) NOT NULL,
    github_url varchar(200) NOT NULL,
    portfolio_url varchar(200) NOT NULL,
    years_experience varchar(5) NOT NULL,
    target_role varchar(100) NOT NULL,
    target_industry varchar(100) NOT NULL,
    education_level varchar(20) NOT NULL,
    field_of_study varchar(100) NOT NULL,
    institution varchar(200) NOT NULL,
    graduation_year integer NULL,
    readiness_score double precision NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

-- ==========================================
-- App: admin_panel
-- ==========================================
-- Model: ActivityLog (Table: admin_panel_activitylog)
CREATE TABLE IF NOT EXISTS admin_panel_activitylog (
    id bigint AUTO_INCREMENT NOT NULL,
    user_id bigint AUTO_INCREMENT NULL,
    action_type varchar(20) NOT NULL,
    description longtext NOT NULL,
    model_name varchar(100) NOT NULL,
    object_id integer UNSIGNED NULL,
    ip_address char(39) NULL,
    user_agent longtext NOT NULL,
    metadata json NOT NULL,
    created_at datetime(6) NOT NULL
);

-- Model: SystemSetting (Table: admin_panel_systemsetting)
CREATE TABLE IF NOT EXISTS admin_panel_systemsetting (
    id bigint AUTO_INCREMENT NOT NULL,
    key varchar(100) NOT NULL,
    label varchar(200) NOT NULL,
    value longtext NOT NULL,
    setting_type varchar(10) NOT NULL,
    description longtext NOT NULL,
    is_public bool NOT NULL,
    created_at datetime(6) NOT NULL,
    updated_at datetime(6) NOT NULL
);

