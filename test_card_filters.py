import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    # Test via database directly first
    import database
    profiles = ["ALL", "AI_ENGINEER", "TEST_ENGINEER"]
    cards = [
        ("total", {}),
        ("relevant", {"min_score": 60}),
        ("sponsorship", {"sponsorship": "CONFIRMED"}),
        ("remote", {"work_arrangement": "Remote"}),
        ("applied", {"status": "APPLIED"}),
        ("interviews", {"status": "INTERVIEW"}),
        ("rejections", {"status": "REJECTED"})
    ]

    card_stat_keys = {
        "total": "total_jobs",
        "relevant": "relevant_jobs",
        "sponsorship": "confirmed_sponsorship",
        "remote": "remote_jobs",
        "applied": "applications_submitted",
        "interviews": "interviews",
        "rejections": "rejections"
    }

    all_passed = True
    print("================================================================")
    print("RUNNING COMPREHENSIVE CARD FILTER & PROFILE ISOLATION TESTS")
    print("================================================================")

    for prof in profiles:
        stats_response = database.get_stats_db(prof)
        stats = stats_response["stats"]
        print(f"\n--- Testing Profile: {prof} ---")

        for card_type, filter_params in cards:
            stat_key = card_stat_keys[card_type]
            expected_count = stats[stat_key]

            # Query database with the card filter
            actual_jobs = database.get_all_jobs(profile_id=prof, **filter_params)
            actual_count = len(actual_jobs)

            match = (expected_count == actual_count)
            status_str = "PASS" if match else "FAIL"
            if not match:
                all_passed = False

            print(f"  [{status_str}] Card '{card_type}': card stat = {expected_count}, filtered records = {actual_count}")

            # Specific rule checks
            if card_type == "sponsorship":
                # Ensure no UNKNOWN was included
                for j in actual_jobs:
                    assert j.get("visa_sponsorship_status", "").upper() == "CONFIRMED", "Unknown treated as confirmed!"
            elif card_type == "remote":
                # Ensure no Hybrid or Onsite was included
                for j in actual_jobs:
                    arr = j.get("work_arrangement", "").lower()
                    assert "remote" in arr and "hybrid" not in arr and "onsite" not in arr, f"Non-remote job included: {arr}"
            elif card_type == "applied":
                # Ensure genuinely APPLIED
                for j in actual_jobs:
                    assert str(j.get("status") or j.get("application_status", "")).upper() == "APPLIED"
            elif card_type == "interviews":
                # Ensure in active pipeline stages
                for j in actual_jobs:
                    st = str(j.get("status") or j.get("application_status", "")).upper()
                    assert st in ("INTERVIEW", "ASSESSMENT", "OFFER", "PIPELINE")
            elif card_type == "rejections":
                # Ensure strictly REJECTED
                for j in actual_jobs:
                    st = str(j.get("status") or j.get("application_status", "")).upper()
                    assert st == "REJECTED"

    print("\n================================================================")
    if all_passed:
        print("ALL 21 CARD FILTER TESTS PASSED (3 Profiles x 7 Cards)!")
    else:
        print("SOME CARD FILTER TESTS FAILED!")
    print("================================================================")
    return all_passed

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
