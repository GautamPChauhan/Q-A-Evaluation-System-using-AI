from flask import Flask, render_template, request, redirect, flash, session
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Replace with your MySQL password
    'database': 'registration_db'
}

# ------------------- Helper Validation Functions -------------------
def is_valid_name(name):
    return bool(name and re.match(r"^[A-Za-z\s]+$", name))

def is_valid_email(email):
    return bool(email and re.match(r"[^@]+@[^@]+\.[^@]+", email))

def is_strong_password(password):
    return bool(password and re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$', password))

def is_valid_contact(contact):
    return bool(contact and re.match(r"^\+?\d{10,12}$", contact))

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# ------------------------- Database Schema -------------------
# def init_db():
#     conn = mysql.connector.connect(**db_config)
#     cursor = conn.cursor()
    
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             uid INT AUTO_INCREMENT PRIMARY KEY,
#             username VARCHAR(255) NOT NULL UNIQUE,
#             email VARCHAR(255) NOT NULL UNIQUE,
#             password VARCHAR(255) NOT NULL,
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#             modified_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
#             role ENUM('student', 'teacher', 'admin') NOT NULL
#         )
#     """)
    
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS teachers (
#             teacher_id INT PRIMARY KEY,
#             full_name VARCHAR(255) NOT NULL,
#             dob DATE NOT NULL,
#             last_degree VARCHAR(100) NOT NULL,
#             contact VARCHAR(20) NOT NULL,
#             gender ENUM('Male', 'Female', 'Other') NOT NULL,
#             address TEXT NOT NULL,
#             expertise VARCHAR(255) NOT NULL,
#             subjects_taught TEXT NOT NULL,
#             experience_years INT NOT NULL,
#             industry_experience_years INT NOT NULL,
#             research_papers INT NOT NULL,
#             department VARCHAR(100) NOT NULL,
#             college VARCHAR(255) NOT NULL,
#             FOREIGN KEY (teacher_id) REFERENCES users(uid)
#         )
#     """)
    
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS students (
#             student_id INT PRIMARY KEY,
#             full_name VARCHAR(255) NOT NULL,
#             roll_no VARCHAR(50) NOT NULL UNIQUE,
#             enrollment_no VARCHAR(50) NOT NULL UNIQUE,
#             contact VARCHAR(20) NOT NULL,
#             dob DATE NOT NULL,
#             course VARCHAR(100) NOT NULL,
#             gender ENUM('Male', 'Female', 'Other') NOT NULL,
#             address TEXT NOT NULL,
#             department VARCHAR(100) NOT NULL,
#             college VARCHAR(255) NOT NULL,
#             FOREIGN KEY (student_id) REFERENCES users(uid)
#         )
#     """)
    
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS admins (
#             admin_id INT PRIMARY KEY,
#             full_name VARCHAR(255) NOT NULL,
#             FOREIGN KEY (admin_id) REFERENCES users(uid)
#         )
#     """)
    
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS questions (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             teacher_id INT NOT NULL,
#             question_text TEXT NOT NULL,
#             keywords TEXT NOT NULL,
#             actual_answer TEXT NOT NULL,
#             FOREIGN KEY (teacher_id) REFERENCES users(uid)
#         )
#     """)
    
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS answers (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             student_id INT NOT NULL,
#             question_id INT NOT NULL,
#             answer_text TEXT NOT NULL,
#             FOREIGN KEY (student_id) REFERENCES users(uid),
#             FOREIGN KEY (question_id) REFERENCES questions(id)
#         )
#     """)
    
#     conn.commit()
#     cursor.close()
#     conn.close()

# ------------------------- Routes ----------------------------------
@app.route('/')
def index():
    return render_template('landing_page.html')

@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if user_type not in ['student', 'teacher', 'admin']:
        flash("Invalid user type!", "error")
        return redirect('/')
    
    if request.method == 'POST':
        # Common fields
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        form_data = {'username': username, 'email': email}
        
        # Role-specific fields
        if user_type == 'teacher':
            fields = [
                'full_name', 'dob', 'last_degree', 'contact', 'gender', 
                'address', 'expertise', 'subjects_taught', 'experience_years',
                'industry_experience_years', 'research_papers', 'department', 'college'
            ]
            for field in fields:
                form_data[field] = request.form.get(field, '').strip()
        elif user_type == 'student':
            fields = [
                'full_name', 'roll_no', 'enrollment_no', 'contact', 
                'dob', 'course', 'gender', 'address', 'department', 'college'
            ]
            for field in fields:
                form_data[field] = request.form.get(field, '').strip()
        else:  # admin
            fields = ['full_name']
            for field in fields:
                form_data[field] = request.form.get(field, '').strip()

        # Server-side Validation
        errors = []
        if not username:
            errors.append("Username is required.")
        if not is_valid_name(form_data.get('full_name', '')):
            errors.append("Full name should contain only letters and spaces.")
        if not is_valid_email(email):
            errors.append("Please enter a valid email address.")
        if not is_strong_password(password):
            errors.append("Password must be at least 6 characters long and include a letter and a number.")
        
        if user_type in ['student', 'teacher']:
            if not is_valid_contact(form_data.get('contact', '')):
                errors.append("Please enter a valid contact number (10-12 digits).")
            if not is_valid_date(form_data.get('dob', '')):
                errors.append("Please enter a valid date of birth (YYYY-MM-DD).")
            if not form_data.get('gender') in ['Male', 'Female', 'Other']:
                errors.append("Please select a valid gender.")
            if not form_data.get('address'):
                errors.append("Address is required.")
            if not form_data.get('department'):
                errors.append("Department is required.")
            if not form_data.get('college'):
                errors.append("College is required.")
        
        if user_type == 'student':
            if not form_data.get('roll_no'):
                errors.append("Roll number is required.")
            if not form_data.get('enrollment_no'):
                errors.append("Enrollment number is required.")
            if not form_data.get('course'):
                errors.append("Course is required.")
        
        if user_type == 'teacher':
            if not form_data.get('last_degree'):
                errors.append("Last educational degree is required.")
            if not form_data.get('expertise'):
                errors.append("Area of expertise is required.")
            if not form_data.get('subjects_taught'):
                errors.append("Subjects taught is required.")
            try:
                if int(form_data.get('experience_years', -1)) < 0:
                    errors.append("Teaching experience years must be a non-negative number.")
                if int(form_data.get('industry_experience_years', -1)) < 0:
                    errors.append("Industry experience years must be a non-negative number.")
                if int(form_data.get('research_papers', -1)) < 0:
                    errors.append("Number of research papers must be a non-negative number.")
            except ValueError:
                errors.append("Experience years and research papers must be valid numbers.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(f'{user_type}_registration.html', user_type=user_type, form_data=form_data)

        # Hash the Password
        hashed_password = generate_password_hash(password)

        # Save to Database
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                (username, email, hashed_password, user_type)
            )
            user_id = cursor.lastrowid

            if user_type == 'teacher':
                cursor.execute(
                    """INSERT INTO teachers (teacher_id, full_name, dob, last_degree, contact, gender, 
                    address, expertise, subjects_taught, experience_years, industry_experience_years, 
                    research_papers, department, college) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (user_id, form_data['full_name'], form_data['dob'], form_data['last_degree'],
                     form_data['contact'], form_data['gender'], form_data['address'],
                     form_data['expertise'], form_data['subjects_taught'], int(form_data['experience_years']),
                     int(form_data['industry_experience_years']), int(form_data['research_papers']),
                     form_data['department'], form_data['college'])
                )
            elif user_type == 'student':
                cursor.execute(
                    """INSERT INTO students (student_id, full_name, roll_no, enrollment_no, contact, 
                    dob, course, gender, address, department, college) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (user_id, form_data['full_name'], form_data['roll_no'], form_data['enrollment_no'],
                     form_data['contact'], form_data['dob'], form_data['course'],
                     form_data['gender'], form_data['address'], form_data['department'], form_data['college'])
                )
            else:  # admin
                cursor.execute(
                    "INSERT INTO admins (admin_id, full_name) VALUES (%s, %s)",
                    (user_id, form_data['full_name'])
                )

            conn.commit()
            cursor.close()
            conn.close()

            flash(f"Registration as {user_type.capitalize()} successful!", "success")
            return redirect('/login')

        except mysql.connector.errors.IntegrityError as err:
            if err.errno == 1062:
                flash("Username, email, roll number, or enrollment number already registered.", "error")
            else:
                flash(f"Database error: {err}", "error")
            return render_template(f'{user_type}_registration.html', user_type=user_type, form_data=form_data)

    return render_template(f'{user_type}_registration.html', user_type=user_type, form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'student')

        if not username or not password:
            flash("Username and password are required!", "error")
            return redirect('/login')

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT uid, username, password, role FROM users WHERE username = %s AND role = %s",
                (username, role)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                flash(f"Welcome, {user[1]}!", "success")
                return redirect(f'/{user[3]}_dashboard')
            else:
                flash("Invalid username, password, or role.", "error")
                return redirect('/login')

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.", "success")
    return redirect('/')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, question_text, keywords FROM questions WHERE teacher_id = %s",
            (session['user_id'],)
        )
        questions = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        questions = []

    return render_template('teacher_dashboard.html', questions=questions, name=session.get('username'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        flash("Please log in as a student.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id, question_text FROM questions")
        questions = cursor.fetchall()
        cursor.execute(
            "SELECT q.question_text, a.answer_text FROM answers a JOIN questions q ON a.question_id = q.id WHERE a.student_id = %s",
            (session['user_id'],)
        )
        feedback = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        questions = []
        feedback = []

    return render_template('student_dashboard.html', questions=questions, feedback=feedback, name=session.get('username'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT uid, username, role FROM users")
        users = cursor.fetchall()
        cursor.execute("SELECT id, question_text, teacher_id FROM questions")
        questions = cursor.fetchall()
        cursor.execute("SELECT id, student_id, question_id, answer_text FROM answers")
        answers = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        users = []
        questions = []
        answers = []

    return render_template('admin_dashboard.html', users=users, questions=questions, answers=answers, name=session.get('username'))

@app.route('/teacher/upload', methods=['POST'])
def teacher_upload():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/')

    question = request.form.get('question', '').strip()
    keywords = request.form.get('keywords', '').strip()
    actual_answer = request.form.get('actual_answer', '').strip()

    if not question or not keywords or not actual_answer:
        flash("All fields are required for uploading a question!", "error")
        return redirect('/teacher_dashboard')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO questions (teacher_id, question_text, keywords, actual_answer) VALUES (%s, %s, %s, %s)",
            (session['user_id'], question, keywords, actual_answer)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Question uploaded successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")

    return redirect('/teacher_dashboard')

@app.route('/student/submit', methods=['POST'])
def student_submit():
    if 'user_id' not in session or session.get('role') != 'student':
        flash("Please log in as a student.", "error")
        return redirect('/')

    answer = request.form.get('answer', '').strip()
    question_id = request.form.get('question_id', '').strip()

    if not answer or not question_id:
        flash("Answer and question selection are required!", "error")
        return redirect('/student_dashboard')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO answers (student_id, question_id, answer_text) VALUES (%s, %s, %s)",
            (session['user_id'], question_id, answer)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Answer submitted successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")

    return redirect('/student_dashboard')

if __name__ == '__main__':
    #init_db()  # Initialize database schema
    app.run(debug=True)