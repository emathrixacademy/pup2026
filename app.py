from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PHOTO_FOLDER'] = 'static/uploads/photos'
app.config['DOCUMENT_FOLDER'] = 'static/uploads/documents'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload folders exist
os.makedirs(app.config['PHOTO_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOCUMENT_FOLDER'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(UserMixin):
    def __init__(self, id, username, full_name, role, student_id=None, section=None, photo='default.png',
                 profile_completed=1, email=None, github_account=None, railway_account=None,
                 messenger=None, pup_id_photo=None, cor_photo=None, contact_number=None,
                 programming_languages=None, databases_known=None, hosting_platforms=None, other_tools=None):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.role = role
        self.student_id = student_id
        self.section = section
        self.photo = photo or 'default.png'
        self.profile_completed = profile_completed
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
            user['other_tools'] if 'other_tools' in keys else None
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
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "student"')
    student_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM sessions')
    session_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM activities')
    activity_count = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM quizzes')
    quiz_count = cursor.fetchone()['count']
    conn.close()

    stats = {
        'students': student_count,
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
    conn.close()

    return render_template('students.html', students=students_list, subjects=subjects)

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
    file_path = None

    # Handle file upload
    if 'submission_file' in request.files:
        file = request.files['submission_file']
        if file and file.filename:
            # Create activity-specific folder
            activity_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'activity_submissions', f"activity_{activity_id}")
            os.makedirs(activity_folder, exist_ok=True)

            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            safe_filename = secure_filename(file.filename)
            filename = f"student_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_filename}"
            file.save(os.path.join(activity_folder, filename))
            file_path = f"activity_{activity_id}/{filename}"

    # Check if already submitted
    cursor.execute('SELECT id FROM submissions WHERE activity_id = ? AND student_id = ?',
                   (activity_id, current_user.id))
    existing = cursor.fetchone()

    if existing:
        if file_path:
            cursor.execute('''
                UPDATE submissions SET content = ?, file_path = ?, submitted_at = CURRENT_TIMESTAMP
                WHERE activity_id = ? AND student_id = ?
            ''', (content, file_path, activity_id, current_user.id))
        else:
            cursor.execute('''
                UPDATE submissions SET content = ?, submitted_at = CURRENT_TIMESTAMP
                WHERE activity_id = ? AND student_id = ?
            ''', (content, activity_id, current_user.id))
    else:
        cursor.execute('''
            INSERT INTO submissions (activity_id, student_id, content, file_path)
            VALUES (?, ?, ?, ?)
        ''', (activity_id, current_user.id, content, file_path))

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
        flash('Session not found', 'error')
        return redirect(url_for('dashboard'))

    # Check visibility for students
    if current_user.role == 'student' and not session_data['is_visible']:
        flash('This lesson is not yet available.', 'warning')
        return redirect(url_for('student_dashboard'))

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
        final_project = None
        final_project_pending = False
        for exam in exams:
            if exam['exam_type'] == 'midterm':
                if exam['score_visible']:
                    midterm = exam['score']
                else:
                    midterm_pending = True
            elif exam['exam_type'] == 'final':
                if exam['score_visible']:
                    final_project = exam['score']
                else:
                    final_project_pending = True

        # Calculate weighted grade based on subject-specific weights
        weighted = (
            (quiz_avg * weights['quizzes']) +
            (activity_avg * weights['activities']) +
            ((midterm or 0) * weights['midterm']) +
            ((final_project or 0) * weights['final']) +
            ((final_project or 0) * weights['final_project'])
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
            'final_project': final_project,
            'final_project_pending': final_project_pending,
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
    # Only get subjects the student is enrolled in
    cursor.execute('''
        SELECT s.* FROM subjects s
        INNER JOIN enrollments e ON s.id = e.subject_id
        WHERE e.student_id = ?
        ORDER BY s.code, s.section
    ''', (current_user.id,))
    subjects = cursor.fetchall()
    conn.close()
    return render_template('student_dashboard.html', subjects=subjects)

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

    # Get available quizzes (only visible quizzes from visible sessions)
    cursor.execute('''
        SELECT q.*, s.session_number
        FROM quizzes q
        JOIN sessions s ON q.session_id = s.id
        WHERE s.subject_id = ? AND s.is_visible = 1 AND q.is_visible = 1
    ''', (subject_id,))
    quizzes = cursor.fetchall()

    # Get available exams (only visible exams)
    cursor.execute('SELECT * FROM exams WHERE subject_id = ? AND is_visible = 1', (subject_id,))
    exams = cursor.fetchall()

    conn.close()
    return render_template('student_subject.html', subject=subject, sessions=sessions, quizzes=quizzes, exams=exams)

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
    return render_template('student_activities.html', session=session_data, activities=activities, submissions=submissions)

@app.route('/student/my-grades')
@login_required
def my_grades():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))
    return redirect(url_for('student_grades', student_id=current_user.id))

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
