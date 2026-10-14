import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "generated_documents"

class CoverLetterGenerator:
    def __init__(self):
        self.candidate_name = "Kamalesan C"
        self.email = "kamaleshcai686@gmail.com"
        self.phone = "+91 7305131264"
        self.location = "Coimbatore, Tamil Nadu, India"
        self.experience_years = "7.4"

    def generate(
        self,
        job_title: str,
        company_name: str,
        job_description: str = "",
        profile_id: str = "AI_ENGINEER",
        save_to_disk: bool = True
    ) -> Dict[str, str]:
        """
        Generates a tailored, factually accurate ATS cover letter based on role profile and job details.
        Saves document into generated_documents/{PROFILE_ID}/{Company}_{JobTitle}_Cover_Letter.txt
        """
        company = company_name.strip() if company_name else "Hiring Team"
        title = job_title.strip() if job_title else "Engineering Role"
        norm_profile = "TEST_ENGINEER" if "TEST" in str(profile_id).upper() else "AI_ENGINEER"

        if norm_profile == "TEST_ENGINEER":
            body = (
                f"Dear Hiring Manager,\n\n"
                f"I am writing to express my strong interest in the {title} position at {company}. "
                f"With {self.experience_years} years of specialized engineering experience in automotive ECU validation, "
                f"Hardware-in-the-Loop (HIL) and Software-in-the-Loop (SIL) testing, and Python-based test automation, "
                f"I bring extensive domain expertise in verifying mission-critical automotive software systems.\n\n"
                f"Currently working at Capgemini Technology Services in collaboration with Bosch Global Software Technologies, "
                f"I have contributed extensively to Mercedes-Benz powertrain ECU validation programs. My core technical capabilities "
                f"include automated test creation in TraceTronic ECU-TEST, hardware bench integration with dSPACE SCALEXIO and ETAS LABCAR, "
                f"network bus analysis (CAN, LIN, FlexRay, Automotive Ethernet), and UDS (ISO 14229) diagnostic protocol testing with Vector CANoe and ETAS INCA. "
                f"I have developed custom Python automation utilities to parse diagnostic fault codes and generate automated compliance metrics, "
                f"measurably accelerating test cycles.\n\n"
                f"I am enthusiastic about bringing my hands-on validation rigor, test automation framework design skills, and defect-analysis "
                f"depth to the engineering initiatives at {company}.\n\n"
                f"I am based in India and am open to worldwide remote opportunities as well as on-site positions offering international relocation "
                f"and work visa sponsorship.\n\n"
                f"Thank you for your time and consideration. I welcome the opportunity to discuss how my automotive validation background "
                f"aligns with your team's objectives.\n\n"
                f"Sincerely,\n"
                f"{self.candidate_name}\n"
                f"Senior Automotive Test Engineer | HIL/SIL Testing & Python Automation\n"
                f"Email: {self.email} | Phone: {self.phone}"
            )
        else: # AI_ENGINEER
            body = (
                f"Dear Hiring Manager,\n\n"
                f"I am writing to submit my application for the {title} role at {company}. "
                f"With {self.experience_years} years of engineering experience spanning Generative AI applications, "
                f"autonomous AI agent development, and robust Python backend systems, I am excited about the opportunity "
                f"to contribute to high-impact intelligent software at {company}.\n\n"
                f"My recent technical focus centers on production Generative AI architectures, including OpenAI and Google Gemini APIs, "
                f"prompt engineering methodologies, Retrieval-Augmented Generation (RAG) with vector databases, and multi-agent workflow orchestration. "
                f"I have engineered full-stack AI platforms such as EpiAgent PMO (multi-agent project governance and automated risk triage), "
                f"an AI-powered test automation solution generating synthetic validation scripts, and autonomous application workflows using FastAPI, "
                f"PostgreSQL, Docker, and modern React interfaces. This is grounded in a deep software foundation developed at Capgemini "
                f"and Bosch-partnered environments.\n\n"
                f"I am eager to apply my experience in building reliable, human-in-the-loop AI systems to solve challenging technical problems "
                f"and deliver measurable value for {company}.\n\n"
                f"I am open to worldwide remote positions as well as international relocation with work visa sponsorship.\n\n"
                f"Thank you for considering my application. I look forward to the chance to speak with your team.\n\n"
                f"Sincerely,\n"
                f"{self.candidate_name}\n"
                f"AI Engineer | Generative AI, AI Agents & Python Microservices\n"
                f"Email: {self.email} | Phone: {self.phone}"
            )

        saved_path_str = ""
        if save_to_disk:
            target_dir = DOCS_DIR / norm_profile
            target_dir.mkdir(parents=True, exist_ok=True)
            clean_company = re.sub(r"[^\w\s-]", "", company).strip().replace(" ", "_") or "Company"
            clean_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_") or "Role"
            out_file = target_dir / f"{clean_company}_{clean_title}_Cover_Letter.txt"
            out_file.write_text(body, encoding="utf-8")
            saved_path_str = str(out_file)

        return {
            "cover_letter": body,
            "profile_id": norm_profile,
            "file_path": saved_path_str
        }

if __name__ == "__main__":
    clg = CoverLetterGenerator()
    res1 = clg.generate("Generative AI Engineer", "Anthropic", profile_id="AI_ENGINEER")
    print("AI Letter saved to:", res1["file_path"])
    res2 = clg.generate("HIL Test Engineer", "BMW Group", profile_id="TEST_ENGINEER")
    print("Test Letter saved to:", res2["file_path"])
