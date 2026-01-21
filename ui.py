import streamlit as st
import requests
import time
import os
from datetime import datetime

# ======================
# CONFIG
# ======================

API_BASE = os.getenv(
    "API_BASE_URL",
    "https://soapify-backend.onrender.com"
)

st.set_page_config(
    page_title="SOAPify",
    layout="wide",
)

# ======================
# SESSION STATE
# ======================

st.session_state.setdefault("token", None)
st.session_state.setdefault("current_note_id", None)
st.session_state.setdefault("editing", False)
st.session_state.setdefault("edited_note", "")

# ======================
# HELPERS
# ======================

def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state.token}"
    }

# ======================
# SIDEBAR
# ======================

st.sidebar.title("SOAPify")
st.sidebar.caption("AI Clinical Scribe")

if st.session_state.token:
    st.sidebar.success("Logged in")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
else:
    st.sidebar.warning("Not logged in")

st.sidebar.markdown("---")

# ======================
# DASHBOARD (SIDEBAR)
# ======================

if st.session_state.token and not st.session_state.current_note_id:
    st.sidebar.markdown("### 📋 Dashboard")

    try:
        dash_res = requests.get(
            f"{API_BASE}/api/v1/notes/DashboardData",
            headers=auth_headers(),
            timeout=5,
        )

        if dash_res.status_code == 200:
            notes = dash_res.json()

            if not notes:
                st.sidebar.info("No notes yet")
            else:
                for n in notes[:10]:
                    created_at = n.get("created_at")

                    try:
                        time_str = datetime.fromisoformat(created_at).strftime("%H:%M")
                    except Exception:
                        time_str = "--:--"

                    label = (
                        f"SOAP #{n['soap_number']} | "
                        f"PID:{n['patient_id']} | "
                        f"{n['patient_name']} | "
                        f"{time_str} | "
                        f"{n['status']}"
                    )

                    if st.sidebar.button(label, key=f"note_{n['note_id']}"):
                        st.session_state.current_note_id = n["note_id"]
                        st.session_state.editing = False
                        st.rerun()
        else:
            st.sidebar.error("Failed to load dashboard")

    except requests.exceptions.RequestException:
        st.sidebar.error("Backend not reachable")

# ======================
# LOGIN / SIGNUP
# ======================

if not st.session_state.token:
    st.title("SOAPify")
    st.subheader("Secure AI-Powered Clinical Scribe")

    tab_login, tab_signup = st.tabs(["🔐 Login", "🆕 Sign Up"])

    # ---------- LOGIN ----------
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.form_submit_button("Login"):
                try:
                    res = requests.post(
                        f"{API_BASE}/api/v1/auth/login",
                        data={
                            "username": email,
                            "password": password,
                        },
                        timeout=10,
                    )

                    if res.status_code == 200:
                        st.session_state.token = res.json()["access_token"]
                        st.success("Login successful")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

                except requests.exceptions.RequestException:
                    st.error("Backend not reachable")

    # ---------- SIGNUP ----------
    with tab_signup:
        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            specialization = st.text_input("Specialization (optional)")

            if st.form_submit_button("Create Account"):
                if not full_name or not email or not password:
                    st.warning("All required fields must be filled")
                else:
                    try:
                        res = requests.post(
                            f"{API_BASE}/api/v1/auth/register",
                            json={
                                "full_name": full_name,
                                "email": email,
                                "password": password,
                                "specialization": specialization,
                            },
                            timeout=10,
                        )

                        if res.status_code in (200, 201):
                            st.success("Account created. Please login.")
                        else:
                            st.error(res.json().get("detail", "Signup failed"))

                    except requests.exceptions.RequestException:
                        st.error("Backend not reachable")

    st.stop()

# ======================
# MAIN DASHBOARD
# ======================

st.title("🩺 SOAP Note Generator")

with st.form("generate_form"):
    col1, col2 = st.columns(2)
    patient_name = col1.text_input("Patient Name")
    age = col2.number_input("Age", min_value=0, max_value=120)
    transcript = st.text_area("Clinical Transcript", height=250)

    submit_generate = st.form_submit_button(" Generate SOAP Note")

if submit_generate:
    if not patient_name or not transcript:
        st.warning("Patient name and transcript required")
    else:
        res = requests.post(
            f"{API_BASE}/api/v1/notes/Generate",
            json={
                "patient_name": patient_name,
                "age": age,
                "transcript_text": transcript,
            },
            headers=auth_headers(),
        )

        if res.status_code == 200:
            st.session_state.current_note_id = res.json()["id"]
            st.session_state.editing = False
            st.success("⏳ Processing started...")
            st.rerun()
        else:
            st.error("Failed to submit transcript")

# ======================
# STATUS + RESULT
# ======================

if st.session_state.current_note_id:
    note_id = st.session_state.current_note_id

    res = requests.get(
        f"{API_BASE}/api/v1/notes/Status/{note_id}",
        headers=auth_headers(),
    )

    if res.status_code == 200:
        data = res.json()
        status = data["status"]
        content = data["content"]

        if status == "PROCESSING":
            st.warning("⏳ Status: PROCESSING")
            time.sleep(4)
            st.rerun()

        elif status == "COMPLETED":
            st.success("✅ Status: COMPLETED")

            if not st.session_state.editing:
                st.text_area("SOAP Note", content, height=400)

                if st.button("✏️ Edit SOAP Note"):
                    st.session_state.editing = True
                    st.session_state.edited_note = content
                    st.rerun()
            else:
                edited = st.text_area(
                    "Edit SOAP Note",
                    st.session_state.edited_note,
                    height=400,
                )

                col_a, col_b = st.columns(2)

                if col_a.button("💾 Save Changes"):
                    update_res = requests.put(
                        f"{API_BASE}/api/v1/notes/Update/{note_id}",
                        json={"updated_content": edited},
                        headers=auth_headers(),
                    )

                    if update_res.status_code == 200:
                        st.session_state.editing = False
                        st.success("Saved successfully")
                        st.rerun()
                    else:
                        st.error("Failed to save")

                if col_b.button("❌ Cancel"):
                    st.session_state.editing = False
                    st.rerun()

        elif status == "FAILED":
            st.error("❌ Generation failed")
