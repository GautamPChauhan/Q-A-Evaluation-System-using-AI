from flask import Flask, render_template, request, redirect, flash, session,send_file,url_for,jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime,time, timedelta
import pandas as pd
import io
import re
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yagmail
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production


ALLOWED_EXTENSIONS = {'xls', 'xlsx'}


# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'port': '3307',
    'password': '',  # Replace with your MySQL password
    'database': 'edusystem_db'
}

# ------------------------- Routes ----------------------------------

import yagmail

# ---------------- EMAIL SENDING FUNCTION ----------------
def send_email(receiver_email, subject, body):
    try:
        # Login with your Gmail (use app password, not raw Gmail password)
        yag = yagmail.SMTP("www.gautam.2005@gmail.com", "yilt qrum ypgz tlgt")
        yag.send(
            to=receiver_email,
            subject=subject,
            contents=body
        )
        print(f"Email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {receiver_email}: {e}")
        return False

# ---------------- PASSWORD GENERATOR ----------------
def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()?"
    return ''.join(random.choice(chars) for _ in range(length))


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
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT uid, email, password, role FROM users WHERE email = %s AND role = %s",
                (email, role)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                user_id = user['uid']
                user_email = user['email']
                stored_password = user['password']
                user_role = user['role']

                # Admin login (plain password check)
                if role == 'admin':
                    if stored_password == password:  
                        session['user_id'] = user_id
                        session['email'] = user_email
                        session['role'] = user_role
                        flash("Welcome back, Admin!", "success")
                        return redirect('/admin_dashboard')

                # Teacher + Student login (hashed password check)
                elif role in ['teacher', 'student']:
                    if check_password_hash(stored_password, password):
                        session['user_id'] = user_id
                        session['email'] = user_email
                        session['role'] = user_role

                        # If teacher, check profile completeness
                        if role == 'teacher':
                            conn = mysql.connector.connect(**db_config)
                            cursor = conn.cursor(dictionary=True)
                            cursor.execute(
                                "SELECT * FROM teachers WHERE teacher_id = %s",
                                (user_id,)
                            )
                            teacher = cursor.fetchone()
                            cursor.close()
                            conn.close()

                            required_fields = ['full_name', 'dob', 'last_degree', 'contact', 'gender', 'address', 'expertise','subjects_taught', 'experience_years', 'industry_experience_years', 'research_papers']
                            incomplete = any(teacher[field] in (None, '', 'Not Provided') for field in required_fields)
                            if incomplete:
                                flash("Please complete your profile first.", "info")
                                return redirect(url_for('complete_teacher_profile'))

                        # Normal redirect after login
                        flash(f"Welcome back, {role.capitalize()}!", "success")
                        return redirect(f'/{role}_dashboard')

            # If nothing matched
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
    
    teacher_id = session['user_id']  # current teacher's UID

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Fetch exams created by this teacher with course, semester, and subject names
        cursor.execute("""
            SELECT 
                e.exam_id,
                e.exam_name,
                e.course_id,
                c.course_name,
                e.semester_id,
                s.semester_name,
                e.subject_id,
                sub.subject_name,
                e.topic,
                e.max_marks,
                e.min_marks,
                e.exam_date,
                e.start_time,
                e.end_time
            FROM exams e
            JOIN courses c ON e.course_id = c.course_id
            JOIN semesters s ON e.semester_id = s.semester_id
            JOIN subjects sub ON e.subject_id = sub.subject_id
            WHERE e.teacher_id = %s
            ORDER BY e.exam_date DESC
        """, (teacher_id,))
        exams = cursor.fetchall()

        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        exams = []

    return render_template('teacher_dashboard.html', exams=exams, name=session.get('email'))

@app.route('/view_exam/<int:exam_id>')
def view_exam(exam_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Fetch exam details with course, semester, and subject names
        cursor.execute("""
            SELECT 
                e.exam_id,
                e.exam_name,
                e.course_id,
                c.course_name,
                e.semester_id,
                s.semester_name,
                e.subject_id,
                sub.subject_name,
                e.topic,
                e.max_marks,
                e.min_marks,
                e.exam_date,
                e.start_time,
                e.end_time
            FROM exams e
            JOIN courses c ON e.course_id = c.course_id
            JOIN semesters s ON e.semester_id = s.semester_id
            JOIN subjects sub ON e.subject_id = sub.subject_id
            WHERE e.exam_id = %s AND e.teacher_id = %s
        """, (exam_id, session['user_id']))
        exam = cursor.fetchone()

        if not exam:
            flash("Exam not found or you don't have permission to view it.", "error")
            cursor.close()
            conn.close()
            return redirect('/teacher_dashboard')

        # Fetch questions for the exam
        cursor.execute("""
            SELECT 
                question_id,
                question_text,
                model_answer,
                max_score
            FROM questions
            WHERE exam_id = %s
            ORDER BY question_id
        """, (exam_id,))
        questions = cursor.fetchall()

        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        return redirect('/teacher_dashboard')

    return render_template('view_exam.html', exam=exam, questions=questions, name=session.get('email'))



def parse_time(time_input):
    if isinstance(time_input, timedelta):
        # Convert timedelta to time
        total_seconds = int(time_input.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hours, minutes, seconds)
    
    # Handle string input
    time_formats = ['%H:%M', '%H:%M:%S', '%H:%M:%S.%f']
    for fmt in time_formats:
        try:
            return datetime.strptime(time_input, fmt).time()
        except (ValueError, TypeError):
            continue
    raise ValueError("Invalid time format")

@app.route('/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
def edit_exam(exam_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Fetch exam details
        cursor.execute("""
            SELECT 
                e.exam_id,
                e.exam_name,
                e.course_id,
                c.course_name,
                e.semester_id,
                s.semester_name,
                e.subject_id,
                sub.subject_name,
                e.topic,
                e.max_marks,
                e.min_marks,
                e.exam_date,
                e.start_time,
                e.end_time
            FROM exams e
            JOIN courses c ON e.course_id = c.course_id
            JOIN semesters s ON e.semester_id = s.semester_id
            JOIN subjects sub ON e.subject_id = sub.subject_id
            WHERE e.exam_id = %s AND e.teacher_id = %s
        """, (exam_id, session['user_id']))
        exam = cursor.fetchone()

        if not exam:
            flash("Exam not found or you don't have permission to edit it.", "error")
            cursor.close()
            conn.close()
            return redirect('/teacher_dashboard')

        # Convert timedelta to time for template
        exam['start_time'] = parse_time(exam['start_time'])
        exam['end_time'] = parse_time(exam['end_time'])

        # Fetch questions
        cursor.execute("""
            SELECT 
                question_id,
                question_text,
                model_answer,
                max_score
            FROM questions
            WHERE exam_id = %s
            ORDER BY question_id
        """, (exam_id,))
        questions = cursor.fetchall()

        if request.method == 'POST':
            # Handle form submission
            exam_name = request.form.get('exam_name', '').strip()
            topic = request.form.get('topic', '').strip()
            min_passing_percentage = request.form.get('min_passing_percentage', '').strip()
            exam_date = request.form.get('exam_date', '').strip()
            start_time = request.form.get('start_time', '').strip()
            end_time = request.form.get('end_time', '').strip()
            
            # Validation
            errors = []
            if not exam_name or len(exam_name) < 2 or len(exam_name) > 255:
                errors.append("Exam name must be 2–255 characters.")
            if not topic or len(topic) < 2 or len(topic) > 255:
                errors.append("Topic must be 2–255 characters.")
            try:
                min_passing_percentage = float(min_passing_percentage)
                if min_passing_percentage < 0 or min_passing_percentage > 100:
                    errors.append("Minimum passing percentage must be 0–100.")
            except ValueError:
                errors.append("Minimum passing percentage must be a number.")
            try:
                exam_date = datetime.strptime(exam_date, '%Y-%m-%d').date()
                if exam_date < datetime.now().date():
                    errors.append("Exam date cannot be in the past.")
            except ValueError:
                errors.append("Invalid exam date. Use YYYY-MM-DD.")
            try:
                start_time = parse_time(start_time)
                end_time = parse_time(end_time)
                if start_time >= end_time:
                    errors.append("End time must be after start time.")
            except ValueError:
                errors.append("Invalid start or end time. Use HH:MM format (e.g., 14:30).")
            
            # Validate and collect updated question marks
            new_max_marks = 0
            updated_questions = []
            for q in questions:
                mark_key = f"marks_{q['question_id']}"
                if mark_key in request.form:
                    try:
                        max_score = float(request.form[mark_key])
                        if max_score < 0:
                            errors.append(f"Marks for question {q['question_id']} cannot be negative.")
                        updated_questions.append({
                            'question_id': q['question_id'],
                            'max_score': max_score
                        })
                        new_max_marks += max_score
                    except ValueError:
                        errors.append(f"Invalid mark value for question {q['question_id']}.")
            
            if errors:
                for e in errors:
                    flash(e, "error")
                cursor.close()
                conn.close()
                return render_template('edit_exam.html', exam=exam, questions=questions, name=session.get('email'), errors=errors)
            
            # Calculate min_marks
            min_marks = int((min_passing_percentage / 100) * new_max_marks)
            
            # Update exams table
            try:
                cursor.execute("""
                    UPDATE exams
                    SET exam_name = %s, topic = %s, max_marks = %s, min_marks = %s, exam_date = %s, start_time = %s, end_time = %s
                    WHERE exam_id = %s AND teacher_id = %s
                """, (exam_name, topic, new_max_marks, min_marks, exam_date, start_time, end_time, exam_id, session['user_id']))
                
                # Update questions
                for q in updated_questions:
                    cursor.execute("""
                        UPDATE questions
                        SET max_score = %s
                        WHERE question_id = %s AND exam_id = %s
                    """, (q['max_score'], q['question_id'], exam_id))
                
                conn.commit()
                flash("Exam updated successfully!", "success")
                cursor.close()
                conn.close()
                return redirect('/teacher_dashboard')
            except mysql.connector.Error as err:
                flash(f"Database error: {err}", "error")
                cursor.close()
                conn.close()
                return render_template('edit_exam.html', exam=exam, questions=questions, name=session.get('email'), errors=errors)
        
        cursor.close()
        conn.close()
        return render_template('edit_exam.html', exam=exam, questions=questions, name=session.get('email'))
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        return redirect('/teacher_dashboard')

# Custom Jinja2 filter for formatting time
def strftime(value, format_string):
    if value is None:
        return ""
    if isinstance(value, timedelta):
        # Convert timedelta to time
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        value = time(hours, minutes, seconds)
    return value.strftime(format_string)

app.jinja_env.filters['strftime'] = strftime



@app.route('/teacher/complete_profile', methods=['GET', 'POST'])
def complete_teacher_profile():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Fetch existing teacher profile
    cursor.execute("SELECT * FROM teachers WHERE teacher_id = %s", (session['user_id'],))
    existing_profile = cursor.fetchone()

    if request.method == 'POST':
        # Case 1: Profile already complete
        if existing_profile and all([
            existing_profile.get('full_name'),
            existing_profile.get('dob'),
            existing_profile.get('last_degree'),
            existing_profile.get('contact'),
            existing_profile.get('gender'),
            existing_profile.get('address'),
            existing_profile.get('expertise'),
            existing_profile.get('subjects_taught'),
            existing_profile.get('experience_years') is not None,
            existing_profile.get('industry_experience_years') is not None,
            existing_profile.get('research_papers') is not None,
            existing_profile.get('department'),
            existing_profile.get('university')
        ]):
            flash("Profile already completed.", "info")
            cursor.close()
            conn.close()
            return redirect('/teacher_dashboard')

        # Case 2: Skip button
        if request.form.get('skip') == '1':
            cursor.close()
            conn.close()
            return redirect('/teacher_dashboard')

        # Get inputs
        full_name = request.form.get('full_name', '').strip()
        dob = request.form.get('dob', '').strip()
        last_degree = request.form.get('last_degree', '').strip()
        contact = request.form.get('contact', '').strip()
        gender = request.form.get('gender', '').strip()
        address = request.form.get('address', '').strip()
        expertise = request.form.get('expertise', '').strip()
        subjects_taught = request.form.get('subjects_taught', '').strip()
        experience_years = request.form.get('experience_years', '').strip()
        industry_experience_years = request.form.get('industry_experience_years', '').strip()
        research_papers = request.form.get('research_papers', '').strip()
        department = request.form.get('department', '').strip()
        university = request.form.get('university', '').strip()

        # ---------- VALIDATION ----------
        errors = []

        # Full name: letters and spaces only
        if not re.match(r'^[A-Za-z ]{3,50}$', full_name):
            errors.append("Full name must be 3–50 alphabetic characters.")

        # DOB: valid date & realistic (e.g., teacher age > 21 years)
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            age = (datetime.now().date() - dob_date).days // 365
            if age < 21:
                errors.append("Teacher must be at least 21 years old.")
        except ValueError:
            errors.append("Invalid date format for DOB. Use YYYY-MM-DD.")

        # Last degree: not empty
        if len(last_degree) < 2:
            errors.append("Last degree must be at least 2 characters.")

        # Contact: numeric and length 10 digits
        if not re.match(r'^\d{10}$', contact):
            errors.append("Contact number must be exactly 10 digits.")

        # Gender: must be one of fixed values
        if gender not in ['Male', 'Female', 'Other']:
            errors.append("Invalid gender selected.")

        # Address: not empty
        if len(address) < 5:
            errors.append("Address must be at least 5 characters.")

        # Expertise: not empty
        if len(expertise) < 2:
            errors.append("Expertise must be at least 2 characters.")

        # Subjects taught: not empty
        if len(subjects_taught) < 2:
            errors.append("Subjects taught must be at least 2 characters.")

        # Experience years: non-negative integer
        try:
            experience_years = int(experience_years)
            if experience_years < 0:
                errors.append("Experience years cannot be negative.")
        except ValueError:
            errors.append("Experience years must be a valid number.")

        # Industry experience years: non-negative integer
        try:
            industry_experience_years = int(industry_experience_years)
            if industry_experience_years < 0:
                errors.append("Industry experience years cannot be negative.")
        except ValueError:
            errors.append("Industry experience years must be a valid number.")

        # Research papers: non-negative integer
        try:
            research_papers = int(research_papers)
            if research_papers < 0:
                errors.append("Research papers cannot be negative.")
        except ValueError:
            errors.append("Research papers must be a valid number.")

        # Department: not empty
        if len(department) < 2:
            errors.append("Department must be at least 2 characters.")

        # University: not empty
        if len(university) < 2:
            errors.append("University name must be at least 2 characters.")

        # If validation failed
        if errors:
            for e in errors:
                flash(e, "error")
            cursor.close()
            conn.close()
            return render_template('complete_teacher_profile.html', name=session.get('email'))

        # ---------- SAVE TO DB ----------
        try:
            if existing_profile:
                # Update existing
                cursor.execute("""
                    UPDATE teachers 
                    SET full_name=%s, dob=%s, last_degree=%s, contact=%s, gender=%s,
                        address=%s, expertise=%s, subjects_taught=%s,
                        experience_years=%s, industry_experience_years=%s,
                        research_papers=%s, department=%s, university=%s
                    WHERE teacher_id=%s
                """, (
                    full_name, dob_date, last_degree, contact, gender,
                    address, expertise, subjects_taught,
                    experience_years, industry_experience_years,
                    research_papers, department, university, session['user_id']
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO teachers (
                        teacher_id, full_name, dob, last_degree, contact, gender, address,
                        expertise, subjects_taught, experience_years, industry_experience_years,
                        research_papers, department, university
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    session['user_id'], full_name, dob_date, last_degree, contact, gender,
                    address, expertise, subjects_taught,
                    experience_years, industry_experience_years,
                    research_papers, department, university
                ))
            conn.commit()
            flash("Profile completed successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")

        cursor.close()
        conn.close()
        return redirect('/teacher_dashboard')

    # GET request
    cursor.close()
    conn.close()
    return render_template('complete_teacher_profile.html', name=session.get('email'))




# Add or update these routes in app.py for teacher profile display and edit

from datetime import datetime
import mysql.connector
from flask import render_template, request, redirect, flash, session
import re

@app.route('/teacher/profile')
def teacher_profile_display():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.full_name, t.dob, t.last_degree, t.contact, t.gender, t.address, t.expertise, 
                   t.subjects_taught, t.experience_years, t.industry_experience_years, t.research_papers, 
                   t.department, t.university, u.email
            FROM teachers t
            JOIN users u ON t.teacher_id = u.uid
            WHERE t.teacher_id = %s
            """,
            (session['user_id'],)
        )
        profile = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not profile:
            flash("No profile found. Please complete your profile.", "warning")
            return redirect('/teacher/complete_profile')
        
        return render_template('teacher_profile.html', profile=profile, email=profile[13], name=session.get('email'))
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        return redirect('/teacher_dashboard')

@app.route('/teacher/edit_profile', methods=['GET', 'POST'])
def teacher_edit_profile():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.full_name, t.dob, t.last_degree, t.contact, t.gender, t.address, t.expertise, 
                   t.subjects_taught, t.experience_years, t.industry_experience_years, t.research_papers, 
                   t.department, t.university, u.email
            FROM teachers t
            JOIN users u ON t.teacher_id = u.uid
            WHERE t.teacher_id = %s
            """,
            (session['user_id'],)
        )
        profile = cursor.fetchone()
        
        if request.method == 'POST':
            full_name = request.form.get('full_name', '').strip()
            dob = request.form.get('dob', '').strip()
            last_degree = request.form.get('last_degree', '').strip()
            contact = request.form.get('contact', '').strip()
            gender = request.form.get('gender', '').strip()
            address = request.form.get('address', '').strip()
            expertise = request.form.get('expertise', '').strip()
            subjects_taught = request.form.get('subjects_taught', '').strip()
            experience_years = request.form.get('experience_years', '').strip()
            industry_experience_years = request.form.get('industry_experience_years', '').strip()
            research_papers = request.form.get('research_papers', '').strip()
            department = request.form.get('department', '').strip()
            university = request.form.get('university', '').strip()

            # ---------- VALIDATION ----------
            errors = []

            # Full name: letters and spaces only
            if not re.match(r'^[A-Za-z ]{3,50}$', full_name):
                errors.append("Full name must be 3–50 alphabetic characters.")

            # DOB: valid date & realistic (e.g., teacher age > 21 years)
            try:
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                age = (datetime.now().date() - dob_date).days // 365
                if age < 21:
                    errors.append("Teacher must be at least 21 years old.")
            except ValueError:
                errors.append("Invalid date format for DOB. Use YYYY-MM-DD.")

            # Last degree: not empty
            if len(last_degree) < 2:
                errors.append("Last degree must be at least 2 characters.")

            # Contact: numeric and length 10 digits
            if not re.match(r'^\d{10}$', contact):
                errors.append("Contact number must be exactly 10 digits.")

            # Gender: must be one of fixed values
            if gender not in ['Male', 'Female', 'Other']:
                errors.append("Invalid gender selected.")

            # Address: not empty
            if len(address) < 5:
                errors.append("Address must be at least 5 characters.")

            # Expertise: not empty
            if len(expertise) < 2:
                errors.append("Expertise must be at least 2 characters.")

            # Subjects taught: not empty
            if len(subjects_taught) < 2:
                errors.append("Subjects taught must be at least 2 characters.")

            # Experience years: non-negative integer
            try:
                experience_years = int(experience_years)
                if experience_years < 0:
                    errors.append("Experience years cannot be negative.")
            except ValueError:
                errors.append("Experience years must be a valid number.")

            # Industry experience years: non-negative integer
            try:
                industry_experience_years = int(industry_experience_years)
                if industry_experience_years < 0:
                    errors.append("Industry experience years cannot be negative.")
            except ValueError:
                errors.append("Industry experience years must be a valid number.")

            # Research papers: non-negative integer
            try:
                research_papers = int(research_papers)
                if research_papers < 0:
                    errors.append("Research papers cannot be negative.")
            except ValueError:
                errors.append("Research papers must be a valid number.")

            # Department: not empty
            if len(department) < 2:
                errors.append("Department must be at least 2 characters.")

            # University: not empty
            if len(university) < 2:
                errors.append("University name must be at least 2 characters.")

            if errors:
                for e in errors:
                    flash(e, "error")
                cursor.close()
                conn.close()
                return render_template('teacher_edit_profile.html', profile=profile, email=profile[13] if profile else session.get('email'), name=session.get('email'))

            cursor.execute(
                """
                UPDATE teachers 
                SET full_name=%s, dob=%s, last_degree=%s, contact=%s, gender=%s,
                    address=%s, expertise=%s, subjects_taught=%s,
                    experience_years=%s, industry_experience_years=%s,
                    research_papers=%s, department=%s, university=%s
                WHERE teacher_id=%s
                """,
                (
                    full_name, dob_date, last_degree, contact, gender,
                    address, expertise, subjects_taught,
                    experience_years, industry_experience_years,
                    research_papers, department, university, session['user_id']
                )
            )
            conn.commit()
            flash("Profile updated successfully!", "success")
            cursor.close()
            conn.close()
            return redirect('/teacher/profile')
        
        cursor.close()
        conn.close()
        return render_template('teacher_edit_profile.html', profile=profile, email=profile[13] if profile else session.get('email'), name=session.get('email'))
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        return redirect('/teacher_dashboard')
    
    

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please log in as a teacher.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch courses (assuming teacher has access to all courses; adjust if teacher-specific)
        cursor.execute("SELECT course_id, course_name FROM courses")
        courses = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        courses = []

    if request.method == 'POST':
        if 'upload_excel' in request.form:
            # Step 1: Handle selection and Excel upload/validation
            course_id = request.form.get('course_id')
            semester_id = request.form.get('semester_id')
            subject_id = request.form.get('subject_id')
            topic = request.form.get('topic', '').strip()
            
            # Validation for selections
            errors = []
            if not course_id or not course_id.isdigit():
                errors.append("Course is required.")
            if not semester_id or not semester_id.isdigit():
                errors.append("Semester is required.")
            if not subject_id or not subject_id.isdigit():
                errors.append("Subject is required.")
            if not topic or len(topic) < 2 or len(topic) > 255:
                errors.append("Topic must be 2–255 characters.")
            
            if 'excel_file' not in request.files:
                errors.append("No Excel file uploaded.")
            
            file = request.files['excel_file']
            if file.filename == '':
                errors.append("No selected file.")
            if file and not allowed_file(file.filename):
                errors.append("Invalid file type. Only XLS/XLSX allowed.")
            
            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template('create_exam.html', courses=courses, name=session.get('email'), errors=errors)
            
            # Save the file temporarily
            filename = secure_filename(file.filename)
            upload_folder = 'static/uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Read and validate Excel
            try:
                df = pd.read_excel(file_path)
                # Normalize column names (case-insensitive for validation)
                normalized_columns = [col.strip().lower() for col in df.columns]
                
                # Expected columns
                required_columns = {'question', 'answer', 'maximum marks'}
                if not required_columns.issubset(normalized_columns):
                    flash("Excel must have columns: Question, Answer, Maximum Marks (case-insensitive).", "error")
                    os.remove(file_path)
                    return render_template('create_exam.html', courses=courses, name=session.get('email'))
                
                # Create a mapping from normalized to original columns
                column_mapping = {col.strip().lower(): col for col in df.columns}
                # Rename columns to standard internal names
                df = df.rename(columns={
                    column_mapping.get('question', 'Question'): 'question_text',
                    column_mapping.get('answer', 'Answer'): 'model_answer',
                    column_mapping.get('maximum marks', 'Maximum Marks'): 'max_score'
                })
                
                # Validate max_score are numbers
                errors = []
                for idx, row in df.iterrows():
                    try:
                        max_score = float(row['max_score'])
                        if max_score < 0:
                            errors.append(f"Invalid maximum marks at row {idx + 2}: must be a non-negative number.")
                    except (ValueError, TypeError):
                        errors.append(f"Invalid maximum marks at row {idx + 2}: must be a number (found '{row['max_score']}').")
                
                if errors:
                    for e in errors:
                        flash(e, "error")
                    os.remove(file_path)
                    return render_template('create_exam.html', courses=courses, name=session.get('email'), errors=errors)
                
                # Convert max_score to Python float for JSON serialization
                df['max_score'] = df['max_score'].astype(float)
                questions = df.to_dict('records')
                for q in questions:
                    q['max_score'] = float(q['max_score'])
                    q['question_text'] = str(q['question_text'])
                    q['model_answer'] = str(q['model_answer'])
                
                # Calculate total max_marks
                total_max_marks = float(df['max_score'].sum())
                
                # Store data in session
                session['temp_exam_data'] = {
                    'course_id': course_id,
                    'semester_id': semester_id,
                    'subject_id': subject_id,
                    'topic': topic,
                    'questions': questions,
                    'max_marks': total_max_marks,
                    'question_excel_path': file_path
                }
                
                return render_template('create_exam.html', courses=courses, name=session.get('email'), questions=questions, 
                                     course_id=course_id, semester_id=semester_id, subject_id=subject_id, topic=topic, 
                                     max_marks=total_max_marks, show_final_form=False, change_marks=False)
            
            except Exception as e:
                flash(f"Error processing Excel: {str(e)}", "error")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return render_template('create_exam.html', courses=courses, name=session.get('email'))
        
        elif 'confirm_max_marks' in request.form:
            # Step 2: Confirm max_marks, show final form
            if 'temp_exam_data' not in session:
                flash("No exam data found. Please start over.", "error")
                return render_template('create_exam.html', courses=courses, name=session.get('email'))
            
            temp_data = session['temp_exam_data']
            return render_template('create_exam.html', courses=courses, name=session.get('email'), 
                                 questions=temp_data['questions'], course_id=temp_data['course_id'], 
                                 semester_id=temp_data['semester_id'], subject_id=temp_data['subject_id'], 
                                 topic=temp_data['topic'], max_marks=temp_data['max_marks'], 
                                 show_final_form=True, change_marks=False)
        
        elif 'change_max_marks' in request.form:
            # Step 3: Show editable marks table
            if 'temp_exam_data' not in session:
                flash("No exam data found. Please start over.", "error")
                return render_template('create_exam.html', courses=courses, name=session.get('email'))
            
            temp_data = session['temp_exam_data']
            return render_template('create_exam.html', courses=courses, name=session.get('email'), 
                                 questions=temp_data['questions'], course_id=temp_data['course_id'], 
                                 semester_id=temp_data['semester_id'], subject_id=temp_data['subject_id'], 
                                 topic=temp_data['topic'], max_marks=temp_data['max_marks'], 
                                 show_final_form=False, change_marks=True)
        
        elif 'update_marks' in request.form:
            # Step 4: Update marks from editable table
            if 'temp_exam_data' not in session:
                flash("No exam data found. Please start over.", "error")
                return render_template('create_exam.html', courses=courses, name=session.get('email'))
            
            temp_data = session['temp_exam_data']
            questions = temp_data['questions']
            new_max_marks = 0
            errors = []
            
            for idx, q in enumerate(questions):
                mark_key = f"marks_{idx + 1}"
                if mark_key in request.form:
                    try:
                        max_score = float(request.form[mark_key])
                        if max_score < 0:
                            errors.append(f"Marks for question {idx + 1} cannot be negative.")
                        q['max_score'] = float(max_score)
                        new_max_marks += max_score
                    except ValueError:
                        errors.append(f"Invalid mark value for question {idx + 1}.")
            
            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template('create_exam.html', courses=courses, name=session.get('email'), 
                                     questions=questions, course_id=temp_data['course_id'], 
                                     semester_id=temp_data['semester_id'], subject_id=temp_data['subject_id'], 
                                     topic=temp_data['topic'], max_marks=new_max_marks, 
                                     show_final_form=False, change_marks=True, errors=errors)
            
            # Update max_marks in session
            temp_data['max_marks'] = float(new_max_marks)
            session['temp_exam_data'] = temp_data
            
            return render_template('create_exam.html', courses=courses, name=session.get('email'), 
                                 questions=questions, course_id=temp_data['course_id'], 
                                 semester_id=temp_data['semester_id'], subject_id=temp_data['subject_id'], 
                                 topic=temp_data['topic'], max_marks=new_max_marks, 
                                 show_final_form=False, change_marks=False)
        
        elif 'final_submit' in request.form:
            # Step 5: Handle final submission
            if 'temp_exam_data' not in session:
                flash("No exam data found. Please start over.", "error")
                return render_template('create_exam.html', courses=courses, name=session.get('email'))
            
            temp_data = session.pop('temp_exam_data')
            course_id = temp_data['course_id']
            semester_id = temp_data['semester_id']
            subject_id = temp_data['subject_id']
            topic = temp_data['topic']
            max_marks = temp_data['max_marks']
            file_path = temp_data['question_excel_path']
            questions = temp_data['questions']
            
            min_passing_percentage = request.form.get('min_passing_percentage', '').strip()
            exam_date = request.form.get('exam_date', '').strip()
            start_time = request.form.get('start_time', '').strip()
            end_time = request.form.get('end_time', '').strip()
            
            # Validation for final fields
            errors = []
            try:
                min_passing_percentage = float(min_passing_percentage)
                if min_passing_percentage < 0 or min_passing_percentage > 100:
                    errors.append("Minimum passing percentage must be 0–100.")
            except ValueError:
                errors.append("Minimum passing percentage must be a number.")
            
            try:
                exam_date = datetime.strptime(exam_date, '%Y-%m-%d').date()
                if exam_date < datetime.now().date():
                    errors.append("Exam date cannot be in the past.")
            except ValueError:
                errors.append("Invalid exam date. Use YYYY-MM-DD.")
            
            try:
                start_time = datetime.strptime(start_time, '%H:%M').time()
                end_time = datetime.strptime(end_time, '%H:%M').time()
                if start_time >= end_time:
                    errors.append("End time must be after start time.")
            except ValueError:
                errors.append("Invalid start or end time. Use HH:MM.")
            
            if errors:
                for e in errors:
                    flash(e, "error")
                # Restore session data to allow retry
                session['temp_exam_data'] = temp_data
                return render_template('create_exam.html', courses=courses, name=session.get('email'), 
                                     questions=questions, course_id=course_id, semester_id=semester_id, 
                                     subject_id=subject_id, topic=topic, max_marks=max_marks, 
                                     show_final_form=True, change_marks=False, errors=errors)
            
            # Calculate min_marks
            min_marks = int((min_passing_percentage / 100) * max_marks)
            
            # Insert into exams table
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                
                exam_name = f"{topic} Exam"
                
                cursor.execute(
                    """
                    INSERT INTO exams (exam_name, teacher_id, course_id, semester_id, subject_id, topic, question_excel_path, 
                                       max_marks, min_marks, exam_date, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (exam_name, session['user_id'], course_id, semester_id, subject_id, topic, file_path, 
                     max_marks, min_marks, exam_date, start_time, end_time)
                )
                exam_id = cursor.lastrowid
                
                # Bulk insert questions
                for q in questions:
                    cursor.execute(
                        """
                        INSERT INTO questions (exam_id, course_id, semester_id, subject_id, question_text, model_answer, max_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (exam_id, course_id, semester_id, subject_id, q['question_text'], q['model_answer'], q['max_score'])
                    )
                
                conn.commit()
                flash("Exam created successfully!", "success")
                
                cursor.close()
                conn.close()
            except mysql.connector.Error as err:
                flash(f"Database error: {err}", "error")
                # Restore session data to allow retry
                session['temp_exam_data'] = temp_data
                return render_template('create_exam.html', courses=courses, name=session.get('email'), 
                                     questions=questions, course_id=course_id, semester_id=semester_id, 
                                     subject_id=subject_id, topic=topic, max_marks=max_marks, 
                                     show_final_form=True, change_marks=False)
            
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return redirect('/teacher_dashboard')
        
    return render_template('create_exam.html', courses=courses, name=session.get('email'))

@app.route('/teacher/get_semesters/<course_id>')
def teacher_get_semesters(course_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT semester_id, semester_name FROM semesters WHERE course_id = %s",
            (course_id,)
        )
        semesters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return jsonify({'semesters': semesters})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500

@app.route('/teacher/get_subjects/<semester_id>')
def teacher_get_subjects(semester_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT subject_id, subject_name FROM subjects WHERE semester_id = %s",
            (semester_id,)
        )
        subjects = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return jsonify({'subjects': subjects})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500    
        
    


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
        cursor = conn.cursor(dictionary=True)  # dictionary=True so you can access by column name

        cursor.execute("""
            SELECT 
                t.teacher_id,
                u.email,
                u.role,
                t.full_name,
                t.dob,
                t.last_degree,
                t.contact,
                t.gender,
                t.address,
                t.expertise,
                t.subjects_taught,
                t.experience_years,
                t.industry_experience_years,
                t.research_papers,
                t.department,
                t.university
            FROM teachers t
            JOIN users u ON t.teacher_id = u.uid
        """)
        teachers = cursor.fetchall()

        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        teachers = []

    return render_template('admin_teachers.html', teachers=teachers, name=session.get('email'))



# ---------------- DOWNLOAD TEACHER TEMPLATE ----------------
@app.route('/admin/download_teacher_template')
def download_teacher_template():
    # Create a sample dataframe
    df = pd.DataFrame({
        "email": [
            "teacher1@example.com",
            "teacher2@example.com",
            "teacher3@example.com"
        ]
    })

    # Save to in-memory buffer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Teachers")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="teacher_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ---------------- UPLOAD TEACHERS EXCEL ----------------
@app.route('/admin/upload_teachers_excel', methods=['POST'])
def upload_teachers_excel():
    if 'excel_file' not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for('admin_teachers'))

    file = request.files['excel_file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for('admin_teachers'))

    try:
        df = pd.read_excel(file)

        if 'email' not in df.columns:
            flash("Excel file must contain 'email' column", "error")
            return redirect(url_for('admin_teachers'))

        emails = df['email'].dropna().tolist()

        # Validate all emails
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_emails = [email for email in emails if not re.match(email_pattern, email)]

        if invalid_emails:
            flash(f"Invalid emails found: {', '.join(invalid_emails)}", "error")
            return redirect(url_for('admin_teachers'))

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        added_count = 0
        for email in emails:
            # Check if email already exists
            cursor.execute("SELECT uid FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                continue  # skip already registered teachers

            # Generate password + hash
            password_plain = generate_password(12)
            password_hashed = generate_password_hash(password_plain)

            # Insert into users table
            cursor.execute("""
                INSERT INTO users (email, password, role)
                VALUES (%s, %s, %s)
            """, (email, password_hashed, 'teacher'))
            uid = cursor.lastrowid  # get generated uid

            # Insert into teachers table with only uid (other cols NULL/empty)
            cursor.execute("""
                INSERT INTO teachers (
                    teacher_id, full_name, dob, last_degree, contact, gender,
                    address, expertise, subjects_taught, experience_years,
                    industry_experience_years, research_papers, department, university
                )
                VALUES (
                    %s, 'Not Provided', NULL, 'Not Provided', 'Not Provided', 'Not Provided',
                    'Not Provided', 'Not Provided', 'Not Provided', 0,
                    0, 0, 'Not Provided', 'Not Provided'
                )
            """, (uid,))


            # Send email with login details
            subject = "EduAI Teacher Registration Successful"
            body = f"""
            Dear Teacher,

            Your registration on EduAI was successful.

            Login Details:
            Email: {email}
            Temporary Password: {password_plain}

            Please log in and update your profile & change your password immediately.

            Regards,
            EduAI Team
            """
            send_email(email, subject, body)

            added_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        if added_count > 0:
            flash(f"Successfully registered {added_count} teachers and sent credentials.", "success")
        else:
            flash("No new teachers were added (all emails already registered).", "info")

    except Exception as e:
        flash(f"Error processing file: {str(e)}", "error")

    return redirect(url_for('admin_teachers'))




@app.route('/admin/upload_students_excel', methods=['POST'])
def upload_students_excel():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect(url_for('login'))

    if 'excel_file' not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for('admin_students'))

    file = request.files['excel_file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for('admin_students'))

    course_id = request.form.get('course_id')
    semester_id = request.form.get('semester_id')

    if not course_id or not semester_id:
        flash("Course and semester must be selected.", "error")
        return redirect(url_for('admin_students'))

    try:
        # Step 1: Read Excel
        df = pd.read_excel(file)

        # Step 2: Check required columns
        required_columns = ['email', 'roll_no', 'enroll_no']
        if not all(col in df.columns for col in required_columns):
            flash("Excel file must contain 'email', 'roll_no', and 'enroll_no' columns", "error")
            return redirect(url_for('admin_students'))

        df = df[required_columns].dropna()
        emails = df['email'].tolist()
        roll_nos = df['roll_no'].tolist()
        enroll_nos = df['enroll_no'].tolist()

        # Step 3: Validate emails
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_emails = [email for email in emails if not re.match(email_pattern, email)]
        if invalid_emails:
            flash(f"Invalid emails found: {', '.join(invalid_emails)}", "error")
            return redirect(url_for('admin_students'))

        # Step 4: Validate DB uniqueness
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        existing_emails, existing_roll_nos, existing_enroll_nos = [], [], []
        for email, roll_no, enroll_no in zip(emails, roll_nos, enroll_nos):
            cursor.execute("SELECT uid FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                existing_emails.append(email)

            cursor.execute("SELECT student_id FROM students WHERE roll_no = %s", (roll_no,))
            if cursor.fetchone():
                existing_roll_nos.append(roll_no)

            cursor.execute("SELECT student_id FROM students WHERE enrollment_no = %s", (enroll_no,))
            if cursor.fetchone():
                existing_enroll_nos.append(enroll_no)

        if existing_emails or existing_roll_nos or existing_enroll_nos:
            errors = []
            if existing_emails:
                errors.append(f"Emails already registered: {', '.join(existing_emails)}")
            if existing_roll_nos:
                errors.append(f"Roll numbers already exist: {', '.join(map(str, existing_roll_nos))}")
            if existing_enroll_nos:
                errors.append(f"Enrollment numbers already exist: {', '.join(map(str, existing_enroll_nos))}")

            for error in errors:
                flash(error, "error")
            cursor.close()
            conn.close()
            return redirect(url_for('admin_students'))

        # Step 5: Insert into DB (prepare data first, no emails yet)
        added_students = []  # [(email, plain_password)]
        for email, roll_no, enroll_no in zip(emails, roll_nos, enroll_nos):
            password_plain = generate_password(12)
            password_hashed = generate_password_hash(password_plain)

            # Insert into users
            cursor.execute("""
                INSERT INTO users (email, password, role)
                VALUES (%s, %s, %s)
            """, (email, password_hashed, 'student'))
            uid = cursor.lastrowid

            # Insert into students
            cursor.execute("""
                INSERT INTO students (
                    student_id, full_name, roll_no, enrollment_no, contact, dob,
                    course_id, semester_id, gender, address, department, university
                )
                VALUES (
                    %s, 'Not Provided', %s, %s, 'Not Provided', NULL,
                    %s, %s, 'Not Provided', 'Not Provided', 'Not Provided', 'Not Provided'
                )
            """, (uid, roll_no, enroll_no, course_id, semester_id))

            added_students.append((email, password_plain))

        conn.commit()
        cursor.close()
        conn.close()

        # Step 6: Send emails after commit succeeded
        for email, password_plain in added_students:
            subject = "EduAI Student Registration Successful"
            body = f"""
            Dear Student,

            Your registration on EduAI was successful.

            Login Details:
            Email: {email}
            Temporary Password: {password_plain}

            Please log in and update your profile & change your password immediately.

            Regards,
            EduAI Team
            """
            send_email(email, subject, body)

        if added_students:
            flash(f"Successfully registered {len(added_students)} students and sent credentials.", "success")
        else:
            flash("No new students were added.", "info")

    except Exception as e:
        flash(f"Error processing file: {str(e)}", "error")

    return redirect(url_for('admin_students'))




@app.route('/admin/students', methods=['GET', 'POST'])
def admin_students():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect(url_for('login'))
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch courses for the upload and filter forms
        cursor.execute("SELECT course_id, course_name FROM courses")
        courses = cursor.fetchall()
        
        # Get filter parameters from the request
        course_id = request.form.get('course_id') if request.method == 'POST' else request.args.get('course_id')
        semester_id = request.form.get('semester_id') if request.method == 'POST' else request.args.get('semester_id')
        
        # Convert to integers and validate
        try:
            course_id = int(course_id) if course_id else None
            semester_id = int(semester_id) if semester_id else None
        except (ValueError, TypeError):
            course_id = None
            semester_id = None
            flash("Invalid course or semester selection.", "error")
        
        # Build the SQL query with optional filters
        query = """
            SELECT 
                s.student_id, s.full_name, s.roll_no, s.enrollment_no, s.contact, s.dob,
                s.course_id, c.course_name, s.semester_id, sem.semester_name,
                s.gender, s.address, s.department, s.university
            FROM students s
            LEFT JOIN courses c ON s.course_id = c.course_id
            LEFT JOIN semesters sem ON s.semester_id = sem.semester_id
        """
        params = []
        conditions = []
        
        if course_id:
            conditions.append("s.course_id = %s")
            params.append(course_id)
        if semester_id:
            conditions.append("s.semester_id = %s")
            params.append(semester_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Debug: Log query and parameters
        print(f"Query: {query}, Params: {params}")
        
        # Fetch students
        cursor.execute(query, params)
        students = cursor.fetchall()
        
        # Debug: Log number of students fetched
        print(f"Fetched {len(students)} students")
        
        cursor.close()
        conn.close()
        return render_template('admin_students.html', courses=courses, students=students, name=session.get('email'), 
                             selected_course_id=course_id, selected_semester_id=semester_id)
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "error")
        return redirect(url_for('admin_dashboard'))
    
            
    
@app.route('/admin/get_semesters/<int:course_id>')
def admin_get_semesters(course_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT semester_id, semester_name FROM semesters WHERE course_id = %s", (course_id,))
        semesters = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(semesters)
    except mysql.connector.Error as e:
        return jsonify([]), 500


@app.route('/admin/courses_semesters')
def admin_courses_semesters():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch courses with semester count
        cursor.execute(
            """
            SELECT c.course_id, c.course_name, c.description, 
                   COUNT(s.semester_id) AS semester_count
            FROM courses c
            LEFT JOIN semesters s ON c.course_id = s.course_id
            GROUP BY c.course_id, c.course_name, c.description
            """
        )
        courses = cursor.fetchall()
        
        # Fetch semesters with course names
        cursor.execute(
            """
            SELECT s.semester_id, c.course_name, s.semester_name, s.start_date, s.end_date, s.course_id
            FROM semesters s
            JOIN courses c ON s.course_id = c.course_id
            """
        )
        semesters = cursor.fetchall()
        
        # Fetch subjects with course and semester names
        cursor.execute(
            """
            SELECT sub.subject_id, c.course_name, s.semester_name, sub.subject_name, sub.course_id, sub.semester_id
            FROM subjects sub
            JOIN courses c ON sub.course_id = c.course_id
            JOIN semesters s ON sub.semester_id = s.semester_id
            """
        )
        subjects = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        courses = []
        semesters = []
        subjects = []

    return render_template('admin_courses_semesters.html', courses=courses, semesters=semesters, 
                         subjects=subjects, name=session.get('email'), 
                         course_to_edit=None, semester_to_edit=None, subject_to_edit=None)

@app.route('/admin/add_course', methods=['POST'])
def admin_add_course():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    course_name = request.form.get('course_name', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validation
    errors = []
    if not course_name or len(course_name) < 2 or len(course_name) > 100:
        errors.append("Course name must be 2–100 characters.")
    if len(description) > 65535:  # TEXT field limit in MySQL
        errors.append("Description is too long (max 65535 characters).")
    
    if errors:
        for e in errors:
            flash(e, "error")
        return redirect('/admin/courses_semesters')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if course_name already exists
        cursor.execute("SELECT COUNT(*) FROM courses WHERE course_name = %s", (course_name,))
        if cursor.fetchone()[0] > 0:
            flash("Course name already exists.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Insert new course
        cursor.execute(
            "INSERT INTO courses (course_name, description) VALUES (%s, %s)",
            (course_name, description or None)
        )
        conn.commit()
        flash("Course added successfully!", "success")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
    
    return redirect('/admin/courses_semesters')

@app.route('/admin/add_semester', methods=['POST'])
def admin_add_semester():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    course_id = request.form.get('course_id', '').strip()
    semester_name = request.form.get('semester_name', '').strip()
    start_date = request.form.get('start_date', '').strip()
    end_date = request.form.get('end_date', '').strip()
    
    # Validation
    errors = []
    if not course_id or not course_id.isdigit():
        errors.append("Invalid course selected.")
    if not semester_name or len(semester_name) < 2 or len(semester_name) > 50:
        errors.append("Semester name must be 2–50 characters.")
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if start_date >= end_date:
            errors.append("End date must be after start date.")
    except ValueError:
        errors.append("Invalid date format for start or end date. Use YYYY-MM-DD.")
    
    if errors:
        for e in errors:
            flash(e, "error")
        return redirect('/admin/courses_semesters')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if course_id exists
        cursor.execute("SELECT COUNT(*) FROM courses WHERE course_id = %s", (course_id,))
        if cursor.fetchone()[0] == 0:
            flash("Selected course does not exist.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Check if semester_name already exists for this course
        cursor.execute(
            "SELECT COUNT(*) FROM semesters WHERE course_id = %s AND semester_name = %s",
            (course_id, semester_name)
        )
        if cursor.fetchone()[0] > 0:
            flash("Semester name already exists for this course.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Insert new semester
        cursor.execute(
            "INSERT INTO semesters (course_id, semester_name, start_date, end_date) VALUES (%s, %s, %s, %s)",
            (course_id, semester_name, start_date, end_date)
        )
        conn.commit()
        flash("Semester added successfully!", "success")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
    
    return redirect('/admin/courses_semesters')

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
def admin_edit_course(course_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch the course to edit
        cursor.execute(
            "SELECT course_id, course_name, description FROM courses WHERE course_id = %s",
            (course_id,)
        )
        course_to_edit = cursor.fetchone()
        
        if not course_to_edit:
            flash("Course not found.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        if request.method == 'POST':
            course_name = request.form.get('course_name', '').strip()
            description = request.form.get('description', '').strip()
            
            # Validation
            errors = []
            if not course_name or len(course_name) < 2 or len(course_name) > 100:
                errors.append("Course name must be 2–100 characters.")
            if len(description) > 65535:
                errors.append("Description is too long (max 65535 characters).")
            
            # Check if course_name is unique (excluding the current course)
            cursor.execute(
                "SELECT COUNT(*) FROM courses WHERE course_name = %s AND course_id != %s",
                (course_name, course_id)
            )
            if cursor.fetchone()['COUNT(*)'] > 0:
                errors.append("Course name already exists.")
            
            if errors:
                for e in errors:
                    flash(e, "error")
                # Fetch courses, semesters, and subjects for re-render
                cursor.execute(
                    """
                    SELECT c.course_id, c.course_name, c.description, 
                           COUNT(s.semester_id) AS semester_count
                    FROM courses c
                    LEFT JOIN semesters s ON c.course_id = s.course_id
                    GROUP BY c.course_id, c.course_name, c.description
                    """
                )
                courses = cursor.fetchall()
                
                cursor.execute(
                    """
                    SELECT s.semester_id, c.course_name, s.semester_name, s.start_date, s.end_date, s.course_id
                    FROM semesters s
                    JOIN courses c ON s.course_id = c.course_id
                    """
                )
                semesters = cursor.fetchall()
                
                cursor.execute(
                    """
                    SELECT sub.subject_id, c.course_name, s.semester_name, sub.subject_name, sub.course_id, sub.semester_id
                    FROM subjects sub
                    JOIN courses c ON sub.course_id = c.course_id
                    JOIN semesters s ON sub.semester_id = s.semester_id
                    """
                )
                subjects = cursor.fetchall()
                
                cursor.close()
                conn.close()
                return render_template('admin_courses_semesters.html', courses=courses, semesters=semesters, 
                                     subjects=subjects, name=session.get('email'), 
                                     course_to_edit=course_to_edit, semester_to_edit=None, subject_to_edit=None)
            
            # Update course
            cursor.execute(
                "UPDATE courses SET course_name = %s, description = %s WHERE course_id = %s",
                (course_name, description or None, course_id)
            )
            conn.commit()
            flash("Course updated successfully!", "success")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Fetch courses, semesters, and subjects for display
        cursor.execute(
            """
            SELECT c.course_id, c.course_name, c.description, 
                   COUNT(s.semester_id) AS semester_count
            FROM courses c
            LEFT JOIN semesters s ON c.course_id = s.course_id
            GROUP BY c.course_id, c.course_name, c.description
            """
        )
        courses = cursor.fetchall()
        
        cursor.execute(
            """
            SELECT s.semester_id, c.course_name, s.semester_name, s.start_date, s.end_date, s.course_id
            FROM semesters s
            JOIN courses c ON s.course_id = c.course_id
            """
        )
        semesters = cursor.fetchall()
        
        cursor.execute(
            """
            SELECT sub.subject_id, c.course_name, s.semester_name, sub.subject_name, sub.course_id, sub.semester_id
            FROM subjects sub
            JOIN courses c ON sub.course_id = c.course_id
            JOIN semesters s ON sub.semester_id = s.semester_id
            """
        )
        subjects = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('admin_courses_semesters.html', courses=courses, semesters=semesters, 
                             subjects=subjects, name=session.get('email'), 
                             course_to_edit=course_to_edit, semester_to_edit=None, subject_to_edit=None)
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        return redirect('/admin/courses_semesters')

@app.route('/admin/edit_semester/<int:semester_id>', methods=['GET', 'POST'])
def admin_edit_semester(semester_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch the semester to edit
        cursor.execute(
            """
            SELECT s.semester_id, s.course_id, s.semester_name, s.start_date, s.end_date, c.course_name
            FROM semesters s
            JOIN courses c ON s.course_id = c.course_id
            WHERE s.semester_id = %s
            """,
            (semester_id,)
        )
        semester_to_edit = cursor.fetchone()
        
        if not semester_to_edit:
            flash("Semester not found.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        if request.method == 'POST':
            course_id = request.form.get('course_id', '').strip()
            semester_name = request.form.get('semester_name', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()
            
            # Validation
            errors = []
            if not course_id or not course_id.isdigit():
                errors.append("Invalid course selected.")
            if not semester_name or len(semester_name) < 2 or len(semester_name) > 50:
                errors.append("Semester name must be 2–50 characters.")
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                if start_date >= end_date:
                    errors.append("End date must be after start date.")
            except ValueError:
                errors.append("Invalid date format for start or end date. Use YYYY-MM-DD.")
            
            # Check if course_id exists
            cursor.execute("SELECT COUNT(*) FROM courses WHERE course_id = %s", (course_id,))
            if cursor.fetchone()['COUNT(*)'] == 0:
                errors.append("Selected course does not exist.")
            
            # Check if semester_name is unique for the course (excluding the current semester)
            cursor.execute(
                "SELECT COUNT(*) FROM semesters WHERE course_id = %s AND semester_name = %s AND semester_id != %s",
                (course_id, semester_name, semester_id)
            )
            if cursor.fetchone()['COUNT(*)'] > 0:
                errors.append("Semester name already exists for this course.")
            
            if errors:
                for e in errors:
                    flash(e, "error")
                # Fetch courses, semesters, and subjects for re-render
                cursor.execute(
                    """
                    SELECT c.course_id, c.course_name, c.description, 
                           COUNT(s.semester_id) AS semester_count
                    FROM courses c
                    LEFT JOIN semesters s ON c.course_id = s.course_id
                    GROUP BY c.course_id, c.course_name, c.description
                    """
                )
                courses = cursor.fetchall()
                
                cursor.execute(
                    """
                    SELECT s.semester_id, c.course_name, s.semester_name, s.start_date, s.end_date, s.course_id
                    FROM semesters s
                    JOIN courses c ON s.course_id = c.course_id
                    """
                )
                semesters = cursor.fetchall()
                
                cursor.execute(
                    """
                    SELECT sub.subject_id, c.course_name, s.semester_name, sub.subject_name, sub.course_id, sub.semester_id
                    FROM subjects sub
                    JOIN courses c ON sub.course_id = c.course_id
                    JOIN semesters s ON sub.semester_id = s.semester_id
                    """
                )
                subjects = cursor.fetchall()
                
                cursor.close()
                conn.close()
                return render_template('admin_courses_semesters.html', courses=courses, semesters=semesters, 
                                     subjects=subjects, name=session.get('email'), 
                                     course_to_edit=None, semester_to_edit=semester_to_edit, subject_to_edit=None)
            
            # Update semester
            cursor.execute(
                """
                UPDATE semesters 
                SET course_id = %s, semester_name = %s, start_date = %s, end_date = %s 
                WHERE semester_id = %s
                """,
                (course_id, semester_name, start_date, end_date, semester_id)
            )
            conn.commit()
            flash("Semester updated successfully!", "success")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Fetch courses, semesters, and subjects for display
        cursor.execute(
            """
            SELECT c.course_id, c.course_name, c.description, 
                   COUNT(s.semester_id) AS semester_count
            FROM courses c
            LEFT JOIN semesters s ON c.course_id = s.course_id
            GROUP BY c.course_id, c.course_name, c.description
            """
        )
        courses = cursor.fetchall()
        
        cursor.execute(
            """
            SELECT s.semester_id, c.course_name, s.semester_name, s.start_date, s.end_date, s.course_id
            FROM semesters s
            JOIN courses c ON s.course_id = c.course_id
            """
        )
        semesters = cursor.fetchall()
        
        cursor.execute(
            """
            SELECT sub.subject_id, c.course_name, s.semester_name, sub.subject_name, sub.course_id, sub.semester_id
            FROM subjects sub
            JOIN courses c ON sub.course_id = c.course_id
            JOIN semesters s ON sub.semester_id = s.semester_id
            """
        )
        subjects = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('admin_courses_semesters.html', courses=courses, semesters=semesters, 
                             subjects=subjects, name=session.get('email'), 
                             course_to_edit=None, semester_to_edit=semester_to_edit, subject_to_edit=None)
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        return redirect('/admin/courses_semesters')

@app.route('/admin/add_subject', methods=['POST'])
def admin_add_subject():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    course_id = request.form.get('course_id', '').strip()
    semester_id = request.form.get('semester_id', '').strip()
    subject_name = request.form.get('subject_name', '').strip()
    
    # Validation
    errors = []
    if not course_id or not course_id.isdigit():
        errors.append("Invalid course selected.")
    if not semester_id or not semester_id.isdigit():
        errors.append("Invalid semester selected.")
    if not subject_name or len(subject_name) < 2 or len(subject_name) > 100:
        errors.append("Subject name must be 2–100 characters.")
    
    if errors:
        for e in errors:
            flash(e, "error")
        return redirect('/admin/courses_semesters')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if course_id exists
        cursor.execute("SELECT COUNT(*) FROM courses WHERE course_id = %s", (course_id,))
        if cursor.fetchone()[0] == 0:
            flash("Selected course does not exist.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Check if semester_id exists and belongs to the selected course
        cursor.execute(
            "SELECT COUNT(*) FROM semesters WHERE semester_id = %s AND course_id = %s",
            (semester_id, course_id)
        )
        if cursor.fetchone()[0] == 0:
            flash("Selected semester does not exist or does not belong to the selected course.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Check if subject_name already exists for this course and semester
        cursor.execute(
            "SELECT COUNT(*) FROM subjects WHERE course_id = %s AND semester_id = %s AND subject_name = %s",
            (course_id, semester_id, subject_name)
        )
        if cursor.fetchone()[0] > 0:
            flash("Subject name already exists for this course and semester.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Insert new subject
        cursor.execute(
            "INSERT INTO subjects (course_id, semester_id, subject_name) VALUES (%s, %s, %s)",
            (course_id, semester_id, subject_name)
        )
        conn.commit()
        flash("Subject added successfully!", "success")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
    
    return redirect('/admin/courses_semesters')

@app.route('/admin/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def admin_edit_subject(subject_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please log in as an admin.", "error")
        return redirect('/login')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch the subject to edit
        cursor.execute(
            """
            SELECT sub.subject_id, sub.course_id, sub.semester_id, sub.subject_name, 
                   c.course_name, s.semester_name
            FROM subjects sub
            JOIN courses c ON sub.course_id = c.course_id
            JOIN semesters s ON sub.semester_id = s.semester_id
            WHERE sub.subject_id = %s
            """,
            (subject_id,)
        )
        subject_to_edit = cursor.fetchone()
        
        if not subject_to_edit:
            flash("Subject not found.", "error")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        if request.method == 'POST':
            course_id = request.form.get('course_id', '').strip()
            semester_id = request.form.get('semester_id', '').strip()
            subject_name = request.form.get('subject_name', '').strip()
            
            # Validation
            errors = []
            if not course_id or not course_id.isdigit():
                errors.append("Invalid course selected.")
            if not semester_id or not semester_id.isdigit():
                errors.append("Invalid semester selected.")
            if not subject_name or len(subject_name) < 2 or len(subject_name) > 100:
                errors.append("Subject name must be 2–100 characters.")
            
            # Check if course_id exists
            cursor.execute("SELECT COUNT(*) FROM courses WHERE course_id = %s", (course_id,))
            if cursor.fetchone()['COUNT(*)'] == 0:
                errors.append("Selected course does not exist.")
            
            # Check if semester_id exists and belongs to the selected course
            cursor.execute(
                "SELECT COUNT(*) FROM semesters WHERE semester_id = %s AND course_id = %s",
                (semester_id, course_id)
            )
            if cursor.fetchone()['COUNT(*)'] == 0:
                errors.append("Selected semester does not exist or does not belong to the selected course.")
            
            # Check if subject_name is unique for the course and semester (excluding the current subject)
            cursor.execute(
                """
                SELECT COUNT(*) FROM subjects 
                WHERE course_id = %s AND semester_id = %s AND subject_name = %s AND subject_id != %s
                """,
                (course_id, semester_id, subject_name, subject_id)
            )
            if cursor.fetchone()['COUNT(*)'] > 0:
                errors.append("Subject name already exists for this course and semester.")
            
            if errors:
                for e in errors:
                    flash(e, "error")
                # Fetch courses, semesters, and subjects for re-render
                cursor.execute(
                    """
                    SELECT c.course_id, c.course_name, c.description, 
                           COUNT(s.semester_id) AS semester_count
                    FROM courses c
                    LEFT JOIN semesters s ON c.course_id = s.course_id
                    GROUP BY c.course_id, c.course_name, c.description
                    """
                )
                courses = cursor.fetchall()
                
                cursor.execute(
                    """
                    SELECT s.semester_id, c.course_name, s.semester_name, s.start_date, s.end_date, s.course_id
                    FROM semesters s
                    JOIN courses c ON s.course_id = c.course_id
                    """
                )
                semesters = cursor.fetchall()
                
                cursor.execute(
                    """
                    SELECT sub.subject_id, c.course_name, s.semester_name, sub.subject_name, sub.course_id, sub.semester_id
                    FROM subjects sub
                    JOIN courses c ON sub.course_id = c.course_id
                    JOIN semesters s ON sub.semester_id = s.semester_id
                    """
                )
                subjects = cursor.fetchall()
                
                cursor.close()
                conn.close()
                return render_template('admin_courses_semesters.html', courses=courses, semesters=semesters, 
                                     subjects=subjects, name=session.get('email'), 
                                     course_to_edit=None, semester_to_edit=None, subject_to_edit=subject_to_edit)
            
            # Update subject
            cursor.execute(
                """
                UPDATE subjects 
                SET course_id = %s, semester_id = %s, subject_name = %s 
                WHERE subject_id = %s
                """,
                (course_id, semester_id, subject_name, subject_id)
            )
            conn.commit()
            flash("Subject updated successfully!", "success")
            cursor.close()
            conn.close()
            return redirect('/admin/courses_semesters')
        
        # Fetch courses, semesters, and subjects for display
        cursor.execute(
            """
            SELECT c.course_id, c.course_name, c.description, 
                   COUNT(s.semester_id) AS semester_count
            FROM courses c
            LEFT JOIN semesters s ON c.course_id = s.course_id
            GROUP BY c.course_id, c.course_name, c.description
            """
        )
        courses = cursor.fetchall()
        
        cursor.execute(
            """
            SELECT s.semester_id, c.course_name, s.semester_name, s.start_date, s.end_date, s.course_id
            FROM semesters s
            JOIN courses c ON s.course_id = c.course_id
            """
        )
        semesters = cursor.fetchall()
        
        cursor.execute(
            """
            SELECT sub.subject_id, c.course_name, s.semester_name, sub.subject_name, sub.course_id, sub.semester_id
            FROM subjects sub
            JOIN courses c ON sub.course_id = c.course_id
            JOIN semesters s ON sub.semester_id = s.semester_id
            """
        )
        subjects = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('admin_courses_semesters.html', courses=courses, semesters=semesters, 
                             subjects=subjects, name=session.get('email'), 
                             course_to_edit=None, semester_to_edit=None, subject_to_edit=subject_to_edit)
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "error")
        return redirect('/admin/courses_semesters')


@app.route('/admin/get_semesters/<int:course_id>')
def get_semesters(course_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT semester_id, semester_name, start_date, end_date
            FROM semesters
            WHERE course_id = %s
            ORDER BY semester_name
            """,
            (course_id,)
        )
        semesters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return jsonify({'semesters': semesters})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    
    


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