import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'classroom_lms.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            student_id TEXT,
            section TEXT,
            photo TEXT DEFAULT 'default.png',
            contact_number TEXT,
            address TEXT,
            profile_completed INTEGER DEFAULT 0,
            is_approved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            section TEXT,
            day TEXT,
            time_schedule TEXT,
            color_theme TEXT DEFAULT 'blue'
        )
    ''')

    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            session_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_visible INTEGER DEFAULT 1,
            visible_from TEXT,
            visible_until TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # Activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            activity_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            instructions TEXT,
            points INTEGER DEFAULT 100,
            file_path TEXT,
            is_visible INTEGER DEFAULT 1,
            visible_from TEXT,
            visible_until TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')

    # Activity submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            content TEXT,
            file_path TEXT,
            score INTEGER,
            feedback TEXT,
            score_visible INTEGER DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities (id),
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    ''')

    # Quizzes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            time_limit INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')

    # Quiz questions with answer key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            points INTEGER DEFAULT 1,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        )
    ''')

    # Quiz attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            answers TEXT,
            score REAL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    ''')

    # Exams table (midterm, final)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            exam_type TEXT NOT NULL,
            title TEXT NOT NULL,
            time_limit INTEGER,
            total_points INTEGER DEFAULT 100,
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # Exam questions with answer key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            points INTEGER DEFAULT 1,
            FOREIGN KEY (exam_id) REFERENCES exams (id)
        )
    ''')

    # Exam attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            answers TEXT,
            score REAL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES exams (id),
            FOREIGN KEY (student_id) REFERENCES users (id)
        )
    ''')

    # Enrollments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            UNIQUE(student_id, subject_id)
        )
    ''')

    # Final Projects table (for COMP012 and subjects with final project component)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS final_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            total_points INTEGER DEFAULT 100,
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # Final Project Scores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS final_project_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            final_project_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            score REAL,
            feedback TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (final_project_id) REFERENCES final_projects (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            UNIQUE(final_project_id, student_id)
        )
    ''')

    # Game Scores table for Python Code Blaster leaderboard
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            level INTEGER NOT NULL,
            codes_typed INTEGER NOT NULL,
            best_streak INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # User game stats for weekly/all-time tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            total_games INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0,
            highest_score INTEGER DEFAULT 0,
            highest_level INTEGER DEFAULT 0,
            total_codes_typed INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            xp_points INTEGER DEFAULT 0,
            current_rank TEXT DEFAULT 'Beginner',
            last_played TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Messages table for instructor-student communication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER,
            recipient_section TEXT,
            recipient_all INTEGER DEFAULT 0,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (recipient_id) REFERENCES users (id)
        )
    ''')

    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT DEFAULT 'info',
            icon TEXT DEFAULT 'bell',
            message TEXT NOT NULL,
            link TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Submission files table - for multiple file uploads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submission_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES submissions (id)
        )
    ''')

    # Peer review criteria table - defines what to check for each activity
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peer_review_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            criterion TEXT NOT NULL,
            points INTEGER DEFAULT 1,
            order_num INTEGER DEFAULT 0,
            FOREIGN KEY (activity_id) REFERENCES activities (id)
        )
    ''')

    # Peer review assignments table - randomly assigns reviewers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peer_review_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            is_completed INTEGER DEFAULT 0,
            FOREIGN KEY (submission_id) REFERENCES submissions (id),
            FOREIGN KEY (reviewer_id) REFERENCES users (id),
            UNIQUE(submission_id, reviewer_id)
        )
    ''')

    # Peer review responses table - stores reviewer answers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peer_review_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            criterion_id INTEGER NOT NULL,
            response TEXT NOT NULL,
            points_awarded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assignment_id) REFERENCES peer_review_assignments (id),
            FOREIGN KEY (criterion_id) REFERENCES peer_review_criteria (id)
        )
    ''')

    # Session video watches table - tracks which students watched session videos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_video_watches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            UNIQUE(session_id, student_id)
        )
    ''')

    # Session progress table - tracks 5-step completion per student per session
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            step_video INTEGER DEFAULT 0,
            step_slides INTEGER DEFAULT 0,
            step_reading INTEGER DEFAULT 0,
            step_activity INTEGER DEFAULT 0,
            step_quiz INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            UNIQUE(session_id, student_id)
        )
    ''')

    # Project groups for finals (sessions 13-16)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            group_number INTEGER NOT NULL,
            group_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            UNIQUE(subject_id, group_number)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member',
            FOREIGN KEY (group_id) REFERENCES project_groups (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            UNIQUE(group_id, student_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            session_number INTEGER NOT NULL,
            percentage INTEGER DEFAULT 0,
            notes TEXT,
            updated_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES project_groups (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            UNIQUE(group_id, session_number)
        )
    ''')

    # Performance alerts for instructor monitoring
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT DEFAULT 'warning',
            message TEXT NOT NULL,
            is_resolved INTEGER DEFAULT 0,
            notification_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # ============== V2 SaaS TABLES ==============

    # Institutions (schools/universities)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS institutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            short_name TEXT,
            logo TEXT,
            domain TEXT UNIQUE,
            address TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            plan TEXT DEFAULT 'free',
            max_students INTEGER DEFAULT 100,
            max_instructors INTEGER DEFAULT 5,
            subscription_start DATE,
            subscription_end DATE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Departments per institution
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            code TEXT,
            head_instructor_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (head_instructor_id) REFERENCES users (id)
        )
    ''')

    # Instructor profiles (extended data for payroll & attendance)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            institution_id INTEGER,
            department_id INTEGER,
            employee_id TEXT,
            hire_date DATE,
            contract_type TEXT DEFAULT 'full-time',
            salary_rate REAL DEFAULT 0,
            salary_frequency TEXT DEFAULT 'monthly',
            tax_id TEXT,
            bank_account TEXT,
            emergency_contact TEXT,
            emergency_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )
    ''')

    # Instructor attendance (daily clock in/out)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructor_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_in TIMESTAMP,
            time_out TIMESTAMP,
            status TEXT DEFAULT 'present',
            hours_worked REAL DEFAULT 0,
            notes TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES users (id),
            UNIQUE(instructor_id, date)
        )
    ''')

    # Instructor payroll
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructor_payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_id INTEGER NOT NULL,
            institution_id INTEGER,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            base_salary REAL DEFAULT 0,
            days_present INTEGER DEFAULT 0,
            days_absent INTEGER DEFAULT 0,
            days_late INTEGER DEFAULT 0,
            total_hours REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            overtime_pay REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            deduction_details TEXT,
            bonuses REAL DEFAULT 0,
            bonus_details TEXT,
            gross_pay REAL DEFAULT 0,
            net_pay REAL DEFAULT 0,
            status TEXT DEFAULT 'draft',
            approved_by INTEGER,
            approved_at TIMESTAMP,
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES users (id),
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''')

    # Academic periods (semesters/terms)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS academic_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER,
            name TEXT NOT NULL,
            period_type TEXT DEFAULT 'semester',
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions (id)
        )
    ''')

    # AI Admin action logs (transparency & audit trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            target_name TEXT,
            decision TEXT NOT NULL,
            reasoning TEXT,
            data TEXT,
            severity TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # AI Admin rules (configurable behavior)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_admin_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            condition_field TEXT,
            condition_operator TEXT,
            condition_value TEXT,
            action_type TEXT NOT NULL,
            action_params TEXT,
            is_active INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 0,
            last_triggered_at TIMESTAMP,
            trigger_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Student payments / tuition tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            institution_id INTEGER,
            payment_type TEXT DEFAULT 'tuition',
            description TEXT,
            amount REAL NOT NULL,
            amount_paid REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            due_date DATE,
            paid_at TIMESTAMP,
            payment_method TEXT,
            reference_number TEXT,
            academic_period_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (academic_period_id) REFERENCES academic_periods (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    # Tuition fee plans per institution
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tuition_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT DEFAULT 'semester',
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions (id)
        )
    ''')

    # File storage / document management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploaded_by INTEGER NOT NULL,
            institution_id INTEGER,
            file_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            file_type TEXT,
            category TEXT DEFAULT 'general',
            subject_id INTEGER,
            session_id INTEGER,
            description TEXT,
            is_public INTEGER DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploaded_by) REFERENCES users (id),
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')

    # Student attendance tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            session_id INTEGER,
            date DATE NOT NULL,
            status TEXT DEFAULT 'present',
            remarks TEXT,
            recorded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (session_id) REFERENCES sessions (id),
            FOREIGN KEY (recorded_by) REFERENCES users (id)
        )
    ''')

    # Platform settings (global + per-institution)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER,
            setting_key TEXT NOT NULL,
            setting_value TEXT,
            setting_type TEXT DEFAULT 'string',
            description TEXT,
            FOREIGN KEY (institution_id) REFERENCES institutions (id)
        )
    ''')

    # Subscription plans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price_monthly REAL DEFAULT 0,
            price_yearly REAL DEFAULT 0,
            max_students INTEGER DEFAULT 100,
            max_instructors INTEGER DEFAULT 5,
            max_subjects INTEGER DEFAULT 20,
            features TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Schedules table (for institution/instructor to set class schedules)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER,
            subject_id INTEGER,
            instructor_id INTEGER,
            title TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT,
            schedule_type TEXT DEFAULT 'class',
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (instructor_id) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    # Programs (academic programs per institution)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER NOT NULL,
            department_id INTEGER,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            short_name TEXT,
            description TEXT,
            year_count INTEGER DEFAULT 4,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (department_id) REFERENCES departments (id),
            UNIQUE(institution_id, code)
        )
    ''')

    # Sections (per program, per year level)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            institution_id INTEGER NOT NULL,
            year_level INTEGER NOT NULL,
            section_number INTEGER NOT NULL,
            label TEXT NOT NULL,
            min_students INTEGER DEFAULT 10,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES programs (id),
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            UNIQUE(program_id, year_level, section_number)
        )
    ''')

    # Payment reminders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER,
            student_id INTEGER,
            payment_id INTEGER,
            reminder_date DATE NOT NULL,
            message TEXT,
            is_sent INTEGER DEFAULT 0,
            sent_at TIMESTAMP,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions (id),
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (payment_id) REFERENCES student_payments (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')

    conn.commit()

    # Migration: Add new columns to existing tables if they don't exist
    migrations = [
        # Users table migrations
        ("users", "photo", "TEXT DEFAULT 'default.png'"),
        ("users", "contact_number", "TEXT"),
        ("users", "address", "TEXT"),
        ("users", "profile_completed", "INTEGER DEFAULT 1"),
        ("users", "email", "TEXT"),
        ("users", "github_account", "TEXT"),
        ("users", "railway_account", "TEXT"),
        ("users", "messenger", "TEXT"),
        ("users", "pup_id_photo", "TEXT"),
        ("users", "cor_photo", "TEXT"),
        ("users", "is_approved", "INTEGER DEFAULT 0"),
        # KYS (Know Your Student) fields
        ("users", "programming_languages", "TEXT"),
        ("users", "databases_known", "TEXT"),
        ("users", "hosting_platforms", "TEXT"),
        ("users", "other_tools", "TEXT"),
        # Sessions table migrations
        ("sessions", "is_visible", "INTEGER DEFAULT 1"),
        ("sessions", "visible_from", "TEXT"),
        ("sessions", "visible_until", "TEXT"),
        ("sessions", "youtube_url", "TEXT"),
        ("sessions", "video_duration", "INTEGER DEFAULT 0"),
        ("sessions", "reading_materials", "TEXT"),
        ("sessions", "reading_audio", "TEXT"),
        # Session video watches table migrations
        ("session_video_watches", "watched_seconds", "INTEGER DEFAULT 0"),
        ("session_video_watches", "last_position", "INTEGER DEFAULT 0"),
        ("session_video_watches", "last_heartbeat_at", "TIMESTAMP"),
        ("session_video_watches", "completed", "INTEGER DEFAULT 0"),
        # Activities table migrations
        ("activities", "is_visible", "INTEGER DEFAULT 1"),
        ("activities", "visible_from", "TEXT"),
        ("activities", "visible_until", "TEXT"),
        ("activities", "file_path", "TEXT"),
        ("activities", "due_date", "TEXT"),
        ("activities", "due_time", "TEXT"),
        ("activities", "is_active", "INTEGER DEFAULT 1"),
        ("activities", "allow_file_upload", "INTEGER DEFAULT 1"),
        ("activities", "allow_multiple_files", "INTEGER DEFAULT 1"),
        ("activities", "max_files", "INTEGER DEFAULT 5"),
        ("activities", "late_penalty_per_day", "INTEGER DEFAULT 1"),
        ("activities", "enable_peer_review", "INTEGER DEFAULT 0"),
        ("activities", "peer_reviewers_count", "INTEGER DEFAULT 1"),
        # Submissions table migrations
        ("submissions", "score_visible", "INTEGER DEFAULT 0"),
        ("submissions", "is_late", "INTEGER DEFAULT 0"),
        ("submissions", "late_days", "INTEGER DEFAULT 0"),
        ("submissions", "late_penalty", "INTEGER DEFAULT 0"),
        ("submissions", "peer_review_score", "REAL"),
        ("submissions", "participation_score", "REAL"),
        ("submissions", "instructor_score", "REAL"),
        ("submissions", "final_score", "REAL"),
        # Peer review assignment quality tracking
        ("peer_review_assignments", "review_quality_score", "REAL"),
        ("peer_review_assignments", "instructor_feedback", "TEXT"),
        ("peer_review_assignments", "approval_status", "TEXT"),
        # Subjects table migrations
        ("subjects", "color_theme", "TEXT DEFAULT 'blue'"),
        # Quizzes visibility
        ("quizzes", "is_visible", "INTEGER DEFAULT 0"),
        # Exams visibility
        ("exams", "is_visible", "INTEGER DEFAULT 0"),
        # Quiz attempts score visibility
        ("quiz_attempts", "score_visible", "INTEGER DEFAULT 0"),
        # Exam attempts score visibility
        ("exam_attempts", "score_visible", "INTEGER DEFAULT 0"),
        # Quiz attempt tracking
        ("quiz_attempts", "time_spent", "INTEGER DEFAULT 0"),
        ("quiz_attempts", "missed_questions", "TEXT"),
        ("quiz_attempts", "total_questions", "INTEGER DEFAULT 0"),
        # V2 SaaS migrations
        ("users", "institution_id", "INTEGER"),
        ("users", "department_id", "INTEGER"),
        ("subjects", "institution_id", "INTEGER"),
        ("subjects", "academic_period_id", "INTEGER"),
        ("subjects", "department_id", "INTEGER"),
        ("subjects", "instructor_id", "INTEGER"),
        ("subjects", "room", "TEXT"),
        ("subjects", "credits", "INTEGER DEFAULT 3"),
        ("subjects", "max_students", "INTEGER DEFAULT 50"),
        # User additional fields
        ("users", "date_of_birth", "DATE"),
        ("users", "gender", "TEXT"),
        ("users", "guardian_name", "TEXT"),
        ("users", "guardian_phone", "TEXT"),
        ("users", "year_level", "TEXT"),
        ("users", "status", "TEXT DEFAULT 'active'"),
        # School-based registration: relational section/program IDs
        ("users", "program_id", "INTEGER"),
        ("users", "section_id", "INTEGER"),
        ("subjects", "section_id", "INTEGER"),
        ("subjects", "program_id", "INTEGER"),
    ]

    for table, column, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Seed default instructor (always approved)
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role, is_approved, profile_completed)
            VALUES (?, ?, ?, ?, 1, 1)
        ''', ('instructor', generate_password_hash('instructor123'), 'Instructor', 'instructor'))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    # Ensure all instructors are approved
    cursor.execute('UPDATE users SET is_approved = 1, profile_completed = 1 WHERE role = "instructor"')
    conn.commit()

    # Seed default student account
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role, student_id, section, profile_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('student', generate_password_hash('student123'), 'Florence Sangrenes', 'student', '2021-00001', 'BSIT-SR 3-1', 1))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    # Seed 7 subjects with schedule
    subjects = [
        ('COMP019', 'Applications Development and Emerging Technologies', 'Web and mobile app development with emerging tech', 'BSIT-SR 3-1', 'Tuesday', '1:00PM-6:00PM'),
        ('COMP019', 'Applications Development and Emerging Technologies', 'Web and mobile app development with emerging tech', 'BSIT-SR 3-2', 'Tuesday', '7:30AM-12:30PM'),
        ('COMP012', 'Network Administration', 'Network setup, management and administration', 'BSIT-SR 2-3', 'Wednesday', '7:30AM-12:30PM'),
        ('COMP012', 'Network Administration', 'Network setup, management and administration', 'BSIT-SR 2-1', 'Thursday', '7:30AM-9:30AM'),
        ('COMP012', 'Network Administration', 'Network setup, management and administration', 'BSIT-SR 2-2', 'Thursday', '1:00PM-6:00PM'),
        ('CNS', 'Computer Networks and Security', 'Network protocols and security', 'BSCPE-BN 3-1', 'Saturday', '7:30AM-1:30PM'),
        ('ES', 'Embedded Systems', 'Microcontrollers and embedded programming', 'BSCPE-BN 4-1', 'Saturday', '2:00PM-8:00PM')
    ]

    for code, name, desc, section, day, time_schedule in subjects:
        cursor.execute('''
            SELECT id FROM subjects WHERE code = ? AND section = ?
        ''', (code, section))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO subjects (code, name, description, section, day, time_schedule)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (code, name, desc, section, day, time_schedule))

    conn.commit()

    # Create 16 sessions for each subject
    cursor.execute('SELECT id, code FROM subjects')
    subjects_list = cursor.fetchall()

    for subject in subjects_list:
        for i in range(1, 17):
            if i <= 12:
                title = f"Session {i}: Lesson"
            else:
                title = f"Session {i}: Project"

            cursor.execute('''
                SELECT id FROM sessions WHERE subject_id = ? AND session_number = ?
            ''', (subject['id'], i))

            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO sessions (subject_id, session_number, title)
                    VALUES (?, ?, ?)
                ''', (subject['id'], i, title))

    conn.commit()

    # Enroll default student in COMP019 BSIT-SR 3-1
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', ('student',))
        student = cursor.fetchone()
        cursor.execute('SELECT id FROM subjects WHERE code = ? AND section = ?', ('COMP019', 'BSIT-SR 3-1'))
        subject = cursor.fetchone()
        if student and subject:
            cursor.execute('''
                INSERT INTO enrollments (student_id, subject_id)
                VALUES (?, ?)
            ''', (student['id'], subject['id']))
            conn.commit()
    except sqlite3.IntegrityError:
        pass  # Already enrolled

    # ============== V2 SaaS SEEDS ==============

    # Seed platform admin account
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role, is_approved, profile_completed)
            VALUES (?, ?, ?, ?, 1, 1)
        ''', ('admin', generate_password_hash('admin123'), 'Platform Admin', 'admin'))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    # Ensure admin is approved
    cursor.execute('UPDATE users SET is_approved = 1, profile_completed = 1 WHERE role = "admin"')
    conn.commit()

    # Seed default institution (PUP)
    cursor.execute('SELECT id FROM institutions WHERE short_name = ?', ('PUP',))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO institutions (name, short_name, domain, address, contact_email, plan, max_students, max_instructors, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', ('Polytechnic University of the Philippines', 'PUP', 'pup.edu.ph',
              'Sta. Mesa, Manila', 'info@pup.edu.ph', 'enterprise', 10000, 100))
        conn.commit()

        # Link existing users and subjects to this institution
        cursor.execute('SELECT id FROM institutions WHERE short_name = ?', ('PUP',))
        inst = cursor.fetchone()
        if inst:
            cursor.execute('UPDATE users SET institution_id = ? WHERE institution_id IS NULL', (inst['id'],))
            cursor.execute('UPDATE subjects SET institution_id = ? WHERE institution_id IS NULL', (inst['id'],))
            conn.commit()

    # Seed subscription plans
    plans = [
        ('Free', 0, 0, 50, 2, 5, 'Basic LMS features, 50 students, 2 instructors'),
        ('Basic', 499, 4990, 200, 10, 20, 'Full LMS + monitoring, 200 students, 10 instructors'),
        ('Premium', 1499, 14990, 1000, 50, 100, 'Full LMS + AI admin + payroll, 1000 students, 50 instructors'),
        ('Enterprise', 4999, 49990, 10000, 100, 500, 'Unlimited features, custom branding, priority support'),
    ]
    for name, monthly, yearly, students, instructors, subjects_limit, features in plans:
        cursor.execute('SELECT id FROM subscription_plans WHERE name = ?', (name,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO subscription_plans (name, price_monthly, price_yearly, max_students, max_instructors, max_subjects, features)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, monthly, yearly, students, instructors, subjects_limit, features))
    conn.commit()

    # Seed default AI admin rules
    default_rules = [
        ('Low Grade Alert', 'grade_monitor', 'weighted_grade', 'less_than', '75',
         'send_notification', '{"severity": "critical", "message_template": "Academic alert: {grade}% in {subject}. You need 75% to pass."}'),
        ('Grade Warning', 'grade_monitor', 'weighted_grade', 'less_than', '82',
         'send_notification', '{"severity": "warning", "message_template": "Your grade in {subject} is {grade}%. Keep pushing to improve!"}'),
        ('Missed Deadline', 'deadline_monitor', 'days_overdue', 'greater_than', '0',
         'send_notification', '{"severity": "warning", "message_template": "You missed the deadline for {activity} in {subject}. Submit ASAP."}'),
        ('Behind on Lessons', 'progress_monitor', 'sessions_behind', 'greater_than', '2',
         'send_notification', '{"severity": "critical", "message_template": "You are {count} sessions behind in {subject}. Catch up now!"}'),
        ('Weekly Performance Report', 'report_generator', 'day_of_week', 'equals', 'Sunday',
         'generate_report', '{"report_type": "weekly_performance", "send_to": "instructors"}'),
        ('Auto Payroll Calculation', 'payroll_processor', 'period_end', 'equals', 'today',
         'calculate_payroll', '{"auto_approve": false}'),
        ('Attendance Reminder', 'attendance_monitor', 'clock_in_missing', 'equals', 'true',
         'send_notification', '{"severity": "info", "message_template": "Reminder: Please clock in for today."}'),
        ('Inactivity Alert', 'activity_monitor', 'days_inactive', 'greater_than', '7',
         'send_notification', '{"severity": "warning", "message_template": "Student {name} has been inactive for {days} days in {subject}."}'),
    ]
    for rule_name, rule_type, cond_field, cond_op, cond_val, action_type, action_params in default_rules:
        cursor.execute('SELECT id FROM ai_admin_rules WHERE rule_name = ?', (rule_name,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO ai_admin_rules (rule_name, rule_type, condition_field, condition_operator, condition_value, action_type, action_params)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (rule_name, rule_type, cond_field, cond_op, cond_val, action_type, action_params))
    conn.commit()

    # Seed default institution account (linked to PUP)
    cursor.execute('SELECT id FROM institutions WHERE short_name = ?', ('PUP',))
    pup_inst = cursor.fetchone()
    if pup_inst:
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, is_approved, profile_completed, institution_id)
                VALUES (?, ?, ?, ?, 1, 1, ?)
            ''', ('institution', generate_password_hash('institution123'), 'PUP Institution Admin', 'institution', pup_inst['id']))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        # Ensure institution users are approved
        cursor.execute('UPDATE users SET is_approved = 1, profile_completed = 1 WHERE role = "institution"')
        conn.commit()

    # Seed programs for PUP institution
    cursor.execute('SELECT id FROM institutions WHERE short_name = ?', ('PUP',))
    pup_for_programs = cursor.fetchone()
    if pup_for_programs:
        pup_programs = [
            ('BSIT', 'Bachelor of Science in Information Technology', 'BSIT-SR', 4),
            ('BSCPE', 'Bachelor of Science in Computer Engineering', 'BSCPE-BN', 4),
        ]
        for code, name, short_name, year_count in pup_programs:
            cursor.execute('SELECT id FROM programs WHERE institution_id = ? AND code = ?',
                           (pup_for_programs['id'], code))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO programs (institution_id, code, name, short_name, year_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pup_for_programs['id'], code, name, short_name, year_count))
        conn.commit()

        # Seed sections for all year levels (1st-4th) for both programs
        sections_seed = [
            # BSIT: 2 sections per year, plus extras for 2nd & 3rd year
            ('BSIT', 1, 1), ('BSIT', 1, 2),
            ('BSIT', 2, 1), ('BSIT', 2, 2), ('BSIT', 2, 3),
            ('BSIT', 3, 1), ('BSIT', 3, 2),
            ('BSIT', 4, 1), ('BSIT', 4, 2),
            # BSCPE: 1-2 sections per year
            ('BSCPE', 1, 1),
            ('BSCPE', 2, 1),
            ('BSCPE', 3, 1),
            ('BSCPE', 4, 1),
        ]
        for prog_code, year, sec_num in sections_seed:
            cursor.execute('SELECT id, short_name FROM programs WHERE institution_id = ? AND code = ?',
                           (pup_for_programs['id'], prog_code))
            prog = cursor.fetchone()
            if prog:
                label = f"{prog['short_name']} {year}-{sec_num}"
                cursor.execute('SELECT id FROM sections WHERE program_id = ? AND year_level = ? AND section_number = ?',
                               (prog['id'], year, sec_num))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO sections (program_id, institution_id, year_level, section_number, label)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (prog['id'], pup_for_programs['id'], year, sec_num, label))
        conn.commit()

        # Back-fill section_id and program_id on existing users and subjects
        cursor.execute('SELECT id, label FROM sections')
        all_sections = cursor.fetchall()
        for sec in all_sections:
            cursor.execute('UPDATE users SET section_id = ? WHERE section = ? AND section_id IS NULL',
                           (sec['id'], sec['label']))
            cursor.execute('UPDATE subjects SET section_id = ? WHERE section = ? AND section_id IS NULL',
                           (sec['id'], sec['label']))
        cursor.execute('''
            UPDATE users SET program_id = (
                SELECT program_id FROM sections WHERE sections.id = users.section_id
            ) WHERE section_id IS NOT NULL AND program_id IS NULL
        ''')
        cursor.execute('''
            UPDATE subjects SET program_id = (
                SELECT program_id FROM sections WHERE sections.id = subjects.section_id
            ) WHERE section_id IS NOT NULL AND program_id IS NULL
        ''')
        conn.commit()

    # Seed default platform settings
    default_settings = [
        (None, 'platform_name', 'eMathrix LMS', 'string', 'Platform display name'),
        (None, 'ai_admin_enabled', 'true', 'boolean', 'Enable AI Admin agent'),
        (None, 'ai_admin_interval_minutes', '30', 'integer', 'AI Admin check interval in minutes'),
        (None, 'auto_payroll_enabled', 'true', 'boolean', 'Enable automatic payroll calculation'),
        (None, 'default_working_hours', '8', 'integer', 'Default working hours per day'),
        (None, 'late_threshold_minutes', '15', 'integer', 'Minutes after schedule to count as late'),
        (None, 'email_notifications_enabled', 'false', 'boolean', 'Send email notifications'),
    ]
    for inst_id, key, value, stype, desc in default_settings:
        cursor.execute('SELECT id FROM platform_settings WHERE setting_key = ? AND institution_id IS ?', (key, inst_id))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO platform_settings (institution_id, setting_key, setting_value, setting_type, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (inst_id, key, value, stype, desc))
    conn.commit()

    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
