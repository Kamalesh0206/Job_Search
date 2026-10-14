import json
from pathlib import Path
import classifier
import scoring_engine
import excel_writer
import cover_letter_generator
import generate_resume_pdf

def run_tests():
    conf = json.load(open('config.json', 'r', encoding='utf-8'))

    print("--- Test 1: Classification ---")
    cases = [
        ('Senior AI Engineer', 'Working on LLM fine-tuning, RAG, and FastAPI', 'AI_ENGINEER'),
        ('HIL Test Engineer', 'Validation of automotive ECU using ECU-TEST and CANoe', 'TEST_ENGINEER'),
        ('Generative AI Software Test Automation Engineer', 'Building GenAI LLM agents for automotive HIL and SIL testing', 'BOTH'),
        ('Python Backend Developer', 'Django web application maintenance using Python', 'IRRELEVANT'),
        ('Manual QA Tester', 'Selenium web browser test cases', 'IRRELEVANT')
    ]

    for title, desc, expected in cases:
        res = classifier.classify_job(title, desc, conf)
        cat = res['category']
        assert cat == expected, f"Failed: '{title}' expected '{expected}', got '{cat}'"
        print(f"  [PASS] '{title}' -> {cat}")

    print("\n--- Test 2: Relevance Scoring & Sponsorship ---")
    score_ai = scoring_engine.calculate_relevance({
        'title': 'AI Engineer',
        'description': 'Building AI agents using Python, FastAPI, Docker, and Gemini API. Remote worldwide. Visa sponsorship provided.',
        'location': 'Worldwide Remote'
    }, 'AI_ENGINEER', conf)
    print(f"  AI Score: {score_ai['score']} | Visa: {score_ai['visa_sponsorship_status']} | Work: {score_ai['work_arrangement']}")
    assert score_ai['score'] >= 70, f"Expected high score, got {score_ai['score']}"
    assert score_ai['visa_sponsorship_status'] == 'CONFIRMED'

    score_test = scoring_engine.calculate_relevance({
        'title': 'Automotive HIL Test Engineer',
        'description': 'Powertrain ECU validation with TraceTronic ECU-TEST, CANoe, dSPACE SCALEXIO. 7+ years experience required.',
        'location': 'Munich, Germany'
    }, 'TEST_ENGINEER', conf)
    print(f"  Test Score: {score_test['score']} | Visa: {score_test['visa_sponsorship_status']} | Work: {score_test['work_arrangement']}")
    assert score_test['score'] >= 70, f"Expected high score, got {score_test['score']}"

    print("\n--- Test 3: Excel Tracker Loading & Schema ---")
    jobs = excel_writer.load_all_jobs(Path('Job_Search_Tracker.xlsx'))
    print(f"  Excel tracker rows: {len(jobs)}")
    assert len(jobs) >= 180
    assert "profile_id" in jobs[0]
    assert "role_category" in jobs[0]
    assert "relevance_score" in jobs[0]
    assert "status" in jobs[0]

    print("\n--- Test 4: Dual Resumes Availability ---")
    ai_res = generate_resume_pdf.get_resume_path_for_profile('AI_ENGINEER')
    test_res = generate_resume_pdf.get_resume_path_for_profile('TEST_ENGINEER')
    assert ai_res.exists(), "AI resume PDF not found"
    assert test_res.exists(), "Test resume PDF not found"
    print(f"  [PASS] AI Resume: {ai_res.name} ({ai_res.stat().st_size} bytes)")
    print(f"  [PASS] Test Resume: {test_res.name} ({test_res.stat().st_size} bytes)")

    print("\n--- Test 5: Dual Tailored Cover Letter Generator ---")
    clg = cover_letter_generator.CoverLetterGenerator()
    cl_ai = clg.generate('AI Agent Developer', 'OpenAI', profile_id='AI_ENGINEER')
    assert 'Generative AI' in cl_ai['cover_letter'] and 'EpiAgent PMO' in cl_ai['cover_letter']
    print(f"  [PASS] AI Cover Letter generated ({len(cl_ai['cover_letter'])} chars)")

    cl_test = clg.generate('Automotive Validation Engineer', 'Mercedes-Benz', profile_id='TEST_ENGINEER')
    assert 'TraceTronic ECU-TEST' in cl_test['cover_letter'] and 'dSPACE' in cl_test['cover_letter']
    print(f"  [PASS] Test Cover Letter generated ({len(cl_test['cover_letter'])} chars)")

    print("\n==========================================")
    print("  ALL 5 TEST SUITE STAGES PASSED!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
