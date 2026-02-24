import time
import math
import os

import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from hospital_system import EnhancedHospitalSystem, Treatment, Staff
from database import (
    init_database,
    load_hospital_from_db,
    save_hospital_to_db,
    load_appointments_from_db,
    save_appointments_to_db,
    get_next_appointment_id
)

# =========================
#   PERSISTENCE SETTINGS
# =========================

# Initialize database on first run
if not os.path.exists("hospital.db"):
    init_database()


def load_hospital_from_disk():
    try:
        return load_hospital_from_db(EnhancedHospitalSystem)
    except Exception as e:
        print("Error loading hospital data:", e)
        return EnhancedHospitalSystem()


def save_hospital_to_disk(hospital):
    try:
        save_hospital_to_db(hospital)
    except Exception as e:
        print("Error saving hospital data:", e)


def load_appointments_from_disk():
    try:
        return load_appointments_from_db()
    except Exception as e:
        print("Error loading appointments:", e)
        return []


def save_appointments_to_disk(appointments):
    try:
        save_appointments_to_db(appointments)
    except Exception as e:
        print("Error saving appointments:", e)


# =========================
#   INIT BACKEND IN SESSION
# =========================
if "hospital" not in st.session_state:
    st.session_state.hospital = load_hospital_from_disk()

hospital: EnhancedHospitalSystem = st.session_state.hospital

if "appointments" not in st.session_state:
    st.session_state.appointments = load_appointments_from_disk()

st.set_page_config(
    page_title="Hospital Priority Management",
    page_icon="🏥",
    layout="wide"
)

# =========================
#   DARK MODE + BASIC THEME
# =========================
dark_mode = st.sidebar.checkbox("🌙 Dark mode", value=False)

if dark_mode:
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #0f172a !important;
            color: #e5e7eb !important;
        }
        .metric-card {
            background: linear-gradient(135deg, #1f2937, #111827);
            padding: 18px 16px;
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.6);
            border: 1px solid #374151;
        }
        .metric-title {
            font-size: 14px;
            color: #9ca3af;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 26px;
            font-weight: 700;
            color: #f9fafb;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        .metric-card {
            background: linear-gradient(135deg, #eff6ff, #e0f2fe);
            padding: 18px 16px;
            border-radius: 16px;
            box-shadow: 0 4px 14px rgba(15,23,42,0.18);
            border: 1px solid #bfdbfe;
        }
        .metric-title {
            font-size: 14px;
            color: #1f2937;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 26px;
            font-weight: 700;
            color: #0f172a;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# =========================
#   HELPER FUNCTIONS
# =========================
def get_all_patients():
    patients = []

    def inorder(node):
        if not node:
            return
        inorder(node.left)
        patients.append(node.patient)
        inorder(node.right)

    inorder(hospital.avl_tree.root)
    return patients


def get_patient_df():
    pts = get_all_patients()
    if not pts:
        return pd.DataFrame()
    # Sort by priority: severity 1 (Critical) first, then 2 (Moderate), then 3 (Less critical)
    pts_sorted = sorted(pts)  # Uses Patient.__lt__ which compares by severity first
    data = [{
        "ID": p.patient_id,
        "Name": p.name,
        "Age": p.age,
        "Gender": p.gender,
        "Severity": p.severity,
        "Room": p.room_id,
        "Disease": p.disease,
        "Arrival Time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.arrival_time)),
    } for p in pts_sorted]
    return pd.DataFrame(data)


def get_treatments_df():
    treatments = hospital.treatment_log.list_data()
    if not treatments:
        return pd.DataFrame()
    data = []
    for t in treatments:
        patient = hospital.avl_tree.find_patient(t.patient_id)
        pname = patient.name if patient else "Unknown"
        staff_name = "Unknown"
        for s in hospital.staff_manager.staff:
            if s.staff_id == t.staff_id:
                staff_name = f"{s.name} ({s.role})"
                break
        data.append({
            "Treatment ID": t.treatment_id,
            "Patient ID": t.patient_id,
            "Patient Name": pname,
            "Staff ID": t.staff_id,
            "Staff": staff_name,
            "Details": t.treatment_details,
            "Date": t.date,
        })
    return pd.DataFrame(data)


def get_staff_df():
    staff = hospital.staff_manager.list_staff()
    if not staff:
        return pd.DataFrame()
    data = [{
        "Staff ID": s.staff_id,
        "Name": s.name,
        "Role": s.role
    } for s in staff]
    return pd.DataFrame(data)


def compute_bill(patient):
    """Simple billing logic based on room type, severity, and stay duration."""
    if not patient.room_id:
        room_type = "General"
    else:
        room_type = hospital.room_manager.rooms[patient.room_id].room_type

    now = time.time()
    seconds = max(0, now - patient.arrival_time)
    days = math.ceil(seconds / (24 * 3600)) or 1

    room_base = {
        "General": 1000,
        "ICU": 3000,
        "Surgery": 5000
    }.get(room_type, 1000)

    severity_charge = {
        1: 2000,
        2: 1000,
        3: 500
    }.get(patient.severity, 500)

    treatment_count = len(patient.treatments)
    treatment_charge = treatment_count * 500

    total_room = room_base * days
    total = total_room + severity_charge + treatment_charge

    return {
        "room_type": room_type,
        "days": days,
        "room_base": room_base,
        "total_room": total_room,
        "severity_charge": severity_charge,
        "treatment_count": treatment_count,
        "treatment_charge": treatment_charge,
        "grand_total": total
    }


def generate_discharge_pdf(patient, bill_info):
    """Generate a simple discharge summary PDF and return (filename, bytes)."""
    filename = f"discharge_patient_{patient.patient_id}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Hospital Discharge Summary")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Patient ID: {patient.patient_id}")
    y -= 20
    c.drawString(50, y, f"Name: {patient.name}")
    y -= 20
    c.drawString(50, y, f"Age: {patient.age}   Gender: {patient.gender}")
    y -= 20
    c.drawString(50, y, f"Disease: {patient.disease or 'Not specified'}")
    y -= 20
    c.drawString(50, y, f"Severity: {patient.severity}")
    y -= 20
    c.drawString(50, y, f"Room: {patient.room_id or 'N/A'}")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Billing Details:")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(60, y, f"Room Type: {bill_info['room_type']}")
    y -= 20
    c.drawString(60, y, f"Days Stayed: {bill_info['days']}  (Base per day: {bill_info['room_base']})")
    y -= 20
    c.drawString(60, y, f"Room Charge: {bill_info['total_room']}")
    y -= 20
    c.drawString(60, y, f"Severity Charge: {bill_info['severity_charge']}")
    y -= 20
    c.drawString(60, y, f"Treatments: {bill_info['treatment_count']} x 500 = {bill_info['treatment_charge']}")
    y -= 20
    c.drawString(60, y, f"Grand Total: {bill_info['grand_total']}")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Medical History:")
    y -= 20
    c.setFont("Helvetica", 10)
    if patient.history:
        for h in patient.history:
            if y < 80:
                c.showPage()
                y = height - 50
            c.drawString(60, y, f"- {h}")
            y -= 15
    else:
        c.drawString(60, y, "No history recorded.")
        y -= 20

    c.showPage()
    c.save()

    with open(filename, "rb") as f:
        pdf_bytes = f.read()
    return filename, pdf_bytes


def discharge_patient_with_bill(pid: int):
    patient = hospital.avl_tree.find_patient(pid)
    if not patient:
        return False, "Patient not found.", None, None

    bill_info = compute_bill(patient)
    filename, pdf_bytes = generate_discharge_pdf(patient, bill_info)

    # release resources
    if patient.room_id:
        room = hospital.room_manager.rooms[patient.room_id]
        room.is_vacant = True

    hospital.avl_tree.delete_patient(pid)
    hospital.priority_queue.remove_patient(pid)
    save_hospital_to_disk(hospital)

    msg = f"Patient {patient.name} discharged from room {patient.room_id}."
    return True, msg, filename, pdf_bytes


def predict_severity(symptoms: list, age: int):
    """Simple rule-based 'AI' helper to suggest severity."""
    critical_keywords = ["chest pain", "unconscious", "severe bleeding", "breathing difficulty", "stroke"]
    moderate_keywords = ["fever", "vomiting", "fracture", "moderate pain"]
    score = 0

    text = " ".join(symptoms).lower()
    if any(k in text for k in critical_keywords):
        score += 2
    if any(k in text for k in moderate_keywords):
        score += 1
    if age >= 65:
        score += 1

    if score >= 2:
        return 1  # Critical
    elif score == 1:
        return 2  # Moderate
    else:
        return 3  # Mild


# =========================
#   SIDEBAR NAV
# =========================
st.sidebar.title("🏥 Hospital System")

page = st.sidebar.radio(
    "Go to",
    [
        "🧑‍⚕️ Patients",
        "🚑 Priority Queue",
        "📅 Appointments",
        "👩‍💼 Staff",
        "💉 Treatments"
    ]
)

# =========================
#   PAGES
# =========================

# ---------- PATIENTS ----------
if page == "🧑‍⚕️ Patients":
    st.title("🧑‍⚕️ Patient Management")

    tab_add, tab_list, tab_search, tab_discharge = st.tabs(
        ["➕ Add Patient", "📋 List & Filter", "🔍 Search / Details", "🚪 Discharge & Billing"]
    )

    # ---- Add Patient ----
    with tab_add:
        st.subheader("➕ Add New Patient")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0, step=1, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        with col2:
            severity = st.selectbox(
                "Severity (1=Critical, 2=Moderate, 3=Mild)",
                [1, 2, 3],
                index=1,
            )
            disease = st.text_input("Disease (optional)")

        with st.expander("🧠 Need help selecting severity? (AI Helper)"):
            symptom_choices = [
                "Chest pain",
                "Breathing difficulty",
                "Unconscious",
                "Severe bleeding",
                "Fever",
                "Vomiting",
                "Fracture",
                "Moderate pain",
            ]
            selected_symptoms = st.multiselect("Select symptoms", symptom_choices)
            if st.button("Predict Severity"):
                if not selected_symptoms:
                    st.warning("Select at least one symptom.")
                else:
                    pred = predict_severity(selected_symptoms, age)
                    mapping = {1: "Critical (1)", 2: "Moderate (2)", 3: "Mild (3)"}
                    st.info(
                        f"Suggested severity: **{mapping[pred]}** "
                        "(you can set it manually above)."
                    )

        if st.button("Add Patient", type="primary"):
            if not name:
                st.error("Name is required.")
            else:
                success, msg = hospital.add_patient_record(
                    name, age, gender, severity, disease or None
                )
                if success:
                    save_hospital_to_disk(hospital)
                    st.success(msg)
                else:
                    st.error(msg)

    # ---- List & Filter ----
    with tab_list:
        st.subheader("📋 All Patients")

        df = get_patient_df()
        if df.empty:
            st.info("No patients found.")
        else:
            colf1, colf2, colf3 = st.columns([1, 1, 2])
            with colf1:
                sev_filter = st.multiselect(
                    "Filter by Severity", [1, 2, 3], default=[1, 2, 3]
                )
            with colf2:
                gender_filter = st.multiselect(
                    "Filter by Gender",
                    options=df["Gender"].unique().tolist(),
                    default=df["Gender"].unique().tolist(),
                )
            with colf3:
                name_search = st.text_input("Search by name (contains)")

            filtered_df = df[
                df["Severity"].isin(sev_filter) & df["Gender"].isin(gender_filter)
            ]
            if name_search.strip():
                filtered_df = filtered_df[
                    filtered_df["Name"].str.contains(
                        name_search, case=False, na=False
                    )
                ]
            
            # Ensure sorting by priority: Severity 1 (Critical) first, then 2, then 3
            # Lower severity number = higher priority
            filtered_df = filtered_df.sort_values(by="Severity", ascending=True)

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Filtered Patients CSV",
                data=csv,
                file_name="patients_filtered.csv",
                mime="text/csv",
            )

    # ---- Search / Details ----
    with tab_search:
        st.subheader("🔍 Search Patient")

        search_mode = st.radio("Search by", ["ID", "Name"], horizontal=True)

        if search_mode == "ID":
            pid = st.number_input("Enter Patient ID", min_value=1, step=1)
            if st.button("Search by ID"):
                patient = hospital.avl_tree.find_patient(pid)
                if patient:
                    st.success(f"Patient Found: {patient.name}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**ID:** {patient.patient_id}")
                        st.write(f"**Age:** {patient.age}")
                        st.write(f"**Gender:** {patient.gender}")
                        st.write(f"**Severity:** {patient.severity}")
                    with c2:
                        st.write(f"**Room:** {patient.room_id}")
                        st.write(
                            f"**Disease:** {patient.disease or 'Not specified'}"
                        )

                    st.markdown("**Medical History:**")
                    if patient.history:
                        for h in patient.history:
                            st.write(f"- {h}")
                    else:
                        st.write("No history recorded.")

                    st.markdown("**Treatments:**")
                    if patient.treatments:
                        for t in patient.treatments:
                            st.write(f"- {t}")
                    else:
                        st.write("No treatments recorded.")
                else:
                    st.error("Patient not found.")
        else:
            name_q = st.text_input("Enter patient name (full or partial)")
            if st.button("Search by Name"):
                pts = get_all_patients()
                matches = [
                    p
                    for p in pts
                    if name_q.strip().lower() in p.name.lower()
                ]
                if not matches:
                    st.error("No patients found with that name.")
                else:
                    st.success(f"Found {len(matches)} patient(s).")
                    # Sort matches by priority: Severity 1 (Critical) first
                    matches_sorted = sorted(matches)
                    data = [{
                        "ID": p.patient_id,
                        "Name": p.name,
                        "Age": p.age,
                        "Gender": p.gender,
                        "Severity": p.severity,
                        "Room": p.room_id,
                        "Disease": p.disease,
                    } for p in matches_sorted]
                    df_matches = pd.DataFrame(data)
                    # Ensure explicit sorting by Severity
                    df_matches = df_matches.sort_values(by="Severity", ascending=True)
                    st.dataframe(
                        df_matches, use_container_width=True, hide_index=True
                    )

    # ---- Discharge & Billing ----
    with tab_discharge:
        st.subheader("🚪 Discharge Patient & Generate Bill")
        pid_discharge = st.number_input(
            "Patient ID to Discharge", min_value=1, step=1
        )

        if st.button("Discharge & Generate PDF", type="primary"):
            success, msg, filename, pdf_bytes = discharge_patient_with_bill(
                pid_discharge
            )
            if success:
                st.success(msg)
                if pdf_bytes:
                    st.download_button(
                        "⬇️ Download Discharge Summary PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                    )
            else:
                st.error(msg)

# ---------- PRIORITY QUEUE ----------
elif page == "🚑 Priority Queue":
    st.title("🚑 Emergency Priority Queue")

    next_patient = hospital.priority_queue.get_next_patient()
    if next_patient:
        st.subheader("Next Patient for Treatment")
        st.markdown(
            f"""
            **ID:** {next_patient.patient_id}  
            **Name:** {next_patient.name}  
            **Age:** {next_patient.age}  
            **Gender:** {next_patient.gender}  
            **Severity:** {next_patient.severity}  
            **Room:** {next_patient.room_id}  
            **Disease:** {next_patient.disease or "Not specified"}  
            """
        )
    else:
        st.info("No patients in priority queue.")

    st.markdown("---")
    st.subheader("All Patients in Priority Order")

    heap_list = sorted(hospital.priority_queue.heap)
    if heap_list:
        data = [{
            "ID": p.patient_id,
            "Name": p.name,
            "Age": p.age,
            "Gender": p.gender,
            "Severity": p.severity,
            "Room": p.room_id,
            "Disease": p.disease,
        } for p in heap_list]
        df = pd.DataFrame(data)
        # Ensure explicit sorting by Severity (1=Critical first, then 2, then 3)
        df = df.sort_values(by="Severity", ascending=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Priority queue is empty.")

# ---------- APPOINTMENTS ----------
elif page == "📅 Appointments":
    st.title("📅 Doctor-wise Appointments")

    tab_new, tab_list = st.tabs(
        ["➕ Schedule Appointment", "📋 View Appointments"]
    )

    patients_df = get_patient_df()
    staff_df = get_staff_df()

    # ---- Schedule Appointment ----
    with tab_new:
        st.subheader("➕ Schedule New Appointment")

        if patients_df.empty or staff_df.empty:
            st.warning(
                "Need at least one patient and one staff (doctor) to schedule appointments."
            )
        else:
            patient_ids = patients_df["ID"].tolist()
            doctors = staff_df[
                staff_df["Role"].str.contains("doctor", case=False, na=False)
            ]

            if doctors.empty:
                st.warning(
                    "No doctor found in staff list. Add staff with role containing 'Doctor'."
                )
            else:
                col1, col2 = st.columns(2)
                with col1:
                    patient_id = st.selectbox("Select Patient ID", patient_ids)
                    doctor_name = st.selectbox(
                        "Select Doctor", doctors["Name"].tolist()
                    )
                with col2:
                    date_str = st.date_input("Appointment Date").strftime(
                        "%Y-%m-%d"
                    )
                    time_str = st.time_input("Appointment Time").strftime(
                        "%H:%M"
                    )

                if st.button("Schedule Appointment", type="primary"):
                    appt_id = get_next_appointment_id()
                    new_appointment = {
                        "id": appt_id,
                        "patient_id": patient_id,
                        "doctor": doctor_name,
                        "date": date_str,
                        "time": time_str,
                        "status": "Scheduled",
                    }
                    st.session_state.appointments.append(new_appointment)
                    save_appointments_to_disk(st.session_state.appointments)
                    st.success(
                        f"Appointment #{appt_id} scheduled for patient {patient_id} with Dr. {doctor_name}."
                    )

    # ---- View Appointments ----
    with tab_list:
        st.subheader("📋 All Appointments")

        appts = st.session_state.appointments
        if not appts:
            st.info("No appointments scheduled yet.")
        else:
            df_appt = pd.DataFrame(appts)
            st.dataframe(df_appt, use_container_width=True, hide_index=True)

# ---------- STAFF ----------
elif page == "👩‍💼 Staff":
    st.title("👩‍💼 Staff Management")

    tab_add_staff, tab_list_staff = st.tabs(
        ["➕ Add Staff", "📋 List Staff"]
    )

    with tab_add_staff:
        st.subheader("➕ Add New Staff Member")
        staff_id = st.text_input("Staff ID")
        name = st.text_input("Name")
        role = st.text_input("Role (e.g., Doctor, Nurse, Admin)")

        if st.button("Add Staff", type="primary"):
            if not (staff_id and name and role):
                st.error("All fields are required.")
            else:
                hospital.staff_manager.add_staff(Staff(staff_id, name, role))
                save_hospital_to_disk(hospital)
                st.success(f"Staff {name} added successfully!")

    with tab_list_staff:
        st.subheader("📋 Staff List")
        df_staff = get_staff_df()
        if df_staff.empty:
            st.info("No staff members added yet.")
        else:
            st.dataframe(df_staff, use_container_width=True, hide_index=True)

# ---------- TREATMENTS ----------
elif page == "💉 Treatments":
    st.title("💉 Treatment Records")

    tab_add_treat, tab_list_treat = st.tabs(
        ["➕ Add Treatment", "📋 View Treatments"]
    )

    with tab_add_treat:
        st.subheader("➕ Add Treatment")

        treatment_id = st.text_input("Treatment ID")
        patient_id = st.number_input("Patient ID", min_value=1, step=1)
        staff_id = st.text_input("Staff ID")
        details = st.text_area("Treatment Details")

        if st.button("Add Treatment", type="primary"):
            patient = hospital.avl_tree.find_patient(
                int(patient_id)
            ) if patient_id else None
            staff_exists = any(
                s.staff_id == staff_id for s in hospital.staff_manager.staff
            )

            if not treatment_id or not patient_id or not staff_id or not details:
                st.error("All fields are required.")
            elif not patient:
                st.error("Patient not found.")
            elif not staff_exists:
                st.error("Staff not found.")
            else:
                date = time.strftime("%Y-%m-%d")
                t = Treatment(
                    treatment_id, int(patient_id), staff_id, details, date
                )
                hospital.treatment_log.append(t)

                patient.add_history(
                    f"Treatment '{details}' performed on {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                patient.add_treatment(details)

                save_hospital_to_disk(hospital)
                st.success(
                    f"Treatment {treatment_id} added for patient {patient.name}."
                )

    with tab_list_treat:
        st.subheader("📋 All Treatment Records")
        df_treat = get_treatments_df()
        if df_treat.empty:
            st.info("No treatments recorded yet.")
        else:
            st.dataframe(df_treat, use_container_width=True, hide_index=True)