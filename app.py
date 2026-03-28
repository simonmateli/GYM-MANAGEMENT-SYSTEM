import sqlite3
import os
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash, jsonify
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    verify_database,
    get_db_connection,
    close_db_connection,
    get_member_by_email,
    get_trainer_by_email,
    insert_member,
    insert_trainer,
    get_all_members,
    update_member,
    get_all_plans,
    insert_plan,
    delete_plan,
    get_all_trainers,
    update_trainer,
    get_gym_schedule,
    book_class,
    cancel_booking,
    get_member_bookings,
    get_member_upcoming_classes,
    get_monthly_booking_count,
    get_member_analytics,
    get_all_trainer_schedules, # Added
    get_booking_analytics,     # Added
    insert_member_schedule,    # Added
    insert_member_report,      # Added
    get_trainer_latest_reports, # Added
    delete_member_schedule,
    delete_class_booking_by_id,
    delete_member_report,
    get_member_schedules,      # Added
    get_member_reports,        # Added
    insert_workout_log,        # Added
    get_member_workout_logs,   # Added
    delete_workout_log,        # Added
    get_members_by_trainer,    # Added
    get_trainer_member_logs    # Added
)

# Ensure we are working in the correct directory (BACKEND)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder="../FRONTEND", static_folder="../STATIC")
app.secret_key = "change-me-now"

# Ensure DB/tables exist on startup
verify_database()


def require(role: str) -> bool:
    return session.get("user_type") == role


def get_admin_by_email_or_username(identifier: str):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        row = conn.execute(
            "SELECT * FROM admin_users WHERE email = ? OR username = ?",
            (identifier, identifier),
        ).fetchone()
        return dict(row) if row else None
    finally:
        close_db_connection(conn)


def ensure_default_admin():
    conn = get_db_connection()
    if not conn:
        return
    try:
        exists = conn.execute("SELECT admin_id FROM admin_users LIMIT 1").fetchone()
        if not exists:
            conn.execute(
                """
                INSERT INTO admin_users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                ("admin", "admin@gymhub.com", generate_password_hash("admin123"), "SuperAdmin"),
            )
            conn.commit()
    finally:
        close_db_connection(conn)


ensure_default_admin()


@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # 1. Common Fields
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    user_type = request.form.get("user_type", "member") # Hidden input in form

    if not all([first_name, last_name, email, password]):
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for("register"))

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("register"))

    # Check if email exists in EITHER table
    if get_member_by_email(email) or get_trainer_by_email(email):
        flash("Email already registered.", "warning")
        return redirect(url_for("login"))

    hashed_pw = generate_password_hash(password)

    # 2. Logic Split based on User Type
    if user_type == "trainer":
        specialization = request.form.get("specialization", "General Fitness")
        bio = request.form.get("bio", "")
        
        new_id = insert_trainer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password_hash=hashed_pw,
            specialization=specialization,
            bio=bio
        )
        if new_id:
            flash("Trainer account created! Please login.", "success")
            return redirect(url_for("login"))
            
    else: 
        # MEMBER REGISTRATION LOGIC
        gender = request.form.get("gender")
        if gender: 
            gender = gender.capitalize() 
        
        date_of_birth = request.form.get("date_of_birth") or None
        
        # Determine Plan ID
        plan_id = request.form.get("plan_id")
        plan_id = int(plan_id) if plan_id and plan_id.isdigit() else 1

        new_id = insert_member(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password_hash=hashed_pw,
            gender=gender,
            date_of_birth=date_of_birth,
            plan_id=plan_id
        )
        if new_id:
            flash("Member account created! Please login.", "success")
            return redirect(url_for("login"))

    flash("Registration failed. Please try again.", "danger")
    return redirect(url_for("register"))


@app.route("/member/register", methods=["GET", "POST"])
def member_register():
    if request.method == "GET":
        return render_template("register.html")
    return register()


@app.route("/trainer/register", methods=["GET", "POST"])
def trainer_register():
    if request.method == "GET":
        return render_template("register.html")
    return register()


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")
    user_type = request.form.get("user_type") # 'member', 'trainer', 'admin'

    # 1. Admin Login (Always check if selected, or if trying admin credentials specifically)
    if user_type == "admin":
        admin = get_admin_by_email_or_username(email)
        if admin and check_password_hash(admin['password_hash'], password):
            session['user_email'] = admin['email']
            session['user_type'] = 'admin' 
            flash("Welcome Admin!", "success")
            return redirect(url_for('admin_dashboard'))

    # 2. Trainer Login
    elif user_type == "trainer":
        trainer = get_trainer_by_email(email)
        if trainer and check_password_hash(trainer['password_hash'], password):
            session['user_email'] = trainer['email']
            session['user_type'] = 'trainer'
            flash(f"Welcome Coach {trainer['first_name']}!", "success")
            return redirect(url_for('trainer_dashboard'))

    # 3. Member Login
    elif user_type == "member":  
        member = get_member_by_email(email)
        if member and check_password_hash(member['password_hash'], password):
            session['user_email'] = member['email']
            session['user_type'] = 'member'
            flash(f"Welcome back, {member['first_name']}!", "success")
            return redirect(url_for('member_dashboard'))

    # 4. Fallback (if no role selected or role logic failed)
    # Be explicit: if role was selected but auth failed, show error.
    # If users don't select role (not possible with required select), we could do the old sequential check.
    # But let's trust the form.
    
    flash("Invalid email, password, or role selection.", "danger")
    return redirect(url_for("login"))


@app.route("/analytics")
def analytics():
    if not require("admin"):
        return redirect(url_for("login"))
    return redirect(url_for("admin_dashboard") + "#revenueChart")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home"))


# ---------------- DASHBOARDS ----------------

# --- FIX: Support multiple URLs and ensure correct template ---
@app.route("/trainer/dashboard")
@app.route("/trainers") 
@app.route("/trainer")
def trainer_dashboard():
    # 1. Auth Check - Strict
    if 'user_email' not in session or session.get('user_type') != 'trainer':
        flash("Access denied. Trainers only.", "warning")
        return redirect(url_for('login'))

    # 2. Get Logged-in Trainer
    email = session['user_email']
    trainer = get_trainer_by_email(email)

    if not trainer:
        session.clear()
        flash("Trainer account not found.", "danger")
        return redirect(url_for('login'))

    # 3. GET REAL DATA
    # Fetch members assigned to THIS trainer, not all members
    clients_members = get_members_by_trainer(trainer['trainer_id']) 
    schedules = get_all_trainer_schedules(trainer['trainer_id'])
    
    # Get general workout logs for these clients
    workout_logs = get_trainer_member_logs(trainer['trainer_id'])

    booking_stats = get_booking_analytics(trainer['trainer_id'])
    latest_reports = get_trainer_latest_reports(trainer['trainer_id']) # Added
    
    # Calculate Stats
    total_clients = len(clients_members)
    sessions_this_week = len(schedules)
    
    peak_day = "N/A"
    if booking_stats:
        # Find the day with max total from the stats
        # booking_stats is sorted by day of week in my impl, so I need to find max
        peak_stat = max(booking_stats, key=lambda x: x['total'])
        peak_day = peak_stat['day']
    
    stats = {
        "active_clients": total_clients, 
        "sessions_this_week": sessions_this_week,
        "reports_logged": len(latest_reports), # Updated
        "attendance_peak_label": peak_day
    }

    # Helper to find next session for member
    next_sessions = {}
    for s in schedules:
        if 'member_id' in s: # Check key exists
            mid = s['member_id']
            if mid not in next_sessions:
                 next_sessions[mid] = f"{s['session_day']} {s['session_time']}"

    # 4. Format Members for the Trainer View
    clients_real = []
    for m in clients_members:
        clients_real.append({
            "member_id": m['member_id'],
            "first_name": m['first_name'],
            "last_name": m['last_name'],
            "name": f"{m['first_name']} {m['last_name']}",
            "email": m['email'],
            "phone": m['phone'],
            "plan_id": m['plan_name'] if 'plan_name' in m else (m['plan_id'] if m['plan_id'] else "Standard"),
            "status": m['status'] if 'status' in m else "Active",
            "latest_session_label": next_sessions.get(m['member_id'], None)
        })

    # 5. Render with Real Data
    return render_template("trainer.html", 
                           trainer=trainer,
                           trainer_name=f"{trainer['first_name']} {trainer['last_name']}",
                           stats=stats, 
                           schedules=schedules,
                           workout_logs=workout_logs, # Pass logs to template 
                           clients=clients_real, 
                           attendance_chart=booking_stats,
                           reports=latest_reports) # Added real data


# --- THESE ARE THE MISSING ROUTES FIXING YOUR ERROR ---

@app.route("/trainer/add-schedule", methods=["POST"])
def trainer_add_schedule():
    if 'user_email' not in session or session.get('user_type') != 'trainer':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    # Get the trainer
    trainer = get_trainer_by_email(session['user_email'])
    if not trainer:
        flash("Trainer not found.", "danger")
        return redirect(url_for('login'))

    member_id = request.form.get("member_id")
    session_type = request.form.get("session_type")
    session_day = request.form.get("session_day")
    session_time = request.form.get("session_time")
    notes = request.form.get("notes")
    
    # Validation
    if not all([member_id, session_type, session_day, session_time]):
        flash("Please fill in all required fields.", "warning")
        return redirect(url_for('trainer_dashboard'))

    if insert_member_schedule(member_id, trainer['trainer_id'], session_type, session_day, session_time, notes):
        flash("Member schedule assigned successfully!", "success")
    else:
        flash("Failed to assign schedule. Please try again.", "danger")
    
    return redirect(url_for('trainer_dashboard'))


@app.route("/trainer/add-report", methods=["POST"])
def trainer_add_report():
    if 'user_email' not in session or session.get('user_type') != 'trainer':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    trainer = get_trainer_by_email(session['user_email'])
    if not trainer:
        flash("Trainer not found.", "danger")
        return redirect(url_for('login'))

    member_id = request.form.get("member_id")
    performance = request.form.get("performance")
    progress = request.form.get("progress")
    notes = request.form.get("notes")
    
    # Simple validation
    if not all([member_id, performance]):
        flash("Please select a member and a performance rating.", "warning")
        return redirect(url_for('trainer_dashboard'))

    success = insert_member_report(
        member_id=member_id,
        trainer_id=trainer['trainer_id'],
        performance=performance,
        progress=progress,
        notes=notes
    )

    if success:
        flash("Member performance report saved successfully!", "success")
    else:
        flash("Failed to save report. Please try again.", "danger")

    return redirect(url_for('trainer_dashboard'))

@app.route("/trainer/delete-schedule/<schedule_id>")
def trainer_delete_schedule(schedule_id):
    if 'user_email' not in session or session.get('user_type') != 'trainer':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    success = False
    if schedule_id.startswith("sched_"):
        real_id = schedule_id.split("_")[1]
        success = delete_member_schedule(real_id)
    elif schedule_id.startswith("book_"):
        real_id = schedule_id.split("_")[1]
        success = delete_class_booking_by_id(real_id)
    
    if success:
        flash("Schedule deleted successfully.", "success")
    else:
        flash("Failed to delete schedule.", "danger")
        
    return redirect(url_for('trainer_dashboard'))

@app.route("/trainer/delete-report/<int:report_id>")
def trainer_delete_report(report_id):
    if 'user_email' not in session or session.get('user_type') != 'trainer':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    if delete_member_report(report_id):
        flash("Report deleted successfully.", "success")
    else:
        flash("Failed to delete report.", "danger")
        
    return redirect(url_for('trainer_dashboard'))



@app.route("/member")
@app.route("/member/dashboard") # Added alternate route for safety
def member_dashboard():
    # 1. Check if user is logged in
    if 'user_email' not in session or session.get('user_type') != 'member':
        flash("Please login to access the dashboard.", "warning")
        return redirect(url_for('login'))

    user_email = session['user_email']

    # 2. Get member details from DB
    member = get_member_by_email(user_email)

    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for('logout'))

    # 3. Get all plans for selection
    plans = get_all_plans()
    
    # 4. Get all trainers
    trainers = get_all_trainers()

# 5. Get upcoming classes (booking)
    upcoming_classes = get_member_upcoming_classes(member['member_id'])
    
    # 5b. Get trainer-assigned schedules
    trainer_schedules = get_member_schedules(member['member_id'])
    
    # Combine both into a single list
    full_schedule = []
    
    for c in upcoming_classes:
        full_schedule.append({
            'type': 'Class',
            'title': c['class_name'],
            'instructor': c['instructor_name'],
            'day': c['day_of_week'],
            'time': c['start_time'],
            'location': c['location'],
            'date': c['booking_date']
        })
        
    for s in trainer_schedules:
        full_schedule.append({
            'type': 'Training',
            'title': s['session_type'],
            'instructor': s['trainer_name'],
            'day': s['session_day'],
            'time': s['session_time'],
            'location': 'Gym Area',
            'notes': s['notes']
        })
        
    # Sort combined schedule
    day_map = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
    full_schedule.sort(key=lambda x: (day_map.get(x['day'], 8), x['time']))

    # 6. Get stats
    bookings_this_month = get_monthly_booking_count(member['member_id'])
    
    # 7. Get user analytics
    user_analytics = get_member_analytics(member['member_id'])

    # 8. Get Reports
    reports = get_member_reports(member['member_id'])

    # 9. Calculate Weekly Challenge & Activity Streak
    current_challenge = {
        'title': 'Active Week Challenge',
        'desc': 'Complete 4 workouts (Classes or Self-Led) this week!',
        'target': 4,
        'current': 0,
        'percentage': 0,
        'days_left': 0
    }
    
    activity_streak = []
    
    conn = get_db_connection()
    if conn:
        try:
            today = date.today()
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            
            cursor = conn.cursor()
            
            # --- 1. Class Bookings Count ---
            query_classes = '''
                SELECT COUNT(*) 
                FROM class_bookings 
                WHERE member_id = ? 
                AND booking_date BETWEEN ? AND ?
                AND status = 'Confirmed'
            '''
            class_count = cursor.execute(query_classes, (member['member_id'], start_week, end_week)).fetchone()[0]
            
            # --- 2. Self-Logged Workouts Count ---
            query_logs = '''
                SELECT COUNT(*)
                FROM workout_logs
                WHERE member_id = ?
                AND completion_date BETWEEN ? AND ?
            '''
            log_count = cursor.execute(query_logs, (member['member_id'], start_week, end_week)).fetchone()[0]
            
            total_workouts = class_count + log_count
            
            days_remaining = (end_week - today).days
            percentage = min(100, int((total_workouts / current_challenge['target']) * 100))
            
            current_challenge.update({
                'current': total_workouts,
                'percentage': percentage,
                'days_left': max(0, days_remaining)
            })
            
            # --- Activity Streak Calculation ---
            # Get dates of bookings with class names
            query_streak_classes = '''
                SELECT c.booking_date, g.class_name
                FROM class_bookings c
                JOIN gym_classes g ON c.class_id = g.class_id
                WHERE c.member_id = ?
                AND c.booking_date BETWEEN ? AND ?
                AND c.status = 'Confirmed'
            '''
            class_rows = cursor.execute(query_streak_classes, (member['member_id'], start_week, end_week)).fetchall()
            
            # Get dates of logs with workout names
            query_streak_logs = '''
                SELECT completion_date, workout_name
                FROM workout_logs
                WHERE member_id = ?
                AND completion_date BETWEEN ? AND ?
                ORDER BY completion_date ASC, log_id DESC
            '''
            log_rows = cursor.execute(query_streak_logs, (member['member_id'], start_week, end_week)).fetchall()
            
            # Create a lookup map for actual activity: date_str -> {'name': name, 'icon': icon}
            activity_map = {}
            
            # Helper to guess icon from name
            def guess_icon(name):
                n = name.lower()
                if 'yoga' in n or 'pilates' in n: return 'fa-spa'
                if 'swim' in n: return 'fa-swimmer'
                if 'run' in n or 'cardio' in n: return 'fa-running'
                if 'bike' in n or 'cycle' in n or 'spin' in n: return 'fa-biking'
                if 'box' in n or 'combat' in n: return 'fa-fist-raised'
                if 'upper' in n or 'arm' in n or 'chest' in n or 'back' in n: return 'fa-dumbbell'
                if 'lower' in n or 'leg' in n or 'squat' in n: return 'fa-burn'
                if 'abs' in n or 'core' in n: return 'fa-child'
                return 'fa-check'

            # Fill map with classes first
            for row in class_rows:
                d = str(row['booking_date'])
                activity_map[d] = {'name': row['class_name'], 'icon': guess_icon(row['class_name'])}
                
            # Overwrite with logs (so if they log specifically, it takes precedence or just shows latest)
            for row in log_rows:
                d = str(row['completion_date'])
                activity_map[d] = {'name': row['workout_name'], 'icon': guess_icon(row['workout_name'])}
            
            # Combine sets for status check
            active_dates_set = set(activity_map.keys())
            
            # Build the week list for UI
            days_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            weekly_plan_defaults = [
                {'name': "Lower Body",          'icon': "fa-running"},          # Mon
                {'name': "Upper Body + Core",   'icon': "fa-dumbbell"},         # Tue
                {'name': "Rest / Cardio",       'icon': "fa-heartbeat"},        # Wed
                {'name': "Upper Legs",          'icon': "fa-burn"},             # Thu
                {'name': "Full Body",           'icon': "fa-child"},            # Fri
                {'name': "Cardio + Abs",        'icon': "fa-lungs"},            # Sat
                {'name': "Rest",                'icon': "fa-bed"}               # Sun
            ]

            for i, label in enumerate(days_labels):
                loop_date = start_week + timedelta(days=i)
                date_str = str(loop_date)
                is_today = (loop_date == today)
                is_active = (date_str in active_dates_set)
                is_past = (loop_date < today)
                
                streak_status = 'inactive'
                if is_active: streak_status = 'active'
                elif is_today: streak_status = 'today' # Check today after active, so if active today it shows check
                elif is_past: streak_status = 'missed'
                
                # Determine display name and icon
                if date_str in activity_map:
                    display_name = activity_map[date_str]['name']
                    display_icon = activity_map[date_str]['icon']
                else:
                    display_name = weekly_plan_defaults[i]['name']
                    display_icon = weekly_plan_defaults[i]['icon']

                activity_streak.append({
                    'day': label,
                    'status': streak_status,
                    'is_today': is_today,
                    'plan': display_name,
                    'icon': display_icon
                })
                
        except Exception as e:
            print(f"Error calculating dashboard stats: {e}")
        finally:
            close_db_connection(conn)

 
    # 10. Pass variables to the template 
    return render_template("member.html", 
                           member=member,
                           plans=plans,
                           trainers=trainers,
                           schedule=full_schedule,
                           stats={
                               'bookings': bookings_this_month,
                               'reports': len(reports)
                           },
                           analytics=user_analytics,
                           reports=reports,
                           challenge=current_challenge,
                           streak=activity_streak)


@app.route("/member/log-workout", methods=["POST"])
def log_workout():
    if 'user_email' not in session or session.get('user_type') != 'member':
        return redirect(url_for('login'))
        
    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    workout_name = request.form.get("workout_name")
    day_name = request.form.get("day_name")
    
    completion_date = None
    
    if day_name:
        # Calculate date for the given day of current week
        today = date.today()
        day_map = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
            'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }
        
        target_weekday = day_map.get(day_name)
        if target_weekday is not None:
            current_weekday = today.weekday()
            diff = target_weekday - current_weekday
            completion_date = today + timedelta(days=diff)
            # Format as YYYY-MM-DD string as database expects
            completion_date = completion_date.strftime('%Y-%m-%d')
    else:
         completion_date = date.today().strftime('%Y-%m-%d')

    if member and workout_name:
        if insert_workout_log(member['member_id'], workout_name, completion_date=completion_date):
            action_verb = "booked" if day_name else "logged"
            flash(f"Success! '{workout_name}' {action_verb} for {day_name if day_name else 'today'}.", "success")
        else:
            flash("Workout already logged for this day.", "info")
    else:
        flash("Failed to log workout.", "danger")
        
    redirect_anchor = request.form.get("redirect_anchor", "weekly-overview")
    return redirect(url_for('workout_plan', _anchor=redirect_anchor))

@app.route("/member/unbook-workout", methods=["POST"])
def unbook_workout():
    if 'user_email' not in session or session.get('user_type') != 'member':
        return redirect(url_for('login'))
        
    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    workout_name = request.form.get("workout_name")
    day_name = request.form.get("day_name")
    
    completion_date = None
    
    if day_name:
        # Calculate date for the given day of current week
        today = date.today()
        day_map = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
            'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }
        
        target_weekday = day_map.get(day_name)
        if target_weekday is not None:
            current_weekday = today.weekday()
            diff = target_weekday - current_weekday
            completion_date = today + timedelta(days=diff)
            # Format as YYYY-MM-DD string as database expects
            completion_date = completion_date.strftime('%Y-%m-%d')
    else:
         completion_date = date.today().strftime('%Y-%m-%d')
         
    if member and workout_name:
        if delete_workout_log(member['member_id'], workout_name, completion_date=completion_date):
            flash(f"Booking cancelled: '{workout_name}' for {day_name}.", "warning")
        else:
            flash("Failed to cancel booking.", "danger")
            
    redirect_anchor = request.form.get("redirect_anchor", "weekly-overview")
    return redirect(url_for('workout_plan', _anchor=redirect_anchor))

@app.route("/member/workout-plan")
def workout_plan():
    if 'user_email' not in session or session.get('user_type') != 'member':
        return redirect(url_for('login'))
        
    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    # Get logs for the ENTIRE current week to show progress correctly
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    
    logs = get_member_workout_logs(member['member_id'], start_date=start_week, end_date=end_week)
    # Use a set of workout names. 
    # NOTE: This might be tricky if "Barbell Squat" is done on Mon AND Thu. 
    # But current structure seems to imply unique exercises per day or just checking "exists in week".
    # A better approach for the detailed view is to check if it's logged for THAT SPECIFIC DAY based on the loop in the template.
    # However, the template layout is static (Monday Div, Tuesday Div). 
    # We can pass `logged_workouts` as a dict/set of (name, date) tuples? 
    # Or just a list of names if exercises are unique per week plan.
    # Let's assume unique exercises for now or just check name presence. 
    # Given the template just checks `if 'Barbell Squat' in logged_workouts`, it doesn't check the date.
    # This means if I do Squats on Monday, it might show checked on Thursday too if Thursday also has Squats.
    # For now, I will stick to the existing pattern but fetch the whole week so "checking" a box persists for the week view.
    
    logged_workouts = {log['workout_name'] for log in logs}
    
    return render_template("workout_plan.html", member=member, logged_workouts=logged_workouts)

@app.route("/member/update-profile", methods=["POST"])
def update_profile():
    if 'user_email' not in session or session.get('user_type') != 'member':
        return redirect(url_for('login'))

    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    if member:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")
        gender = request.form.get("gender")
        date_of_birth = request.form.get("date_of_birth")

        if update_member(member['member_id'], first_name=first_name, last_name=last_name, phone=phone, gender=gender, date_of_birth=date_of_birth):
             flash("Profile updated successfully!", "success")
        else:
             flash("Failed to update profile.", "danger")
    else:
        flash("Member not found.", "danger")
        
    return redirect(url_for('member_dashboard'))


@app.route("/member/update-plan", methods=["POST"])
def update_member_plan():
    if 'user_email' not in session or session.get('user_type') != 'member':
        return redirect(url_for('login'))

    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    new_plan_id = request.form.get("plan_id")
    
    if member and new_plan_id:
        update_member(member['member_id'], plan_id=int(new_plan_id))
        flash("Membership plan updated successfully!", "success")
    else:
        flash("Failed to update plan.", "danger")
        
    return redirect(url_for('member_dashboard'))


@app.route("/member/select-trainer", methods=["POST"])
def select_trainer():
    if 'user_email' not in session or session.get('user_type') != 'member':
        return redirect(url_for('login'))

    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    trainer_id = request.form.get("trainer_id")
    
    if member and trainer_id:
        update_member(member['member_id'], trainer_id=int(trainer_id))
        flash("Personal trainer selected successfully!", "success")
    elif member and not trainer_id:
        # Allow removing trainer if empty value sent
         # Need to handle None in update_member carefully, currently it ignores None. 
         # But the HTML form will send a value.
         pass
    else:
        flash("Failed to select trainer.", "danger")
        
    return redirect(url_for('member_dashboard'))

@app.route("/schedule")
def schedule():
    if 'user_email' not in session or session.get('user_type') != 'member':
        return redirect(url_for('login'))

    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    # Group classes by day and time for easier template rendering
    raw_schedule = get_gym_schedule()
    
    # We want a structured dict:
    # { '06:00': { 'Monday': class_obj, 'Tuesday': class_obj ... } }
    # Or maybe just pass raw list and filter in Jinja.
    # Let's pass raw and let Jinja handle basic filtering or pass a structured object if needed.
    # The image shows rows as TIMES and columns as DAYS.
    
    classes_by_time = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    times = sorted(list(set([c['start_time'] for c in raw_schedule])))
    
    for t in times:
         classes_by_time[t] = { d: [] for d in days } # Initialize with empty lists
    
    for c in raw_schedule:
        t = c['start_time']
        d = c['day_of_week']
        if t in classes_by_time and d in classes_by_time[t]:
             classes_by_time[t][d].append(c) # Append to list instead of overwriting

    my_bookings = get_member_bookings(member['member_id'])
    
    return render_template('schedule.html', 
                         member=member,
                         schedule=classes_by_time,
                         times=times,
                         days=days,
                         my_bookings=my_bookings)

@app.route("/book-class/<int:class_id>", methods=["POST"])
def booking_route(class_id):
    if 'user_email' not in session or session.get('user_type') != 'member':
       return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    user_email = session['user_email']
    member = get_member_by_email(user_email)
    
    # Check if already booked
    current_bookings = get_member_bookings(member['member_id'])
    
    if class_id in current_bookings:
        # If already booked, CANCEL it
        if cancel_booking(member['member_id'], class_id):
             return jsonify({'success': True, 'action': 'unbooked', 'message': 'Booking cancelled.'})
        else:
             return jsonify({'success': False, 'message': 'Failed to cancel.'})
    else:
        # If not booked, BOOK it
        if book_class(member['member_id'], class_id):
             return jsonify({'success': True, 'action': 'booked', 'message': 'Class booked!'})
        else:
             return jsonify({'success': False, 'message': 'Booking failed.'})


@app.route("/admin")
def admin_dashboard():
    if not require("admin"):
        flash("Please login as admin.", "warning")
        return redirect(url_for("login"))

    members = get_all_members()
    
    # Calculate revenue for chart
    # This prepares a dictionary where keys are member names and values are their plan amount
    revenue_data = {}
    for member in members:
        # Include all members with a plan
        if member.get('plan_price'):
            status = member.get('status') or 'Unknown'
            # Use name and status for label clarity
            name = f"{member['first_name']} {member['last_name']} ({status})"
            price = member.get('plan_price') or 0
            revenue_data[name] = float(price)
            
    return render_template("admin.html", members=members, revenue_data=revenue_data)


@app.route("/payments")
def payments_dashboard():
    if not require("admin"):
        flash("Please login as admin.", "warning")
        return redirect(url_for("login"))

    members = get_all_members()  # Now includes plan_name and price
    return render_template("payments.html", members=members)


@app.route("/admin/export-report")
def export_report():
    if not require("admin"):
        return redirect(url_for("login"))

    members = get_all_members()
    
    # Create CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Header
    cw.writerow(["Member ID", "First Name", "Last Name", "Email", "Phone", "Gender", "Status", "Plan Name", "Plan Price", "Join Date"])
    
    # Member data
    for member in members:
        cw.writerow([
            member.get('member_id'),
            member.get('first_name'),
            member.get('last_name'),
            member.get('email'),
            member.get('phone') or '',
            member.get('gender') or '',
            member.get('status'),
            member.get('plan_name') or '',
            member.get('plan_price') or 0,
            member.get('join_date')
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=gym_members.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/admin/export-revenue")
def export_revenue():
    if not require("admin"):
        return redirect(url_for("login"))

    members = get_all_members()
    
    # Create CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Header
    cw.writerow(["Member Name", "Email", "Plan Name", "Status", "Revenue Amount ($)"])
    
    total_revenue = 0.0
    
    # Member data with valid plans/prices
    for member in members:
        price = member.get('plan_price')
        if price:
            try:
                price_float = float(price)
                total_revenue += price_float
                cw.writerow([
                    f"{member.get('first_name', '')} {member.get('last_name', '')}",
                    member.get('email', ''),
                    member.get('plan_name', 'N/A'),
                    member.get('status', 'Unknown'),
                    f"{price_float:.2f}"
                ])
            except (ValueError, TypeError):
                continue

    # Add Summary Rows
    cw.writerow([])
    cw.writerow(["", "", "", "TOTAL REVENUE:", f"${total_revenue:.2f}"])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=gym_revenue_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output


# ---------------- ADMIN MEMBER CRUD ----------------
@app.route("/admin/add-member", methods=["POST"])
def add_member():
    if not require("admin"):
        return redirect(url_for("login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    gender = request.form.get("gender", None)
    date_of_birth = request.form.get("date_of_birth", None)
    plan_id = request.form.get("plan_id", None)
    status = request.form.get("status", "Active")
    password_hash = generate_password_hash("123456")  # default password

    if not first_name or not last_name or not email:
        flash("First name, last name, email are required.", "danger")
        return redirect(url_for("admin_dashboard"))

    member_id = insert_member(
        first_name, last_name, email, phone if phone else None,
        password_hash, gender, date_of_birth,
        int(plan_id) if plan_id else None, status
    )

    if member_id:
        flash("Member added.", "success")
    else:
        flash("Could not add member (duplicate email/phone).", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/edit-member", methods=["POST"])
def edit_member():
    if not require("admin"):
        return redirect(url_for("login"))

    member_id = request.form.get("member_id", type=int)
    if not member_id:
        flash("Member ID missing.", "danger")
        return redirect(url_for("admin_dashboard"))

    ok = update_member(
        member_id,
        first_name=request.form.get("first_name"),
        last_name=request.form.get("last_name"),
        phone=request.form.get("phone"),
        gender=request.form.get("gender"),
        date_of_birth=request.form.get("date_of_birth"),
        plan_id=request.form.get("plan_id", type=int),
        status=request.form.get("status"),
    )

    if ok:
        flash("Member updated.", "success")
    else:
        flash("Member update failed.", "danger")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    if not require("admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "DB connection failed"}), 500

    try:
        conn.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        close_db_connection(conn)


# ---------------- SETTINGS & PLANS ----------------
@app.route("/settings")
def settings():
    if not require("admin"):
        return redirect(url_for("login"))
    plans = get_all_plans()
    trainers = get_all_trainers()
    return render_template("settings.html", plans=plans, trainers=trainers)

@app.route("/admin/update-salary", methods=["POST"])
def update_salary():
    if not require("admin"):
        return redirect(url_for("login"))
    
    trainer_id = request.form.get("trainer_id")
    salary = request.form.get("salary")
    
    if trainer_id and salary:
        update_trainer(trainer_id, salary=float(salary))
        flash("Trainer salary updated.", "success")
    else:
        flash("Invalid data.", "danger")
    return redirect(url_for("settings"))

@app.route("/admin/add-plan", methods=["POST"])
def add_plan():
    if not require("admin"):
        return redirect(url_for("login"))
    
    name = request.form.get("plan_name")
    duration = request.form.get("duration_months")
    price = request.form.get("price")
    
    if name and duration and price:
        insert_plan(name, int(duration), float(price))
        flash("New plan added successfully!", "success")
    else:
        flash("Missing plan details.", "danger")
    return redirect(url_for("settings"))

@app.route("/admin/delete-plan/<int:plan_id>", methods=["POST"])
def remove_plan(plan_id):
    if not require("admin"):
        return redirect(url_for("login"))
    
    if delete_plan(plan_id):
        flash("Plan deleted successfully.", "success")
    else:
        flash("Cannot delete plan. It may be in use by active members.", "danger")
    return redirect(url_for("settings"))

@app.route("/admin/change-password", methods=["POST"])
def change_password():
    if not require("admin"):
        return redirect(url_for("login"))
        
    current = request.form.get("current_password")
    new_pass = request.form.get("new_password")
    
    # Mock implementation - In a real app, verify current password against DB
    # and update to new password hash.
    # For now, we'll just simulate a success message.
    if current and new_pass:
        flash("Admin password updated successfully! (Simulation)", "success")
    else:
        flash("Please provide both current and new passwords.", "warning")
        
    return redirect(url_for("settings"))


@app.errorhandler(404)
def not_found(_):
    return "404 Not Found - Check URL", 404


@app.errorhandler(500)
def server_error(_):
    return "500 Internal Server Error", 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)