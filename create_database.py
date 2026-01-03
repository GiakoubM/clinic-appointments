import sqlite3
from pathlib import Path

# -----------------------------
# Ρυθμίσεις
# -----------------------------

DB_NAME = "project.db"   # Η βάση θα δημιουργηθεί στον ίδιο φάκελο
DB_PATH = Path(__file__).parent / DB_NAME


def create_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ενεργοποίηση foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Διαγραφή πινάκων (αν υπάρχουν)
    
    cursor.executescript("""
    DROP TABLE IF EXISTS CANCELS;
    DROP TABLE IF EXISTS BILL;
    DROP TABLE IF EXISTS MAKES;
    DROP TABLE IF EXISTS DECLARES;
    DROP TABLE IF EXISTS HAS;
    DROP TABLE IF EXISTS APPOINTMENT;
    DROP TABLE IF EXISTS SPECIALTY;
    DROP TABLE IF EXISTS DOCTOR;
    DROP TABLE IF EXISTS PATIENT;
    DROP TABLE IF EXISTS USER;
    """)

    # Δημιουργία πινάκων

    cursor.executescript("""
    CREATE TABLE USER (
        id INTEGER PRIMARY KEY,
        firstname TEXT NOT NULL,
        lastname TEXT NOT NULL,
        address TEXT NOT NULL,
        phone INTEGER NOT NULL,
        email TEXT NOT NULL
    );

    CREATE TABLE SPECIALTY (
        Name TEXT PRIMARY KEY
    );

    CREATE TABLE DOCTOR (
        docid INTEGER PRIMARY KEY,
        office TEXT,
        FOREIGN KEY (docid) REFERENCES USER(id)
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE PATIENT (
        patid INTEGER PRIMARY KEY,
        sex TEXT NOT NULL,
        allergie TEXT,
        birth_date TEXT NOT NULL,
        FOREIGN KEY (patid) REFERENCES USER(id)
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE APPOINTMENT (
        apno INTEGER PRIMARY KEY AUTOINCREMENT,
        apdate TEXT,
        aptime TEXT,
        availability INTEGER,
        comment TEXT
    );

    CREATE TABLE HAS (
        docid INTEGER NOT NULL,
        sname TEXT NOT NULL,
        PRIMARY KEY (docid, sname),
        FOREIGN KEY (docid) REFERENCES DOCTOR(docid)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (sname) REFERENCES SPECIALTY(Name)
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE DECLARES (
        apno INTEGER PRIMARY KEY AUTOINCREMENT,
        docid INTEGER NOT NULL,
        duration TEXT,
        day TEXT,
        FOREIGN KEY (apno) REFERENCES APPOINTMENT(apno)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (docid) REFERENCES DOCTOR(docid)
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE MAKES (
        apno INTEGER PRIMARY KEY,
        docid INTEGER NOT NULL,
        patid INTEGER NOT NULL,
        reason TEXT,
        FOREIGN KEY (apno) REFERENCES APPOINTMENT(apno)
            ON DELETE CASCADE,
        FOREIGN KEY (docid) REFERENCES DOCTOR(docid),
        FOREIGN KEY (patid) REFERENCES PATIENT(patid)
    );

    CREATE TABLE BILL (
        billid INTEGER PRIMARY KEY AUTOINCREMENT,
        apno INTEGER NOT NULL UNIQUE,
        patid INTEGER NOT NULL,
        payment_meth TEXT NOT NULL,
        payment INTEGER NOT NULL,
        amount REAL,
        FOREIGN KEY (apno) REFERENCES APPOINTMENT(apno)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (patid) REFERENCES PATIENT(patid)
            ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE CANCELS (
        docid INTEGER NOT NULL,
        patid INTEGER NOT NULL,
        apno INTEGER NOT NULL,
        PRIMARY KEY (docid, patid, apno),
        FOREIGN KEY (apno) REFERENCES APPOINTMENT(apno)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (docid) REFERENCES DOCTOR(docid)
            ON UPDATE CASCADE ON DELETE CASCADE,
        FOREIGN KEY (patid) REFERENCES PATIENT(patid)
            ON UPDATE CASCADE ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print("✅ Η βάση δεδομένων δημιουργήθηκε επιτυχώς!")


if __name__ == "__main__":
    create_db()
