import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "user_profile.json"

class ProfileManager:
    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or PROFILE_PATH
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        if not self.profile_path.exists():
            logging.warning(f"Profile file not found at {self.profile_path}")
            self.data = {}
            return self.data

        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            logging.info(f"Loaded user profile from {self.profile_path}")
        except Exception as e:
            logging.error(f"Failed to load user profile: {e}")
            self.data = {}
        return self.data

    @property
    def personal(self) -> Dict[str, str]:
        return self.data.get("personal", {})


    @property
    def links(self) -> Dict[str, str]:
        return self.data.get("links", {})

    @property
    def documents(self) -> Dict[str, str]:
        return self.data.get("documents", {})

    @property
    def work_auth(self) -> Dict[str, str]:
        return self.data.get("work_authorization", {})

    @property
    def standard_answers(self) -> Dict[str, str]:
        return self.data.get("standard_answers", {})

    def get_full_name(self) -> str:
        p = self.personal
        first = p.get("first_name", "")
        last = p.get("last_name", "")
        return f"{first} {last}".strip()

    def get_resume_absolute_path(self) -> Optional[Path]:
        res_rel = self.documents.get("resume_path", "")
        if not res_rel:
            return None
        res_p = Path(res_rel)
        if not res_p.is_absolute():
            res_p = self.profile_path.parent / res_p
        return res_p if res_p.exists() else None

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
    print("Resume Path:", pm.get_resume_absolute_path())
