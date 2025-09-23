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
    'port': '3307',
    'password': '',  # Replace with your MySQL password
    'database': 'edusystem_db'
}

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

            if user:
                if role == 'admin':
                    if user[2] == password:  # Check without hash for admin
                        session['user_id'] = user[0]
                        session['email'] = user[1]
                        session['role'] = user[3]
                        flash(f"Welcome back!", "success")
                        return redirect('/admin_dashboard')
                else:
                    if check_password_hash(user[2], password):  # Check with hash for student and teacher
                        session['user_id'] = user[0]
                        session['email'] = user[1]
                        session['role'] = user[3]
                        flash(f"Welcome back!", "success")
                        return redirect(f'/{user[3]}_dashboard')
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
            "SELECT question_id, question_text, model_answer, max_score, course_id, semester_id FROM questions WHERE course_id IN (SELECT course_id FROM courses)"
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
        cursor.execute("SELECT question_id, question_text, course_id, semester_id FROM questions")
        questions = cursor.fetchall()
        cursor.execute(
            "SELECT q.question_text, a.answer_text FROM student_answers a JOIN questions q ON a.question_id = q.question_id WHERE a.student_id = %s",
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
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM questions")
        question_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM student_answers")
        answer_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM evaluations")
        evaluation_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        user_count = question_count = answer_count = evaluation_count = 0

    return render_template('admin_dashboard.html', user_count=user_count, question_count=question_count, answer_count=answer_count, evaluation_count=evaluation_count, name=session.get('email'))

@app.route('/admin/teachers')
def admin_teachers():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT teacher_id, full_name, dob, last_degree, contact, gender, address, expertise, subjects_taught, experience_years, industry_experience_years, research_papers, department, university FROM teachers")
        teachers = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        teachers = []

    return render_template('admin_teachers.html', teachers=teachers, name=session.get('email'))

@app.route('/admin/students')
def admin_students():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, full_name, roll_no, enrollment_no, contact, dob, course_id, semester_id, gender, address, department, university FROM students")
        students = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        students = []

    return render_template('admin_students.html', students=students, name=session.get('email'))

@app.route('/admin/courses_semesters')
def admin_courses_semesters():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT c.course_id, c.course_name, c.description, s.semester_id, s.semester_name, s.start_date, s.end_date FROM courses c LEFT JOIN semesters s ON c.course_id = s.course_id")
        courses_semesters = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        courses_semesters = []

    return render_template('admin_courses_semesters.html', courses_semesters=courses_semesters, name=session.get('email'))

@app.route('/admin/evaluations')
def admin_evaluations():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT e.evaluation_id, e.answer_id, e.score, e.feedback, e.evaluated_at, a.student_id, a.question_id, a.answer_text, q.question_text "
            "FROM evaluations e "
            "JOIN student_answers a ON e.answer_id = a.answer_id "
            "JOIN questions q ON a.question_id = q.question_id"
        )
        evaluations = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        evaluations = []

    return render_template('admin_evaluations.html', evaluations=evaluations, name=session.get('email'))

@app.route('/teacher/upload', methods=['POST'])
def teacher_upload():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')

    question_text = request.form.get('question_text', '').strip()
    model_answer = request.form.get('model_answer', '').strip()
    max_score = request.form.get('max_score', '').strip()
    course_id = request.form.get('course_id', '').strip()
    semester_id = request.form.get('semester_id', '').strip()

    if not question_text or not model_answer or not max_score or not course_id or not semester_id:
        flash("All fields are required for uploading a question!", "error")
        return redirect('/teacher_dashboard')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO questions (course_id, semester_id, question_text, model_answer, max_score) VALUES (%s, %s, %s, %s, %s)",
            (course_id, semester_id, question_text, model_answer, max_score)
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

    answer_text = request.form.get('answer_text', '').strip()
    question_id = request.form.get('question_id', '').strip()

    if not answer_text or not question_id:
        flash("Answer and question selection are required!", "error")
        return redirect('/student_dashboard')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO student_answers (student_id, question_id, answer_text) VALUES (%s, %s, %s)",
            (session['user_id'], question_id, answer_text)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Answer submitted successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")

    return redirect('/student_dashboard')

if __name__ == '__main__':
    app.run(debug=True)