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
    page_title="Candidate Ingestion Dashboard",
    layout="wide"
)

st.title("Candidate Ingestion Dashboard")
st.markdown("""
Streamline candidate screening by ingesting data from multiple sources, normalizing details, and generating a clean, reconciled view for recruiters.
""")

# Setup two-column layout
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("Input Sources")

    # Structured Sources
    st.markdown("#### Structured Sources")
    ats_file = st.file_uploader("Upload ATS JSON file", type=["json"])
    csv_file = st.file_uploader("Upload Recruiter CSV Export", type=["csv"])

    # Unstructured Sources
    st.markdown("#### Unstructured Sources")
    resume_file = st.file_uploader("Upload Resume (DOCX, PDF, TXT)", type=["docx", "pdf", "txt"])
    notes_file = st.file_uploader("Upload Recruiter Notes (.txt)", type=["txt"])

    # Social Profiles
    st.markdown("#### Social & Public URLs")
    github_url = st.text_input("GitHub Profile URL", placeholder="https://github.com/username")
    linkedin_url = st.text_input("LinkedIn Profile URL", placeholder="https://linkedin.com/in/username")

    # Runtime Projection Config
    st.markdown("#### Output Configuration")
    config_file = st.file_uploader("Upload custom projection config JSON (optional)", type=["json"])

with col2:
    st.subheader("Recruiter Profile View")
    
    generate_btn = st.button("Process & Merge Candidate Data", type="primary", use_container_width=True)
    
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
                st.toast("ATS JSON parsed")
            except Exception as e:
                st.error(f"Failed to parse ATS JSON: {e}")

        # Process Structured CSV
        if csv_file:
            try:
                tmp_path = save_temp_file(csv_file)
                csv_profile = normalize_profile(parse_csv(tmp_path))
                parsed_profiles.append(csv_profile)
                os.remove(tmp_path)
                st.toast("Recruiter CSV parsed")
            except Exception as e:
                st.error(f"Failed to parse CSV: {e}")

        # Process Unstructured Resume
        resume_profile = None
        if resume_file:
            try:
                tmp_path = save_temp_file(resume_file)
                resume_profile = normalize_profile(parse_resume(tmp_path))
                parsed_profiles.append(resume_profile)
                os.remove(tmp_path)
                st.toast("Resume parsed")
            except Exception as e:
                st.error(f"Failed to parse Resume: {e}")

        # Process Unstructured Recruiter Notes
        if notes_file:
            try:
                tmp_path = save_temp_file(notes_file)
                notes_profile = normalize_profile(parse_notes(tmp_path))
                parsed_profiles.append(notes_profile)
                os.remove(tmp_path)
                st.toast("Recruiter Notes parsed")
            except Exception as e:
                st.error(f"Failed to parse Recruiter Notes: {e}")

        # Auto-follow links extracted from Resume
        github_to_parse = github_url
        linkedin_to_parse = linkedin_url

        if resume_profile and "links" in resume_profile and resume_profile["links"] and resume_profile["links"]["value"]:
            r_links = resume_profile["links"]["value"]
            if not github_to_parse and r_links.get("github"):
                github_to_parse = r_links.get("github")
                if not github_to_parse.startswith("http"):
                    github_to_parse = "https://" + github_to_parse
                st.info(f"Auto-discovered GitHub URL from resume: {github_to_parse}")
            if not linkedin_to_parse and r_links.get("linkedin"):
                linkedin_to_parse = r_links.get("linkedin")
                if not linkedin_to_parse.startswith("http"):
                    linkedin_to_parse = "https://" + linkedin_to_parse
                st.info(f"Auto-discovered LinkedIn URL from resume: {linkedin_to_parse}")

        # Process GitHub URL
        if github_to_parse:
            try:
                github_profile = normalize_profile(parse_github(github_to_parse))
                parsed_profiles.append(github_profile)
                st.toast("GitHub Profile parsed")
            except Exception as e:
                st.error(f"Failed to parse GitHub URL: {e}")

        # Process LinkedIn URL
        if linkedin_to_parse:
            try:
                linkedin_profile = normalize_profile(parse_linkedin(linkedin_to_parse))
                parsed_profiles.append(linkedin_profile)
                st.toast("LinkedIn Profile parsed")
            except Exception as e:
                st.error(f"Failed to parse LinkedIn URL: {e}")

        # Execute Pipeline Reconciliation
        if parsed_profiles:
            with st.spinner("Executing pipeline Ingestion..."):
                final_profile = merge(parsed_profiles)
                errors = validate(final_profile)
                
                # Load Config
                config = None
                if config_file:
                    try:
                        config = json.loads(config_file.getvalue().decode("utf-8"))
                    except Exception as e:
                        st.error(f"Invalid custom config JSON: {e}")
                
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
                    st.error(f"Error during projection mapping: {e}")
                    projected_profile = None

            if projected_profile:
                # View tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "Recruiter Dashboard", 
                    "Projected Output JSON", 
                    "Canonical Intermediate JSON", 
                    "Validation & Audit"
                ])
                
                with tab1:
                    st.markdown(f"### Candidate ID: {final_profile.get('candidate_id')}")
                    
                    mc1, mc2, mc3 = st.columns(3)
                    with mc1:
                        st.metric(
                            label="Candidate Name", 
                            value=final_profile.get("full_name") or "Unknown"
                        )
                    with mc2:
                        st.metric(
                            label="Location", 
                            value=f"{final_profile['location']['city']}, {final_profile['location']['country']}" if (final_profile.get("location") and final_profile["location"].get("city")) else "Not Provided"
                        )
                    with mc3:
                        st.metric(
                            label="Experience", 
                            value=f"{final_profile.get('years_experience', 0.0)} Years"
                        )

                    st.markdown("---")

                    # Overview & Contact Details
                    oc1, oc2 = st.columns(2)
                    with oc1:
                        st.markdown("#### Contact Details")
                        emails = final_profile.get("emails", [])
                        primary_email = emails[0] if emails else "None"
                        phones = final_profile.get("phones", [])
                        primary_phone = phones[0] if phones else "None"
                        st.markdown(f"**Primary Email**: `{primary_email}`")
                        st.markdown(f"**Primary Phone**: `{primary_phone}`")
                        
                        st.markdown("#### Links")
                        links = final_profile.get("links")
                        if links:
                            st.markdown(f"- **LinkedIn**: {links.get('linkedin') or 'None'}")
                            st.markdown(f"- **GitHub**: {links.get('github') or 'None'}")
                            st.markdown(f"- **Portfolio**: {links.get('portfolio') or 'None'}")
                        else:
                            st.markdown("No URLs detected.")
                    
                    with oc2:
                        st.markdown("#### Confidence Metrics")
                        conf = final_profile.get("overall_confidence", 0.0)
                        st.markdown(f"**Overall Ingestion Confidence**: `{int(conf*100)}%`")
                        st.progress(conf)
                        st.markdown(f"**Unique Ingestion Sources**: `{len(parsed_profiles)}`")
                        st.markdown(f"**Skills Detected**: `{len(final_profile.get('skills', []))}`")

                    st.markdown("---")

                    # Skills section rendered cleanly
                    st.markdown("#### Technical Skills")
                    skills = final_profile.get("skills", [])
                    if skills:
                        # Render skills in a nice grid
                        cols = st.columns(5)
                        for idx, s in enumerate(skills):
                            with cols[idx % 5]:
                                st.info(f"**{s['name']}**\n\nScore: {int(s['confidence']*100)}%")
                    else:
                        st.markdown("No skills detected.")

                    st.markdown("---")

                    # Experience and Education columns
                    ec1, ec2 = st.columns(2)
                    
                    with ec1:
                        st.markdown("#### Experience History")
                        exp = final_profile.get("experience", [])
                        if exp:
                            for e in exp:
                                st.markdown(f"##### **{e.get('title')}**")
                                st.markdown(f"*{e.get('company')}*  |  `{e.get('start') or ''}` - `{e.get('end') or 'Present'}`")
                                if e.get("summary"):
                                    st.markdown(e.get("summary").replace("\n", "\n\n"))
                                st.markdown("---")
                        else:
                            st.markdown("No experience history detected.")
                            
                    with ec2:
                        st.markdown("#### Education Details")
                        edu = final_profile.get("education", [])
                        if edu:
                            for ed in edu:
                                st.markdown(f"##### **{ed.get('degree')} in {ed.get('field')}**")
                                st.markdown(f"*{ed.get('institution')}*  |  End Year: `{ed.get('end_year') or 'N/A'}`")
                                st.markdown("---")
                        else:
                            st.markdown("No education details detected.")

                with tab2:
                    st.json(projected_profile)
                    st.download_button(
                        label="Download Projected Profile",
                        data=json.dumps(projected_profile, indent=2),
                        file_name="candidate_profile.json",
                        mime="application/json"
                    )
                
                with tab3:
                    st.json(final_profile)
                    st.download_button(
                        label="Download Canonical Intermediate",
                        data=json.dumps(final_profile, indent=2),
                        file_name="canonical_profile.json",
                        mime="application/json"
                    )
                    
                with tab4:
                    st.markdown("### Quality Audit Checks")
                    validation_report_path = "output/validation_report.json"
                    if os.path.exists(validation_report_path):
                        with open(validation_report_path, "r") as f:
                            report = json.load(f)
                        st.json(report)
                    else:
                        st.warning("Validation report not generated.")
                        
                    st.markdown("### Ingestion Provenance Logs")
                    provenance_log = final_profile.get("provenance", [])
                    if provenance_log:
                        st.table(provenance_log)
        else:
            st.warning("Please provide at least one input source before generating.")
