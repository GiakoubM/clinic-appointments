import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from project_db import get_specialties, show_doctors, show_appointments, book_appointment, show_patient_appointments, cancel_appointment

class PatientWindow:
    def __init__(self, root, patient_id):
        self.root = root
        self.patient_id = patient_id
        self.root.title(f"Πίνακας Ασθενή - AMKA: {patient_id}")
        self.root.geometry("600x500")
        self.root.configure(bg="#E6F2FF")

        # Δημιουργία Tabs (Notebook)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Κλείσιμο Ραντεβού
        self.tab_book = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_book, text='Κλείσιμο Ραντεβού')

        # Tab 2: Τα Ραντεβού μου
        self.tab_my_apps = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_my_apps, text='Τα Ραντεβού μου')

        self.setup_booking_tab()
        self.setup_my_appointments_tab()

        # Όταν αλλάζει tab, να κάνουμε refresh
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def setup_booking_tab(self):
        # Κεντρικός τίτλος
        # Χρησιμοποιούμε self.tab_book αντί για self.root
        ttk.Label(self.tab_book, text="Κλείσιμο Ραντεβού", font=("Verdana", 16, "bold")).pack(pady=20)

        # --- Επιλογή Ειδικότητας ---
        ttk.Label(self.tab_book, text="1. Επιλέξτε Ειδικότητα:").pack(pady=5)
        self.cb_specialty = ttk.Combobox(self.tab_book, state="readonly", width=40)
        self.cb_specialty.pack(pady=5)
        
        # Γέμισμα ειδικοτήτων
        specialties = get_specialties()
        self.cb_specialty['values'] = specialties
        self.cb_specialty.bind("<<ComboboxSelected>>", self.on_specialty_select)

        # --- Επιλογή Γιατρού ---
        ttk.Label(self.tab_book, text="2. Επιλέξτε Γιατρό:").pack(pady=5)
        self.cb_doctor = ttk.Combobox(self.tab_book, state="readonly", width=40)
        self.cb_doctor.pack(pady=5)
        self.cb_doctor.bind("<<ComboboxSelected>>", self.on_doctor_select)
        
        # Λίστα για να κρατάμε τα IDs των γιατρών που φορτώνονται
        self.loaded_doctors = [] 

        # --- Επιλογή Ραντεβού (Ημερομηνία & Ώρα) ---
        ttk.Label(self.tab_book, text="3. Επιλέξτε Ημερομηνία και Ώρα:").pack(pady=5)
        
        self.frame_datetime = ttk.Frame(self.tab_book)
        self.frame_datetime.pack(pady=5)

        self.cb_date = ttk.Combobox(self.frame_datetime, state="readonly", width=18)
        self.cb_date.pack(side="left", padx=5)
        self.cb_date.bind("<<ComboboxSelected>>", self.on_date_select)

        self.cb_time = ttk.Combobox(self.frame_datetime, state="readonly", width=10)
        self.cb_time.pack(side="left", padx=5)
        
        # Λίστα για να κρατάμε τα IDs των ραντεβού (apno)
        self.loaded_appointments = []

        # --- Σχόλια ---
        ttk.Label(self.tab_book, text="4. Σχόλια (Προαιρετικό):").pack(pady=5)
        self.ent_comment = ttk.Entry(self.tab_book, width=40)
        self.ent_comment.pack(pady=5)

        # --- Κουμπί Κράτησης ---
        self.btn_book = ttk.Button(self.tab_book, text="Κράτηση Ραντεβού", command=self.book_now, state="disabled")
        self.btn_book.pack(pady=30)

        # Μήνυμα επιβεβαίωσης
        self.lbl_status = ttk.Label(self.tab_book, text="", font=("Verdana", 10))
        self.lbl_status.pack(pady=5)

    def on_specialty_select(self, event):
        """Όταν επιλέγει ειδικότητα, φέρε τους γιατρούς"""
        selected_spec = self.cb_specialty.get()
        doctors = show_doctors(selected_spec) # Επιστρέφει (docid, firstname, lastname)
        
        # Καθαρισμός επόμενων πεδίων
        self.cb_doctor.set('')
        self.cb_date.set('')
        self.cb_time.set('')
        self.cb_date['values'] = []
        self.cb_time['values'] = []
        self.btn_book.config(state="disabled")

        if doctors:
            # Φτιάχνουμε μια λίστα ονομάτων για το Combobox και κρατάμε τα IDs
            self.loaded_doctors = doctors # [(id, name, surname), ...]
            doc_names = [f"{doc[1]} {doc[2]}" for doc in doctors]
            self.cb_doctor['values'] = doc_names
        else:
            self.cb_doctor['values'] = ["Δεν βρέθηκαν γιατροί"]

    def on_doctor_select(self, event):
        """Όταν επιλέγει γιατρό, φέρε τα ραντεβού"""
        idx = self.cb_doctor.current()
        if idx == -1: return

        doc_id = self.loaded_doctors[idx][0] # Παίρνουμε το ID του επιλεγμένου γιατρού
        appointments = show_appointments(doc_id) # Επιστρέφει (apdate, aptime, availability, apno)

        self.cb_date.set('')
        self.cb_time.set('')
        self.cb_time['values'] = []
        
        if appointments:
            # Η SQL query επιστρέφει ήδη μόνο τα διαθέσιμα (availability=1)
            # app structure: (apdate, aptime, availability, apno)
            self.loaded_appointments = appointments
            
            # Βρίσκουμε τις μοναδικές ημερομηνίες
            unique_dates = sorted(list(set(app[0] for app in appointments)))
            self.cb_date['values'] = unique_dates
            
            if self.loaded_appointments:
                self.btn_book.config(state="normal")
            else:
                self.cb_date['values'] = ["Μη διαθέσιμο"]
                self.btn_book.config(state="disabled")
        else:
            self.cb_date['values'] = ["Μη διαθέσιμο"]
            self.btn_book.config(state="disabled")

    def on_date_select(self, event):
        """Όταν επιλέγει ημερομηνία, φέρε τις ώρες"""
        selected_date = self.cb_date.get()
        # Φιλτράρουμε τις ώρες για τη συγκεκριμένη ημερομηνία
        available_times = [app[1] for app in self.loaded_appointments if app[0] == selected_date]
        self.cb_time['values'] = available_times
        self.cb_time.set('')

    def book_now(self):
        """Εκτέλεση της κράτησης"""
        # Πρέπει να βρούμε ποιο ραντεβού διάλεξε
        doc_idx = self.cb_doctor.current()
        date = self.cb_date.get()
        time = self.cb_time.get()
        
        if doc_idx == -1 or not date or not time:
            messagebox.showerror("Error", "Παρακαλώ επιλέξτε όλα τα πεδία")
            return

        # Ανάκτηση δεδομένων από τις λίστες μας
        # Βρίσκουμε το apno με βάση την ημερομηνία και ώρα
        apno = None
        for app in self.loaded_appointments:
            if app[0] == date and app[1] == time:
                apno = app[3]
                break
        
        if apno is None:
            messagebox.showerror("Error", "Το ραντεβού δεν βρέθηκε.")
            return

        doc_id = self.loaded_doctors[doc_idx][0]
        
        # Ανάκτηση σχολίου
        comment = self.ent_comment.get().strip()
        if not comment: comment = "-"
        
        # Κλήση της συνάρτησης database
        success = book_appointment(self.patient_id, doc_id, apno, comment)
        
        if success:
            messagebox.showinfo("Επιτυχία", "Το ραντεβού έκλεισε επιτυχώς!")
            self.lbl_status.config(text="Το ραντεβού κατοχυρώθηκε!", foreground="green")
            # Ανανέωση της λίστας (αφού το ραντεβού δεν είναι πια διαθέσιμο)
            self.on_doctor_select(None)
        else:
            messagebox.showerror("Σφάλμα", "Κάτι πήγε στραβά. Προσπαθήστε ξανά.")

    def setup_my_appointments_tab(self):
        """Στήσιμο του Tab για τα ραντεβού του ασθενή"""
        ttk.Label(self.tab_my_apps, text="Τα Ραντεβού μου", font=("Verdana", 16, "bold")).pack(pady=20)

        # Treeview
        columns = ("Date", "Time", "Doctor", "ID")
        self.tree_apps = ttk.Treeview(self.tab_my_apps, columns=columns, show='headings', height=10)
        self.tree_apps.heading("Date", text="Ημερομηνία")
        self.tree_apps.heading("Time", text="Ώρα")
        self.tree_apps.heading("Doctor", text="Γιατρός")
        self.tree_apps.column("ID", width=0, stretch=False) # Κρύβουμε το ID
        self.tree_apps.pack(fill='both', expand=True, padx=10, pady=5)

        btn_cancel = ttk.Button(self.tab_my_apps, text="Ακύρωση Επιλεγμένου", command=self.cancel_selected)
        btn_cancel.pack(pady=10)

    def refresh_my_appointments(self):
        """Ανανεώνει τη λίστα με τα ραντεβού"""
        for item in self.tree_apps.get_children():
            self.tree_apps.delete(item)
        
        apps = show_patient_appointments(self.patient_id)
        for app in apps:
            # app: (date, time, fname, lname, apno)
            doc_name = f"{app[2]} {app[3]}"
            self.tree_apps.insert("", "end", values=(app[0], app[1], doc_name, app[4]))

    def cancel_selected(self):
        selected = self.tree_apps.selection()
        if not selected:
            messagebox.showwarning("Προσοχή", "Παρακαλώ επιλέξτε ένα ραντεβού για ακύρωση.")
            return
        
        item = self.tree_apps.item(selected)
        apno = item['values'][3] # Το ID είναι στην 4η στήλη

        if messagebox.askyesno("Επιβεβαίωση", "Είστε σίγουροι ότι θέλετε να ακυρώσετε το ραντεβού;"):
            if cancel_appointment(apno):
                messagebox.showinfo("Επιτυχία", "Το ραντεβού ακυρώθηκε.")
                self.refresh_my_appointments()

    def on_tab_change(self, event):
        # Αν επιλέχθηκε το 2ο tab (index 1), κάνε refresh
        if self.notebook.index(self.notebook.select()) == 1:
            self.refresh_my_appointments()