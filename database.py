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

    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
