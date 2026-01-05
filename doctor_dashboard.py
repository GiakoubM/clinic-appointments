import tkinter as tk
from tkinter import ttk, messagebox
from project_db import set_doctor_schedule, show_appointments, show_patient, add_bill, show_doctor_booked_appointments, get_doctor_stats
import paho.mqtt.client as mqtt


#Δημιουργω το παραθυρο
def create_doctor_dashboard(container, home_frame, current_user_id_var):
    frame = ttk.Frame(container)
    
    # Τίτλος
    lbl_title = ttk.Label(frame, text="Doctor Dashboard", font=("Verdana", 20, "bold"))
    lbl_title.pack(pady=20)

    # Πρόγραμμα
    schedule_frame = ttk.LabelFrame(frame, text="Management Panel", padding=10)
    schedule_frame.pack(fill="x", padx=20, pady=10)

    # Επιλογή Διάρκειας ραντεβού
    ttk.Label(schedule_frame, text="Slot Duration (mins):").grid(row=0, column=0, padx=5)
    combo_duration = ttk.Combobox(schedule_frame, values=["15", "20", "30", "45", "60"], width=5)
    combo_duration.set("30")
    combo_duration.grid(row=0, column=1, padx=5)

    # Μέρες και Ώρες Ραντεβού
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_vars = {}
    time_entries = {}

    for i, day in enumerate(days):
        row = i + 1
        var = tk.IntVar()
        chk = tk.Checkbutton(schedule_frame, text=day, variable=var, anchor="w")
        chk.grid(row=row, column=0, sticky="w")
        days_vars[day] = var

        ttk.Label(schedule_frame, text="Start:").grid(row=row, column=1)
        ent_start = ttk.Entry(schedule_frame, width=8)
        ent_start.insert(0, "09:00")
        ent_start.grid(row=row, column=2, padx=2)

        ttk.Label(schedule_frame, text="End:").grid(row=row, column=3)
        ent_end = ttk.Entry(schedule_frame, width=8)
        ent_end.insert(0, "17:00")
        ent_end.grid(row=row, column=4, padx=2)
        
        time_entries[day] = (ent_start, ent_end)

    def save_schedule():
        # Αποθήκευση προγράμματος στην βάση
        doc_id = current_user_id_var.get()
        try:
            duration = int(combo_duration.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid Duration")
            return

        schedule_list = []
        for day, var in days_vars.items():
            if var.get() == 1:
                start = time_entries[day][0].get()
                end = time_entries[day][1].get()
                schedule_list.append((day, start, end))

        if set_doctor_schedule(doc_id, duration, schedule_list):
            messagebox.showinfo("Success", "Schedule updated!")
            refresh_appointments()
        else:
            messagebox.showerror("Error", "Failed to update schedule.")

    # κουμπιά
    ttk.Button(schedule_frame, text="Save Schedule", command=save_schedule).grid(row=8, column=0, pady=10, padx=5)
    
    btn_show_schedule = ttk.Button(schedule_frame, text="Show Schedule")
    btn_show_schedule.grid(row=9, column=0, padx=5, pady=10)
    
    def show_booked_details():
        #Για τις λεπτομέρειες των ραντεβου
        tree["displaycolumns"] = "#all"
        tree["columns"] = ("Patient", "Comment", "Date", "Time", "Paid", "Method", "Amount", "ID")
        tree["displaycolumns"] = ("Patient", "Comment", "Date", "Time", "Paid", "Method", "Amount")
        
        tree.heading("Patient", text="Patient Name")
        tree.heading("Comment", text="Comment")
        tree.heading("Date", text="Date")
        tree.heading("Time", text="Time")
        tree.heading("Paid", text="Paid")
        tree.heading("Method", text="Method")
        tree.heading("Amount", text="Amount")
        
        
        for item in tree.get_children():
            tree.delete(item)
            
        doc_id = current_user_id_var.get()
        booked_apps = show_doctor_booked_appointments(doc_id)
        
        for fname, lname, comment, date, time, apno, payment, method, amount in booked_apps:
            full_name = f"{fname} {lname}"
            if payment == 1:
                paid_status = "Paid"
            else:
                paid_status = "Unpaid"
            pay_method = method if method else "-"
            pay_amount = f"{amount}€" if amount else "-"
            tree.insert("", "end", values=(full_name, comment, date, time, paid_status, pay_method, pay_amount, apno))

    ttk.Button(schedule_frame, text="Booked Details", command=show_booked_details).grid(row=9, column=1, padx=5, pady=10)

    # Κουμπί στατηστικών
    def show_stats_popup():
        doc_id = current_user_id_var.get()
        stats = get_doctor_stats(doc_id)
        
        # Αν υπάρξει λάθος και επιστρέψει κενό 
        if not stats:
             messagebox.showinfo("Info", "No data available yet.")
             return

        msg = f"--- Financial Overview ---\n\n"
        msg += f"Total Appointments: {stats.get('total_appts', 0)}\n"
        msg += f"Total Revenue: {stats.get('total_revenue', 0)} €\n\n"
        msg += "Breakdown by Payment Method:\n"
        
        methods = stats.get('payment_methods', [])
        if methods:
            for method, count in methods:
                msg += f"  • {method}: {count} appointments\n"
        else:
            msg += "  No payments recorded yet.\n"
            
        messagebox.showinfo("Doctor Statistics", msg)

    ttk.Button(schedule_frame, text="Show Stats", command=show_stats_popup).grid(row=9, column=2, padx=5, pady=10)

    # Λίστα ραντεβού
    app_frame = ttk.LabelFrame(frame, text="Appointments View", padding=10)
    app_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Search Frame
    search_frame = ttk.Frame(app_frame)
    search_frame.pack(fill="x", pady=5)
    ttk.Label(search_frame, text="Search Date:").pack(side="left")
    ent_search_date = ttk.Entry(search_frame, width=15)
    ent_search_date.pack(side="left", padx=5)
    btn_search = ttk.Button(search_frame, text="Search")
    btn_search.pack(side="left")
    btn_clear = ttk.Button(search_frame, text="Clear")
    btn_clear.pack(side="left", padx=5)

    tree = ttk.Treeview(app_frame, columns=("Date", "Time", "Status", "ID"), show="headings", height=8, displaycolumns=("Date", "Time", "Status"))
    tree.heading("Date", text="Date")
    tree.heading("Time", text="Time")
    tree.heading("Status", text="Status")
    tree.pack(fill="both", expand=True)

    # Χρώμα κοκκινο ή πράσινο για αν κλεισμένα ή ελεύθερα ραντεβού
    tree.tag_configure("free", foreground="green")
    tree.tag_configure("booked", foreground="red")

    # Εμφάνιση  λεπτομερειών των ραντεβού με διπλό κλίκ
    def on_appointment_double_click(event):
        selected_item = tree.selection()
        if not selected_item:
            return
        
        # Λεπτομέρειες ραντεβου
        item = tree.item(selected_item)
        values = item['values']
        apno = values[7] 
        
        paid_status = values[4]
        pay_method = values[5]
        pay_amount = values[6]

        patient_data = show_patient(apno)
        if patient_data:
            p = patient_data[0]
            patid = p[2]
            
            # Παράθυρο για πληρωμή
            top = tk.Toplevel(frame)
            top.title("Appointment Details & Payment")
            top.geometry("400x500")
            
            reason = p[6] if len(p) > 6 and p[6] else "-"
            info = f"Name: {p[0]} {p[1]}\nAMKA: {p[2]}\nSex: {p[3]}\nAllergies: {p[4]}\nBirth Date: {p[5]}\nReason: {reason}"
            
            ttk.Label(top, text="Patient Information", font=("Verdana", 12, "bold")).pack(pady=10)
            ttk.Label(top, text=info, justify="left").pack(pady=5, padx=10)
            
            ttk.Separator(top, orient='horizontal').pack(fill='x', pady=10)
            
            ttk.Label(top, text="Payment Processing", font=("Verdana", 12, "bold")).pack(pady=5)
            status_text = f"Current Status: {paid_status}"
            if paid_status == "Paid":
                status_text += f" ({pay_method}, {pay_amount})"
            
            lbl_color = "green" if paid_status == "Paid" else "red"
            ttk.Label(top, text=status_text, foreground=lbl_color, font=("Verdana", 10)).pack(pady=2)
            pay_frame = ttk.Frame(top)
            pay_frame.pack(pady=5)
            
            ttk.Label(pay_frame, text="Method:").grid(row=0, column=0, padx=5, pady=5)
            combo_method = ttk.Combobox(pay_frame, values=["Cash", "Card"], state="readonly", width=10)
            combo_method.grid(row=0, column=1, padx=5, pady=5)
            combo_method.set("Cash")
            
            ttk.Label(pay_frame, text="Amount (€):").grid(row=1, column=0, padx=5, pady=5)
            ent_amount = ttk.Entry(pay_frame, width=12)
            ent_amount.grid(row=1, column=1, padx=5, pady=5)
            
            def save_payment():
                try:
                    amt = float(ent_amount.get())
                    method = combo_method.get()
                    if add_bill(apno, patid, method, amt):
                        messagebox.showinfo("Success", "Payment saved!", parent=top)
                        top.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to save payment.", parent=top)
                except ValueError:
                    messagebox.showerror("Error", "Invalid Amount", parent=top)
            
            ttk.Button(top, text="Save Payment", command=save_payment).pack(pady=15)
        else:
            messagebox.showinfo("Info", "No patient details found for this appointment.")

    tree.bind("<Double-1>", on_appointment_double_click)

    #Επαναφέρει την προβολή στο γενικό πρόγραμμα
    def refresh_appointments():
        tree["displaycolumns"] = "#all"
        tree["columns"] = ("Date", "Time", "Status", "ID")
        tree["displaycolumns"] = ("Date", "Time", "Status")
        tree.heading("Date", text="Date")
        tree.heading("Time", text="Time")
        tree.heading("Status", text="Status")

        for item in tree.get_children():
            tree.delete(item)
        
        doc_id = current_user_id_var.get()
        date_filter = ent_search_date.get().strip()
        apps = show_appointments(doc_id, only_free=False, date_filter=date_filter if date_filter else None)
        for date, time, avail, apno in apps:
            status = "Free" if avail == 1 else "Booked"
            tag = "free" if avail == 1 else "booked"
            tree.insert("", "end", values=(date, time, status, apno), tags=(tag,))
            
    btn_show_schedule.config(command=refresh_appointments)
    btn_search.config(command=refresh_appointments)
    
    def clear_view():
        ent_search_date.delete(0, tk.END)
        for item in tree.get_children():
            tree.delete(item)
    btn_clear.config(command=clear_view)

    ttk.Button(app_frame, text="Refresh View", command=refresh_appointments).pack(pady=5)
    ttk.Button(frame, text="Logout", command=lambda: home_frame.tkraise()).pack(pady=10)
    def start_mqtt():
        doc_id = current_user_id_var.get()
        broker = "broker.emqx.io"
        topic = f"clinic/doctor/{doc_id}/refresh"

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe(topic)
                print(f"MQTT: Connected and subscribed to {topic}")

        def on_message(client, userdata, msg):
            frame.after(0, refresh_appointments)

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        
        try:
            client.connect(broker, 1883, 60)
            client.loop_start()
            
            # Κόβει την σύνδεση όταν γίνει Logout ή κλείσει η εφαρμογή
            def cleanup(event):
                client.loop_stop()
                client.disconnect()
            frame.bind("<Destroy>", cleanup)
            
        except Exception as e:
            print(f"MQTT Connection Error: {e}")

    start_mqtt()

    return frame