import sqlite3
import json
import os
from datetime import datetime

DB_FILE = "hospital.db"


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_database():
    """Initialize the database with required tables."""
    from hospital_system import Room
    
    conn = get_connection()
    cursor = conn.cursor()

    # Patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            severity INTEGER NOT NULL,
            arrival_time REAL NOT NULL,
            disease TEXT,
            room_id TEXT,
            history TEXT,
            treatments TEXT,
            current_id INTEGER
        )
    """)

    # Staff table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            staff_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Treatments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treatments (
            treatment_id TEXT PRIMARY KEY,
            patient_id INTEGER NOT NULL,
            staff_id TEXT NOT NULL,
            treatment_details TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)

    # Appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Scheduled'
        )
    """)

    # Rooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY,
            is_vacant INTEGER NOT NULL DEFAULT 1,
            room_type TEXT NOT NULL DEFAULT 'General',
            condition TEXT NOT NULL DEFAULT 'Clean'
        )
    """)

    # System state table (for current_id tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
    """)

    conn.commit()
    
    # Initialize default rooms if database is empty
    cursor.execute("SELECT COUNT(*) as count FROM rooms")
    if cursor.fetchone()['count'] == 0:
        default_rooms = [
            ("Reception", False, "General", "Clean"),
            ("Room 1", True, "General", "Clean"),
            ("Room 2", True, "ICU", "Clean"),
            ("Room 3", True, "Surgery", "Clean"),
            ("Room 4", True, "General", "Clean"),
            ("Power and Monitoring Hub", False, "General", "Clean")
        ]
        for room_id, is_vacant, room_type, condition in default_rooms:
            cursor.execute(
                "INSERT INTO rooms (room_id, is_vacant, room_type, condition) VALUES (?, ?, ?, ?)",
                (room_id, 1 if is_vacant else 0, room_type, condition)
            )
        conn.commit()
    
    conn.close()


def save_hospital_to_db(hospital):
    """Save the entire hospital system state to database."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Clear existing data
        cursor.execute("DELETE FROM patients")
        cursor.execute("DELETE FROM treatments")
        cursor.execute("DELETE FROM staff")
        cursor.execute("DELETE FROM rooms")
        cursor.execute("DELETE FROM system_state")

        # Save current_id
        cursor.execute(
            "INSERT INTO system_state (key, value) VALUES (?, ?)",
            ("current_id", hospital.current_id)
        )

        # Save rooms
        for room_id, room in hospital.room_manager.rooms.items():
            cursor.execute(
                "INSERT INTO rooms (room_id, is_vacant, room_type, condition) VALUES (?, ?, ?, ?)",
                (room_id, 1 if room.is_vacant else 0, room.room_type, room.condition)
            )

        # Save patients (from AVL tree)
        def save_patient_recursive(node):
            if node:
                patient = node.patient
                cursor.execute(
                    """INSERT INTO patients 
                       (patient_id, name, age, gender, severity, arrival_time, disease, room_id, history, treatments)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        patient.patient_id,
                        patient.name,
                        patient.age,
                        patient.gender,
                        patient.severity,
                        patient.arrival_time,
                        patient.disease,
                        patient.room_id,
                        json.dumps(patient.history),
                        json.dumps(patient.treatments)
                    )
                )
                save_patient_recursive(node.left)
                save_patient_recursive(node.right)

        save_patient_recursive(hospital.avl_tree.root)

        # Save staff
        for staff in hospital.staff_manager.staff:
            cursor.execute(
                "INSERT INTO staff (staff_id, name, role) VALUES (?, ?, ?)",
                (staff.staff_id, staff.name, staff.role)
            )

        # Save treatments
        current = hospital.treatment_log.head
        while current:
            treatment = current.data
            cursor.execute(
                "INSERT INTO treatments (treatment_id, patient_id, staff_id, treatment_details, date) VALUES (?, ?, ?, ?, ?)",
                (
                    treatment.treatment_id,
                    treatment.patient_id,
                    treatment.staff_id,
                    treatment.treatment_details,
                    treatment.date
                )
            )
            current = current.next

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving hospital data: {e}")
        return False
    finally:
        conn.close()


def load_hospital_from_db(hospital_system_class):
    """Load hospital system from database and reconstruct all data structures."""
    from hospital_system import Patient, Staff, Treatment, Room

    if not os.path.exists(DB_FILE):
        return hospital_system_class()

    conn = get_connection()
    cursor = conn.cursor()

    hospital = hospital_system_class()

    try:
        # Load current_id
        cursor.execute("SELECT value FROM system_state WHERE key = ?", ("current_id",))
        row = cursor.fetchone()
        if row:
            hospital.current_id = row[0]

        # Load rooms
        cursor.execute("SELECT room_id, is_vacant, room_type, condition FROM rooms")
        for row in cursor.fetchall():
            room = Room(row[0], bool(row[1]), row[2])
            room.condition = row[3]
            hospital.room_manager.rooms[row[0]] = room

        # If no rooms exist, initialize default rooms
        if not hospital.room_manager.rooms:
            hospital.room_manager.initialize_rooms()
            save_hospital_to_db(hospital)
            return hospital

        # Load patients
        cursor.execute("SELECT * FROM patients")
        patients_to_add = []
        for row in cursor.fetchall():
            patient = Patient(
                row['patient_id'],
                row['name'],
                row['age'],
                row['gender'],
                row['severity'],
                row['arrival_time'],
                row['disease']
            )
            patient.room_id = row['room_id']
            patient.history = json.loads(row['history']) if row['history'] else []
            patient.treatments = json.loads(row['treatments']) if row['treatments'] else []

            hospital.avl_tree.insert(patient)
            patients_to_add.append(patient)
        
        # Add all patients to priority queue, then rebuild heap to ensure proper structure
        for patient in patients_to_add:
            hospital.priority_queue.heap.append(patient)
        hospital.priority_queue.rebuild_heap()

        # Load staff
        cursor.execute("SELECT * FROM staff")
        for row in cursor.fetchall():
            staff = Staff(row['staff_id'], row['name'], row['role'])
            hospital.staff_manager.add_staff(staff)

        # Load treatments
        cursor.execute("SELECT * FROM treatments ORDER BY date")
        for row in cursor.fetchall():
            treatment = Treatment(
                row['treatment_id'],
                row['patient_id'],
                row['staff_id'],
                row['treatment_details'],
                row['date']
            )
            hospital.treatment_log.append(treatment)

        return hospital
    except Exception as e:
        print(f"Error loading hospital data: {e}")
        return hospital_system_class()
    finally:
        conn.close()


def save_appointments_to_db(appointments):
    """Save appointments list to database."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Clear existing appointments
        cursor.execute("DELETE FROM appointments")

        # Insert all appointments
        for appt in appointments:
            appt_id = appt.get('id')
            if appt_id:
                cursor.execute(
                    """INSERT INTO appointments (id, patient_id, doctor, date, time, status)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        appt_id,
                        appt['patient_id'],
                        appt['doctor'],
                        appt['date'],
                        appt['time'],
                        appt.get('status', 'Scheduled')
                    )
                )
            else:
                # Let SQLite auto-generate ID
                cursor.execute(
                    """INSERT INTO appointments (patient_id, doctor, date, time, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        appt['patient_id'],
                        appt['doctor'],
                        appt['date'],
                        appt['time'],
                        appt.get('status', 'Scheduled')
                    )
                )
                # Update the appointment dict with the generated ID
                appt['id'] = cursor.lastrowid

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving appointments: {e}")
        return False
    finally:
        conn.close()


def get_next_appointment_id():
    """Get the next available appointment ID."""
    if not os.path.exists(DB_FILE):
        return 1
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT MAX(id) as max_id FROM appointments")
        row = cursor.fetchone()
        max_id = row['max_id'] if row['max_id'] else 0
        return max_id + 1
    except Exception as e:
        print(f"Error getting next appointment ID: {e}")
        return 1
    finally:
        conn.close()


def load_appointments_from_db():
    """Load appointments list from database."""
    if not os.path.exists(DB_FILE):
        return []

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM appointments ORDER BY date, time")
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                'id': row['id'],
                'patient_id': row['patient_id'],
                'doctor': row['doctor'],
                'date': row['date'],
                'time': row['time'],
                'status': row['status']
            })
        return appointments
    except Exception as e:
        print(f"Error loading appointments: {e}")
        return []
    finally:
        conn.close()

