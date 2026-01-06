

A **desktop medical appointment management system** built with **Python, Tkinter, SQLite**, featuring **real-time updates** using **MQTT**.



---

## Features

### Doctor
- Set weekly schedule & appointment duration
- View available & booked appointments
- View patient details
- Register payments
- **Real-time appointment updates (MQTT)**

### Patient
- View available appointments
- Book appointments
- View personal appointments 

---
## Requirements

- Python 3.x    
- paho-mqtt (`pip install paho-mqtt`)
- ALL FILES must be in the same folder
### Installation
1. Open command prompt(cmd)

2. Clone the repository:

git clone https://github.com/GiakoubM/clinic-appointments.git \
cd clinic_appointments\
3. Create a virtual environment (recommended)\
python -m venv .venv

4. Activate the virtual environment

Windows:

.venv\Scripts\activate


Linux / Mac:

source .venv/bin/activate 

5.Install requirements\
pip install -r requirements.txt

6. Create the database\
   python create_database.py

7.Run the application\
python connect_window.py


## Screenshots

### Login Window
![Login](screenshots/login1.png)
### Doctor Login Window
![Login](screenshots/login_doc.png)
### Patient Login Window
![Login](screenshots/login_patient.png)
### Patient Register Window
![Patient Window](screenshots/patient_register.png)

### Doctor Dashboard
![Doctor Dashboard](screenshots/doc_dashboard.png)
### Doctor Booked Appointments
![Doctor Dashboard](screenshots/doctor_booked_appointments.png)
### Doctor Appointments Details
![Doctor Dashboard](screenshots/appointment_details.png)
### Doctor Schedule And Search fo Appointments
![Doctor Dashboard](screenshots/doc_schedule.png)
![Doctor Dashboard](screenshots/doc_search.png)
### Doctor Statistics and Payment Details
![Doctor Dashboard](screenshots/statistics.png)
![Doctor Dashboard](screenshots/unpaid.png) 
![Doctor Dashboard](screenshots/paid.png)

### Patient Book Appointment Window
![Patient Window](screenshots/patient_book_appointment.png)
![Patient Window](screenshots/patient_book_appointment2.png)
### Patient Cancel Appointment Window
![Patient Window](screenshots/patient_cancel_appointment.png)










