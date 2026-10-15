import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from profile_manager import ProfileManager

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "generated_documents"

class CoverLetterGenerator:
    def __init__(self, profile_manager: Optional[ProfileManager] = None):
        self.pm = profile_manager or ProfileManager()

    def generate(
        self,
        job_title: str,
        company_name: str,
        job_description: str = "",
        profile_id: str = "AI_ENGINEER",
        save_to_disk: bool = True
    ) -> Dict[str, str]:
        """
        Generates a tailored, ATS-compliant international cover letter using profile-specific
        contact details, current date, actual job title & company name, and domain experience.
        Saves to generated_documents/{PROFILE_ID}/{Company}_{JobTitle}_Cover_Letter_{YYYYMMDD}.txt
        """
        norm_profile = self.pm.normalize_profile_id(profile_id)
        info = self.pm.get_personal_info(norm_profile)
        p_data = self.pm.get_profile(norm_profile)

        company = company_name.strip() if company_name else "Target Company"
        title = job_title.strip() if job_title else ("AI Engineer" if norm_profile == "AI_ENGINEER" else "Test Engineer")

        # Dynamic current date
        current_date_str = datetime.now().strftime("%B %d, %Y")
        today_stamp = datetime.now().strftime("%Y%m%d")

        name = info.get("name", "Kamalesan C")
        location = info.get("location", "Coimbatore, India")
        phone = info.get("phone", "")
        email = info.get("email", "")
        linkedin = info.get("linkedin", "")
        github = info.get("github", "")
        exp_years = info.get("experience_years", "7.4")

        subject_line = f"Application for {title} Position – {company}"

        # Contact block
        contact_lines = [name, location, f"Phone: {phone}", f"Email: {email}"]
        if linkedin:
            contact_lines.append(f"LinkedIn: {linkedin}")
        if github:
            contact_lines.append(f"GitHub: {github}")

        contact_header = "\n".join(contact_lines)

        if norm_profile == "TEST_ENGINEER":
            body = f"""{contact_header}

Date: {current_date_str}

Hiring Team
{company}

Subject: {subject_line}

Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. With {exp_years} years of specialized engineering experience in automotive ECU validation, Hardware-in-the-Loop (HIL) and Software-in-the-Loop (SIL) testing, and Python-based test automation frameworks, I bring extensive domain capability in verifying mission-critical automotive software systems.

In my recent work at Capgemini Technology Services in strategic collaboration with Bosch Global Software Technologies, I have contributed extensively to Mercedes-Benz powertrain ECU validation programs. My core technical capabilities include:
- Automated test case creation, execution, and defect triage utilizing TraceTronic ECU-TEST.
- Test bench hardware integration and signal conditioning with dSPACE SCALEXIO and ETAS LABCAR.
- Deep automotive network bus analysis across CAN, LIN, FlexRay, and Automotive Ethernet.
- Comprehensive diagnostic protocol testing using UDS (ISO 14229) and OBD-II with Vector CANoe and ETAS INCA.
- Developing customized Python automation utilities to parse diagnostic trouble codes (DTCs) and automate regression suites.

I am enthusiastic about applying my validation rigor, automation architecture knowledge, and defect root-cause analysis depth to the engineering initiatives at {company}.

I am based in India and actively open to international relocation with work visa sponsorship, as well as worldwide remote work opportunities.

Thank you for your time and consideration. I welcome the opportunity to discuss how my automotive validation background aligns with your team's goals.

Sincerely,

{name}
Test Engineer | HIL/SIL Testing, ECU Validation & Python Automation
Email: {email} | Phone: {phone}
"""
        else: # AI_ENGINEER
            body = f"""{contact_header}

Date: {current_date_str}

Hiring Team
{company}

Subject: {subject_line}

Dear Hiring Manager,

I am writing to submit my application for the {title} position at {company}. With {exp_years} years of engineering experience spanning production Generative AI applications, autonomous AI agent development, and scalable Python backend architectures, I am excited about the opportunity to build high-impact intelligent software for {company}.

My technical expertise centers on state-of-the-art Generative AI systems and multi-agent workflows, including:
- Production LLM applications utilizing OpenAI API and Google Gemini API with advanced prompt engineering.
- Retrieval-Augmented Generation (RAG) architectures with vector databases and semantic search.
- Engineering end-to-end platforms including EpiAgent PMO (multi-agent project governance and automated risk triage) and AI-powered synthetic test automation platforms.
- High-performance asynchronous microservices with FastAPI, REST APIs, PostgreSQL, Redis, and Docker.
- Designing human-in-the-loop interfaces and enterprise AI workflows that guarantee safety and measurable business value.

I am eager to apply my practical experience in building reliable, autonomous AI agents to solve demanding technical problems and drive product innovation at {company}.

I am open to worldwide remote opportunities as well as international relocation with work visa sponsorship.

Thank you for your consideration. I look forward to speaking with your team about how my skills align with your engineering objectives.

Sincerely,

{name}
AI Engineer | Generative AI, AI Agents & Python Microservices
Email: {email} | Phone: {phone}
"""

        saved_path_str = ""
        if save_to_disk:
            target_dir = DOCS_DIR / norm_profile
            target_dir.mkdir(parents=True, exist_ok=True)
            clean_company = re.sub(r"[^\w\s-]", "", company).strip().replace(" ", "_") or "Company"
            clean_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_") or "Role"
            out_file = target_dir / f"{clean_company}_{clean_title}_Cover_Letter_{today_stamp}.txt"
            out_file.write_text(body.strip(), encoding="utf-8")
            saved_path_str = str(out_file)

        return {
            "cover_letter": body.strip(),
            "profile_id": norm_profile,
            "subject": subject_line,
            "date": current_date_str,
            "file_path": saved_path_str
        }

if __name__ == "__main__":
    clg = CoverLetterGenerator()
    res_ai = clg.generate("Generative AI Engineer", "Anthropic", profile_id="AI_ENGINEER")
    print("AI Subject:", res_ai["subject"])
    print("AI Date:", res_ai["date"])
    print("AI Letter saved to:", res_ai["file_path"])
    assert "kamaleshcai686@gmail.com" in res_ai["cover_letter"]
    assert "https://github.com/Kamalesh0206" in res_ai["cover_letter"]

    res_test = clg.generate("HIL Test Engineer", "BMW Group", profile_id="TEST_ENGINEER")
    print("Test Subject:", res_test["subject"])
    print("Test Date:", res_test["date"])
    print("Test Letter saved to:", res_test["file_path"])
    assert "softkamalesh@gmail.com" in res_test["cover_letter"]
    assert "+91 98436 19970" in res_test["cover_letter"]
    assert "https://github.com/Kamalesh0206" not in res_test["cover_letter"]
    print("[PASS] CoverLetterGenerator dual-profile tests passed.")
