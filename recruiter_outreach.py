"""
Recruiter Outreach Generator
Generates personalized outreach messages for recruiters, hiring managers, and LinkedIn connections
tailored to Kamalesan C's AI Engineer background.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "user_profile.json"

class RecruiterOutreach:
    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or PROFILE_PATH
        with open(self.profile_path, "r", encoding="utf-8") as f:
            self.profile = json.load(f)

        self.candidate_name = f"{self.profile['personal']['first_name']} {self.profile['personal']['last_name']}".strip()
        self.email = self.profile['personal']['email']
        self.phone = self.profile['personal']['phone']
        self.linkedin = self.profile['links']['linkedin']
        self.github = self.profile['links']['github']
        self.yoe = self.profile['preferences']['years_of_experience']

    def generate_linkedin_connection_note(self, recruiter_name: str = "Hiring Manager", company: str = "your team") -> str:
        """Generates a concise note (under 300 chars) for LinkedIn connection requests."""
        return (
            f"Hi {recruiter_name}, I saw your engineering work at {company}. "
            f"With {self.yoe}y experience building GenAI agents, LLM pipelines & Python backends, "
            f"I'd love to connect and follow AI opportunities at {company}!"
        )[:300]

    def generate_recruiter_inmail(self, recruiter_name: str = "Recruiter", company: str = "your team", role_title: str = "AI Engineer") -> str:
        """Generates a high-converting direct message / InMail to recruiters."""
        return f"""Hi {recruiter_name},

I hope this message finds you well.

I came across open {role_title} opportunities at {company} and wanted to reach out directly.

With {self.yoe} years of engineering experience spanning Generative AI applications, autonomous agents, Python backend architecture (FastAPI, PostgreSQL, Redis, Docker), and automated system validation, I specialize in building production-ready AI workflows that deliver measurable results.

Highlights of what I bring:
• Production GenAI & Agent Workflows: Designed end-to-end agents with human-in-the-loop validation, tool calling/MCP, and Gemini/OpenAI integrations (e.g., EpiAgent PMO, AI SIL Test Automation Platform).
• Robust Backend Systems: Scalable APIs in FastAPI/Python, async pipelines, and Dockerized cloud deployments.
• Strong Engineering Foundation: 7.4 years delivering complex automation, systems testing, and reliability at scale.

I would welcome the chance to discuss how my skillset fits current or upcoming AI openings at {company}.

My LinkedIn Profile: {self.linkedin}
GitHub Projects: {self.github}
Email: {self.email} | Phone: {self.phone}

Thank you for your time, and I look forward to connecting!

Best regards,
{self.candidate_name}
AI Engineer | Generative AI | AI Agents | Python Automation"""

    def generate_cold_email(self, hiring_manager_name: str = "Hiring Manager", company: str = "your company", role_title: str = "AI Engineer") -> Dict[str, str]:
        """Generates a complete email with subject line and body for hiring managers."""
        subject = f"Application / Inquiry: {role_title} – {self.candidate_name} ({self.yoe}+ Years | GenAI, AI Agents & Python)"
        body = f"""Dear {hiring_manager_name},

I hope your week is going well.

I am reaching out to express my keen interest in joining {company} as a {role_title}. Having tracked {company}'s tech innovations, I believe my background in Generative AI engineering, autonomous agents, and Python backend systems can add immediate value to your engineering team.

A snapshot of my experience:
• 7.4 Years Engineering Track Record: Extensive background building production Python automation, software systems, and AI agent architectures.
• GenAI & Agentic Systems: Hands-on implementation of multi-agent workflows, Gemini & OpenAI APIs, Model Context Protocol (MCP), prompt engineering, and deterministic human-in-the-loop validation.
• Production Architecture: Built and deployed services with FastAPI, PostgreSQL, SQLAlchemy, Redis, Docker, and Google Cloud Run (including projects like EpiAgent PMO and automotive AI SIL test platforms).
• Work Authorization: Open to worldwide remote opportunities and international relocation with visa sponsorship.

Please find my resume attached. You can also view my live profile and code repositories here:
• LinkedIn: {self.linkedin}
• GitHub: {self.github}

Would you be open to a brief 10-15 minute chat next week to discuss how I can contribute to {company}'s AI initiatives?

Thank you for your time and consideration.

Warm regards,

{self.candidate_name}
Email: {self.email}
Phone: {self.phone}
Coimbatore, India (Open to Remote / Relocation)"""
        return {"subject": subject, "body": body}

    def generate_followup(self, recruiter_name: str = "Hiring Team", company: str = "your company", role_title: str = "AI Engineer") -> str:
        """Generates a polite follow-up message 5-7 days after application."""
        return f"""Hi {recruiter_name},

I hope you're having a great week!

I recently submitted my application for the {role_title} position at {company} and wanted to follow up. I remain very enthusiastic about the opportunity to contribute my {self.yoe} years of GenAI, agentic workflow, and Python backend experience to your team.

If you need any additional portfolio samples or details from my end, please feel free to reach out.

LinkedIn: {self.linkedin}
Email: {self.email}

Thank you again for your time and review!

Best regards,
{self.candidate_name}"""

if __name__ == "__main__":
    outreach = RecruiterOutreach()
    print("=== LINKEDIN CONNECTION NOTE (<=300 chars) ===")
    print(outreach.generate_linkedin_connection_note("Sarah", "OpenAI Partner"))
    print("\n=== RECRUITER INMAIL ===")
    print(outreach.generate_recruiter_inmail("Sarah", "Anthropic Client", "Senior AI Engineer"))
