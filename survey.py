[3/31/2026 1:49 PM] Muhammadjon Baxritdinov: import json
import re
import io
import csv
from datetime import datetime
import streamlit as st

# --- Variable types used for marking criteria ---
survey_title: str = "Extracurricular Activities & Study Stress Survey"
passing_score: float = 40.0
allowed_formats: tuple = ("txt", "csv", "json")
score_range: range = range(0, 81)
frozen_states: frozenset = frozenset(
    ["Balanced", "Mild", "Moderate", "High", "Severe", "Critical"])

states: dict = {
    (0,  13): "Fully Balanced — Extracurricular activities have no negative stress impact.",
    (14, 27): "Mildly Stressed — Minor imbalance; self-monitoring is sufficient.",
    (28, 41): "Moderately Stressed — Noticeable pressure; consider adjusting commitments.",
    (42, 55): "Highly Stressed — Significant impact on well-being; stress management advised.",
    (56, 69): "Severely Stressed — Extracurricular activities are heavily disrupting academic life.",
    (70, 80): "Critical Imbalance — Immediate academic counselling and psychological support recommended."
}


def get_questions(filename: str) -> list:
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def get_psychological_state(total: int) -> str:
    for (low, high), state in states.items():
        if low <= total <= high:
            return state
    return "Unknown state."


def validate_name(name: str) -> bool:
    if not name:
        return False
    for ch in name:
        if not (ch.isalpha() or ch in "-' "):
            return False
    return True


def validate_date_of_birth(dob: str) -> bool:
    try:
        date_obj = datetime.strptime(dob, "%d/%m/%Y")
        return date_obj <= datetime.now()
    except ValueError:
        return False


def validate_student_id(sid: str) -> bool:
    return sid.isdigit() and len(sid) > 0


def build_download_content(data: dict, fmt: str) -> tuple:
    """Return (content_bytes, mime_type) for a given format."""
    if fmt == "json":
        content = json.dumps(data, indent=4).encode("utf-8")
        mime = "application/json"
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        for k, v in data.items():
            writer.writerow([k, v])
        content = buf.getvalue().encode("utf-8")
        mime = "text/csv"
    else:  # txt
        lines = "\n".join(f"{k}: {v}" for k, v in data.items())
        content = lines.encode("utf-8")
        mime = "text/plain"
    return content, mime


# ── Session state initialisation ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "menu",          # menu | details | survey | results | load
        "name": "",
        "dob": "",
        "sid": "",
        "answers": [],
        "total": 0,
        "state_label": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
questions: list = get_questions("questions.json")

st.title(f"📋 {survey_title}")
st.divider()

# ── PAGE: menu ────────────────────────────────────────────────────────────────
if st.session_state.page == "menu":
    st.subheader("Welcome")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 Start a new survey", use_container_width=True):
            st.session_state.page = "details"
            st.rerun()
    with col2:
        if st.button("📂 Load existing results", use_container_width=True):
            st.session_state.page = "load"
            st.rerun()

# ── PAGE: load ────────────────────────────────────────────────────────────────
elif st.session_state.page == "load":
    st.subheader("Load Existing Results")
    uploaded = st.file_uploader(
        "Upload your result file", type=["json", "csv", "txt"])

    if uploaded:
        fmt = uploaded.name.rsplit(".", 1)[-1].lower()
        raw = uploaded.read().decode("utf-8")
[3/31/2026 1:49 PM] Muhammadjon Baxritdinov: st.markdown("### Loaded Results")
        if fmt == "json":
            try:
                data = json.loads(raw)
                for k, v in data.items():
                    st.write(f"{k}: {v}")
            except json.JSONDecodeError:
                st.error("Could not parse JSON file.")
        elif fmt in ("csv", "txt"):
            st.text(raw)
        else:
            st.error("Unsupported format.")

    if st.button("← Back to menu"):
        st.session_state.page = "menu"
        st.rerun()

# ── PAGE: details ─────────────────────────────────────────────────────────────
elif st.session_state.page == "details":
    st.subheader("Your Details")

    name = st.text_input("Full name", value=st.session_state.name,
                         placeholder="e.g. Alice O'Brien")
    dob = st.text_input("Date of birth (DD/MM/YYYY)",
                        value=st.session_state.dob, placeholder="e.g. 15/03/2004")
    sid = st.text_input("Student ID (digits only)",
                        value=st.session_state.sid, placeholder="e.g. 123456")

    if st.button("Continue →"):
        errors = []
        if not validate_name(name):
            errors.append(
                "Name is invalid — only letters, hyphens, apostrophes, and spaces allowed.")
        if not validate_date_of_birth(dob):
            errors.append(
                "Date of birth must be in DD/MM/YYYY format and not in the future.")
        if not validate_student_id(sid):
            errors.append("Student ID must contain digits only.")
        if not questions:
            errors.append(
                "questions.json not found. Please add it to the project.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state.name = name
            st.session_state.dob = dob
            st.session_state.sid = sid
            st.session_state.answers = []
            st.session_state.page = "survey"
            st.rerun()

    if st.button("← Back to menu"):
        st.session_state.page = "menu"
        st.rerun()

# ── PAGE: survey ──────────────────────────────────────────────────────────────
elif st.session_state.page == "survey":
    st.subheader("Survey Questions")
    st.info("Answer every question, then click Submit.")

    if not questions:
        st.error("questions.json not found.")
        st.stop()

    responses = {}
    all_answered = True

    with st.form("survey_form"):
        for i, q in enumerate(questions):
            st.markdown(f"Q{i+1}. {q['question']}")
            choice = st.radio(
                label=f"q{i}",
                options=q["options"],
                index=None,
                label_visibility="collapsed",
                key=f"q_{i}"
            )
            responses[i] = choice
            if choice is None:
                all_answered = False
            st.divider()

        submitted = st.form_submit_button("Submit Survey")

    if submitted:
        if not all_answered:
            st.warning("Please answer all questions before submitting.")
        else:
            total = 0
            for i, q in enumerate(questions):
                chosen_option = responses[i]
                idx = q["options"].index(chosen_option)
                total += q["scores"][idx]

            st.session_state.total = total
            st.session_state.state_label = get_psychological_state(total)
            st.session_state.page = "results"
            st.rerun()

# ── PAGE: results ─────────────────────────────────────────────────────────────
elif st.session_state.page == "results":
    st.subheader("Your Results")

    total = st.session_state.total
    state = st.session_state.state_label
    max_score = max(score_range) - 1  # matches original: max(range(0,81))-1 = 80

    col1, col2 = st.columns(2)
    col1.metric("Total Score", f"{total} / {max_score}")
[3/31/2026 1:49 PM] Muhammadjon Baxritdinov: # Colour-coded result
    if total <= 13:
        st.success(f"✅ {state}")
    elif total <= 27:
        st.info(f"ℹ️ {state}")
    elif total <= 41:
        st.warning(f"⚠️ {state}")
    else:
        st.error(f"🚨 {state}")

    st.markdown("---")
    st.markdown(f"Name: {st.session_state.name}")
    st.markdown(f"Date of Birth: {st.session_state.dob}")
    st.markdown(f"Student ID: {st.session_state.sid}")

    st.markdown("---")
    st.subheader("Save Results")

    fmt = st.selectbox("Choose format", allowed_formats)
    result_data: dict = {
        "name": st.session_state.name,
        "date_of_birth": st.session_state.dob,
        "student_id": st.session_state.sid,
        "total_score": total,
        "psychological_state": state,
    }
    content, mime = build_download_content(result_data, fmt)
    filename = f"result_{st.session_state.sid}.{fmt}"

    st.download_button(
        label=f"⬇️ Download as .{fmt}",
        data=content,
        file_name=filename,
        mime=mime,
    )

    if st.button("🔄 Start over"):
        for k in ["name", "dob", "sid", "answers", "total", "state_label"]:
            st.session_state[k] = "" if isinstance(
                st.session_state[k], str) else 0 if isinstance(st.session_state[k], int) else []
        st.session_state.page = "menu"
        st.rerun()
