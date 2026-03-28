import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create a database connection with row factory for dict-like access"""
    try:
        conn = sqlite3.connect('gym.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def close_db_connection(conn):
    """Safely close database connection"""
    try:
        if conn:
            conn.close()
    except sqlite3.Error as e:
        logger.error(f"Error closing database: {e}")

def drop_tables():
    """Drop all existing tables to allow for a clean schema creation"""
    conn = sqlite3.connect('gym.db')
    cursor = conn.cursor()
    try:
        # Order matters due to foreign keys
        tables = [
            'member_reports', 'member_schedules', 'admin_users', 
            'attendance_logs', 'payments', 'trainers', 'members', 'plans'
        ]
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"🗑️  Dropped table: {table}")
            
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"❌ Error dropping tables: {e}")
        return False
    finally:
        conn.close()

def create_tables():
    """Create all necessary tables for the gym management system"""
    conn = sqlite3.connect('gym.db')
    cursor = conn.cursor()

    try:
        # PLANS TABLE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_name VARCHAR(100) NOT NULL,
                duration_months INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        logger.info("✓ Plans table created/verified")

        # MEMBERS TABLE - Fixed password_hash column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20) UNIQUE,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                gender TEXT CHECK(gender IN ('Male','Female','Other')),
                date_of_birth DATE,
                join_date DATE DEFAULT CURRENT_DATE,
                plan_id INTEGER,
                status TEXT CHECK(status IN ('Active','Inactive','Suspended')) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
            );
        ''')
        logger.info("✓ Members table created/verified")

        # TRAINERS TABLE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trainers (
                trainer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20) UNIQUE,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                specialization VARCHAR(150),
                bio TEXT,
                hire_date DATE,
                salary DECIMAL(10,2),
                status TEXT CHECK(status IN ('Active','Inactive')) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        logger.info("✓ Trainers table created/verified")

        # PAYMENTS TABLE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT CHECK(payment_method IN ('Cash','Card','Mobile Money','Bank Transfer')),
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(member_id)
                    ON DELETE CASCADE
            );
        ''')
        logger.info("✓ Payments table created/verified")

        # ATTENDANCE TABLE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_logs (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                check_in_date DATE DEFAULT CURRENT_DATE,
                check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                check_out_time TIMESTAMP,
                duration_minutes INTEGER,
                FOREIGN KEY (member_id) REFERENCES members(member_id)
                    ON DELETE CASCADE
            );
        ''')
        logger.info("✓ Attendance table created/verified")

        # ADMIN USERS TABLE - Fixed email column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role TEXT CHECK(role IN ('SuperAdmin','Manager','Staff')) DEFAULT 'Staff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        logger.info("✓ Admin users table created/verified")

        # MEMBER SCHEDULES TABLE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS member_schedules (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                trainer_id INTEGER,
                session_type TEXT NOT NULL,
                session_day TEXT NOT NULL,
                session_time TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(member_id),
                FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id)
            );
        ''')
        logger.info("✓ Member schedules table created/verified")

        # MEMBER REPORTS TABLE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS member_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                trainer_id INTEGER,
                performance TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(member_id),
                FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id)
            );
        ''')
        logger.info("✓ Member reports table created/verified")

        # WORKOUT LOGS TABLE (New)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                workout_name VARCHAR(100) NOT NULL,
                completion_date DATE DEFAULT CURRENT_DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(member_id)
            );
        ''')
        logger.info("✓ Workout Logs table created/verified")

        # GYM CLASSES TABLE (New)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gym_classes (
                class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name VARCHAR(100) NOT NULL,
                instructor_name VARCHAR(100),
                day_of_week TEXT NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                location VARCHAR(100),
                capacity INTEGER DEFAULT 20,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        logger.info("✓ Gym Classes table created/verified")

        # BOOKINGS TABLE (New - for members booking classes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                booking_date DATE DEFAULT CURRENT_DATE,
                status TEXT CHECK(status IN ('Confirmed','Cancelled')) DEFAULT 'Confirmed',
                FOREIGN KEY (member_id) REFERENCES members(member_id),
                FOREIGN KEY (class_id) REFERENCES gym_classes(class_id)
            );
        ''')
        logger.info("✓ Class Bookings table created/verified")

        conn.commit()
        logger.info("✅ All tables created successfully!")
        return True

    except sqlite3.Error as e:
        logger.error(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

def seed_classes(conn):
    """Seed gym classes schedule (05:30 AM - 09:00 PM)"""
    try:
        cursor = conn.cursor()
        
        # Determine if we should clear existing (if the user wants a diversity update)
        # For now, let's check count. If > 30, assume it's already diversified.
        # But user wants to change it. safest is to clear.
        # Let's clear ALL classes to ensure the new schedule is applied fully.
        # WARNING: This deletes existing bookings/schedules if foreign keys cascade or if constraints exist.
        # But this is a prototype/seed function.
        # To be safe, let's delete only if we are "updating" or just insert if empty.
        # Since the user explicitly asked for a change, let's force a re-seed if the count is small (< 50)
        # which implies it's the old schedule. The old schedule had ~20 classes.
        
        count = cursor.execute("SELECT count(*) FROM gym_classes").fetchone()[0]
        if count > 40: 
            return # Already diversified

        if count > 0:
            logger.info("Clearing old schedule to apply new diverse schedule...")
            cursor.execute("DELETE FROM class_bookings") # Must clear bookings first due to FK
            cursor.execute("DELETE FROM gym_classes")

        # (ClassName, Instructor, Day, Start, End, Location)
        classes = [
            # --- MORNING (05:30 - 09:00) ---
            ('CrossFit', 'Coach Mark', 'Monday', '05:30', '06:30', 'CrossFit Zone'),
            ('Sunrise Yoga', 'Elena Rose', 'Monday', '06:00', '07:00', 'Studio A'),
            ('Spin: Hill Climb', 'Shayan Adah', 'Monday', '07:00', '07:45', 'Spin Studio'),
            
            ('HIIT Blast', 'Marjorie Muiruri', 'Tuesday', '05:45', '06:30', 'Active Zone'),
            ('BodyPump', 'Frank Mukhwana', 'Tuesday', '06:30', '07:30', 'Studio B'),
            ('Pilates Core', 'Sarah Jen', 'Tuesday', '08:00', '09:00', 'Studio A'),

            ('CrossFit', 'Coach Dave', 'Wednesday', '05:30', '06:30', 'CrossFit Zone'),
            ('BoxFit', 'Ignatius Shitiavayi', 'Wednesday', '06:00', '07:00', 'BoxFit Zone'),
            ('Mobility Flow', 'Elena Rose', 'Wednesday', '07:30', '08:15', 'Studio A'),

            ('Power Yoga', 'Elena Rose', 'Thursday', '06:00', '07:00', 'Studio A'),
            ('Spin: Endurance', 'Shayan Adah', 'Thursday', '06:30', '07:15', 'Spin Studio'),
            ('Kettlebell Power', 'Collins Madali', 'Thursday', '07:30', '08:15', 'Active Zone'),

            ('MetCon', 'Coach Sarah', 'Friday', '05:30', '06:30', 'CrossFit Zone'),
            ('Zumba Morning', 'Winnie Mukai', 'Friday', '07:00', '08:00', 'Studio B'),
            
            # --- LUNCH (12:00 - 14:00) ---
            ('Express Abs', 'Mikey Lochodi', 'Monday', '12:15', '12:45', 'Studio B'),
            ('Lunchtime Yoga', 'Elena Rose', 'Tuesday', '12:30', '13:15', 'Studio A'),
            ('HIIT 30', 'Active Zone Team', 'Wednesday', '12:15', '12:45', 'Active Zone'),
            ('Spin Express', 'Shayan Adah', 'Thursday', '12:30', '13:15', 'Spin Studio'),
            ('Flexibility', 'Elena Rose', 'Friday', '12:15', '13:00', 'Studio A'),

            # --- AFTERNOON/EVENING (16:30 - 21:00) ---
            ('Teen Fitness', 'Coach Dave', 'Monday', '16:30', '17:30', 'Active Zone'),
            ('Zumba Party', 'Winnie Mukai', 'Monday', '17:30', '18:30', 'Studio B'),
            ('CrossFit WOD', 'Coach Mark', 'Monday', '18:00', '19:00', 'CrossFit Zone'),
            ('Muay Thai', 'Kru John', 'Monday', '19:00', '20:30', 'BoxFit Zone'),

            ('BodyCombat', 'Frank Mukhwana', 'Tuesday', '17:30', '18:30', 'Studio B'),
            ('Spin: Intervals', 'Shayan Adah', 'Tuesday', '18:00', '18:45', 'Spin Studio'),
            ('Powerlifting', 'Coach Dave', 'Tuesday', '19:00', '20:30', 'Weight Room'),
            ('Evening Yoga', 'Elena Rose', 'Tuesday', '20:00', '21:00', 'Studio A'),

            ('BoxFit Advanced', 'Hillary Baraza', 'Wednesday', '17:30', '18:30', 'BoxFit Zone'),
            ('Step Aerobics', 'Marjorie Muiruri', 'Wednesday', '18:00', '19:00', 'Studio B'),
            ('CrossFit WOD', 'Coach Sarah', 'Wednesday', '18:30', '19:30', 'CrossFit Zone'),
            ('Meditation', 'Elena Rose', 'Wednesday', '20:00', '20:45', 'Studio A'),

            ('Circuit Training', 'Collins Madali', 'Thursday', '17:30', '18:30', 'Active Zone'),
            ('Dance Cardio', 'Winnie Mukai', 'Thursday', '18:30', '19:30', 'Studio B'),
            ('BJJ Fundamentals', 'Coach Mike', 'Thursday', '19:00', '20:30', 'Mat Area'),

            ('Friday Night Lift', 'Coach Dave', 'Friday', '17:00', '18:30', 'Weight Room'),
            ('Salsa Class', 'Guest Instructor', 'Friday', '18:30', '19:30', 'Studio B'),
            ('Restorative Yoga', 'Elena Rose', 'Friday', '19:30', '20:30', 'Studio A'),

            # --- WEEKEND (Saturday/Sunday) ---
            ('Weekend Warriors', 'Team', 'Saturday', '08:00', '09:30', 'Outdoor/Track'),
            ('Spin: Marathon', 'Shayan Adah', 'Saturday', '09:00', '10:30', 'Spin Studio'),
            ('Family Yoga', 'Elena Rose', 'Sunday', '10:00', '11:00', 'Studio A'),
        ]

        cursor.executemany('''
            INSERT INTO gym_classes (class_name, instructor_name, day_of_week, start_time, end_time, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', classes)
        
        conn.commit()
        logger.info("✓ Seeded diverse gym schedule classes")
    except Exception as e:
        logger.error(f"Error seeding classes: {e}")

def get_gym_schedule():
    """Get all scheduled classes grouped by day/time"""
    conn = get_db_connection()
    if not conn: return []
    try:
         classes = conn.execute("SELECT * FROM gym_classes ORDER BY start_time, day_of_week").fetchall()
         return [dict(c) for c in classes]
    finally:
        close_db_connection(conn)

def book_class(member_id, class_id):
    """Book a spot in a class"""
    conn = get_db_connection()
    if not conn: return False
    try:
        # Check if already booked
        existing = conn.execute("SELECT booking_id FROM class_bookings WHERE member_id=? AND class_id=?", (member_id, class_id)).fetchone()
        if existing: return False # Already booked

        conn.execute("INSERT INTO class_bookings (member_id, class_id) VALUES (?, ?)", (member_id, class_id))
        conn.commit()
        return True
    except:
        return False
    finally:
        close_db_connection(conn)

def cancel_booking(member_id, class_id):
    """Cancel a class booking"""
    conn = get_db_connection()
    if not conn: return False
    try:
        conn.execute("DELETE FROM class_bookings WHERE member_id=? AND class_id=?", (member_id, class_id))
        conn.commit()
        return True
    except:
        return False
    finally:
        close_db_connection(conn)

def get_member_bookings(member_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        # Get list of class_ids booked by this member
        rows = conn.execute("SELECT class_id FROM class_bookings WHERE member_id=? AND status='Confirmed'", (member_id,)).fetchall()
        return [r['class_id'] for r in rows]
    finally:
         close_db_connection(conn)

def get_member_schedules(member_id):
    """Get all schedules assigned to a member."""
    conn = get_db_connection()
    if not conn: return []
    try:
        query = '''
            SELECT s.*, t.first_name || ' ' || t.last_name as trainer_name
            FROM member_schedules s
            LEFT JOIN trainers t ON s.trainer_id = t.trainer_id
            WHERE s.member_id = ?
            ORDER BY 
                CASE s.session_day 
                    WHEN 'Monday' THEN 1 
                    WHEN 'Tuesday' THEN 2 
                    WHEN 'Wednesday' THEN 3 
                    WHEN 'Thursday' THEN 4 
                    WHEN 'Friday' THEN 5 
                    WHEN 'Saturday' THEN 6 
                    WHEN 'Sunday' THEN 7 
                END,
                s.session_time
        '''
        cursor = conn.execute(query, (member_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_db_connection(conn)

def get_member_reports(member_id):
    """Get all performance reports for a member."""
    conn = get_db_connection()
    if not conn: return []
    try:
        query = '''
            SELECT r.*, t.first_name || ' ' || t.last_name as trainer_name
            FROM member_reports r
            LEFT JOIN trainers t ON r.trainer_id = t.trainer_id
            WHERE r.member_id = ?
            ORDER BY r.created_at DESC
        '''
        cursor = conn.execute(query, (member_id,))
        reports = [dict(row) for row in cursor.fetchall()]
        
        # Format date
        for report in reports:
            if isinstance(report['created_at'], str):
                try:
                     dt = datetime.strptime(report['created_at'], '%Y-%m-%d %H:%M:%S.%f')
                     report['created_at'] = dt.strftime('%b %d, %Y')
                except:
                    pass
        return reports
    finally:
        close_db_connection(conn)

def get_member_upcoming_classes(member_id):
    """Get detailed list of classes booked by member"""
    conn = get_db_connection()
    if not conn: return []
    try:
        query = '''
            SELECT 
                C.class_name, 
                C.instructor_name, 
                C.day_of_week, 
                C.start_time, 
                C.location,
                B.booking_date
            FROM class_bookings B
            JOIN gym_classes C ON B.class_id = C.class_id
            WHERE B.member_id = ? AND B.status = 'Confirmed'
            ORDER BY 
                CASE 
                    WHEN C.day_of_week = 'Monday' THEN 1
                    WHEN C.day_of_week = 'Tuesday' THEN 2
                    WHEN C.day_of_week = 'Wednesday' THEN 3
                    WHEN C.day_of_week = 'Thursday' THEN 4
                    WHEN C.day_of_week = 'Friday' THEN 5
                    WHEN C.day_of_week = 'Saturday' THEN 6
                    WHEN C.day_of_week = 'Sunday' THEN 7
                END,
                C.start_time
        '''
        classes = conn.execute(query, (member_id,)).fetchall()
        return [dict(c) for c in classes]
    finally:
        close_db_connection(conn)

def get_monthly_booking_count(member_id):
    """Count bookings for the current month"""
    conn = get_db_connection()
    if not conn: return 0
    try:
        query = "SELECT COUNT(*) FROM class_bookings WHERE member_id=? AND status='Confirmed' AND strftime('%Y-%m', booking_date) = strftime('%Y-%m', 'now')"
        count = conn.execute(query, (member_id,)).fetchone()[0]
        return count
    except:
        return 0
    finally:
        close_db_connection(conn)

def get_member_analytics(member_id):
    """Get analytics data for member dashboard"""
    conn = get_db_connection()
    analytics = {
        'daily_activity': {'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0, 'Saturday': 0, 'Sunday': 0},
        'class_distribution': {}
    }
    
    if not conn: return analytics
    
    try:
        # 1. Daily Activity (Bookings per day of week)
        query_daily = '''
            SELECT C.day_of_week, COUNT(*) as count
            FROM class_bookings B
            JOIN gym_classes C ON B.class_id = C.class_id
            WHERE B.member_id = ? AND B.status = 'Confirmed'
            GROUP BY C.day_of_week
        '''
        cursor = conn.cursor()
        rows_daily = cursor.execute(query_daily, (member_id,)).fetchall()
        for row in rows_daily:
            day = row[0]
            if day in analytics['daily_activity']:
                analytics['daily_activity'][day] = row[1]
                
        # 2. Class Distribution (Top class types)
        query_dist = '''
            SELECT C.class_name, COUNT(*) as count
            FROM class_bookings B
            JOIN gym_classes C ON B.class_id = C.class_id
            WHERE B.member_id = ? AND B.status = 'Confirmed'
            GROUP BY C.class_name
            ORDER BY count DESC
            LIMIT 5
        '''
        rows_dist = cursor.execute(query_dist, (member_id,)).fetchall()
        for row in rows_dist:
            analytics['class_distribution'][row[0]] = row[1]
            
        return analytics
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        return analytics
    finally:
        close_db_connection(conn)

def verify_database():
    """Verify the database exists and has all tables. Also checks/updates schema."""
    conn = None
    try:
        conn = sqlite3.connect('gym.db')
        cursor = conn.cursor()
        
        # 1. Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [t[0] for t in cursor.fetchall()]
        
        required_tables = [
            'plans', 'members', 'trainers', 'payments', 
            'attendance_logs', 'admin_users', 'member_schedules', 'member_reports',
            'gym_classes', 'class_bookings'
        ]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        # 2. Create missing tables if any
        if missing_tables:
            logger.info(f"Missing tables: {missing_tables}. Running create_tables...")
            conn.close() 
            create_tables() # This usually creates its own connection, so we close ours first
            conn = sqlite3.connect('gym.db') # Reopen
            cursor = conn.cursor()
        
        # 3. Schema Migrations (Trainer ID)
        if 'members' in existing_tables or not missing_tables:
            cursor.execute("PRAGMA table_info(members)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'trainer_id' not in columns:
                logger.info("Migrating: Adding 'trainer_id' to members table...")
                cursor.execute("ALTER TABLE members ADD COLUMN trainer_id INTEGER REFERENCES trainers(trainer_id)")
                conn.commit()

        # 4. Seed Data
        seed_classes(conn) 
        
        # Check plans
        cursor.execute("SELECT COUNT(*) FROM plans")
        count = cursor.fetchone()[0]
        if count == 0 or count < 6:
            seed_plans(conn)

        logger.info("✅ Database verified and ready!")
        return True
            
    except Exception as e:
        logger.error(f"Error verifying database: {e}")
        return False
    finally:
        if conn: conn.close()

def seed_plans(conn):
    """Seed default membership plans"""
    try:
        cursor = conn.cursor()
        plans = [
            ("Weekly Pass", 0.25, 15.00),
            ("Standard Monthly", 1, 50.00),
            ("Quarterly Plan", 3, 135.00),
            ("Semi-Annual Plan", 6, 250.00),
            ("Annual Premium", 12, 450.00),
            ("Student Plan", 1, 35.00),
            ("Family Plan", 1, 90.00)
        ]
        
        for name, duration, price in plans:
            exists = cursor.execute("SELECT plan_id FROM plans WHERE plan_name = ?", (name,)).fetchone()
            if not exists:
                cursor.execute(
                    "INSERT INTO plans (plan_name, duration_months, price) VALUES (?, ?, ?)", 
                    (name, duration, price)
                )
        conn.commit()
        logger.info("✓ Seeded membership plans")
    except Exception as e:
        logger.error(f"Error seeding plans: {e}")


# --- INSERT / GET FUNCTIONS ---

def insert_member(first_name, last_name, email, phone, password_hash, gender, date_of_birth, plan_id, status='Active'):
    """Insert a new member into the database"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO members 
            (first_name, last_name, email, phone, password_hash, gender, date_of_birth, plan_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, password_hash, gender, date_of_birth, plan_id, status, datetime.now()))
        
        conn.commit()
        member_id = cursor.lastrowid
        logger.info(f"✅ Member created - ID: {member_id}")
        return member_id

    except sqlite3.IntegrityError as e:
        logger.warning(f"Integrity error (Member): {e}")
        return None
    except Exception as e:
        logger.error(f"Error inserting member: {e}")
        return None
    finally:
        close_db_connection(conn)

def insert_trainer(first_name, last_name, email, phone, password_hash, specialization, bio='', status='Active'):
    """Insert a new trainer into the database"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trainers 
            (first_name, last_name, email, phone, password_hash, specialization, bio, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, password_hash, specialization, bio, status, datetime.now()))
        
        conn.commit()
        trainer_id = cursor.lastrowid
        logger.info(f"✅ Trainer created - ID: {trainer_id}")
        return trainer_id

    except sqlite3.IntegrityError as e:
        logger.warning(f"Integrity error (Trainer): {e}")
        return None
    except Exception as e:
        logger.error(f"Error inserting trainer: {e}")
        return None
    finally:
        close_db_connection(conn)

def get_member_by_email(email):
    """Retrieve member by email with plan and trainer details"""
    conn = get_db_connection()
    if not conn: return None
    try:
        query = '''
            SELECT m.*, 
                   p.plan_name, p.price as plan_price, p.duration_months,
                   t.first_name as trainer_first_name, t.last_name as trainer_last_name, 
                   t.specialization as trainer_specialization, t.phone as trainer_phone, 
                   t.email as trainer_email, t.bio as trainer_bio
            FROM members m
            LEFT JOIN plans p ON m.plan_id = p.plan_id
            LEFT JOIN trainers t ON m.trainer_id = t.trainer_id
            WHERE m.email = ?
        '''
        member = conn.execute(query, (email,)).fetchone()
        return dict(member) if member else None
    finally:
        close_db_connection(conn)

def get_all_plans():
    """Retrieve all available subscription plans"""
    conn = get_db_connection()
    if not conn: return []
    try:
        plans = conn.execute('SELECT * FROM plans').fetchall()
        return [dict(p) for p in plans]
    finally:
        close_db_connection(conn)

def insert_plan(plan_name, duration_months, price):
    """Insert a new subscription plan"""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO plans (plan_name, duration_months, price) 
            VALUES (?, ?, ?)
        ''', (plan_name, duration_months, price))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Error adding plan: {e}")
        return None
    finally:
        close_db_connection(conn)

def delete_plan(plan_id):
    """Delete a plan if it's not in use by active members"""
    conn = get_db_connection()
    if not conn: return False
    try:
        # Check if plan is associated with members
        count = conn.execute('SELECT COUNT(*) FROM members WHERE plan_id = ?', (plan_id,)).fetchone()[0]
        if count > 0:
            logger.warning(f"Cannot delete plan {plan_id}: In use by {count} members")
            return False

        conn.execute('DELETE FROM plans WHERE plan_id = ?', (plan_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error delete plan: {e}")
        return False
    finally:
        close_db_connection(conn)

def get_trainer_by_email(email):
    """Retrieve trainer by email"""
    conn = get_db_connection()
    if not conn: return None
    try:
        trainer = conn.execute('SELECT * FROM trainers WHERE email = ?', (email,)).fetchone()
        return dict(trainer) if trainer else None
    finally:
        close_db_connection(conn)

def get_all_members():
    """Retrieve all members with their plan details"""
    conn = get_db_connection()
    if not conn: return []
    try:
        query = '''
            SELECT m.*, p.plan_name, p.price as plan_price
            FROM members m
            LEFT JOIN plans p ON m.plan_id = p.plan_id
            ORDER BY m.created_at DESC
        '''
        members = conn.execute(query).fetchall()
        return [dict(m) for m in members]
    finally:
        close_db_connection(conn)

def get_all_trainers():
    conn = get_db_connection()
    if not conn: return []
    try:
        trainers = conn.execute('SELECT * FROM trainers ORDER BY created_at DESC').fetchall()
        return [dict(t) for t in trainers]
    finally:
        close_db_connection(conn)

def update_member(member_id, **kwargs):
    conn = get_db_connection()
    if not conn: return False
    try:
        allowed = ['first_name', 'last_name', 'phone', 'gender', 'date_of_birth', 'plan_id', 'status', 'trainer_id']
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields: return False
        
        fields['updated_at'] = datetime.now()
        query = 'UPDATE members SET ' + ', '.join([f'{k}=?' for k in fields]) + ' WHERE member_id=?'
        conn.execute(query, list(fields.values()) + [member_id])
        conn.commit()
        return True
    finally:
        close_db_connection(conn)

def update_trainer(trainer_id, **kwargs):
    conn = get_db_connection()
    if not conn: return False
    try:
        allowed = ['first_name', 'last_name', 'phone', 'specialization', 'bio', 'status', 'salary']
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields: return False
        
        fields['updated_at'] = datetime.now()
        query = 'UPDATE trainers SET ' + ', '.join([f'{k}=?' for k in fields]) + ' WHERE trainer_id=?'
        conn.execute(query, list(fields.values()) + [trainer_id])
        conn.commit()
        return True
    finally:
        close_db_connection(conn)

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🏋️  GYM DATABASE INITIALIZATION")
    logger.info("=" * 50)
    
    # WARN: Drops all data to ensure schema correctness
    drop_tables()
    
    if create_tables():
        logger.info("\n✅ Database table structure successfully reset!")
        # Seed a default plan so members can register
        try:
            conn = sqlite3.connect('gym.db')
            conn.execute("INSERT OR IGNORE INTO plans (plan_name, duration_months, price) VALUES ('Standard Monthly', 1, 50.00)")
            conn.commit()
            conn.close()
            logger.info("➕ Added default subscription plan")
        except: pass
    else:
        logger.error("\n❌ Database initialization failed!")
def get_all_trainer_schedules(trainer_id=None):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        # 1. Get existing member schedules (1-on-1)
        query_schedules = '''
            SELECT s.*, m.first_name || ' ' || m.last_name as member_name 
            FROM member_schedules s
            JOIN members m ON s.member_id = m.member_id
        '''
        args_schedules = []
        if trainer_id:
            query_schedules += ' WHERE s.trainer_id = ?'
            args_schedules.append(trainer_id)
            
        cursor = conn.execute(query_schedules, args_schedules)
        # Add a type identifier for deletion logic
        schedules = []
        for row in cursor.fetchall():
            d = dict(row)
            d['type'] = 'schedule' # Indicates 1-on-1
            d['delete_id'] = f"sched_{d['schedule_id']}"
            schedules.append(d)
        
        # 2. Get All Confirmed Class Bookings for Trainer
        if trainer_id:
            trainer = conn.execute("SELECT first_name, last_name FROM trainers WHERE trainer_id=?", (trainer_id,)).fetchone()
            if trainer:
                fname = trainer['first_name']
                lname = trainer['last_name']
                # Removed date filter - assuming weekly recurring schedule, so ANY active booking counts for "this week"
                query_classes = '''
                    SELECT b.booking_id, b.booking_date, c.class_name, c.day_of_week, c.start_time, 
                           m.first_name || ' ' || m.last_name as member_name
                    FROM class_bookings b
                    JOIN gym_classes c ON b.class_id = c.class_id
                    JOIN members m ON b.member_id = m.member_id
                    WHERE (c.instructor_name LIKE '%' || ? || '%' 
                        OR c.instructor_name LIKE '%' || ? || '%')
                      AND b.status = 'Confirmed'
                '''
                class_bookings = conn.execute(query_classes, (fname, lname)).fetchall()
                
                for cb in class_bookings:
                    schedules.append({
                        'schedule_id': f"cls_{cb['booking_id']}", 
                        'member_name': cb['member_name'],
                        'session_type': f"Class: {cb['class_name']}",
                        'session_day': cb['day_of_week'], 
                        'session_time': cb['start_time'],
                        'notes': f"Class Time: {cb['start_time']}",
                        'type': 'booking', # Indicates Class Booking
                        'delete_id': f"book_{cb['booking_id']}"
                    })

        # Sort Logic
        day_map = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
        schedules.sort(key=lambda x: (day_map.get(x['session_day'], 8), x['session_time']))
        
        return schedules
    finally:
        close_db_connection(conn)

def get_booking_analytics(trainer_id=None):
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        # 1. Schedules count
        query = '''
            SELECT session_day as day, COUNT(*) as total
            FROM member_schedules
        '''
        args = []
        if trainer_id:
            query += ' WHERE trainer_id = ?'
            args.append(trainer_id)
        query += ' GROUP BY session_day'
        
        cursor = conn.execute(query, args)
        results = {row['day']: row['total'] for row in cursor.fetchall()}
        
        # 2. Class Bookings count
        if trainer_id:
            trainer = conn.execute("SELECT first_name, last_name FROM trainers WHERE trainer_id=?", (trainer_id,)).fetchone()
            if trainer:
                fname = trainer['first_name']
                lname = trainer['last_name']
                query_classes = '''
                    SELECT c.day_of_week, COUNT(*) as total
                    FROM class_bookings b
                    JOIN gym_classes c ON b.class_id = c.class_id
                    WHERE (c.instructor_name LIKE '%' || ? || '%' 
                        OR c.instructor_name LIKE '%' || ? || '%')
                      AND b.status = 'Confirmed'
                    GROUP BY c.day_of_week
                '''
                class_counts = conn.execute(query_classes, (fname, lname)).fetchall()
                for cc in class_counts:
                    day = cc['day_of_week']
                    results[day] = results.get(day, 0) + cc['total']

        # Format for chart
        final_results = [{'day': k, 'total': v} for k, v in results.items()]
        
        if not final_results:
            return []
            
        max_total = max([r['total'] for r in final_results])
        for r in final_results:
            r['percentage'] = int((r['total'] / max_total) * 100) if max_total > 0 else 0
            
        days_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
        final_results.sort(key=lambda x: days_order.get(x['day'], 8))
        
        return final_results
            
    finally:
        close_db_connection(conn)

def insert_workout_log(member_id, workout_name, completion_date=None, notes=None):
    """Log a member's completed workout for the day."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        
        # Check if already logged today
        if not completion_date:
            completion_date = datetime.now().strftime('%Y-%m-%d')
        
        existing = cursor.execute('''
            SELECT log_id FROM workout_logs 
            WHERE member_id = ? AND workout_name = ? AND completion_date = ?
        ''', (member_id, workout_name, completion_date)).fetchone()
        
        if existing:
            return True # Already logged, just return success
            
        cursor.execute('''
            INSERT INTO workout_logs (member_id, workout_name, completion_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (member_id, workout_name, completion_date, notes))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error logging workout: {e}")
        return False
    finally:
        close_db_connection(conn)

def delete_workout_log(member_id, workout_name, completion_date=None):
    """Delete a member's workout log for the day."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        
        # Check if already logged today
        if not completion_date:
            completion_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            DELETE FROM workout_logs 
            WHERE member_id = ? AND workout_name = ? AND completion_date = ?
        ''', (member_id, workout_name, completion_date))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting workout log: {e}")
        return False
    finally:
        close_db_connection(conn)

def get_member_workout_logs(member_id, start_date=None, end_date=None):
    """Get workout logs for a member within a date range."""
    conn = get_db_connection()
    if not conn: return []
    try:
        query = 'SELECT * FROM workout_logs WHERE member_id = ?'
        params = [member_id]
        
        if start_date and end_date:
            query += ' AND completion_date BETWEEN ? AND ?'
            params.extend([start_date, end_date])
            
        conn.row_factory = sqlite3.Row
        logs = conn.execute(query, params).fetchall()
        return [dict(row) for row in logs]
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return []
    finally:
        close_db_connection(conn)

def insert_member_schedule(member_id, trainer_id, session_type, session_day, session_time, notes):
    """Insert a new member schedule into the database."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO member_schedules (member_id, trainer_id, session_type, session_day, session_time, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (member_id, trainer_id, session_type, session_day, session_time, notes))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error inserting member schedule: {e}")
        return False
    finally:
        close_db_connection(conn)

def insert_member_report(member_id, trainer_id, performance, progress, notes):
    """Insert a new member performance report."""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO member_reports (member_id, trainer_id, performance, progress, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (member_id, trainer_id, performance, progress, notes))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error inserting member report: {e}")
        return False
    finally:
        close_db_connection(conn)

def get_trainer_latest_reports(trainer_id):
    """Get the latest member performance reports created by this trainer."""
    conn = get_db_connection()
    if not conn: return []
    try:
        query = '''
            SELECT r.report_id, r.performance, r.progress, r.notes, r.created_at,
                   m.first_name || ' ' || m.last_name as member_name
            FROM member_reports r
            JOIN members m ON r.member_id = m.member_id
            WHERE r.trainer_id = ?
            ORDER BY r.created_at DESC
            LIMIT 10
        '''
        cursor = conn.execute(query, (trainer_id,))
        reports = [dict(row) for row in cursor.fetchall()]
        
        # Format the date nicely
        for report in reports:
            # Assumes created_at is a string, if it's a datetime object, convert differently
            if isinstance(report['created_at'], str):
                try:
                     dt = datetime.strptime(report['created_at'], '%Y-%m-%d %H:%M:%S.%f')
                     report['created_at'] = dt.strftime('%b %d, %Y')
                except:
                    pass
        return reports
    finally:
        close_db_connection(conn)

def delete_member_schedule(schedule_id):
    """Delete a member schedule entry."""
    conn = get_db_connection()
    if not conn: return False
    try:
        conn.execute("DELETE FROM member_schedules WHERE schedule_id = ?", (schedule_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        return False
    finally:
        close_db_connection(conn)

def get_members_by_trainer(trainer_id):
    """Retrieves members assigned to a trainer"""
    conn = get_db_connection()
    if not conn: return []
    try:
        query = '''
            SELECT m.*, p.plan_name 
            FROM members m
            LEFT JOIN plans p ON m.plan_id = p.plan_id
            WHERE m.trainer_id = ?
            ORDER BY m.first_name ASC
        '''
        members = conn.execute(query, (trainer_id,)).fetchall()
        return [dict(m) for m in members]
    except Exception as e:
        logger.error(f"Error fetching trainer members: {e}")
        return []
    finally:
        close_db_connection(conn)

def get_trainer_member_logs(trainer_id):
    """Retrieve workout logs for all members assigned to a trainer, with schedule plan matching"""
    conn = get_db_connection()
    if not conn: return []
    try:
        # Include member_id in select
        query = '''
            SELECT w.log_id, w.completion_date as date, w.workout_name as workout, 
                   w.notes, w.member_id,
                   m.first_name || ' ' || m.last_name as member_name
            FROM workout_logs w
            JOIN members m ON w.member_id = m.member_id
            WHERE m.trainer_id = ?
            ORDER BY w.completion_date DESC, w.log_id DESC LIMIT 20
        '''
        logs = conn.execute(query, (trainer_id,)).fetchall()
        
        results = []
        for l in logs:
            d = dict(l)
            d['duration'] = '--' # Default
            d['plan_status'] = 'Independent' 
            d['planned_workout'] = None

            try:
                # 1. Get Day of Week from Log Date (e.g. 'Monday')
                log_date = datetime.strptime(d['date'], '%Y-%m-%d')
                day_name = log_date.strftime('%A')
                
                # 2. Check if there was a scheduled session for this member on this day
                sched_query = '''
                    SELECT session_type FROM member_schedules 
                    WHERE member_id = ? AND session_day = ? AND trainer_id = ?
                '''
                schedule = conn.execute(sched_query, (d['member_id'], day_name, trainer_id)).fetchone()
                
                if schedule:
                    planned = schedule['session_type']
                    d['planned_workout'] = planned
                    
                    # 3. Simple fuzzy match to see if they followed the plan
                    # If log.workout contains planned or vice versa (case-insensitive)
                    w_lower = d['workout'].lower()
                    p_lower = planned.lower()
                    
                    if w_lower in p_lower or p_lower in w_lower:
                        d['plan_status'] = 'On Track'
                    else:
                        d['plan_status'] = 'Deviation' # Did something else on a training day
                else:
                    d['plan_status'] = 'Extra Work' # Workout on a rest day
                    
            except Exception as e:
                # Fallback if date parsing fails
                d['plan_status'] = 'Unknown'

            results.append(d)
            
        return results
    except Exception as e:
        logger.error(f"Error fetching trainer member logs: {e}")
        return []
    finally:
        close_db_connection(conn)


def delete_class_booking_by_id(booking_id):
    """Delete a class booking by ID."""
    conn = get_db_connection()
    if not conn: return False
    try:
        conn.execute("DELETE FROM class_bookings WHERE booking_id = ?", (booking_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting booking: {e}")
        return False
    finally:
        close_db_connection(conn)

def delete_member_report(report_id):
    """Delete a member report."""
    conn = get_db_connection()
    if not conn: return False
    try:
        conn.execute("DELETE FROM member_reports WHERE report_id = ?", (report_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        return False
    finally:
        close_db_connection(conn)



