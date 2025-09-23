from flask import Flask, render_template, request, redirect, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'port':'3307',
    'password': '',  # Replace with your MySQL password
    'database': 'registration_db'
}

# ------------------------- Database Schema -------------------
def init_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            password_status TINYINT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            role ENUM('student', 'teacher', 'admin') NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id INT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            dob DATE NOT NULL,
            last_degree VARCHAR(100) NOT NULL,
            contact VARCHAR(20) NOT NULL,
            gender ENUM('Male', 'Female', 'Other') NOT NULL,
            address TEXT NOT NULL,
            expertise VARCHAR(255) NOT NULL,
            subjects_taught TEXT NOT NULL,
            experience_years INT NOT NULL,
            industry_experience_years INT NOT NULL,
            research_papers INT NOT NULL,
            department VARCHAR(100) NOT NULL,
            university VARCHAR(255) NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES users(uid)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            roll_no VARCHAR(50) NOT NULL UNIQUE,
            enrollment_no VARCHAR(50) NOT NULL UNIQUE,
            contact VARCHAR(20) NOT NULL,
            dob DATE NOT NULL,
            course VARCHAR(100) NOT NULL,
            gender ENUM('Male', 'Female', 'Other') NOT NULL,
            address TEXT NOT NULL,
            department VARCHAR(100) NOT NULL,
            university VARCHAR(255) NOT NULL,
            FOREIGN KEY (student_id) REFERENCES users(uid)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES users(uid)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_id INT NOT NULL,
            question_text TEXT NOT NULL,
            keywords TEXT NOT NULL,
            actual_answer TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES users(uid)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            question_id INT NOT NULL,
            answer_text TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES users(uid),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# ------------------------- Routes ----------------------------------
@app.route('/')
def index():
    return render_template('landing_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()

        if not email or not password or not role:
            flash("Email, password, and role are required!", "error")
            return redirect('/login')

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT uid, email, password, role FROM users WHERE email = %s AND role = %s",
                (email, role)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['email'] = user[1]
                session['role'] = user[3]
                flash(f"Welcome back!", "success")
                return redirect(f'/{user[3]}_dashboard')
            else:
                flash("Invalid email, password, or role.", "error")
                return redirect('/login')

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
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

    return render_template('teacher_dashboard.html', questions=questions, name=session.get('email'))

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

    return render_template('student_dashboard.html', questions=questions, feedback=feedback, name=session.get('email'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT uid, email, role FROM users")
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

    return render_template('admin_dashboard.html', users=users, questions=questions, answers=answers, name=session.get('email'))

@app.route('/teacher/upload', methods=['POST'])
def teacher_upload():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')

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
        return redirect('/login')

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
    init_db()  # Initialize database schema
    app.run(debug=True)