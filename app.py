import streamlit as st
import json
import os
import tempfile

from src.parsers.ats_parser import parse as parse_ats
from src.parsers.resume_parser import parse_resume
from src.parsers.csv_parser import parse_csv
from src.parsers.recruiter_notes_parser import parse_notes
from src.parsers.github_parser import parse_github
from src.parsers.linkedin_parser import parse_linkedin

from src.normalizers.normalizer import normalize_profile
from src.merger import merge
from src.validator import validate
from src.projector import project
from src.database import (
    init_db, save_candidate, get_all_candidates,
    get_candidate_by_id, delete_candidate, clear_all_candidates, get_stats
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Eightfold · Talent Intelligence Platform",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Typography & base ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Page background ───────────────────────────────────────────────── */
.stApp { background: #F1F5F9; }
.block-container { padding: 1.5rem 2.5rem 3rem; max-width: 1400px; }

/* ── Top navigation bar ────────────────────────────────────────────── */
.portal-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #0F172A;
    color: #F8FAFC;
    padding: 0 2rem;
    height: 56px;
    margin: -1.5rem -2.5rem 1.5rem;
    border-bottom: 3px solid #2563EB;
}
.portal-nav .brand {
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #FFFFFF;
}
.portal-nav .brand span { color: #60A5FA; }
.portal-nav .nav-meta {
    font-size: 0.78rem;
    color: #94A3B8;
    letter-spacing: 0.02em;
}

/* ── Section headings ──────────────────────────────────────────────── */
.section-title {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748B;
    margin: 1.2rem 0 0.5rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid #E2E8F0;
}
.page-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 0.15rem;
}
.page-subtitle {
    font-size: 0.83rem;
    color: #64748B;
    margin-bottom: 1.2rem;
}

/* ── Cards ─────────────────────────────────────────────────────────── */
.card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.card-sm {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    height: 100%;
}
.card-sm.selected {
    border-color: #2563EB;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.15);
}
.candidate-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #0F172A;
    margin-bottom: 0.25rem;
}
.candidate-meta {
    font-size: 0.76rem;
    color: #64748B;
    margin-bottom: 0.6rem;
    line-height: 1.5;
}
.candidate-id {
    font-size: 0.68rem;
    color: #94A3B8;
    font-family: 'SFMono-Regular', Consolas, monospace;
    word-break: break-all;
    margin-bottom: 0.7rem;
}

/* ── Badges / pills ────────────────────────────────────────────────── */
.badge-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 0.75rem; }
.badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    border-radius: 4px;
    padding: 2px 8px;
    letter-spacing: 0.02em;
}
.badge-blue  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.badge-green { background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }
.badge-purple{ background: #FAF5FF; color: #6B21A8; border: 1px solid #E9D5FF; }
.badge-gray  { background: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; }

/* ── Stat tiles ────────────────────────────────────────────────────── */
.stat-tile {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    text-align: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.1;
}
.stat-label {
    font-size: 0.72rem;
    color: #64748B;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.2rem;
}

/* ── Confidence bar ────────────────────────────────────────────────── */
.conf-bar-wrap { margin: 0.4rem 0; }
.conf-label {
    font-size: 0.72rem;
    color: #475569;
    display: flex;
    justify-content: space-between;
    margin-bottom: 3px;
}
.conf-bar-bg {
    background: #E2E8F0;
    border-radius: 100px;
    height: 6px;
    overflow: hidden;
}
.conf-bar-fill {
    height: 100%;
    border-radius: 100px;
    background: linear-gradient(90deg, #2563EB, #60A5FA);
}

/* ── Detail panel header ────────────────────────────────────────────── */
.detail-header {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #2563EB;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.detail-header .dh-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0F172A;
}
.detail-header .dh-meta {
    font-size: 0.76rem;
    color: #64748B;
    margin-top: 0.2rem;
    font-family: 'SFMono-Regular', Consolas, monospace;
}

/* ── Info row (contact/links) ──────────────────────────────────────── */
.info-row { margin-bottom: 0.5rem; }
.info-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.info-value {
    font-size: 0.85rem;
    color: #1E293B;
    margin-top: 1px;
    word-break: break-all;
}

/* ── Skill chip ─────────────────────────────────────────────────────── */
.skill-chip {
    display: inline-block;
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 0.76rem;
    color: #334155;
    margin: 3px 3px 0 0;
    font-weight: 500;
}
.skill-conf {
    font-size: 0.68rem;
    color: #94A3B8;
    display: block;
    text-align: center;
    margin-top: 1px;
}

/* ── Timeline (experience/education) ─────────────────────────────── */
.timeline-item {
    border-left: 2px solid #E2E8F0;
    padding-left: 1rem;
    margin-bottom: 1.25rem;
    position: relative;
}
.timeline-item::before {
    content: '';
    position: absolute;
    left: -5px;
    top: 5px;
    width: 8px;
    height: 8px;
    background: #2563EB;
    border-radius: 50%;
}
.timeline-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: #0F172A;
}
.timeline-sub {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 2px;
}
.timeline-date {
    font-size: 0.72rem;
    color: #94A3B8;
    font-family: monospace;
    margin-top: 2px;
}
.timeline-body {
    font-size: 0.8rem;
    color: #475569;
    margin-top: 0.4rem;
    line-height: 1.6;
}

/* ── Input panel ────────────────────────────────────────────────────── */
.input-panel {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* ── Streamlit overrides ─────────────────────────────────────────── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    font-size: 0.83rem !important;
}
.stButton > button[kind="primary"] {
    background: #2563EB !important;
    border: none !important;
    color: #FFFFFF !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1D4ED8 !important;
}
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    color: #374151 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #94A3B8 !important;
    background: #F8FAFC !important;
}
div[data-testid="stMetricValue"] {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    color: #0F172A !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    color: #64748B !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.stProgress > div > div { background-color: #2563EB !important; border-radius: 100px !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #E2E8F0;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: #64748B !important;
    padding: 0.55rem 1.1rem !important;
    border-radius: 0 !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #2563EB !important;
    border-bottom: 2px solid #2563EB !important;
    font-weight: 600 !important;
}
.stTextInput > div > div > input, .stFileUploader {
    border-radius: 6px !important;
    font-size: 0.83rem !important;
}
.stAlert {
    border-radius: 6px !important;
    font-size: 0.82rem !important;
}
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
hr { border-color: #E2E8F0 !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "github_url_val" not in st.session_state:
    st.session_state.github_url_val = ""
if "linkedin_url_val" not in st.session_state:
    st.session_state.linkedin_url_val = ""
if "candidate_history" not in st.session_state:
    st.session_state.candidate_history = []
if "db_selected_id" not in st.session_state:
    st.session_state.db_selected_id = None
if "input_reset_counter" not in st.session_state:
    # Incremented each time the user clicks "New Candidate" to force
    # file-uploader widgets to reset (they key off this counter).
    st.session_state.input_reset_counter = 0

init_db()


# ── Helpers ────────────────────────────────────────────────────────────────────
def save_temp_file(uploaded_file):
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


def conf_bar(label, value_pct):
    return f"""
    <div class="conf-bar-wrap">
        <div class="conf-label"><span>{label}</span><span>{value_pct}%</span></div>
        <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{value_pct}%"></div></div>
    </div>"""


def render_candidate_dashboard(final_profile, projected_profile, sources_count, candidate_key="current"):
    tab1, tab2, tab3, tab4 = st.tabs([
        "Profile Overview", "Projected Output", "Canonical Record", "Quality Audit"
    ])

    with tab1:
        # ── Top metrics row
        m1, m2, m3, m4 = st.columns(4)
        loc = final_profile.get("location")
        loc_str = f"{loc['city']}, {loc['country']}" if loc and loc.get("city") else "—"
        m1.metric("Full Name", final_profile.get("full_name") or "—")
        m2.metric("Location", loc_str)
        m3.metric("Experience", f"{final_profile.get('years_experience', 0) or 0} yrs")
        m4.metric("Data Sources", sources_count)
        st.markdown("")

        left, right = st.columns([1, 1])

        with left:
            st.markdown('<p class="section-title">Contact Information</p>', unsafe_allow_html=True)
            emails = final_profile.get("emails", [])
            phones = final_profile.get("phones", [])
            links  = final_profile.get("links") or {}

            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem">
                <div class="info-row">
                    <div class="info-label">Email</div>
                    <div class="info-value">{emails[0] if emails else "—"}</div>
                </div>
                <div class="info-row" style="margin-top:0.6rem">
                    <div class="info-label">Phone</div>
                    <div class="info-value">{phones[0] if phones else "—"}</div>
                </div>
                <div class="info-row" style="margin-top:0.6rem">
                    <div class="info-label">LinkedIn</div>
                    <div class="info-value">{links.get("linkedin") or "—"}</div>
                </div>
                <div class="info-row" style="margin-top:0.6rem">
                    <div class="info-label">GitHub</div>
                    <div class="info-value">{links.get("github") or "—"}</div>
                </div>
                <div class="info-row" style="margin-top:0.6rem">
                    <div class="info-label">Portfolio</div>
                    <div class="info-value">{links.get("portfolio") or "—"}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<p class="section-title">Ingestion Quality</p>', unsafe_allow_html=True)
            conf = final_profile.get("overall_confidence", 0.0)
            conf_pct = int(conf * 100)
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.2rem">
                {conf_bar("Overall Confidence", conf_pct)}
                <div style="margin-top:0.75rem;font-size:0.78rem;color:#64748B">
                    <span style="margin-right:1.5rem"><strong>{sources_count}</strong> sources ingested</span>
                    <span><strong>{len(final_profile.get("skills",[]))}</strong> skills detected</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with right:
            st.markdown('<p class="section-title">Skills</p>', unsafe_allow_html=True)
            skills = final_profile.get("skills", [])
            if skills:
                chips = "".join(
                    f'<div class="skill-chip">{s["name"]}'
                    f'<span class="skill-conf">{int(s["confidence"]*100)}%</span></div>'
                    for s in skills
                )
                st.markdown(f'<div class="card" style="padding:0.9rem 1.1rem">{chips}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="card"><span style="color:#94A3B8;font-size:0.82rem">No skills detected</span></div>',
                            unsafe_allow_html=True)

        st.markdown("")

        exp_col, edu_col = st.columns(2)

        with exp_col:
            st.markdown('<p class="section-title">Work Experience</p>', unsafe_allow_html=True)
            experience = final_profile.get("experience", [])
            if experience:
                items = ""
                for e in experience:
                    start = e.get("start") or ""
                    end   = e.get("end") or "Present"
                    summary = (e.get("summary") or "").replace("\n", "<br>")
                    items += f"""
                    <div class="timeline-item">
                        <div class="timeline-title">{e.get("title") or "—"}</div>
                        <div class="timeline-sub">{e.get("company") or "—"}</div>
                        <div class="timeline-date">{start} — {end}</div>
                        {"<div class='timeline-body'>" + summary + "</div>" if summary else ""}
                    </div>"""
                st.markdown(f'<div class="card">{items}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card"><span style="color:#94A3B8;font-size:0.82rem">No experience records found</span></div>',
                            unsafe_allow_html=True)

        with edu_col:
            st.markdown('<p class="section-title">Education</p>', unsafe_allow_html=True)
            education = final_profile.get("education", [])
            if education:
                items = ""
                for ed in education:
                    end_yr = str(ed.get("end_year")) if ed.get("end_year") else "—"
                    items += f"""
                    <div class="timeline-item">
                        <div class="timeline-title">{ed.get("degree") or "—"}</div>
                        <div class="timeline-sub">{ed.get("field") or "—"}</div>
                        <div class="timeline-sub">{ed.get("institution") or "—"}</div>
                        <div class="timeline-date">Graduated {end_yr}</div>
                    </div>"""
                st.markdown(f'<div class="card">{items}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card"><span style="color:#94A3B8;font-size:0.82rem">No education records found</span></div>',
                            unsafe_allow_html=True)

    with tab2:
        st.json(projected_profile)
        st.download_button(
            "Download Projected Profile",
            data=json.dumps(projected_profile, indent=2),
            file_name=f"candidate_{final_profile.get('candidate_id','profile')}.json",
            mime="application/json",
            key=f"dl_proj_{candidate_key}",
        )

    with tab3:
        st.json(final_profile)
        st.download_button(
            "Download Canonical Record",
            data=json.dumps(final_profile, indent=2),
            file_name=f"canonical_{final_profile.get('candidate_id','profile')}.json",
            mime="application/json",
            key=f"dl_canon_{candidate_key}",
        )

    with tab4:
        st.markdown('<p class="section-title">Quality Checks</p>', unsafe_allow_html=True)
        errors = validate(final_profile)
        if errors:
            for err in errors:
                st.warning(err)
        else:
            st.success("All quality checks passed.")

        st.markdown('<p class="section-title">Provenance Log</p>', unsafe_allow_html=True)
        prov = final_profile.get("provenance", [])
        if prov:
            st.dataframe(prov, use_container_width=True)
        else:
            st.caption("No provenance data.")


# ── Navigation bar ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="portal-nav">
    <div class="brand">EIGHTFOLD <span>/ Talent Intelligence Platform</span></div>
    <div class="nav-meta">Recruiter Portal &nbsp;&middot;&nbsp; Candidate Ingestion</div>
</div>
""", unsafe_allow_html=True)

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown('<p class="page-title">Candidate Ingestion</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="page-subtitle">Ingest candidate data from multiple sources, normalize '
    'and reconcile fields, and generate a structured profile. '
    'Process one candidate at a time — results persist across sessions.</p>',
    unsafe_allow_html=True
)

# ══════════════════════════════════════════════════════════════════════
# Layout: Input panel (left) | Results panel (right)
# ══════════════════════════════════════════════════════════════════════
input_col, result_col = st.columns([1, 1.6], gap="large")

with input_col:
    st.markdown('<div class="input-panel">', unsafe_allow_html=True)

    st.markdown('<p class="section-title">Structured Sources</p>', unsafe_allow_html=True)
    _rc = st.session_state.input_reset_counter
    ats_file = st.file_uploader("ATS JSON Export", type=["json"], label_visibility="visible",
                                 key=f"ats_{_rc}")
    csv_file = st.file_uploader("Recruiter CSV Export", type=["csv"], key=f"csv_{_rc}")

    st.markdown('<p class="section-title">Unstructured Sources</p>', unsafe_allow_html=True)
    resume_file = st.file_uploader("Resume  (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"],
                                    key=f"resume_{_rc}")
    notes_file  = st.file_uploader("Recruiter Notes (.txt)", type=["txt"], key=f"notes_{_rc}")

    st.markdown('<p class="section-title">Online Profiles</p>', unsafe_allow_html=True)
    github_url   = st.text_input("GitHub Profile URL",
                                  value=st.session_state.github_url_val,
                                  placeholder="https://github.com/username",
                                  key=f"gh_{_rc}")
    st.session_state.github_url_val = github_url
    linkedin_url = st.text_input("LinkedIn Profile URL",
                                  value=st.session_state.linkedin_url_val,
                                  placeholder="https://linkedin.com/in/username",
                                  key=f"li_{_rc}")
    st.session_state.linkedin_url_val = linkedin_url

    st.markdown('<p class="section-title">Output Configuration</p>', unsafe_allow_html=True)
    _rc = st.session_state.input_reset_counter
    config_file = st.file_uploader("Custom Projection Config (optional)", type=["json"],
                                    key=f"cfg_{_rc}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    # ── New Candidate / Reset button ─────────────────────────────────────────
    if st.button("⟳  New Candidate (Reset Inputs)", use_container_width=True, type="secondary",
                 help="Clears all uploaded files and URL fields so you can process a new candidate without contaminating state."):
        st.session_state.github_url_val   = ""
        st.session_state.linkedin_url_val = ""
        st.session_state.input_reset_counter += 1
        st.rerun()

    history_count = len(st.session_state.candidate_history)
    if history_count:
        st.caption(f"{history_count} candidate(s) processed this session")
        if st.button("Clear Session History", use_container_width=True):
            st.session_state.candidate_history = []
            st.rerun()


# ── Results column ─────────────────────────────────────────────────────────────
with result_col:
    process_btn = st.button("Run Ingestion Pipeline", type="primary", use_container_width=True)

    if process_btn:
        parsed_profiles = []
        resume_name = resume_file.name if resume_file else "Unknown"

        # ATS
        if ats_file:
            try:
                raw = ats_file.getvalue().decode("utf-8")
                # Strip JS-style comments (// and /* */) which are not valid JSON
                import re as _re
                cleaned = _re.sub(r'//[^\n]*', '', raw)          # // line comments
                cleaned = _re.sub(r'/\*.*?\*/', '', cleaned, flags=_re.DOTALL)  # /* block */
                # Remove trailing commas before } or ]
                cleaned = _re.sub(r',\s*([}\]])', r'\1', cleaned)
                ats_data = json.loads(cleaned)
                parsed_profiles.append(normalize_profile(parse_ats(ats_data)))
                st.toast("ATS data parsed")
            except Exception as e:
                st.error(f"ATS parse failed: {e}")

        # CSV
        if csv_file:
            try:
                tmp = save_temp_file(csv_file)
                parsed_profiles.append(normalize_profile(parse_csv(tmp)))
                os.remove(tmp)
                st.toast("Recruiter CSV parsed")
            except Exception as e:
                st.error(f"CSV parse failed: {e}")

        # Resume
        resume_profile = None
        if resume_file:
            try:
                tmp = save_temp_file(resume_file)
                resume_profile = normalize_profile(parse_resume(tmp))
                parsed_profiles.append(resume_profile)
                os.remove(tmp)
                st.toast("Resume parsed")

                if resume_profile and resume_profile.get("links") and resume_profile["links"].get("value"):
                    r_links = resume_profile["links"]["value"]
                    has_new = False
                    if r_links.get("github") and not st.session_state.github_url_val.strip():
                        gv = r_links["github"]
                        st.session_state.github_url_val = gv if gv.startswith("http") else "https://" + gv
                        has_new = True
                    if r_links.get("linkedin") and not st.session_state.linkedin_url_val.strip():
                        lv = r_links["linkedin"]
                        st.session_state.linkedin_url_val = lv if lv.startswith("http") else "https://" + lv
                        has_new = True
                    if has_new:
                        st.rerun()
            except Exception as e:
                st.error(f"Resume parse failed: {e}")

        # Notes
        if notes_file:
            try:
                tmp = save_temp_file(notes_file)
                parsed_profiles.append(normalize_profile(parse_notes(tmp)))
                os.remove(tmp)
                st.toast("Recruiter notes parsed")
            except Exception as e:
                st.error(f"Notes parse failed: {e}")

        # Auto-discover links from resume
        github_to_parse  = github_url
        linkedin_to_parse = linkedin_url
        if resume_profile and resume_profile.get("links") and resume_profile["links"].get("value"):
            r_links = resume_profile["links"]["value"]
            if not github_to_parse and r_links.get("github"):
                github_to_parse = r_links["github"]
                if not github_to_parse.startswith("http"):
                    github_to_parse = "https://" + github_to_parse
                st.info(f"Auto-detected GitHub from resume: {github_to_parse}")
            if not linkedin_to_parse and r_links.get("linkedin"):
                linkedin_to_parse = r_links["linkedin"]
                if not linkedin_to_parse.startswith("http"):
                    linkedin_to_parse = "https://" + linkedin_to_parse
                st.info(f"Auto-detected LinkedIn from resume: {linkedin_to_parse}")

        # GitHub
        if github_to_parse:
            try:
                parsed_profiles.append(normalize_profile(parse_github(github_to_parse)))
                st.toast("GitHub profile parsed")
            except Exception as e:
                st.error(f"GitHub parse failed: {e}")

        # LinkedIn
        if linkedin_to_parse:
            try:
                parsed_profiles.append(normalize_profile(parse_linkedin(linkedin_to_parse)))
                st.toast("LinkedIn profile parsed")
            except Exception as e:
                st.error(f"LinkedIn parse failed: {e}")

        if parsed_profiles:
            with st.spinner("Reconciling candidate data..."):
                final_profile = merge(parsed_profiles)

                config = None
                if config_file:
                    try:
                        config = json.loads(config_file.getvalue().decode("utf-8"))
                    except Exception as e:
                        st.error(f"Invalid config: {e}")
                if not config:
                    cfg_path = "configs/default.json"
                    if os.path.exists(cfg_path):
                        with open(cfg_path) as f:
                            config = json.load(f)
                    else:
                        config = {"fields": [{"path": "full_name"}, {"path": "emails"}, {"path": "skills"}]}

                try:
                    projected = project(final_profile, config)
                except Exception as e:
                    st.error(f"Projection failed: {e}")
                    projected = None

            if projected:
                st.session_state.candidate_history.append({
                    "resume_name": resume_name,
                    "final_profile": final_profile,
                    "projected_profile": projected,
                    "sources_count": len(parsed_profiles),
                })
                try:
                    save_candidate(resume_name, final_profile, projected, len(parsed_profiles))
                except Exception as db_err:
                    st.warning(f"Database save warning: {db_err}")

                name = final_profile.get("full_name") or "Unknown"
                cid  = final_profile.get("candidate_id", "")
                st.markdown(f"""
                <div class="detail-header">
                    <div class="dh-name">{name}</div>
                    <div class="dh-meta">
                        Candidate ID: {cid}&nbsp;&nbsp;|&nbsp;&nbsp;
                        Sources: {len(parsed_profiles)}&nbsp;&nbsp;|&nbsp;&nbsp;
                        Confidence: {int(final_profile.get("overall_confidence",0)*100)}%
                    </div>
                </div>""", unsafe_allow_html=True)

                render_candidate_dashboard(final_profile, projected, len(parsed_profiles), "current")

                # Reset URL fields AND file uploaders for the next candidate
                st.session_state.github_url_val   = ""
                st.session_state.linkedin_url_val = ""
                st.session_state.input_reset_counter += 1
        else:
            st.warning("Please provide at least one input source to begin processing.")


# ══════════════════════════════════════════════════════════════════════
# Bottom tabs: Session History  |  Database
# ══════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
history = st.session_state.candidate_history

tab_session, tab_db = st.tabs(["Session History", "Candidate Database"])

# ── Session History ────────────────────────────────────────────────────────────
with tab_session:
    if not history:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem;color:#94A3B8;font-size:0.85rem">
            No candidates processed in this session yet.<br>
            Upload a resume and run the ingestion pipeline above.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="section-title">{len(history)} Candidate(s) — Current Session</p>',
                    unsafe_allow_html=True)

        rows = []
        for entry in history:
            fp = entry["final_profile"]
            emails = fp.get("emails", [])
            loc = fp.get("location")
            rows.append({
                "Name":          fp.get("full_name") or "—",
                "Email":         emails[0] if emails else "—",
                "Location":      f"{loc['city']}, {loc['country']}" if loc and loc.get("city") else "—",
                "Experience":    f"{fp.get('years_experience') or 0} yrs",
                "Skills":        len(fp.get("skills", [])),
                "Confidence":    f"{int(fp.get('overall_confidence',0)*100)}%",
                "Sources":       entry["sources_count"],
                "Resume File":   entry["resume_name"],
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        st.download_button(
            "Download All Profiles (JSON)",
            data=json.dumps([e["projected_profile"] for e in history], indent=2),
            file_name="session_candidates.json",
            mime="application/json",
            key="dl_all_session",
        )

        st.markdown('<p class="section-title">Individual Profiles</p>', unsafe_allow_html=True)
        for i, entry in enumerate(reversed(history)):
            fp   = entry["final_profile"]
            name = fp.get("full_name") or "Unknown"
            conf = int(fp.get("overall_confidence", 0) * 100)
            label = f"#{len(history)-i}  ·  {name}  ·  {entry['resume_name']}  ·  {conf}% confidence"
            with st.expander(label, expanded=(i == 0)):
                render_candidate_dashboard(
                    fp, entry["projected_profile"], entry["sources_count"],
                    candidate_key=f"hist_{len(history)-i}",
                )

# ── Candidate Database ─────────────────────────────────────────────────────────
with tab_db:
    from src.database import DB_PATH

    # Header row
    hdr_left, hdr_right = st.columns([4, 1])
    with hdr_left:
        st.markdown('<p class="page-title" style="font-size:1.1rem">Candidate Database</p>',
                    unsafe_allow_html=True)
        st.markdown(f'<p class="page-subtitle" style="font-size:0.75rem">SQLite · {DB_PATH}</p>',
                    unsafe_allow_html=True)
    with hdr_right:
        if st.button("Clear Database", type="secondary", key="clear_db", use_container_width=True):
            clear_all_candidates()
            st.session_state.db_selected_id = None
            st.success("Database cleared.")
            st.rerun()

    # Aggregate stats
    stats = get_stats()
    if stats.get("total"):
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.markdown(f'<div class="stat-tile"><div class="stat-value">{stats["total"]}</div><div class="stat-label">Total Candidates</div></div>', unsafe_allow_html=True)
        sc2.markdown(f'<div class="stat-tile"><div class="stat-value">{int((stats["avg_confidence"] or 0)*100)}%</div><div class="stat-label">Avg Confidence</div></div>', unsafe_allow_html=True)
        sc3.markdown(f'<div class="stat-tile"><div class="stat-value">{stats["avg_skills"] or 0}</div><div class="stat-label">Avg Skills</div></div>', unsafe_allow_html=True)
        sc4.markdown(f'<div class="stat-tile"><div class="stat-value">{stats["avg_experience"] or 0}</div><div class="stat-label">Avg Experience (yrs)</div></div>', unsafe_allow_html=True)
        st.markdown("")

    st.markdown("<hr>", unsafe_allow_html=True)

    db_rows = get_all_candidates()

    if not db_rows:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem;color:#94A3B8;font-size:0.85rem">
            No candidates stored in the database.<br>
            Process a resume above to begin building your candidate pool.
        </div>""", unsafe_allow_html=True)
    else:
        # Bulk download
        all_projected = []
        for r in db_rows:
            full = get_candidate_by_id(r["id"])
            if full:
                all_projected.append(full["projected_profile"])
        st.download_button(
            "Download All Profiles (JSON)",
            data=json.dumps(all_projected, indent=2),
            file_name="database_candidates.json",
            mime="application/json",
            key="dl_all_db",
        )

        st.markdown(f'<p class="section-title">{len(db_rows)} Stored Candidate(s) — Click a row to view the full profile</p>',
                    unsafe_allow_html=True)

        # ── Candidate card grid ───────────────────────────────────────────────
        COLS = 3
        for row_start in range(0, len(db_rows), COLS):
            cols = st.columns(COLS, gap="medium")
            for ci, r in enumerate(db_rows[row_start: row_start + COLS]):
                is_sel   = (st.session_state.db_selected_id == r["id"])
                conf_pct = int((r["overall_confidence"] or 0) * 100)
                loc_str  = r["location"] or "—"
                name_str = r["full_name"] or "Unknown"
                cid_str  = r["candidate_id"] or ""
                date_str = (r["processed_at"] or "")[:10]

                border = "border-color:#2563EB;box-shadow:0 0 0 2px rgba(37,99,235,0.18);" if is_sel else ""

                with cols[ci]:
                    st.markdown(f"""
                    <div class="card-sm {'selected' if is_sel else ''}" style="{border}">
                        <div class="candidate-name">{name_str}</div>
                        <div class="candidate-meta">
                            {loc_str}<br>Processed {date_str}
                        </div>
                        <div class="badge-row">
                            <span class="badge badge-blue">{conf_pct}% confidence</span>
                            <span class="badge badge-purple">{r["skills_count"]} skills</span>
                            <span class="badge badge-green">{r["years_experience"] or 0} yrs</span>
                        </div>
                        <div class="candidate-id">ID: {cid_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_label = "Deselect" if is_sel else "View Profile"
                    btn_type  = "primary" if is_sel else "secondary"
                    if st.button(btn_label, key=f"dbcard_{r['id']}",
                                 use_container_width=True, type=btn_type):
                        st.session_state.db_selected_id = None if is_sel else r["id"]
                        st.rerun()

        # ── Detail panel ─────────────────────────────────────────────────────
        sel_id = st.session_state.db_selected_id
        if sel_id:
            rec = get_candidate_by_id(sel_id)
            if rec:
                st.markdown("<hr>", unsafe_allow_html=True)
                fp   = rec["final_profile"]
                name = fp.get("full_name") or "Unknown"
                cid  = fp.get("candidate_id", "")

                dh_l, dh_r = st.columns([5, 1])
                with dh_l:
                    st.markdown(f"""
                    <div class="detail-header">
                        <div class="dh-name">{name}</div>
                        <div class="dh-meta">
                            Candidate ID: {cid}&nbsp;&nbsp;|&nbsp;&nbsp;
                            Resume: {rec["resume_name"]}&nbsp;&nbsp;|&nbsp;&nbsp;
                            Ingested: {(rec.get("processed_at") or "")[:10]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with dh_r:
                    if st.button("Close", key="db_close", use_container_width=True):
                        st.session_state.db_selected_id = None
                        st.rerun()

                render_candidate_dashboard(
                    fp, rec["projected_profile"], rec["sources_count"],
                    candidate_key=f"db_{sel_id}",
                )

                st.markdown("")
                if st.button(
                    f"Remove {name} from Database",
                    key=f"del_{sel_id}", type="secondary"
                ):
                    delete_candidate(sel_id)
                    st.session_state.db_selected_id = None
                    st.success(f"'{name}' removed from the database.")
                    st.rerun()
