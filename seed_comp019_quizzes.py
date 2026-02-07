"""
Seed COMP019 quizzes with answer keys for all 12 sessions.
Each session has 10 questions.
"""

import sqlite3
import json

DATABASE = 'classroom_lms.db'

def seed_comp019_quizzes():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get ALL COMP019 subjects
    cursor.execute("SELECT id, section FROM subjects WHERE code = 'COMP019'")
    subjects = cursor.fetchall()
    if not subjects:
        print("COMP019 subjects not found!")
        return

    print(f"Found {len(subjects)} COMP019 subjects")

    # Quiz data for all 12 sessions
    quizzes_data = {
        1: {
            "title": "Session 1: Introduction to Full-Stack Python Development",
            "questions": [
                {
                    "text": "What does \"full-stack\" development mean?",
                    "type": "multiple_choice",
                    "options": ["Only frontend development", "Only backend development", "Both frontend and backend development", "Database development only"],
                    "answer": "C",
                    "explanation": "Full-stack means working on both frontend (client-side) and backend (server-side)"
                },
                {
                    "text": "Which command creates a Python virtual environment?",
                    "type": "multiple_choice",
                    "options": ["pip install venv", "python -m venv venv", "create venv python", "virtualenv --create"],
                    "answer": "B",
                    "explanation": "python -m venv venv creates a virtual environment named 'venv'"
                },
                {
                    "text": "In Django's MVT architecture, what does the \"V\" stand for?",
                    "type": "multiple_choice",
                    "options": ["Virtual", "View", "Variable", "Vendor"],
                    "answer": "B",
                    "explanation": "MVT = Model-View-Template; View handles business logic in Django"
                },
                {
                    "text": "A virtual environment isolates project dependencies from the system Python installation.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Virtual environments isolate dependencies per project"
                },
                {
                    "text": "Which file lists all Python package dependencies for a project?",
                    "type": "multiple_choice",
                    "options": ["packages.json", "dependencies.txt", "requirements.txt", "modules.list"],
                    "answer": "C",
                    "explanation": "requirements.txt is the standard file for listing Python dependencies"
                },
                {
                    "text": "What is the purpose of the backend in a full-stack application?",
                    "type": "multiple_choice",
                    "options": ["Display the user interface", "Handle server-side logic and database operations", "Style the web pages", "Create animations"],
                    "answer": "B",
                    "explanation": "Backend handles server logic, database operations, and business rules"
                },
                {
                    "text": "To activate a virtual environment on Windows, you run venv\\Scripts\\____________",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "activate",
                    "explanation": "The full command is venv\\Scripts\\activate"
                },
                {
                    "text": "Which of the following is NOT a component of full-stack development?",
                    "type": "multiple_choice",
                    "options": ["Frontend (UI)", "Backend (Server)", "Database", "Printer Driver"],
                    "answer": "D",
                    "explanation": "Printer drivers are not part of web application development"
                },
                {
                    "text": "Django is a Python framework used for building web applications.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Django is a popular Python web framework"
                },
                {
                    "text": "What command installs packages from requirements.txt?",
                    "type": "multiple_choice",
                    "options": ["python install -r requirements.txt", "pip install -r requirements.txt", "pip requirements install", "install pip requirements.txt"],
                    "answer": "B",
                    "explanation": "pip install -r requirements.txt installs all listed packages"
                }
            ]
        },
        2: {
            "title": "Session 2: Django Fundamentals",
            "questions": [
                {
                    "text": "What command creates a new Django project named \"mysite\"?",
                    "type": "multiple_choice",
                    "options": ["django create mysite", "django-admin startproject mysite", "python manage.py newproject mysite", "pip install django mysite"],
                    "answer": "B",
                    "explanation": "django-admin startproject mysite creates a new Django project"
                },
                {
                    "text": "Which file contains the main configuration settings for a Django project?",
                    "type": "multiple_choice",
                    "options": ["config.py", "settings.py", "manage.py", "urls.py"],
                    "answer": "B",
                    "explanation": "settings.py contains all project configuration"
                },
                {
                    "text": "In Django's MVT pattern, what is responsible for database structure?",
                    "type": "multiple_choice",
                    "options": ["Model", "View", "Template", "Controller"],
                    "answer": "A",
                    "explanation": "Models define database structure using Python classes"
                },
                {
                    "text": "What command creates a new Django app called \"blog\"?",
                    "type": "multiple_choice",
                    "options": ["python manage.py startapp blog", "django-admin createapp blog", "python manage.py newapp blog", "django startapp blog"],
                    "answer": "A",
                    "explanation": "python manage.py startapp blog creates a new app"
                },
                {
                    "text": "Templates in Django are HTML files that can include dynamic content using template tags.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Templates use {{ }} and {% %} for dynamic content"
                },
                {
                    "text": "Which command applies database migrations in Django?",
                    "type": "multiple_choice",
                    "options": ["python manage.py makemigrations", "python manage.py migrate", "python manage.py syncdb", "python manage.py dbupdate"],
                    "answer": "B",
                    "explanation": "migrate applies migrations; makemigrations creates them"
                },
                {
                    "text": "In Django templates, to display a variable called \"name\", you use {{ ________ }}",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "name",
                    "explanation": "Variables are displayed using {{ variable_name }}"
                },
                {
                    "text": "What is the default database that Django uses?",
                    "type": "multiple_choice",
                    "options": ["MySQL", "PostgreSQL", "SQLite", "MongoDB"],
                    "answer": "C",
                    "explanation": "Django uses SQLite by default (db.sqlite3)"
                },
                {
                    "text": "Which Django template tag is used for loops?",
                    "type": "multiple_choice",
                    "options": ["{% loop %}", "{% for %}", "{% each %}", "{% iterate %}"],
                    "answer": "B",
                    "explanation": "{% for item in items %}...{% endfor %}"
                },
                {
                    "text": "What command starts the Django development server?",
                    "type": "multiple_choice",
                    "options": ["python manage.py start", "python manage.py runserver", "django run", "python manage.py serve"],
                    "answer": "B",
                    "explanation": "python manage.py runserver starts the dev server on port 8000"
                }
            ]
        },
        3: {
            "title": "Session 3: Django Advanced Features",
            "questions": [
                {
                    "text": "Which Django class is used to create forms from models automatically?",
                    "type": "multiple_choice",
                    "options": ["AutoForm", "ModelForm", "FormModel", "DatabaseForm"],
                    "answer": "B",
                    "explanation": "ModelForm automatically creates form fields from model"
                },
                {
                    "text": "What template tag is required in Django forms to prevent CSRF attacks?",
                    "type": "multiple_choice",
                    "options": ["{% secure %}", "{% csrf_token %}", "{% form_protect %}", "{% security %}"],
                    "answer": "B",
                    "explanation": "{% csrf_token %} prevents Cross-Site Request Forgery"
                },
                {
                    "text": "The @login_required decorator restricts view access to authenticated users only.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "@login_required redirects unauthenticated users to login"
                },
                {
                    "text": "Which file is used to register models in Django admin?",
                    "type": "multiple_choice",
                    "options": ["models.py", "admin.py", "views.py", "register.py"],
                    "answer": "B",
                    "explanation": "admin.py is where you register models for the admin interface"
                },
                {
                    "text": "What command creates a superuser for Django admin?",
                    "type": "multiple_choice",
                    "options": ["python manage.py createadmin", "python manage.py createsuperuser", "python manage.py addadmin", "python manage.py superuser"],
                    "answer": "B",
                    "explanation": "createsuperuser creates an admin account"
                },
                {
                    "text": "In Django admin, what does list_display customize?",
                    "type": "multiple_choice",
                    "options": ["The login page", "The columns shown in the list view", "The database structure", "The form fields"],
                    "answer": "B",
                    "explanation": "list_display specifies which fields appear as columns"
                },
                {
                    "text": "To render a form with paragraph tags, use {{ form.________ }}",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "as_p",
                    "explanation": "{{ form.as_p }} renders form fields in paragraph tags"
                },
                {
                    "text": "Which authentication view handles user login in Django?",
                    "type": "multiple_choice",
                    "options": ["AuthView", "LoginView", "UserLogin", "SignInView"],
                    "answer": "B",
                    "explanation": "LoginView is Django's built-in class-based login view"
                },
                {
                    "text": "What does form.is_valid() do?",
                    "type": "multiple_choice",
                    "options": ["Saves the form to database", "Checks if submitted data passes validation", "Renders the form", "Clears the form"],
                    "answer": "B",
                    "explanation": "is_valid() validates form data and returns True/False"
                },
                {
                    "text": "Middleware in Django processes requests before they reach the view.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Middleware processes requests/responses globally"
                }
            ]
        },
        4: {
            "title": "Session 4: Mobile App Development with Kivy",
            "questions": [
                {
                    "text": "Kivy is a Python framework primarily used for:",
                    "type": "multiple_choice",
                    "options": ["Web development only", "Cross-platform mobile and desktop applications", "Machine learning", "Database management"],
                    "answer": "B",
                    "explanation": "Kivy creates cross-platform apps for mobile and desktop"
                },
                {
                    "text": "What is the main class that every Kivy application must inherit from?",
                    "type": "multiple_choice",
                    "options": ["Application", "KivyApp", "App", "MainApp"],
                    "answer": "C",
                    "explanation": "All Kivy apps inherit from the App class"
                },
                {
                    "text": "Which method must be overridden in a Kivy App class to build the UI?",
                    "type": "multiple_choice",
                    "options": ["create()", "init()", "build()", "start()"],
                    "answer": "C",
                    "explanation": "build() method returns the root widget of the app"
                },
                {
                    "text": "BoxLayout arranges widgets either horizontally or vertically.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "BoxLayout has orientation property: 'horizontal' or 'vertical'"
                },
                {
                    "text": "What is the file extension for Kivy language files?",
                    "type": "multiple_choice",
                    "options": [".kivy", ".kv", ".kvl", ".ui"],
                    "answer": "B",
                    "explanation": "Kivy language files use .kv extension"
                },
                {
                    "text": "Which widget is used for text input in Kivy?",
                    "type": "multiple_choice",
                    "options": ["TextField", "TextBox", "TextInput", "InputField"],
                    "answer": "C",
                    "explanation": "TextInput is the widget for text entry"
                },
                {
                    "text": "To make a TextInput show dots instead of characters (for passwords), set password=________",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "True",
                    "explanation": "password=True masks input characters"
                },
                {
                    "text": "In KV language, how do you reference a method in the Python class?",
                    "type": "multiple_choice",
                    "options": ["call: self.method()", "on_press: root.method()", "onclick: app.method()", "run: method()"],
                    "answer": "B",
                    "explanation": "root.method() calls methods in the root widget class"
                },
                {
                    "text": "Which layout arranges widgets in rows and columns?",
                    "type": "multiple_choice",
                    "options": ["BoxLayout", "GridLayout", "FloatLayout", "StackLayout"],
                    "answer": "B",
                    "explanation": "GridLayout arranges widgets in a grid of rows and columns"
                },
                {
                    "text": "The KV file name must match the App class name (without \"App\" suffix) in lowercase.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "MyApp class uses my.kv file automatically"
                }
            ]
        },
        5: {
            "title": "Session 5: Local Database with SQLite",
            "questions": [
                {
                    "text": "SQLite is a:",
                    "type": "multiple_choice",
                    "options": ["Server-based database", "File-based database", "Cloud-only database", "Memory-only database"],
                    "answer": "B",
                    "explanation": "SQLite stores the entire database in a single file"
                },
                {
                    "text": "What Python module is used to work with SQLite?",
                    "type": "multiple_choice",
                    "options": ["mysql", "sqlite3", "sqldb", "pysqlite"],
                    "answer": "B",
                    "explanation": "sqlite3 is Python's built-in module for SQLite"
                },
                {
                    "text": "Which SQL command retrieves data from a database?",
                    "type": "multiple_choice",
                    "options": ["GET", "FETCH", "SELECT", "RETRIEVE"],
                    "answer": "C",
                    "explanation": "SELECT retrieves data from tables"
                },
                {
                    "text": "In Django ORM, what does Model.objects.all() return?",
                    "type": "multiple_choice",
                    "options": ["A single object", "All objects of that model (QuerySet)", "The first object", "None"],
                    "answer": "B",
                    "explanation": "all() returns a QuerySet containing all objects"
                },
                {
                    "text": "Django ORM allows you to interact with the database without writing raw SQL.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "ORM translates Python code to SQL automatically"
                },
                {
                    "text": "Which SQL command adds new data to a table?",
                    "type": "multiple_choice",
                    "options": ["ADD", "INSERT INTO", "CREATE", "PUT"],
                    "answer": "B",
                    "explanation": "INSERT INTO adds new records to a table"
                },
                {
                    "text": "In Django ORM, to get a single object by ID, use Model.objects.________(id=1)",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "get",
                    "explanation": "Model.objects.get(id=1) retrieves a single object"
                },
                {
                    "text": "What does CRUD stand for?",
                    "type": "multiple_choice",
                    "options": ["Create, Read, Update, Delete", "Copy, Rename, Undo, Delete", "Create, Rename, Upload, Download", "Copy, Read, Update, Display"],
                    "answer": "A",
                    "explanation": "CRUD = Create, Read, Update, Delete operations"
                },
                {
                    "text": "Which Django ORM method filters objects based on conditions?",
                    "type": "multiple_choice",
                    "options": ["where()", "filter()", "find()", "search()"],
                    "answer": "B",
                    "explanation": "filter() returns objects matching the conditions"
                },
                {
                    "text": "The default SQLite database file in Django is named \"db.sqlite3\".",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Django creates db.sqlite3 by default"
                }
            ]
        },
        6: {
            "title": "Session 6: Cloud Database with PostgreSQL",
            "questions": [
                {
                    "text": "Which Python package is used to connect Django to PostgreSQL?",
                    "type": "multiple_choice",
                    "options": ["postgres", "psycopg2", "pgconnect", "postgresql-python"],
                    "answer": "B",
                    "explanation": "psycopg2 (or psycopg2-binary) is the PostgreSQL adapter"
                },
                {
                    "text": "What is the main advantage of PostgreSQL over SQLite?",
                    "type": "multiple_choice",
                    "options": ["It's smaller", "It supports multiple concurrent users and better performance", "It's easier to install", "It doesn't require configuration"],
                    "answer": "B",
                    "explanation": "PostgreSQL handles concurrent users and scales better"
                },
                {
                    "text": "Environment variables should be used to store sensitive data like database passwords.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Never hardcode passwords; use environment variables"
                },
                {
                    "text": "What package helps load environment variables from a .env file?",
                    "type": "multiple_choice",
                    "options": ["dotenv", "python-dotenv", "envloader", "loadenv"],
                    "answer": "B",
                    "explanation": "python-dotenv loads variables from .env files"
                },
                {
                    "text": "In Django settings, what is the database ENGINE value for PostgreSQL?",
                    "type": "multiple_choice",
                    "options": ["django.db.backends.postgres", "django.db.backends.postgresql", "django.db.backends.pg", "postgresql.engine"],
                    "answer": "B",
                    "explanation": "django.db.backends.postgresql is the correct engine"
                },
                {
                    "text": "To load the database URL in settings.py, use os.getenv('____________')",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "DATABASE_URL",
                    "explanation": "os.getenv('DATABASE_URL') retrieves the database connection string"
                },
                {
                    "text": "Which file should NEVER be committed to Git because it contains secrets?",
                    "type": "multiple_choice",
                    "options": ["settings.py", "requirements.txt", ".env", "manage.py"],
                    "answer": "C",
                    "explanation": ".env contains secrets and must be in .gitignore"
                },
                {
                    "text": "What command applies existing migrations to a new database?",
                    "type": "multiple_choice",
                    "options": ["python manage.py makemigrations", "python manage.py migrate", "python manage.py syncdb", "python manage.py dbsync"],
                    "answer": "B",
                    "explanation": "migrate applies migrations to the database"
                },
                {
                    "text": "You can use the same Django models with both SQLite and PostgreSQL.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Django ORM abstracts database differences"
                },
                {
                    "text": "Which is NOT a cloud PostgreSQL provider?",
                    "type": "multiple_choice",
                    "options": ["Supabase", "Neon", "Railway", "GitHub Pages"],
                    "answer": "D",
                    "explanation": "GitHub Pages is for static websites, not databases"
                }
            ]
        },
        7: {
            "title": "Session 7: REST API with Django REST Framework",
            "questions": [
                {
                    "text": "What does REST stand for?",
                    "type": "multiple_choice",
                    "options": ["Remote Execution Service Transfer", "Representational State Transfer", "Request-Response State Transfer", "Remote Server Technology"],
                    "answer": "B",
                    "explanation": "REST = Representational State Transfer"
                },
                {
                    "text": "In DRF, what converts model instances to JSON and vice versa?",
                    "type": "multiple_choice",
                    "options": ["Converter", "Parser", "Serializer", "Transformer"],
                    "answer": "C",
                    "explanation": "Serializers convert between Python objects and JSON"
                },
                {
                    "text": "Which HTTP method is typically used to CREATE a new resource?",
                    "type": "multiple_choice",
                    "options": ["GET", "POST", "PUT", "DELETE"],
                    "answer": "B",
                    "explanation": "POST creates new resources"
                },
                {
                    "text": "ModelSerializer automatically creates serializer fields based on the model.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "ModelSerializer generates fields from model definition"
                },
                {
                    "text": "What DRF class provides full CRUD functionality with minimal code?",
                    "type": "multiple_choice",
                    "options": ["APIView", "GenericView", "ModelViewSet", "CRUDView"],
                    "answer": "C",
                    "explanation": "ModelViewSet provides list, create, retrieve, update, delete"
                },
                {
                    "text": "Which HTTP method is used to READ/retrieve data?",
                    "type": "multiple_choice",
                    "options": ["GET", "POST", "PUT", "PATCH"],
                    "answer": "A",
                    "explanation": "GET retrieves/reads data without modifying it"
                },
                {
                    "text": "To protect an API view, use permission_classes = [________]",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "IsAuthenticated",
                    "explanation": "permission_classes = [IsAuthenticated] restricts to logged-in users"
                },
                {
                    "text": "What does Token Authentication require in the HTTP header?",
                    "type": "multiple_choice",
                    "options": ["Token: <token>", "Authorization: Token <token>", "Auth: <token>", "Bearer: <token>"],
                    "answer": "B",
                    "explanation": "Format: Authorization: Token <token_value>"
                },
                {
                    "text": "Which status code indicates a successful POST request that created a resource?",
                    "type": "multiple_choice",
                    "options": ["200", "201", "204", "301"],
                    "answer": "B",
                    "explanation": "201 Created indicates successful resource creation"
                },
                {
                    "text": "DRF provides a browsable API interface for testing endpoints in the browser.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "The browsable API is a major DRF feature"
                }
            ]
        },
        8: {
            "title": "Session 8: Cloud Deployment",
            "questions": [
                {
                    "text": "What should DEBUG be set to in production?",
                    "type": "multiple_choice",
                    "options": ["True", "False", "None", "1"],
                    "answer": "B",
                    "explanation": "DEBUG=False in production for security"
                },
                {
                    "text": "Which Django package serves static files in production without a separate web server?",
                    "type": "multiple_choice",
                    "options": ["staticfiles", "whitenoise", "staticserve", "fileserver"],
                    "answer": "B",
                    "explanation": "WhiteNoise serves static files efficiently"
                },
                {
                    "text": "ALLOWED_HOSTS should contain the domain name(s) where your app is deployed.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "ALLOWED_HOSTS prevents HTTP Host header attacks"
                },
                {
                    "text": "What command collects all static files into one directory?",
                    "type": "multiple_choice",
                    "options": ["python manage.py collectstatic", "python manage.py gatherstatic", "python manage.py static", "python manage.py copystatic"],
                    "answer": "A",
                    "explanation": "collectstatic gathers static files to STATIC_ROOT"
                },
                {
                    "text": "Which of these is a cloud platform for deploying Django apps?",
                    "type": "multiple_choice",
                    "options": ["Railway", "Render", "Heroku", "All of the above"],
                    "answer": "D",
                    "explanation": "All three are valid Django deployment platforms"
                },
                {
                    "text": "What is the purpose of a Procfile?",
                    "type": "multiple_choice",
                    "options": ["Store environment variables", "Define how to run the application", "List dependencies", "Configure the database"],
                    "answer": "B",
                    "explanation": "Procfile tells the platform how to run your app"
                },
                {
                    "text": "For production, use a WSGI server like ________ instead of Django's development server.",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "gunicorn",
                    "explanation": "Gunicorn is a popular production WSGI server"
                },
                {
                    "text": "Which security setting enables HTTPS redirect?",
                    "type": "multiple_choice",
                    "options": ["HTTPS_REDIRECT = True", "SECURE_SSL_REDIRECT = True", "SSL_ENABLED = True", "FORCE_HTTPS = True"],
                    "answer": "B",
                    "explanation": "SECURE_SSL_REDIRECT redirects HTTP to HTTPS"
                },
                {
                    "text": "The Django development server (runserver) should be used in production.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "False",
                    "explanation": "Use gunicorn, uWSGI, or similar in production"
                },
                {
                    "text": "What Python library is used to make HTTP requests from a Kivy app to an API?",
                    "type": "multiple_choice",
                    "options": ["http", "requests", "urllib", "api"],
                    "answer": "B",
                    "explanation": "requests library is the standard for HTTP calls"
                }
            ]
        },
        9: {
            "title": "Session 9: MCP Fundamentals (Emerging Technology)",
            "questions": [
                {
                    "text": "What does MCP stand for?",
                    "type": "multiple_choice",
                    "options": ["Model Communication Protocol", "Model Context Protocol", "Machine Control Protocol", "Message Connection Protocol"],
                    "answer": "B",
                    "explanation": "MCP = Model Context Protocol"
                },
                {
                    "text": "Who created the Model Context Protocol?",
                    "type": "multiple_choice",
                    "options": ["OpenAI", "Google", "Anthropic", "Microsoft"],
                    "answer": "C",
                    "explanation": "Anthropic created MCP in November 2024"
                },
                {
                    "text": "MCP standardizes how AI agents connect to external tools and data sources.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "MCP standardizes AI agent-to-tool communication"
                },
                {
                    "text": "What are the three MCP primitives?",
                    "type": "multiple_choice",
                    "options": ["Input, Output, Process", "Tools, Resources, Prompts", "Read, Write, Execute", "Connect, Send, Receive"],
                    "answer": "B",
                    "explanation": "Tools (model-controlled), Resources (app-controlled), Prompts (user-controlled)"
                },
                {
                    "text": "In MCP architecture, what provides tools to AI agents?",
                    "type": "multiple_choice",
                    "options": ["MCP Host", "MCP Client", "MCP Server", "MCP Bridge"],
                    "answer": "C",
                    "explanation": "MCP Servers expose tools and resources to clients"
                },
                {
                    "text": "Which Python library/framework is used to build MCP servers?",
                    "type": "multiple_choice",
                    "options": ["mcp-server", "mcp", "fastmcp", "Both B and C"],
                    "answer": "D",
                    "explanation": "Both mcp package and FastMCP framework work"
                },
                {
                    "text": "MCP solves the N×M integration problem by providing a ________ interface.",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "standardized",
                    "explanation": "One standard interface for all integrations"
                },
                {
                    "text": "What transport methods does MCP support?",
                    "type": "multiple_choice",
                    "options": ["stdio only", "HTTP only", "stdio and HTTP+SSE", "WebSocket only"],
                    "answer": "C",
                    "explanation": "MCP supports stdio (local) and HTTP+SSE (remote)"
                },
                {
                    "text": "MCP tools are functions that AI agents can call to perform actions.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Tools are callable functions with defined inputs/outputs"
                },
                {
                    "text": "Which companies adopted MCP in addition to Anthropic?",
                    "type": "multiple_choice",
                    "options": ["Only OpenAI", "Only Google", "Only Microsoft", "OpenAI, Google, and Microsoft"],
                    "answer": "D",
                    "explanation": "OpenAI, Google, and Microsoft all adopted MCP"
                }
            ]
        },
        10: {
            "title": "Session 10: A2A Protocol (Emerging Technology)",
            "questions": [
                {
                    "text": "What does A2A stand for?",
                    "type": "multiple_choice",
                    "options": ["App-to-App", "Agent-to-Agent", "API-to-API", "Access-to-Access"],
                    "answer": "B",
                    "explanation": "A2A = Agent-to-Agent Protocol"
                },
                {
                    "text": "Which company created the A2A protocol?",
                    "type": "multiple_choice",
                    "options": ["Anthropic", "OpenAI", "Google", "Microsoft"],
                    "answer": "C",
                    "explanation": "Google created A2A in April 2025"
                },
                {
                    "text": "A2A enables different AI agents from different vendors to communicate and collaborate.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "A2A enables interoperability between different agents"
                },
                {
                    "text": "What is an Agent Card in A2A?",
                    "type": "multiple_choice",
                    "options": ["A physical identification card", "A JSON file describing agent capabilities", "A credit card for AI services", "A debug tool"],
                    "answer": "B",
                    "explanation": "Agent Card is a JSON file listing capabilities and skills"
                },
                {
                    "text": "Where is the Agent Card typically located?",
                    "type": "multiple_choice",
                    "options": ["/api/agent", "/.well-known/agent.json", "/agent/card", "/config/agent"],
                    "answer": "B",
                    "explanation": "Standard location: /.well-known/agent.json"
                },
                {
                    "text": "How does A2A complement MCP?",
                    "type": "multiple_choice",
                    "options": ["A2A replaces MCP", "MCP is agent-to-tool, A2A is agent-to-agent", "They are the same thing", "A2A is only for mobile apps"],
                    "answer": "B",
                    "explanation": "MCP connects agents to tools; A2A connects agents to agents"
                },
                {
                    "text": "A2A uses ________ over HTTP for communication.",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "JSON-RPC",
                    "explanation": "A2A uses JSON-RPC protocol over HTTP/SSE"
                },
                {
                    "text": "Which organization now governs both MCP and A2A?",
                    "type": "multiple_choice",
                    "options": ["Apache Foundation", "Linux Foundation", "W3C", "IEEE"],
                    "answer": "B",
                    "explanation": "Linux Foundation governs both protocols"
                },
                {
                    "text": "In A2A, a client agent sends task requests to server agents.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Client agents request tasks; server agents execute them"
                },
                {
                    "text": "How many organizations support the A2A protocol?",
                    "type": "multiple_choice",
                    "options": ["About 10", "About 50", "Over 150", "Over 500"],
                    "answer": "C",
                    "explanation": "Over 150 organizations including Salesforce, SAP, Adobe"
                }
            ]
        },
        11: {
            "title": "Session 11: Vector Databases & Pgvector (Emerging Technology)",
            "questions": [
                {
                    "text": "What is an embedding in the context of AI?",
                    "type": "multiple_choice",
                    "options": ["Inserting images into documents", "A numerical vector representation of text/data", "Embedding code in HTML", "A type of database"],
                    "answer": "B",
                    "explanation": "Embeddings convert text/data into numerical vectors"
                },
                {
                    "text": "What is Pgvector?",
                    "type": "multiple_choice",
                    "options": ["A new database system", "A PostgreSQL extension for vector operations", "A Python library", "A type of graph database"],
                    "answer": "B",
                    "explanation": "Pgvector adds vector data types and operations to PostgreSQL"
                },
                {
                    "text": "Vector similarity search finds data based on meaning rather than exact keyword match.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Vector search finds semantically similar content"
                },
                {
                    "text": "What does RAG stand for?",
                    "type": "multiple_choice",
                    "options": ["Random Access Generation", "Retrieval-Augmented Generation", "Rapid AI Growth", "Remote Agent Gateway"],
                    "answer": "B",
                    "explanation": "RAG = Retrieval-Augmented Generation"
                },
                {
                    "text": "Which SQL command enables the vector extension in PostgreSQL?",
                    "type": "multiple_choice",
                    "options": ["ENABLE EXTENSION vector", "CREATE EXTENSION vector", "INSTALL vector", "ADD EXTENSION vector"],
                    "answer": "B",
                    "explanation": "CREATE EXTENSION vector; enables pgvector"
                },
                {
                    "text": "What is the typical dimension of OpenAI's text-embedding-ada-002?",
                    "type": "multiple_choice",
                    "options": ["256", "512", "1536", "2048"],
                    "answer": "C",
                    "explanation": "text-embedding-ada-002 produces 1536-dimensional vectors"
                },
                {
                    "text": "In vector databases, we measure ________ between vectors to find related content.",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "distance",
                    "explanation": "Cosine similarity or Euclidean distance measures relatedness"
                },
                {
                    "text": "Why is RAG useful for AI applications?",
                    "type": "multiple_choice",
                    "options": ["It makes AI faster", "It allows AI to use current/private data not in training", "It reduces costs", "It improves graphics"],
                    "answer": "B",
                    "explanation": "RAG retrieves relevant context for accurate, up-to-date answers"
                },
                {
                    "text": "Pgvector allows you to store vectors alongside regular data in the same PostgreSQL database.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Pgvector integrates with existing PostgreSQL tables"
                },
                {
                    "text": "What is semantic search?",
                    "type": "multiple_choice",
                    "options": ["Searching by exact keywords", "Searching by meaning and context", "Searching by file type", "Searching by date"],
                    "answer": "B",
                    "explanation": "Semantic search understands meaning, not just keywords"
                }
            ]
        },
        12: {
            "title": "Session 12: Building AI-Powered Applications (Emerging Technology)",
            "questions": [
                {
                    "text": "What is the recommended approach to combine MCP, A2A, and Pgvector?",
                    "type": "multiple_choice",
                    "options": ["Use only one technology at a time", "Integrate them for different purposes (tools, agents, knowledge)", "Replace one with another", "They cannot be combined"],
                    "answer": "B",
                    "explanation": "Each technology serves different purposes and works together"
                },
                {
                    "text": "In an AI-powered app, what does the Django backend typically handle?",
                    "type": "multiple_choice",
                    "options": ["Only the frontend display", "Data storage, API, and business logic", "Only AI processing", "Only user authentication"],
                    "answer": "B",
                    "explanation": "Django handles data, API endpoints, and business logic"
                },
                {
                    "text": "Testing AI features should include checking response relevance and accuracy.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "AI features need accuracy, relevance, and performance testing"
                },
                {
                    "text": "Which component would you use for intelligent document search?",
                    "type": "multiple_choice",
                    "options": ["MCP", "A2A", "Pgvector/RAG", "Django templates"],
                    "answer": "C",
                    "explanation": "Pgvector/RAG enables semantic search in documents"
                },
                {
                    "text": "When deploying AI-powered apps, what should you consider for MCP servers?",
                    "type": "multiple_choice",
                    "options": ["They don't need deployment", "They need to be accessible to AI clients", "They only work locally", "They replace the main app"],
                    "answer": "B",
                    "explanation": "MCP servers must be reachable by AI clients"
                },
                {
                    "text": "The pattern \"Build with ADK, equip with ________, communicate with A2A\" describes modern AI development.",
                    "type": "fill_in_blank",
                    "options": [],
                    "answer": "MCP",
                    "explanation": "Build with ADK, equip with MCP, communicate with A2A"
                },
                {
                    "text": "What is the purpose of combining MCP + A2A in one system?",
                    "type": "multiple_choice",
                    "options": ["To make the app slower", "To enable agents to use tools AND collaborate with other agents", "To reduce functionality", "To avoid using databases"],
                    "answer": "B",
                    "explanation": "Combined: agents use tools (MCP) and talk to other agents (A2A)"
                },
                {
                    "text": "Production AI applications should include monitoring and logging.",
                    "type": "true_false",
                    "options": ["True", "False"],
                    "answer": "True",
                    "explanation": "Production apps need observability for debugging and optimization"
                },
                {
                    "text": "Which is NOT a good practice when building AI-powered applications?",
                    "type": "multiple_choice",
                    "options": ["Implementing error handling", "Hardcoding API keys in source code", "Using environment variables for secrets", "Testing with various inputs"],
                    "answer": "B",
                    "explanation": "Never hardcode secrets; use environment variables"
                },
                {
                    "text": "What makes an application \"AI-powered\"?",
                    "type": "multiple_choice",
                    "options": ["Using any Python library", "Having a database", "Integrating AI capabilities like intelligent search, agents, or generation", "Having a mobile app"],
                    "answer": "C",
                    "explanation": "AI-powered means integrating intelligent/AI capabilities"
                }
            ]
        }
    }

    # Process each COMP019 subject
    for subject in subjects:
        subject_id = subject['id']
        section = subject['section']
        print(f"\nProcessing: Applications Development - {section}")

        # Get all sessions for this subject
        cursor.execute("SELECT id, session_number FROM sessions WHERE subject_id = ? ORDER BY session_number", (subject_id,))
        sessions = cursor.fetchall()

        for session in sessions:
            session_num = session['session_number']
            session_id = session['id']

            if session_num not in quizzes_data:
                continue

            quiz_data = quizzes_data[session_num]

            # Check if quiz already exists for this session
            cursor.execute("SELECT id FROM quizzes WHERE session_id = ?", (session_id,))
            existing_quiz = cursor.fetchone()

            if existing_quiz:
                # Delete existing quiz and questions
                cursor.execute("DELETE FROM quiz_questions WHERE quiz_id = ?", (existing_quiz['id'],))
                cursor.execute("DELETE FROM quizzes WHERE id = ?", (existing_quiz['id'],))

            # Create quiz
            cursor.execute('''
                INSERT INTO quizzes (session_id, title, time_limit)
                VALUES (?, ?, ?)
            ''', (session_id, quiz_data['title'], 15))  # 15 minutes time limit

            quiz_id = cursor.lastrowid

            # Add questions
            for q in quiz_data['questions']:
                options_json = json.dumps(q['options']) if q['options'] else None
                cursor.execute('''
                    INSERT INTO quiz_questions (quiz_id, question_text, question_type, options, correct_answer, points)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (quiz_id, q['text'], q['type'], options_json, q['answer'], 1))

            print(f"  Added Quiz for Session {session_num}: {quiz_data['title']} (10 questions)")

    conn.commit()
    conn.close()
    print("\nAll COMP019 quizzes seeded successfully!")

if __name__ == '__main__':
    seed_comp019_quizzes()
