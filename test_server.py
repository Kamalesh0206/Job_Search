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
    print("\n--- 5. Testing /health and /api/health ---")
    r_health = client.get('/health')
    assert r_health.status_code == 200, f"Health check failed: {r_health.status_code}"
    h_data = r_health.json()
    assert h_data['status'] == 'ok'
    assert h_data['database'] == 'healthy'
    assert h_data['total_jobs_stored'] >= 200
    print("  [PASS] Health check returns status 'ok', DB 'healthy', jobs count:", h_data['total_jobs_stored'])

    print("\n--- 6. Testing /api/schedule ---")
    r_sched = client.get('/api/schedule')
    assert r_sched.status_code == 200
    s_data = r_sched.json()
    print("  [PASS] Schedule status retrieved:", s_data.get('interval_hours'), "hours")

    print("\n--- 7. Testing /api/export/excel ---")
    r_excel = client.get('/api/export/excel')
    assert r_excel.status_code == 200
    assert len(r_excel.content) > 1000
    print(f"  [PASS] Excel export returned valid spreadsheet ({len(r_excel.content)} bytes)")

    print("\n--- 8. Testing Authentication Security Flow ---")
    # Temporarily enable auth
    server.AUTH_REQUIRED = True
    server.DASHBOARD_USERNAME = "testadmin"
    server.DASHBOARD_PASSWORD = "secretpassword123"

    # Unauthorized request should receive 401
    r_unauth = client.get('/api/stats')
    assert r_unauth.status_code == 401, f"Expected 401, got {r_unauth.status_code}"
    print("  [PASS] Unauthenticated request blocked with 401 Unauthorized")

    # Health check remains public
    r_pub_health = client.get('/health')
    assert r_pub_health.status_code == 200
    print("  [PASS] Health check remains publicly accessible without auth")

    # Login endpoint generates token
    r_login = client.post('/api/auth/login', json={"username": "testadmin", "password": "secretpassword123"})
    assert r_login.status_code == 200
    token = r_login.json()['token']
    assert len(token) > 10
    print("  [PASS] Valid login generates token:", token[:8] + "...")

    # Authenticated request with Bearer token succeeds
    r_authed = client.get('/api/stats', headers={"Authorization": f"Bearer {token}"})
    assert r_authed.status_code == 200
    print("  [PASS] Authenticated request with Bearer token succeeds (200 OK)")

    # Reset auth state for local dev
    server.AUTH_REQUIRED = False
    server.DASHBOARD_PASSWORD = ""

    print("\n--- 9. Testing /api/profiles and /api/profiles/{id} ---")
    r_profs = client.get('/api/profiles')
    assert r_profs.status_code == 200
    profs_data = r_profs.json()
    assert "AI_ENGINEER" in profs_data
    assert "TEST_ENGINEER" in profs_data
    assert profs_data["AI_ENGINEER"]["phone"] == "+91 7305131264"
    assert profs_data["TEST_ENGINEER"]["phone"] == "+91 98436 19970"
    print("  [PASS] /api/profiles returned dual independent profiles")

    # Update profile settings test
    r_update = client.put('/api/profiles/AI_ENGINEER', json={
        "match_threshold": 75,
        "auto_apply_enabled": True
    })
    assert r_update.status_code == 200
    assert r_update.json()["profile"]["match_threshold"] == 75

    # Reset profile test
    r_reset = client.post('/api/profiles/AI_ENGINEER/reset')
    assert r_reset.status_code == 200
    assert r_reset.json()["profile"]["match_threshold"] == 70
    print("  [PASS] Profile update and reset endpoints succeeded")

    print("\n--- 10. Testing /api/profiles/{id}/auto-apply endpoint ---")
    r_toggle_on = client.post('/api/profiles/AI_ENGINEER/auto-apply', json={"enabled": True})
    assert r_toggle_on.status_code == 200
    assert r_toggle_on.json()["auto_apply_enabled"] is True

    r_toggle_off = client.post('/api/profiles/AI_ENGINEER/auto-apply', json={"enabled": False})
    assert r_toggle_off.status_code == 200
    assert r_toggle_off.json()["auto_apply_enabled"] is False
    print("  [PASS] Auto-apply toggle endpoint succeeded (ON and OFF)")

    print("\n==========================================")
    print("  ALL 10 API & SECURITY TESTS PASSED!    ")
    print("==========================================")

if __name__ == "__main__":
    test_endpoints()

