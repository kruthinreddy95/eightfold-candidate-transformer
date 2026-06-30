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
from src.validator import validate, validate_projected
from src.projector import project

# Set page style
st.set_page_config(
    page_title="Eightfold Candidate Data Transformer",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Multi-Source Candidate Data Transformer")
st.markdown("""
This interactive UI ingests candidate information from multiple heterogeneous sources, normalizes, resolves conflicts by confidence scores, and projects the final output based on runtime configuration.
""")

# Setup two-column layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 Input Sources")

    # Structured Sources
    st.markdown("### Structured Sources")
    ats_file = st.file_uploader("Upload ATS JSON file", type=["json"])
    csv_file = st.file_uploader("Upload Recruiter CSV Export", type=["csv"])

    # Unstructured Sources
    st.markdown("### Unstructured Sources")
    resume_file = st.file_uploader("Upload Resume (DOCX, PDF, TXT)", type=["docx", "pdf", "txt"])
    notes_file = st.file_uploader("Upload Recruiter Notes (.txt)", type=["txt"])

    # Social Profiles
    st.markdown("### Social & Public URLs")
    github_url = st.text_input("GitHub Profile URL", placeholder="https://github.com/username")
    linkedin_url = st.text_input("LinkedIn Profile URL", placeholder="https://linkedin.com/in/username")

    # Runtime Projection Config
    st.markdown("### Output Configuration")
    config_file = st.file_uploader("Upload custom projection config JSON (optional)", type=["json"])

with col2:
    st.subheader("📊 Output Results")
    
    generate_btn = st.button("⚡ Generate Canonical Profile", type="primary", use_container_width=True)
    
    if generate_btn:
        parsed_profiles = []
        
        # Helper to write streamlit uploads to temporary files
        def save_temp_file(uploaded_file):
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                return tmp.name

        # Process Structured ATS
        if ats_file:
            try:
                ats_data = json.loads(ats_file.getvalue().decode("utf-8"))
                ats_profile = normalize_profile(parse_ats(ats_data))
                parsed_profiles.append(ats_profile)
                st.success("✅ ATS JSON parsed successfully")
            except Exception as e:
                st.error(f"❌ Failed to parse ATS JSON: {e}")

        # Process Structured CSV
        if csv_file:
            try:
                tmp_path = save_temp_file(csv_file)
                csv_profile = normalize_profile(parse_csv(tmp_path))
                parsed_profiles.append(csv_profile)
                os.remove(tmp_path)
                st.success("✅ Recruiter CSV parsed successfully")
            except Exception as e:
                st.error(f"❌ Failed to parse CSV: {e}")

        # Process Unstructured Resume
        if resume_file:
            try:
                tmp_path = save_temp_file(resume_file)
                resume_profile = normalize_profile(parse_resume(tmp_path))
                parsed_profiles.append(resume_profile)
                os.remove(tmp_path)
                st.success("✅ Resume parsed successfully")
            except Exception as e:
                st.error(f"❌ Failed to parse Resume: {e}")

        # Process Unstructured Recruiter Notes
        if notes_file:
            try:
                tmp_path = save_temp_file(notes_file)
                notes_profile = normalize_profile(parse_notes(tmp_path))
                parsed_profiles.append(notes_profile)
                os.remove(tmp_path)
                st.success("✅ Recruiter Notes parsed successfully")
            except Exception as e:
                st.error(f"❌ Failed to parse Recruiter Notes: {e}")

        # Process GitHub URL
        if github_url:
            try:
                github_profile = normalize_profile(parse_github(github_url))
                parsed_profiles.append(github_profile)
                st.success("✅ GitHub Profile parsed successfully")
            except Exception as e:
                st.error(f"❌ Failed to parse GitHub URL: {e}")

        # Process LinkedIn URL
        if linkedin_url:
            try:
                linkedin_profile = normalize_profile(parse_linkedin(linkedin_url))
                parsed_profiles.append(linkedin_profile)
                st.success("✅ LinkedIn Profile parsed successfully")
            except Exception as e:
                st.error(f"❌ Failed to parse LinkedIn URL: {e}")

        # Execute Pipeline Reconciliation
        if parsed_profiles:
            with st.spinner("Reconciling and merging profiles..."):
                final_profile = merge(parsed_profiles)
                errors = validate(final_profile)
                
                # Load Config
                config = None
                if config_file:
                    try:
                        config = json.loads(config_file.getvalue().decode("utf-8"))
                    except Exception as e:
                        st.error(f"❌ Invalid custom config JSON: {e}")
                
                if not config:
                    default_config_path = "configs/default.json"
                    if os.path.exists(default_config_path):
                        with open(default_config_path, "r") as f:
                            config = json.load(f)
                    else:
                        config = {"fields": [{"path": "full_name"}, {"path": "emails"}, {"path": "skills"}]}

                try:
                    projected_profile = project(final_profile, config)
                except Exception as e:
                    st.error(f"❌ Error during projection mapping: {e}")
                    projected_profile = None

            if projected_profile:
                # Tabs to visualize reports
                tab1, tab2, tab3 = st.tabs(["✨ Projected Profile", "📁 Canonical Intermediate", "📋 Validation Report"])
                
                with tab1:
                    st.json(projected_profile)
                    st.download_button(
                        label="Download Projected Profile",
                        data=json.dumps(projected_profile, indent=2),
                        file_name="candidate_profile.json",
                        mime="application/json"
                    )
                
                with tab2:
                    st.json(final_profile)
                    st.download_button(
                        label="Download Canonical Intermediate",
                        data=json.dumps(final_profile, indent=2),
                        file_name="canonical_profile.json",
                        mime="application/json"
                    )
                    
                with tab3:
                    validation_report_path = "output/validation_report.json"
                    if os.path.exists(validation_report_path):
                        with open(validation_report_path, "r") as f:
                            report = json.load(f)
                        st.json(report)
                    else:
                        st.warning("Validation report not generated.")
        else:
            st.warning("⚠️ Please provide at least one input source before generating.")
