from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import os
import json
import base64
import io
import pandas as pd
from PIL import Image
from database import get_db, init_db, DATABASE
import shutil
import glob as glob_module
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PHOTO_FOLDER'] = 'static/uploads/photos'
app.config['DOCUMENT_FOLDER'] = 'static/uploads/documents'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload folders exist
os.makedirs(app.config['PHOTO_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOCUMENT_FOLDER'], exist_ok=True)

# Initialize database (creates tables, runs migrations, seeds defaults)
init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Custom Jinja2 filter for newlines to <br>
@app.template_filter('nl2br')
def nl2br_filter(s):
    if s:
        return s.replace('\n', '<br>')
    return s

# Error handler for Request Entity Too Large (file upload too big)
@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large! Please upload a smaller file (max 16MB).', 'error')
    return redirect(request.referrer or url_for('profile'))

def compress_image(image_data, max_size=(400, 400), quality=70):
    """Compress and resize image to reduce file size"""
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))

        # Convert RGBA to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if larger than max_size while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save to bytes with compression
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"Image compression error: {e}")
        return image_data

# Custom Jinja filter to parse JSON
@app.template_filter('parse_json')
def parse_json_filter(value):
    if value:
        try:
            return json.loads(value)
        except:
            return []
    return []

@app.template_filter('from_json')
def from_json_filter(value):
    if value:
        try:
            return json.loads(value)
        except:
            return []
    return []

@app.template_filter('youtube_embed')
def youtube_embed_filter(url):
    """Convert YouTube URL to embed format."""
    if not url:
        return ''
    # Handle youtu.be/VIDEO_ID
    match = re.match(r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    # Handle youtube.com/watch?v=VIDEO_ID
    match = re.match(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', url)
    if match:
        return f'https://www.youtube.com/embed/{match.group(1)}'
    # Already embed format
    if 'youtube.com/embed/' in url:
        return url
    return url

# ==================== SESSION PROGRESS HELPERS ====================

def get_session_progress(cursor, session_id, student_id):
    """Get 5-step progress for a student in a session. Auto-completes steps that don't apply."""
    cursor.execute('SELECT * FROM session_progress WHERE session_id = ? AND student_id = ?',
                   (session_id, student_id))
    row = cursor.fetchone()
    progress = {
        'step_video': row['step_video'] if row else 0,
        'step_slides': row['step_slides'] if row else 0,
        'step_reading': row['step_reading'] if row else 0,
        'step_activity': row['step_activity'] if row else 0,
        'step_quiz': row['step_quiz'] if row else 0,
        'completed_at': row['completed_at'] if row else None,
    }
    # Auto-complete steps that don't apply for this session
    cursor.execute('SELECT youtube_url, reading_materials FROM sessions WHERE id = ?', (session_id,))
    sess = cursor.fetchone()
    if sess:
        if not sess['youtube_url']:
            progress['step_video'] = 1
        if not sess['reading_materials']:
            progress['step_reading'] = 1
    # Check if activities exist for this session
    cursor.execute('SELECT COUNT(*) as cnt FROM activities WHERE session_id = ? AND is_visible = 1', (session_id,))
    act_count = cursor.fetchone()['cnt']
    if act_count == 0:
        progress['step_activity'] = 1
    # Check if quizzes exist for this session
    cursor.execute('SELECT COUNT(*) as cnt FROM quizzes WHERE session_id = ? AND is_visible = 1', (session_id,))
    quiz_count = cursor.fetchone()['cnt']
    if quiz_count == 0:
        progress['step_quiz'] = 1
    progress['completed'] = all([
        progress['step_video'], progress['step_slides'], progress['step_reading'],
        progress['step_activity'], progress['step_quiz']
    ])
    return progress

def check_previous_session_complete(cursor, session_id, student_id):
    """Check if the previous session (by session_number) is fully completed."""
    cursor.execute('SELECT session_number, subject_id FROM sessions WHERE id = ?', (session_id,))
    current = cursor.fetchone()
    if not current or current['session_number'] <= 1:
        return True
    # Find previous visible session in same subject
    cursor.execute('''
        SELECT id FROM sessions
        WHERE subject_id = ? AND session_number = ? AND is_visible = 1
    ''', (current['subject_id'], current['session_number'] - 1))
    prev = cursor.fetchone()
    if not prev:
        return True  # No previous visible session, allow access
    cursor.execute('''
        SELECT completed_at FROM session_progress
        WHERE session_id = ? AND student_id = ?
    ''', (prev['id'], student_id))
    prog = cursor.fetchone()
    if prog and prog['completed_at']:
        return True
    # Also check via get_session_progress in case all steps auto-complete
    prev_progress = get_session_progress(cursor, prev['id'], student_id)
    return prev_progress['completed']

def check_and_mark_session_complete(cursor, session_id, student_id):
    """If all applicable steps are done, mark session as completed."""
    progress = get_session_progress(cursor, session_id, student_id)
    if progress['completed'] and not progress['completed_at']:
        cursor.execute('''
            INSERT INTO session_progress (session_id, student_id, step_video, step_slides, step_reading, step_activity, step_quiz, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id, student_id) DO UPDATE SET completed_at = CURRENT_TIMESTAMP
        ''', (session_id, student_id, progress['step_video'], progress['step_slides'],
              progress['step_reading'], progress['step_activity'], progress['step_quiz']))

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(UserMixin):
    def __init__(self, id, username, full_name, role, student_id=None, section=None, photo='default.png',
                 profile_completed=1, is_approved=1, email=None, github_account=None, railway_account=None,
                 messenger=None, pup_id_photo=None, cor_photo=None, contact_number=None,
                 programming_languages=None, databases_known=None, hosting_platforms=None, other_tools=None,
                 institution_id=None, department_id=None):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.role = role
        self.student_id = student_id
        self.section = section
        self.photo = photo or 'default.png'
        self.profile_completed = profile_completed
        self.is_approved = is_approved
        self.email = email
        self.github_account = github_account
        self.railway_account = railway_account
        self.messenger = messenger
        self.pup_id_photo = pup_id_photo
        self.cor_photo = cor_photo
        self.contact_number = contact_number
        self.programming_languages = programming_languages
        self.databases_known = databases_known
        self.hosting_platforms = hosting_platforms
        self.other_tools = other_tools
        self.institution_id = institution_id
        self.department_id = department_id

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        keys = user.keys()
        return User(
            user['id'],
            user['username'],
            user['full_name'],
            user['role'],
            user['student_id'],
            user['section'],
            user['photo'] if 'photo' in keys else 'default.png',
            user['profile_completed'] if 'profile_completed' in keys else 1,
            user['is_approved'] if 'is_approved' in keys else 1,
            user['email'] if 'email' in keys else None,
            user['github_account'] if 'github_account' in keys else None,
            user['railway_account'] if 'railway_account' in keys else None,
            user['messenger'] if 'messenger' in keys else None,
            user['pup_id_photo'] if 'pup_id_photo' in keys else None,
            user['cor_photo'] if 'cor_photo' in keys else None,
            user['contact_number'] if 'contact_number' in keys else None,
            user['programming_languages'] if 'programming_languages' in keys else None,
            user['databases_known'] if 'databases_known' in keys else None,
            user['hosting_platforms'] if 'hosting_platforms' in keys else None,
            user['other_tools'] if 'other_tools' in keys else None,
            user['institution_id'] if 'institution_id' in keys else None,
            user['department_id'] if 'department_id' in keys else None
        )
    return None

# Profile completion required decorator
def profile_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and not current_user.profile_completed:
            flash('Please complete your profile first.', 'warning')
            return redirect(url_for('complete_profile'))
        return f(*args, **kwargs)
    return decorated_function

# Admin role required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
    """Get grade component weights based on subject code
    Standard PUP Grade Distribution:
    - Activities: 50%
    - Quizzes: 10%
    - Midterm: 20%
    - Final: 20%
    """
    # All subjects use the same standard PUP grade distribution
    return {
        'quizzes': 0.10,      # 10%
        'activities': 0.50,   # 50%
        'midterm': 0.20,      # 20%
        'final': 0.20,        # 20%
        'final_project': 0.00 # Included in activities if applicable
    }

# ==================== GRADE & PERFORMANCE HELPERS ====================

def compute_weighted_grade(cursor, subject_id, student_id):
    """Compute weighted grade percentage for a student in a subject."""
    weights = get_grade_weights('')
    # Activity average (using final_score if available, else score)
    cursor.execute('''
        SELECT AVG(COALESCE(sub.final_score, sub.score)) as avg_score
        FROM submissions sub
        JOIN activities a ON sub.activity_id = a.id
        JOIN sessions ses ON a.session_id = ses.id
        WHERE ses.subject_id = ? AND sub.student_id = ?
        AND COALESCE(sub.final_score, sub.score) IS NOT NULL
    ''', (subject_id, student_id))
    activity_avg = cursor.fetchone()['avg_score'] or 0

    # Quiz average
    cursor.execute('''
        SELECT AVG(qa.score) as avg_score
        FROM quiz_attempts qa
        JOIN quizzes q ON qa.quiz_id = q.id
        JOIN sessions ses ON q.session_id = ses.id
        WHERE ses.subject_id = ? AND qa.student_id = ? AND qa.score IS NOT NULL
    ''', (subject_id, student_id))
    quiz_avg = cursor.fetchone()['avg_score'] or 0

    # Exams
    midterm = 0
    final_exam = 0
    cursor.execute('''
        SELECT ea.score, e.exam_type
        FROM exam_attempts ea
        JOIN exams e ON ea.exam_id = e.id
        WHERE e.subject_id = ? AND ea.student_id = ?
    ''', (subject_id, student_id))
    for exam in cursor.fetchall():
        if exam['exam_type'] == 'midterm':
            midterm = exam['score'] or 0
        elif exam['exam_type'] == 'final':
            final_exam = exam['score'] or 0

    # If no final exam but project groups exist, use project grade
    if final_exam == 0:
        proj = compute_project_grade(cursor, subject_id, student_id)
        if proj is not None and proj > 0:
            final_exam = proj

    return (activity_avg * weights['activities'] +
            quiz_avg * weights['quizzes'] +
            midterm * weights['midterm'] +
            final_exam * weights['final'])


def compute_project_grade(cursor, subject_id, student_id):
    """Compute project grade (0-100) based on group project progress for sessions 13-16."""
    cursor.execute('''
        SELECT pg.id FROM project_groups pg
        JOIN project_group_members pgm ON pg.id = pgm.group_id
        WHERE pg.subject_id = ? AND pgm.student_id = ?
    ''', (subject_id, student_id))
    group = cursor.fetchone()
    if not group:
        return None
    cursor.execute('''
        SELECT session_number, percentage FROM project_progress
        WHERE group_id = ?
    ''', (group['id'],))
    progress = {r['session_number']: r['percentage'] for r in cursor.fetchall()}
    if not progress:
        return 0
    total = sum(progress.get(sn, 0) for sn in [13, 14, 15, 16])
    return total / 4


def build_guidance_message(activity_avg, quiz_avg, sessions_behind, subject_code):
    """Generate smart guidance text based on student performance patterns."""
    parts = []
    if activity_avg >= 85 and quiz_avg < 75 and quiz_avg > 0:
        parts.append(f"Your activity work in {subject_code} is strong, but quiz scores need improvement. Review the lesson materials before taking quizzes.")
    elif quiz_avg >= 85 and activity_avg < 75 and activity_avg > 0:
        parts.append(f"You're doing well on quizzes in {subject_code}, showing solid understanding. Focus on submitting activities on time to boost your grade.")
    elif activity_avg < 75 and activity_avg > 0 and quiz_avg < 75 and quiz_avg > 0:
        parts.append(f"Both activity and quiz scores in {subject_code} need improvement. Consider reviewing lesson materials and attending office hours.")
    elif activity_avg >= 85 and quiz_avg >= 85:
        parts.append(f"Excellent work in {subject_code}! Keep up the outstanding performance.")
    if sessions_behind >= 3:
        parts.append(f"You're {sessions_behind} lessons behind. Complete the video and reading materials before moving to activities.")
    elif sessions_behind >= 2:
        parts.append(f"You're {sessions_behind} lessons behind. Try to catch up this week.")
    if not parts:
        parts.append(f"Keep up the work in {subject_code} and submit all requirements on time.")
    return ' '.join(parts)


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
            keys = user.keys()
            is_approved = user['is_approved'] if 'is_approved' in keys else 1

            # Check if student is approved (instructors are always approved)
            if user['role'] == 'student' and not is_approved:
                flash('Your enrollment is pending approval. Please wait for instructor approval.', 'warning')
                return render_template('login.html')

            user_obj = User(
                user['id'], user['username'], user['full_name'], user['role'],
                user['student_id'], user['section'],
                user['photo'] if 'photo' in keys else 'default.png',
                user['profile_completed'] if 'profile_completed' in keys else 1,
                is_approved
            )
            login_user(user_obj)
            flash('Logged in successfully!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'instructor':
                return redirect(url_for('dashboard'))
            return redirect(url_for('student_dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        section = request.form.get('section', '').strip()

        # Validation
        errors = []
        if not email or '@' not in email or '.' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not full_name:
            errors.append('Full name is required.')
        if not student_id:
            errors.append('Student ID is required.')
        if not section:
            errors.append('Section is required.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (email,))
        if cursor.fetchone():
            flash('Email address already registered. Please use another or log in.', 'error')
            conn.close()
            return render_template('register.html')

        # Check if student ID already exists
        cursor.execute('SELECT id FROM users WHERE student_id = ?', (student_id,))
        if cursor.fetchone():
            flash('Student ID already registered. Please contact your instructor.', 'error')
            conn.close()
            return render_template('register.html')

        # Create new student account (email is stored as username for login)
        # is_approved defaults to 0, profile_completed defaults to 0
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, student_id, section, profile_completed, is_approved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (email, generate_password_hash(password), full_name, 'student', student_id, section, 0, 0))
            conn.commit()
            flash('Registration successful! Please wait for instructor approval before logging in.', 'success')
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
            conn.close()
            return render_template('register.html')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# ==================== PROFILE ====================

@app.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if current_user.profile_completed:
        if current_user.role == 'instructor':
            return redirect(url_for('dashboard'))
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        photo_data = request.form.get('photo_data', '')
        student_id = request.form.get('student_id', '')
        email = request.form.get('email', '')
        contact_number = request.form.get('contact_number', '')
        github_account = request.form.get('github_account', '')
        railway_account = request.form.get('railway_account', '')
        messenger = request.form.get('messenger', '')

        # KYS (Know Your Student) fields
        prog_langs = request.form.getlist('programming_languages')
        prog_langs_other = request.form.get('programming_languages_other', '')
        if prog_langs_other:
            prog_langs.extend([x.strip() for x in prog_langs_other.split(',') if x.strip()])
        programming_languages = ', '.join(prog_langs)

        dbs = request.form.getlist('databases_known')
        dbs_other = request.form.get('databases_known_other', '')
        if dbs_other:
            dbs.extend([x.strip() for x in dbs_other.split(',') if x.strip()])
        databases_known = ', '.join(dbs)

        hosts = request.form.getlist('hosting_platforms')
        hosts_other = request.form.get('hosting_platforms_other', '')
        if hosts_other:
            hosts.extend([x.strip() for x in hosts_other.split(',') if x.strip()])
        hosting_platforms = ', '.join(hosts)

        tools = request.form.getlist('other_tools')
        tools_other = request.form.get('other_tools_other', '')
        if tools_other:
            tools.extend([x.strip() for x in tools_other.split(',') if x.strip()])
        other_tools = ', '.join(tools)

        conn = get_db()
        cursor = conn.cursor()

        photo_filename = 'default.png'
        pup_id_filename = None
        cor_filename = None

        # Handle base64 camera capture for selfie
        if photo_data and photo_data.startswith('data:image'):
            try:
                header, encoded = photo_data.split(',', 1)
                # Always save as jpg for smaller file size
                photo_filename = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                filepath = os.path.join(app.config['PHOTO_FOLDER'], photo_filename)

                # Decode and compress the image
                raw_image = base64.b64decode(encoded)
                compressed_image = compress_image(raw_image, max_size=(400, 400), quality=70)

                with open(filepath, 'wb') as f:
                    f.write(compressed_image)
            except Exception as e:
                flash('Error saving photo. Please try again.', 'error')
                return render_template('complete_profile.html')

        # Handle PUP ID upload
        if 'pup_id' in request.files:
            file = request.files['pup_id']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'pdf']:
                    if ext == 'pdf':
                        pup_id_filename = f"pupid_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                        file.save(os.path.join(app.config['DOCUMENT_FOLDER'], pup_id_filename))
                    else:
                        # Compress image uploads
                        pup_id_filename = f"pupid_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                        raw_image = file.read()
                        compressed_image = compress_image(raw_image, max_size=(800, 800), quality=75)
                        with open(os.path.join(app.config['DOCUMENT_FOLDER'], pup_id_filename), 'wb') as f:
                            f.write(compressed_image)

        # Handle COR upload
        if 'cor' in request.files:
            file = request.files['cor']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'pdf']:
                    if ext == 'pdf':
                        cor_filename = f"cor_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                        file.save(os.path.join(app.config['DOCUMENT_FOLDER'], cor_filename))
                    else:
                        # Compress image uploads
                        cor_filename = f"cor_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                        raw_image = file.read()
                        compressed_image = compress_image(raw_image, max_size=(800, 800), quality=75)
                        with open(os.path.join(app.config['DOCUMENT_FOLDER'], cor_filename), 'wb') as f:
                            f.write(compressed_image)

        # Update user profile with all fields including KYS
        cursor.execute('''
            UPDATE users SET
                photo = ?,
                student_id = ?,
                email = ?,
                contact_number = ?,
                github_account = ?,
                railway_account = ?,
                messenger = ?,
                pup_id_photo = ?,
                cor_photo = ?,
                programming_languages = ?,
                databases_known = ?,
                hosting_platforms = ?,
                other_tools = ?,
                profile_completed = 1
            WHERE id = ?
        ''', (photo_filename, student_id, email, contact_number, github_account,
              railway_account, messenger, pup_id_filename, cor_filename,
              programming_languages, databases_known, hosting_platforms, other_tools, current_user.id))
        conn.commit()
        conn.close()

        flash('Profile completed successfully!', 'success')
        if current_user.role == 'instructor':
            return redirect(url_for('dashboard'))
        return redirect(url_for('student_dashboard'))

    return render_template('complete_profile.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        photo_data = request.form.get('photo_data', '')

        conn = get_db()
        cursor = conn.cursor()

        # Handle base64 camera capture
        if photo_data and photo_data.startswith('data:image'):
            try:
                header, encoded = photo_data.split(',', 1)
                # Always save as jpg for smaller file size
                filename = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                filepath = os.path.join(app.config['PHOTO_FOLDER'], filename)

                # Decode and compress the image
                raw_image = base64.b64decode(encoded)
                compressed_image = compress_image(raw_image, max_size=(400, 400), quality=70)

                with open(filepath, 'wb') as f:
                    f.write(compressed_image)

                cursor.execute('UPDATE users SET photo = ? WHERE id = ?', (filename, current_user.id))
            except Exception as e:
                flash('Error saving photo.', 'error')

        # Handle file upload
        elif 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                if ext in ['png', 'jpg', 'jpeg', 'gif']:
                    # Always save as jpg for smaller file size
                    filename = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    filepath = os.path.join(app.config['PHOTO_FOLDER'], filename)

                    # Read and compress uploaded image
                    raw_image = file.read()
                    compressed_image = compress_image(raw_image, max_size=(400, 400), quality=70)

                    with open(filepath, 'wb') as f:
                        f.write(compressed_image)

                    cursor.execute('UPDATE users SET photo = ? WHERE id = ?', (filename, current_user.id))

        conn.commit()
        conn.close()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    if current_user.role != 'student':
        flash('Only students can update their profile.', 'error')
        return redirect(url_for('profile'))

    student_id = request.form.get('student_id', '')
    email = request.form.get('email', '')
    contact_number = request.form.get('contact_number', '')
    github_account = request.form.get('github_account', '')
    railway_account = request.form.get('railway_account', '')
    messenger = request.form.get('messenger', '')

    conn = get_db()
    cursor = conn.cursor()

    # Start building the update query
    update_fields = []
    params = []

    if student_id:
        update_fields.append('student_id = ?')
        params.append(student_id)
    if email:
        update_fields.append('email = ?')
        params.append(email)
    if contact_number:
        update_fields.append('contact_number = ?')
        params.append(contact_number)
    if github_account:
        update_fields.append('github_account = ?')
        params.append(github_account)
    if railway_account:
        update_fields.append('railway_account = ?')
        params.append(railway_account)

    # Messenger can be empty (optional)
    update_fields.append('messenger = ?')
    params.append(messenger if messenger else None)

    # Handle PUP ID upload
    if 'pup_id' in request.files:
        file = request.files['pup_id']
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            if ext in ['png', 'jpg', 'jpeg', 'gif', 'pdf']:
                if ext == 'pdf':
                    pup_id_filename = f"pupid_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                    file.save(os.path.join(app.config['DOCUMENT_FOLDER'], pup_id_filename))
                else:
                    # Compress image uploads
                    pup_id_filename = f"pupid_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    raw_image = file.read()
                    compressed_image = compress_image(raw_image, max_size=(800, 800), quality=75)
                    with open(os.path.join(app.config['DOCUMENT_FOLDER'], pup_id_filename), 'wb') as f:
                        f.write(compressed_image)
                update_fields.append('pup_id_photo = ?')
                params.append(pup_id_filename)

    # Handle COR upload
    if 'cor' in request.files:
        file = request.files['cor']
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            if ext in ['png', 'jpg', 'jpeg', 'gif', 'pdf']:
                if ext == 'pdf':
                    cor_filename = f"cor_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                    file.save(os.path.join(app.config['DOCUMENT_FOLDER'], cor_filename))
                else:
                    # Compress image uploads
                    cor_filename = f"cor_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    raw_image = file.read()
                    compressed_image = compress_image(raw_image, max_size=(800, 800), quality=75)
                    with open(os.path.join(app.config['DOCUMENT_FOLDER'], cor_filename), 'wb') as f:
                        f.write(compressed_image)
                update_fields.append('cor_photo = ?')
                params.append(cor_filename)

    if update_fields:
        params.append(current_user.id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

    conn.close()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        flash('All fields are required.', 'error')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('profile'))

    conn = get_db()
    cursor = conn.cursor()

    # Verify current password
    cursor.execute('SELECT password_hash FROM users WHERE id = ?', (current_user.id,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user['password_hash'], current_password):
        flash('Current password is incorrect.', 'error')
        conn.close()
        return redirect(url_for('profile'))

    # Update password
    new_hash = generate_password_hash(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, current_user.id))
    conn.commit()
    conn.close()

    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile'))

# ==================== VISIBILITY API ====================

@app.route('/api/toggle-visibility', methods=['POST'])
@login_required
def toggle_visibility():
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    item_type = data.get('type')
    item_id = data.get('id')

    conn = get_db()
    cursor = conn.cursor()

    if item_type == 'session':
        cursor.execute('SELECT is_visible FROM sessions WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            new_value = 0 if result['is_visible'] else 1
            cursor.execute('UPDATE sessions SET is_visible = ? WHERE id = ?', (new_value, item_id))
    elif item_type == 'activity':
        cursor.execute('SELECT is_visible FROM activities WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            new_value = 0 if result['is_visible'] else 1
            cursor.execute('UPDATE activities SET is_visible = ? WHERE id = ?', (new_value, item_id))
    elif item_type == 'activity_active':
        cursor.execute('SELECT is_active FROM activities WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            keys = result.keys()
            current_value = result['is_active'] if 'is_active' in keys else 1
            new_value = 0 if current_value else 1
            cursor.execute('UPDATE activities SET is_active = ? WHERE id = ?', (new_value, item_id))
    elif item_type == 'quiz':
        cursor.execute('SELECT is_visible FROM quizzes WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            new_value = 0 if result['is_visible'] else 1
            cursor.execute('UPDATE quizzes SET is_visible = ? WHERE id = ?', (new_value, item_id))
    elif item_type == 'exam':
        cursor.execute('SELECT is_visible FROM exams WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            new_value = 0 if result['is_visible'] else 1
            cursor.execute('UPDATE exams SET is_visible = ? WHERE id = ?', (new_value, item_id))
    elif item_type == 'score':
        cursor.execute('SELECT score_visible FROM submissions WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            new_value = 0 if result['score_visible'] else 1
            cursor.execute('UPDATE submissions SET score_visible = ? WHERE id = ?', (new_value, item_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'is_visible': bool(new_value)})
    elif item_type == 'quiz_score':
        cursor.execute('SELECT score_visible FROM quiz_attempts WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            new_value = 0 if result['score_visible'] else 1
            cursor.execute('UPDATE quiz_attempts SET score_visible = ? WHERE id = ?', (new_value, item_id))
    elif item_type == 'exam_score':
        cursor.execute('SELECT score_visible FROM exam_attempts WHERE id = ?', (item_id,))
        result = cursor.fetchone()
        if result:
            new_value = 0 if result['score_visible'] else 1
            cursor.execute('UPDATE exam_attempts SET score_visible = ? WHERE id = ?', (new_value, item_id))
    else:
        conn.close()
        return jsonify({'error': 'Invalid type'}), 400

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'is_visible': bool(new_value)})

@app.route('/api/session/youtube-url', methods=['POST'])
@login_required
def save_session_youtube_url():
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')
    youtube_url = data.get('youtube_url', '').strip()
    video_duration = data.get('video_duration', 0)

    # Validate YouTube URL format (allow empty to clear)
    if youtube_url and not any(domain in youtube_url for domain in ['youtube.com', 'youtu.be']):
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE sessions SET youtube_url = ?, video_duration = ? WHERE id = ?',
                   (youtube_url or None, video_duration or 0, session_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'youtube_url': youtube_url})

@app.route('/api/session/video-heartbeat', methods=['POST'])
@login_required
def video_heartbeat():
    """Track video watch progress with anti-cheat validation."""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')
    current_time = data.get('current_time', 0)  # seconds
    duration = data.get('duration', 0)  # total video duration in seconds

    if not session_id or duration <= 0:
        return jsonify({'error': 'Invalid data'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Verify session has a YouTube URL
    cursor.execute('SELECT youtube_url, video_duration FROM sessions WHERE id = ?', (session_id,))
    sess = cursor.fetchone()
    if not sess or not sess['youtube_url']:
        conn.close()
        return jsonify({'error': 'No video for this session'}), 400

    # Update video_duration if not set yet
    if not sess['video_duration'] and duration > 0:
        cursor.execute('UPDATE sessions SET video_duration = ? WHERE id = ?', (int(duration), session_id))

    # Get or create watch record
    cursor.execute('''
        SELECT * FROM session_video_watches WHERE session_id = ? AND student_id = ?
    ''', (session_id, current_user.id))
    watch = cursor.fetchone()

    if watch:
        last_pos = watch['last_position'] or 0
        delta = current_time - last_pos
        # Anti-cheat: max 10 seconds per heartbeat (5s interval + 5s tolerance)
        # Also handle backward seeks (delta < 0) — that's fine, just don't add time
        if delta > 10:
            delta = 5  # Cap to normal heartbeat interval
        if delta < 0:
            delta = 0
        new_watched = (watch['watched_seconds'] or 0) + delta
        completed = 1 if new_watched >= duration * 0.98 else (watch['completed'] or 0)  # 98% threshold for rounding
        cursor.execute('''
            UPDATE session_video_watches
            SET watched_seconds = ?, last_position = ?, last_heartbeat_at = CURRENT_TIMESTAMP, completed = ?
            WHERE session_id = ? AND student_id = ?
        ''', (int(new_watched), int(current_time), completed, session_id, current_user.id))
    else:
        new_watched = min(current_time, 5)  # First heartbeat
        completed = 1 if new_watched >= duration * 0.98 else 0
        cursor.execute('''
            INSERT INTO session_video_watches (session_id, student_id, watched_seconds, last_position, last_heartbeat_at, completed)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        ''', (session_id, current_user.id, int(new_watched), int(current_time), completed))

    # If completed, update session progress
    if completed:
        cursor.execute('''
            INSERT INTO session_progress (session_id, student_id, step_video)
            VALUES (?, ?, 1)
            ON CONFLICT(session_id, student_id) DO UPDATE SET step_video = 1
        ''', (session_id, current_user.id))
        check_and_mark_session_complete(cursor, session_id, current_user.id)

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'watched_seconds': int(new_watched), 'completed': bool(completed)})

@app.route('/api/session/complete-slides', methods=['POST'])
@login_required
def complete_slides():
    """Mark slides as read for a session."""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')

    conn = get_db()
    cursor = conn.cursor()

    # Check video step is complete first
    progress = get_session_progress(cursor, session_id, current_user.id)
    if not progress['step_video']:
        conn.close()
        return jsonify({'error': 'Watch the video first'}), 400

    cursor.execute('''
        INSERT INTO session_progress (session_id, student_id, step_slides)
        VALUES (?, ?, 1)
        ON CONFLICT(session_id, student_id) DO UPDATE SET step_slides = 1
    ''', (session_id, current_user.id))
    check_and_mark_session_complete(cursor, session_id, current_user.id)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/session/complete-reading', methods=['POST'])
@login_required
def complete_reading():
    """Mark reading materials as finished for a session."""
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')

    conn = get_db()
    cursor = conn.cursor()

    # Check slides step is complete first
    progress = get_session_progress(cursor, session_id, current_user.id)
    if not progress['step_slides']:
        conn.close()
        return jsonify({'error': 'Complete the slides first'}), 400

    cursor.execute('''
        INSERT INTO session_progress (session_id, student_id, step_reading)
        VALUES (?, ?, 1)
        ON CONFLICT(session_id, student_id) DO UPDATE SET step_reading = 1
    ''', (session_id, current_user.id))
    check_and_mark_session_complete(cursor, session_id, current_user.id)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/session/<int:session_id>/progress')
@login_required
def get_progress(session_id):
    """Get full progress for a student in a session."""
    conn = get_db()
    cursor = conn.cursor()
    progress = get_session_progress(cursor, session_id, current_user.id)

    # Also get video watch seconds
    cursor.execute('''
        SELECT watched_seconds, completed FROM session_video_watches
        WHERE session_id = ? AND student_id = ?
    ''', (session_id, current_user.id))
    watch = cursor.fetchone()
    progress['watched_seconds'] = watch['watched_seconds'] if watch else 0
    progress['video_completed'] = bool(watch['completed']) if watch else False

    # Get video duration
    cursor.execute('SELECT video_duration FROM sessions WHERE id = ?', (session_id,))
    sess = cursor.fetchone()
    progress['video_duration'] = sess['video_duration'] if sess else 0

    conn.close()
    return jsonify(progress)

@app.route('/api/session/reading-materials', methods=['POST'])
@login_required
def save_reading_materials():
    """Save reading materials for a session (instructor only)."""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')
    content = data.get('content', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE sessions SET reading_materials = ? WHERE id = ?',
                   (content or None, session_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/session/reading-audio', methods=['POST'])
@login_required
def upload_reading_audio():
    """Upload MP3 audio for reading materials (instructor only)."""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file extension
    allowed_extensions = {'.mp3', '.wav', '.ogg', '.m4a'}
    ext = os.path.splitext(audio_file.filename)[1].lower()
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: MP3, WAV, OGG, M4A'}), 400

    # Save file
    filename = f"reading_audio_{session_id}{ext}"
    audio_dir = os.path.join(app.root_path, 'static', 'uploads', 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    filepath = os.path.join(audio_dir, filename)
    audio_file.save(filepath)

    # Update database
    relative_path = f"uploads/audio/{filename}"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE sessions SET reading_audio = ? WHERE id = ?',
                   (relative_path, session_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'audio_path': relative_path})

@app.route('/api/session/reading-audio/delete', methods=['POST'])
@login_required
def delete_reading_audio():
    """Delete reading audio for a session (instructor only)."""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT reading_audio FROM sessions WHERE id = ?', (session_id,))
    session = cursor.fetchone()
    if session and session['reading_audio']:
        # Delete file
        filepath = os.path.join(app.root_path, 'static', session['reading_audio'])
        if os.path.exists(filepath):
            os.remove(filepath)
    cursor.execute('UPDATE sessions SET reading_audio = NULL WHERE id = ?', (session_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/session/unlock', methods=['POST'])
@login_required
def unlock_session_for_students():
    """Instructor manually unlocks a session by marking the PREVIOUS session as complete."""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    session_id = data.get('session_id')
    student_id = data.get('student_id')  # specific student or 'all'

    conn = get_db()
    cursor = conn.cursor()

    # Get session info
    cursor.execute('SELECT id, subject_id, session_number FROM sessions WHERE id = ?', (session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        return jsonify({'error': 'Session not found'}), 404

    # Find the previous session to mark as complete
    cursor.execute('''
        SELECT id FROM sessions
        WHERE subject_id = ? AND session_number = ? AND is_visible = 1
    ''', (session['subject_id'], session['session_number'] - 1))
    prev_session = cursor.fetchone()

    # Determine which session to mark complete
    # If session_number == 1, we mark THIS session's progress steps as complete
    # Otherwise, we mark the PREVIOUS session as complete to unlock THIS one
    target_session_id = prev_session['id'] if prev_session else session_id

    # Get students to unlock for
    if student_id == 'all':
        cursor.execute('''
            SELECT student_id FROM enrollments WHERE subject_id = ?
        ''', (session['subject_id'],))
        student_ids = [row['student_id'] for row in cursor.fetchall()]
    else:
        student_ids = [int(student_id)]

    unlocked = 0
    for sid in student_ids:
        cursor.execute('''
            INSERT INTO session_progress (session_id, student_id, step_video, step_slides, step_reading, step_activity, step_quiz, completed_at)
            VALUES (?, ?, 1, 1, 1, 1, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id, student_id) DO UPDATE SET
                step_video = 1, step_slides = 1, step_reading = 1,
                step_activity = 1, step_quiz = 1, completed_at = CURRENT_TIMESTAMP
        ''', (target_session_id, sid))
        unlocked += 1

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'unlocked': unlocked})

# ==================== PROJECT GROUP MANAGEMENT ====================

@app.route('/subject/<int:subject_id>/groups')
@login_required
def project_groups(subject_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()
    if not subject:
        conn.close()
        flash('Subject not found', 'error')
        return redirect(url_for('dashboard'))

    # Get groups with members
    cursor.execute('SELECT * FROM project_groups WHERE subject_id = ? ORDER BY group_number', (subject_id,))
    groups = [dict(g) for g in cursor.fetchall()]
    for group in groups:
        cursor.execute('''
            SELECT u.id, u.full_name, u.photo, u.student_id as sid, pgm.role
            FROM project_group_members pgm
            JOIN users u ON pgm.student_id = u.id
            WHERE pgm.group_id = ?
            ORDER BY pgm.role DESC, u.full_name
        ''', (group['id'],))
        group['members'] = [dict(m) for m in cursor.fetchall()]
        cursor.execute('SELECT * FROM project_progress WHERE group_id = ? ORDER BY session_number', (group['id'],))
        prog_rows = cursor.fetchall()
        group['progress'] = {r['session_number']: dict(r) for r in prog_rows}
        total_pct = sum(r['percentage'] for r in prog_rows)
        group['avg_progress'] = total_pct / 4 if prog_rows else 0

    # Get enrolled students for count
    cursor.execute('''
        SELECT COUNT(*) as cnt FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.subject_id = ? AND u.is_approved = 1
    ''', (subject_id,))
    total_enrolled = cursor.fetchone()['cnt']

    conn.close()
    return render_template('project_groups.html', subject=subject, groups=groups, total_enrolled=total_enrolled)


@app.route('/api/groups/assign/<int:subject_id>', methods=['POST'])
@login_required
def assign_project_groups(subject_id):
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403
    import random
    conn = get_db()
    cursor = conn.cursor()

    # Check existing groups
    cursor.execute('SELECT COUNT(*) as cnt FROM project_groups WHERE subject_id = ?', (subject_id,))
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
        return jsonify({'error': 'Groups already exist. Delete them first to re-randomize.'}), 400

    # Get enrolled students
    cursor.execute('''
        SELECT u.id, u.full_name FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.subject_id = ? AND u.is_approved = 1
        ORDER BY u.full_name
    ''', (subject_id,))
    students = [dict(s) for s in cursor.fetchall()]
    if len(students) < 2:
        conn.close()
        return jsonify({'error': 'Need at least 2 enrolled students'}), 400

    random.shuffle(students)

    # Divide into groups of 3
    groups = []
    i = 0
    while i < len(students):
        remaining = len(students) - i
        if remaining == 4:
            groups.append(students[i:i+4])
            i += 4
        elif remaining == 2:
            groups.append(students[i:i+2])
            i += 2
        else:
            groups.append(students[i:i+3])
            i += 3

    # Insert groups
    for idx, group_students in enumerate(groups):
        gnum = idx + 1
        cursor.execute('INSERT INTO project_groups (subject_id, group_number, group_name) VALUES (?, ?, ?)',
                        (subject_id, gnum, f'Group {gnum}'))
        group_id = cursor.lastrowid
        for j, student in enumerate(group_students):
            role = 'leader' if j == 0 else 'member'
            cursor.execute('INSERT INTO project_group_members (group_id, student_id, role) VALUES (?, ?, ?)',
                            (group_id, student['id'], role))
        # Initialize progress for sessions 13-16
        for sn in [13, 14, 15, 16]:
            cursor.execute('INSERT OR IGNORE INTO project_progress (group_id, session_number, percentage) VALUES (?, ?, 0)',
                            (group_id, sn))
        # Notify members
        member_names = ', '.join(s['full_name'] for s in group_students)
        for student in group_students:
            cursor.execute('''
                INSERT INTO notifications (user_id, type, icon, message, link)
                VALUES (?, 'info', 'users', ?, ?)
            ''', (student['id'],
                  f'You have been assigned to Group {gnum} for the finals project! Members: {member_names}',
                  f'/student/dashboard'))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'groups_created': len(groups), 'students_assigned': len(students)})


@app.route('/api/groups/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_project_groups(subject_id):
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM project_groups WHERE subject_id = ?', (subject_id,))
    group_ids = [r['id'] for r in cursor.fetchall()]
    if group_ids:
        ph = ','.join('?' * len(group_ids))
        cursor.execute(f'DELETE FROM project_progress WHERE group_id IN ({ph})', group_ids)
        cursor.execute(f'DELETE FROM project_group_members WHERE group_id IN ({ph})', group_ids)
        cursor.execute('DELETE FROM project_groups WHERE subject_id = ?', (subject_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/groups/progress', methods=['POST'])
@login_required
def update_group_progress():
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    group_id = data['group_id']
    session_number = data['session_number']
    percentage = min(100, max(0, int(data['percentage'])))
    notes = data.get('notes', '')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO project_progress (group_id, session_number, percentage, notes, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(group_id, session_number) DO UPDATE SET
            percentage = ?, notes = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
    ''', (group_id, session_number, percentage, notes, current_user.id,
          percentage, notes, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== INSTRUCTOR MONITORING ====================

@app.route('/instructor/monitoring')
@login_required
def instructor_monitoring():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))
    filter_subject = request.args.get('subject_id', type=int)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects ORDER BY code, section')
    subjects = cursor.fetchall()

    at_risk_students = []
    missed_deadline_count = 0
    low_grade_count = 0
    behind_count = 0

    target_subjects = [s for s in subjects if s['id'] == filter_subject] if filter_subject else subjects
    for subj in target_subjects:
        cursor.execute('''
            SELECT u.* FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.subject_id = ? AND u.is_approved = 1
            ORDER BY u.full_name
        ''', (subj['id'],))
        students = cursor.fetchall()
        for student in students:
            issues = []
            # 1. Missed deadlines
            cursor.execute('''
                SELECT a.title, a.due_date, ses.session_number
                FROM activities a
                JOIN sessions ses ON a.session_id = ses.id
                WHERE ses.subject_id = ? AND a.due_date IS NOT NULL
                AND a.due_date < date('now') AND a.is_visible = 1
                AND a.id NOT IN (SELECT activity_id FROM submissions WHERE student_id = ?)
            ''', (subj['id'], student['id']))
            missed = cursor.fetchall()
            for m in missed:
                issues.append({'type': 'missed_deadline', 'severity': 'critical',
                               'message': f'Missed {m["title"]} (Session {m["session_number"]}, due {m["due_date"]})',
                               'icon': 'clock'})
                missed_deadline_count += 1

            # 2. Low grades
            weighted = compute_weighted_grade(cursor, subj['id'], student['id'])
            if weighted > 0 and weighted < 75:
                issues.append({'type': 'low_grade', 'severity': 'critical',
                               'message': f'Failing: {weighted:.1f}% (needs 75%)',
                               'icon': 'exclamation-triangle'})
                low_grade_count += 1
            elif weighted > 0 and weighted < 82:
                issues.append({'type': 'low_grade', 'severity': 'warning',
                               'message': f'At risk: {weighted:.1f}%',
                               'icon': 'exclamation-circle'})
                low_grade_count += 1

            # 3. Behind on sessions
            cursor.execute('SELECT id FROM sessions WHERE subject_id = ? AND is_visible = 1', (subj['id'],))
            visible_sessions = cursor.fetchall()
            completed_count = 0
            for vs in visible_sessions:
                prog = get_session_progress(cursor, vs['id'], student['id'])
                if prog.get('completed'):
                    completed_count += 1
            sessions_behind = len(visible_sessions) - completed_count
            if sessions_behind >= 3:
                issues.append({'type': 'behind_progress', 'severity': 'critical',
                               'message': f'{sessions_behind} sessions behind ({completed_count}/{len(visible_sessions)})',
                               'icon': 'tasks'})
                behind_count += 1
            elif sessions_behind >= 2:
                issues.append({'type': 'behind_progress', 'severity': 'warning',
                               'message': f'{sessions_behind} sessions behind',
                               'icon': 'tasks'})
                behind_count += 1

            if issues:
                at_risk_students.append({
                    'student': student, 'subject': subj, 'issues': issues,
                    'issue_count': len(issues),
                    'max_severity': 'critical' if any(i['severity'] == 'critical' for i in issues) else 'warning',
                    'weighted_grade': weighted
                })

    at_risk_students.sort(key=lambda x: (0 if x['max_severity'] == 'critical' else 1, -x['issue_count']))

    # Count alerts already sent
    cursor.execute('SELECT COUNT(*) as cnt FROM performance_alerts WHERE notification_sent = 1')
    alerts_sent = cursor.fetchone()['cnt']
    conn.close()

    return render_template('instructor_monitoring.html',
                           subjects=subjects, at_risk_students=at_risk_students,
                           filter_subject=filter_subject,
                           missed_deadline_count=missed_deadline_count,
                           low_grade_count=low_grade_count, behind_count=behind_count,
                           alerts_sent=alerts_sent)


@app.route('/api/monitoring/send-reminders', methods=['POST'])
@login_required
def send_performance_reminders():
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    subject_id = data.get('subject_id')
    conn = get_db()
    cursor = conn.cursor()

    # Compute at-risk students
    target_subjects = []
    if subject_id:
        cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
        s = cursor.fetchone()
        if s:
            target_subjects = [s]
    else:
        cursor.execute('SELECT * FROM subjects ORDER BY code')
        target_subjects = cursor.fetchall()

    notifs_sent = 0
    for subj in target_subjects:
        cursor.execute('''
            SELECT u.id, u.full_name FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.subject_id = ? AND u.is_approved = 1
        ''', (subj['id'],))
        students = cursor.fetchall()
        for student in students:
            messages = []
            # Check missed deadlines
            cursor.execute('''
                SELECT a.title FROM activities a
                JOIN sessions ses ON a.session_id = ses.id
                WHERE ses.subject_id = ? AND a.due_date IS NOT NULL
                AND a.due_date < date('now') AND a.is_visible = 1
                AND a.id NOT IN (SELECT activity_id FROM submissions WHERE student_id = ?)
            ''', (subj['id'], student['id']))
            missed = cursor.fetchall()
            if missed:
                titles = ', '.join(m['title'] for m in missed[:3])
                messages.append(f"You have {len(missed)} missed deadline(s) in {subj['code']}: {titles}. Submit ASAP.")

            # Check low grade
            weighted = compute_weighted_grade(cursor, subj['id'], student['id'])
            if weighted > 0 and weighted < 75:
                messages.append(f"Academic alert: Your grade in {subj['code']} is {weighted:.1f}%. You need 75% to pass.")

            # Check behind
            cursor.execute('SELECT id FROM sessions WHERE subject_id = ? AND is_visible = 1', (subj['id'],))
            vis = cursor.fetchall()
            done = 0
            for v in vis:
                p = get_session_progress(cursor, v['id'], student['id'])
                if p.get('completed'):
                    done += 1
            behind = len(vis) - done
            if behind >= 3:
                messages.append(f"You are {behind} sessions behind in {subj['code']}. Complete your lessons.")

            for msg in messages:
                # Check if we already sent this exact message recently
                cursor.execute('''
                    SELECT id FROM performance_alerts
                    WHERE student_id = ? AND subject_id = ? AND message = ? AND notification_sent = 1
                    AND created_at > datetime('now', '-7 days')
                ''', (student['id'], subj['id'], msg))
                if cursor.fetchone():
                    continue
                # Create alert record
                alert_type = 'missed_deadline' if 'missed' in msg.lower() else ('low_grade' if 'grade' in msg.lower() else 'behind_progress')
                severity = 'critical' if 'need 75%' in msg or behind >= 3 else 'warning'
                cursor.execute('''
                    INSERT INTO performance_alerts (student_id, subject_id, alert_type, severity, message, notification_sent)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (student['id'], subj['id'], alert_type, severity, msg))
                # Send notification
                icon = 'clock' if alert_type == 'missed_deadline' else ('chart-line' if alert_type == 'low_grade' else 'tasks')
                cursor.execute('''
                    INSERT INTO notifications (user_id, type, icon, message, link)
                    VALUES (?, 'warning', ?, ?, '/student/dashboard')
                ''', (student['id'], icon, msg))
                notifs_sent += 1

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'notifications_sent': notifs_sent})


@app.route('/api/monitoring/send-guidance', methods=['POST'])
@login_required
def send_performance_guidance():
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    student_id = data['student_id']
    subject_id = data['subject_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()
    if not subject:
        conn.close()
        return jsonify({'error': 'Subject not found'}), 404

    # Compute component averages
    cursor.execute('''
        SELECT AVG(COALESCE(sub.final_score, sub.score)) as avg
        FROM submissions sub JOIN activities a ON sub.activity_id = a.id
        JOIN sessions ses ON a.session_id = ses.id
        WHERE ses.subject_id = ? AND sub.student_id = ? AND COALESCE(sub.final_score, sub.score) IS NOT NULL
    ''', (subject_id, student_id))
    activity_avg = cursor.fetchone()['avg'] or 0

    cursor.execute('''
        SELECT AVG(qa.score) as avg FROM quiz_attempts qa
        JOIN quizzes q ON qa.quiz_id = q.id JOIN sessions ses ON q.session_id = ses.id
        WHERE ses.subject_id = ? AND qa.student_id = ? AND qa.score IS NOT NULL
    ''', (subject_id, student_id))
    quiz_avg = cursor.fetchone()['avg'] or 0

    cursor.execute('SELECT id FROM sessions WHERE subject_id = ? AND is_visible = 1', (subject_id,))
    vis = cursor.fetchall()
    done = sum(1 for v in vis if get_session_progress(cursor, v['id'], student_id).get('completed'))
    sessions_behind = len(vis) - done

    msg = build_guidance_message(activity_avg, quiz_avg, sessions_behind, subject['code'])
    cursor.execute('''
        INSERT INTO notifications (user_id, type, icon, message, link)
        VALUES (?, 'info', 'lightbulb', ?, '/my_grades')
    ''', (student_id, msg))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': msg})


@app.route('/api/bulk-visibility', methods=['POST'])
@login_required
def bulk_visibility():
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    activity_id = data.get('activity_id')
    make_visible = data.get('make_visible', True)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE submissions SET score_visible = ? WHERE activity_id = ?',
                   (1 if make_visible else 0, activity_id))
    count = cursor.rowcount
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'count': count})

@app.route('/api/bulk-toggle-subject-visibility', methods=['POST'])
@login_required
def bulk_toggle_subject_visibility():
    """Show or hide ALL sessions, activities, quizzes, and exams for a subject at once."""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    subject_id = data.get('subject_id')
    action = data.get('action')  # 'show' or 'hide'

    if not subject_id or action not in ('show', 'hide'):
        return jsonify({'error': 'Invalid parameters'}), 400

    new_value = 1 if action == 'show' else 0

    conn = get_db()
    cursor = conn.cursor()

    # Update all sessions
    cursor.execute('UPDATE sessions SET is_visible = ? WHERE subject_id = ?', (new_value, subject_id))
    session_count = cursor.rowcount

    # Update all activities within those sessions
    cursor.execute('''
        UPDATE activities SET is_visible = ?
        WHERE session_id IN (SELECT id FROM sessions WHERE subject_id = ?)
    ''', (new_value, subject_id))

    # Update all quizzes within those sessions
    cursor.execute('''
        UPDATE quizzes SET is_visible = ?
        WHERE session_id IN (SELECT id FROM sessions WHERE subject_id = ?)
    ''', (new_value, subject_id))

    # Update all exams for this subject
    cursor.execute('''
        UPDATE exams SET is_visible = ?
        WHERE subject_id = ?
    ''', (new_value, subject_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'action': action, 'sessions': session_count})

@app.route('/api/bulk-toggle-activities', methods=['POST'])
@login_required
def bulk_toggle_activities():
    """Open or close all activities for a given subject at once."""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    subject_id = data.get('subject_id')
    action = data.get('action')  # 'open' or 'close'

    if not subject_id or action not in ('open', 'close'):
        return jsonify({'error': 'Invalid parameters'}), 400

    new_value = 1 if action == 'open' else 0

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE activities SET is_active = ?
        WHERE session_id IN (SELECT id FROM sessions WHERE subject_id = ?)
    ''', (new_value, subject_id))
    count = cursor.rowcount
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'count': count, 'action': action})

# ==================== INSTRUCTOR DASHBOARD ====================

@app.route('/dashboard')
@login_required
@profile_required
def dashboard():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects')
    subjects = cursor.fetchall()
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "student" AND is_approved = 1')
    student_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "student" AND (is_approved = 0 OR is_approved IS NULL)')
    pending_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM sessions')
    session_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM activities')
    activity_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM quizzes')
    quiz_count = cursor.fetchone()['count']
    conn.close()

    stats = {
        'students': student_count,
        'pending': pending_count,
        'subjects': len(subjects),
        'sessions': session_count,
        'activities': activity_count,
        'quizzes': quiz_count
    }

    return render_template('dashboard.html', subjects=subjects, student_count=student_count, stats=stats)

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
    cursor.execute('SELECT * FROM subjects ORDER BY code, section')
    subjects = cursor.fetchall()

    # Get distinct sections for filter
    cursor.execute('SELECT DISTINCT section FROM users WHERE role = "student" AND section IS NOT NULL ORDER BY section')
    sections = [r['section'] for r in cursor.fetchall()]

    # Get enrollment counts per student
    cursor.execute('''
        SELECT e.student_id, COUNT(*) as subject_count,
               GROUP_CONCAT(s.code || ' ' || s.section, ', ') as enrolled_subjects
        FROM enrollments e
        JOIN subjects s ON e.subject_id = s.id
        GROUP BY e.student_id
    ''')
    enrollment_map = {r['student_id']: r for r in cursor.fetchall()}

    conn.close()

    return render_template('students.html', students=students_list, subjects=subjects,
                           sections=sections, enrollment_map=enrollment_map)

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
    subject_ids = request.form.getlist('subjects')  # Get selected subjects

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role, student_id, section)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, generate_password_hash(password), full_name, 'student', student_id, section))
        conn.commit()

        # Get the new student's ID
        new_student_id = cursor.lastrowid

        # Enroll student in selected subjects
        for subj_id in subject_ids:
            try:
                cursor.execute('''
                    INSERT INTO enrollments (student_id, subject_id)
                    VALUES (?, ?)
                ''', (new_student_id, int(subj_id)))
            except:
                pass  # Skip if already enrolled
        conn.commit()

        flash(f'Student {full_name} added and enrolled in {len(subject_ids)} subject(s)!', 'success')
    except Exception as e:
        flash(f'Error adding student: {str(e)}', 'error')
    conn.close()

    return redirect(url_for('students'))

@app.route('/students/<int:student_id>/enrollments', methods=['GET', 'POST'])
@login_required
def manage_enrollments(student_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get student info
    cursor.execute('SELECT * FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()

    if not student:
        flash('Student not found', 'error')
        conn.close()
        return redirect(url_for('students'))

    if request.method == 'POST':
        # Get selected subjects
        subject_ids = request.form.getlist('subjects')

        # Remove all current enrollments
        cursor.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))

        # Add new enrollments
        for subj_id in subject_ids:
            cursor.execute('''
                INSERT INTO enrollments (student_id, subject_id) VALUES (?, ?)
            ''', (student_id, int(subj_id)))

        conn.commit()
        flash(f'Enrollments updated for {student["full_name"]}!', 'success')
        conn.close()
        return redirect(url_for('students'))

    # GET: Show enrollment form
    cursor.execute('SELECT * FROM subjects ORDER BY code, section')
    subjects = cursor.fetchall()

    # Get current enrollments
    cursor.execute('SELECT subject_id FROM enrollments WHERE student_id = ?', (student_id,))
    enrolled_ids = [row['subject_id'] for row in cursor.fetchall()]

    conn.close()
    return render_template('manage_enrollments.html', student=student, subjects=subjects, enrolled_ids=enrolled_ids)

@app.route('/students/bulk-enroll', methods=['POST'])
@login_required
def bulk_enroll_students():
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    subject_ids = request.form.getlist('subjects')
    student_ids_str = request.form.get('student_ids', '')  # comma-separated
    mode = request.form.get('mode', 'all')  # 'all' or 'selected'

    if not subject_ids:
        flash('Please select at least one subject.', 'error')
        return redirect(url_for('students'))

    conn = get_db()
    cursor = conn.cursor()

    # Get student list
    if mode == 'selected' and student_ids_str:
        student_id_list = [int(sid) for sid in student_ids_str.split(',') if sid.strip()]
        placeholders = ','.join('?' * len(student_id_list))
        cursor.execute(f'SELECT id, full_name FROM users WHERE role = "student" AND id IN ({placeholders})', student_id_list)
    else:
        cursor.execute('SELECT id, full_name FROM users WHERE role = "student"')

    student_list = cursor.fetchall()
    enrolled_count = 0

    for student in student_list:
        for subj_id in subject_ids:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO enrollments (student_id, subject_id)
                    VALUES (?, ?)
                ''', (student['id'], int(subj_id)))
                if cursor.rowcount > 0:
                    enrolled_count += 1
            except:
                pass

    conn.commit()
    conn.close()

    flash(f'Bulk enrollment complete! {enrolled_count} new enrollment(s) added for {len(student_list)} student(s).', 'success')
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

# ==================== ENROLLMENT APPROVAL ====================

@app.route('/enrollments')
@login_required
def enrollments():
    """Enrollment approval page for instructors"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get pending (unapproved) students
    cursor.execute('''
        SELECT u.*, GROUP_CONCAT(s.code || ' - ' || s.section) as enrolled_subjects
        FROM users u
        LEFT JOIN enrollments e ON u.id = e.student_id
        LEFT JOIN subjects s ON e.subject_id = s.id
        WHERE u.role = 'student' AND (u.is_approved = 0 OR u.is_approved IS NULL)
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    pending_students = cursor.fetchall()

    # Get approved students
    cursor.execute('''
        SELECT u.*, GROUP_CONCAT(s.code || ' - ' || s.section) as enrolled_subjects
        FROM users u
        LEFT JOIN enrollments e ON u.id = e.student_id
        LEFT JOIN subjects s ON e.subject_id = s.id
        WHERE u.role = 'student' AND u.is_approved = 1
        GROUP BY u.id
        ORDER BY u.full_name
    ''')
    approved_students = cursor.fetchall()

    # Get sections for filtering
    cursor.execute('SELECT DISTINCT section FROM users WHERE role = "student" AND section IS NOT NULL ORDER BY section')
    sections = [row['section'] for row in cursor.fetchall()]

    # Get subjects for filtering
    cursor.execute('SELECT id, code, section FROM subjects ORDER BY code, section')
    subjects = cursor.fetchall()

    # Count pending by section
    cursor.execute('''
        SELECT section, COUNT(*) as count
        FROM users
        WHERE role = 'student' AND (is_approved = 0 OR is_approved IS NULL)
        GROUP BY section
    ''')
    pending_by_section = {row['section']: row['count'] for row in cursor.fetchall()}

    conn.close()

    return render_template('enrollments.html',
                           pending_students=pending_students,
                           approved_students=approved_students,
                           sections=sections,
                           subjects=subjects,
                           pending_by_section=pending_by_section)

def auto_enroll_student_in_matching_subjects(cursor, student_id, section):
    """Helper function to auto-enroll a student in subjects matching their section"""
    if not section:
        return 0

    # Find all subjects that match the student's section
    cursor.execute('SELECT id FROM subjects WHERE section = ?', (section,))
    matching_subjects = cursor.fetchall()

    enrolled_count = 0
    for subject in matching_subjects:
        # Check if already enrolled
        cursor.execute('''
            SELECT id FROM enrollments WHERE student_id = ? AND subject_id = ?
        ''', (student_id, subject['id']))
        if not cursor.fetchone():
            # Enroll the student
            cursor.execute('''
                INSERT INTO enrollments (student_id, subject_id)
                VALUES (?, ?)
            ''', (student_id, subject['id']))
            enrolled_count += 1

    return enrolled_count

@app.route('/enrollments/approve/<int:student_id>', methods=['POST'])
@login_required
def approve_student(student_id):
    """Approve a single student"""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()

    # Get student info including section
    cursor.execute('SELECT full_name, section FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()

    # Approve the student
    cursor.execute('UPDATE users SET is_approved = 1 WHERE id = ? AND role = "student"', (student_id,))

    # Auto-enroll in matching subjects
    enrolled_count = auto_enroll_student_in_matching_subjects(cursor, student_id, student['section'])

    # Create notification for the student
    notification_msg = 'Your enrollment has been approved! You can now access the system.'
    if enrolled_count > 0:
        notification_msg += f' You have been enrolled in {enrolled_count} subject(s).'

    cursor.execute('''
        INSERT INTO notifications (user_id, type, icon, message, link)
        VALUES (?, 'success', 'check-circle', ?, '/student/dashboard')
    ''', (student_id, notification_msg))
    conn.commit()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f'{student["full_name"]} approved!'})

    flash(f'Student {student["full_name"]} approved!', 'success')
    return redirect(url_for('enrollments'))

@app.route('/enrollments/reject/<int:student_id>', methods=['POST'])
@login_required
def reject_student(student_id):
    """Reject and delete a student enrollment"""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()

    # Get student info before deleting
    cursor.execute('SELECT full_name FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    student_name = student['full_name'] if student else 'Student'

    # Delete enrollments first
    cursor.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))
    # Delete the user
    cursor.execute('DELETE FROM users WHERE id = ? AND role = "student"', (student_id,))
    conn.commit()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f'{student_name} rejected and removed!'})

    flash(f'Student {student_name} rejected and removed!', 'success')
    return redirect(url_for('enrollments'))

@app.route('/enrollments/approve-section/<section>', methods=['POST'])
@login_required
def approve_section(section):
    """Approve all pending students in a section"""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()

    # Get pending students in this section
    cursor.execute('''
        SELECT id, full_name, section FROM users
        WHERE role = 'student' AND section = ? AND (is_approved = 0 OR is_approved IS NULL)
    ''', (section,))
    students = cursor.fetchall()

    # Approve all
    cursor.execute('''
        UPDATE users SET is_approved = 1
        WHERE role = 'student' AND section = ? AND (is_approved = 0 OR is_approved IS NULL)
    ''', (section,))
    count = cursor.rowcount

    # Auto-enroll each student and create notifications
    for student in students:
        enrolled_count = auto_enroll_student_in_matching_subjects(cursor, student['id'], student['section'])

        notification_msg = 'Your enrollment has been approved! You can now access the system.'
        if enrolled_count > 0:
            notification_msg += f' You have been enrolled in {enrolled_count} subject(s).'

        cursor.execute('''
            INSERT INTO notifications (user_id, type, icon, message, link)
            VALUES (?, 'success', 'check-circle', ?, '/student/dashboard')
        ''', (student['id'], notification_msg))

    conn.commit()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f'{count} students in {section} approved!'})

    flash(f'{count} students in {section} approved!', 'success')
    return redirect(url_for('enrollments'))

@app.route('/enrollments/approve-all', methods=['POST'])
@login_required
def approve_all_students():
    """Approve all pending students"""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()

    # Get all pending students with their sections
    cursor.execute('''
        SELECT id, full_name, section FROM users
        WHERE role = 'student' AND (is_approved = 0 OR is_approved IS NULL)
    ''')
    students = cursor.fetchall()

    # Approve all
    cursor.execute('''
        UPDATE users SET is_approved = 1
        WHERE role = 'student' AND (is_approved = 0 OR is_approved IS NULL)
    ''')
    count = cursor.rowcount

    # Auto-enroll each student and create notifications
    for student in students:
        enrolled_count = auto_enroll_student_in_matching_subjects(cursor, student['id'], student['section'])

        notification_msg = 'Your enrollment has been approved! You can now access the system.'
        if enrolled_count > 0:
            notification_msg += f' You have been enrolled in {enrolled_count} subject(s).'

        cursor.execute('''
            INSERT INTO notifications (user_id, type, icon, message, link)
            VALUES (?, 'success', 'check-circle', ?, '/student/dashboard')
        ''', (student['id'], notification_msg))

    conn.commit()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f'{count} students approved!'})

    flash(f'{count} students approved!', 'success')
    return redirect(url_for('enrollments'))

@app.route('/enrollments/revoke/<int:student_id>', methods=['POST'])
@login_required
def revoke_approval(student_id):
    """Revoke approval for a student"""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_approved = 0 WHERE id = ? AND role = "student"', (student_id,))
    conn.commit()

    cursor.execute('SELECT full_name FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f'{student["full_name"]} approval revoked!'})

    flash(f'Approval revoked for {student["full_name"]}!', 'success')
    return redirect(url_for('enrollments'))

@app.route('/enrollments/sync-subjects/<int:student_id>', methods=['POST'])
@login_required
def sync_student_subjects(student_id):
    """Sync a student's enrollments with their section's subjects"""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()

    # Get student info
    cursor.execute('SELECT full_name, section FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return jsonify({'error': 'Student not found'}), 404

    # Auto-enroll in matching subjects
    enrolled_count = auto_enroll_student_in_matching_subjects(cursor, student_id, student['section'])
    conn.commit()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if enrolled_count > 0:
            return jsonify({'success': True, 'message': f'{student["full_name"]} enrolled in {enrolled_count} subject(s)!'})
        else:
            return jsonify({'success': True, 'message': f'{student["full_name"]} is already enrolled in all matching subjects.'})

    if enrolled_count > 0:
        flash(f'{student["full_name"]} enrolled in {enrolled_count} subject(s)!', 'success')
    else:
        flash(f'{student["full_name"]} is already enrolled in all matching subjects.', 'info')
    return redirect(url_for('enrollments'))

@app.route('/enrollments/sync-all-subjects', methods=['POST'])
@login_required
def sync_all_student_subjects():
    """Sync all approved students' enrollments with their section's subjects"""
    if current_user.role != 'instructor':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db()
    cursor = conn.cursor()

    # Get all approved students
    cursor.execute('''
        SELECT id, full_name, section FROM users
        WHERE role = 'student' AND is_approved = 1
    ''')
    students = cursor.fetchall()

    total_enrolled = 0
    students_updated = 0
    for student in students:
        enrolled_count = auto_enroll_student_in_matching_subjects(cursor, student['id'], student['section'])
        if enrolled_count > 0:
            total_enrolled += enrolled_count
            students_updated += 1

    conn.commit()
    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f'{students_updated} student(s) enrolled in {total_enrolled} subject(s)!'})

    flash(f'{students_updated} student(s) enrolled in {total_enrolled} subject(s)!', 'success')
    return redirect(url_for('enrollments'))

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

    # Get enrolled students with photos
    cursor.execute('''
        SELECT u.id, u.full_name, u.photo FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.subject_id = ?
        ORDER BY u.full_name
    ''', (id,))
    enrolled_students = cursor.fetchall()
    total_enrolled = len(enrolled_students)

    # Batch queries for per-session performance stats
    session_ids = [s['id'] for s in sessions]
    session_stats = {}

    if session_ids:
        placeholders = ','.join(['?'] * len(session_ids))

        # Query 1: Activity submission stats per session
        cursor.execute(f'''
            SELECT a.session_id,
                   COUNT(DISTINCT a.id) as activity_count,
                   COUNT(DISTINCT sub.id) as submission_count,
                   COUNT(DISTINCT sub.student_id) as students_submitted,
                   AVG(CASE WHEN sub.final_score IS NOT NULL THEN sub.final_score
                        WHEN sub.score IS NOT NULL THEN sub.score END) as avg_score,
                   SUM(CASE WHEN sub.score IS NOT NULL OR sub.final_score IS NOT NULL THEN 1 ELSE 0 END) as graded_count
            FROM activities a
            LEFT JOIN submissions sub ON a.id = sub.activity_id
            WHERE a.session_id IN ({placeholders})
            GROUP BY a.session_id
        ''', session_ids)
        activity_stats = {row['session_id']: dict(row) for row in cursor.fetchall()}

        # Query 2: Quiz stats per session
        cursor.execute(f'''
            SELECT q.session_id,
                   COUNT(DISTINCT q.id) as quiz_count,
                   COUNT(DISTINCT qa.student_id) as students_attempted,
                   AVG(qa.score) as avg_score,
                   MAX(qa.score) as max_score
            FROM quizzes q
            LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id
            WHERE q.session_id IN ({placeholders})
            GROUP BY q.session_id
        ''', session_ids)
        quiz_stats = {row['session_id']: dict(row) for row in cursor.fetchall()}

        # Query 3: Peer review stats per session
        cursor.execute(f'''
            SELECT a.session_id,
                   COUNT(DISTINCT a.id) as peer_review_activities,
                   COUNT(DISTINCT pra.id) as total_assignments,
                   SUM(CASE WHEN pra.is_completed = 1 THEN 1 ELSE 0 END) as completed_assignments
            FROM activities a
            JOIN submissions sub ON a.id = sub.activity_id
            JOIN peer_review_assignments pra ON sub.id = pra.submission_id
            WHERE a.session_id IN ({placeholders}) AND a.enable_peer_review = 1
            GROUP BY a.session_id
        ''', session_ids)
        peer_stats = {row['session_id']: dict(row) for row in cursor.fetchall()}

        # Query 4: Completed students per session (batched)
        cursor.execute(f'''
            SELECT a.session_id, u.id, u.full_name, u.photo
            FROM submissions sub
            JOIN activities a ON sub.activity_id = a.id
            JOIN users u ON sub.student_id = u.id
            WHERE a.session_id IN ({placeholders})
            GROUP BY a.session_id, u.id
            ORDER BY u.full_name
        ''', session_ids)
        completed_map = {}
        for row in cursor.fetchall():
            sid = row['session_id']
            if sid not in completed_map:
                completed_map[sid] = []
            completed_map[sid].append(dict(row))

        # Assemble enriched session_stats
        for s in sessions:
            sid = s['id']
            act = activity_stats.get(sid, {})
            quiz = quiz_stats.get(sid, {})
            pr = peer_stats.get(sid, {})

            session_stats[sid] = {
                'completed_students': completed_map.get(sid, []),
                'completed_count': len(completed_map.get(sid, [])),
                'activity_count': act.get('activity_count', 0),
                'submission_count': act.get('submission_count', 0),
                'students_submitted': act.get('students_submitted', 0),
                'avg_score': round(act.get('avg_score') or 0, 1),
                'graded_count': act.get('graded_count', 0),
                'quiz_count': quiz.get('quiz_count', 0),
                'quiz_students_attempted': quiz.get('students_attempted', 0),
                'quiz_avg_score': round(quiz.get('avg_score') or 0, 1),
                'quiz_max_score': round(quiz.get('max_score') or 0, 1),
                'peer_review_activities': pr.get('peer_review_activities', 0),
                'peer_review_total': pr.get('total_assignments', 0),
                'peer_review_completed': pr.get('completed_assignments', 0),
            }

    conn.close()
    return render_template('sessions.html', subject=subject, sessions=sessions,
                           enrolled_students=enrolled_students, total_enrolled=total_enrolled,
                           session_stats=session_stats)

# ==================== ACTIVITIES ====================

@app.route('/subject/<int:subject_id>/all-activities')
@login_required
def all_activities(subject_id):
    """Show ALL 16 sessions' activities on ONE page"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()

    # Get enrolled count
    cursor.execute('SELECT COUNT(*) FROM enrollments WHERE subject_id = ?', (subject_id,))
    total_enrolled = cursor.fetchone()[0]

    # Get all sessions with their activities
    cursor.execute('SELECT * FROM sessions WHERE subject_id = ? ORDER BY session_number', (subject_id,))
    sessions = cursor.fetchall()

    # Get submission stats per activity in one batch
    session_ids = [s['id'] for s in sessions]
    activity_stats = {}
    if session_ids:
        placeholders = ','.join(['?'] * len(session_ids))
        cursor.execute(f'''
            SELECT a.id as activity_id,
                   COUNT(DISTINCT sub.student_id) as submitted_count,
                   AVG(CASE WHEN sub.score IS NOT NULL THEN sub.score
                        WHEN sub.final_score IS NOT NULL THEN sub.final_score END) as avg_score,
                   SUM(CASE WHEN sub.score IS NOT NULL OR sub.final_score IS NOT NULL THEN 1 ELSE 0 END) as graded_count
            FROM activities a
            LEFT JOIN submissions sub ON a.id = sub.activity_id
            WHERE a.session_id IN ({placeholders})
            GROUP BY a.id
        ''', session_ids)
        for row in cursor.fetchall():
            activity_stats[row['activity_id']] = dict(row)

    sessions_with_activities = []
    for session in sessions:
        cursor.execute('SELECT * FROM activities WHERE session_id = ? ORDER BY activity_number', (session['id'],))
        activities = cursor.fetchall()
        sessions_with_activities.append({
            'session': session,
            'activities': activities
        })

    conn.close()
    return render_template('all_activities.html', subject=subject, sessions_data=sessions_with_activities,
                           total_enrolled=total_enrolled, activity_stats=activity_stats)

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

    conn = get_db()
    cursor = conn.cursor()

    # Check if activity exists and is active
    cursor.execute('''
        SELECT a.*, s.subject_id FROM activities a
        JOIN sessions s ON a.session_id = s.id
        WHERE a.id = ?
    ''', (activity_id,))
    activity = cursor.fetchone()

    if not activity:
        flash('Activity not found.', 'error')
        conn.close()
        return redirect(url_for('student_dashboard'))

    # Check if activity is active (not deactivated)
    keys = activity.keys()
    is_active = activity['is_active'] if 'is_active' in keys else 1
    if not is_active:
        flash('This activity is no longer accepting submissions.', 'error')
        conn.close()
        return redirect(url_for('student_dashboard'))

    content = request.form.get('content', '')

    # Calculate late submission penalty
    is_late = 0
    late_days = 0
    late_penalty = 0

    due_date = activity['due_date'] if 'due_date' in keys else None
    due_time = activity['due_time'] if 'due_time' in keys else '23:59'
    late_penalty_per_day = activity['late_penalty_per_day'] if 'late_penalty_per_day' in keys else 1

    if due_date:
        # Combine due date and time
        due_datetime_str = f"{due_date} {due_time or '23:59'}"
        try:
            due_datetime = datetime.strptime(due_datetime_str, '%Y-%m-%d %H:%M')
            now = datetime.now()

            if now > due_datetime:
                is_late = 1
                # Calculate days late (every 24 hours = 1 day)
                time_diff = now - due_datetime
                late_days = time_diff.days + (1 if time_diff.seconds > 0 else 0)
                late_penalty = late_days * late_penalty_per_day
        except ValueError:
            pass  # If date parsing fails, don't apply penalty

    # Handle multiple file uploads
    uploaded_files = []
    files = request.files.getlist('submission_files')

    # Also check for single file upload (backwards compatibility)
    if not files or (len(files) == 1 and not files[0].filename):
        if 'submission_file' in request.files:
            single_file = request.files['submission_file']
            if single_file and single_file.filename:
                files = [single_file]

    # Create activity-specific folder
    activity_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'activity_submissions', f"activity_{activity_id}")
    os.makedirs(activity_folder, exist_ok=True)

    first_file_path = None
    for file in files:
        if file and file.filename:
            safe_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            filename = f"student_{current_user.id}_{timestamp}_{safe_filename}"
            file.save(os.path.join(activity_folder, filename))
            file_path = f"activity_{activity_id}/{filename}"

            if first_file_path is None:
                first_file_path = file_path

            uploaded_files.append({
                'file_path': file_path,
                'file_name': file.filename
            })

    # Check if already submitted
    cursor.execute('SELECT id FROM submissions WHERE activity_id = ? AND student_id = ?',
                   (activity_id, current_user.id))
    existing = cursor.fetchone()

    if existing:
        submission_id = existing['id']
        # Update existing submission with late info
        cursor.execute('''
            UPDATE submissions SET content = ?, file_path = ?, submitted_at = CURRENT_TIMESTAMP,
            is_late = ?, late_days = ?, late_penalty = ?
            WHERE activity_id = ? AND student_id = ?
        ''', (content, first_file_path, is_late, late_days, late_penalty, activity_id, current_user.id))

        # Delete old files from submission_files table
        cursor.execute('DELETE FROM submission_files WHERE submission_id = ?', (submission_id,))
    else:
        cursor.execute('''
            INSERT INTO submissions (activity_id, student_id, content, file_path, is_late, late_days, late_penalty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (activity_id, current_user.id, content, first_file_path, is_late, late_days, late_penalty))
        submission_id = cursor.lastrowid

    # Insert all uploaded files into submission_files table
    for file_info in uploaded_files:
        cursor.execute('''
            INSERT INTO submission_files (submission_id, file_path, file_name)
            VALUES (?, ?, ?)
        ''', (submission_id, file_info['file_path'], file_info['file_name']))

    # Note: step_activity is NOT marked here on submission.
    # It will be marked when the instructor grades the submission (grade_activity route).

    conn.commit()
    conn.close()

    if is_late:
        flash(f'Activity submitted successfully! Note: Your submission is {late_days} day(s) late with a penalty of {late_penalty} point(s).', 'warning')
    else:
        flash('Activity submitted successfully!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/activity/<int:activity_id>/grade', methods=['POST'])
@login_required
def grade_activity(activity_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    submission_id = request.form['submission_id']
    instructor_score = float(request.form['score'])
    feedback = request.form['feedback']

    conn = get_db()
    cursor = conn.cursor()

    # Get the submission and activity info
    cursor.execute('''
        SELECT s.*, a.points, a.enable_peer_review, a.session_id as activity_session_id
        FROM submissions s
        JOIN activities a ON s.activity_id = a.id
        WHERE s.id = ?
    ''', (submission_id,))
    submission = cursor.fetchone()

    if not submission:
        flash('Submission not found', 'error')
        conn.close()
        return redirect(url_for('view_submissions', activity_id=activity_id))

    student_id = submission['student_id']
    max_points = submission['points']
    enable_peer_review = submission['enable_peer_review'] if 'enable_peer_review' in submission.keys() else 0

    # Calculate final score based on peer review enabled or not
    if enable_peer_review:
        # Get peer review score (25% weight) - now stored as percentage (60-100)
        peer_review_score = submission['peer_review_score'] if submission['peer_review_score'] else 60

        # Calculate participation score (25% weight) - returns percentage (0-100)
        # Based on: completed reviews + quality of reviews
        participation_score = calculate_participation_score(cursor, student_id, activity_id, max_points)

        # Calculate weighted final score
        # 25% peer review + 25% participation + 50% instructor
        # peer_review_score is already 60-100 (percentage)
        # participation_score is already 0-100 (percentage)
        # instructor_score needs to be converted to percentage
        peer_component = (peer_review_score / 100) * 25
        participation_component = (participation_score / 100) * 25
        instructor_component = (instructor_score / max_points) * 50 if max_points > 0 else 0

        # Final score as percentage, then converted to points
        final_percentage = peer_component + participation_component + instructor_component
        final_score = (final_percentage / 100) * max_points

        # Apply late penalty if any
        late_penalty = submission['late_penalty'] if submission['late_penalty'] else 0
        final_score = max(0, final_score - late_penalty)

        cursor.execute('''
            UPDATE submissions
            SET score = ?, instructor_score = ?, participation_score = ?, final_score = ?, feedback = ?
            WHERE id = ?
        ''', (instructor_score, instructor_score, participation_score, final_score, feedback, submission_id))
    else:
        # No peer review - instructor score is the final score
        late_penalty = submission['late_penalty'] if submission['late_penalty'] else 0
        final_score = max(0, instructor_score - late_penalty)

        cursor.execute('''
            UPDATE submissions
            SET score = ?, instructor_score = ?, final_score = ?, feedback = ?
            WHERE id = ?
        ''', (instructor_score, instructor_score, final_score, feedback, submission_id))

    # Check if ALL visible activities for this session are graded for this student
    act_session_id = submission['activity_session_id']
    cursor.execute('''
        SELECT COUNT(*) as total FROM activities WHERE session_id = ? AND is_visible = 1
    ''', (act_session_id,))
    total_activities = cursor.fetchone()['total']

    cursor.execute('''
        SELECT COUNT(DISTINCT a.id) as graded
        FROM activities a
        JOIN submissions s ON s.activity_id = a.id
        WHERE a.session_id = ? AND s.student_id = ? AND s.final_score IS NOT NULL AND a.is_visible = 1
    ''', (act_session_id, student_id))
    graded_activities = cursor.fetchone()['graded']

    if graded_activities >= total_activities:
        cursor.execute('''
            INSERT INTO session_progress (session_id, student_id, step_activity)
            VALUES (?, ?, 1)
            ON CONFLICT(session_id, student_id) DO UPDATE SET step_activity = 1
        ''', (act_session_id, student_id))
        check_and_mark_session_complete(cursor, act_session_id, student_id)

    conn.commit()
    conn.close()
    flash('Grade saved successfully!', 'success')

    # Support redirecting back to peer review status page
    redirect_to = request.form.get('redirect_to', '')
    if redirect_to == 'peer_review_status':
        return redirect(url_for('peer_review_status', activity_id=activity_id))
    return redirect(url_for('view_submissions', activity_id=activity_id))


def calculate_participation_score(cursor, student_id, activity_id, max_points):
    """
    Calculate participation score for a student as a PERCENTAGE (0-100) based on
    instructor approval of their peer reviews.

    - approved reviews / total assignments * 100
    - If no assignments exist -> 100% (not required to review)
    - Completed but not yet approved -> counts as 0 until instructor approves

    Returns: percentage score (0-100)
    """
    # Get all peer review assignments for this student for this activity
    cursor.execute('''
        SELECT pra.*, s.activity_id
        FROM peer_review_assignments pra
        JOIN submissions s ON pra.submission_id = s.id
        WHERE pra.reviewer_id = ? AND s.activity_id = ?
    ''', (student_id, activity_id))
    assignments = cursor.fetchall()

    if not assignments:
        # No assignments = full participation score (they weren't required to review)
        return 100  # Return 100%

    total_assignments = len(assignments)
    approved_count = sum(1 for a in assignments
                         if 'approval_status' in a.keys() and a['approval_status'] == 'approved')

    # Participation = percentage of approved reviews
    return (approved_count / total_assignments) * 100 if total_assignments > 0 else 0

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
    submissions_raw = cursor.fetchall()

    # Fetch all files for each submission
    submissions = []
    for sub in submissions_raw:
        sub_dict = dict(sub)
        cursor.execute('''
            SELECT * FROM submission_files WHERE submission_id = ?
        ''', (sub['id'],))
        sub_dict['files'] = cursor.fetchall()
        submissions.append(sub_dict)

    conn.close()
    return render_template('submissions.html', activity=activity, submissions=submissions)

# ==================== PEER REVIEW SYSTEM ====================

@app.route('/instructor/peer-reviews')
@login_required
def instructor_peer_reviews():
    """Instructor overview of all peer reviews across activities"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get all activities with peer review enabled
    cursor.execute('''
        SELECT a.*, ses.title as session_title, sub.name as subject_name, sub.section,
               (SELECT COUNT(*) FROM submissions WHERE activity_id = a.id) as submission_count,
               (SELECT COUNT(*) FROM peer_review_assignments pra
                JOIN submissions s ON pra.submission_id = s.id
                WHERE s.activity_id = a.id) as assignment_count,
               (SELECT COUNT(*) FROM peer_review_assignments pra
                JOIN submissions s ON pra.submission_id = s.id
                WHERE s.activity_id = a.id AND pra.is_completed = 1) as completed_count
        FROM activities a
        JOIN sessions ses ON a.session_id = ses.id
        JOIN subjects sub ON ses.subject_id = sub.id
        WHERE a.enable_peer_review = 1
        ORDER BY a.id DESC
    ''')
    activities = cursor.fetchall()

    conn.close()
    return render_template('instructor_peer_reviews.html', activities=activities)


@app.route('/activity/<int:activity_id>/peer-review/settings', methods=['GET', 'POST'])
@login_required
def peer_review_settings(activity_id):
    """Instructor page to configure peer review settings and criteria"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()

    if not activity:
        flash('Activity not found', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        enable_peer_review = 1 if request.form.get('enable_peer_review') else 0
        peer_reviewers_count = int(request.form.get('peer_reviewers_count', 1))

        cursor.execute('''
            UPDATE activities SET enable_peer_review = ?, peer_reviewers_count = ?
            WHERE id = ?
        ''', (enable_peer_review, peer_reviewers_count, activity_id))
        conn.commit()
        flash('Peer review settings updated!', 'success')

    # Get existing criteria
    cursor.execute('''
        SELECT * FROM peer_review_criteria WHERE activity_id = ? ORDER BY order_num
    ''', (activity_id,))
    criteria = cursor.fetchall()

    # Get activity with updated settings
    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()

    conn.close()
    return render_template('peer_review_settings.html', activity=activity, criteria=criteria)


@app.route('/activity/<int:activity_id>/peer-review/criteria', methods=['POST'])
@login_required
def add_peer_review_criteria(activity_id):
    """Add a new peer review criterion"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    criterion = request.form.get('criterion', '').strip()
    points = int(request.form.get('points', 1))

    if not criterion:
        flash('Criterion text is required', 'error')
        return redirect(url_for('peer_review_settings', activity_id=activity_id))

    conn = get_db()
    cursor = conn.cursor()

    # Get next order number
    cursor.execute('SELECT MAX(order_num) as max_order FROM peer_review_criteria WHERE activity_id = ?', (activity_id,))
    result = cursor.fetchone()
    next_order = (result['max_order'] or 0) + 1

    cursor.execute('''
        INSERT INTO peer_review_criteria (activity_id, criterion, points, order_num)
        VALUES (?, ?, ?, ?)
    ''', (activity_id, criterion, points, next_order))
    conn.commit()
    conn.close()

    flash('Criterion added successfully!', 'success')
    return redirect(url_for('peer_review_settings', activity_id=activity_id))


@app.route('/activity/<int:activity_id>/peer-review/criteria/<int:criterion_id>/delete', methods=['POST'])
@login_required
def delete_peer_review_criteria(activity_id, criterion_id):
    """Delete a peer review criterion"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM peer_review_criteria WHERE id = ? AND activity_id = ?', (criterion_id, activity_id))
    conn.commit()
    conn.close()

    flash('Criterion deleted', 'success')
    return redirect(url_for('peer_review_settings', activity_id=activity_id))


@app.route('/activity/<int:activity_id>/peer-review/assign', methods=['POST'])
@login_required
def assign_peer_reviewers(activity_id):
    """Randomly assign peer reviewers to submissions - smart assignment that preserves completed reviews"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    import random

    conn = get_db()
    cursor = conn.cursor()

    # Get activity settings
    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()

    if not activity:
        flash('Activity not found', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    keys = activity.keys()
    peer_reviewers_count = activity['peer_reviewers_count'] if 'peer_reviewers_count' in keys else 1

    # Auto-generate topic-specific review criteria if none exist
    cursor.execute('SELECT COUNT(*) FROM peer_review_criteria WHERE activity_id = ?', (activity_id,))
    if cursor.fetchone()[0] == 0:
        import re
        # Get session title for topic context
        cursor.execute('''
            SELECT s.title as session_title, a.title as activity_title, a.instructions
            FROM activities a JOIN sessions s ON a.session_id = s.id WHERE a.id = ?
        ''', (activity_id,))
        info = cursor.fetchone()
        session_topic = info['session_title'] if info else 'the lesson'
        act_title = info['activity_title'] if info else 'the activity'
        instructions_html = info['instructions'] if info and info['instructions'] else ''

        # Extract key tasks/objectives from instructions HTML
        task_items = []
        # Extract <li> items
        li_matches = re.findall(r'<li[^>]*>(.*?)</li>', instructions_html, re.DOTALL)
        for item in li_matches:
            clean = re.sub(r'<[^>]+>', '', item).strip()
            if clean and len(clean) > 10 and len(clean) < 150:
                task_items.append(clean)
        # Extract <td> descriptions from task tables (skip header and number/points columns)
        td_matches = re.findall(r'<td[^>]*>(.*?)</td>', instructions_html, re.DOTALL)
        for item in td_matches:
            clean = re.sub(r'<[^>]+>', '', item).strip()
            if clean and len(clean) > 15 and not clean.isdigit():
                task_items.append(clean)

        # Build specific criteria from extracted content
        criteria = []
        order = 1
        # Add topic-level question
        criteria.append((f'Did the student demonstrate understanding of "{session_topic}"?', 1, order))
        order += 1

        # Add task-specific questions (up to 4)
        seen = set()
        for task in task_items[:6]:
            if task.lower() not in seen and len(criteria) < 6:
                seen.add(task.lower())
                criteria.append((f'Did the student mention or show: "{task}"?', 1, order))
                order += 1

        # Fill remaining with general criteria if less than 4 total
        if len(criteria) < 3:
            criteria.append((f'Did the student follow the instructions for "{act_title}" correctly?', 1, order))
            order += 1
        if len(criteria) < 4:
            criteria.append(('Is the submission complete with all required deliverables?', 1, order))
            order += 1
        if len(criteria) < 5:
            criteria.append(('Would you consider this submission satisfactory overall?', 1, order))
            order += 1

        for criterion, points, order_num in criteria:
            cursor.execute('''
                INSERT INTO peer_review_criteria (activity_id, criterion, points, order_num)
                VALUES (?, ?, ?, ?)
            ''', (activity_id, criterion, points, order_num))
        conn.commit()

    # Get all submissions for this activity
    cursor.execute('''
        SELECT s.id, s.student_id FROM submissions s
        WHERE s.activity_id = ?
    ''', (activity_id,))
    submissions = cursor.fetchall()

    if len(submissions) < 2:
        flash('Need at least 2 submissions to assign peer reviews', 'error')
        conn.close()
        return redirect(url_for('peer_review_settings', activity_id=activity_id))

    # Get existing assignments (both completed and pending) to avoid duplicates
    submission_ids = [s['id'] for s in submissions]
    placeholders = ','.join(['?' for _ in submission_ids])
    cursor.execute(f'''
        SELECT submission_id, reviewer_id, is_completed FROM peer_review_assignments
        WHERE submission_id IN ({placeholders})
    ''', submission_ids)
    existing_assignments = cursor.fetchall()

    # Build a set of existing (submission_id, reviewer_id) pairs
    existing_pairs = set((a['submission_id'], a['reviewer_id']) for a in existing_assignments)

    # Track completed assignments - these should not be removed
    completed_pairs = set((a['submission_id'], a['reviewer_id']) for a in existing_assignments if a['is_completed'])

    # Only delete PENDING (not completed) assignments for fresh reassignment
    for sub_id in submission_ids:
        cursor.execute('''
            DELETE FROM peer_review_assignments
            WHERE submission_id = ? AND is_completed = 0
        ''', (sub_id,))

    # Track how many reviews each student has already completed for this activity
    cursor.execute(f'''
        SELECT reviewer_id, COUNT(*) as review_count
        FROM peer_review_assignments
        WHERE submission_id IN ({placeholders}) AND is_completed = 1
        GROUP BY reviewer_id
    ''', submission_ids)
    completed_counts = {row['reviewer_id']: row['review_count'] for row in cursor.fetchall()}

    # Create assignment pool - each student should review X other submissions
    assignments_made = 0

    for submission in submissions:
        submitter_id = submission['student_id']
        submission_id = submission['id']

        # Check how many reviewers this submission already has (completed)
        existing_reviewers_for_sub = [p[1] for p in completed_pairs if p[0] == submission_id]
        needed_reviewers = max(0, peer_reviewers_count - len(existing_reviewers_for_sub))

        if needed_reviewers <= 0:
            continue  # This submission already has enough reviews

        # Get potential reviewers (all students who submitted, except the submitter)
        # and who haven't already reviewed this submission
        potential_reviewers = [
            s['student_id'] for s in submissions
            if s['student_id'] != submitter_id
            and (submission_id, s['student_id']) not in completed_pairs
        ]

        # Sort by least reviews completed (so workload is distributed evenly)
        potential_reviewers.sort(key=lambda r: completed_counts.get(r, 0))

        # Add some randomness within similar workload groups
        random.shuffle(potential_reviewers)

        selected_reviewers = potential_reviewers[:min(needed_reviewers, len(potential_reviewers))]

        for reviewer_id in selected_reviewers:
            # Double check not already assigned
            if (submission_id, reviewer_id) not in existing_pairs:
                try:
                    cursor.execute('''
                        INSERT INTO peer_review_assignments (submission_id, reviewer_id)
                        VALUES (?, ?)
                    ''', (submission_id, reviewer_id))
                    assignments_made += 1
                    existing_pairs.add((submission_id, reviewer_id))
                except:
                    pass  # Skip duplicates

    conn.commit()
    conn.close()

    flash(f'Peer review assignments updated! {assignments_made} new reviews assigned. Completed reviews preserved.', 'success')
    return redirect(url_for('peer_review_settings', activity_id=activity_id))


@app.route('/student/peer-reviews')
@login_required
def student_peer_reviews():
    """Student page to see pending and completed peer reviews"""
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get pending peer reviews (assigned to this student but not completed)
    cursor.execute('''
        SELECT pra.*, s.content, s.file_path, a.title as activity_title, a.id as activity_id,
               ses.title as session_title, sub.name as subject_name
        FROM peer_review_assignments pra
        JOIN submissions s ON pra.submission_id = s.id
        JOIN activities a ON s.activity_id = a.id
        JOIN sessions ses ON a.session_id = ses.id
        JOIN subjects sub ON ses.subject_id = sub.id
        WHERE pra.reviewer_id = ? AND pra.is_completed = 0
        ORDER BY pra.assigned_at DESC
    ''', (current_user.id,))
    pending_reviews = cursor.fetchall()

    # Get completed peer reviews with score given
    cursor.execute('''
        SELECT pra.*, s.content, a.title as activity_title, a.id as activity_id,
               ses.title as session_title, sub.name as subject_name,
               (SELECT AVG(points_awarded) FROM peer_review_responses WHERE assignment_id = pra.id) as review_score
        FROM peer_review_assignments pra
        JOIN submissions s ON pra.submission_id = s.id
        JOIN activities a ON s.activity_id = a.id
        JOIN sessions ses ON a.session_id = ses.id
        JOIN subjects sub ON ses.subject_id = sub.id
        WHERE pra.reviewer_id = ? AND pra.is_completed = 1
        ORDER BY pra.completed_at DESC
    ''', (current_user.id,))
    completed_reviews = cursor.fetchall()

    # Get the student's own submissions that have peer review scores
    cursor.execute('''
        SELECT s.peer_review_score, a.title as activity_title,
               ses.title as session_title, sub.name as subject_name,
               (SELECT COUNT(*) FROM peer_review_assignments WHERE submission_id = s.id AND is_completed = 1) as reviews_received
        FROM submissions s
        JOIN activities a ON s.activity_id = a.id
        JOIN sessions ses ON a.session_id = ses.id
        JOIN subjects sub ON ses.subject_id = sub.id
        WHERE s.student_id = ? AND a.enable_peer_review = 1 AND s.peer_review_score IS NOT NULL
        ORDER BY s.submitted_at DESC
    ''', (current_user.id,))
    my_scores = cursor.fetchall()

    conn.close()
    return render_template('student_peer_reviews.html',
                           pending_reviews=pending_reviews,
                           completed_reviews=completed_reviews,
                           my_scores=my_scores)


@app.route('/peer-review/<int:assignment_id>')
@login_required
def do_peer_review(assignment_id):
    """Page for student to complete a peer review"""
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get the assignment and verify it belongs to the current user
    cursor.execute('''
        SELECT pra.*, s.content, s.file_path, s.activity_id,
               a.title as activity_title, a.instructions
        FROM peer_review_assignments pra
        JOIN submissions s ON pra.submission_id = s.id
        JOIN activities a ON s.activity_id = a.id
        WHERE pra.id = ? AND pra.reviewer_id = ?
    ''', (assignment_id, current_user.id))
    assignment = cursor.fetchone()

    if not assignment:
        flash('Peer review assignment not found', 'error')
        conn.close()
        return redirect(url_for('student_peer_reviews'))

    # Get the submission files
    cursor.execute('''
        SELECT * FROM submission_files WHERE submission_id = ?
    ''', (assignment['submission_id'],))
    files = cursor.fetchall()

    # Get review criteria for this activity
    cursor.execute('''
        SELECT * FROM peer_review_criteria WHERE activity_id = ? ORDER BY order_num
    ''', (assignment['activity_id'],))
    criteria = cursor.fetchall()

    conn.close()
    return render_template('do_peer_review.html',
                           assignment=assignment,
                           files=files,
                           criteria=criteria)


@app.route('/peer-review/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_peer_review(assignment_id):
    """Submit peer review responses"""
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Verify assignment belongs to current user
    cursor.execute('''
        SELECT pra.*, s.activity_id FROM peer_review_assignments pra
        JOIN submissions s ON pra.submission_id = s.id
        WHERE pra.id = ? AND pra.reviewer_id = ?
    ''', (assignment_id, current_user.id))
    assignment = cursor.fetchone()

    if not assignment:
        flash('Peer review assignment not found', 'error')
        conn.close()
        return redirect(url_for('student_peer_reviews'))

    # Get all criteria for this activity
    cursor.execute('''
        SELECT * FROM peer_review_criteria WHERE activity_id = ?
    ''', (assignment['activity_id'],))
    criteria = cursor.fetchall()

    # New scoring system:
    # Yes = 100, Somehow = 85, No = 70, No answer = 60
    SCORE_YES = 100
    SCORE_SOMEHOW = 85
    SCORE_NO = 70
    SCORE_NO_ANSWER = 60

    total_score = 0
    criteria_count = len(criteria)

    # Process each criterion response
    for criterion in criteria:
        criterion_id = criterion['id']
        response = request.form.get(f'criterion_{criterion_id}', '')

        # Calculate score based on response
        if response == 'yes':
            points_awarded = SCORE_YES
        elif response == 'somehow':
            points_awarded = SCORE_SOMEHOW
        elif response == 'no':
            points_awarded = SCORE_NO
        else:
            points_awarded = SCORE_NO_ANSWER
            response = 'no_answer'

        total_score += points_awarded

        # Save the response
        cursor.execute('''
            INSERT INTO peer_review_responses (assignment_id, criterion_id, response, points_awarded)
            VALUES (?, ?, ?, ?)
        ''', (assignment_id, criterion_id, response, points_awarded))

    # Calculate average score for this review (percentage out of 100)
    avg_review_score = total_score / criteria_count if criteria_count > 0 else SCORE_NO_ANSWER

    # Mark assignment as completed
    cursor.execute('''
        UPDATE peer_review_assignments SET is_completed = 1, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (assignment_id,))

    # Update the submission's peer review score (average of all reviewers)
    submission_id = assignment['submission_id']

    # Calculate average peer review score across all completed reviews for this submission
    cursor.execute('''
        SELECT AVG(
            (SELECT AVG(points_awarded) FROM peer_review_responses WHERE assignment_id = pra.id)
        ) as avg_score
        FROM peer_review_assignments pra
        WHERE pra.submission_id = ? AND pra.is_completed = 1
    ''', (submission_id,))
    result = cursor.fetchone()
    avg_peer_score = result['avg_score'] if result and result['avg_score'] else avg_review_score

    cursor.execute('''
        UPDATE submissions SET peer_review_score = ? WHERE id = ?
    ''', (avg_peer_score, submission_id))

    conn.commit()
    conn.close()

    flash(f'Peer review submitted! Average score awarded: {avg_review_score:.1f}/100', 'success')
    return redirect(url_for('student_peer_reviews'))


@app.route('/activity/<int:activity_id>/peer-review/status')
@login_required
def peer_review_status(activity_id):
    """Instructor view of peer review status, approve/reject reviews, and grade submissions"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()

    if not activity:
        flash('Activity not found', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    max_points = activity['points'] if activity['points'] else 100

    # Get all submissions with peer review stats
    cursor.execute('''
        SELECT s.*, u.full_name, u.student_id as sid, u.photo,
               (SELECT COUNT(*) FROM peer_review_assignments WHERE submission_id = s.id) as total_reviewers,
               (SELECT COUNT(*) FROM peer_review_assignments WHERE submission_id = s.id AND is_completed = 1) as completed_reviews,
               (SELECT COUNT(*) FROM peer_review_assignments WHERE submission_id = s.id AND approval_status = 'approved') as approved_reviews,
               (SELECT COUNT(*) FROM peer_review_assignments WHERE submission_id = s.id AND approval_status = 'rejected') as rejected_reviews
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        WHERE s.activity_id = ?
        ORDER BY u.full_name
    ''', (activity_id,))
    submissions_raw = cursor.fetchall()

    # Enrich each submission with reviews, files, and reviewer participation info
    submissions = []
    for sub in submissions_raw:
        sub_dict = dict(sub)

        # Get submission files
        cursor.execute('SELECT * FROM submission_files WHERE submission_id = ?', (sub['id'],))
        sub_dict['files'] = cursor.fetchall()

        # Get peer reviews for this submission
        cursor.execute('''
            SELECT pra.*, u.full_name as reviewer_name, u.student_id as reviewer_sid,
                   (SELECT AVG(points_awarded) FROM peer_review_responses WHERE assignment_id = pra.id) as review_avg
            FROM peer_review_assignments pra
            JOIN users u ON pra.reviewer_id = u.id
            WHERE pra.submission_id = ?
            ORDER BY pra.is_completed DESC, pra.assigned_at
        ''', (sub['id'],))
        reviews = cursor.fetchall()
        sub_dict['reviews'] = []
        for rev in reviews:
            rev_dict = dict(rev)
            if rev['is_completed']:
                cursor.execute('''
                    SELECT prr.*, COALESCE(prc.criterion, 'Review criterion') as criterion
                    FROM peer_review_responses prr
                    LEFT JOIN peer_review_criteria prc ON prr.criterion_id = prc.id
                    WHERE prr.assignment_id = ?
                    ORDER BY prr.id
                ''', (rev['id'],))
                rev_dict['responses'] = cursor.fetchall()
            else:
                rev_dict['responses'] = []
            sub_dict['reviews'].append(rev_dict)

        submissions.append(sub_dict)

    # Summary stats
    total_subs = len(submissions)
    graded_count = sum(1 for s in submissions if s.get('instructor_score') is not None)
    all_reviewed = sum(1 for s in submissions if s['completed_reviews'] == s['total_reviewers'] and s['total_reviewers'] > 0)

    conn.close()
    return render_template('peer_review_status.html',
                           activity=activity, submissions=submissions,
                           max_points=max_points,
                           total_subs=total_subs, graded_count=graded_count,
                           all_reviewed=all_reviewed)


@app.route('/activity/<int:activity_id>/peer-review/reviews')
@login_required
def view_peer_reviews(activity_id):
    """Instructor page to view all peer reviews and rate their quality"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()

    if not activity:
        flash('Activity not found', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    # Get all completed peer review assignments with details
    cursor.execute('''
        SELECT pra.*,
               reviewer.full_name as reviewer_name, reviewer.student_id as reviewer_sid,
               submitter.full_name as submitter_name, submitter.student_id as submitter_sid,
               s.content as submission_content, s.file_path as submission_file_path,
               s.id as sub_id
        FROM peer_review_assignments pra
        JOIN submissions s ON pra.submission_id = s.id
        JOIN users reviewer ON pra.reviewer_id = reviewer.id
        JOIN users submitter ON s.student_id = submitter.id
        WHERE s.activity_id = ? AND pra.is_completed = 1
        ORDER BY pra.completed_at DESC
    ''', (activity_id,))
    reviews = cursor.fetchall()

    # Get criteria for this activity
    cursor.execute('SELECT * FROM peer_review_criteria WHERE activity_id = ? ORDER BY order_num', (activity_id,))
    criteria = cursor.fetchall()

    # Get responses and files for each review
    reviews_with_responses = []
    for review in reviews:
        review_dict = dict(review)
        cursor.execute('''
            SELECT prr.*, COALESCE(prc.criterion, 'Review criterion') as criterion
            FROM peer_review_responses prr
            LEFT JOIN peer_review_criteria prc ON prr.criterion_id = prc.id
            WHERE prr.assignment_id = ?
            ORDER BY prr.id
        ''', (review['id'],))
        review_dict['responses'] = cursor.fetchall()

        # Get submission files
        cursor.execute('SELECT * FROM submission_files WHERE submission_id = ?', (review['sub_id'],))
        review_dict['files'] = cursor.fetchall()

        # Calculate average score for this review from direct query
        cursor.execute('SELECT AVG(points_awarded) as avg FROM peer_review_responses WHERE assignment_id = ?',
                       (review['id'],))
        avg_row = cursor.fetchone()
        review_dict['avg_score'] = round(avg_row['avg'], 1) if avg_row and avg_row['avg'] else None

        reviews_with_responses.append(review_dict)

    conn.close()
    return render_template('view_peer_reviews.html',
                           activity=activity,
                           reviews=reviews_with_responses,
                           criteria=criteria)


@app.route('/peer-review/<int:assignment_id>/approve', methods=['POST'])
@login_required
def approve_reject_peer_review(assignment_id):
    """Instructor approves or rejects a peer review - approved = 25% participation grade"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    action = request.form.get('action', '')  # 'approve' or 'reject'
    instructor_feedback = request.form.get('instructor_feedback', '')

    if action not in ('approve', 'reject'):
        flash('Invalid action', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get the assignment details including reviewer and activity info
    cursor.execute('''
        SELECT pra.*, s.activity_id, s.student_id as submitter_id,
               a.points as max_points, a.enable_peer_review
        FROM peer_review_assignments pra
        JOIN submissions s ON pra.submission_id = s.id
        JOIN activities a ON s.activity_id = a.id
        WHERE pra.id = ?
    ''', (assignment_id,))
    assignment = cursor.fetchone()

    if not assignment:
        flash('Review not found', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    activity_id = assignment['activity_id']
    reviewer_id = assignment['reviewer_id']
    max_points = assignment['max_points'] or 100

    # Update the assignment with approval status
    quality_score = 100 if action == 'approve' else 0
    cursor.execute('''
        UPDATE peer_review_assignments
        SET approval_status = ?, review_quality_score = ?, instructor_feedback = ?
        WHERE id = ?
    ''', ('approved' if action == 'approve' else 'rejected', quality_score, instructor_feedback, assignment_id))

    # Recalculate reviewer's participation score for this activity
    participation_score = calculate_participation_score(cursor, reviewer_id, activity_id, max_points)

    # Find and update the reviewer's own submission for this activity
    cursor.execute('''
        SELECT s.*, a.points as max_points
        FROM submissions s
        JOIN activities a ON s.activity_id = a.id
        WHERE s.student_id = ? AND s.activity_id = ?
    ''', (reviewer_id, activity_id))
    reviewer_submission = cursor.fetchone()

    if reviewer_submission:
        # Update participation_score
        cursor.execute('''
            UPDATE submissions SET participation_score = ? WHERE id = ?
        ''', (participation_score, reviewer_submission['id']))

        # If instructor has already graded this submission, recalculate final_score
        if reviewer_submission['instructor_score'] is not None:
            instructor_score = reviewer_submission['instructor_score']
            peer_review_score = reviewer_submission['peer_review_score'] or 60
            sub_max = reviewer_submission['max_points'] or 100

            peer_component = (peer_review_score / 100) * 25
            participation_component = (participation_score / 100) * 25
            instructor_component = (instructor_score / sub_max) * 50 if sub_max > 0 else 0
            final_percentage = peer_component + participation_component + instructor_component
            final_score = (final_percentage / 100) * sub_max

            late_penalty = reviewer_submission['late_penalty'] if reviewer_submission['late_penalty'] else 0
            final_score = max(0, final_score - late_penalty)

            cursor.execute('''
                UPDATE submissions SET final_score = ? WHERE id = ?
            ''', (final_score, reviewer_submission['id']))

    conn.commit()
    conn.close()

    status_text = 'approved' if action == 'approve' else 'rejected'
    flash(f'Peer review {status_text}! Reviewer participation score updated to {participation_score:.0f}%', 'success')

    redirect_to = request.form.get('redirect_to', '')
    if redirect_to == 'peer_review_status':
        return redirect(url_for('peer_review_status', activity_id=activity_id))
    return redirect(url_for('view_peer_reviews', activity_id=activity_id))


@app.route('/activity/<int:activity_id>/recalculate-scores', methods=['POST'])
@login_required
def recalculate_activity_scores(activity_id):
    """Recalculate all final scores for an activity using the 25-25-50 formula"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM activities WHERE id = ?', (activity_id,))
    activity = cursor.fetchone()

    if not activity:
        flash('Activity not found', 'error')
        conn.close()
        return redirect(url_for('dashboard'))

    max_points = activity['points']
    enable_peer_review = activity['enable_peer_review'] if 'enable_peer_review' in activity.keys() else 0

    # Get all submissions for this activity
    cursor.execute('SELECT * FROM submissions WHERE activity_id = ?', (activity_id,))
    submissions = cursor.fetchall()

    updated_count = 0
    for sub in submissions:
        if sub['instructor_score'] is None and sub['score'] is None:
            continue  # Skip ungraded submissions

        instructor_score = sub['instructor_score'] if sub['instructor_score'] else sub['score']
        if instructor_score is None:
            continue

        student_id = sub['student_id']
        late_penalty = sub['late_penalty'] if sub['late_penalty'] else 0

        if enable_peer_review:
            # peer_review_score is now a percentage (60-100)
            peer_review_score = sub['peer_review_score'] if sub['peer_review_score'] else 60
            # participation_score is now a percentage (0-100)
            participation_score = calculate_participation_score(cursor, student_id, activity_id, max_points)

            # Calculate weighted final score
            # peer_review_score is 60-100 (percentage)
            # participation_score is 0-100 (percentage)
            # instructor_score is raw points, needs to be converted
            peer_component = (peer_review_score / 100) * 25
            participation_component = (participation_score / 100) * 25
            instructor_component = (instructor_score / max_points) * 50 if max_points > 0 else 0

            final_percentage = peer_component + participation_component + instructor_component
            final_score = (final_percentage / 100) * max_points
            final_score = max(0, final_score - late_penalty)

            cursor.execute('''
                UPDATE submissions
                SET instructor_score = ?, participation_score = ?, final_score = ?
                WHERE id = ?
            ''', (instructor_score, participation_score, final_score, sub['id']))
        else:
            final_score = max(0, instructor_score - late_penalty)
            cursor.execute('''
                UPDATE submissions SET instructor_score = ?, final_score = ? WHERE id = ?
            ''', (instructor_score, final_score, sub['id']))

        updated_count += 1

    conn.commit()
    conn.close()

    flash(f'Recalculated scores for {updated_count} submissions!', 'success')
    return redirect(url_for('view_submissions', activity_id=activity_id))

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

    if not session_data:
        conn.close()
        flash('Session not found', 'error')
        return redirect(url_for('dashboard'))

    # Check visibility for students
    if current_user.role == 'student' and not session_data['is_visible']:
        conn.close()
        flash('This lesson is not yet available.', 'warning')
        return redirect(url_for('student_dashboard'))

    # Check session gating for students (previous session must be complete)
    progress = {}
    video_watched = True
    video_watch_seconds = 0
    if current_user.role == 'student':
        if not check_previous_session_complete(cursor, session_id, current_user.id):
            conn.close()
            flash('You must complete the previous session first.', 'warning')
            return redirect(url_for('student_subject', subject_id=session_data['subject_id']))

        progress = get_session_progress(cursor, session_id, current_user.id)
        video_watched = bool(progress['step_video'])

        # Get video watch seconds
        cursor.execute('SELECT watched_seconds, completed FROM session_video_watches WHERE session_id = ? AND student_id = ?',
                       (session_id, current_user.id))
        watch_row = cursor.fetchone()
        video_watch_seconds = watch_row['watched_seconds'] if watch_row else 0

    conn.close()

    # Route to subject-specific lesson templates
    subject_code = session_data['subject_code']
    session_number = session_data['session_number']

    # Check for subject-specific lesson template
    if subject_code == 'COMP012':
        template_name = f'lessons/comp012/session{session_number}.html'
    elif subject_code == 'COMP019':
        template_name = f'lessons/comp019/session{session_number}.html'
    elif subject_code == 'ES':
        template_name = f'lessons/es/session{session_number}.html'
    else:
        template_name = 'lesson.html'

    tpl_data = dict(session=session_data, video_watched=video_watched,
                    progress=progress, video_watch_seconds=video_watch_seconds)

    # Try to use subject-specific template, fallback to generic
    try:
        return render_template(template_name, **tpl_data)
    except:
        return render_template('lesson.html', **tpl_data)

@app.route('/session/<int:session_id>/reading')
@login_required
def session_reading(session_id):
    """Student reading materials page."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, sub.code as subject_code, sub.name as subject_name, sub.id as subject_id
        FROM sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.id = ?
    ''', (session_id,))
    session_data = cursor.fetchone()

    if not session_data:
        conn.close()
        flash('Session not found', 'error')
        return redirect(url_for('dashboard'))

    if current_user.role == 'student':
        if not session_data['is_visible']:
            conn.close()
            flash('This session is not available.', 'warning')
            return redirect(url_for('student_dashboard'))

        if not check_previous_session_complete(cursor, session_id, current_user.id):
            conn.close()
            flash('You must complete the previous session first.', 'warning')
            return redirect(url_for('student_subject', subject_id=session_data['subject_id']))

        progress = get_session_progress(cursor, session_id, current_user.id)
        if not progress['step_slides']:
            conn.close()
            flash('You must complete the slides first.', 'warning')
            return redirect(url_for('session_lesson', session_id=session_id))
    else:
        progress = {}

    conn.close()
    return render_template('session_reading.html', session=session_data, progress=progress)

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
    options_raw = request.form.get('options', '')
    correct_answer = request.form['correct_answer']
    points = request.form.get('points', 1)

    # Convert options from newline-separated to JSON array
    if question_type == 'multiple_choice' and options_raw:
        opts_list = [o.strip() for o in options_raw.strip().split('\n') if o.strip()]
        options = json.dumps(opts_list)
    elif question_type == 'true_false':
        options = json.dumps(['True', 'False'])
    else:
        options = ''

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quiz_questions (quiz_id, question_text, question_type, options, correct_answer, points)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (quiz_id, question_text, question_type, options, correct_answer, points))

    conn.commit()
    conn.close()
    flash('Question added successfully!', 'success')

    # Redirect back to manage page if that's where we came from
    if request.form.get('from_manage'):
        return redirect(url_for('manage_quiz', quiz_id=quiz_id))

    cursor2 = get_db()
    c2 = cursor2.cursor()
    c2.execute('SELECT session_id FROM quizzes WHERE id = ?', (quiz_id,))
    session_id = c2.fetchone()['session_id']
    cursor2.close()
    return redirect(url_for('session_quiz', session_id=session_id))


@app.route('/quiz/<int:quiz_id>/manage')
@login_required
def manage_quiz(quiz_id):
    """Instructor quiz management - edit/add/remove questions"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT q.*, s.title as session_title, s.session_number, s.subject_id,
               sub.name as subject_name, sub.section
        FROM quizzes q
        JOIN sessions s ON q.session_id = s.id
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE q.id = ?
    ''', (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz:
        conn.close()
        flash('Quiz not found.', 'error')
        return redirect(url_for('student_performance'))

    cursor.execute('SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY id', (quiz_id,))
    questions = cursor.fetchall()

    conn.close()
    return render_template('manage_quiz.html', quiz=quiz, questions=questions)


@app.route('/quiz/<int:quiz_id>/edit-question/<int:question_id>', methods=['POST'])
@login_required
def edit_quiz_question(quiz_id, question_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    question_text = request.form['question_text']
    question_type = request.form['question_type']
    correct_answer = request.form['correct_answer']
    options = request.form.get('options', '')

    # Convert options from newline-separated to JSON array
    if question_type == 'multiple_choice' and options:
        opts_list = [o.strip() for o in options.strip().split('\n') if o.strip()]
        options = json.dumps(opts_list)
    elif question_type == 'true_false':
        options = json.dumps(['True', 'False'])
    else:
        options = ''

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE quiz_questions SET question_text = ?, question_type = ?, options = ?, correct_answer = ?
        WHERE id = ? AND quiz_id = ?
    ''', (question_text, question_type, options, correct_answer, question_id, quiz_id))
    conn.commit()
    conn.close()
    flash('Question updated successfully!', 'success')
    return redirect(url_for('manage_quiz', quiz_id=quiz_id))


@app.route('/quiz/<int:quiz_id>/delete-question/<int:question_id>', methods=['POST'])
@login_required
def delete_quiz_question(quiz_id, question_id):
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM quiz_questions WHERE id = ? AND quiz_id = ?', (question_id, quiz_id))
    conn.commit()
    conn.close()
    flash('Question deleted.', 'success')
    return redirect(url_for('manage_quiz', quiz_id=quiz_id))


@app.route('/quiz/<int:quiz_id>/edit', methods=['POST'])
@login_required
def edit_quiz(quiz_id):
    """Edit quiz title and time limit"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    title = request.form['title']
    time_limit = request.form.get('time_limit', 0)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE quizzes SET title = ?, time_limit = ? WHERE id = ?',
                   (title, time_limit, quiz_id))
    conn.commit()
    conn.close()
    flash('Quiz updated successfully!', 'success')
    return redirect(url_for('manage_quiz', quiz_id=quiz_id))


@app.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    """Delete entire quiz and its questions"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM quiz_questions WHERE quiz_id = ?', (quiz_id,))
    cursor.execute('DELETE FROM quiz_attempts WHERE quiz_id = ?', (quiz_id,))
    cursor.execute('DELETE FROM quizzes WHERE id = ?', (quiz_id,))
    conn.commit()
    conn.close()
    flash('Quiz deleted successfully.', 'success')
    return redirect(url_for('student_performance'))


@app.route('/quiz/<int:quiz_id>/take')
@login_required
def take_quiz(quiz_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get quiz and check visibility
    cursor.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        conn.close()
        flash('Quiz not found.', 'error')
        return redirect(url_for('student_dashboard'))

    # Check if quiz is visible to students
    if not quiz['is_visible']:
        conn.close()
        flash('This quiz is not yet available.', 'warning')
        return redirect(url_for('student_dashboard'))

    # Check session progress — must complete activity step before quiz
    session_id_for_quiz = quiz['session_id']
    if not check_previous_session_complete(cursor, session_id_for_quiz, current_user.id):
        conn.close()
        flash('You must complete the previous session first.', 'warning')
        return redirect(url_for('student_dashboard'))

    progress = get_session_progress(cursor, session_id_for_quiz, current_user.id)
    if not progress['step_activity']:
        conn.close()
        flash('You must complete the activity before taking the quiz.', 'warning')
        return redirect(url_for('student_session_activities', session_id=session_id_for_quiz))

    # Check if already taken
    cursor.execute('SELECT * FROM quiz_attempts WHERE quiz_id = ? AND student_id = ?',
                   (quiz_id, current_user.id))
    attempt = cursor.fetchone()

    if attempt:
        conn.close()
        flash('You have already taken this quiz.', 'error')
        return redirect(url_for('student_dashboard'))

    cursor.execute('SELECT id, question_text, question_type, options, points FROM quiz_questions WHERE quiz_id = ? ORDER BY id', (quiz_id,))
    questions = cursor.fetchall()

    # Get session data for stepper
    cursor.execute('''
        SELECT s.*, sub.code as subject_code, sub.name as subject_name, sub.id as subject_id
        FROM sessions s JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.id = ?
    ''', (session_id_for_quiz,))
    session_data = cursor.fetchone()

    conn.close()

    return render_template('quiz_take.html', quiz=quiz, questions=questions,
                           session=session_data, progress=progress)

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

    # Mark quiz step complete in session progress
    cursor.execute('SELECT session_id FROM quizzes WHERE id = ?', (quiz_id,))
    quiz_row = cursor.fetchone()
    if quiz_row:
        cursor.execute('''
            INSERT INTO session_progress (session_id, student_id, step_quiz)
            VALUES (?, ?, 1)
            ON CONFLICT(session_id, student_id) DO UPDATE SET step_quiz = 1
        ''', (quiz_row['session_id'], current_user.id))
        check_and_mark_session_complete(cursor, quiz_row['session_id'], current_user.id)

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

    # Get exam and check visibility
    cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
    exam = cursor.fetchone()

    if not exam:
        conn.close()
        flash('Exam not found.', 'error')
        return redirect(url_for('student_dashboard'))

    # Check if exam is visible to students
    if not exam['is_visible']:
        conn.close()
        flash('This exam is not yet available.', 'warning')
        return redirect(url_for('student_dashboard'))

    cursor.execute('SELECT * FROM exam_attempts WHERE exam_id = ? AND student_id = ?',
                   (exam_id, current_user.id))
    attempt = cursor.fetchone()

    if attempt:
        conn.close()
        flash('You have already taken this exam.', 'error')
        return redirect(url_for('student_dashboard'))

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

    filter_subject = request.args.get('subject_id', '')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subjects ORDER BY code, section')
    subjects = cursor.fetchall()
    cursor.execute('SELECT * FROM users WHERE role = "student" ORDER BY full_name')
    students = cursor.fetchall()

    # Get distinct sections for filter
    cursor.execute('SELECT DISTINCT section FROM users WHERE role = "student" AND section IS NOT NULL ORDER BY section')
    sections = [r['section'] for r in cursor.fetchall()]

    # Build grade summary per student (across all enrolled subjects or filtered subject)
    student_grades_map = {}
    for student in students:
        # Get enrolled subjects
        cursor.execute('''
            SELECT s.* FROM subjects s
            INNER JOIN enrollments e ON s.id = e.subject_id
            WHERE e.student_id = ?
            ORDER BY s.code
        ''', (student['id'],))
        enrolled_subjects = cursor.fetchall()

        subject_grades = []
        for subj in enrolled_subjects:
            weights = get_grade_weights(subj['code'])

            # Activity avg
            cursor.execute('''
                SELECT AVG(sub.score) as avg_score
                FROM submissions sub
                JOIN activities a ON sub.activity_id = a.id
                JOIN sessions ses ON a.session_id = ses.id
                WHERE ses.subject_id = ? AND sub.student_id = ? AND sub.score IS NOT NULL AND sub.score_visible = 1
            ''', (subj['id'], student['id']))
            row = cursor.fetchone()
            activity_avg = row['avg_score'] if row and row['avg_score'] else 0

            # Quiz avg
            cursor.execute('''
                SELECT AVG(qa.score) as avg_score
                FROM quiz_attempts qa
                JOIN quizzes q ON qa.quiz_id = q.id
                JOIN sessions ses ON q.session_id = ses.id
                WHERE ses.subject_id = ? AND qa.student_id = ? AND qa.score IS NOT NULL AND qa.score_visible = 1
            ''', (subj['id'], student['id']))
            row = cursor.fetchone()
            quiz_avg = row['avg_score'] if row and row['avg_score'] else 0

            # Exam scores
            cursor.execute('''
                SELECT ea.score, e.exam_type
                FROM exam_attempts ea
                JOIN exams e ON ea.exam_id = e.id
                WHERE e.subject_id = ? AND ea.student_id = ? AND ea.score_visible = 1
            ''', (subj['id'], student['id']))
            midterm = None
            final_exam = None
            for exam in cursor.fetchall():
                if exam['exam_type'] == 'midterm':
                    midterm = exam['score']
                elif exam['exam_type'] == 'final':
                    final_exam = exam['score']

            weighted = (
                (activity_avg * weights['activities']) +
                (quiz_avg * weights['quizzes']) +
                ((midterm or 0) * weights['midterm']) +
                ((final_exam or 0) * weights['final'])
            )
            pup_grade = get_pup_grade(weighted)

            subject_grades.append({
                'subject_id': subj['id'],
                'code': subj['code'],
                'section': subj['section'],
                'activity_avg': round(activity_avg, 1),
                'quiz_avg': round(quiz_avg, 1),
                'midterm': round(midterm, 1) if midterm is not None else None,
                'final': round(final_exam, 1) if final_exam is not None else None,
                'weighted': round(weighted, 2),
                'pup_grade': pup_grade,
                'passed': pup_grade <= 3.00
            })

        student_grades_map[student['id']] = subject_grades

    conn.close()
    return render_template('grades.html', subjects=subjects, students=students,
                           sections=sections, student_grades_map=student_grades_map,
                           filter_subject=filter_subject)

@app.route('/grades/download')
@login_required
def download_grades_csv():
    """Download grade book as CSV"""
    if current_user.role != 'instructor':
        return redirect(url_for('student_dashboard'))

    subject_id = request.args.get('subject_id', type=int)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE role = "student" ORDER BY full_name')
    students = cursor.fetchall()

    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)

    if subject_id:
        cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
        subj = cursor.fetchone()
        if not subj:
            conn.close()
            flash('Subject not found', 'error')
            return redirect(url_for('grades'))

        writer.writerow(['Student ID', 'Full Name', 'Section', 'Subject',
                         'Activity Avg', 'Quiz Avg', 'Midterm', 'Final',
                         'Weighted Avg', 'PUP Grade', 'Status'])

        weights = get_grade_weights(subj['code'])
        for student in students:
            cursor.execute('SELECT 1 FROM enrollments WHERE student_id = ? AND subject_id = ?',
                           (student['id'], subject_id))
            if not cursor.fetchone():
                continue

            cursor.execute('''
                SELECT AVG(sub.score) as avg FROM submissions sub
                JOIN activities a ON sub.activity_id = a.id JOIN sessions ses ON a.session_id = ses.id
                WHERE ses.subject_id = ? AND sub.student_id = ? AND sub.score IS NOT NULL AND sub.score_visible = 1
            ''', (subject_id, student['id']))
            act_avg = cursor.fetchone()['avg'] or 0

            cursor.execute('''
                SELECT AVG(qa.score) as avg FROM quiz_attempts qa
                JOIN quizzes q ON qa.quiz_id = q.id JOIN sessions ses ON q.session_id = ses.id
                WHERE ses.subject_id = ? AND qa.student_id = ? AND qa.score IS NOT NULL AND qa.score_visible = 1
            ''', (subject_id, student['id']))
            quiz_avg = cursor.fetchone()['avg'] or 0

            cursor.execute('''
                SELECT ea.score, e.exam_type FROM exam_attempts ea
                JOIN exams e ON ea.exam_id = e.id
                WHERE e.subject_id = ? AND ea.student_id = ? AND ea.score_visible = 1
            ''', (subject_id, student['id']))
            midterm = final_exam = None
            for exam in cursor.fetchall():
                if exam['exam_type'] == 'midterm':
                    midterm = exam['score']
                elif exam['exam_type'] == 'final':
                    final_exam = exam['score']

            weighted = (act_avg * weights['activities'] + quiz_avg * weights['quizzes'] +
                        (midterm or 0) * weights['midterm'] + (final_exam or 0) * weights['final'])
            pup = get_pup_grade(weighted)

            writer.writerow([student['student_id'], student['full_name'], student['section'],
                             f"{subj['code']} {subj['section']}",
                             f"{act_avg:.1f}", f"{quiz_avg:.1f}",
                             f"{midterm:.1f}" if midterm is not None else '--',
                             f"{final_exam:.1f}" if final_exam is not None else '--',
                             f"{weighted:.2f}%", f"{pup:.2f}",
                             'PASSED' if pup <= 3.00 else 'FAILED'])
    else:
        writer.writerow(['Student ID', 'Full Name', 'Section', 'Subject',
                         'Activity Avg', 'Quiz Avg', 'Midterm', 'Final',
                         'Weighted Avg', 'PUP Grade', 'Status'])
        for student in students:
            cursor.execute('''
                SELECT s.* FROM subjects s
                INNER JOIN enrollments e ON s.id = e.subject_id
                WHERE e.student_id = ? ORDER BY s.code
            ''', (student['id'],))
            for subj in cursor.fetchall():
                weights = get_grade_weights(subj['code'])
                cursor.execute('''
                    SELECT AVG(sub.score) as avg FROM submissions sub
                    JOIN activities a ON sub.activity_id = a.id JOIN sessions ses ON a.session_id = ses.id
                    WHERE ses.subject_id = ? AND sub.student_id = ? AND sub.score IS NOT NULL AND sub.score_visible = 1
                ''', (subj['id'], student['id']))
                act_avg = cursor.fetchone()['avg'] or 0

                cursor.execute('''
                    SELECT AVG(qa.score) as avg FROM quiz_attempts qa
                    JOIN quizzes q ON qa.quiz_id = q.id JOIN sessions ses ON q.session_id = ses.id
                    WHERE ses.subject_id = ? AND qa.student_id = ? AND qa.score IS NOT NULL AND qa.score_visible = 1
                ''', (subj['id'], student['id']))
                quiz_avg = cursor.fetchone()['avg'] or 0

                cursor.execute('''
                    SELECT ea.score, e.exam_type FROM exam_attempts ea
                    JOIN exams e ON ea.exam_id = e.id
                    WHERE e.subject_id = ? AND ea.student_id = ? AND ea.score_visible = 1
                ''', (subj['id'], student['id']))
                midterm = final_exam = None
                for exam in cursor.fetchall():
                    if exam['exam_type'] == 'midterm':
                        midterm = exam['score']
                    elif exam['exam_type'] == 'final':
                        final_exam = exam['score']

                weighted = (act_avg * weights['activities'] + quiz_avg * weights['quizzes'] +
                            (midterm or 0) * weights['midterm'] + (final_exam or 0) * weights['final'])
                pup = get_pup_grade(weighted)

                writer.writerow([student['student_id'], student['full_name'], student['section'],
                                 f"{subj['code']} {subj['section']}",
                                 f"{act_avg:.1f}", f"{quiz_avg:.1f}",
                                 f"{midterm:.1f}" if midterm is not None else '--',
                                 f"{final_exam:.1f}" if final_exam is not None else '--',
                                 f"{weighted:.2f}%", f"{pup:.2f}",
                                 'PASSED' if pup <= 3.00 else 'FAILED'])

    conn.close()
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=grade_book.csv'}
    )


@app.route('/grades/student/<int:student_id>')
@login_required
def student_grades(student_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()

    # For students viewing their own grades, only show enrolled subjects
    if current_user.role == 'student':
        if current_user.id != student_id:
            flash('You can only view your own grades.', 'error')
            conn.close()
            return redirect(url_for('student_dashboard'))

    # Always show only enrolled subjects (for both students and instructors)
    cursor.execute('''
        SELECT s.* FROM subjects s
        INNER JOIN enrollments e ON s.id = e.subject_id
        WHERE e.student_id = ?
        ORDER BY s.code
    ''', (student_id,))
    subjects = cursor.fetchall()

    grades_data = []
    for subject in subjects:
        # Get subject-specific grade weights
        weights = get_grade_weights(subject['code'])

        # Get individual quiz scores (up to 12 quizzes)
        cursor.execute('''
            SELECT q.id, s.session_number, qa.score, qa.score_visible
            FROM quizzes q
            JOIN sessions s ON q.session_id = s.id
            LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id AND qa.student_id = ?
            WHERE s.subject_id = ?
            ORDER BY s.session_number
            LIMIT 12
        ''', (student_id, subject['id']))
        quiz_scores = []
        for row in cursor.fetchall():
            quiz_scores.append({
                'session': row['session_number'],
                'score': row['score'] if row['score'] is not None and row['score_visible'] else None,
                'pending': row['score'] is not None and not row['score_visible']
            })
        # Pad to 12 quizzes if less
        while len(quiz_scores) < 12:
            quiz_scores.append({'session': len(quiz_scores) + 1, 'score': None, 'pending': False})

        # Get individual activity scores (up to 12 activities)
        cursor.execute('''
            SELECT a.id, a.activity_number, s.session_number, sub.score, sub.score_visible
            FROM activities a
            JOIN sessions s ON a.session_id = s.id
            LEFT JOIN submissions sub ON a.id = sub.activity_id AND sub.student_id = ?
            WHERE s.subject_id = ?
            ORDER BY s.session_number, a.activity_number
            LIMIT 12
        ''', (student_id, subject['id']))
        activity_scores = []
        for row in cursor.fetchall():
            activity_scores.append({
                'session': row['session_number'],
                'activity_num': row['activity_number'],
                'score': row['score'] if row['score'] is not None and row['score_visible'] else None,
                'pending': row['score'] is not None and not row['score_visible']
            })
        # Pad to 12 activities if less
        while len(activity_scores) < 12:
            activity_scores.append({'session': len(activity_scores) + 1, 'activity_num': 1, 'score': None, 'pending': False})

        # Calculate averages for weighted calculation
        valid_quiz_scores = [q['score'] for q in quiz_scores if q['score'] is not None]
        quiz_avg = sum(valid_quiz_scores) / len(valid_quiz_scores) if valid_quiz_scores else 0

        valid_activity_scores = [a['score'] for a in activity_scores if a['score'] is not None]
        activity_avg = sum(valid_activity_scores) / len(valid_activity_scores) if valid_activity_scores else 0

        # Get exam scores
        cursor.execute('''
            SELECT ea.score, e.exam_type, ea.score_visible
            FROM exam_attempts ea
            JOIN exams e ON ea.exam_id = e.id
            WHERE e.subject_id = ? AND ea.student_id = ?
        ''', (subject['id'], student_id))
        exams = cursor.fetchall()

        midterm = None
        midterm_pending = False
        final_exam = None
        final_pending = False
        for exam in exams:
            if exam['exam_type'] == 'midterm':
                if exam['score_visible']:
                    midterm = exam['score']
                else:
                    midterm_pending = True
            elif exam['exam_type'] == 'final':
                if exam['score_visible']:
                    final_exam = exam['score']
                else:
                    final_pending = True

        # Check for project grade if no final exam
        project_grade = None
        final_for_calc = final_exam or 0
        if final_for_calc == 0:
            proj = compute_project_grade(cursor, subject['id'], student_id)
            if proj is not None and proj > 0:
                project_grade = proj
                final_for_calc = proj

        # Calculate weighted grade based on subject-specific weights
        # Activities: 50%, Quizzes: 10%, Midterm: 20%, Final: 20%
        weighted = (
            (activity_avg * weights['activities']) +
            (quiz_avg * weights['quizzes']) +
            ((midterm or 0) * weights['midterm']) +
            (final_for_calc * weights['final'])
        )

        # Get PUP grade equivalent
        pup_grade = get_pup_grade(weighted)

        grades_data.append({
            'subject': subject,
            'quiz_scores': quiz_scores,
            'activity_scores': activity_scores,
            'quiz_avg': quiz_avg,
            'activity_avg': activity_avg,
            'midterm': midterm,
            'midterm_pending': midterm_pending,
            'final': final_exam,
            'final_pending': final_pending,
            'project_grade': project_grade,
            'weighted': weighted,
            'pup_grade': pup_grade,
            'weights': weights
        })

    conn.close()
    return render_template('student_grades.html', student=student, grades=grades_data)

# ==================== STUDENT DASHBOARD ====================

@app.route('/student/dashboard')
@login_required
@profile_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.* FROM subjects s
        INNER JOIN enrollments e ON s.id = e.subject_id
        WHERE e.student_id = ?
        ORDER BY s.code, s.section
    ''', (current_user.id,))
    subjects = cursor.fetchall()

    # Compute per-subject performance
    subject_performance = []
    total_activities_done = 0
    total_activities = 0
    total_quizzes_done = 0
    total_quizzes = 0
    total_sessions_completed = 0
    total_sessions = 0
    overall_weighted_sum = 0
    overall_count = 0
    strength_areas = []
    weakness_areas = []

    for subj in subjects:
        # Activity stats
        cursor.execute('''
            SELECT COUNT(*) as total FROM activities a
            JOIN sessions s ON a.session_id = s.id
            WHERE s.subject_id = ? AND a.is_visible = 1
        ''', (subj['id'],))
        act_total = cursor.fetchone()['total']

        cursor.execute('''
            SELECT COUNT(*) as done, AVG(COALESCE(sub.final_score, sub.score)) as avg
            FROM submissions sub
            JOIN activities a ON sub.activity_id = a.id
            JOIN sessions s ON a.session_id = s.id
            WHERE s.subject_id = ? AND sub.student_id = ?
        ''', (subj['id'], current_user.id))
        act_row = cursor.fetchone()
        act_done = act_row['done']
        act_avg = act_row['avg'] or 0

        # Quiz stats
        cursor.execute('''
            SELECT COUNT(*) as total FROM quizzes q
            JOIN sessions s ON q.session_id = s.id
            WHERE s.subject_id = ? AND q.is_visible = 1
        ''', (subj['id'],))
        quiz_total = cursor.fetchone()['total']

        cursor.execute('''
            SELECT COUNT(*) as done, AVG(qa.score) as avg FROM quiz_attempts qa
            JOIN quizzes q ON qa.quiz_id = q.id
            JOIN sessions s ON q.session_id = s.id
            WHERE s.subject_id = ? AND qa.student_id = ?
        ''', (subj['id'], current_user.id))
        quiz_row = cursor.fetchone()
        quiz_done = quiz_row['done']
        quiz_avg = quiz_row['avg'] or 0

        # Session progress
        cursor.execute('SELECT id FROM sessions WHERE subject_id = ? AND is_visible = 1', (subj['id'],))
        vis_sessions = cursor.fetchall()
        sess_completed = sum(1 for v in vis_sessions if get_session_progress(cursor, v['id'], current_user.id).get('completed'))

        total_activities += act_total
        total_activities_done += act_done
        total_quizzes += quiz_total
        total_quizzes_done += quiz_done
        total_sessions += len(vis_sessions)
        total_sessions_completed += sess_completed

        # Weighted grade
        weighted = compute_weighted_grade(cursor, subj['id'], current_user.id)
        pup = get_pup_grade(weighted)
        if weighted > 0:
            overall_weighted_sum += weighted
            overall_count += 1

        # Strengths/weaknesses
        if act_avg >= 85:
            strength_areas.append((f"{subj['code']} Activities", act_avg))
        elif 0 < act_avg < 75:
            weakness_areas.append((f"{subj['code']} Activities", act_avg))
        if quiz_avg >= 85:
            strength_areas.append((f"{subj['code']} Quizzes", quiz_avg))
        elif 0 < quiz_avg < 75:
            weakness_areas.append((f"{subj['code']} Quizzes", quiz_avg))

        subject_performance.append({
            'subject': subj, 'activity_done': act_done, 'activity_total': act_total,
            'activity_avg': act_avg, 'quiz_done': quiz_done, 'quiz_total': quiz_total,
            'quiz_avg': quiz_avg, 'sessions_completed': sess_completed,
            'sessions_total': len(vis_sessions), 'weighted': weighted, 'pup_grade': pup,
            'passed': pup <= 3.00 if weighted > 0 else None
        })

    # Upcoming deadlines
    cursor.execute('''
        SELECT a.title, a.due_date, a.due_time, ses.session_number, sub.code as subject_code
        FROM activities a
        JOIN sessions ses ON a.session_id = ses.id
        JOIN subjects sub ON ses.subject_id = sub.id
        JOIN enrollments e ON sub.id = e.subject_id
        WHERE e.student_id = ? AND a.due_date >= date('now') AND a.is_visible = 1
        AND a.id NOT IN (SELECT activity_id FROM submissions WHERE student_id = ?)
        ORDER BY a.due_date, a.due_time
        LIMIT 5
    ''', (current_user.id, current_user.id))
    upcoming_deadlines = cursor.fetchall()

    # Project groups
    cursor.execute('''
        SELECT pg.group_name, pg.subject_id, sub.code as subject_code,
               (SELECT AVG(pp.percentage) FROM project_progress pp WHERE pp.group_id = pg.id) as avg_progress
        FROM project_groups pg
        JOIN project_group_members pgm ON pg.id = pgm.group_id
        JOIN subjects sub ON pg.subject_id = sub.id
        WHERE pgm.student_id = ?
    ''', (current_user.id,))
    my_groups = [dict(r) for r in cursor.fetchall()]

    overall_avg = overall_weighted_sum / overall_count if overall_count > 0 else 0
    overall_pup = get_pup_grade(overall_avg) if overall_avg > 0 else None
    strength_areas.sort(key=lambda x: -x[1])
    weakness_areas.sort(key=lambda x: x[1])

    conn.close()
    return render_template('student_dashboard.html',
                           subjects=subjects, subject_performance=subject_performance,
                           overall_avg=overall_avg, overall_pup=overall_pup,
                           total_activities_done=total_activities_done, total_activities=total_activities,
                           total_quizzes_done=total_quizzes_done, total_quizzes=total_quizzes,
                           total_sessions_completed=total_sessions_completed, total_sessions=total_sessions,
                           strength_areas=strength_areas[:5], weakness_areas=weakness_areas[:5],
                           upcoming_deadlines=upcoming_deadlines, my_groups=my_groups)

@app.route('/student/subject/<int:subject_id>')
@login_required
@profile_required
def student_subject(subject_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Check if student is enrolled in this subject
    cursor.execute('''
        SELECT 1 FROM enrollments WHERE student_id = ? AND subject_id = ?
    ''', (current_user.id, subject_id))
    if not cursor.fetchone():
        flash('You are not enrolled in this subject.', 'error')
        conn.close()
        return redirect(url_for('student_dashboard'))

    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()

    # Only show visible sessions to students
    cursor.execute('''
        SELECT * FROM sessions
        WHERE subject_id = ? AND is_visible = 1
        ORDER BY session_number
    ''', (subject_id,))
    sessions = cursor.fetchall()

    # Get progress and gating status for each session
    session_progress = {}
    locked_sessions = set()
    prev_completed = True  # First session is always unlocked
    for s in sessions:
        progress = get_session_progress(cursor, s['id'], current_user.id)
        session_progress[s['id']] = progress
        if not prev_completed:
            locked_sessions.add(s['id'])
        prev_completed = progress['completed'] or bool(progress.get('completed_at'))

    # Get available quizzes (only visible quizzes from visible sessions)
    cursor.execute('''
        SELECT q.*, s.session_number, q.session_id
        FROM quizzes q
        JOIN sessions s ON q.session_id = s.id
        WHERE s.subject_id = ? AND s.is_visible = 1 AND q.is_visible = 1
    ''', (subject_id,))
    quizzes = cursor.fetchall()

    # Get available exams (only visible exams)
    cursor.execute('SELECT * FROM exams WHERE subject_id = ? AND is_visible = 1', (subject_id,))
    exams = cursor.fetchall()

    conn.close()
    return render_template('student_subject.html', subject=subject, sessions=sessions,
                           quizzes=quizzes, exams=exams, session_progress=session_progress,
                           locked_sessions=locked_sessions)

@app.route('/student/session/<int:session_id>/activities')
@login_required
@profile_required
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

    # Check if session is visible
    if session_data and not session_data['is_visible']:
        flash('This session is not available.', 'warning')
        conn.close()
        return redirect(url_for('student_dashboard'))

    # Check session gating (previous session must be complete)
    if not check_previous_session_complete(cursor, session_id, current_user.id):
        conn.close()
        flash('You must complete the previous session first.', 'warning')
        return redirect(url_for('student_subject', subject_id=session_data['subject_id']))

    # Check step enforcement: video + slides + reading must be complete
    progress = get_session_progress(cursor, session_id, current_user.id)
    if not progress['step_video'] or not progress['step_slides'] or not progress['step_reading']:
        flash('You must complete the video, slides, and reading materials before accessing activities.', 'warning')
        conn.close()
        return redirect(url_for('session_lesson', session_id=session_id))

    # Only show visible activities
    cursor.execute('''
        SELECT * FROM activities
        WHERE session_id = ? AND is_visible = 1
        ORDER BY activity_number
    ''', (session_id,))
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

    # Current date string for due date comparison
    now_str = datetime.now().strftime('%Y-%m-%d')

    return render_template('student_activities.html',
                           session=session_data,
                           activities=activities,
                           submissions=submissions,
                           now_str=now_str,
                           progress=progress)

@app.route('/student/my-grades')
@login_required
def my_grades():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))
    return redirect(url_for('student_grades', student_id=current_user.id))

@app.route('/games')
@login_required
def games_hub():
    """Combined games & quizzes hub - students play, instructors see performance"""
    if current_user.role == 'instructor':
        return redirect(url_for('student_performance'))
    return render_template('games_hub.html')


@app.route('/games/performance')
@login_required
def student_performance():
    """Instructor view - student performance across games and quizzes"""
    if current_user.role != 'instructor':
        return redirect(url_for('games_hub'))

    import json as json_mod

    conn = get_db()
    cursor = conn.cursor()

    # ---- QUIZ ANALYTICS: per-quiz breakdown ----
    cursor.execute('''
        SELECT q.id, q.title as quiz_title, s.title as session_title,
               sub.name as subject_name, sub.section,
               (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = q.id) as total_questions,
               COUNT(qa.id) as attempts,
               AVG(qa.score) as avg_score,
               MAX(qa.score) as best_score,
               MIN(qa.score) as worst_score,
               AVG(qa.time_spent) as avg_time
        FROM quizzes q
        JOIN sessions s ON q.session_id = s.id
        JOIN subjects sub ON s.subject_id = sub.id
        LEFT JOIN quiz_attempts qa ON q.id = qa.quiz_id
        GROUP BY q.id
        ORDER BY sub.name, s.session_number
    ''')
    quizzes = [dict(row) for row in cursor.fetchall()]

    # For each quiz, get student attempts with details
    for quiz in quizzes:
        cursor.execute('''
            SELECT qa.*, u.full_name, u.student_id as sid, u.section, u.photo
            FROM quiz_attempts qa
            JOIN users u ON qa.student_id = u.id
            WHERE qa.quiz_id = ?
            ORDER BY qa.score DESC, qa.time_spent ASC
        ''', (quiz['id'],))
        attempts = [dict(r) for r in cursor.fetchall()]

        # Parse missed questions
        for a in attempts:
            try:
                a['missed_list'] = json_mod.loads(a.get('missed_questions') or '[]')
            except:
                a['missed_list'] = []
            a['is_perfect'] = (a['score'] == quiz['total_questions'])
            a['pct'] = round((a['score'] / quiz['total_questions'] * 100) if quiz['total_questions'] else 0)
            time_mins = (a.get('time_spent') or 0) // 60
            time_secs = (a.get('time_spent') or 0) % 60
            a['time_display'] = f'{time_mins}m {time_secs}s' if time_mins else f'{time_secs}s'

        quiz['attempt_count'] = len(attempts)
        quiz['attempt_list'] = attempts
        quiz['perfect_count'] = sum(1 for a in attempts if a['is_perfect'])
        quiz['fail_count'] = sum(1 for a in attempts if a['pct'] < 50)

    # ---- GAME ANALYTICS ----
    cursor.execute('''
        SELECT u.id, u.full_name, u.student_id, u.section, u.photo,
               gs.total_games, gs.highest_score as game_high_score, gs.highest_level,
               gs.total_codes_typed, gs.xp_points, gs.current_rank, gs.best_streak
        FROM users u
        LEFT JOIN game_user_stats gs ON u.id = gs.user_id
        WHERE u.role = 'student' AND u.is_approved = 1 AND gs.total_games > 0
        ORDER BY gs.highest_score DESC
    ''')
    game_players = [dict(row) for row in cursor.fetchall()]

    # Get sections
    cursor.execute('''
        SELECT DISTINCT section FROM users WHERE role = 'student' AND section IS NOT NULL ORDER BY section
    ''')
    sections = [r['section'] for r in cursor.fetchall()]

    # Get subjects for filter
    cursor.execute('SELECT DISTINCT name FROM subjects ORDER BY name')
    subjects = [r['name'] for r in cursor.fetchall()]

    # Summary stats
    total_attempts = sum(q['attempt_count'] for q in quizzes)
    overall_avg = round(sum(q.get('avg_score') or 0 for q in quizzes if q['attempt_count'] > 0) / max(1, sum(1 for q in quizzes if q['attempt_count'] > 0)), 1)
    total_perfect = sum(q['perfect_count'] for q in quizzes)

    conn.close()
    return render_template('student_performance.html',
                           quizzes=quizzes,
                           game_players=game_players,
                           sections=sections,
                           subjects=subjects,
                           total_attempts=total_attempts,
                           overall_avg=overall_avg,
                           total_perfect=total_perfect)


@app.route('/typing-game')
@login_required
def typing_game():
    return render_template('typing_game.html')

@app.route('/api/game/save-score', methods=['POST'])
@login_required
def save_game_score():
    data = request.get_json()
    score = data.get('score', 0)
    level = data.get('level', 1)
    codes_typed = data.get('codesTyped', 0)
    best_streak = data.get('bestStreak', 0)
    difficulty = data.get('difficulty', 'medium')

    conn = get_db()
    cursor = conn.cursor()

    # Save individual game score
    cursor.execute('''
        INSERT INTO game_scores (user_id, score, level, codes_typed, best_streak, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, score, level, codes_typed, best_streak, difficulty))

    # Update or create user stats
    cursor.execute('SELECT * FROM game_user_stats WHERE user_id = ?', (current_user.id,))
    stats = cursor.fetchone()

    # Calculate XP (1 XP per 10 points scored)
    xp_earned = score // 10

    # Determine rank based on total XP
    def get_rank(xp):
        if xp >= 10000: return 'Python Master'
        if xp >= 5000: return 'Code Ninja'
        if xp >= 2500: return 'Senior Dev'
        if xp >= 1000: return 'Developer'
        if xp >= 500: return 'Junior Dev'
        if xp >= 200: return 'Apprentice'
        if xp >= 50: return 'Novice'
        return 'Beginner'

    if stats:
        new_total_xp = stats['xp_points'] + xp_earned
        new_rank = get_rank(new_total_xp)
        cursor.execute('''
            UPDATE game_user_stats SET
                total_games = total_games + 1,
                total_score = total_score + ?,
                highest_score = MAX(highest_score, ?),
                highest_level = MAX(highest_level, ?),
                total_codes_typed = total_codes_typed + ?,
                best_streak = MAX(best_streak, ?),
                xp_points = ?,
                current_rank = ?,
                last_played = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (score, score, level, codes_typed, best_streak, new_total_xp, new_rank, current_user.id))
    else:
        new_rank = get_rank(xp_earned)
        cursor.execute('''
            INSERT INTO game_user_stats
            (user_id, total_games, total_score, highest_score, highest_level, total_codes_typed, best_streak, xp_points, current_rank, last_played)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (current_user.id, score, score, level, codes_typed, best_streak, xp_earned, new_rank))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'xp_earned': xp_earned, 'rank': new_rank if not stats else get_rank(stats['xp_points'] + xp_earned)})

@app.route('/api/game/leaderboard')
@login_required
def get_leaderboard():
    conn = get_db()
    cursor = conn.cursor()

    # Get top 10 all-time scores
    cursor.execute('''
        SELECT u.id, u.full_name, u.photo, u.section, gs.highest_score, gs.highest_level,
               gs.total_codes_typed, gs.best_streak, gs.xp_points, gs.current_rank, gs.total_games
        FROM game_user_stats gs
        JOIN users u ON gs.user_id = u.id
        ORDER BY gs.highest_score DESC
        LIMIT 10
    ''')
    all_time = [dict(row) for row in cursor.fetchall()]

    # Get weekly top scores (games played in last 7 days)
    cursor.execute('''
        SELECT u.id, u.full_name, u.photo, u.section, MAX(g.score) as highest_score,
               MAX(g.level) as highest_level, SUM(g.codes_typed) as total_codes_typed,
               MAX(g.best_streak) as best_streak
        FROM game_scores g
        JOIN users u ON g.user_id = u.id
        WHERE g.played_at >= datetime('now', '-7 days')
        GROUP BY g.user_id
        ORDER BY highest_score DESC
        LIMIT 10
    ''')
    weekly = [dict(row) for row in cursor.fetchall()]

    # Get current user's stats and rank
    cursor.execute('''
        SELECT gs.*,
               (SELECT COUNT(*) + 1 FROM game_user_stats WHERE highest_score > gs.highest_score) as global_rank
        FROM game_user_stats gs
        WHERE gs.user_id = ?
    ''', (current_user.id,))
    user_stats = cursor.fetchone()

    conn.close()

    return jsonify({
        'allTime': all_time,
        'weekly': weekly,
        'userStats': dict(user_stats) if user_stats else None,
        'currentUser': {
            'id': current_user.id,
            'name': current_user.full_name,
            'photo': current_user.photo
        }
    })

# ============== QUIZ JOURNEY GAME ==============

@app.route('/quiz-journey')
@login_required
def quiz_journey():
    """Quiz journey - level-based quiz game"""
    conn = get_db()
    cursor = conn.cursor()

    # For students, get enrolled subjects
    if current_user.role == 'student':
        cursor.execute('''
            SELECT DISTINCT sub.* FROM subjects sub
            JOIN enrollments e ON sub.id = e.subject_id
            WHERE e.student_id = ?
            ORDER BY sub.name
        ''', (current_user.id,))
    else:
        # Instructors see all subjects
        cursor.execute('SELECT * FROM subjects ORDER BY name')

    subjects = cursor.fetchall()

    # Get session/quiz data for each subject
    subjects_data = []
    for subject in subjects:
        cursor.execute('''
            SELECT s.*, COUNT(DISTINCT q.id) as quiz_count
            FROM sessions s
            LEFT JOIN quizzes q ON s.id = q.session_id
            WHERE s.subject_id = ?
            GROUP BY s.id
            ORDER BY s.session_number
        ''', (subject['id'],))
        sessions = cursor.fetchall()

        # Get completed quizzes for this student
        cursor.execute('''
            SELECT DISTINCT q.id FROM quiz_attempts qa
            JOIN quizzes q ON qa.quiz_id = q.id
            JOIN sessions s ON q.session_id = s.id
            WHERE qa.student_id = ? AND s.subject_id = ?
        ''', (current_user.id, subject['id']))
        completed_quiz_ids = [r['id'] for r in cursor.fetchall()]

        subjects_data.append({
            'subject': subject,
            'sessions': sessions,
            'completed_quiz_ids': completed_quiz_ids
        })

    conn.close()
    return render_template('quiz_journey.html', subjects_data=subjects_data)


@app.route('/quiz-journey/subject/<int:subject_id>')
@login_required
def quiz_journey_subject(subject_id):
    """Show sessions/levels for a subject"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
    subject = cursor.fetchone()

    if not subject:
        flash('Subject not found', 'error')
        conn.close()
        return redirect(url_for('quiz_journey'))

    # Get sessions with quizzes
    cursor.execute('''
        SELECT s.*, COUNT(q.id) as quiz_count,
               (SELECT COUNT(*) FROM quiz_attempts qa
                JOIN quizzes q2 ON qa.quiz_id = q2.id
                WHERE q2.session_id = s.id AND qa.student_id = ?) as completed_quizzes
        FROM sessions s
        LEFT JOIN quizzes q ON s.id = q.session_id
        WHERE s.subject_id = ?
        GROUP BY s.id
        ORDER BY s.session_number
    ''', (current_user.id, subject_id))
    sessions = cursor.fetchall()

    conn.close()
    return render_template('quiz_journey_subject.html', subject=subject, sessions=sessions)


@app.route('/quiz-journey/session/<int:session_id>')
@login_required
def quiz_journey_session(session_id):
    """Show quizzes available in a session"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.*, sub.name as subject_name, sub.id as subject_id
        FROM sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.id = ?
    ''', (session_id,))
    session = cursor.fetchone()

    if not session:
        flash('Session not found', 'error')
        conn.close()
        return redirect(url_for('quiz_journey'))

    # Get quizzes for this session
    cursor.execute('''
        SELECT q.*,
               (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = q.id) as question_count,
               (SELECT score FROM quiz_attempts WHERE quiz_id = q.id AND student_id = ? ORDER BY submitted_at DESC LIMIT 1) as last_score,
               (SELECT MAX(score) FROM quiz_attempts WHERE quiz_id = q.id AND student_id = ?) as best_score
        FROM quizzes q
        WHERE q.session_id = ?
    ''', (current_user.id, current_user.id, session_id))
    quizzes = cursor.fetchall()

    conn.close()
    return render_template('quiz_journey_session.html', session=session, quizzes=quizzes)


@app.route('/quiz-journey/start/<int:quiz_id>')
@login_required
def start_quiz_journey_game(quiz_id):
    """Start a timed quiz with randomized questions"""
    import random
    import hashlib

    conn = get_db()
    cursor = conn.cursor()

    # Get quiz info
    cursor.execute('''
        SELECT q.*, s.title as session_title, sub.name as subject_name
        FROM quizzes q
        JOIN sessions s ON q.session_id = s.id
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE q.id = ?
    ''', (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        flash('Quiz not found', 'error')
        conn.close()
        return redirect(url_for('quiz_journey'))

    # Get questions
    cursor.execute('''
        SELECT * FROM quiz_questions WHERE quiz_id = ?
    ''', (quiz_id,))
    questions = [dict(q) for q in cursor.fetchall()]

    # Randomize questions based on user ID + quiz ID (consistent for same user)
    seed = int(hashlib.md5(f"{current_user.id}-{quiz_id}".encode()).hexdigest(), 16)
    random.seed(seed)
    random.shuffle(questions)

    # Randomize options for each multiple choice question
    for q in questions:
        if q['options']:
            import json
            try:
                options = json.loads(q['options'])
                random.shuffle(options)
                q['options'] = json.dumps(options)
            except:
                pass

    conn.close()
    return render_template('quiz_journey_game.html', quiz=quiz, questions=questions)


@app.route('/quiz-journey/submit/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz_journey_game(quiz_id):
    """Submit quiz answers and calculate score"""
    import json

    conn = get_db()
    cursor = conn.cursor()

    # Get quiz questions
    cursor.execute('''
        SELECT * FROM quiz_questions WHERE quiz_id = ?
    ''', (quiz_id,))
    questions = cursor.fetchall()

    # Get time spent from form
    time_spent = int(request.form.get('time_spent', 0))

    # Calculate score and track missed questions
    answers = {}
    score = 0
    total_points = 0
    missed = []

    for q in questions:
        question_id = q['id']
        user_answer = request.form.get(f'question_{question_id}', '').strip()
        answers[str(question_id)] = user_answer

        total_points += q['points']
        if user_answer.lower() == q['correct_answer'].lower():
            score += q['points']
        else:
            missed.append({
                'question_id': question_id,
                'question': q['question_text'][:100],
                'your_answer': user_answer or '(no answer)',
                'correct_answer': q['correct_answer']
            })

    total_questions = len(questions)

    # Check if already attempted (update or create)
    cursor.execute('''
        SELECT id FROM quiz_attempts WHERE quiz_id = ? AND student_id = ?
    ''', (quiz_id, current_user.id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE quiz_attempts SET answers = ?, score = ?, time_spent = ?,
                   missed_questions = ?, total_questions = ?, submitted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(answers), score, time_spent, json.dumps(missed), total_questions, existing['id']))
    else:
        cursor.execute('''
            INSERT INTO quiz_attempts (quiz_id, student_id, answers, score, time_spent, missed_questions, total_questions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (quiz_id, current_user.id, json.dumps(answers), score, time_spent, json.dumps(missed), total_questions))

    conn.commit()

    # Get quiz info for result page
    cursor.execute('''
        SELECT q.*, s.title as session_title, sub.name as subject_name, s.subject_id
        FROM quizzes q
        JOIN sessions s ON q.session_id = s.id
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE q.id = ?
    ''', (quiz_id,))
    quiz = cursor.fetchone()

    conn.close()

    percentage = (score / total_points * 100) if total_points > 0 else 0

    return render_template('quiz_journey_result.html',
                           quiz=quiz,
                           score=score,
                           total_points=total_points,
                           percentage=percentage,
                           answers=answers,
                           missed=missed,
                           time_spent=time_spent)


@app.route('/api/quiz-journey/leaderboard/<int:quiz_id>')
@login_required
def quiz_journey_leaderboard(quiz_id):
    """Get leaderboard for a specific quiz"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.id, u.full_name, u.photo, u.section, qa.score, qa.submitted_at
        FROM quiz_attempts qa
        JOIN users u ON qa.student_id = u.id
        WHERE qa.quiz_id = ?
        ORDER BY qa.score DESC, qa.submitted_at ASC
        LIMIT 10
    ''', (quiz_id,))
    leaderboard = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(leaderboard)


# ============== MESSAGING SYSTEM ==============

def time_ago(dt):
    """Convert datetime to human-readable time ago string"""
    if not dt:
        return ''
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins}m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours}h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago'
    else:
        return dt.strftime('%b %d')

@app.route('/api/messages/unread-count')
@login_required
def get_unread_counts():
    conn = get_db()
    cursor = conn.cursor()

    # Count unread messages for current user
    if current_user.role == 'instructor':
        # Instructors see replies to their messages
        cursor.execute('''
            SELECT COUNT(*) FROM messages
            WHERE recipient_id = ? AND is_read = 0
        ''', (current_user.id,))
    else:
        # Students see messages sent to them (individual, section, or all)
        cursor.execute('''
            SELECT COUNT(*) FROM messages
            WHERE is_read = 0 AND (
                recipient_id = ?
                OR recipient_section = ?
                OR recipient_all = 1
            ) AND sender_id != ?
        ''', (current_user.id, current_user.section, current_user.id))

    msg_count = cursor.fetchone()[0]

    # Count unread notifications
    cursor.execute('''
        SELECT COUNT(*) FROM notifications
        WHERE user_id = ? AND is_read = 0
    ''', (current_user.id,))
    notif_count = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        'messages': msg_count,
        'notifications': notif_count
    })

@app.route('/api/messages/preview')
@login_required
def get_messages_preview():
    conn = get_db()
    cursor = conn.cursor()

    if current_user.role == 'instructor':
        # Instructors see their sent messages
        cursor.execute('''
            SELECT m.*, u.full_name as sender_name, u.photo as sender_photo
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.sender_id = ?
            ORDER BY m.created_at DESC
            LIMIT 5
        ''', (current_user.id,))
    else:
        # Students see messages sent to them
        cursor.execute('''
            SELECT m.*, u.full_name as sender_name, u.photo as sender_photo
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (
                m.recipient_id = ?
                OR m.recipient_section = ?
                OR m.recipient_all = 1
            ) AND m.sender_id != ?
            ORDER BY m.created_at DESC
            LIMIT 5
        ''', (current_user.id, current_user.section, current_user.id))

    messages = []
    for row in cursor.fetchall():
        msg = dict(row)
        created = datetime.strptime(msg['created_at'], '%Y-%m-%d %H:%M:%S') if msg['created_at'] else datetime.now()
        msg['time_ago'] = time_ago(created)
        msg['sender_photo'] = url_for('static', filename='uploads/photos/' + (msg['sender_photo'] or 'default.png'))
        messages.append(msg)

    conn.close()
    return jsonify(messages)

@app.route('/api/notifications')
@login_required
def get_notifications():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (current_user.id,))

    notifications = []
    for row in cursor.fetchall():
        notif = dict(row)
        created = datetime.strptime(notif['created_at'], '%Y-%m-%d %H:%M:%S') if notif['created_at'] else datetime.now()
        notif['time_ago'] = time_ago(created)
        notif['read'] = bool(notif['is_read'])
        notifications.append(notif)

    conn.close()
    return jsonify(notifications)

@app.route('/api/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_read(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?', (id, current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (current_user.id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/messages')
@login_required
def messages():
    conn = get_db()
    cursor = conn.cursor()

    if current_user.role == 'instructor':
        # Get sent messages
        cursor.execute('''
            SELECT m.*,
                   CASE
                       WHEN m.recipient_all = 1 THEN 'All Students'
                       WHEN m.recipient_section IS NOT NULL THEN m.recipient_section
                       ELSE (SELECT full_name FROM users WHERE id = m.recipient_id)
                   END as recipient_name
            FROM messages m
            WHERE m.sender_id = ?
            ORDER BY m.created_at DESC
        ''', (current_user.id,))
        sent_messages = [dict(row) for row in cursor.fetchall()]

        # Get list of sections and students for compose
        cursor.execute('SELECT DISTINCT section FROM users WHERE section IS NOT NULL ORDER BY section')
        sections = [row['section'] for row in cursor.fetchall()]

        cursor.execute('SELECT id, full_name, section, student_id FROM users WHERE role = "student" ORDER BY section, full_name')
        students = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return render_template('messages_instructor.html',
                               sent_messages=sent_messages,
                               sections=sections,
                               students=students)
    else:
        # Students: Get received messages
        cursor.execute('''
            SELECT m.*, u.full_name as sender_name, u.photo as sender_photo
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (
                m.recipient_id = ?
                OR m.recipient_section = ?
                OR m.recipient_all = 1
            ) AND m.sender_id != ?
            ORDER BY m.created_at DESC
        ''', (current_user.id, current_user.section, current_user.id))
        received_messages = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return render_template('messages_student.html', messages=received_messages)

@app.route('/messages/<int:id>')
@login_required
def view_message(id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.*, u.full_name as sender_name, u.photo as sender_photo
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.id = ?
    ''', (id,))
    message = cursor.fetchone()

    if not message:
        flash('Message not found.', 'error')
        conn.close()
        return redirect(url_for('messages'))

    message = dict(message)

    # Mark as read if student viewing
    if current_user.role == 'student':
        cursor.execute('UPDATE messages SET is_read = 1 WHERE id = ?', (id,))
        conn.commit()

    conn.close()
    return render_template('view_message.html', message=message)

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    if current_user.role != 'instructor':
        flash('Only instructors can send messages.', 'error')
        return redirect(url_for('messages'))

    recipient_type = request.form.get('recipient_type')
    subject = request.form.get('subject', '').strip()
    content = request.form.get('content', '').strip()

    if not subject or not content:
        flash('Subject and message content are required.', 'error')
        return redirect(url_for('messages'))

    conn = get_db()
    cursor = conn.cursor()

    if recipient_type == 'all':
        # Send to all students
        cursor.execute('''
            INSERT INTO messages (sender_id, recipient_all, subject, content)
            VALUES (?, 1, ?, ?)
        ''', (current_user.id, subject, content))

        # Create notifications for all students
        cursor.execute('SELECT id FROM users WHERE role = "student"')
        students = cursor.fetchall()
        for student in students:
            cursor.execute('''
                INSERT INTO notifications (user_id, type, icon, message, link)
                VALUES (?, 'message', 'envelope', ?, ?)
            ''', (student['id'], f'New message from {current_user.full_name}: {subject}', f'/messages/{cursor.lastrowid}'))

        flash(f'Message sent to all students!', 'success')

    elif recipient_type == 'section':
        section = request.form.get('section')
        if not section:
            flash('Please select a section.', 'error')
            conn.close()
            return redirect(url_for('messages'))

        cursor.execute('''
            INSERT INTO messages (sender_id, recipient_section, subject, content)
            VALUES (?, ?, ?, ?)
        ''', (current_user.id, section, subject, content))
        msg_id = cursor.lastrowid

        # Create notifications for section students
        cursor.execute('SELECT id FROM users WHERE role = "student" AND section = ?', (section,))
        students = cursor.fetchall()
        for student in students:
            cursor.execute('''
                INSERT INTO notifications (user_id, type, icon, message, link)
                VALUES (?, 'message', 'envelope', ?, ?)
            ''', (student['id'], f'New message from {current_user.full_name}: {subject}', f'/messages/{msg_id}'))

        flash(f'Message sent to {section}!', 'success')

    elif recipient_type == 'individual':
        recipient_id = request.form.get('recipient_id')
        if not recipient_id:
            flash('Please select a student.', 'error')
            conn.close()
            return redirect(url_for('messages'))

        cursor.execute('''
            INSERT INTO messages (sender_id, recipient_id, subject, content)
            VALUES (?, ?, ?, ?)
        ''', (current_user.id, recipient_id, subject, content))
        msg_id = cursor.lastrowid

        # Create notification for the student
        cursor.execute('''
            INSERT INTO notifications (user_id, type, icon, message, link)
            VALUES (?, 'message', 'envelope', ?, ?)
        ''', (recipient_id, f'New message from {current_user.full_name}: {subject}', f'/messages/{msg_id}'))

        flash('Message sent!', 'success')

    conn.commit()
    conn.close()
    return redirect(url_for('messages'))


# ============== V2: PLATFORM ADMIN ROUTES ==============

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    # Platform-wide stats
    cursor.execute('SELECT COUNT(*) FROM institutions WHERE is_active = 1')
    total_institutions = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "instructor"')
    total_instructors = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "student"')
    total_students = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM subjects')
    total_subjects = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM submissions')
    total_submissions = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM ai_admin_logs')
    total_ai_actions = cursor.fetchone()[0]

    # Recent AI actions
    cursor.execute('''
        SELECT * FROM ai_admin_logs ORDER BY created_at DESC LIMIT 10
    ''')
    recent_ai_logs = cursor.fetchall()

    # Active AI rules
    cursor.execute('SELECT COUNT(*) FROM ai_admin_rules WHERE is_active = 1')
    active_rules = cursor.fetchone()[0]

    # Institutions list
    cursor.execute('SELECT * FROM institutions ORDER BY name')
    institutions = cursor.fetchall()

    # Payroll summary
    cursor.execute('SELECT COUNT(*) FROM instructor_payroll WHERE status = "draft"')
    pending_payroll = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(net_pay) FROM instructor_payroll WHERE status = "paid"')
    total_paid = cursor.fetchone()[0] or 0

    conn.close()

    return render_template('admin_dashboard.html',
        total_institutions=total_institutions,
        total_instructors=total_instructors,
        total_students=total_students,
        total_subjects=total_subjects,
        total_submissions=total_submissions,
        total_ai_actions=total_ai_actions,
        recent_ai_logs=recent_ai_logs,
        active_rules=active_rules,
        institutions=institutions,
        pending_payroll=pending_payroll,
        total_paid=total_paid
    )


@app.route('/admin/institutions')
@login_required
@admin_required
def admin_institutions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.*,
               (SELECT COUNT(*) FROM users WHERE institution_id = i.id AND role = 'instructor') as instructor_count,
               (SELECT COUNT(*) FROM users WHERE institution_id = i.id AND role = 'student') as student_count,
               (SELECT COUNT(*) FROM subjects WHERE institution_id = i.id) as subject_count
        FROM institutions i ORDER BY i.name
    ''')
    institutions = cursor.fetchall()
    cursor.execute('SELECT * FROM subscription_plans WHERE is_active = 1 ORDER BY price_monthly')
    plans = cursor.fetchall()
    conn.close()
    return render_template('admin_institutions.html', institutions=institutions, plans=plans)


@app.route('/api/admin/institutions', methods=['POST'])
@login_required
@admin_required
def create_institution():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO institutions (name, short_name, domain, address, contact_email, contact_phone, plan, max_students, max_instructors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('name'), data.get('short_name'), data.get('domain'), data.get('address'),
              data.get('contact_email'), data.get('contact_phone'), data.get('plan', 'free'),
              data.get('max_students', 100), data.get('max_instructors', 5)))
        conn.commit()

        # Log AI action
        cursor.execute('''
            INSERT INTO ai_admin_logs (action_type, target_type, target_name, decision, reasoning, severity)
            VALUES ('institution_created', 'institution', ?, 'New institution registered', 'Admin created new institution', 'info')
        ''', (data.get('name'),))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Institution created'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/institutions/<int:inst_id>', methods=['PUT'])
@login_required
@admin_required
def update_institution(inst_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE institutions SET name=?, short_name=?, domain=?, address=?, contact_email=?, contact_phone=?,
               plan=?, max_students=?, max_instructors=?, is_active=?
        WHERE id=?
    ''', (data.get('name'), data.get('short_name'), data.get('domain'), data.get('address'),
          data.get('contact_email'), data.get('contact_phone'), data.get('plan'),
          data.get('max_students'), data.get('max_instructors'), data.get('is_active', 1), inst_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/instructors')
@login_required
@admin_required
def admin_instructors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.*, i.name as institution_name, ip.employee_id, ip.hire_date, ip.contract_type,
               ip.salary_rate, ip.salary_frequency
        FROM users u
        LEFT JOIN institutions i ON u.institution_id = i.id
        LEFT JOIN instructor_profiles ip ON u.id = ip.user_id
        WHERE u.role = 'instructor'
        ORDER BY u.full_name
    ''')
    instructors = cursor.fetchall()
    cursor.execute('SELECT id, name, short_name FROM institutions WHERE is_active = 1 ORDER BY name')
    institutions = cursor.fetchall()
    conn.close()
    return render_template('admin_instructors.html', instructors=instructors, institutions=institutions)


@app.route('/api/admin/instructor-profile/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_instructor_profile(user_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    # Update institution assignment
    cursor.execute('UPDATE users SET institution_id = ? WHERE id = ?', (data.get('institution_id'), user_id))

    # Upsert instructor profile
    cursor.execute('SELECT id FROM instructor_profiles WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE instructor_profiles SET institution_id=?, employee_id=?, hire_date=?, contract_type=?,
                   salary_rate=?, salary_frequency=?
            WHERE user_id=?
        ''', (data.get('institution_id'), data.get('employee_id'), data.get('hire_date'),
              data.get('contract_type', 'full-time'), data.get('salary_rate', 0),
              data.get('salary_frequency', 'monthly'), user_id))
    else:
        cursor.execute('''
            INSERT INTO instructor_profiles (user_id, institution_id, employee_id, hire_date, contract_type, salary_rate, salary_frequency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, data.get('institution_id'), data.get('employee_id'), data.get('hire_date'),
              data.get('contract_type', 'full-time'), data.get('salary_rate', 0),
              data.get('salary_frequency', 'monthly')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN PAYROLL ==============

@app.route('/admin/payroll')
@login_required
@admin_required
def admin_payroll():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.*, u.full_name, i.short_name as institution_name
        FROM instructor_payroll p
        JOIN users u ON p.instructor_id = u.id
        LEFT JOIN institutions i ON p.institution_id = i.id
        ORDER BY p.created_at DESC
    ''')
    payrolls = cursor.fetchall()

    cursor.execute('''
        SELECT u.id, u.full_name, ip.salary_rate, ip.salary_frequency, ip.contract_type, i.short_name as institution_name
        FROM users u
        JOIN instructor_profiles ip ON u.id = ip.user_id
        LEFT JOIN institutions i ON ip.institution_id = i.id
        WHERE u.role = 'instructor'
        ORDER BY u.full_name
    ''')
    instructors = cursor.fetchall()

    conn.close()
    return render_template('admin_payroll.html', payrolls=payrolls, instructors=instructors)


@app.route('/api/admin/payroll/generate', methods=['POST'])
@login_required
@admin_required
def generate_payroll():
    data = request.get_json()
    period_start = data.get('period_start')
    period_end = data.get('period_end')

    if not period_start or not period_end:
        return jsonify({'success': False, 'error': 'Period dates required'})

    conn = get_db()
    cursor = conn.cursor()

    # Get all instructors with profiles
    cursor.execute('''
        SELECT u.id, u.full_name, ip.institution_id, ip.salary_rate, ip.salary_frequency, ip.contract_type
        FROM users u
        JOIN instructor_profiles ip ON u.id = ip.user_id
        WHERE u.role = 'instructor' AND ip.salary_rate > 0
    ''')
    instructors = cursor.fetchall()

    generated = 0
    for inst in instructors:
        # Calculate attendance for the period
        cursor.execute('''
            SELECT COUNT(*) as total_days,
                   SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
                   SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
                   SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
                   SUM(hours_worked) as total_hours
            FROM instructor_attendance
            WHERE instructor_id = ? AND date BETWEEN ? AND ?
        ''', (inst['id'], period_start, period_end))
        att = cursor.fetchone()

        days_present = (att['present'] or 0) + (att['late'] or 0)
        days_absent = att['absent'] or 0
        days_late = att['late'] or 0
        total_hours = att['total_hours'] or 0

        base_salary = inst['salary_rate']
        if inst['salary_frequency'] == 'hourly':
            gross_pay = base_salary * total_hours
        else:
            gross_pay = base_salary

        # Simple deductions: absent days proportional deduction
        daily_rate = gross_pay / 22 if gross_pay > 0 else 0  # ~22 working days/month
        absent_deduction = daily_rate * days_absent
        late_deduction = (daily_rate * 0.1) * days_late  # 10% of daily rate per late day
        total_deductions = absent_deduction + late_deduction
        deduction_details = json.dumps({
            'absent_days': days_absent, 'absent_deduction': round(absent_deduction, 2),
            'late_days': days_late, 'late_deduction': round(late_deduction, 2)
        })

        net_pay = max(0, gross_pay - total_deductions)

        # Check if payroll already exists for this period
        cursor.execute('''
            SELECT id FROM instructor_payroll WHERE instructor_id = ? AND period_start = ? AND period_end = ?
        ''', (inst['id'], period_start, period_end))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO instructor_payroll (instructor_id, institution_id, period_start, period_end,
                    base_salary, days_present, days_absent, days_late, total_hours,
                    deductions, deduction_details, gross_pay, net_pay, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')
            ''', (inst['id'], inst['institution_id'], period_start, period_end,
                  base_salary, days_present, days_absent, days_late, round(total_hours, 1),
                  round(total_deductions, 2), deduction_details, round(gross_pay, 2), round(net_pay, 2)))
            generated += 1

    conn.commit()

    # AI log
    cursor.execute('''
        INSERT INTO ai_admin_logs (action_type, target_type, decision, reasoning, severity)
        VALUES ('payroll_generated', 'payroll', ?, ?, 'info')
    ''', (f'Generated {generated} payroll records for {period_start} to {period_end}',
          'Auto-calculated based on attendance records and salary rates'))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'generated': generated})


@app.route('/api/admin/payroll/<int:payroll_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_payroll(payroll_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE instructor_payroll SET status = 'approved', approved_by = ?, approved_at = datetime('now')
        WHERE id = ?
    ''', (current_user.id, payroll_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/payroll/<int:payroll_id>/pay', methods=['POST'])
@login_required
@admin_required
def mark_payroll_paid(payroll_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE instructor_payroll SET status = 'paid', paid_at = datetime('now')
        WHERE id = ? AND status = 'approved'
    ''', (payroll_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN AI LOGS & RULES ==============

@app.route('/admin/ai-logs')
@login_required
@admin_required
def admin_ai_logs():
    conn = get_db()
    cursor = conn.cursor()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    filter_type = request.args.get('type', '')
    filter_severity = request.args.get('severity', '')

    query = 'SELECT * FROM ai_admin_logs WHERE 1=1'
    params = []
    if filter_type:
        query += ' AND action_type = ?'
        params.append(filter_type)
    if filter_severity:
        query += ' AND severity = ?'
        params.append(filter_severity)
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])

    cursor.execute(query, params)
    logs = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) FROM ai_admin_logs')
    total = cursor.fetchone()[0]

    # Get distinct types for filter
    cursor.execute('SELECT DISTINCT action_type FROM ai_admin_logs ORDER BY action_type')
    action_types = [r['action_type'] for r in cursor.fetchall()]

    conn.close()
    return render_template('admin_ai_logs.html', logs=logs, action_types=action_types,
                          filter_type=filter_type, filter_severity=filter_severity,
                          page=page, total=total, per_page=per_page)


@app.route('/admin/ai-rules')
@login_required
@admin_required
def admin_ai_rules():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ai_admin_rules ORDER BY priority DESC, rule_name')
    rules = cursor.fetchall()
    conn.close()
    return render_template('admin_ai_rules.html', rules=rules)


@app.route('/api/admin/ai-rules/<int:rule_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_ai_rule(rule_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT is_active FROM ai_admin_rules WHERE id = ?', (rule_id,))
    rule = cursor.fetchone()
    if rule:
        new_state = 0 if rule['is_active'] else 1
        cursor.execute('UPDATE ai_admin_rules SET is_active = ? WHERE id = ?', (new_state, rule_id))
        conn.commit()
    conn.close()
    return jsonify({'success': True, 'is_active': new_state})


@app.route('/api/admin/ai-rules', methods=['POST'])
@login_required
@admin_required
def create_ai_rule():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ai_admin_rules (rule_name, rule_type, condition_field, condition_operator, condition_value, action_type, action_params, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data.get('rule_name'), data.get('rule_type'), data.get('condition_field'),
          data.get('condition_operator'), data.get('condition_value'),
          data.get('action_type'), data.get('action_params', '{}'), data.get('priority', 0)))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== INSTRUCTOR ATTENDANCE ==============

@app.route('/instructor/attendance')
@login_required
def instructor_attendance():
    if current_user.role not in ('instructor', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get current month attendance
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().strftime('%Y-%m-01')

    cursor.execute('''
        SELECT * FROM instructor_attendance
        WHERE instructor_id = ? AND date BETWEEN ? AND ?
        ORDER BY date DESC
    ''', (current_user.id, month_start, today))
    attendance_records = cursor.fetchall()

    # Check if clocked in today
    cursor.execute('''
        SELECT * FROM instructor_attendance WHERE instructor_id = ? AND date = ?
    ''', (current_user.id, today))
    today_record = cursor.fetchone()

    # Monthly summary
    cursor.execute('''
        SELECT COUNT(*) as total_days,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
               SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
               SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
               SUM(hours_worked) as total_hours
        FROM instructor_attendance
        WHERE instructor_id = ? AND date BETWEEN ? AND ?
    ''', (current_user.id, month_start, today))
    summary = cursor.fetchone()

    conn.close()
    return render_template('instructor_attendance.html',
        attendance=attendance_records, today_record=today_record,
        summary=summary, today=today)


@app.route('/api/attendance/clock-in', methods=['POST'])
@login_required
def clock_in():
    if current_user.role != 'instructor':
        return jsonify({'success': False, 'error': 'Instructors only'})

    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('SELECT id FROM instructor_attendance WHERE instructor_id = ? AND date = ?',
                   (current_user.id, today))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Already clocked in today'})

    ip_address = request.remote_addr
    cursor.execute('''
        INSERT INTO instructor_attendance (instructor_id, date, time_in, status, ip_address)
        VALUES (?, ?, ?, 'present', ?)
    ''', (current_user.id, today, now, ip_address))
    conn.commit()

    # AI log
    cursor.execute('''
        INSERT INTO ai_admin_logs (action_type, target_type, target_id, target_name, decision, severity)
        VALUES ('clock_in', 'instructor', ?, ?, ?, 'info')
    ''', (current_user.id, current_user.full_name, f'Clocked in at {now}'))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'time_in': now})


@app.route('/api/attendance/clock-out', methods=['POST'])
@login_required
def clock_out():
    if current_user.role != 'instructor':
        return jsonify({'success': False, 'error': 'Instructors only'})

    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('SELECT * FROM instructor_attendance WHERE instructor_id = ? AND date = ?',
                   (current_user.id, today))
    record = cursor.fetchone()
    if not record:
        conn.close()
        return jsonify({'success': False, 'error': 'No clock-in record for today'})

    if record['time_out']:
        conn.close()
        return jsonify({'success': False, 'error': 'Already clocked out today'})

    # Calculate hours worked
    time_in = datetime.strptime(record['time_in'], '%Y-%m-%d %H:%M:%S')
    time_out = datetime.strptime(now, '%Y-%m-%d %H:%M:%S')
    hours_worked = round((time_out - time_in).total_seconds() / 3600, 2)

    cursor.execute('''
        UPDATE instructor_attendance SET time_out = ?, hours_worked = ? WHERE id = ?
    ''', (now, hours_worked, record['id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'time_out': now, 'hours_worked': hours_worked})


# ============== INSTRUCTOR PAYROLL VIEW ==============

@app.route('/instructor/payroll')
@login_required
def instructor_payroll_view():
    if current_user.role not in ('instructor', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM instructor_payroll
        WHERE instructor_id = ?
        ORDER BY period_end DESC
    ''', (current_user.id,))
    payrolls = cursor.fetchall()

    # Get profile info
    cursor.execute('SELECT * FROM instructor_profiles WHERE user_id = ?', (current_user.id,))
    profile = cursor.fetchone()

    # Current month attendance summary
    month_start = datetime.now().strftime('%Y-%m-01')
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) as total_days,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present,
               SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late,
               SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent,
               SUM(hours_worked) as total_hours
        FROM instructor_attendance
        WHERE instructor_id = ? AND date BETWEEN ? AND ?
    ''', (current_user.id, month_start, today))
    attendance_summary = cursor.fetchone()

    conn.close()
    return render_template('instructor_payroll.html',
        payrolls=payrolls, profile=profile, attendance_summary=attendance_summary)


# ============== AI ADMIN AGENT ==============

def ai_admin_agent():
    """Background AI admin agent that monitors and triggers actions based on rules."""
    import time
    import sqlite3 as _sqlite3

    time.sleep(120)  # Wait 2 minutes on startup

    while True:
        try:
            conn = _sqlite3.connect(DATABASE)
            conn.row_factory = _sqlite3.Row
            cursor = conn.cursor()

            # Check if AI admin is enabled
            cursor.execute("SELECT setting_value FROM platform_settings WHERE setting_key = 'ai_admin_enabled'")
            setting = cursor.fetchone()
            if not setting or setting['setting_value'] != 'true':
                conn.close()
                time.sleep(1800)
                continue

            # Get active rules
            cursor.execute('SELECT * FROM ai_admin_rules WHERE is_active = 1 ORDER BY priority DESC')
            rules = cursor.fetchall()

            for rule in rules:
                try:
                    if rule['rule_type'] == 'grade_monitor':
                        _ai_check_grades(cursor, conn, rule)
                    elif rule['rule_type'] == 'deadline_monitor':
                        _ai_check_deadlines(cursor, conn, rule)
                    elif rule['rule_type'] == 'progress_monitor':
                        _ai_check_progress(cursor, conn, rule)
                    elif rule['rule_type'] == 'attendance_monitor':
                        _ai_check_attendance(cursor, conn, rule)
                except Exception as e:
                    print(f'[AI-Admin] Rule "{rule["rule_name"]}" error: {e}')

            conn.close()
        except Exception as e:
            print(f'[AI-Admin] Agent error: {e}')

        # Get interval from settings or default 30 min
        time.sleep(1800)


def _ai_check_grades(cursor, conn, rule):
    """Check student grades against threshold and send alerts."""
    threshold = float(rule['condition_value'])
    params = json.loads(rule['action_params']) if rule['action_params'] else {}

    cursor.execute('''
        SELECT DISTINCT e.subject_id, e.student_id FROM enrollments e
        JOIN users u ON e.student_id = u.id AND u.is_approved = 1
    ''')
    enrollments = cursor.fetchall()

    for enr in enrollments:
        try:
            grade = compute_weighted_grade(cursor, enr['subject_id'], enr['student_id'])
            if grade and grade > 0 and grade < threshold:
                # Check if we already alerted recently
                cursor.execute('''
                    SELECT id FROM ai_admin_logs
                    WHERE action_type = 'grade_alert' AND target_id = ? AND target_type = ?
                    AND created_at > datetime('now', '-7 days')
                ''', (enr['student_id'], f"subject_{enr['subject_id']}"))
                if not cursor.fetchone():
                    cursor.execute('SELECT full_name FROM users WHERE id = ?', (enr['student_id'],))
                    student = cursor.fetchone()
                    cursor.execute('SELECT code FROM subjects WHERE id = ?', (enr['subject_id'],))
                    subject = cursor.fetchone()

                    if student and subject:
                        msg = params.get('message_template', 'Your grade needs improvement in {subject}.')
                        msg = msg.replace('{grade}', f'{grade:.1f}').replace('{subject}', subject['code'])

                        cursor.execute('''
                            INSERT INTO notifications (user_id, type, icon, message, link)
                            VALUES (?, 'warning', 'exclamation-triangle', ?, '/my-grades')
                        ''', (enr['student_id'], msg))

                        cursor.execute('''
                            INSERT INTO ai_admin_logs (action_type, target_type, target_id, target_name, decision, reasoning, severity)
                            VALUES ('grade_alert', ?, ?, ?, ?, ?, ?)
                        ''', (f"subject_{enr['subject_id']}", enr['student_id'], student['full_name'],
                              f'Sent grade alert: {grade:.1f}% in {subject["code"]}',
                              f'Grade below {threshold}% threshold', params.get('severity', 'warning')))
                        conn.commit()
        except Exception:
            pass


def _ai_check_deadlines(cursor, conn, rule):
    """Check for missed activity deadlines."""
    today = datetime.now().strftime('%Y-%m-%d')

    cursor.execute('''
        SELECT a.id, a.title, a.due_date, s.code as subject_code, s.id as subject_id,
               e.student_id
        FROM activities a
        JOIN sessions ses ON a.session_id = ses.id
        JOIN subjects s ON ses.subject_id = s.id
        JOIN enrollments e ON e.subject_id = s.id
        JOIN users u ON e.student_id = u.id AND u.is_approved = 1
        LEFT JOIN submissions sub ON sub.activity_id = a.id AND sub.student_id = e.student_id
        WHERE a.due_date IS NOT NULL AND a.due_date < ? AND sub.id IS NULL
    ''', (today,))
    missed = cursor.fetchall()

    for m in missed:
        cursor.execute('''
            SELECT id FROM ai_admin_logs
            WHERE action_type = 'deadline_alert' AND target_id = ?
            AND data LIKE ? AND created_at > datetime('now', '-3 days')
        ''', (m['student_id'], f'%activity_{m["id"]}%'))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO notifications (user_id, type, icon, message, link)
                VALUES (?, 'warning', 'clock', ?, ?)
            ''', (m['student_id'],
                  f'Missed deadline: "{m["title"]}" in {m["subject_code"]} was due {m["due_date"]}.',
                  f'/student/subject/{m["subject_id"]}'))

            cursor.execute('''
                INSERT INTO ai_admin_logs (action_type, target_type, target_id, decision, data, severity)
                VALUES ('deadline_alert', 'student', ?, ?, ?, 'warning')
            ''', (m['student_id'], f'Missed deadline alert for {m["title"]}',
                  json.dumps({'activity_id': m['id'], 'key': f'activity_{m["id"]}'})))
            conn.commit()


def _ai_check_progress(cursor, conn, rule):
    """Check for students behind on sessions."""
    threshold = int(rule['condition_value'])

    cursor.execute('''
        SELECT e.student_id, e.subject_id, s.code as subject_code,
               (SELECT COUNT(*) FROM sessions WHERE subject_id = e.subject_id AND is_visible = 1) as total_sessions,
               (SELECT COUNT(*) FROM session_progress sp
                JOIN sessions ses ON sp.session_id = ses.id
                WHERE ses.subject_id = e.subject_id AND sp.student_id = e.student_id AND sp.completed_at IS NOT NULL) as completed_sessions
        FROM enrollments e
        JOIN subjects s ON e.subject_id = s.id
        JOIN users u ON e.student_id = u.id AND u.is_approved = 1
    ''')
    for enr in cursor.fetchall():
        behind = enr['total_sessions'] - enr['completed_sessions']
        if behind > threshold:
            cursor.execute('''
                SELECT id FROM ai_admin_logs
                WHERE action_type = 'progress_alert' AND target_id = ?
                AND data LIKE ? AND created_at > datetime('now', '-7 days')
            ''', (enr['student_id'], f'%subject_{enr["subject_id"]}%'))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO notifications (user_id, type, icon, message, link)
                    VALUES (?, 'warning', 'tasks', ?, ?)
                ''', (enr['student_id'],
                      f'You are {behind} sessions behind in {enr["subject_code"]}. Catch up!',
                      f'/student/subject/{enr["subject_id"]}'))
                cursor.execute('''
                    INSERT INTO ai_admin_logs (action_type, target_type, target_id, decision, data, severity)
                    VALUES ('progress_alert', 'student', ?, ?, ?, 'warning')
                ''', (enr['student_id'], f'{behind} sessions behind in {enr["subject_code"]}',
                      json.dumps({'subject_id': enr['subject_id'], 'key': f'subject_{enr["subject_id"]}'})))
                conn.commit()


def _ai_check_attendance(cursor, conn, rule):
    """Check if instructors have clocked in today."""
    today = datetime.now().strftime('%Y-%m-%d')
    day_of_week = datetime.now().strftime('%A')

    # Only check on weekdays
    if day_of_week in ('Saturday', 'Sunday'):
        return

    cursor.execute('''
        SELECT u.id, u.full_name FROM users u
        WHERE u.role = 'instructor'
        AND u.id NOT IN (SELECT instructor_id FROM instructor_attendance WHERE date = ?)
    ''', (today,))
    missing = cursor.fetchall()

    for inst in missing:
        cursor.execute('''
            SELECT id FROM ai_admin_logs
            WHERE action_type = 'attendance_reminder' AND target_id = ? AND created_at > datetime('now', '-12 hours')
        ''', (inst['id'],))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO notifications (user_id, type, icon, message, link)
                VALUES (?, 'info', 'clock', 'Reminder: Please clock in for today.', '/instructor/attendance')
            ''', (inst['id'],))
            cursor.execute('''
                INSERT INTO ai_admin_logs (action_type, target_type, target_id, target_name, decision, severity)
                VALUES ('attendance_reminder', 'instructor', ?, ?, 'Sent clock-in reminder', 'info')
            ''', (inst['id'], inst['full_name']))
            conn.commit()


# Start AI Admin agent in background thread
import threading as _threading
_ai_thread = _threading.Thread(target=ai_admin_agent, daemon=True)
_ai_thread.start()


# ============== DATABASE BACKUP & RESTORE ==============

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

BACKUP_FOLDER = 'backups'
os.makedirs(BACKUP_FOLDER, exist_ok=True)

AUTO_BACKUP_INTERVAL = 24  # hours
REMINDER_BEFORE_HOURS = 5  # remind 5 hours before auto-backup deadline

# Email backup config
BACKUP_EMAIL_TO = 'sangrenesflorante@gmail.com'
BACKUP_EMAIL_FROM = os.environ.get('SMTP_EMAIL', '')
BACKUP_EMAIL_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587


def email_backup(filepath):
    """Email the database backup file to the configured address."""
    if not BACKUP_EMAIL_FROM or not BACKUP_EMAIL_PASSWORD:
        print('[Email-Backup] SMTP_EMAIL or SMTP_PASSWORD not configured. Skipping email.')
        return False

    try:
        import sqlite3 as _sqlite3
        conn = _sqlite3.connect(DATABASE)
        conn.row_factory = _sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "student"')
        student_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM subjects')
        subject_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM submissions')
        submission_count = cursor.fetchone()[0]
        conn.close()

        db_size = round(os.path.getsize(filepath) / (1024 * 1024), 2)
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        filename = os.path.basename(filepath)

        msg = MIMEMultipart()
        msg['From'] = BACKUP_EMAIL_FROM
        msg['To'] = BACKUP_EMAIL_TO
        msg['Subject'] = f'LMS Database Backup - {datetime.now().strftime("%b %d, %Y %I:%M %p")}'

        body = f"""Sangrenes LMS Portal - Automatic Database Backup

Backup File: {filename}
Database Size: {db_size} MB
Timestamp: {timestamp}

Records Summary:
- Students: {student_count}
- Subjects: {subject_count}
- Submissions: {submission_count}

This backup was sent automatically by the LMS backup system.
To restore, upload this .db file via the Backup & Restore page.
"""
        msg.attach(MIMEText(body, 'plain'))

        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(BACKUP_EMAIL_FROM, BACKUP_EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f'[Email-Backup] Sent backup to {BACKUP_EMAIL_TO}: {filename}')
        return True
    except Exception as e:
        print(f'[Email-Backup] Failed to send: {e}')
        return False


def get_last_backup_time():
    """Get the timestamp of the most recent backup file."""
    backups = glob_module.glob(os.path.join(BACKUP_FOLDER, '*.db'))
    if not backups:
        return None
    latest = max(backups, key=os.path.getmtime)
    return datetime.fromtimestamp(os.path.getmtime(latest))


def get_hours_since_last_backup():
    """Get hours elapsed since the last backup."""
    last = get_last_backup_time()
    if last is None:
        return float('inf')
    delta = datetime.now() - last
    return delta.total_seconds() / 3600


def create_auto_backup():
    """Create an automatic backup of the database and email it."""
    import sqlite3 as _sqlite3
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'auto_{timestamp}.db'
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)
    try:
        source = _sqlite3.connect(DATABASE)
        dest = _sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()
        print(f'[Auto-Backup] Created: {backup_name}')
        # Email the backup
        email_backup(backup_path)
        return True
    except Exception as e:
        print(f'[Auto-Backup] Failed: {e}')
        return False


def send_backup_reminder():
    """Send a notification to all instructors reminding them to back up."""
    import sqlite3 as _sqlite3
    try:
        conn = _sqlite3.connect(DATABASE)
        conn.row_factory = _sqlite3.Row
        cursor = conn.cursor()

        # Check if we already sent a reminder in the last 20 hours (avoid spam)
        cursor.execute('''
            SELECT COUNT(*) FROM notifications
            WHERE message LIKE '%backup reminder%'
            AND created_at > datetime('now', '-20 hours')
        ''')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        cursor.execute('SELECT id FROM users WHERE role = "instructor"')
        instructors = cursor.fetchall()
        for inst in instructors:
            cursor.execute('''
                INSERT INTO notifications (user_id, type, icon, message, link)
                VALUES (?, 'warning', 'exclamation-triangle',
                        'Backup reminder: No database backup in the last 19 hours. Please create a backup soon or one will be created automatically.',
                        '/admin/backup')
            ''', (inst['id'],))
        conn.commit()
        conn.close()
        print('[Auto-Backup] Reminder notifications sent to instructors.')
    except Exception as e:
        print(f'[Auto-Backup] Reminder failed: {e}')


def backup_scheduler():
    """Background thread that checks backup status every 30 minutes."""
    import time
    # Wait 60 seconds on startup before first check
    time.sleep(60)
    while True:
        try:
            hours = get_hours_since_last_backup()
            reminder_threshold = AUTO_BACKUP_INTERVAL - REMINDER_BEFORE_HOURS  # 19 hours

            if hours >= AUTO_BACKUP_INTERVAL:
                # 24+ hours with no backup -> auto-backup
                create_auto_backup()
            elif hours >= reminder_threshold:
                # 19+ hours with no backup -> send reminder
                send_backup_reminder()
        except Exception as e:
            print(f'[Auto-Backup] Scheduler error: {e}')

        time.sleep(1800)  # Check every 30 minutes


# Start the backup scheduler in a background thread
import threading
_backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
_backup_thread.start()


@app.route('/admin/backup')
@login_required
def backup_page():
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    # List existing backups
    backup_files = []
    for f in sorted(glob_module.glob(os.path.join(BACKUP_FOLDER, '*.db')), key=os.path.getmtime, reverse=True):
        stat = os.stat(f)
        backup_files.append({
            'filename': os.path.basename(f),
            'size': round(stat.st_size / (1024 * 1024), 2),  # MB
            'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %I:%M %p')
        })

    # Current DB size
    db_size = round(os.path.getsize(DATABASE) / (1024 * 1024), 2) if os.path.exists(DATABASE) else 0

    # Count records
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "student"')
    student_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM subjects')
    subject_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM submissions')
    submission_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM quiz_attempts')
    quiz_attempt_count = cursor.fetchone()[0]
    conn.close()

    # Auto-backup timing info
    last_backup = get_last_backup_time()
    hours_since_raw = get_hours_since_last_backup()
    hours_since = round(hours_since_raw, 1) if hours_since_raw != float('inf') else 0
    if last_backup:
        from datetime import timedelta
        next_auto = last_backup + timedelta(hours=AUTO_BACKUP_INTERVAL)
        hours_remaining = max(0, round(AUTO_BACKUP_INTERVAL - hours_since_raw, 1))
    else:
        next_auto = None
        hours_remaining = 0

    email_configured = bool(BACKUP_EMAIL_FROM and BACKUP_EMAIL_PASSWORD)

    return render_template('backup.html',
        backups=backup_files,
        db_size=db_size,
        student_count=student_count,
        subject_count=subject_count,
        submission_count=submission_count,
        quiz_attempt_count=quiz_attempt_count,
        last_backup=last_backup,
        hours_since=hours_since,
        hours_remaining=round(hours_remaining, 1),
        next_auto=next_auto,
        auto_interval=AUTO_BACKUP_INTERVAL,
        reminder_hours=REMINDER_BEFORE_HOURS,
        email_configured=email_configured,
        backup_email=BACKUP_EMAIL_TO
    )


@app.route('/admin/backup/create', methods=['POST'])
@login_required
def create_backup():
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)

    try:
        # Use SQLite backup API for safe copy
        import sqlite3
        source = sqlite3.connect(DATABASE)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()
        flash(f'Backup created successfully: {backup_name}', 'success')
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'error')

    return redirect(url_for('backup_page'))


@app.route('/admin/backup/email-now', methods=['POST'])
@login_required
def email_backup_now():
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    if not BACKUP_EMAIL_FROM or not BACKUP_EMAIL_PASSWORD:
        flash('Email not configured. Set SMTP_EMAIL and SMTP_PASSWORD environment variables.', 'error')
        return redirect(url_for('backup_page'))

    if not os.path.exists(DATABASE):
        flash('Database not found.', 'error')
        return redirect(url_for('backup_page'))

    success = email_backup(DATABASE)
    if success:
        flash(f'Database backup emailed to {BACKUP_EMAIL_TO} successfully!', 'success')
    else:
        flash('Failed to send email. Check SMTP settings.', 'error')

    return redirect(url_for('backup_page'))


@app.route('/admin/backup/download/<filename>')
@login_required
def download_backup(filename):
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    safe_name = secure_filename(filename)
    backup_path = os.path.join(BACKUP_FOLDER, safe_name)

    if not os.path.exists(backup_path):
        flash('Backup file not found.', 'error')
        return redirect(url_for('backup_page'))

    return send_file(backup_path, as_attachment=True, download_name=safe_name)


@app.route('/admin/backup/download-current')
@login_required
def download_current_db():
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    if not os.path.exists(DATABASE):
        flash('Database file not found.', 'error')
        return redirect(url_for('backup_page'))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(DATABASE, as_attachment=True, download_name=f'classroom_lms_{timestamp}.db')


@app.route('/admin/backup/restore/<filename>', methods=['POST'])
@login_required
def restore_backup(filename):
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    safe_name = secure_filename(filename)
    backup_path = os.path.join(BACKUP_FOLDER, safe_name)

    if not os.path.exists(backup_path):
        flash('Backup file not found.', 'error')
        return redirect(url_for('backup_page'))

    try:
        # Auto-backup current DB before restoring
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        auto_backup = os.path.join(BACKUP_FOLDER, f'pre_restore_{timestamp}.db')
        import sqlite3
        source = sqlite3.connect(DATABASE)
        dest = sqlite3.connect(auto_backup)
        source.backup(dest)
        dest.close()
        source.close()

        # Restore: copy backup over current DB
        shutil.copy2(backup_path, DATABASE)
        flash(f'Database restored from {safe_name}. A pre-restore backup was saved automatically.', 'success')
    except Exception as e:
        flash(f'Restore failed: {str(e)}', 'error')

    return redirect(url_for('backup_page'))


@app.route('/admin/backup/upload', methods=['POST'])
@login_required
def upload_backup():
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    if 'backup_file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('backup_page'))

    file = request.files['backup_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('backup_page'))

    if not file.filename.endswith('.db'):
        flash('Invalid file type. Only .db files are accepted.', 'error')
        return redirect(url_for('backup_page'))

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = f'uploaded_{timestamp}.db'
        upload_path = os.path.join(BACKUP_FOLDER, safe_name)
        file.save(upload_path)

        # Validate it's a real SQLite database
        import sqlite3
        test_conn = sqlite3.connect(upload_path)
        test_conn.execute('SELECT count(*) FROM sqlite_master')
        test_conn.close()

        flash(f'Backup file uploaded: {safe_name}', 'success')
    except Exception as e:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        flash(f'Invalid database file: {str(e)}', 'error')

    return redirect(url_for('backup_page'))


@app.route('/admin/backup/delete/<filename>', methods=['POST'])
@login_required
def delete_backup(filename):
    if current_user.role != 'instructor':
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    safe_name = secure_filename(filename)
    backup_path = os.path.join(BACKUP_FOLDER, safe_name)

    if os.path.exists(backup_path):
        os.remove(backup_path)
        flash(f'Backup deleted: {safe_name}', 'success')
    else:
        flash('Backup file not found.', 'error')

    return redirect(url_for('backup_page'))


# ============== ADMIN STUDENTS MANAGEMENT ==============

@app.route('/admin/students')
@login_required
@admin_required
def admin_students():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.*, i.short_name as institution_name,
               (SELECT COUNT(*) FROM enrollments WHERE student_id = u.id) as enrolled_subjects,
               (SELECT COUNT(*) FROM submissions WHERE student_id = u.id) as total_submissions,
               (SELECT COUNT(*) FROM quiz_attempts WHERE student_id = u.id) as quiz_attempts
        FROM users u
        LEFT JOIN institutions i ON u.institution_id = i.id
        WHERE u.role = 'student'
        ORDER BY u.full_name
    ''')
    students = cursor.fetchall()
    cursor.execute('SELECT id, name, short_name FROM institutions WHERE is_active = 1 ORDER BY name')
    institutions = cursor.fetchall()
    cursor.execute('SELECT DISTINCT section FROM users WHERE section IS NOT NULL AND section != "" ORDER BY section')
    sections = [r['section'] for r in cursor.fetchall()]
    conn.close()
    return render_template('admin_students.html', students=students, institutions=institutions, sections=sections)


@app.route('/api/admin/students', methods=['POST'])
@login_required
@admin_required
def admin_create_student():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role, student_id, section,
                             institution_id, email, contact_number, is_approved, profile_completed)
            VALUES (?, ?, ?, 'student', ?, ?, ?, ?, ?, 1, 1)
        ''', (data.get('username'), generate_password_hash(data.get('password', 'student123')),
              data.get('full_name'), data.get('student_id'), data.get('section'),
              data.get('institution_id'), data.get('email'), data.get('contact_number')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/students/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def admin_update_student(user_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET full_name=?, email=?, student_id=?, section=?, contact_number=?,
               institution_id=?, is_approved=?, status=?
        WHERE id=? AND role='student'
    ''', (data.get('full_name'), data.get('email'), data.get('student_id'), data.get('section'),
          data.get('contact_number'), data.get('institution_id'),
          data.get('is_approved', 1), data.get('status', 'active'), user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/students/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_student(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = "inactive" WHERE id = ? AND role = "student"', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN SUBJECTS MANAGEMENT ==============

@app.route('/admin/subjects')
@login_required
@admin_required
def admin_subjects():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, i.short_name as institution_name, u.full_name as instructor_name,
               (SELECT COUNT(*) FROM enrollments WHERE subject_id = s.id) as student_count,
               (SELECT COUNT(*) FROM sessions WHERE subject_id = s.id) as session_count,
               (SELECT COUNT(*) FROM activities a JOIN sessions se ON a.session_id = se.id WHERE se.subject_id = s.id) as activity_count
        FROM subjects s
        LEFT JOIN institutions i ON s.institution_id = i.id
        LEFT JOIN users u ON s.instructor_id = u.id
        ORDER BY s.code, s.section
    ''')
    subjects = [dict(row) for row in cursor.fetchall()]
    cursor.execute('SELECT id, name, short_name FROM institutions WHERE is_active = 1 ORDER BY name')
    institutions = cursor.fetchall()
    cursor.execute('SELECT id, full_name FROM users WHERE role = "instructor" ORDER BY full_name')
    instructors = cursor.fetchall()
    conn.close()
    return render_template('admin_subjects.html', subjects=subjects, institutions=institutions, instructors=instructors)


@app.route('/api/admin/subjects', methods=['POST'])
@login_required
@admin_required
def admin_create_subject():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO subjects (code, name, description, section, day, time_schedule,
                                institution_id, instructor_id, room, credits, max_students, color_theme)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('code'), data.get('name'), data.get('description'), data.get('section'),
              data.get('day'), data.get('time_schedule'), data.get('institution_id'),
              data.get('instructor_id'), data.get('room'), data.get('credits', 3),
              data.get('max_students', 50), data.get('color_theme', 'blue')))
        subject_id = cursor.lastrowid
        # Create 16 sessions
        for i in range(1, 17):
            title = f"Session {i}: {'Lesson' if i <= 12 else 'Project'}"
            cursor.execute('INSERT INTO sessions (subject_id, session_number, title) VALUES (?, ?, ?)',
                         (subject_id, i, title))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/subjects/<int:subject_id>', methods=['PUT'])
@login_required
@admin_required
def admin_update_subject(subject_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE subjects SET code=?, name=?, description=?, section=?, day=?, time_schedule=?,
               institution_id=?, instructor_id=?, room=?, credits=?, max_students=?, color_theme=?
        WHERE id=?
    ''', (data.get('code'), data.get('name'), data.get('description'), data.get('section'),
          data.get('day'), data.get('time_schedule'), data.get('institution_id'),
          data.get('instructor_id'), data.get('room'), data.get('credits', 3),
          data.get('max_students', 50), data.get('color_theme', 'blue'), subject_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN MATERIALS & VIDEOS ==============

@app.route('/admin/materials')
@login_required
@admin_required
def admin_materials():
    conn = get_db()
    cursor = conn.cursor()
    # Get all sessions with their materials info
    cursor.execute('''
        SELECT se.*, s.code as subject_code, s.name as subject_name, s.section,
               (SELECT COUNT(*) FROM activities WHERE session_id = se.id) as activity_count,
               (SELECT COUNT(*) FROM quizzes WHERE session_id = se.id) as quiz_count
        FROM sessions se
        JOIN subjects s ON se.subject_id = s.id
        ORDER BY s.code, s.section, se.session_number
    ''')
    sessions = cursor.fetchall()
    # Get file storage entries
    cursor.execute('''
        SELECT f.*, u.full_name as uploader_name, s.code as subject_code, s.name as subject_name
        FROM file_storage f
        LEFT JOIN users u ON f.uploaded_by = u.id
        LEFT JOIN subjects s ON f.subject_id = s.id
        ORDER BY f.created_at DESC
        LIMIT 100
    ''')
    files = cursor.fetchall()
    cursor.execute('SELECT id, code, name, section FROM subjects ORDER BY code, section')
    subjects = cursor.fetchall()
    conn.close()
    return render_template('admin_materials.html', sessions=sessions, files=files, subjects=subjects)


@app.route('/api/admin/materials/upload', methods=['POST'])
@login_required
@admin_required
def admin_upload_material():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    safe_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"{timestamp}_{safe_name}"
    file_path = os.path.join(app.config['DOCUMENT_FOLDER'], file_name)
    file.save(file_path)
    file_size = os.path.getsize(file_path)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO file_storage (uploaded_by, file_name, original_name, file_path, file_size,
                                 file_type, category, subject_id, description, is_public)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_user.id, file_name, safe_name, file_path, file_size,
          safe_name.rsplit('.', 1)[-1] if '.' in safe_name else 'unknown',
          request.form.get('category', 'general'),
          request.form.get('subject_id') or None,
          request.form.get('description', ''),
          1 if request.form.get('is_public') else 0))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/materials/<int:file_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_material(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT file_path FROM file_storage WHERE id = ?', (file_id,))
    f = cursor.fetchone()
    if f and os.path.exists(f['file_path']):
        os.remove(f['file_path'])
    cursor.execute('DELETE FROM file_storage WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN QUIZZES MANAGEMENT ==============

@app.route('/admin/quizzes')
@login_required
@admin_required
def admin_quizzes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT q.*, se.session_number, s.code as subject_code, s.name as subject_name, s.section,
               (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = q.id) as question_count,
               (SELECT COUNT(*) FROM quiz_attempts WHERE quiz_id = q.id) as attempt_count,
               (SELECT AVG(score) FROM quiz_attempts WHERE quiz_id = q.id) as avg_score
        FROM quizzes q
        JOIN sessions se ON q.session_id = se.id
        JOIN subjects s ON se.subject_id = s.id
        ORDER BY s.code, se.session_number
    ''')
    quizzes = cursor.fetchall()
    # Exams too
    cursor.execute('''
        SELECT e.*, s.code as subject_code, s.name as subject_name, s.section,
               (SELECT COUNT(*) FROM exam_questions WHERE exam_id = e.id) as question_count,
               (SELECT COUNT(*) FROM exam_attempts WHERE exam_id = e.id) as attempt_count,
               (SELECT AVG(score) FROM exam_attempts WHERE exam_id = e.id) as avg_score
        FROM exams e
        JOIN subjects s ON e.subject_id = s.id
        ORDER BY s.code, e.exam_type
    ''')
    exams = cursor.fetchall()
    conn.close()
    return render_template('admin_quizzes.html', quizzes=quizzes, exams=exams)


# ============== ADMIN GRADES OVERVIEW ==============

@app.route('/admin/grades')
@login_required
@admin_required
def admin_grades():
    conn = get_db()
    cursor = conn.cursor()
    # Per-subject grade summary
    cursor.execute('''
        SELECT s.id, s.code, s.name, s.section,
               (SELECT COUNT(*) FROM enrollments WHERE subject_id = s.id) as enrolled,
               (SELECT AVG(sub.score) FROM submissions sub
                JOIN activities a ON sub.activity_id = a.id
                JOIN sessions se ON a.session_id = se.id
                WHERE se.subject_id = s.id AND sub.score IS NOT NULL) as avg_activity_score,
               (SELECT AVG(qa.score) FROM quiz_attempts qa
                JOIN quizzes q ON qa.quiz_id = q.id
                JOIN sessions se ON q.session_id = se.id
                WHERE se.subject_id = s.id AND qa.score IS NOT NULL) as avg_quiz_score,
               (SELECT AVG(ea.score) FROM exam_attempts ea
                JOIN exams e ON ea.exam_id = e.id
                WHERE e.subject_id = s.id AND ea.score IS NOT NULL) as avg_exam_score
        FROM subjects s
        ORDER BY s.code, s.section
    ''')
    grade_summary = cursor.fetchall()
    # Top and bottom performers
    cursor.execute('''
        SELECT u.id, u.full_name, u.section, u.student_id,
               COUNT(DISTINCT sub.activity_id) as activities_done,
               AVG(sub.score) as avg_score
        FROM users u
        JOIN submissions sub ON u.id = sub.student_id
        WHERE u.role = 'student' AND sub.score IS NOT NULL
        GROUP BY u.id
        ORDER BY avg_score DESC
        LIMIT 20
    ''')
    top_students = cursor.fetchall()
    cursor.execute('''
        SELECT u.id, u.full_name, u.section, u.student_id,
               (SELECT COUNT(*) FROM submissions WHERE student_id = u.id AND score IS NOT NULL) as graded,
               (SELECT AVG(score) FROM submissions WHERE student_id = u.id AND score IS NOT NULL) as avg_score
        FROM users u WHERE u.role = 'student'
        AND (SELECT AVG(score) FROM submissions WHERE student_id = u.id AND score IS NOT NULL) IS NOT NULL
        ORDER BY avg_score ASC
        LIMIT 20
    ''')
    at_risk_students = cursor.fetchall()
    conn.close()
    return render_template('admin_grades.html', grade_summary=grade_summary,
                          top_students=top_students, at_risk_students=at_risk_students)


# ============== ADMIN ATTENDANCE OVERVIEW ==============

@app.route('/admin/attendance')
@login_required
@admin_required
def admin_attendance():
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().strftime('%Y-%m-01')

    # Instructor attendance summary
    cursor.execute('''
        SELECT u.id, u.full_name, ip.employee_id,
               (SELECT COUNT(*) FROM instructor_attendance WHERE instructor_id = u.id AND date BETWEEN ? AND ? AND status='present') as present,
               (SELECT COUNT(*) FROM instructor_attendance WHERE instructor_id = u.id AND date BETWEEN ? AND ? AND status='late') as late,
               (SELECT COUNT(*) FROM instructor_attendance WHERE instructor_id = u.id AND date BETWEEN ? AND ? AND status='absent') as absent,
               (SELECT SUM(hours_worked) FROM instructor_attendance WHERE instructor_id = u.id AND date BETWEEN ? AND ?) as total_hours,
               (SELECT time_in FROM instructor_attendance WHERE instructor_id = u.id AND date = ?) as today_in,
               (SELECT time_out FROM instructor_attendance WHERE instructor_id = u.id AND date = ?) as today_out
        FROM users u
        LEFT JOIN instructor_profiles ip ON u.id = ip.user_id
        WHERE u.role = 'instructor'
        ORDER BY u.full_name
    ''', (month_start, today, month_start, today, month_start, today, month_start, today, today, today))
    instructor_attendance = cursor.fetchall()

    # Student attendance
    cursor.execute('''
        SELECT sa.date, s.code as subject_code, s.section,
               SUM(CASE WHEN sa.status = 'present' THEN 1 ELSE 0 END) as present,
               SUM(CASE WHEN sa.status = 'absent' THEN 1 ELSE 0 END) as absent,
               SUM(CASE WHEN sa.status = 'late' THEN 1 ELSE 0 END) as late,
               COUNT(*) as total
        FROM student_attendance sa
        JOIN subjects s ON sa.subject_id = s.id
        WHERE sa.date BETWEEN ? AND ?
        GROUP BY sa.date, sa.subject_id
        ORDER BY sa.date DESC
        LIMIT 50
    ''', (month_start, today))
    student_attendance = cursor.fetchall()

    conn.close()
    return render_template('admin_attendance.html',
        instructor_attendance=instructor_attendance,
        student_attendance=student_attendance,
        today=today, month_start=month_start)


@app.route('/api/admin/student-attendance', methods=['POST'])
@login_required
@admin_required
def admin_record_student_attendance():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    subject_id = data.get('subject_id')
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    records = data.get('records', [])

    for rec in records:
        try:
            cursor.execute('''
                INSERT INTO student_attendance (student_id, subject_id, date, status, recorded_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (rec['student_id'], subject_id, date, rec.get('status', 'present'), current_user.id))
        except Exception:
            cursor.execute('''
                UPDATE student_attendance SET status = ?, recorded_by = ?
                WHERE student_id = ? AND subject_id = ? AND date = ?
            ''', (rec.get('status', 'present'), current_user.id, rec['student_id'], subject_id, date))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN PAYMENTS & TUITION ==============

@app.route('/admin/payments')
@login_required
@admin_required
def admin_payments():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sp.*, u.full_name, u.student_id as sid, u.section, i.short_name as institution_name
        FROM student_payments sp
        JOIN users u ON sp.student_id = u.id
        LEFT JOIN institutions i ON sp.institution_id = i.id
        ORDER BY sp.created_at DESC
        LIMIT 200
    ''')
    payments = cursor.fetchall()
    # Summary stats
    cursor.execute('SELECT SUM(amount) FROM student_payments')
    total_billed = cursor.fetchone()[0] or 0
    cursor.execute('SELECT SUM(amount_paid) FROM student_payments WHERE status IN ("paid","partial")')
    total_collected = cursor.fetchone()[0] or 0
    cursor.execute('SELECT SUM(balance) FROM student_payments WHERE status IN ("pending","partial","overdue")')
    total_outstanding = cursor.fetchone()[0] or 0
    cursor.execute('SELECT COUNT(*) FROM student_payments WHERE status = "overdue"')
    overdue_count = cursor.fetchone()[0]
    # Tuition plans
    cursor.execute('''
        SELECT tp.*, i.short_name as institution_name
        FROM tuition_plans tp
        LEFT JOIN institutions i ON tp.institution_id = i.id
        WHERE tp.is_active = 1
        ORDER BY tp.name
    ''')
    tuition_plans = cursor.fetchall()
    cursor.execute('SELECT id, name, short_name FROM institutions WHERE is_active = 1 ORDER BY name')
    institutions = cursor.fetchall()
    cursor.execute('''SELECT id, full_name, student_id, section FROM users WHERE role = 'student' AND status != 'inactive' ORDER BY full_name''')
    students = cursor.fetchall()
    conn.close()
    return render_template('admin_payments.html', payments=payments,
        total_billed=total_billed, total_collected=total_collected,
        total_outstanding=total_outstanding, overdue_count=overdue_count,
        tuition_plans=tuition_plans, institutions=institutions, students=students)


@app.route('/api/admin/payments', methods=['POST'])
@login_required
@admin_required
def admin_create_payment():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    amount = float(data.get('amount', 0))
    cursor.execute('''
        INSERT INTO student_payments (student_id, institution_id, payment_type, description,
                                     amount, balance, due_date, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    ''', (data.get('student_id'), data.get('institution_id'), data.get('payment_type', 'tuition'),
          data.get('description'), amount, amount, data.get('due_date'), current_user.id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/payments/<int:payment_id>/pay', methods=['POST'])
@login_required
@admin_required
def admin_record_payment(payment_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    amount_paid = float(data.get('amount_paid', 0))
    cursor.execute('SELECT * FROM student_payments WHERE id = ?', (payment_id,))
    payment = cursor.fetchone()
    if not payment:
        conn.close()
        return jsonify({'success': False, 'error': 'Payment not found'})
    new_paid = (payment['amount_paid'] or 0) + amount_paid
    new_balance = payment['amount'] - new_paid
    status = 'paid' if new_balance <= 0 else 'partial'
    cursor.execute('''
        UPDATE student_payments SET amount_paid = ?, balance = ?, status = ?,
               payment_method = ?, reference_number = ?, paid_at = ?
        WHERE id = ?
    ''', (new_paid, max(0, new_balance), status,
          data.get('payment_method'), data.get('reference_number'),
          datetime.now().strftime('%Y-%m-%d %H:%M:%S'), payment_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/tuition-plans', methods=['POST'])
@login_required
@admin_required
def admin_create_tuition_plan():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tuition_plans (institution_id, name, amount, frequency, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (data.get('institution_id'), data.get('name'), data.get('amount', 0),
          data.get('frequency', 'semester'), data.get('description')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN FILES MANAGEMENT ==============

@app.route('/admin/files')
@login_required
@admin_required
def admin_files():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, u.full_name as uploader_name, s.code as subject_code, s.name as subject_name
        FROM file_storage f
        LEFT JOIN users u ON f.uploaded_by = u.id
        LEFT JOIN subjects s ON f.subject_id = s.id
        ORDER BY f.created_at DESC
    ''')
    files = cursor.fetchall()
    # Storage summary
    cursor.execute('SELECT SUM(file_size) FROM file_storage')
    total_size = cursor.fetchone()[0] or 0
    cursor.execute('SELECT COUNT(*) FROM file_storage')
    total_files = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT category) FROM file_storage')
    total_categories = cursor.fetchone()[0]
    cursor.execute('SELECT id, code, name, section FROM subjects ORDER BY code, section')
    subjects = cursor.fetchall()
    conn.close()
    return render_template('admin_files.html', files=files, total_size=total_size,
                          total_files=total_files, total_categories=total_categories, subjects=subjects)


@app.route('/admin/files/download/<int:file_id>')
@login_required
def admin_download_file(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM file_storage WHERE id = ?', (file_id,))
    f = cursor.fetchone()
    if not f:
        flash('File not found.', 'error')
        return redirect(url_for('admin_files'))
    cursor.execute('UPDATE file_storage SET download_count = download_count + 1 WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    return send_file(f['file_path'], as_attachment=True, download_name=f['original_name'])


# ============== ADMIN SUBSCRIPTIONS ==============

@app.route('/admin/subscriptions')
@login_required
@admin_required
def admin_subscriptions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subscription_plans ORDER BY price_monthly')
    plans = [dict(row) for row in cursor.fetchall()]
    cursor.execute('''
        SELECT i.*, sp.name as plan_name, sp.price_monthly,
               (SELECT COUNT(*) FROM users WHERE institution_id = i.id AND role = 'student') as student_count,
               (SELECT COUNT(*) FROM users WHERE institution_id = i.id AND role = 'instructor') as instructor_count
        FROM institutions i
        LEFT JOIN subscription_plans sp ON i.plan = sp.name
        WHERE i.is_active = 1
        ORDER BY i.name
    ''')
    institutions = cursor.fetchall()
    # Revenue
    cursor.execute('SELECT SUM(price_monthly) FROM subscription_plans sp JOIN institutions i ON i.plan = sp.name WHERE i.is_active = 1')
    monthly_revenue = cursor.fetchone()[0] or 0
    conn.close()
    return render_template('admin_subscriptions.html', plans=plans, institutions=institutions, monthly_revenue=monthly_revenue)


@app.route('/api/admin/subscriptions', methods=['POST'])
@login_required
@admin_required
def admin_create_plan():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO subscription_plans (name, price_monthly, price_yearly, max_students, max_instructors, max_subjects, features)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('name'), data.get('price_monthly', 0), data.get('price_yearly', 0),
              data.get('max_students', 100), data.get('max_instructors', 5),
              data.get('max_subjects', 20), data.get('features', '')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/subscriptions/<int:plan_id>', methods=['PUT'])
@login_required
@admin_required
def admin_update_plan(plan_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE subscription_plans SET name=?, price_monthly=?, price_yearly=?, max_students=?,
               max_instructors=?, max_subjects=?, features=?, is_active=?
        WHERE id=?
    ''', (data.get('name'), data.get('price_monthly', 0), data.get('price_yearly', 0),
          data.get('max_students'), data.get('max_instructors'), data.get('max_subjects'),
          data.get('features'), data.get('is_active', 1), plan_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ============== ADMIN TEACHER PROFILES ==============

@app.route('/admin/teacher-profiles')
@login_required
@admin_required
def admin_teacher_profiles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.*, ip.*, i.name as institution_name, i.short_name as inst_short,
               d.name as department_name,
               (SELECT COUNT(*) FROM subjects WHERE instructor_id = u.id) as subject_count,
               (SELECT COUNT(*) FROM instructor_attendance WHERE instructor_id = u.id AND status = 'present') as total_present,
               (SELECT SUM(hours_worked) FROM instructor_attendance WHERE instructor_id = u.id) as total_hours,
               (SELECT SUM(net_pay) FROM instructor_payroll WHERE instructor_id = u.id AND status = 'paid') as total_earned
        FROM users u
        LEFT JOIN instructor_profiles ip ON u.id = ip.user_id
        LEFT JOIN institutions i ON ip.institution_id = i.id
        LEFT JOIN departments d ON ip.department_id = d.id
        WHERE u.role = 'instructor'
        ORDER BY u.full_name
    ''')
    teachers = [dict(row) for row in cursor.fetchall()]
    cursor.execute('SELECT id, name, short_name FROM institutions WHERE is_active = 1 ORDER BY name')
    institutions = cursor.fetchall()
    cursor.execute('SELECT id, name, institution_id FROM departments ORDER BY name')
    departments = cursor.fetchall()
    conn.close()
    return render_template('admin_teacher_profiles.html', teachers=teachers,
                          institutions=institutions, departments=departments)


@app.route('/api/admin/teacher-profile/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_teacher_profile(user_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    # Update user basic info
    cursor.execute('''
        UPDATE users SET full_name=?, email=?, contact_number=?, institution_id=?
        WHERE id=? AND role='instructor'
    ''', (data.get('full_name'), data.get('email'), data.get('contact_number'),
          data.get('institution_id'), user_id))
    # Upsert profile
    cursor.execute('SELECT id FROM instructor_profiles WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE instructor_profiles SET institution_id=?, department_id=?, employee_id=?,
                   hire_date=?, contract_type=?, salary_rate=?, salary_frequency=?,
                   tax_id=?, bank_account=?, emergency_contact=?, emergency_phone=?
            WHERE user_id=?
        ''', (data.get('institution_id'), data.get('department_id'), data.get('employee_id'),
              data.get('hire_date'), data.get('contract_type', 'full-time'),
              data.get('salary_rate', 0), data.get('salary_frequency', 'monthly'),
              data.get('tax_id'), data.get('bank_account'),
              data.get('emergency_contact'), data.get('emergency_phone'), user_id))
    else:
        cursor.execute('''
            INSERT INTO instructor_profiles (user_id, institution_id, department_id, employee_id,
                   hire_date, contract_type, salary_rate, salary_frequency, tax_id, bank_account,
                   emergency_contact, emergency_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, data.get('institution_id'), data.get('department_id'), data.get('employee_id'),
              data.get('hire_date'), data.get('contract_type', 'full-time'),
              data.get('salary_rate', 0), data.get('salary_frequency', 'monthly'),
              data.get('tax_id'), data.get('bank_account'),
              data.get('emergency_contact'), data.get('emergency_phone')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=3000)
