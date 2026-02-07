from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Custom Jinja filter to parse JSON
@app.template_filter('parse_json')
def parse_json_filter(value):
    if value:
        try:
            return json.loads(value)
        except:
            return []
    return []

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(UserMixin):
    def __init__(self, id, username, full_name, role, student_id=None, section=None):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.role = role
        self.student_id = student_id
        self.section = section

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['full_name'], user['role'], user['student_id'], user['section'])
    return None

# PUP Transmutation Table
def get_pup_grade(percentage):
    """Convert percentage to PUP grade scale (1.00 - 5.00)"""
    if percentage >= 97:
        return 1.00
    elif percentage >= 94:
        return 1.25
    elif percentage >= 91:
        return 1.50
    elif percentage >= 88:
        return 1.75
    elif percentage >= 85:
        return 2.00
    elif percentage >= 82:
        return 2.25
    elif percentage >= 79:
        return 2.50
    elif percentage >= 76:
        return 2.75
    elif percentage >= 75:
        return 3.00
    else:
        return 5.00

# Grade weights per subject
def get_grade_weights(subject_code):
    """Get grade component weights based on subject code"""
    if subject_code == 'COMP012':
        # Network Administration specific weights
        return {
            'quizzes': 0.10,      # 10%
            'activities': 0.25,   # 25%
            'midterm': 0.15,      # 15%
            'final': 0.15,        # 15%
            'final_project': 0.35 # 35%
        }
    else:
        # Default weights for other subjects
        return {
            'quizzes': 0.20,      # 20%
            'activities': 0.40,   # 40%
            'midterm': 0.20,      # 20%
            'final': 0.20,        # 20%
            'final_project': 0.00 # No final project
        }

# ==================== AUTH ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'instructor':
            return redirect(url_for('dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'], user['full_name'], user['role'], user['student_id'], user['section'])
            login_user(user_obj)
            flash('Logged in successfully!', 'success')
            if user['role'] == 'instructor':
                return redirect(url_for('dashboard'))
            return redirect(url_for('student_dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# ==================== INSTRUCTOR DASHBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects')
    subjects = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "student"')
    student_count = cursor.fetchone()['count']
    conn.close()

    return render_template('dashboard.html', subjects=subjects, student_count=student_count)

# ==================== STUDENT MANAGEMENT ====================

@app.route('/students')
@login_required
def students():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE role = "student" ORDER BY full_name')
    students_list = cursor.fetchall()
    conn.close()

    return render_template('students.html', students=students_list)

@app.route('/students/add', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    student_id = request.form['student_id']
    username = request.form['username']
    password = request.form['password']
    full_name = request.form['full_name']
    section = request.form['section']

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role, student_id, section)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, generate_password_hash(password), full_name, 'student', student_id, section))
        conn.commit()
        flash(f'Student {full_name} added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding student: {str(e)}', 'error')
    conn.close()

    return redirect(url_for('students'))

@app.route('/students/bulk-upload', methods=['POST'])
@login_required
def bulk_upload_students():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('students'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('students'))

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(filepath)
            elif filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                flash('Invalid file format. Use .xlsx, .xls, or .csv', 'error')
                return redirect(url_for('students'))

            conn = get_db()
            cursor = conn.cursor()
            added = 0
            errors = []

            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT INTO users (username, password_hash, full_name, role, student_id, section)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row['username']),
                        generate_password_hash(str(row['password'])),
                        str(row['full_name']),
                        'student',
                        str(row['student_id']),
                        str(row.get('section', ''))
                    ))
                    added += 1
                except Exception as e:
                    errors.append(f"{row.get('username', 'Unknown')}: {str(e)}")

            conn.commit()
            conn.close()

            flash(f'Successfully added {added} students!', 'success')
            if errors:
                flash(f'Errors: {", ".join(errors[:5])}', 'error')

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')

        os.remove(filepath)

    return redirect(url_for('students'))

@app.route('/students/delete/<int:id>')
@login_required
def delete_student(id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ? AND role = "student"', (id,))
    conn.commit()
    conn.close()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('students'))

# ==================== SUBJECTS ====================

@app.route('/subjects')
@login_required
def subjects():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects')
    subjects_list = cursor.fetchall()
    conn.close()
    return render_template('subjects.html', subjects=subjects_list)

@app.route('/subjects/<int:id>')
@login_required
def subject_detail(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (id,))
    subject = cursor.fetchone()
    cursor.execute('SELECT * FROM sessions WHERE subject_id = ? ORDER BY session_number', (id,))
    sessions = cursor.fetchall()
    conn.close()
    return render_template('sessions.html', subject=subject, sessions=sessions)

# ==================== ACTIVITIES ====================

@app.route('/subject/<int:subject_id>/all-activities')
@login_required
def all_activities(subject_id):
    """Show ALL 16 sessions' activities on ONE page"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()

    # Get all sessions with their activities
    cursor.execute('SELECT * FROM sessions WHERE subject_id = ? ORDER BY session_number', (subject_id,))
    sessions = cursor.fetchall()

    sessions_with_activities = []
    for session in sessions:
        cursor.execute('SELECT * FROM activities WHERE session_id = ? ORDER BY activity_number', (session['id'],))
        activities = cursor.fetchall()
        sessions_with_activities.append({
            'session': session,
            'activities': activities
        })

    conn.close()
    return render_template('all_activities.html', subject=subject, sessions_data=sessions_with_activities)

@app.route('/session/<int:session_id>/activities')
@login_required
def session_activities(session_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, sub.code as subject_code, sub.name as subject_name
        FROM sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.id = ?
    ''', (session_id,))
    session_data = cursor.fetchone()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (session_data['subject_id'],))
    subject = cursor.fetchone()
    cursor.execute('SELECT * FROM activities WHERE session_id = ? ORDER BY activity_number', (session_id,))
    activities = cursor.fetchall()
    conn.close()
    return render_template('activities.html', session=session_data, subject=subject, activities=activities)

@app.route('/activity/create/<int:session_id>', methods=['POST'])
@login_required
def create_activity(session_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    title = request.form['title']
    instructions = request.form['instructions']
    points = request.form['points']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM activities WHERE session_id = ?', (session_id,))
    count = cursor.fetchone()['count']
    cursor.execute('''
        INSERT INTO activities (session_id, activity_number, title, instructions, points)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, count + 1, title, instructions, points))
    conn.commit()
    conn.close()
    flash('Activity created successfully!', 'success')
    return redirect(url_for('session_activities', session_id=session_id))

@app.route('/activity/<int:activity_id>/upload', methods=['POST'])
@login_required
def upload_activity_file(activity_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(request.referrer)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.referrer)

    allowed_extensions = ('.pdf', '.docx', '.doc', '.pptx', '.ppt')
    if file and file.filename.lower().endswith(allowed_extensions):
        filename = secure_filename(f"activity_{activity_id}_{file.filename}")
        filepath = os.path.join('static', 'activity_files', filename)
        file.save(filepath)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE activities SET file_path = ? WHERE id = ?', (filename, activity_id))
        conn.commit()

        # Get session_id to redirect back
        cursor.execute('SELECT session_id FROM activities WHERE id = ?', (activity_id,))
        session_id = cursor.fetchone()['session_id']
        conn.close()

        flash('File uploaded successfully!', 'success')
        return redirect(url_for('session_activities', session_id=session_id))
    else:
        flash('Only PDF, DOCX, DOC, PPTX, PPT files are allowed', 'error')
        return redirect(request.referrer)

@app.route('/activity/<int:activity_id>/view-pdf')
@login_required
def view_activity_pdf(activity_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()
    conn.close()

    if activity and activity['file_path']:
        return redirect(url_for('static', filename=f"activity_files/{activity['file_path']}"))
    flash('No file found for this activity', 'error')
    return redirect(request.referrer)

@app.route('/activity/<int:activity_id>/submit', methods=['POST'])
@login_required
def submit_activity(activity_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    content = request.form['content']

    conn = get_db()
    cursor = conn.cursor()

    # Check if already submitted
    cursor.execute('SELECT id FROM submissions WHERE activity_id = ? AND student_id = ?',
                   (activity_id, current_user.id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE submissions SET content = ?, submitted_at = CURRENT_TIMESTAMP
            WHERE activity_id = ? AND student_id = ?
        ''', (content, activity_id, current_user.id))
    else:
        cursor.execute('''
            INSERT INTO submissions (activity_id, student_id, content)
            VALUES (?, ?, ?)
        ''', (activity_id, current_user.id, content))

    conn.commit()
    conn.close()
    flash('Activity submitted successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/activity/<int:activity_id>/grade', methods=['POST'])
@login_required
def grade_activity(activity_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    submission_id = request.form['submission_id']
    score = request.form['score']
    feedback = request.form['feedback']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE submissions SET score = ?, feedback = ?
        WHERE id = ?
    ''', (score, feedback, submission_id))
    conn.commit()
    conn.close()
    flash('Grade saved successfully!', 'success')
    return redirect(url_for('view_submissions', activity_id=activity_id))

@app.route('/activity/<int:activity_id>/submissions')
@login_required
def view_submissions(activity_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()
    cursor.execute('''
        SELECT s.*, u.full_name, u.student_id as sid
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        WHERE s.activity_id = ?
        ORDER BY s.submitted_at
    ''', (activity_id,))
    submissions = cursor.fetchall()
    conn.close()
    return render_template('submissions.html', activity=activity, submissions=submissions)

# ==================== LESSONS ====================

@app.route('/session/<int:session_id>/lesson')
@login_required
def session_lesson(session_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, sub.code as subject_code, sub.name as subject_name, sub.id as subject_id
        FROM sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.id = ?
    ''', (session_id,))
    session_data = cursor.fetchone()
    conn.close()

    if not session_data:
        flash('Session not found')
        return redirect(url_for('dashboard'))

    # Route to subject-specific lesson templates
    subject_code = session_data['subject_code']
    session_number = session_data['session_number']

    # Check for subject-specific lesson template
    if subject_code == 'COMP012':
        template_name = f'lessons/comp012/session{session_number}.html'
    elif subject_code == 'COMP019':
        template_name = f'lessons/comp019/session{session_number}.html'
    else:
        template_name = 'lesson.html'

    # Try to use subject-specific template, fallback to generic
    try:
        return render_template(template_name, session=session_data)
    except:
        return render_template('lesson.html', session=session_data)

# ==================== QUIZZES ====================

@app.route('/session/<int:session_id>/quiz')
@login_required
def session_quiz(session_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, sub.code as subject_code
        FROM sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.id = ?
    ''', (session_id,))
    session_data = cursor.fetchone()
    cursor.execute('SELECT * FROM quizzes WHERE session_id = ?', (session_id,))
    quiz = cursor.fetchone()

    questions = []
    if quiz:
        cursor.execute('SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY id', (quiz['id'],))
        questions = cursor.fetchall()

    conn.close()
    return render_template('quiz.html', session=session_data, quiz=quiz, questions=questions)

@app.route('/quiz/create/<int:session_id>', methods=['POST'])
@login_required
def create_quiz(session_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    title = request.form['title']
    time_limit = request.form.get('time_limit', 0)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quizzes (session_id, title, time_limit)
        VALUES (?, ?, ?)
    ''', (session_id, title, time_limit))
    conn.commit()
    conn.close()
    flash('Quiz created successfully! Now add questions.', 'success')
    return redirect(url_for('session_quiz', session_id=session_id))

@app.route('/quiz/<int:quiz_id>/add-question', methods=['POST'])
@login_required
def add_quiz_question(quiz_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    question_text = request.form['question_text']
    question_type = request.form['question_type']
    options = request.form.get('options', '')
    correct_answer = request.form['correct_answer']
    points = request.form.get('points', 1)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quiz_questions (quiz_id, question_text, question_type, options, correct_answer, points)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (quiz_id, question_text, question_type, options, correct_answer, points))

    cursor.execute('SELECT session_id FROM quizzes WHERE id = ?', (quiz_id,))
    session_id = cursor.fetchone()['session_id']

    conn.commit()
    conn.close()
    flash('Question added successfully!', 'success')
    return redirect(url_for('session_quiz', session_id=session_id))

@app.route('/quiz/<int:quiz_id>/take')
@login_required
def take_quiz(quiz_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Check if already taken
    cursor.execute('SELECT * FROM quiz_attempts WHERE quiz_id = ? AND student_id = ?',
                   (quiz_id, current_user.id))
    attempt = cursor.fetchone()

    if attempt:
        conn.close()
        flash('You have already taken this quiz.', 'error')
        return redirect(url_for('student_dashboard'))

    cursor.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,))
    quiz = cursor.fetchone()
    cursor.execute('SELECT id, question_text, question_type, options, points FROM quiz_questions WHERE quiz_id = ? ORDER BY id', (quiz_id,))
    questions = cursor.fetchall()
    conn.close()

    return render_template('quiz_take.html', quiz=quiz, questions=questions)

@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM quiz_questions WHERE quiz_id = ?', (quiz_id,))
    questions = cursor.fetchall()

    answers = {}
    total_score = 0
    max_score = 0

    for q in questions:
        answer = request.form.get(f'q_{q["id"]}', '')
        answers[str(q['id'])] = answer
        max_score += q['points']

        # Auto-grade
        if q['question_type'] in ['multiple_choice', 'true_false']:
            if answer.strip().lower() == q['correct_answer'].strip().lower():
                total_score += q['points']
        elif q['question_type'] == 'short_answer':
            if answer.strip().lower() == q['correct_answer'].strip().lower():
                total_score += q['points']

    percentage = (total_score / max_score * 100) if max_score > 0 else 0

    cursor.execute('''
        INSERT INTO quiz_attempts (quiz_id, student_id, answers, score)
        VALUES (?, ?, ?, ?)
    ''', (quiz_id, current_user.id, json.dumps(answers), percentage))

    conn.commit()
    conn.close()

    flash(f'Quiz submitted! Your score: {total_score}/{max_score} ({percentage:.1f}%)', 'success')
    return redirect(url_for('student_dashboard'))

# ==================== EXAMS ====================

@app.route('/subject/<int:subject_id>/exams')
@login_required
def subject_exams(subject_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()
    cursor.execute('SELECT * FROM exams WHERE subject_id = ? ORDER BY exam_type', (subject_id,))
    exams = cursor.fetchall()
    conn.close()
    return render_template('exams.html', subject=subject, exams=exams)

@app.route('/exam/create/<int:subject_id>', methods=['POST'])
@login_required
def create_exam(subject_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    title = request.form['title']
    exam_type = request.form['exam_type']
    time_limit = request.form.get('time_limit', 0)
    total_points = request.form.get('total_points', 100)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO exams (subject_id, exam_type, title, time_limit, total_points)
        VALUES (?, ?, ?, ?, ?)
    ''', (subject_id, exam_type, title, time_limit, total_points))
    conn.commit()
    conn.close()
    flash('Exam created successfully! Now add questions.', 'success')
    return redirect(url_for('subject_exams', subject_id=subject_id))

@app.route('/exam/<int:exam_id>/questions')
@login_required
def exam_questions(exam_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT e.*, s.code as subject_code FROM exams e JOIN subjects s ON e.subject_id = s.id WHERE e.id = ?', (exam_id,))
    exam = cursor.fetchone()
    cursor.execute('SELECT * FROM exam_questions WHERE exam_id = ? ORDER BY id', (exam_id,))
    questions = cursor.fetchall()
    conn.close()
    return render_template('exam_questions.html', exam=exam, questions=questions)

@app.route('/exam/<int:exam_id>/add-question', methods=['POST'])
@login_required
def add_exam_question(exam_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    question_text = request.form['question_text']
    question_type = request.form['question_type']
    options = request.form.get('options', '')
    correct_answer = request.form['correct_answer']
    points = request.form.get('points', 1)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO exam_questions (exam_id, question_text, question_type, options, correct_answer, points)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (exam_id, question_text, question_type, options, correct_answer, points))
    conn.commit()
    conn.close()
    flash('Question added successfully!', 'success')
    return redirect(url_for('exam_questions', exam_id=exam_id))

@app.route('/exam/<int:exam_id>/take')
@login_required
def take_exam(exam_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM exam_attempts WHERE exam_id = ? AND student_id = ?',
                   (exam_id, current_user.id))
    attempt = cursor.fetchone()

    if attempt:
        conn.close()
        flash('You have already taken this exam.', 'error')
        return redirect(url_for('student_dashboard'))

    cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
    exam = cursor.fetchone()
    cursor.execute('SELECT id, question_text, question_type, options, points FROM exam_questions WHERE exam_id = ? ORDER BY id', (exam_id,))
    questions = cursor.fetchall()
    conn.close()

    return render_template('exam_take.html', exam=exam, questions=questions)

@app.route('/exam/<int:exam_id>/submit', methods=['POST'])
@login_required
def submit_exam(exam_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM exam_questions WHERE exam_id = ?', (exam_id,))
    questions = cursor.fetchall()

    answers = {}
    total_score = 0
    max_score = 0

    for q in questions:
        answer = request.form.get(f'q_{q["id"]}', '')
        answers[str(q['id'])] = answer
        max_score += q['points']

        if q['question_type'] in ['multiple_choice', 'true_false']:
            if answer.strip().lower() == q['correct_answer'].strip().lower():
                total_score += q['points']
        elif q['question_type'] == 'short_answer':
            if answer.strip().lower() == q['correct_answer'].strip().lower():
                total_score += q['points']

    percentage = (total_score / max_score * 100) if max_score > 0 else 0

    cursor.execute('''
        INSERT INTO exam_attempts (exam_id, student_id, answers, score)
        VALUES (?, ?, ?, ?)
    ''', (exam_id, current_user.id, json.dumps(answers), percentage))

    conn.commit()
    conn.close()

    flash(f'Exam submitted! Your score: {total_score}/{max_score} ({percentage:.1f}%)', 'success')
    return redirect(url_for('student_dashboard'))

# ==================== GRADES ====================

@app.route('/grades')
@login_required
def grades():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects')
    subjects = cursor.fetchall()
    cursor.execute('SELECT * FROM users WHERE role = "student" ORDER BY full_name')
    students = cursor.fetchall()
    conn.close()
    return render_template('grades.html', subjects=subjects, students=students)

@app.route('/grades/student/<int:student_id>')
@login_required
def student_grades(student_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()

    cursor.execute('SELECT * FROM subjects')
    subjects = cursor.fetchall()

    grades_data = []
    for subject in subjects:
        # Get subject-specific grade weights
        weights = get_grade_weights(subject['code'])

        # Get quiz scores
        cursor.execute('''
            SELECT AVG(qa.score) as avg_quiz
            FROM quiz_attempts qa
            JOIN quizzes q ON qa.quiz_id = q.id
            JOIN sessions s ON q.session_id = s.id
            WHERE s.subject_id = ? AND qa.student_id = ?
        ''', (subject['id'], student_id))
        quiz_avg = cursor.fetchone()['avg_quiz'] or 0

        # Get activity scores
        cursor.execute('''
            SELECT AVG(sub.score) as avg_activity
            FROM submissions sub
            JOIN activities a ON sub.activity_id = a.id
            JOIN sessions s ON a.session_id = s.id
            WHERE s.subject_id = ? AND sub.student_id = ?
        ''', (subject['id'], student_id))
        activity_avg = cursor.fetchone()['avg_activity'] or 0

        # Get exam scores
        cursor.execute('''
            SELECT ea.score, e.exam_type
            FROM exam_attempts ea
            JOIN exams e ON ea.exam_id = e.id
            WHERE e.subject_id = ? AND ea.student_id = ?
        ''', (subject['id'], student_id))
        exams = cursor.fetchall()

        midterm = 0
        final = 0
        for exam in exams:
            if exam['exam_type'] == 'midterm':
                midterm = exam['score']
            elif exam['exam_type'] == 'final':
                final = exam['score']

        # Get final project score (for COMP012)
        final_project = 0
        if weights['final_project'] > 0:
            cursor.execute('''
                SELECT fps.score
                FROM final_project_scores fps
                JOIN final_projects fp ON fps.final_project_id = fp.id
                WHERE fp.subject_id = ? AND fps.student_id = ?
            ''', (subject['id'], student_id))
            fp_result = cursor.fetchone()
            if fp_result:
                final_project = fp_result['score'] or 0

        # Calculate weighted grade based on subject-specific weights
        weighted = (
            (quiz_avg * weights['quizzes']) +
            (activity_avg * weights['activities']) +
            (midterm * weights['midterm']) +
            (final * weights['final']) +
            (final_project * weights['final_project'])
        )

        # Get PUP grade equivalent
        pup_grade = get_pup_grade(weighted)

        grades_data.append({
            'subject': subject,
            'quiz_avg': quiz_avg,
            'activity_avg': activity_avg,
            'midterm': midterm,
            'final': final,
            'final_project': final_project,
            'weighted': weighted,
            'pup_grade': pup_grade,
            'weights': weights
        })

    conn.close()
    return render_template('student_grades.html', student=student, grades=grades_data)

# ==================== STUDENT DASHBOARD ====================

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects')
    subjects = cursor.fetchall()
    conn.close()
    return render_template('student_dashboard.html', subjects=subjects)

@app.route('/student/subject/<int:subject_id>')
@login_required
def student_subject(subject_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()
    cursor.execute('SELECT * FROM sessions WHERE subject_id = ? ORDER BY session_number', (subject_id,))
    sessions = cursor.fetchall()

    # Get available quizzes
    cursor.execute('''
        SELECT q.*, s.session_number
        FROM quizzes q
        JOIN sessions s ON q.session_id = s.id
        WHERE s.subject_id = ?
    ''', (subject_id,))
    quizzes = cursor.fetchall()

    # Get available exams
    cursor.execute('SELECT * FROM exams WHERE subject_id = ?', (subject_id,))
    exams = cursor.fetchall()

    conn.close()
    return render_template('student_subject.html', subject=subject, sessions=sessions, quizzes=quizzes, exams=exams)

@app.route('/student/session/<int:session_id>/activities')
@login_required
def student_session_activities(session_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, sub.code as subject_code, sub.name as subject_name, sub.id as subject_id
        FROM sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.id = ?
    ''', (session_id,))
    session_data = cursor.fetchone()
    cursor.execute('SELECT * FROM activities WHERE session_id = ? ORDER BY activity_number', (session_id,))
    activities = cursor.fetchall()

    # Get student's submissions for these activities
    activity_ids = [a['id'] for a in activities]
    submissions = {}
    if activity_ids:
        placeholders = ','.join('?' * len(activity_ids))
        cursor.execute(f'''
            SELECT * FROM submissions
            WHERE activity_id IN ({placeholders}) AND student_id = ?
        ''', (*activity_ids, current_user.id))
        for sub in cursor.fetchall():
            submissions[sub['activity_id']] = sub

    conn.close()
    return render_template('student_activities.html', session=session_data, activities=activities, submissions=submissions)

@app.route('/student/my-grades')
@login_required
def my_grades():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))
    return redirect(url_for('student_grades', student_id=current_user.id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
