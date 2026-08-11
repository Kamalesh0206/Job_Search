from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Job:
    source: str
    source_job_id: str
    title: str
    company: str = ""
    location: str = ""
    posted_date: str = ""
    url: str = ""
    description: str = ""
    role_category: str = ""
    found_date: str = ""
    status: str = "New"

    def to_dict(self):
        return asdict(self)
