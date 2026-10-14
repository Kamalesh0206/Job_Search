import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "generated_documents"
AI_DOCS_DIR = DOCS_DIR / "AI_ENGINEER"
TEST_DOCS_DIR = DOCS_DIR / "TEST_ENGINEER"

AI_RESUME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 12mm 14mm 12mm 14mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b; line-height: 1.4; font-size: 9.3pt; background: #ffffff;
  }
  .header { text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 6px; margin-bottom: 9px; }
  .header h1 { font-size: 20pt; font-weight: 800; letter-spacing: 0.5px; color: #0f172a; text-transform: uppercase; margin-bottom: 2px; }
  .header .tagline { font-size: 10.2pt; font-weight: 700; color: #0284c7; margin-bottom: 4px; }
  .header .contact-row { font-size: 8.6pt; color: #475569; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
  .header .contact-row a { color: #0284c7; text-decoration: none; font-weight: 500; }
  .section { margin-bottom: 9px; }
  .section-title {
    font-size: 10.2pt; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px;
    border-bottom: 1px solid #cbd5e1; padding-bottom: 2px; margin-bottom: 5px;
  }
  p.summary { font-size: 9pt; color: #334155; text-align: justify; line-height: 1.42; }
  .skills-grid { display: grid; grid-template-columns: 140px 1fr; row-gap: 3px; font-size: 8.7pt; }
  .skill-label { font-weight: 700; color: #0f172a; }
  .skill-val { color: #334155; }
  .item { margin-bottom: 6px; }
  .item-header { display: flex; justify-content: space-between; align-items: baseline; font-size: 9.2pt; font-weight: 700; color: #0f172a; }
  .item-sub { display: flex; justify-content: space-between; font-size: 8.6pt; color: #0369a1; font-weight: 600; margin-bottom: 2px; }
  .item-tech { font-size: 8.3pt; color: #64748b; font-style: italic; margin-bottom: 3px; }
  ul.bullets { margin-left: 15px; font-size: 8.7pt; color: #334155; }
  ul.bullets li { margin-bottom: 2px; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
</style>
</head>
<body>

<div class="header">
  <h1>Kamalesan C</h1>
  <div class="tagline">AI Engineer | Generative AI, AI Agents & Python Automation</div>
  <div class="contact-row">
    <span>📍 Coimbatore, India (Open to Remote & Visa Relocation)</span>
    <span>📞 +91 7305131264</span>
    <span>✉️ <a href="mailto:kamaleshcai686@gmail.com">kamaleshcai686@gmail.com</a></span>
    <span>🔗 <a href="https://www.linkedin.com/in/kamalesan-c-546646442">LinkedIn</a></span>
    <span>💻 <a href="https://github.com/Kamalesh0206">GitHub</a></span>
  </div>
</div>

<div class="section">
  <div class="section-title">Professional Summary</div>
  <p class="summary">
    Versatile and results-driven AI Engineer with 7.4 years of robust software engineering and automation experience, specializing in Generative AI, LLM applications, autonomous AI agent workflows, and backend API platforms. Proven record of developing production-grade AI solutions including multi-agent governance frameworks, AI-powered engineering test automation, and full-stack REST microservices with Python, FastAPI, Docker, and vector databases. Strong background in complex system architectures, test automation, and prompt engineering, dedicated to building reliable, high-performance intelligent software.
  </p>
</div>

<div class="section">
  <div class="section-title">Technical Skills</div>
  <div class="skills-grid">
    <div class="skill-label">Generative AI & LLMs:</div>
    <div class="skill-val">Gemini API, OpenAI API, LLM Applications, Prompt Engineering, RAG Architectures, Vector Databases, MCP</div>
    <div class="skill-label">AI Agents & Workflows:</div>
    <div class="skill-val">Multi-Agent Systems, Autonomous Workflow Orchestration, n8n, Human-in-the-Loop AI Automation</div>
    <div class="skill-label">Languages & Backends:</div>
    <div class="skill-val">Python, FastAPI, REST APIs, SQLAlchemy, PostgreSQL, Redis, React, Embedded C</div>
    <div class="skill-label">DevOps & Cloud:</div>
    <div class="skill-val">Docker, Git & GitHub, Google Cloud Platform (Cloud Run), Linux, CI/CD Pipelines</div>
  </div>
</div>

<div class="section">
  <div class="section-title">Key AI & Software Projects</div>

  <div class="item">
    <div class="item-header">
      <span>AI-Powered SIL Test Automation Platform</span>
      <span>2024 – 2026</span>
    </div>
    <div class="item-tech">Python, FastAPI, Generative AI (LLMs), Prompt Engineering, Automated Diagnostics</div>
    <ul class="bullets">
      <li>Designed an end-to-end intelligent platform that parses test requirements and auto-generates test scripts for software validation.</li>
      <li>Integrated LLM-assisted failure triage, reducing diagnostic turnaround time and accelerating regression cycles.</li>
      <li>Built responsive FastAPI backend services handling structured telemetry, automated reports, and execution monitoring.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-header">
      <span>EpiAgent PMO — AI Project Governance & Risk Platform</span>
      <span>2024</span>
    </div>
    <div class="item-tech">Python, Gemini API, Multi-Agent Architecture, Vector Search, Streamlit/FastAPI</div>
    <ul class="bullets">
      <li>Architected multi-agent system coordinating automated PMO risk assessments, milestone tracking, and compliance audits.</li>
      <li>Implemented context-aware RAG pipelines querying unstructured project documentation to surface delivery blockers.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-header">
      <span>Automation Job Applying & Outreach Agent</span>
      <span>2026</span>
    </div>
    <div class="item-tech">Python, FastAPI, Playwright, ATS Handlers, OpenPyXL, HTML/CSS UI</div>
    <ul class="bullets">
      <li>Developed dual-role autonomous job-hunting engine scraping, scoring, and auto-applying to international job boards.</li>
      <li>Integrated human-in-the-loop approval workflows, ATS resume matching, and recruiter outreach generation.</li>
    </ul>
  </div>
</div>

<div class="section">
  <div class="section-title">Professional Experience</div>
  <div class="item">
    <div class="item-header">
      <span>Senior Software Engineer / Automation Engineer</span>
      <span>2019 – Present</span>
    </div>
    <div class="item-sub">
      <span>Capgemini Technology Services (Client: Bosch Global Software Technologies)</span>
      <span>Coimbatore, India</span>
    </div>
    <ul class="bullets">
      <li>Led Python automation architectures and system-level validation for mission-critical software deployments.</li>
      <li>Engineered custom test harnesses, automated verification pipelines, and analytical data export utilities.</li>
      <li>Collaborated across international engineering teams to deliver high-quality releases under strict SLAs.</li>
    </ul>
  </div>
</div>

<div class="two-col section">
  <div>
    <div class="section-title">Certifications</div>
    <ul class="bullets">
      <li><strong>Generative AI Mastermind</strong> — OutSkill</li>
      <li><strong>AI Foundation & Prompt Engineering</strong> — Udemy</li>
      <li><strong>n8n Masterclass: AI Automations & Workflows</strong> — Udemy</li>
    </ul>
  </div>
  <div>
    <div class="section-title">Education & Mobility</div>
    <ul class="bullets">
      <li><strong>Master of Computer Applications (M.C.A)</strong> — Bharathidasan University</li>
      <li><strong>Mobility:</strong> Open to Worldwide Remote & International Visa Relocation</li>
      <li><strong>Languages:</strong> English (Professional), Tamil (Native)</li>
    </ul>
  </div>
</div>

</body>
</html>
"""

TEST_RESUME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 12mm 14mm 12mm 14mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b; line-height: 1.4; font-size: 9.3pt; background: #ffffff;
  }
  .header { text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 6px; margin-bottom: 9px; }
  .header h1 { font-size: 20pt; font-weight: 800; letter-spacing: 0.5px; color: #0f172a; text-transform: uppercase; margin-bottom: 2px; }
  .header .tagline { font-size: 10.2pt; font-weight: 700; color: #0284c7; margin-bottom: 4px; }
  .header .contact-row { font-size: 8.6pt; color: #475569; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
  .header .contact-row a { color: #0284c7; text-decoration: none; font-weight: 500; }
  .section { margin-bottom: 9px; }
  .section-title {
    font-size: 10.2pt; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px;
    border-bottom: 1px solid #cbd5e1; padding-bottom: 2px; margin-bottom: 5px;
  }
  p.summary { font-size: 9pt; color: #334155; text-align: justify; line-height: 1.42; }
  .skills-grid { display: grid; grid-template-columns: 140px 1fr; row-gap: 3px; font-size: 8.7pt; }
  .skill-label { font-weight: 700; color: #0f172a; }
  .skill-val { color: #334155; }
  .item { margin-bottom: 6px; }
  .item-header { display: flex; justify-content: space-between; align-items: baseline; font-size: 9.2pt; font-weight: 700; color: #0f172a; }
  .item-sub { display: flex; justify-content: space-between; font-size: 8.6pt; color: #0369a1; font-weight: 600; margin-bottom: 2px; }
  .item-tech { font-size: 8.3pt; color: #64748b; font-style: italic; margin-bottom: 3px; }
  ul.bullets { margin-left: 15px; font-size: 8.7pt; color: #334155; }
  ul.bullets li { margin-bottom: 2px; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
</style>
</head>
<body>

<div class="header">
  <h1>Kamalesan C</h1>
  <div class="tagline">Senior Automotive Test Engineer | HIL/SIL Testing, ECU Validation & Python Automation</div>
  <div class="contact-row">
    <span>📍 Coimbatore, India (Open to Worldwide Relocation & Remote)</span>
    <span>📞 +91 7305131264</span>
    <span>✉️ <a href="mailto:kamaleshcai686@gmail.com">kamaleshcai686@gmail.com</a></span>
    <span>🔗 <a href="https://www.linkedin.com/in/kamalesan-c-546646442">LinkedIn</a></span>
    <span>💻 <a href="https://github.com/Kamalesh0206">GitHub</a></span>
  </div>
</div>

<div class="section">
  <div class="section-title">Professional Summary</div>
  <p class="summary">
    Accomplished Senior Automotive Test and Validation Engineer with 7.4 years of specialized engineering experience in ECU validation, Hardware-in-the-Loop (HIL) and Software-in-the-Loop (SIL) test automation, and automotive embedded systems. Extensive domain expertise delivering powertrain validation for Mercedes-Benz projects with Capgemini and Bosch Global Software Technologies. Proficient in TraceTronic ECU-TEST, dSPACE SCALEXIO, ETAS LABCAR, CANoe, CANalyzer, INCA, UDS diagnostic protocols (ISO 14229), and Python test script development. Expert in requirement-based verification, regression automation, and defect root-cause analysis.
  </p>
</div>

<div class="section">
  <div class="section-title">Technical Expertise</div>
  <div class="skills-grid">
    <div class="skill-label">Testing Disciplines:</div>
    <div class="skill-val">HIL Testing, SIL Testing, ECU Validation, System V&V, Regression Testing, Requirements-Based Testing</div>
    <div class="skill-label">Test Tools & Hardware:</div>
    <div class="skill-val">TraceTronic ECU-TEST, dSPACE SCALEXIO, ETAS LABCAR, SystemDesk, ControlDesk, UDE Debugger</div>
    <div class="skill-label">Automotive Protocols:</div>
    <div class="skill-val">CAN, LIN, FlexRay, Automotive Ethernet, UDS (ISO 14229), OBD-II, OBDonUDS</div>
    <div class="skill-label">Measurement & Calibration:</div>
    <div class="skill-val">Vector CANoe, CANalyzer, ETAS INCA, MDA, CANape</div>
    <div class="skill-label">Languages & Scripting:</div>
    <div class="skill-val">Python (Automated Test Frameworks, PyTest), Embedded C, CAPL, XML, Batch Scripting</div>
  </div>
</div>

<div class="section">
  <div class="section-title">Professional Experience</div>

  <div class="item">
    <div class="item-header">
      <span>Senior Test Engineer — Automotive ECU & HIL/SIL Validation</span>
      <span>2019 – Present</span>
    </div>
    <div class="item-sub">
      <span>Capgemini Technology Services (Client: Bosch Global Software Technologies)</span>
      <span>Coimbatore, India</span>
    </div>
    <ul class="bullets">
      <li>Spearheaded powertrain ECU validation and HIL test execution for premium OEM programs (Mercedes-Benz).</li>
      <li>Developed and maintained automated test suites in TraceTronic ECU-TEST integrated with dSPACE SCALEXIO and ETAS LABCAR benches.</li>
      <li>Executed comprehensive UDS diagnostic validation, fault injection, and fail-safe recovery testing across CAN/LIN bus networks.</li>
      <li>Authored automated Python tools to parse MDF/A2L measurement files, extract diagnostic DTCs, and auto-generate compliance reports.</li>
      <li>Participated in cross-functional defect triage with ECU software developers, accelerating defect closure and release readiness.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-header">
      <span>Embedded Test & Software Engineer</span>
      <span>2018 – 2019</span>
    </div>
    <div class="item-sub">
      <span>Embedded Automation Labs</span>
      <span>India</span>
    </div>
    <ul class="bullets">
      <li>Developed Embedded C firmware and automated regression test harnesses for microcontroller-based controllers.</li>
      <li>Executed hardware communication protocol tests (UART, SPI, I2C) and sensor signal validation using oscilloscopes and logic analyzers.</li>
    </ul>
  </div>
</div>

<div class="section">
  <div class="section-title">Key Projects & Achievements</div>
  <div class="item">
    <div class="item-header">
      <span>Mercedes-Benz Powertrain ECU Validation & Diagnostic Automation</span>
    </div>
    <div class="item-tech">TraceTronic ECU-TEST, dSPACE SCALEXIO, CANoe, INCA, UDS Diagnostic Protocols</div>
    <ul class="bullets">
      <li>Automated 500+ powertrain validation test scenarios, cutting regression execution cycles by 40%.</li>
      <li>Created automated flashing and diagnostic verification scripts verifying ECU software build integrity.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-header">
      <span>Python-Based SIL Test Automation Framework</span>
    </div>
    <div class="item-tech">Python, Simulation Models, CANalyzer API, Automated Test Reporting</div>
    <ul class="bullets">
      <li>Constructed Python simulation test runner enabling developers to run virtual ECU validation ahead of physical bench allocation.</li>
    </ul>
  </div>
</div>

<div class="two-col section">
  <div>
    <div class="section-title">Education & Credentials</div>
    <ul class="bullets">
      <li><strong>Master of Computer Applications (M.C.A)</strong> — Bharathidasan University</li>
      <li><strong>Automotive Diagnostics (UDS & OBD-II)</strong> Validation Training</li>
      <li><strong>Python for Automotive Test Automation</strong> Certification</li>
    </ul>
  </div>
  <div>
    <div class="section-title">Mobility & Work Authorization</div>
    <ul class="bullets">
      <li><strong>Mobility:</strong> Open to International Relocation & Worldwide Remote</li>
      <li><strong>Sponsorship:</strong> Requires work visa for EU/US on-site positions</li>
      <li><strong>Languages:</strong> English (Professional), Tamil (Native)</li>
    </ul>
  </div>
</div>

</body>
</html>
"""

async def generate_pdf(html_content: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "8mm", "bottom": "8mm", "left": "10mm", "right": "10mm"}
        )
        await browser.close()

async def generate_all_resumes():
    AI_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    ai_pdf = AI_DOCS_DIR / "Kamalesan_C_AI_Engineer_Resume.pdf"
    test_pdf = TEST_DOCS_DIR / "Kamalesan_C_Test_Engineer_Resume.pdf"

    await generate_pdf(AI_RESUME_HTML, ai_pdf)
    await generate_pdf(TEST_RESUME_HTML, test_pdf)

    # Also keep base resume.pdf in root for backwards compatibility
    root_resume = ROOT / "resume.pdf"
    await generate_pdf(AI_RESUME_HTML, root_resume)

    print(f"Generated AI Engineer Resume: {ai_pdf}")
    print(f"Generated Test Engineer Resume: {test_pdf}")

def get_resume_path_for_profile(profile_id: str, company_name: Optional[str] = None) -> Path:
    norm_pid = "TEST_ENGINEER" if "TEST" in str(profile_id).upper() else "AI_ENGINEER"
    target_dir = TEST_DOCS_DIR if norm_pid == "TEST_ENGINEER" else AI_DOCS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    if company_name:
        clean_company = "".join(c for c in company_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        company_pdf = target_dir / f"{clean_company}_Resume.pdf"
        if company_pdf.exists():
            return company_pdf

    default_file = target_dir / ("Kamalesan_C_Test_Engineer_Resume.pdf" if norm_pid == "TEST_ENGINEER" else "Kamalesan_C_AI_Engineer_Resume.pdf")
    if not default_file.exists():
        # Fall back to root resume.pdf if not yet generated
        return ROOT / "resume.pdf"
    return default_file

if __name__ == "__main__":
    asyncio.run(generate_all_resumes())
