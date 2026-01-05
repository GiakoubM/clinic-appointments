import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
import os

# Το όνομα του αρχείου της βάσης (πρέπει να είν αι σε κοινό φακελο με τον κωδικα)
# Παίρνει τον φάκελο που βρίσκεται το project_db.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Η βάση δεδομένων βρίσκεται στον ίδιο φάκελο
DATABASE_FILE = os.path.join(BASE_DIR, "project.db")

# Χρησιμοποιώ έναν context manager για τη συνδεση
# Αυτό βοηθάει να μην ξεχναω ανοιχτή τη σύνδεση και να γίνονται αυτόματα
# commit ή rollback (ακύρωση) αν κάτι πάει στραβά

@contextmanager
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE, timeout=30)
        # Ενεργοποιω τα Foreign Keys για να υπάρχει ακεραιότητα στα δεδομένα
        # (π.χ. να μην μπορώ να διαγράψω γιατρό αν έχει ραντεβού)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # Για να μπορώ να ζητάω τα πεδία με το όνομά τους
        yield conn.cursor()
        conn.commit() #Αποθήκευση αλλαγών
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback() # Ακύρωση αλλαγών αν γίνει λάθος
        raise
    finally:
        if conn:
            conn.close() # Κλείσιμο σύνδεσης

def verify_user(user_id, role=None):
    # Ελέγχω αν υπάρχει ο χρήστης ανάλογα με τον ρολο του (γιατρός ή ασθενής)
    if not user_id: return False
    try:
        with db_connection() as cursor:
            # Χρησιμοποιώ το ? (placeholders) για να αποφύγω SQL Injection
            if role == 'doctor':
                cursor.execute("SELECT docid FROM DOCTOR WHERE docid = ?", (user_id,))
            elif role == 'patient':
                cursor.execute("SELECT patid FROM PATIENT WHERE patid = ?", (user_id,))
            else:
                cursor.execute("SELECT id FROM USER WHERE id = ?", (user_id,))
            return cursor.fetchone() is not None
    except sqlite3.Error:
        return False

# Συνάρτηση για εγγραφή νέου χρήστη
def sing_up_user(user_id, phone, address, firstname, lastname, email, birth_date=None, sex=None, allergies=None):
    try:
        user_id = int(user_id)
    except ValueError:
        return False, "ID must be a number"

    try:
        with db_connection() as cursor:
            # Ζητώ τα γενικά στοιχέια του πίνακα USER
            cursor.execute("INSERT INTO USER (id, phone, address, firstname, lastname, email) VALUES (?,?,?,?,?,?)", 
                           (user_id, phone, address, firstname, lastname, email))
            # Ζητώ τα στοιχοία αν είναι ασθενής
            if birth_date or sex:
                cursor.execute("INSERT INTO PATIENT (patid, birth_date, sex, allergie) VALUES (?,?,?,?)", 
                               (user_id, birth_date, sex, allergies))
        return True, "Registered Successfully!"
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint" in str(e):
            return False, "User ID or Email already exists."
        return False, f"Database Integrity Error: {e}"
    except sqlite3.Error as e:
        return False, f"Database Error: {e}"

# Παίρνω τις μοναδικές ειδικότητες για να τις δείξω στο menu
def get_specialties():
    try:
        with db_connection() as cursor:
            cursor.execute("SELECT DISTINCT sname FROM HAS ORDER BY sname ASC")
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error:
        return []
    
# Εμφανίζω τους γιατρούς που έχουν τη συγκεκριμένη ειδικότητα
# Κάνω JOIN τους πίνακες USER, DOCTOR και HAS
def show_doctors(specialty_name):
    try:
        with db_connection() as cursor:
            query = """
            SELECT u.id, u.firstname, u.lastname, d.office
            FROM USER u
            JOIN DOCTOR d ON u.id = d.docid
            JOIN HAS h ON d.docid = h.docid
            WHERE h.sname = ?
            ORDER BY u.lastname
            """
            cursor.execute(query, (specialty_name,))
            # Επιστρέφουμε λίστα από tuples
            return [(r['id'], r['firstname'], r['lastname']) for r in cursor.fetchall()]
    except sqlite3.Error:
        return []

# Δημιουργία προγράμματος γιατρού.
# Αν ένα ραντεβού έχει κλειστεί, δεν το πειράζω (Ακεραιότητα δεδομένων)
def set_doctor_schedule(doc_id, duration, schedule_list):
    """
    ΔΙΟΡΘΩΣΗ: Δεν διαγράφουμε ραντεβού που έχουν κλειστεί (availability=0).
    Διαγράφουμε μόνο τα διαθέσιμα μελλοντικά για να μην δημιουργηθούν διπλοεγγραφές.
    """
    try:
        with db_connection() as cursor:
            start_date = datetime.now().date()
            start_date_str = start_date.strftime("%Y-%m-%d")
            
            # 1. Διαγραφή μόνο των ΔΙΑΘΕΣΙΜΩΝ (availability=1) μελλοντικών ραντεβού
            # Χρησιμοποιούμε subquery για να βρούμε τα apno που ανήκουν στον γιατρό
            delete_query = """
            DELETE FROM APPOINTMENT 
            WHERE availability = 1 
            AND apdate >= ? 
            AND apno IN (SELECT apno FROM DECLARES WHERE docid = ?)
            """
            cursor.execute(delete_query, (start_date_str, doc_id))
            
            # 2. Υπολογισμός και εισαγωγή νέου slot
            end_date = start_date + timedelta(weeks=4)
            current_date = start_date
            
            while current_date <= end_date:
                day_name = current_date.strftime("%A")
                date_str = current_date.strftime("%Y-%m-%d")

                for sched_day, start, end in schedule_list:
                    if sched_day == day_name:
                        fmt = "%H:%M"
                        t_start = datetime.strptime(start, fmt)
                        t_end = datetime.strptime(end, fmt)
                        
                        while t_start + timedelta(minutes=int(duration)) <= t_end:
                            slot_time = t_start.strftime(fmt)
                            
                            # Έλεγχος αν υπάρχει ήδη κλεισμένο ραντεβού για να μην γίνει διπλοεγγραφή
                            check_query = """
                            SELECT 1 FROM APPOINTMENT a
                            JOIN DECLARES d ON a.apno = d.apno
                            WHERE d.docid = ? AND a.apdate = ? AND a.aptime = ?
                            """
                            cursor.execute(check_query, (doc_id, date_str, slot_time))
                            
                            if not cursor.fetchone():
                                # Αν δεν υπάρχει, το δημιουργούμε
                                cursor.execute("INSERT INTO APPOINTMENT (apdate, aptime, availability) VALUES (?, ?, 1)", 
                                               (date_str, slot_time))
                                new_apno = cursor.lastrowid
                                cursor.execute("INSERT INTO DECLARES (docid, apno, duration, day) VALUES (?, ?, ?, ?)", 
                                               (doc_id, new_apno, str(duration), day_name))
                            
                            t_start += timedelta(minutes=int(duration))
                
                current_date += timedelta(days=1)
        return True
    except sqlite3.Error as e:
        print(f"Error setting schedule: {e}")
        return False

# Κλείσιμο ραντεβού. Χρησιμοποιώ Transaction μέσω του db_connection
def book_appointment(pat_id, doc_id, apno, reason):
    try:
        with db_connection() as cursor:
            # Έλεγχος αν το ραντεβού είναι ακόμα διαθέσιμο (Concurrency control)
            cursor.execute("SELECT availability FROM APPOINTMENT WHERE apno = ?", (apno,))
            row = cursor.fetchone()
            if not row or row['availability'] == 0:
                return False # Κάποιος άλλος έχει κλείσει

            # Ενημέρωση ότι δεν είναι πια διαθέσιμο
            cursor.execute("UPDATE APPOINTMENT SET comment = ?, availability = 0 WHERE apno = ?", (reason, apno))
            
            # Εισαγωγή στον πίνακα MAKES (σύνδεση ασθενή-ραντεβού)
            cursor.execute("INSERT INTO MAKES (docid, patid, apno, reason) VALUES (?, ?, ?, ?)", 
                           (doc_id, pat_id, apno, reason))
        return True
    except sqlite3.Error as e:
        print(f"Booking error: {e}")
        return False

# Εμφάνιση ραντεβού με βάση το ID του γιατρού
def show_appointments(doc_id, only_free=True, date_filter=None):
    try:
        with db_connection() as cursor:
            query = """
                SELECT a.apdate, a.aptime, a.availability, a.apno
                FROM APPOINTMENT a
                JOIN DECLARES d ON a.apno = d.apno
                WHERE d.docid = ? 
            """
            params = [doc_id]
            if only_free:
                query += " AND a.availability = 1"
            
            if date_filter:
                query += " AND strftime('%Y-%m-%d', a.apdate) = ?"
                params.append(date_filter)

            query += " GROUP BY a.apdate, a.aptime ORDER BY a.apdate, a.aptime"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except sqlite3.Error:
        return []

# JOIN για να δω τα στοιχεία του ασθενή και αν έχει πληρώσει (BILL)
def show_patient_appointments(pat_id):
    try:
        with db_connection() as cursor:
            query = """
                SELECT a.apdate, a.aptime, u.firstname, u.lastname, d.office, a.apno, m.docid
                FROM MAKES m
                JOIN APPOINTMENT a ON m.apno = a.apno
                JOIN USER u ON m.docid = u.id
                JOIN DOCTOR d ON m.docid = d.docid
                WHERE m.patid = ?
                ORDER BY a.apdate DESC, a.aptime DESC
            """
            cursor.execute(query, (pat_id,))
            return cursor.fetchall()
    except sqlite3.Error:
        return []

# Ακύρωση ραντεβού (Διαγραφή από MAKES, Ενημέρωση APPOINTMENT)
def cancel_appointment(apno):
    try:
        with db_connection() as cursor:
            # Πρώτα παίρνουμε τα στοιχεία για να τα βάλουμε στο CANCELS
            cursor.execute("SELECT docid, patid FROM MAKES WHERE apno = ?", (apno,))
            res = cursor.fetchone()
            
            if res:
                docid, patid = res['docid'], res['patid']
                # Διαγραφή από MAKES
                cursor.execute("DELETE FROM MAKES WHERE apno = ?", (apno,))
                
                # Ενημέρωση APPOINTMENT σε διαθέσιμο
                cursor.execute("UPDATE APPOINTMENT SET availability = 1, comment = NULL WHERE apno = ?", (apno,))
                
                # (Προαιρετικά) Καταγραφή στο CANCELS για ιστορικότητα
                try:
                    cursor.execute("INSERT INTO CANCELS (docid, patid, apno) VALUES (?, ?, ?)", (docid, patid, apno))
                except sqlite3.Error:
                    pass # Αν υπάρχει ήδη ή αποτύχει, δεν πειράζει, η ακύρωση έγινε
            
        return True
    except sqlite3.Error as e:
        print(f"Cancel error: {e}")
        return False

# JOIN για να δω τα στοιχεία του ασθενή και αν έχει πληρώσει (BILL)
def show_doctor_booked_appointments(doc_id):
    try:
        with db_connection() as cursor:
            query = """
                SELECT u.firstname, u.lastname, m.reason, a.apdate, a.aptime, a.apno, 
                       b.payment, b.payment_meth, b.amount
                FROM MAKES m
                JOIN APPOINTMENT a ON m.apno = a.apno
                JOIN USER u ON m.patid = u.id
                LEFT JOIN BILL b ON a.apno = b.apno
                WHERE m.docid = ?
                ORDER BY a.apdate, a.aptime
            """
            cursor.execute(query, (doc_id,))
            return cursor.fetchall()
    except sqlite3.Error:
        return []

# Πληρωμή ραντεβού
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

# Βρίσκω τα στοιχεία του ασθενή για ένα συγκεκριμένο ραντεβού
def show_patient(appoint_number):
    try:
        with db_connection() as cursor:
            cursor.execute("""
                SELECT u.firstname, u.lastname, u.id, p.sex, p.allergie, p.birth_date, m.reason 
                FROM MAKES m 
                JOIN PATIENT p ON m.patid = p.patid 
                JOIN USER u ON p.patid = u.id 
                WHERE m.apno=?
            """, (appoint_number,))
            return cursor.fetchall()
    except sqlite3.Error:
        return []

# Συνάρτηση στατιστικών με GROUP BY και Aggregate Functions (SUM, COUNT)
def get_doctor_stats(doc_id):
    """
    Επιστρέφει στατιστικά για τον γιατρό:
    1. Συνολικά ραντεβού
    2. Συνολικά έσοδα
    3. Ραντεβού ανά ημέρα (Group By)
    """
    stats = {}
    try:
        with db_connection() as cursor:
            # Συνολικά Ραντεβού
            cursor.execute("SELECT COUNT(*) FROM MAKES WHERE docid = ?", (doc_id,))
            stats['total_appts'] = cursor.fetchone()[0]

            # Συνολικά Έσοδα (Aggregation SUM)
            cursor.execute("""
                SELECT SUM(amount) FROM BILL 
                JOIN APPOINTMENT USING(apno)
                JOIN DECLARES USING(apno)
                WHERE docid = ? AND payment = 1
            """, (doc_id,))
            res = cursor.fetchone()[0]
            stats['total_revenue'] = res if res else 0.0

            # Ομαδοποίηση ανά τρόπο πληρωμής (GROUP BY)
            cursor.execute("""
                SELECT payment_meth, COUNT(*) as count 
                FROM BILL 
                JOIN DECLARES USING(apno)
                WHERE docid = ? 
                GROUP BY payment_meth
            """, (doc_id,))
            stats['payment_methods'] = cursor.fetchall()
            
    except sqlite3.Error as e:
        print(f"Stats Error: {e}")
    return stats