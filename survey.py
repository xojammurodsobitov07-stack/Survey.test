import json
import io
import csv
from datetime import datetime
import streamlit as st
 
# --- Variable types (marking criteria) ---
survey_title: str = "Extracurricular Activities & Study Stress Survey"
passing_score: float = 40.0
allowed_formats: tuple = ("txt", "csv", "json")
score_range: range = range(0, 81)
seen_ids: set = set()
frozen_states: frozenset = frozenset(["Balanced", "Mild", "Moderate", "High", "Severe", "Critical"])
is_saved: bool = False
max_score: int = 80
 
states: dict = {
    (0,  13): "Fully Balanced — No negative stress impact detected.",
    (14, 27): "Mildly Stressed — Minor imbalance; self-monitoring is sufficient.",
    (28, 41): "Moderately Stressed — Consider adjusting your commitments.",
    (42, 55): "Highly Stressed — Stress management support is advised.",
    (56, 69): "Severely Stressed — Extracurriculars are disrupting your academic life.",
    (70, 80): "Critical Imbalance — Immediate counselling is recommended."
}
 
 
def get_questions(filename: str) -> list:
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
 
 
def get_psychological_state(total: int) -> str:
    for (low, high), label in states.items():
        if low <= total <= high:
            return label
    return "Unknown state."
 
 
def validate_name(name: str) -> bool:
    if not name:
        return False
    for ch in name:                             # for loop — input validation
        if not (ch.isalpha() or ch in "-' "):
            return False
    return True
 
 
def validate_dob(dob: str) -> bool:
    parts: list = dob.split("/")
    i: int = 0
    while i < len(parts):                       # while loop — input validation
        if not parts[i].isdigit():
            return False
        i += 1
    try:
        return datetime.strptime(dob, "%d/%m/%Y") <= datetime.now()
    except ValueError:
        return False
 
 
def validate_student_id(sid: str) -> bool:
    return sid.isdigit() and len(sid) > 0
 
 
def build_download(data: dict, fmt: str) -> tuple:
    if fmt == "json":                           # if / elif / else
        content = json.dumps(data, indent=4).encode("utf-8")
        mime = "application/json"
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        for k, v in data.items():
            writer.writerow([k, v])
        content = buf.getvalue().encode("utf-8")
        mime = "text/csv"
    else:
        content = "\n".join(f"{k}: {v}" for k, v in data.items()).encode("utf-8")
        mime = "text/plain"
    return content, mime
 
 
# --- Session state ---
def init_state():
    defaults = {"page": "menu", "name": "", "dob": "", "sid": "", "total": 0, "state_label": ""}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
 
 
init_state()
questions: list = get_questions("questions.json")
st.title(f"📋 {survey_title}")
st.divider()
 
# ── MENU ──────────────────────────────────────────────────────────────────────
if st.session_state.page == "menu":
    st.subheader("Welcome")
    st.write("This survey measures how extracurricular activities affect your study stress.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Start a new survey", use_container_width=True):
            st.session_state.page = "details"
            st.rerun()
    with col2:
        if st.button("📂 Load existing results", use_container_width=True):
            st.session_state.page = "load"
            st.rerun()
 
# ── LOAD ──────────────────────────────────────────────────────────────────────
elif st.session_state.page == "load":
    st.subheader("Load Existing Results")
    uploaded = st.file_uploader("Upload your result file", type=["json", "csv", "txt"])
    if uploaded:
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        raw = uploaded.read().decode("utf-8")
        st.markdown("### Results")
        if ext == "json":
            try:
                for k, v in json.loads(raw).items():
                    st.write(f"**{k}:** {v}")
            except json.JSONDecodeError:
                st.error("Could not parse JSON file.")
        else:
            st.text(raw)
    if st.button("← Back"):
        st.session_state.page = "menu"
        st.rerun()
 
# ── DETAILS ───────────────────────────────────────────────────────────────────
elif st.session_state.page == "details":
    st.subheader("Your Details")
    name = st.text_input("Full name", placeholder="e.g. Alice O'Brien")
    dob  = st.text_input("Date of birth (DD/MM/YYYY)", placeholder="e.g. 15/03/2004")
    sid  = st.text_input("Student ID (digits only)", placeholder="e.g. 00012345")
 
    if st.button("Continue →"):
        errors: list = []
        if not validate_name(name):
            errors.append("Name invalid — only letters, hyphens, apostrophes and spaces allowed.")
        if not validate_dob(dob):
            errors.append("Date of birth must be DD/MM/YYYY and not in the future.")
        if not validate_student_id(sid):
            errors.append("Student ID must contain digits only.")
        if not questions:
            errors.append("questions.json not found. Place it in the same folder.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state.name = name
            st.session_state.dob  = dob
            st.session_state.sid  = sid
            seen_ids.add(sid)
            st.session_state.page = "survey"
            st.rerun()
 
    if st.button("← Back"):
        st.session_state.page = "menu"
        st.rerun()
 
# ── SURVEY ────────────────────────────────────────────────────────────────────
elif st.session_state.page == "survey":
    st.subheader("Survey Questions")
    st.info("Answer every question then click **Submit**.")
    if not questions:
        st.error("questions.json not found.")
        st.stop()
 
    responses: dict = {}
    with st.form("survey_form"):
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            responses[i] = st.radio("", options=q["options"], index=None,
                                    label_visibility="collapsed", key=f"q_{i}")
            st.divider()
        submitted = st.form_submit_button("Submit Survey")
 
    if submitted:
        if None in responses.values():
            st.warning("Please answer all questions before submitting.")
        else:
            total: int = 0
            for i, q in enumerate(questions):
                total += q["scores"][q["options"].index(responses[i])]
            st.session_state.total       = total
            st.session_state.state_label = get_psychological_state(total)
            st.session_state.page        = "results"
            st.rerun()
 
# ── RESULTS ───────────────────────────────────────────────────────────────────
elif st.session_state.page == "results":
    st.subheader("Your Results")
    total = st.session_state.total
    state = st.session_state.state_label
 
    st.metric("Total Score", f"{total} / {max_score}")
 
    if total <= 13:
        st.success(state)
    elif total <= 27:
        st.info(state)
    elif total <= 41:
        st.warning(state)
    else:
        st.error(state)
 
    st.markdown("---")
    st.write(f"**Name:** {st.session_state.name}")
    st.write(f"**Date of Birth:** {st.session_state.dob}")
    st.write(f"**Student ID:** {st.session_state.sid}")
    st.markdown("---")
 
    st.subheader("Save Results")
    fmt = st.selectbox("Choose format", allowed_formats)
    result_data: dict = {
        "name": st.session_state.name,
        "date_of_birth": st.session_state.dob,
        "student_id": st.session_state.sid,
        "total_score": total,
        "psychological_state": state
    }
    content, mime = build_download(result_data, fmt)
    st.download_button(f"⬇ Download as .{fmt}", data=content,
                       file_name=f"result_{st.session_state.sid}.{fmt}", mime=mime)
 
    if st.button("🔄 Start over"):
        for k in ["name", "dob", "sid", "state_label"]:
            st.session_state[k] = ""
        st.session_state.total = 0
        st.session_state.page  = "menu"
        st.rerun()
