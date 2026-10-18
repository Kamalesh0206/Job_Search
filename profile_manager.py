import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "user_profile.json"
PROFILES_CONFIG_PATH = ROOT / "profiles.json"
CONFIG_PATH = ROOT / "config.json"

logger = logging.getLogger(__name__)

CANONICAL_DEFAULTS = {
    "AI_ENGINEER": {
        "profile_id": "AI_ENGINEER",
        "name": "Kamalesan C",
        "display_title": "AI Engineer",
        "experience_years": "7.4",
        "location": "Coimbatore, India",
        "phone": "+91 7305131264",
        "email": "kamaleshcai686@gmail.com",
        "linkedin": "https://www.linkedin.com/in/kamalesan-c-546646442",
        "github": "https://github.com/Kamalesh0206",
        "auto_apply_enabled": False,
        "match_threshold": 70,
        "target_roles": [
            "AI Engineer",
            "Generative AI Engineer",
            "AI Agent Developer",
            "AI Agent Engineer",
            "LLM Engineer",
            "Applied AI Engineer",
            "AI Automation Engineer",
            "Python AI Developer",
            "Python AI Engineer",
            "AI Application Engineer",
            "Senior AI Engineer",
            "Junior AI Engineer",
            "GenAI Engineer",
            "Machine Learning Engineer",
            "ML Engineer",
            "Agentic AI Engineer"
        ],
        "technical_skills": [
            "Python",
            "Generative AI",
            "Gemini API",
            "OpenAI API",
            "LLM applications",
            "AI agents",
            "Prompt engineering",
            "FastAPI",
            "REST APIs",
            "RAG",
            "Vector databases",
            "PostgreSQL",
            "SQLAlchemy",
            "Redis",
            "Docker",
            "React",
            "n8n",
            "MCP",
            "Git",
            "GitHub",
            "Cloud deployment"
        ],
        "skill_weights": {
            "Python": 1.0,
            "Generative AI": 1.2,
            "Gemini API": 1.0,
            "OpenAI API": 1.0,
            "LLM applications": 1.2,
            "AI agents": 1.2,
            "Prompt engineering": 1.0,
            "FastAPI": 1.0,
            "REST APIs": 0.9,
            "RAG": 1.1,
            "Vector databases": 1.0,
            "PostgreSQL": 0.8,
            "Docker": 0.9
        },
        "exclude_terms": [
            "intern",
            "internship",
            "sales",
            "account executive",
            "recruiter",
            "human resources",
            "civil",
            "mechanical hardware",
            "marketing manager"
        ],
        "priority_projects": [
            "EpiAgent PMO — AI Project Governance & Risk Management Platform",
            "AI-Powered SIL Test Automation Platform",
            "Automation Job Applying Agent",
            "AI Instagram Publisher Agent",
            "HyGreen — Smart Grocery / E-commerce Application"
        ]
    },
    "TEST_ENGINEER": {
        "profile_id": "TEST_ENGINEER",
        "name": "Kamalesan C",
        "display_title": "Test Engineer",
        "experience_years": "7.4",
        "location": "Coimbatore, Tamil Nadu, India",
        "phone": "+91 98436 19970",
        "email": "softkamalesh@gmail.com",
        "linkedin": "https://www.linkedin.com/in/kamalesh-chinnathambi-62b952299",
        "github": "",
        "auto_apply_enabled": False,
        "match_threshold": 70,
        "target_roles": [
            "Test Engineer",
            "Senior Test Engineer",
            "HIL Test Engineer",
            "SIL Test Engineer",
            "ECU Validation Engineer",
            "Automotive Test Engineer",
            "Test Automation Engineer",
            "Python Test Automation Engineer",
            "Embedded Software Test Engineer",
            "Automotive System Validation Engineer",
            "Verification and Validation Engineer",
            "V&V Engineer",
            "Software Test Engineer",
            "System Test Engineer",
            "Powertrain Validation Engineer",
            "Embedded Test Engineer"
        ],
        "technical_skills": [
            "HIL testing",
            "SIL testing",
            "ECU validation",
            "Python",
            "ECU-TEST",
            "dSPACE SCALEXIO",
            "ETAS LABCAR",
            "CANoe",
            "CANalyzer",
            "INCA",
            "UDE",
            "CAN",
            "LIN",
            "FlexRay",
            "Ethernet",
            "UDS",
            "OBD-II",
            "OBDonUDS",
            "Embedded C",
            "Regression testing",
            "Diagnostic testing",
            "Requirements-based testing",
            "Root cause analysis"
        ],
        "skill_weights": {
            "HIL testing": 1.2,
            "SIL testing": 1.1,
            "ECU validation": 1.2,
            "Python": 1.0,
            "ECU-TEST": 1.2,
            "dSPACE SCALEXIO": 1.0,
            "ETAS LABCAR": 1.0,
            "CANoe": 1.1,
            "CANalyzer": 1.0,
            "INCA": 1.0,
            "UDS": 1.1,
            "Diagnostic testing": 1.0
        },
        "exclude_terms": [
            "intern",
            "internship",
            "civil",
            "structural",
            "chemical",
            "biomedical",
            "nursing",
            "clinical",
            "sales",
            "account executive",
            "recruiter",
            "human resources",
            "marketing"
        ],
        "priority_projects": [
            "Mercedes-Benz Powertrain Testing (Capgemini & Bosch)",
            "Automotive HIL/SIL Test Automation with ECU-TEST",
            "Automotive Diagnostics (UDS, OBD-II, CANoe)",
            "Python Automotive Test Automation Frameworks"
        ]
    }
}

class ProfileManager:
    def __init__(self, profile_id: Optional[str] = "AI_ENGINEER"):
        self.profiles: Dict[str, Any] = {}
        self.active_profile_id = self.normalize_profile_id(profile_id)
        self.load()

    @property
    def personal(self) -> Dict[str, str]:
        p = self.get_personal_info(self.active_profile_id)
        p["first_name"] = "Kamalesan"
        p["last_name"] = "C"
        return p

    @property
    def links(self) -> Dict[str, str]:
        p = self.get_personal_info(self.active_profile_id)
        return {
            "linkedin": p.get("linkedin", ""),
            "github": p.get("github", ""),
            "portfolio": p.get("github", "") or p.get("linkedin", ""),
            "website": p.get("linkedin", "")
        }

    def get_full_name(self) -> str:
        return self.personal.get("name", "Kamalesan C")

    def get_resume_absolute_path(self) -> Path:
        return self.get_resume_path(self.active_profile_id)

    def normalize_profile_id(self, profile_id: Optional[str]) -> str:
        if not profile_id:
            return "AI_ENGINEER"
        p_up = str(profile_id).upper().strip()
        if "TEST" in p_up:
            return "TEST_ENGINEER"
        return "AI_ENGINEER"

    def load(self):
        # Load from profiles.json if exists
        loaded = {}
        if PROFILES_CONFIG_PATH.exists():
            try:
                with open(PROFILES_CONFIG_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {PROFILES_CONFIG_PATH}: {e}")

        # Ensure canonical structures exist
        self.profiles["AI_ENGINEER"] = dict(CANONICAL_DEFAULTS["AI_ENGINEER"])
        self.profiles["TEST_ENGINEER"] = dict(CANONICAL_DEFAULTS["TEST_ENGINEER"])

        for pid in ("AI_ENGINEER", "TEST_ENGINEER"):
            if pid in loaded and isinstance(loaded[pid], dict):
                self.profiles[pid].update(loaded[pid])

    def save(self):
        try:
            with open(PROFILES_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save {PROFILES_CONFIG_PATH}: {e}")

        # Also synchronize config.json
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)

                config.setdefault("profiles", {})
                for pid in ("AI_ENGINEER", "TEST_ENGINEER"):
                    p_data = self.profiles[pid]
                    config["profiles"].setdefault(pid, {})
                    config["profiles"][pid]["personal"] = {
                        "name": p_data.get("name", "Kamalesan C"),
                        "location": p_data.get("location", ""),
                        "phone": p_data.get("phone", ""),
                        "email": p_data.get("email", ""),
                        "linkedin": p_data.get("linkedin", ""),
                        "github": p_data.get("github", "")
                    }
                    config["profiles"][pid]["target_titles"] = p_data.get("target_roles", [])
                    config["profiles"][pid]["technical_skills"] = p_data.get("technical_skills", [])
                    config["profiles"][pid]["skill_weights"] = p_data.get("skill_weights", {})
                    config["profiles"][pid]["exclude_terms"] = p_data.get("exclude_terms", [])
                    config["profiles"][pid]["auto_apply_enabled"] = p_data.get("auto_apply_enabled", True)
                    config["profiles"][pid]["match_threshold"] = p_data.get("match_threshold", 70)

                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Failed to sync {CONFIG_PATH}: {e}")

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        norm = self.normalize_profile_id(profile_id)
        return self.profiles.get(norm, self.profiles["AI_ENGINEER"])

    def get_personal_info(self, profile_id: str) -> Dict[str, str]:
        p = self.get_profile(profile_id)
        return {
            "name": p.get("name", "Kamalesan C"),
            "display_title": p.get("display_title", "Engineer"),
            "experience_years": str(p.get("experience_years", "7.4")),
            "location": p.get("location", ""),
            "phone": p.get("phone", ""),
            "email": p.get("email", ""),
            "linkedin": p.get("linkedin", ""),
            "github": p.get("github", "") if profile_id == "AI_ENGINEER" or p.get("github") else ""
        }

    def get_all_profiles(self) -> Dict[str, Any]:
        return {
            "AI_ENGINEER": self.get_profile("AI_ENGINEER"),
            "TEST_ENGINEER": self.get_profile("TEST_ENGINEER")
        }

    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        norm = self.normalize_profile_id(profile_id)
        current = self.profiles[norm]

        # Update contact / personal info
        if "personal" in updates and isinstance(updates["personal"], dict):
            p_in = updates["personal"]
            for field in ("name", "location", "phone", "email", "linkedin", "github"):
                if field in p_in:
                    current[field] = str(p_in[field]).strip()

        for field in ("name", "location", "phone", "email", "linkedin", "github"):
            if field in updates:
                current[field] = str(updates[field]).strip()

        # Update skills (deduplicate, remove empty)
        if "technical_skills" in updates:
            raw_skills = updates["technical_skills"]
            clean_skills = []
            for s in raw_skills:
                s_str = str(s).strip()
                if s_str and s_str not in clean_skills:
                    clean_skills.append(s_str)
            current["technical_skills"] = clean_skills

        # Update job titles
        if "target_roles" in updates:
            raw_roles = updates["target_roles"]
            clean_roles = []
            for r in raw_roles:
                r_str = str(r).strip()
                if r_str and r_str not in clean_roles:
                    clean_roles.append(r_str)
            current["target_roles"] = clean_roles

        # Update excluded terms
        if "exclude_terms" in updates:
            raw_ex = updates["exclude_terms"]
            clean_ex = []
            for x in raw_ex:
                x_str = str(x).strip().lower()
                if x_str and x_str not in clean_ex:
                    clean_ex.append(x_str)
            current["exclude_terms"] = clean_ex

        # Update skill weights
        if "skill_weights" in updates and isinstance(updates["skill_weights"], dict):
            current["skill_weights"] = {
                str(k).strip(): float(v)
                for k, v in updates["skill_weights"].items()
                if str(k).strip()
            }

        # Update auto-apply toggle and threshold
        if "auto_apply_enabled" in updates:
            current["auto_apply_enabled"] = bool(updates["auto_apply_enabled"])

        if "match_threshold" in updates:
            try:
                thresh = int(updates["match_threshold"])
                current["match_threshold"] = max(50, min(95, thresh))
            except (ValueError, TypeError):
                pass

        self.save()
        return current

    def reset_to_defaults(self, profile_id: str) -> Dict[str, Any]:
        norm = self.normalize_profile_id(profile_id)
        self.profiles[norm] = dict(CANONICAL_DEFAULTS[norm])
        self.save()
        return self.profiles[norm]

    def get_resume_path(self, profile_id: str, company_name: Optional[str] = None) -> Path:
        from generate_resume_pdf import get_resume_path_for_profile
        return get_resume_path_for_profile(profile_id, company_name)

    @property
    def data(self) -> Dict[str, Any]:
        # Backwards compatibility accessor
        return {
            "personal": self.get_personal_info("AI_ENGINEER"),
            "profiles": self.get_all_profiles()
        }

if __name__ == "__main__":
    pm = ProfileManager()
    ai_p = pm.get_personal_info("AI_ENGINEER")
    test_p = pm.get_personal_info("TEST_ENGINEER")
    print("AI Profile Info:", ai_p)
    print("Test Profile Info:", test_p)
    assert ai_p["email"] == "kamaleshcai686@gmail.com"
    assert test_p["email"] == "softkamalesh@gmail.com"
    assert test_p["phone"] == "+91 98436 19970"
    assert test_p["github"] == ""
    print("[PASS] ProfileManager dual-profile separation verified.")
