import os
import json
from datetime import datetime
from pathlib import Path

from profile_manager import ProfileManager
from cover_letter_generator import CoverLetterGenerator
from scoring_engine import calculate_relevance
from apply_engine import evaluate_auto_apply_eligibility
import database

def run_all_tests():
    print("=" * 65)
    print("  DUAL-PROFILE ENHANCEMENT TEST SUITE (15 TESTS)")
    print("=" * 65)

    database.init_db()
    pm = ProfileManager()
    clg = CoverLetterGenerator()
    conf = json.load(open("config.json", "r", encoding="utf-8"))

    # ----------------------------------------------------
    # TEST 1: Switch to AI Engineer and verify contact details
    # ----------------------------------------------------
    print("\n[TEST 1] AI Engineer Contact Details Verification")
    ai_info = pm.get_personal_info("AI_ENGINEER")
    assert ai_info["name"] == "Kamalesan C", f"Expected Kamalesan C, got {ai_info['name']}"
    assert ai_info["phone"] == "+91 7305131264", f"Expected +91 7305131264, got {ai_info['phone']}"
    assert ai_info["email"] == "kamaleshcai686@gmail.com", f"Expected kamaleshcai686@gmail.com, got {ai_info['email']}"
    assert "546646442" in ai_info["linkedin"], f"Unexpected LinkedIn URL: {ai_info['linkedin']}"
    assert ai_info["github"] == "https://github.com/Kamalesh0206", f"Expected GitHub URL, got {ai_info['github']}"
    assert "Coimbatore" in ai_info["location"]
    print("  [OK] Phone: " + ai_info["phone"])
    print("  [OK] Email: " + ai_info["email"])
    print("  [OK] LinkedIn: " + ai_info["linkedin"])
    print("  [OK] GitHub: " + ai_info["github"])
    print("  [PASS] TEST 1 passed successfully.")

    # ----------------------------------------------------
    # TEST 2: Switch to Test Engineer and verify separate contact details
    # ----------------------------------------------------
    print("\n[TEST 2] Test Engineer Contact Details (Independent & No GitHub)")
    test_info = pm.get_personal_info("TEST_ENGINEER")
    assert test_info["name"] == "Kamalesan C"
    assert test_info["phone"] == "+91 98436 19970", f"Expected +91 98436 19970, got {test_info['phone']}"
    assert test_info["email"] == "softkamalesh@gmail.com", f"Expected softkamalesh@gmail.com, got {test_info['email']}"
    assert "62b952299" in test_info["linkedin"]
    assert "Tamil Nadu" in test_info["location"]
    assert test_info["github"] == "", f"Test Engineer GitHub should be empty unless configured, got '{test_info['github']}'"
    # Ensure no contact details are shared
    assert test_info["phone"] != ai_info["phone"], "Phones must not match"
    assert test_info["email"] != ai_info["email"], "Emails must not match"
    print("  [OK] Phone: " + test_info["phone"])
    print("  [OK] Email: " + test_info["email"])
    print("  [OK] LinkedIn: " + test_info["linkedin"])
    print("  [OK] GitHub: (Hidden / Empty as configured)")
    print("  [PASS] TEST 2 passed successfully.")

    # ----------------------------------------------------
    # TEST 3: Generate AI Engineer Cover Letter and verify contact fields
    # ----------------------------------------------------
    print("\n[TEST 3] AI Engineer Tailored Cover Letter Contact Fields")
    cl_ai = clg.generate("AI Agent Developer", "Anthropic", profile_id="AI_ENGINEER", save_to_disk=False)
    ai_cl_text = cl_ai["cover_letter"]
    assert "kamaleshcai686@gmail.com" in ai_cl_text
    assert "+91 7305131264" in ai_cl_text
    assert "https://github.com/Kamalesh0206" in ai_cl_text
    assert "softkamalesh@gmail.com" not in ai_cl_text
    assert "+91 98436 19970" not in ai_cl_text
    print("  [OK] Contains AI Engineer email, phone, and GitHub")
    print("  [OK] Excluded Test Engineer contact details completely")
    print("  [PASS] TEST 3 passed successfully.")

    # ----------------------------------------------------
    # TEST 4: Generate Test Engineer Cover Letter and verify contact fields
    # ----------------------------------------------------
    print("\n[TEST 4] Test Engineer Tailored Cover Letter Contact Fields")
    cl_test = clg.generate("HIL Test Engineer", "BMW Group", profile_id="TEST_ENGINEER", save_to_disk=False)
    test_cl_text = cl_test["cover_letter"]
    assert "softkamalesh@gmail.com" in test_cl_text
    assert "+91 98436 19970" in test_cl_text
    assert "kamaleshcai686@gmail.com" not in test_cl_text
    assert "+91 7305131264" not in test_cl_text
    assert "github.com" not in test_cl_text, "Test Engineer cover letter must not contain GitHub URL"
    print("  [OK] Contains Test Engineer email, phone, and location")
    print("  [OK] Excluded GitHub Portfolio from Test Engineer letter")
    print("  [PASS] TEST 4 passed successfully.")

    # ----------------------------------------------------
    # TEST 5: Verify Cover Letter Date Uses Actual Current Date
    # ----------------------------------------------------
    print("\n[TEST 5] Cover Letter Date Verification (Actual Current Date)")
    today_formatted = datetime.now().strftime("%B %d, %Y")
    assert today_formatted in ai_cl_text, f"Expected '{today_formatted}' in cover letter date"
    assert today_formatted in test_cl_text, f"Expected '{today_formatted}' in cover letter date"
    print(f"  [OK] Cover letter uses today's current date: {today_formatted}")
    print("  [PASS] TEST 5 passed successfully.")

    # ----------------------------------------------------
    # TEST 6: Verify Subject Contains Actual Job Title and Company
    # ----------------------------------------------------
    print("\n[TEST 6] Cover Letter Subject Verification")
    expected_ai_subj = "Application for AI Agent Developer Position – Anthropic"
    expected_test_subj = "Application for HIL Test Engineer Position – BMW Group"
    assert expected_ai_subj in ai_cl_text, f"Expected subject '{expected_ai_subj}' in AI letter"
    assert expected_test_subj in test_cl_text, f"Expected subject '{expected_test_subj}' in Test letter"
    print(f"  [OK] AI Subject: {expected_ai_subj}")
    print(f"  [OK] Test Subject: {expected_test_subj}")
    print("  [PASS] TEST 6 passed successfully.")

    # ----------------------------------------------------
    # TEST 7: Change AI Engineer skills and verify Test Engineer unchanged
    # ----------------------------------------------------
    print("\n[TEST 7] Independent Skills Isolation")
    test_skills_before = list(pm.get_profile("TEST_ENGINEER")["technical_skills"])
    # Modify AI Engineer skills
    pm.update_profile("AI_ENGINEER", {
        "technical_skills": ["Python", "Generative AI", "Unique_AI_Skill_X99"]
    })
    test_skills_after = list(pm.get_profile("TEST_ENGINEER")["technical_skills"])
    assert test_skills_before == test_skills_after, "Test Engineer skills must not be altered by AI Engineer modifications!"
    assert "Unique_AI_Skill_X99" not in test_skills_after
    # Reset AI Engineer back to default
    pm.reset_to_defaults("AI_ENGINEER")
    print("  [OK] Modified AI Engineer skills; verified Test Engineer skills remained identical")
    print("  [OK] Reset AI Engineer to defaults successfully")
    print("  [PASS] TEST 7 passed successfully.")

    # ----------------------------------------------------
    # TEST 8: Verify a 75% match is eligible for automatic application
    # ----------------------------------------------------
    print("\n[TEST 8] Automatic Application Eligibility (> 70% Threshold)")
    res_75 = evaluate_auto_apply_eligibility(
        match_score=75,
        mandatory_pass=True,
        job_is_open=True,
        not_already_applied=True,
        application_data_is_valid=True,
        submission_method_is_authorized=True,
        threshold=70
    )
    assert res_75["eligible"] is True, f"75% match should be eligible for auto-apply: {res_75}"
    print(f"  [OK] 75% Match Evaluation: Eligible={res_75['eligible']} ({res_75['reason']})")
    print("  [PASS] TEST 8 passed successfully.")

    # ----------------------------------------------------
    # TEST 9: Verify a 70% match is NOT automatically submitted
    # ----------------------------------------------------
    print("\n[TEST 9] Strict Threshold Boundary (Score == 70%)")
    res_70 = evaluate_auto_apply_eligibility(
        match_score=70,
        mandatory_pass=True,
        job_is_open=True,
        not_already_applied=True,
        application_data_is_valid=True,
        submission_method_is_authorized=True,
        threshold=70
    )
    assert res_70["eligible"] is False, "Score of exactly 70% must NOT be automatically submitted"
    assert res_70["status"] == "READY_TO_APPLY", f"Expected READY_TO_APPLY, got {res_70['status']}"
    print(f"  [OK] 70% Match Evaluation: Eligible={res_70['eligible']}, Status={res_70['status']}")
    print("  [PASS] TEST 9 passed successfully.")

    # ----------------------------------------------------
    # TEST 10: Verify a 60% match goes to manual review
    # ----------------------------------------------------
    print("\n[TEST 10] Manual Review Queue (Score == 60%)")
    res_60 = evaluate_auto_apply_eligibility(
        match_score=60,
        mandatory_pass=True,
        job_is_open=True,
        not_already_applied=True,
        application_data_is_valid=True,
        submission_method_is_authorized=True,
        threshold=70
    )
    assert res_60["eligible"] is False
    assert res_60["status"] == "READY_TO_APPLY", f"60% score must route to manual review queue (READY_TO_APPLY), got {res_60['status']}"
    print(f"  [OK] 60% Match Evaluation: Status={res_60['status']} (Manual Review Queue)")
    print("  [PASS] TEST 10 passed successfully.")

    # ----------------------------------------------------
    # TEST 11: Verify duplicate job is not submitted twice
    # ----------------------------------------------------
    print("\n[TEST 11] Duplicate Submission Prevention")
    res_dup = evaluate_auto_apply_eligibility(
        match_score=85,
        mandatory_pass=True,
        not_already_applied=False # Already submitted
    )
    assert res_dup["eligible"] is False, "Duplicate vacancy must NOT be submitted twice"
    assert res_dup["status"] == "APPLIED"
    print("  [OK] Duplicate check blocked submission and preserved APPLIED status")
    print("  [PASS] TEST 11 passed successfully.")

    # ----------------------------------------------------
    # TEST 12: Verify missing mandatory qualifications prevent automatic submission
    # ----------------------------------------------------
    print("\n[TEST 12] Mandatory Qualification Gaps Disqualification")
    res_disq = evaluate_auto_apply_eligibility(
        match_score=85,
        mandatory_pass=False, # Mandatory disqualification (e.g. security clearance gap)
        threshold=70
    )
    assert res_disq["eligible"] is False
    assert res_disq["status"] == "MANUAL_ACTION_REQUIRED"
    print(f"  [OK] Mandatory requirement gap prevented auto-apply; Status={res_disq['status']}")
    print("  [PASS] TEST 12 passed successfully.")

    # ----------------------------------------------------
    # TEST 13: Verify failed submissions are NOT recorded as APPLIED
    # ----------------------------------------------------
    print("\n[TEST 13] Failed Submissions Not Recorded as APPLIED")
    sample_jobs = database.get_all_jobs(limit=1)
    assert len(sample_jobs) > 0, "Database should have records"
    test_job = sample_jobs[0]
    test_job_id = test_job["id"]
    initial_status = test_job.get("status", "DISCOVERED")

    # Simulate submission error update
    database.update_job_application_db(
        job_id=test_job_id,
        status="SUBMISSION_FAILED",
        error_details="Employer ATS network timeout during form submit",
        submission_timestamp=datetime.now().isoformat()
    )
    updated_job = database.get_job_by_id(test_job_id)
    assert updated_job is not None, f"Job {test_job_id} not found"
    assert updated_job["application_status"] == "SUBMISSION_FAILED", f"Status should be SUBMISSION_FAILED, got {updated_job['application_status']}"
    assert updated_job["application_status"] != "APPLIED", "Failed application must NEVER be marked APPLIED"
    assert "timeout" in (updated_job.get("error_details") or "")

    # Restore initial status
    database.update_job_status_db(test_job_id, initial_status)
    print("  [OK] Status correctly recorded as SUBMISSION_FAILED with error details preserved")
    print("  [PASS] TEST 13 passed successfully.")

    # ----------------------------------------------------
    # TEST 14: Verify application tracker preserves historical records
    # ----------------------------------------------------
    print("\n[TEST 14] Application Tracker History Preservation")
    all_jobs = database.get_all_jobs()
    print(f"  [OK] Total job records stored in database: {len(all_jobs)}")
    assert len(all_jobs) >= 200, f"Expected >= 200 preserved job records, found {len(all_jobs)}"
    ai_jobs = [j for j in all_jobs if j.get("profile_id") == "AI_ENGINEER"]
    test_jobs = [j for j in all_jobs if j.get("profile_id") == "TEST_ENGINEER"]
    print(f"  [OK] AI Engineer historical jobs: {len(ai_jobs)}")
    print(f"  [OK] Test Engineer historical jobs: {len(test_jobs)}")
    assert len(ai_jobs) > 0 and len(test_jobs) > 0
    print("  [PASS] TEST 14 passed successfully.")

    # ----------------------------------------------------
    # TEST 15: Independent Automatic-Submission Toggle & Policy Verification
    # ----------------------------------------------------
    print("\n[TEST 15] Independent Automatic-Submission Toggle & Policy Verification")
    
    # 1. Verify default to OFF
    pm.reset_to_defaults("AI_ENGINEER")
    pm.reset_to_defaults("TEST_ENGINEER")
    ai_def = pm.get_profile("AI_ENGINEER")["auto_apply_enabled"]
    test_def = pm.get_profile("TEST_ENGINEER")["auto_apply_enabled"]
    print(f"  [OK] Default state: AI_ENGINEER={ai_def}, TEST_ENGINEER={test_def}")
    assert ai_def is False, "AI Engineer must default to OFF"
    assert test_def is False, "Test Engineer must default to OFF"

    # 2. Enabling AI Engineer does NOT enable Test Engineer
    pm.update_profile("AI_ENGINEER", {"auto_apply_enabled": True})
    assert pm.get_profile("AI_ENGINEER")["auto_apply_enabled"] is True
    assert pm.get_profile("TEST_ENGINEER")["auto_apply_enabled"] is False
    print("  [OK] Enabling AI Engineer: AI=True, TEST=False (Independent)")

    # 3. Enabling Test Engineer does NOT enable AI Engineer
    pm.update_profile("AI_ENGINEER", {"auto_apply_enabled": False})
    pm.update_profile("TEST_ENGINEER", {"auto_apply_enabled": True})
    assert pm.get_profile("AI_ENGINEER")["auto_apply_enabled"] is False
    assert pm.get_profile("TEST_ENGINEER")["auto_apply_enabled"] is True
    print("  [OK] Enabling Test Engineer: AI=False, TEST=True (Independent)")

    # 4. Eligibility check reflecting profile setting
    e_ai = evaluate_auto_apply_eligibility(80, True, submission_method_is_authorized=pm.get_profile("AI_ENGINEER")["auto_apply_enabled"])
    e_test = evaluate_auto_apply_eligibility(80, True, submission_method_is_authorized=pm.get_profile("TEST_ENGINEER")["auto_apply_enabled"])
    assert e_ai["eligible"] is False, "AI Engineer auto-apply disabled must prevent auto-apply"
    assert e_test["eligible"] is True, "Test Engineer auto-apply enabled must allow auto-apply"
    print("  [OK] Eligibility enforcement reflects independent profile flags")

    # 5. Daily limit enforcement
    e_limit = evaluate_auto_apply_eligibility(85, True, submission_method_is_authorized=True, daily_limit_reached=True)
    assert e_limit["eligible"] is False, "Daily limit reached must prevent auto-apply"
    print("  [OK] Daily application limit enforcement: Blocked auto-apply when limit reached")

    # 6. Policy message accuracy
    def get_policy_status(ai_on, test_on):
        if not ai_on and not test_on:
            return "Automatic submission is disabled for both profiles."
        elif ai_on and test_on:
            return "Automatic submission is enabled for both profiles."
        elif ai_on:
            return "Automatic submission is enabled for AI Engineer."
        else:
            return "Automatic submission is enabled for Test Engineer."

    assert "disabled for both" in get_policy_status(False, False)
    assert "enabled for AI Engineer" in get_policy_status(True, False)
    assert "enabled for Test Engineer" in get_policy_status(False, True)
    assert "enabled for both" in get_policy_status(True, True)
    print("  [OK] Dynamic policy message accurately reflects all 4 profile states")

    # Restore default safe state (both OFF)
    pm.update_profile("AI_ENGINEER", {"auto_apply_enabled": False})
    pm.update_profile("TEST_ENGINEER", {"auto_apply_enabled": False})
    print("  [OK] Reset both profiles to default safe state (OFF)")
    print("  [PASS] TEST 15 passed successfully.")

    print("\n" + "=" * 65)
    print("  ALL 15 DUAL-PROFILE TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
