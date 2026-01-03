import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
import os

# Παίρνει τον φάκελο που βρίσκεται το project_db.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Η βάση δεδομένων βρίσκεται στον ίδιο φάκελο
DATABASE_FILE = os.path.join(BASE_DIR, "project.db")

@contextmanager
def db_connection():
    """A context manager to handle database connections safely."""
    conn = None
    try:
        # Increased timeout to 30 seconds to wait longer if DB is busy
        conn = sqlite3.connect(DATABASE_FILE, timeout=30) 
        # Enable WAL mode (Write-Ahead Logging) to allow concurrent reads/writes
        conn.execute("PRAGMA journal_mode=WAL")
        
        yield conn.cursor() #βάζει τον cursor στην μεταβλητή που έθεσα οταν καλώ την συνάρτηση και περιμένει
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback() # Rollback changes on error
        # Re-raise the exception to let the caller know something went wrong
        raise
    finally:
        if conn:
            conn.close()

def verify_user(user_id, role=None):
    if not user_id :
        return False
    try:
        # Use the context manager to get a cursor
        with db_connection() as cursor:
            if role == 'doctor':
                cursor.execute("SELECT docid FROM DOCTOR WHERE docid = ?", (user_id,))
            elif role == 'patient':
                cursor.execute("SELECT patid FROM PATIENT WHERE patid = ?", (user_id,))
            else:
                cursor.execute("SELECT id FROM USER WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                
                return True
        return False  # User not found or other issue
    except sqlite3.Error:
        # The error is already printed by the context manager
        return False

def sing_up_user(user_id,phone,address,firstname,lastname,email,city,birth_date=None,sex=None,allergies=None):
    if not user_id :
        return False
    try:
        with db_connection() as cursor:
            cursor.execute("INSERT INTO USER (id,phone,address,firstname,lastname,email,city) VALUES (?,?,?,?,?,?,?)", (user_id,phone,address,firstname,lastname,email,city))
            
            # If patient details are provided, insert into PATIENT table
            if birth_date or sex or allergies:
                cursor.execute("INSERT INTO PATIENT (patid, birth_date, sex, allergie) VALUES (?,?,?,?)", (user_id, birth_date, sex, allergies))
        return True
    except sqlite3.IntegrityError as e:
        # This specific error means the username (which should be UNIQUE) already exists.
        print(f"Sign up failed: {e}")
        return False
    except sqlite3.Error:
        # All other database errors are handled by the context manager
        return False

def get_specialties():
    try:
        with db_connection() as cursor:
            cursor.execute("SELECT DISTINCT sname FROM HAS")
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error:
        return []

#Για να εμφανίζει τους γιατρούς από κάθε ειδικότητα
def show_doctors(specialty_name):
    try:
        with db_connection() as cursor:
            cursor.execute("SELECT docid, firstname, lastname  \
            FROM USER JOIN DOCTOR on (id=docid) \
            JOIN HAS as h USING(docid) \
            WHERE h.sname=?", (specialty_name,))
            doctors = cursor.fetchall()
            return doctors
    except sqlite3.Error:
        # All other database errors are handled by the context manager
        return False

def show_appointments(doc_id, only_free=True):
    try:
        with db_connection() as cursor:
            # Χρειαζόμαστε και το apno (το ID του ραντεβού) για να το κλείσουμε μετά
            query = """
                SELECT a.apdate, a.aptime, a.availability, a.apno
                FROM DOCTOR 
                JOIN DECLARES USING(docid) 
                JOIN APPOINTMENT a USING (apno) 
                WHERE docid = ? 
            """
            if only_free:
                query += " AND a.availability = 1"
            
            query += " ORDER BY apdate, aptime"
            
            cursor.execute(query, (doc_id,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching appointments: {e}")
        return []

# 2. Πρόσθεσε αυτή τη νέα συνάρτηση στο τέλος του αρχείου:
def book_appointment(pat_id, doc_id, apno, reason):
    """Κλείνει το ραντεβού: Ενημερώνει το availability και εισάγει στο MAKES"""
    try:
        with db_connection() as cursor:
            # Βήμα 1: Ενημέρωση διαθεσιμότητας
            cursor.execute("UPDATE APPOINTMENT SET comment = ?, availability = 0 WHERE apno = ?", (reason, apno))
            
            # Βήμα 2: Σύνδεση ασθενή με το ραντεβού (Πίνακας MAKES)
            # Υποθέτουμε ότι το πεδίο 'reason' είναι κενό ή προαιρετικό προς το παρόν
            cursor.execute("INSERT INTO MAKES (docid, patid, apno, reason) VALUES (?, ?, ?, ?)", 
                           (doc_id, pat_id, apno, reason))
        return True
    except sqlite3.Error as e:
        print(f"Error booking appointment: {e}")
        return False

def set_doctor_schedule(doc_id, duration, schedule_list):
    """
    Generates appointment slots for the next 4 weeks based on schedule.
    schedule_list: list of tuples [(day, start_time, end_time), ...]
    """
    try:
        with db_connection() as cursor:
            start_date = datetime.now().date()
            
            # Delete existing future appointments (from today onwards) before creating new ones
            start_date_str = start_date.strftime("%Y-%m-%d")
            cursor.execute("SELECT apno FROM DECLARES JOIN APPOINTMENT USING(apno) WHERE docid=? AND apdate >= ?", (doc_id, start_date_str))
            rows = cursor.fetchall()
            
            if rows:
                apnos = [r[0] for r in rows]
                placeholders = ','.join(['?'] * len(apnos))
                cursor.execute(f"DELETE FROM DECLARES WHERE apno IN ({placeholders})", apnos)
                cursor.execute(f"DELETE FROM APPOINTMENT WHERE apno IN ({placeholders})", apnos)

            end_date = start_date + timedelta(weeks=4)
            
            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime("%A")
                
                for sched_day, start, end in schedule_list:
                    if sched_day == day_name:
                        fmt = "%H:%M"
                        t_start = datetime.strptime(start, fmt)
                        t_end = datetime.strptime(end, fmt)
                        
                        while t_start + timedelta(minutes=int(duration)) <= t_end:
                            slot_time = t_start.strftime(fmt)
                            cursor.execute("INSERT INTO APPOINTMENT (apdate, aptime, availability) VALUES (?, ?, 1)", (current_date.strftime("%Y-%m-%d"), slot_time))
                            apno = cursor.lastrowid
                            cursor.execute("INSERT INTO DECLARES (docid, apno, duration, day) VALUES (?, ?, ?, ?)", (doc_id, apno, str(duration), day_name))
                            t_start += timedelta(minutes=int(duration))
                current_date += timedelta(days=1)
        return True
    except sqlite3.Error as e:
        print(f"Error setting schedule: {e}")
        return False


def show_patient(appoint_number):
    try:
        with db_connection() as cursor:
            cursor.execute("""SELECT u.firstname, u.lastname, p.patid, p.sex, p.allergie, p.birth_date, m.reason 
                              FROM MAKES m 
                              JOIN PATIENT p ON m.patid = p.patid 
                              JOIN USER u ON p.patid = u.id 
                              WHERE m.apno=?""", (appoint_number,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error: {e}")
        return []

def add_bill(apno, patid, payment_method, amount):
    try:
        with db_connection() as cursor:
            # Check if bill exists for this appointment
            cursor.execute("SELECT billid FROM BILL WHERE apno=?", (apno,))
            if cursor.fetchone():
                # Update existing bill
                cursor.execute("UPDATE BILL SET payment_meth=?, amount=?, payment=1 WHERE apno=?", (payment_method, amount, apno))
            else:
                # Insert new bill (payment=1 assumes 'Paid')
                cursor.execute("INSERT INTO BILL (apno, patid, payment_meth, payment, amount) VALUES (?, ?, ?, 1, ?)", (apno, patid, payment_method, amount))
            return True
    except sqlite3.Error as e:
        print(f"Error adding bill: {e}")
        return False

def show_patient_appointments(pat_id):
    """Επιστρέφει τα ραντεβού ενός συγκεκριμένου ασθενή."""
    try:
        with db_connection() as cursor:
            # Συνδέουμε MAKES -> APPOINTMENT -> DECLARES -> USER (για όνομα γιατρού)
            query = """
                SELECT a.apdate, a.aptime, u.firstname, u.lastname, a.apno, m.docid
                FROM MAKES m
                JOIN APPOINTMENT a ON m.apno = a.apno
                JOIN USER u ON m.docid = u.id
                WHERE m.patid = ?
                ORDER BY a.apdate, a.aptime
            """
            cursor.execute(query, (pat_id,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching patient appointments: {e}")
        return []

def cancel_appointment(apno):
    """Ακυρώνει το ραντεβού: Διαγράφει από MAKES και ελευθερώνει το APPOINTMENT."""
    try:
        with db_connection() as cursor:
            cursor.execute("DELETE FROM MAKES WHERE apno = ?", (apno,))
            cursor.execute("UPDATE APPOINTMENT SET availability = 1 WHERE apno = ?", (apno,))
            cursor.execute("UPDATE APPOINTMENT SET comment = NULL WHERE apno = ?", (apno,))
            return True
    except sqlite3.Error as e:
        print(f"Error canceling appointment: {e}")
        return False

def show_doctor_booked_appointments(doc_id):
    """Επιστρέφει τα κλεισμένα ραντεβού με λεπτομέρειες ασθενή και σχόλια."""
    try:
        with db_connection() as cursor:
            query = """
                SELECT u.firstname, u.lastname, a.comment, a.apdate, a.aptime, a.apno, b.payment, b.payment_meth, b.amount
                FROM MAKES m
                JOIN APPOINTMENT a ON m.apno = a.apno
                JOIN USER u ON m.patid = u.id
                LEFT JOIN BILL b ON a.apno = b.apno
                WHERE m.docid = ?
                ORDER BY a.apdate, a.aptime
            """
            cursor.execute(query, (doc_id,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching booked appointments: {e}")
        return []