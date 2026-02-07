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
            time_schedule TEXT
        )
    ''')

    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            session_number INTEGER NOT NULL,
            title TEXT NOT NULL,
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

    conn.commit()

    # Seed default instructor
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('instructor', generate_password_hash('instructor123'), 'Instructor', 'instructor'))
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
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
