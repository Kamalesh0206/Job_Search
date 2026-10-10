import logging
from typing import Dict, Any, Optional
from profile_manager import ProfileManager

class CoverLetterGenerator:
    def __init__(self, profile_manager: Optional[ProfileManager] = None):
        self.profile = profile_manager or ProfileManager()

    def generate(self, job_title: str, company_name: str, job_description: str = "") -> str:
        template = self.profile.documents.get("default_cover_letter", "")
        if not template:
            template = (
                "Dear Hiring Manager at {company},\n\n"
                "I am thrilled to apply for the position of {title}. "
                "Given my technical background and experience in building robust software solutions, "
                "I am confident in my ability to add immediate value to {company}.\n\n"
                "Thank you for considering my application.\n\n"
                "Best regards,\n{full_name}"
            )

        full_name = self.profile.get_full_name() or "Applicant"
        
        # Safe format
        try:
            letter = template.format(
                company=company_name or "your team",
                title=job_title or "Position",
                full_name=full_name
            )
        except KeyError:
            # Fallback if extra tokens exist
            letter = template.replace("{company}", company_name or "your team")\
                             .replace("{title}", job_title or "Position")\
                             .replace("{full_name}", full_name)
                             
        return letter.strip()

if __name__ == "__main__":
    clg = CoverLetterGenerator()
    letter = clg.generate("Senior AI Software Engineer", "Acme AI Corp")
    print("--- Sample Cover Letter ---")
    print(letter)
