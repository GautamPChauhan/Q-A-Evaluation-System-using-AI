from flask import Flask, render_template, request, redirect, flash, session
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash

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
    return bool(re.match(r"^[A-Za-z\s]+$", name))

def is_valid_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def is_strong_password(password):
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$', password))

# ------------------------- Routes ----------------------------------

@app.route('/')
def index():
    return render_template('landing_page.html')

@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if user_type not in ['student', 'teacher']:
        flash("Invalid user type!", "error")
        return redirect('/')
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        raw_password = request.form.get('password', '').strip()
        institution = request.form.get('institution', '').strip() if user_type == 'teacher' else None
        form_data = {
            'name': name,
            'email': email,
            'password': raw_password
        }
        if user_type == 'teacher':
            form_data['institution'] = institution

        # Server-side Validation
        if not name or not email or not raw_password or (user_type == 'teacher' and not institution):
            flash("All fields are required!", "error")
            return render_template(f'{user_type}_registration.html', user_type=user_type, form_data=form_data)

        if not is_valid_name(name):
            flash("Name should contain only letters and spaces.", "error")
            return render_template(f'{user_type}_registration.html', user_type=user_type, form_data=form_data)

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "error")
            return render_template(f'{user_type}_registration.html', user_type=user_type, form_data=form_data)

        if not is_strong_password(raw_password):
            flash("Password must be at least 6 characters long and include a letter and a number.", "error")
            return render_template(f'{user_type}_registration.html', user_type=user_type, form_data=form_data)

        # Hash the Password
        hashed_password = generate_password_hash(raw_password)

        # Save to Database
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            if user_type == 'teacher' and institution:
                cursor.execute(
                    "INSERT INTO users (name, email, password, user_type, institution) VALUES (%s, %s, %s, %s, %s)",
                    (name, email, hashed_password, user_type, institution)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (name, email, password, user_type) VALUES (%s, %s, %s, %s)",
                    (name, email, hashed_password, user_type)
                )
            conn.commit()
            cursor.close()
            conn.close()

            flash(f"Registration as {user_type.capitalize()} successful!", "success")
            return redirect('/login')

        except mysql.connector.errors.IntegrityError as err:
            if err.errno == 1062:
                flash("Email already registered. Try using a different one.", "error")
            else:
                flash(f"Database error: {err}", "error")
            return render_template(f'{user_type}_registration.html', user_type=user_type, form_data=form_data)

    return render_template(f'{user_type}_registration.html', user_type=user_type, form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'student')

        if not email or not password:
            flash("Email and password are required!", "error")
            return redirect('/login')

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, password, user_type FROM users WHERE email = %s AND user_type = %s",
                (email, role)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['name'] = user[1]
                session['role'] = user[3]
                flash(f"Welcome, {user[1]}!", "success")
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
    session.pop('name', None)
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

    return render_template('teacher_dashboard.html', questions=questions, name=session.get('name'))

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
            "SELECT q.question_text, a.answer_text FROM answers a JOIN questions q ON a.question_id = q.quid WHERE a.student_id = %s",
            (session['user_id'],)
        )
        feedback = cursor.fetchall()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        questions = []
        feedback = []

    return render_template('student_dashboard.html', questions=questions, feedback=feedback, name=session.get('name'))

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
    app.run(debug=True)