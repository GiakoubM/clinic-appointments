from project_db import verify_user, sing_up_user
import tkinter as tk
from patient_window import PatientWindow
from doctor_dashboard import create_doctor_dashboard


def handle_patient_click(login_title_var, login_prompt_var, signup_title_var, id_label_var, login_frame, signup_btn, back_btn):
    login_title_var.set("Patient Login")
    login_prompt_var.set("Εισάγετε το ΑΜΚΑ σας:")
    signup_title_var.set("New Patient Registration")
    id_label_var.set("ΑΜΚΑ")
    signup_btn.pack(pady=5, before=back_btn)
    login_frame.tkraise()

def handle_doctor_click(login_title_var, login_prompt_var, signup_title_var, id_label_var, login_frame, signup_btn):
    login_title_var.set("Doctor Login")
    login_prompt_var.set("Εισάγετε το ID σας:")
    signup_title_var.set("New Doctor Registration")
    id_label_var.set("ID")
    signup_btn.pack_forget()
    login_frame.tkraise()

def attempt_login(entry_id, lbl_message, login_title_var, current_user_id_var, event=None):
    user_id = entry_id.get()
    
    # Determine role based on the login screen title
    role = 'doctor' if "Doctor" in login_title_var.get() else 'patient'
    
    if verify_user(user_id, role):
        lbl_message.config(text="Login Successful!", foreground="green")
        current_user_id_var.set(user_id)
        
        # Check if we are in Doctor Login mode
        if "Doctor" in login_title_var.get():
            root = entry_id.winfo_toplevel()
            root.withdraw()
            
            new_window = tk.Toplevel()
            new_window.title("Doctor Dashboard")
            new_window.geometry("800x600")
            
            def on_close():
                new_window.destroy()
                root.deiconify()
            new_window.protocol("WM_DELETE_WINDOW", on_close)
            
            class LogoutHandler:
                def tkraise(self):
                    on_close()
            
            dashboard = create_doctor_dashboard(new_window, LogoutHandler(), current_user_id_var)
            dashboard.pack(fill="both", expand=True)
        else:
            # Patient Login Logic
            new_window = tk.Toplevel() 
            app = PatientWindow(new_window, user_id)
            
            # Hide the main login window and restore it when the patient window closes
            root = entry_id.winfo_toplevel()
            root.withdraw()
            def on_close():
                new_window.destroy()
                root.deiconify()
            new_window.protocol("WM_DELETE_WINDOW", on_close)
    else:
        lbl_message.config(text="Invalid ID", foreground="red")

def show_signup(signup_frame):
    signup_frame.tkraise()

def back_to_home(home_frame):
    home_frame.tkraise()

def submit_signup(entries, lbl_res):
    for key, entry in entries.items():
        val = entry.get().strip()
        # Check if Phone is still the placeholder
        if key == "Phone" and val == "+30690000000":
            lbl_res.config(text="Please enter a valid phone number", foreground="red")
            return
        
        # Check for default values in date dropdowns
        if key in ["Birth_Day", "Birth_Month", "Birth_Year"] and val in ["Day", "Month", "Year"]:
            lbl_res.config(text="Please select a valid Birth Date", foreground="red")
            return

        # Check for empty fields (Allergies can be optional if desired, but here we enforce all)
        if not val:
            lbl_res.config(text="All fields are required", foreground="red")
            return

    # Construct Birth Date
    day = entries["Birth_Day"].get()
    month = entries["Birth_Month"].get()
    year = entries["Birth_Year"].get()
    birth_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    if sing_up_user(entries["ID_FIELD"].get(), entries["Phone"].get(), entries["Address"].get(),
                    entries["First Name"].get(), entries["Last Name"].get(), entries["Email"].get(),
                    "", # City (Placeholder as per current form fields)
                    birth_date, entries["Sex"].get(), entries["Allergies"].get()):
        lbl_res.config(text="Registered Successfully!", foreground="green")
    else:
        lbl_res.config(text="Registration Failed (ID might exist)", foreground="red")

def back_to_login(lbl_res, login_frame):
    lbl_res.config(text="") # Clear any previous messages
    login_frame.tkraise()