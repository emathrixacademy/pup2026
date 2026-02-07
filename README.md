# Classroom Learning Management System (LMS)

A simple Flask-based LMS for managing classroom activities, quizzes, and exams with auto-grading.

## Tech Stack
- **Backend**: Python Flask
- **Database**: SQLite (single file)
- **Frontend**: HTML/CSS/JavaScript (custom CSS only)

## Features

### User Roles
- **Instructor**: Full access to manage students, create quizzes/exams, grade activities
- **Student**: Take quizzes/exams, submit activities, view grades

### Student Management
- Add students one-by-one via form
- Bulk upload via Excel (.xlsx) or CSV file
- Required columns: `student_id`, `username`, `password`, `full_name`, `section`

### Subjects (7 Classes)
| Day | Time | Subject | Section |
|-----|------|---------|---------|
| Tuesday | 1:00PM-6:00PM | Applications Development and Emerging Technologies | BSIT-SR 3-1 |
| Tuesday | 7:30AM-12:30PM | Applications Development and Emerging Technologies | BSIT-SR 3-2 |
| Wednesday | 7:30AM-12:30PM | Network Administration | BSIT-SR 2-3 |
| Thursday | 7:30AM-9:30AM | Network Administration | BSIT-SR 2-1 |
| Thursday | 1:00PM-6:00PM | Network Administration | BSIT-SR 2-2 |
| Saturday | 7:30AM-1:30PM | Computer Networks and Security | BSCPE-BN 3-1 |
| Saturday | 2:00PM-8:00PM | Embedded Systems | BSCPE-BN 4-1 |

Each subject has 16 sessions (Sessions 1-12: Lessons, Sessions 13-16: Project)

### Quiz System
- Create quizzes with answer keys
- Question types: Multiple Choice, True/False, Short Answer
- Auto-grading based on answer keys
- Timer support

### Exam System
- Midterm and Final exams
- Same question types as quizzes
- Answer keys for auto-grading
- Timer support

### Activities
- 3 activities per session
- Student submissions
- Manual grading with feedback by instructor

### Grade Calculation
| Component | Weight |
|-----------|--------|
| Quizzes | 20% |
| Activities | 40% |
| Midterm Exam | 20% |
| Final Exam | 20% |

## Project Structure
```
classroom_lms/
├── app.py              # Main Flask application
├── database.py         # SQLite database setup & initialization
├── requirements.txt    # Python dependencies
├── README.md
├── classroom_lms.db    # SQLite database (auto-created)
├── uploads/            # Bulk upload files (temporary)
├── static/
│   ├── css/
│   │   └── style.css   # Custom styling
│   └── js/
│       └── main.js     # JavaScript functions
└── templates/
    ├── base.html               # Base layout
    ├── login.html              # Login page
    ├── dashboard.html          # Instructor dashboard
    ├── students.html           # Student management
    ├── subjects.html           # Subject list
    ├── sessions.html           # Session list
    ├── activities.html         # Activities management
    ├── submissions.html        # View/grade submissions
    ├── quiz.html               # Quiz management
    ├── quiz_take.html          # Student quiz interface
    ├── exams.html              # Exam list
    ├── exam_questions.html     # Exam question management
    ├── exam_take.html          # Student exam interface
    ├── grades.html             # Grade book
    ├── student_grades.html     # Individual student grades
    ├── student_dashboard.html  # Student home
    ├── student_subject.html    # Student subject view
    └── student_activities.html # Student activity submission
```

## Database Tables
1. **users** - User accounts (instructor/students)
2. **subjects** - 4 preset subjects
3. **sessions** - 16 sessions per subject
4. **activities** - Activities per session
5. **submissions** - Student activity submissions
6. **quizzes** - Quiz definitions
7. **quiz_questions** - Questions with answer keys
8. **quiz_attempts** - Student quiz attempts
9. **exams** - Exam definitions (midterm/final)
10. **exam_questions** - Exam questions with answer keys
11. **exam_attempts** - Student exam attempts
12. **enrollments** - Student-subject relationships

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser to `http://localhost:5000`

## Default Login
- **Instructor**: `instructor` / `instructor123`

## Design
- Background: White (#FFFFFF)
- Primary accent: Sky Blue (#0EA5E9)
- Light backgrounds: #E0F2FE
- Text: #374151 (gray-700)
- Borders: #E5E7EB (gray-200)
- Font: Inter or system sans-serif

## Bulk Upload Template
Excel/CSV file should have these columns:
| student_id | username | password | full_name | section |
|------------|----------|----------|-----------|---------|
| 2024-0001 | juan.cruz | pass123 | Juan Cruz | A |
| 2024-0002 | maria.santos | pass456 | Maria Santos | A |
