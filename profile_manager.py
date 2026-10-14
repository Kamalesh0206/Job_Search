import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "user_profile.json"
PROFILES_CONFIG_PATH = ROOT / "profiles.json"
CONFIG_PATH = ROOT / "config.json"

class ProfileManager:
    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or PROFILE_PATH
        self.data: Dict[str, Any] = {}
        self.roles_data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load user profile: {e}")
                self.data = {}

        if PROFILES_CONFIG_PATH.exists():
            try:
                with open(PROFILES_CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.roles_data = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load profiles.json: {e}")
                self.roles_data = {}

        return self.data

    @property
    def personal(self) -> Dict[str, str]:
        return self.data.get("personal", {})

    @property
    def links(self) -> Dict[str, str]:
        return self.data.get("links", {})

    @property
    def work_auth(self) -> Dict[str, str]:
        return self.data.get("work_authorization", {})

    @property
    def standard_answers(self) -> Dict[str, str]:
        return self.data.get("standard_answers", {})

    def get_full_name(self) -> str:
        p = self.personal
        first = p.get("first_name", "Kamalesan")
        last = p.get("last_name", "C")
        return f"{first} {last}".strip()

    def get_profile_info(self, profile_id: str) -> Dict[str, Any]:
        norm = "automotive_test_engineer" if "TEST" in profile_id.upper() else "ai_engineer"
        return self.roles_data.get("profiles", {}).get(norm, {})

    def get_resume_path(self, profile_id: str = "AI_ENGINEER", company_name: Optional[str] = None) -> Path:
        from generate_resume_pdf import get_resume_path_for_profile
        return get_resume_path_for_profile(profile_id, company_name)

    def get_standard_answer(self, question_text: str) -> Optional[str]:
        q_lower = question_text.lower()
        answers = self.standard_answers
        for key, val in answers.items():
            if key.lower() in q_lower:
                return val
        return None

if __name__ == "__main__":
    pm = ProfileManager()
    print("Full Name:", pm.get_full_name())
    print("AI Resume:", pm.get_resume_path("AI_ENGINEER"))
    print("Test Resume:", pm.get_resume_path("TEST_ENGINEER"))
