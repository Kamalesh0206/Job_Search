import subprocess
import time
import urllib.request
import os
import sys
from playwright.sync_api import sync_playwright

PORT = 8099
BASE_URL = f"http://127.0.0.1:{PORT}"

def wait_for_server(timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/stats") as res:
                if res.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def run_tests():
    print(f"Starting uvicorn server on port {PORT}...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--port", str(PORT), "--host", "127.0.0.1"],
        cwd=r"c:\Users\softk\Documents\Jobs\10_Job_Search_Automation\10_Job_Search_Automation",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        if not wait_for_server():
            print("Server failed to start!")
            return False

        print("Server ready! Launching Playwright tests...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            page.goto(BASE_URL)
            page.wait_for_selector("#statsGrid")
            time.sleep(1)

            # 1. TOTAL JOBS CARD
            print("Testing Card 1: Total Jobs Found...")
            page.click("#card-total")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "225", f"Expected 225, got {count_text}"
            assert "active" in page.locator("#card-total").get_attribute("class")
            print(f"  PASS: Card 1 Total Jobs ({count_text} jobs)")

            # 2. RELEVANT JOBS CARD
            print("Testing Card 2: Relevant Jobs (60+)...")
            page.click("#card-relevant")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "199", f"Expected 199, got {count_text}"
            assert page.locator("#filterMinScore").input_value() == "60"
            assert "active" in page.locator("#card-relevant").get_attribute("class")
            assert page.is_visible("#activeCardBanner")
            print(f"  PASS: Card 2 Relevant Jobs ({count_text} jobs)")

            # 3. CONFIRMED SPONSORSHIP CARD (Zero results -> empty state)
            print("Testing Card 3: Confirmed Sponsorship...")
            page.click("#card-sponsorship")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "0", f"Expected 0, got {count_text}"
            assert page.locator("#filterSponsorship").input_value() == "CONFIRMED"
            empty_text = page.locator("#jobsTableBody").inner_text()
            assert "No jobs match this filter." in empty_text, f"Empty state missing! Found: {empty_text}"
            print(f"  PASS: Card 3 Confirmed Sponsorship (0 jobs, empty state: 'No jobs match this filter.')")

            # 4. TEST CLEAR FILTER FROM EMPTY STATE
            print("Testing Clear Filter...")
            page.click("#jobsTableBody button:has-text('Clear Filter')")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "225", f"Expected 225 after clear, got {count_text}"
            assert not page.is_visible("#activeCardBanner")
            print(f"  PASS: Clear Filter restored {count_text} jobs")

            # 5. REMOTE POSITIONS CARD
            print("Testing Card 4: Remote Positions...")
            page.click("#card-remote")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "34", f"Expected 34, got {count_text}"
            assert page.locator("#filterWorkArrangement").input_value() == "Remote"
            print(f"  PASS: Card 4 Remote Positions ({count_text} jobs)")

            # 6. PROFILE SWITCHING WITH ACTIVE CARD FILTER
            print("Testing Profile Switching while Remote card active...")
            # Click AI Engineer pill
            page.click("#profileSelector button[data-profile='AI_ENGINEER']")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "33", f"Expected 33 for AI Remote, got {count_text}"
            assert page.is_visible("#activeCardBanner")
            assert "AI Engineer" in page.locator("#activeCardLabel").inner_text()
            print(f"  PASS: Remote filter preserved on AI Engineer ({count_text} jobs)")

            # Click Test Engineer pill
            page.click("#profileSelector button[data-profile='TEST_ENGINEER']")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "1", f"Expected 1 for Test Remote, got {count_text}"
            assert "Test Engineer" in page.locator("#activeCardLabel").inner_text()
            print(f"  PASS: Remote filter preserved on Test Engineer ({count_text} jobs)")

            # Switch back to All Profiles
            page.click("#profileSelector button[data-profile='ALL']")
            time.sleep(0.5)

            # 7. APPLICATIONS SUBMITTED CARD
            print("Testing Card 5: Applications Submitted...")
            page.click("#card-applied")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "1", f"Expected 1, got {count_text}"
            assert page.locator("#filterStatus").input_value() == "APPLIED"
            print(f"  PASS: Card 5 Applications Submitted ({count_text} jobs)")

            # 8. INTERVIEWS / PIPELINE CARD
            print("Testing Card 6: Interviews / Pipeline...")
            page.click("#card-interviews")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "0", f"Expected 0, got {count_text}"
            assert "No jobs match this filter." in page.locator("#jobsTableBody").inner_text()
            print(f"  PASS: Card 6 Interviews / Pipeline (0 jobs, empty state)")

            # 9. REJECTIONS CARD
            print("Testing Card 7: Rejections...")
            page.click("#card-rejections")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "0", f"Expected 0, got {count_text}"
            assert "No jobs match this filter." in page.locator("#jobsTableBody").inner_text()
            print(f"  PASS: Card 7 Rejections (0 jobs, empty state)")

            # Take screenshot of Rejections empty state
            os.makedirs(r"C:\Users\softk\.gemini\antigravity-ide\brain\7fb6af82-408b-4f41-9e8f-2c7085ae1637", exist_ok=True)
            shot1 = r"C:\Users\softk\.gemini\antigravity-ide\brain\7fb6af82-408b-4f41-9e8f-2c7085ae1637\card_empty_state.png"
            page.screenshot(path=shot1, full_page=False)

            # Click Clear Filter button in active card banner
            page.click("#activeCardBanner button")
            time.sleep(0.5)
            count_text = page.locator("#tabCountJobs").inner_text()
            assert count_text == "225", f"Expected 225 after clear, got {count_text}"

            # Click Remote card and capture screenshot of active state
            page.click("#card-remote")
            time.sleep(0.5)
            shot2 = r"C:\Users\softk\.gemini\antigravity-ide\brain\7fb6af82-408b-4f41-9e8f-2c7085ae1637\card_remote_filtered.png"
            page.screenshot(path=shot2, full_page=False)

            browser.close()
            print("\nALL BROWSER AUTOMATION TESTS COMPLETED SUCCESSFULLY!")
            return True

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
