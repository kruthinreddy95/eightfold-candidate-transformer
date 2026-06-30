"""
Main entry point for the Multi-Source Candidate Data Transformer pipeline.
Can be run as a command-line tool.
Supports ATS JSON, Resume files, Recruiter CSV, Recruiter Notes, GitHub URLs, and LinkedIn URLs.
"""

import json
import logging
import os
import argparse
import sys
from datetime import datetime

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/pipeline.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def main():
    setup_logging()
    start_time = datetime.now()

    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--ats", default="data/ats.json", help="Path to ATS JSON file")
    parser.add_argument("--resume", default="data/resume.docx", help="Path to Resume file")
    parser.add_argument("--csv", help="Path to Recruiter CSV file")
    parser.add_argument("--notes", help="Path to Recruiter Notes file")
    parser.add_argument("--github", help="GitHub Profile URL")
    parser.add_argument("--linkedin", help="LinkedIn Profile URL")
    parser.add_argument("--config", default="configs/default.json", help="Path to projection configuration JSON")
    parser.add_argument("--output", default="output/candidate_profile.json", help="Path to output projected profile")
    args = parser.parse_args()

    print("\n🚀 Eightfold Pipeline Started\n")
    logging.info("Pipeline Started")

    parsed_profiles = []

    # 1. Load and parse ATS
    if os.path.exists(args.ats):
        print(f"Loading ATS Data from: {args.ats}...")
        try:
            with open(args.ats, "r", encoding="utf-8") as file:
                ats_data = json.load(file)
            ats_profile = normalize_profile(parse_ats(ats_data))
            parsed_profiles.append(ats_profile)
            logging.info("ATS Parsed and Normalized Successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to parse ATS data: {e}")
            logging.warning(f"ATS Parse failed: {e}")
    else:
        logging.warning(f"ATS file {args.ats} not found")

    # 2. Load and parse Resume
    if os.path.exists(args.resume):
        print(f"Loading Resume from: {args.resume}...")
        try:
            resume_profile = normalize_profile(parse_resume(args.resume))
            parsed_profiles.append(resume_profile)
            logging.info("Resume Parsed and Normalized Successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to parse Resume: {e}")
            logging.warning(f"Resume Parse failed: {e}")
    else:
        logging.warning(f"Resume file {args.resume} not found")

    # 3. Load and parse CSV
    if args.csv:
        if os.path.exists(args.csv):
            print(f"Loading Recruiter CSV from: {args.csv}...")
            try:
                csv_profile = normalize_profile(parse_csv(args.csv))
                parsed_profiles.append(csv_profile)
                logging.info("CSV Parsed and Normalized Successfully")
            except Exception as e:
                print(f"⚠️ Warning: Failed to parse CSV: {e}")
                logging.warning(f"CSV Parse failed: {e}")
        else:
            print(f"⚠️ Warning: CSV file {args.csv} not found. Skipping.")

    # 4. Load and parse Recruiter Notes
    if args.notes:
        if os.path.exists(args.notes):
            print(f"Loading Recruiter Notes from: {args.notes}...")
            try:
                notes_profile = normalize_profile(parse_notes(args.notes))
                parsed_profiles.append(notes_profile)
                logging.info("Recruiter Notes Parsed and Normalized Successfully")
            except Exception as e:
                print(f"⚠️ Warning: Failed to parse Recruiter Notes: {e}")
                logging.warning(f"Recruiter Notes Parse failed: {e}")
        else:
            print(f"⚠️ Warning: Notes file {args.notes} not found. Skipping.")

    # 5. Load and parse GitHub URL
    if args.github:
        print(f"Fetching GitHub Profile URL: {args.github}...")
        try:
            github_profile = normalize_profile(parse_github(args.github))
            parsed_profiles.append(github_profile)
            logging.info("GitHub URL Parsed and Normalized Successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to parse GitHub URL: {e}")
            logging.warning(f"GitHub URL Parse failed: {e}")

    # 6. Load and parse LinkedIn URL
    if args.linkedin:
        print(f"Resolving LinkedIn Profile URL: {args.linkedin}...")
        try:
            linkedin_profile = normalize_profile(parse_linkedin(args.linkedin))
            parsed_profiles.append(linkedin_profile)
            logging.info("LinkedIn URL Parsed and Normalized Successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to parse LinkedIn URL: {e}")
            logging.warning(f"LinkedIn URL Parse failed: {e}")

    # Check if we have at least one source
    if not parsed_profiles:
        print("\n❌ Error: No valid candidate sources parsed. Pipeline aborted.\n")
        logging.error("No valid candidate sources parsed")
        return

    # Merge
    print(f"Merging {len(parsed_profiles)} parsed profiles...")
    final_profile = merge(parsed_profiles)
    logging.info("Merge Completed")

    # Validate Intermediate Profile
    print("Validating Canonical Profile...")
    errors = validate(final_profile)

    if errors:
        print("\n⚠️ Profile Quality Warnings:")
        for error in errors:
            print(f"- {error}")
        logging.warning(f"Canonical Profile Validation warnings: {errors}")
    else:
        print("✅ Canonical Profile Valid")
        logging.info("Canonical Profile Validation Passed")

    # Load Config
    print(f"Loading Projection Config from: {args.config}...")
    if not os.path.exists(args.config):
        print(f"❌ Error: Config file {args.config} not found. Aborting.")
        logging.error(f"Config file {args.config} not found")
        return

    with open(args.config, "r", encoding="utf-8") as file:
        config = json.load(file)

    # Project
    print("Projecting Output...")
    try:
        projected_output = project(final_profile, config)
    except Exception as e:
        print(f"\n❌ Error during projection: {e}\n")
        logging.error(f"Projection failed: {e}")
        return

    # Validate Projected Output
    proj_errors = validate_projected(projected_output, config)
    if proj_errors:
        print("\n❌ Projected Schema Validation Failed:")
        for err in proj_errors:
            print(f"- {err}")
        logging.error(f"Projected Schema Validation Failed: {proj_errors}")
        if config.get("on_missing") == "error":
            print("\n❌ Aborting pipeline due to missing required projected fields.\n")
            return
    else:
        print("✅ Projected Schema Validation Passed")
        logging.info("Projected Schema Validation Passed")

    # Save Output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(projected_output, file, indent=2)

    # Also save the raw intermediate canonical profile for transparency/debugging
    canon_output_path = os.path.join(os.path.dirname(args.output), "canonical_profile.json")
    with open(canon_output_path, "w", encoding="utf-8") as file:
        json.dump(final_profile, file, indent=2)

    logging.info("Output Exported")

    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()

    print("\n📄 Outputs Saved:")
    print(f"  - Projected Output: {args.output}")
    print(f"  - Canonical Intermediate: {canon_output_path}")
    print(f"  - Validation Report: output/validation_report.json")
    print(f"\n⏱ Execution Time: {execution_time:.4f} seconds")
    logging.info(f"Execution Time: {execution_time} seconds")

    print("\n📊 Final Projected Profile:\n")
    print(json.dumps(projected_output, indent=2))


if __name__ == "__main__":
    main()
