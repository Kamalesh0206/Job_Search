from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any

@dataclass
class Job:
    source: str = ""
    source_job_id: str = ""
    title: str = ""
    company: str = ""
    country: str = ""
    city: str = ""
    location: str = ""
    work_arrangement: str = "Remote"
    remote_eligibility: str = "Worldwide"
    visa_sponsorship_status: str = "UNKNOWN"
    salary_range: str = ""
    experience_required: str = ""
    required_skills: str = ""
    matched_skills: str = ""
    missing_skills: str = ""
    description: str = ""
    url: str = ""
    posted_date: str = ""
    found_date: str = ""
    last_seen_date: str = ""
    profile_id: str = "AI_ENGINEER"
    role_category: str = "AI_ENGINEER"
    relevance_score: int = 0
    score_explanation: str = ""
    resume_used: str = ""
    cover_letter_path: str = ""
    status: str = "DISCOVERED"
    application_date: str = ""
    recruiter_name: str = ""
    recruiter_contact: str = ""
    follow_up_date: str = ""
    notes: str = ""
    fingerprint: str = ""
    id: Optional[Any] = None

    def __post_init__(self):
        if not self.id and self.source_job_id:
            self.id = self.source_job_id
        if not self.location and (self.city or self.country):
            self.location = f"{self.city}, {self.country}".strip(", ")
        elif self.location and not self.country:
            parts = [p.strip() for p in self.location.split(",") if p.strip()]
            self.city = parts[0] if len(parts) >= 1 else ""
            self.country = parts[-1] if len(parts) >= 2 else self.location

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
