import tkinter as tk
from tkinter import ttk
from datetime import datetime
from connect_functions import (
    handle_patient_click, handle_doctor_click, attempt_login, 
    show_signup, back_to_home, submit_signup, back_to_login
)
import paho.mqtt.client as mqtt



def main_window():
    root = tk.Tk()
    root.title("Clinic App")
    root.geometry("800x600")
    
    #Χρώματα
    bg_color = "#E6F2FF"  #backgound
    text_color = "#004080" 

    root.configure(bg=bg_color)
    style = ttk.Style()
    style.configure("TFrame", background=bg_color)

    # Main container
    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    home_frame = ttk.Frame(container)
    doctor_frame = ttk.Frame(container)
    signup_frame = ttk.Frame(container)
    patient_frame=ttk.Frame(container)
    login_frame = ttk.Frame(container)
    
    # Μεταβλητή για το ID του χρήστη
    current_user_id_var = tk.StringVar()
    
    # #Μεταβλητές για να αλλάζει το text ανάλογα με τον χρήστη
    login_title_var = tk.StringVar(value="Login")
    login_prompt_var = tk.StringVar(value="Enter ID:")
    signup_title_var = tk.StringVar(value="Registration")
    id_label_var = tk.StringVar(value="ID")

    for f in (home_frame, doctor_frame, signup_frame, patient_frame, login_frame):
        f.grid(row=0, column=0, sticky="nsew")

    # Welcome Label
    welcome_label = ttk.Label(home_frame, text="Welcome to the Clinic", font=("Verdana", 28, "bold"), foreground=text_color, background=bg_color)
    welcome_label.pack(side="top", pady=50)

    button_frame = ttk.Frame(home_frame)
    button_frame.pack(expand=True)

    patient_btn = ttk.Button(button_frame, text="Entry for patients", command=lambda: handle_patient_click(login_title_var, login_prompt_var, signup_title_var, id_label_var, login_frame, btn_signup_nav, btn_back))
    patient_btn.pack(pady=10, ipadx=10, ipady=5)

    doctor_btn = ttk.Button(button_frame, text="Entry for doctors", command=lambda: handle_doctor_click(login_title_var, login_prompt_var, signup_title_var, id_label_var, login_frame, btn_signup_nav))
    doctor_btn.pack(pady=10, ipadx=10, ipady=5)

    #Doctor Frame
    lbl_doc_title = ttk.Label(login_frame, textvariable=login_title_var, font=("Verdana", 24, "bold"), foreground=text_color, background=bg_color)
    lbl_doc_title.pack(pady=40)

    lbl_id = ttk.Label(login_frame, textvariable=login_prompt_var, font=("Verdana", 14), background=bg_color)
    lbl_id.pack(pady=5)

    entry_id = ttk.Entry(login_frame, font=("Verdana", 14))
    entry_id.pack(pady=10)

    lbl_message = ttk.Label(login_frame, text="", font=("Verdana", 12), background=bg_color)
    lbl_message.pack(pady=5)
    #Patient frame:
    

    btn_login = ttk.Button(login_frame, text="Login", command=lambda: attempt_login(entry_id, lbl_message, login_title_var, current_user_id_var))
    btn_login.pack(pady=10)
    
    entry_id.bind("<Return>", lambda event: attempt_login(entry_id, lbl_message, login_title_var, current_user_id_var, event)) #όταν πατηθεί enter να εκτελεστεί η attempt_login

    btn_signup_nav = ttk.Button(login_frame, text="Sign Up", command=lambda: show_signup(signup_frame))
    btn_signup_nav.pack(pady=5)

    btn_back = ttk.Button(login_frame, text="Back", command=lambda: back_to_home(home_frame))
    btn_back.pack(pady=20)

    #Signup Frame
    lbl_signup = ttk.Label(signup_frame, textvariable=signup_title_var, font=("Verdana", 20, "bold"), foreground=text_color, background=bg_color)
    lbl_signup.pack(pady=20)
    


    form_frame = ttk.Frame(signup_frame)
    form_frame.pack(pady=10)
    entries = {}
    row = ttk.Frame(form_frame)
    row.pack(fill="x", pady=5)
    ttk.Label(row, textvariable=id_label_var, width=15, anchor="w", background=bg_color).pack(side="left")
    ent_id = ttk.Entry(row, width=30)
    ent_id.pack(side="left")
    entries["ID_FIELD"] = ent_id

    field_hints = {
        "AMKA": "(10-digit)",
        "Address": "(City, Street+Number, e.g. Athens, Akropolis 40)",
        "Sex": "(F - for female and M - for male)",
        "Phone": "(e.g. +306900000000)",
        "Allergies": "(e.g. Penicillin)"
    }

    for field in ["First Name", "Last Name", "Phone", "Address", "Email"]:
        row = ttk.Frame(form_frame)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=field, width=15, anchor="w", background=bg_color).pack(side="left")
        ent = ttk.Entry(row, width=30)
        ent.pack(side="left")
        entries[field] = ent
        if field in field_hints:
            ttk.Label(row, text=field_hints[field], font=("Verdana", 8), foreground="#555555", background=bg_color).pack(side="left", padx=5)

    # Για την ημερομηνία γέννησης
    row = ttk.Frame(form_frame)
    row.pack(fill="x", pady=5)
    ttk.Label(row, text="Birth Date", width=15, anchor="w", background=bg_color).pack(side="left")
    
    days = [str(i) for i in range(1, 32)]
    cb_day = ttk.Combobox(row, values=days, width=3, state="readonly")
    cb_day.set("Day")
    cb_day.pack(side="left", padx=(0, 5))
    entries["Birth_Day"] = cb_day

    months = [str(i) for i in range(1, 13)]
    cb_month = ttk.Combobox(row, values=months, width=4, state="readonly")
    cb_month.set("Month")
    cb_month.pack(side="left", padx=(0, 5))
    entries["Birth_Month"] = cb_month

    current_year = datetime.now().year
    years = [str(i) for i in range(current_year, 1900, -1)]
    cb_year = ttk.Combobox(row, values=years, width=6, state="readonly")
    cb_year.set("Year")
    cb_year.pack(side="left")
    entries["Birth_Year"] = cb_year

    for field in ["Sex"]:
        row = ttk.Frame(form_frame)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=field, width=15, anchor="w", background=bg_color).pack(side="left")
        ent = ttk.Entry(row, width=30)
        ent.pack(side="left")
        entries[field] = ent
        if field in field_hints:
            ttk.Label(row, text=field_hints[field], font=("Verdana", 8), foreground="#555555", background=bg_color).pack(side="left", padx=5)

    # Για τις αλλεργίες
    row = ttk.Frame(form_frame)
    row.pack(fill="x", pady=5)
    ttk.Label(row, text="Tick the box if you have Allergies?", anchor="w", background=bg_color).pack(side="left")
    
    has_allergies = tk.BooleanVar()
    ent_allergies = ttk.Entry(row, width=30)
    entries["Allergies"] = ent_allergies
    
    def toggle_allergies():
        if has_allergies.get():
            ent_allergies.pack(side="left", padx=5)
        else:
            ent_allergies.delete(0, tk.END)
            ent_allergies.pack_forget()

    chk_allergies = ttk.Checkbutton(row, text="Yes", variable=has_allergies, command=toggle_allergies)
    chk_allergies.pack(side="left")

    lbl_res = ttk.Label(signup_frame, text="", font=("Verdana", 10), background=bg_color)
    lbl_res.pack(pady=5)

    ttk.Button(signup_frame, text="Register", command=lambda: submit_signup(entries, lbl_res)).pack(pady=10)
    
    ttk.Button(signup_frame, text="Back to Login", command=lambda: back_to_login(lbl_res, login_frame)).pack(pady=5)

    
    home_frame.tkraise()

    root.mainloop()

if __name__ == "__main__":
    main_window()