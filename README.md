# Dual-Role AI Job Search and Application Automation Agent

An autonomous, production-grade job search and application assistant that manages **TWO independent professional profiles** with worldwide vacancy discovery, evidence-based relevance scoring, ATS document customization, and human-in-the-loop application review.

---

## 1. Candidate Background & Profiles

Candidate: **Kamalesan C** (7.4 Years Overall Engineering Experience)  
Location: Coimbatore, Tamil Nadu, India (Open to Worldwide Remote & Relocation with Visa Sponsorship)

### Profile A: AI ENGINEER (`AI_ENGINEER`)
* **Target Titles:** AI Engineer, Generative AI Engineer, AI Agent Developer, LLM Engineer, Applied AI Engineer, AI Automation Engineer, Python AI Developer, AI Application Engineer.
* **Core Skills:** Python, Generative AI, Gemini API, OpenAI API, LLM Applications, AI Agent Development, Prompt Engineering, FastAPI, REST APIs, PostgreSQL, SQLAlchemy, Redis, Docker, React, n8n, MCP, RAG, Git & GitHub.
* **Featured Projects:**
  1. AI-Powered SIL Test Automation Platform
  2. EpiAgent PMO — AI Project Governance & Risk Platform
  3. AI Instagram Publisher Agent
  4. Automation Job Applying Agent
  5. HyGreen Application
* **Resume:** `generated_documents/AI_ENGINEER/Kamalesan_C_AI_Engineer_Resume.pdf`

### Profile B: TEST ENGINEER (`TEST_ENGINEER`)
* **Target Titles:** Test Engineer, Senior Test Engineer, Automotive Test Engineer, HIL Test Engineer, SIL Test Engineer, ECU Validation Engineer, Test Automation Engineer, Python Test Automation Engineer, Embedded Software Test Engineer, Automotive System Validation Engineer, V&V Engineer.
* **Core Skills:** Automotive Embedded Systems, HIL/SIL Testing, ECU Validation, Python Test Automation, TraceTronic ECU-TEST, dSPACE SCALEXIO, ETAS LABCAR, CANoe, CANalyzer, INCA, UDE, SystemDesk, ControlDesk, CAN, LIN, FlexRay, Ethernet, UDS (ISO 14229), OBD-II, OBDonUDS, Embedded C, Requirements-based Testing, Regression Testing, Diagnostic Testing.
* **Relevant Experience:** 7.4 years automotive powertrain ECU validation with Capgemini and Bosch Global Software Technologies on Mercedes-Benz programs.
* **Resume:** `generated_documents/TEST_ENGINEER/Kamalesan_C_Test_Engineer_Resume.pdf`

---

## 2. Core Architecture & Features

### 1. Dual Independent Profiles
* Configure either role independently in `config.json`.
* Switch between **`AI ENGINEER`**, **`TEST ENGINEER`**, or **`ALL PROFILES`** with 1-click in the dashboard.
* Statistics, resumes, and tailored cover letters are strictly separated and never mixed.

### 2. Worldwide Job Search
* Collects from authorized multi-source channels:
  1. **Remotive Public API** — Worldwide Remote engineering listings.
  2. **Arbeitnow Public API** — Germany, Netherlands, Sweden, UK & Europe.
  3. **EU Remote Jobs** — European remote tech roles.
  4. **LinkedIn Public Endpoints** — Polite guest listings with rate-limit backoff.
* Preferred Locations: Germany, Netherlands, Ireland, Sweden, UK, US, Canada, Australia, Singapore, UAE, Worldwide Remote.

### 3. Strict Job Classification (`classifier.py`)
Classifies every discovered job into:
* `AI_ENGINEER`
* `TEST_ENGINEER`
* `BOTH`
* `IRRELEVANT`
* **Rule Guards:** Mentions of Python alone do *not* qualify as AI Engineer. General web/mobile QA does *not* qualify as Automotive Test Engineer.

### 4. 0–100 Explainable Relevance Scoring (`scoring_engine.py`)
* Technical skills match: 35%
* Job responsibilities match: 25%
* Experience match: 15%
* Job title relevance: 10%
* Location & work arrangement: 10%
* Visa sponsorship match: 5%
* Detects confirmed sponsorship vs unknown vs on-site work authorization requirements.

### 5. Deduplication & Excel Tracker (`excel_writer.py`)
* Maintains standard 31-column `Job_Search_Tracker.xlsx`.
* Automatically updates `Last Seen Date` without creating duplicate rows or altering initial discovery timestamps.
* Preserves complete historical application states.

### 6. Human-in-the-Loop Application Approval
* Strict safety: No application is submitted automatically without candidate review and explicit approval.
* Tailored cover letters and resumes saved to `generated_documents/{PROFILE_ID}/`.

---

## 3. Installation & Setup

1. **Clone repository and open terminal**:
   ```bash
   cd c:\Users\softk\Documents\Jobs\10_Job_Search_Automation\10_Job_Search_Automation
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

---

## 4. Running the Application

### Option A: Launch Interactive Dashboard (Recommended)
Double-click `run_dashboard.bat` or run:
```bash
python server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### Option B: Run Job Search via CLI
Search both profiles:
```bash
python main.py ALL
```
Search AI Engineer only:
```bash
python main.py AI_ENGINEER
```
Search Automotive Test Engineer only:
```bash
python main.py TEST_ENGINEER
```

### Option C: Re-generate ATS Resumes
```bash
python generate_resume_pdf.py
```

---

## 5. Excel Columns Reference
1. `Job ID`
2. `Profile ID`
3. `Role Category`
4. `Job Title`
5. `Company`
6. `Country`
7. `City`
8. `Work Arrangement`
9. `Remote Eligibility`
10. `Visa Sponsorship Status`
11. `Salary Range`
12. `Experience Required`
13. `Required Skills`
14. `Matched Skills`
15. `Missing Skills`
16. `Job Description`
17. `Job URL`
18. `Source`
19. `Posted Date`
20. `Found Date`
21. `Last Seen Date`
22. `Relevance Score`
23. `Resume Used`
24. `Cover Letter Path`
25. `Application Status` (DISCOVERED, SHORTLISTED, READY_FOR_REVIEW, APPROVED, APPLIED, INTERVIEW, REJECTED, WITHDRAWN, CLOSED)
26. `Application Date`
27. `Recruiter Name`
28. `Recruiter Contact`
29. `Follow-Up Date`
30. `Notes`
31. `Fingerprint`
