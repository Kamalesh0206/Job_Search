import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "resume_template.html"
PDF_PATH = ROOT / "resume.pdf"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {
    size: A4;
    margin: 14mm 15mm 14mm 15mm;
  }
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.42;
    font-size: 9.5pt;
    background: #ffffff;
  }
  .header {
    text-align: center;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 8px;
    margin-bottom: 11px;
  }
  .header h1 {
    font-size: 21pt;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #0f172a;
    text-transform: uppercase;
    margin-bottom: 3px;
  }
  .header .tagline {
    font-size: 10.5pt;
    font-weight: 700;
    color: #0369a1;
    letter-spacing: 0.3px;
    margin-bottom: 5px;
  }
  .header .contact-row {
    font-size: 8.8pt;
    color: #475569;
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  .header .contact-row a {
    color: #0369a1;
    text-decoration: none;
    font-weight: 500;
  }
  .section {
    margin-bottom: 11px;
  }
  .section-title {
    font-size: 10.5pt;
    font-weight: 700;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 2px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
  }
  p.summary {
    font-size: 9.2pt;
    color: #334155;
    text-align: justify;
    line-height: 1.45;
  }
  .skills-grid {
    display: grid;
    grid-template-columns: 145px 1fr;
    row-gap: 3.5px;
    font-size: 8.8pt;
  }
  .skill-label {
    font-weight: 700;
    color: #0f172a;
  }
  .skill-val {
    color: #334155;
  }
  .item {
    margin-bottom: 7px;
  }
  .item:last-child {
    margin-bottom: 0;
  }
  .item-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 2px;
  }
  .item-title {
    font-size: 9.8pt;
    font-weight: 700;
    color: #0f172a;
  }
  .item-company {
    font-size: 9pt;
    font-weight: 600;
    color: #0369a1;
  }
  .item-tech {
    font-size: 8.4pt;
    font-weight: 600;
    color: #64748b;
    font-style: italic;
  }
  .item-meta {
    font-size: 8.5pt;
    font-weight: 500;
    color: #64748b;
    white-space: nowrap;
  }
  ul.bullets {
    list-style: none;
    padding-left: 0;
  }
  ul.bullets li {
    position: relative;
    padding-left: 12px;
    font-size: 8.8pt;
    color: #334155;
    margin-bottom: 2px;
    line-height: 1.38;
  }
  ul.bullets li::before {
    content: "•";
    position: absolute;
    left: 1px;
    color: #0369a1;
    font-weight: bold;
  }
  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }
</style>
</head>
<body>

<div class="header">
  <h1>Kamalesan C</h1>
  <div class="tagline">AI ENGINEER &bull; GENERATIVE AI &bull; AI AGENTS &bull; PYTHON AUTOMATION</div>
  <div class="contact-row">
    <span>Coimbatore, Tamil Nadu, India</span>
    <span>•</span>
    <span>+91 7305131264</span>
    <span>•</span>
    <span><a href="mailto:kamaleshcai686@gmail.com">kamaleshcai686@gmail.com</a></span>
    <span>•</span>
    <span><a href="https://www.linkedin.com/in/kamalesan-c-546646442">linkedin.com/in/kamalesan-c-546646442</a></span>
    <span>•</span>
    <span><a href="https://github.com/AdminEpiware/EpiAgent-PMO">github.com/AdminEpiware/EpiAgent-PMO</a></span>
  </div>
</div>

<div class="section">
  <div class="section-title">Professional Summary</div>
  <p class="summary">
    AI-focused engineer with <strong>7.4 years of engineering experience</strong> across Generative AI application development, Python automation, automotive embedded systems, and software engineering. Hands-on experience architecting autonomous AI agents, LLM pipelines, and backend integrations using <strong>Gemini and OpenAI APIs, Python, FastAPI, REST APIs, PostgreSQL, SQLAlchemy, Redis, and Docker</strong>. Proven expertise implementing human-in-the-loop workflows, MCP concepts, deterministic validation gates, and automated test orchestration. Open to worldwide remote roles and international relocation.
  </p>
</div>

<div class="section">
  <div class="section-title">Core Technical Skills</div>
  <div class="skills-grid">
    <div class="skill-label">Generative AI & LLMs:</div>
    <div class="skill-val">Gemini API, OpenAI API, LLM Application Architecture, Prompt Engineering, Context Engineering, RAG Concepts, Function Calling / Tool Calling</div>
    <div class="skill-label">AI Agents & Workflow:</div>
    <div class="skill-val">Autonomous Agents, Multi-Agent Orchestration, Model Context Protocol (MCP), n8n Automation, Human-in-the-Loop Validation, Audit Trails</div>
    <div class="skill-label">Backend & APIs:</div>
    <div class="skill-val">Python, FastAPI, RESTful APIs, PostgreSQL, SQLAlchemy, Redis, SQLite, Microservices, JWT Authentication</div>
    <div class="skill-label">Testing & Automation:</div>
    <div class="skill-val">Python Test Automation, Playwright, TraceTronic ECU-TEST, HIL & SIL Testing, Diagnostic Protocols (CAN, UDS, OBD-II, OBDonUDS)</div>
    <div class="skill-label">DevOps & Cloud:</div>
    <div class="skill-val">Docker Containerization, Git & GitHub, Google Cloud (Cloud Run), Linux, Asynchronous Task Pipelines</div>
    <div class="skill-label">Frontend & UI:</div>
    <div class="skill-val">React, API-Driven Operational Dashboards, Risk Visibility Interfaces, Interactive Web UIs</div>
  </div>
</div>

<div class="section">
  <div class="section-title">Key AI & Automation Projects</div>

  <div class="item">
    <div class="item-head">
      <span class="item-title">EpiAgent PMO — AI Project Governance & Risk Platform</span>
      <span class="item-meta">Google Cloud Run | GitHub</span>
    </div>
    <div class="item-tech">Python, FastAPI, GitLab API, Gemini API, Risk Engine, Interactive Dashboard</div>
    <ul class="bullets">
      <li>Designed an enterprise AI platform that ingests project and repository data via GitLab API to generate portfolio governance and risk visibility.</li>
      <li>Integrated Gemini API to produce executive summary reports, risk interpretations, blocked-task detection, and action recommendations.</li>
      <li>Implemented automated scoring algorithms for project health, completion rates, and critical issue alerts with production REST endpoints.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-head">
      <span class="item-title">AI-Powered SIL Test Automation Platform</span>
      <span class="item-meta">Python | MCP | ECU-TEST</span>
    </div>
    <div class="item-tech">Gemini API, Antigravity, MCP Tool Interfaces, Python, FastAPI, TraceTronic ECU-TEST, RSC/SIL</div>
    <ul class="bullets">
      <li>Designed an AI orchestration layer interfacing with automotive software-in-the-loop (SIL) test execution pipelines to cut manual setup effort.</li>
      <li>Built structured agent workflow: Context Retrieval → Requirement Parsing → Reusable Test Discovery → Draft Generation → Engineer Approval → Controlled Execution → Failure Analysis.</li>
      <li>Enforced strict human-in-the-loop approval gates for WRITE/EXECUTE actions, maintaining deterministic audit logs and evidence-first reports.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-head">
      <span class="item-title">Automation Job Search & Applying Agent</span>
      <span class="item-meta">Python | Playwright | LLM APIs</span>
    </div>
    <div class="item-tech">Python, Playwright, FastAPI, PostgreSQL, Gemini/OpenAI APIs, Excel Tracker</div>
    <ul class="bullets">
      <li>Built an autonomous application assistant that scrapes job portals (LinkedIn, EU Remote Jobs) and categorizes opportunities by role taxonomy.</li>
      <li>Implemented dynamic cover letter and profile customization using LLMs, plus Playwright-powered automated ATS form filling (Greenhouse, Lever, generic ATS) with interactive human review modes.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-head">
      <span class="item-title">AI Instagram Publisher Agent</span>
      <span class="item-meta">FastAPI | React | Docker</span>
    </div>
    <div class="item-tech">Python, FastAPI, React, PostgreSQL, Redis, Docker, Meta Graph API, OpenAI/Gemini</div>
    <ul class="bullets">
      <li>Developed multi-account social media publishing engine featuring scheduled queues, media management, and automated caption/hashtag generation.</li>
    </ul>
  </div>
</div>

<div class="section">
  <div class="section-title">Professional Experience</div>

  <div class="item">
    <div class="item-head">
      <div>
        <span class="item-title">Test Engineer (HIL & SIL)</span> &bull; <span class="item-company">Capgemini Technology Services</span>
      </div>
      <span class="item-meta">Oct 2021 – Present | Coimbatore, India</span>
    </div>
    <div class="item-tech">Client: Bosch Global Software Technologies &bull; Mercedes-Benz Powertrain Management System Testing</div>
    <ul class="bullets">
      <li>Validate powertrain management ECUs for Mercedes-Benz diesel and gasoline engine configurations across multiple variants.</li>
      <li>Develop and execute Python-based automated HIL/SIL test scripts using TraceTronic ECU-TEST, improving execution efficiency by ~30%.</li>
      <li>Perform diagnostic validation using CAN, UDS, OBD-II, and OBDonUDS protocols; simulate networks with CANoe, CANalyzer, INCA, and UDE.</li>
      <li>Spearhead structured failure analysis across signals, ECU communications, and test configurations; apply LLM-assisted workflows to accelerate requirement interpretation and root-cause analysis.</li>
    </ul>
  </div>

  <div class="item">
    <div class="item-head">
      <div>
        <span class="item-title">Embedded Software Engineer</span> &bull; <span class="item-company">GRID RGD</span>
      </div>
      <span class="item-meta">May 2019 – Oct 2021 | Bangalore, India</span>
    </div>
    <div class="item-tech">Embedded C, PIC, 8051 Microcontrollers, GSM, Zigbee Wireless, Power Management</div>
    <ul class="bullets">
      <li>Developed Embedded C logic for GSM/SMS-based remote appliance automation, relay control, and status monitoring.</li>
      <li>Engineered 8051-based monitoring and Zigbee wireless communications for renewable energy switching and power management.</li>
    </ul>
  </div>
</div>

<div class="two-col section">
  <div>
    <div class="section-title">Certifications</div>
    <ul class="bullets">
      <li><strong>Generative AI Mastermind</strong> — OutSkill</li>
      <li><strong>AI Foundation</strong> — Udemy</li>
      <li><strong>n8n Masterclass: AI Automations & Workflows</strong> — Udemy</li>
      <li><strong>Prompt Engineering Frameworks & Methodologies</strong> — Udemy</li>
    </ul>
  </div>
  <div>
    <div class="section-title">Education & Details</div>
    <ul class="bullets">
      <li><strong>Master of Computer Applications (M.C.A)</strong><br>Bharathidasan University | 2024 – 2026</li>
      <li><strong>Languages:</strong> English (Professional), Tamil (Native)</li>
      <li><strong>Mobility:</strong> Open to Worldwide Remote & Visa Sponsorship</li>
    </ul>
  </div>
</div>

</body>
</html>
"""

async def main():
    HTML_PATH.write_text(HTML_CONTENT, encoding="utf-8")
    print(f"Wrote HTML template to {HTML_PATH}")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file:///{HTML_PATH.as_posix()}", wait_until="networkidle")
        await page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"}
        )
        await browser.close()
    print(f"Generated professional PDF resume at {PDF_PATH} ({PDF_PATH.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
