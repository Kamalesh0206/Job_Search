import server
from fastapi.testclient import TestClient

def test_endpoints():
    client = TestClient(server.app)

    print("--- 1. Testing /api/stats ---")
    r1 = client.get('/api/stats?profile=ALL')
    assert r1.status_code == 200, f"Stats failed: {r1.status_code}"
    data1 = r1.json()
    print("  Total jobs (ALL):", data1['stats']['total_jobs'])
    print("  Total AI jobs:", data1['ai_engineer']['total_jobs'])
    print("  Total Test jobs:", data1['test_engineer']['total_jobs'])
    print("  Available countries count:", len(data1['available_countries']))

    print("\n--- 2. Testing /api/jobs per profile ---")
    r2 = client.get('/api/jobs?profile=AI_ENGINEER')
    assert r2.status_code == 200, f"Jobs failed: {r2.status_code}"
    data2 = r2.json()
    print("  AI Engineer jobs returned:", data2['count'])

    r3 = client.get('/api/jobs?profile=TEST_ENGINEER')
    assert r3.status_code == 200, f"Jobs failed: {r3.status_code}"
    data3 = r3.json()
    print("  Test Engineer jobs returned:", data3['count'])

    print("\n--- 3. Testing /api/resume/{profile_id} ---")
    r4 = client.get('/api/resume/AI_ENGINEER')
    assert r4.status_code == 200, f"AI Resume failed: {r4.status_code}"
    assert r4.headers['content-type'] == 'application/pdf'
    print(f"  [PASS] AI Resume returned PDF ({len(r4.content)} bytes)")

    r5 = client.get('/api/resume/TEST_ENGINEER')
    assert r5.status_code == 200, f"Test Resume failed: {r5.status_code}"
    assert r5.headers['content-type'] == 'application/pdf'
    print(f"  [PASS] Test Resume returned PDF ({len(r5.content)} bytes)")

    print("\n--- 4. Testing /api/cover-letter ---")
    r6 = client.post('/api/cover-letter', json={
        "company_name": "Siemens Healthineers",
        "job_title": "Senior AI Validation Engineer",
        "profile_id": "AI_ENGINEER"
    })
    assert r6.status_code == 200
    print("  [PASS] Cover letter generation API works:", len(r6.json().get('cover_letter', '')) > 200)

    print("\n==========================================")
    print("  ALL API ENDPOINTS TESTED SUCCESSFULLY!  ")
    print("==========================================")

if __name__ == "__main__":
    test_endpoints()
