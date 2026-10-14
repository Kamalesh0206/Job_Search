import re
from typing import Dict, Any, List, Tuple, Optional

# Keywords that confirm visa sponsorship or relocation
CONFIRMED_SPONSORSHIP_TERMS = [
    "visa sponsorship provided", "visa sponsorship available", "willing to sponsor",
    "sponsorship provided", "relocation assistance", "relocation support",
    "international relocation", "visa support", "can sponsor", "relocation package"
]

# Keywords that explicitly deny sponsorship
DENIED_SPONSORSHIP_TERMS = [
    "no visa sponsorship", "must be a us citizen", "us citizenship required",
    "active security clearance", "secret clearance", "top secret", "no sponsorship",
    "must have legal right to work without sponsorship", "not able to sponsor",
    "citizenship required", "gc or us citizen only"
]

# Remote / work arrangement terms
REMOTE_TERMS = ["remote", "work from home", "wfh", "telecommute", "anywhere in the world", "fully remote"]
HYBRID_TERMS = ["hybrid", "flexible work", "partial remote"]
ONSITE_TERMS = ["on-site", "onsite", "in-office", "in office", "relocate to"]

def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\u2013\u2014/_|(),:\-\.]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def calculate_relevance(
    job: Dict[str, Any],
    profile_id: str,
    config: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes a 0 to 100 explainable relevance score according to configured weights:
      - Technical skills match: 35 pts
      - Job responsibilities match: 25 pts
      - Experience match: 15 pts
      - Job title relevance: 10 pts
      - Location & work arrangement: 10 pts
      - Sponsorship preference match: 5 pts
    """
    weights = config.get("relevance_weights", {
        "technical_skills": 35,
        "responsibilities": 25,
        "experience": 15,
        "title_relevance": 10,
        "location_work_arrangement": 10,
        "sponsorship_preference": 5
    })

    title = job.get("title", "")
    description = job.get("description", "")
    location = job.get("location", "") or job.get("country", "")
    combined = (title + " " + description).lower()
    title_n = normalize(title)
    desc_n = normalize(description)

    profile_conf = config.get("profiles", {}).get(profile_id, {})
    if not profile_conf and profile_id == "BOTH":
        profile_conf = config.get("profiles", {}).get("AI_ENGINEER", {})

    target_skills = profile_conf.get("technical_skills", [])
    target_titles = profile_conf.get("target_titles", [])
    candidate_exp = float(profile_conf.get("experience_years", 7.4))

    # 1. Technical Skills Match (Max 35)
    matched_skills = []
    missing_skills = []
    for skill in target_skills:
        s_norm = normalize(skill)
        pattern = r"\b" + re.escape(s_norm) + r"\b"
        if re.search(pattern, desc_n) or re.search(pattern, title_n):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    skills_ratio = len(matched_skills) / max(len(target_skills), 1)
    # Give full points if candidate has >= 40% of target skills represented in job, scaling proportionally
    skill_pts = min(weights["technical_skills"], int((len(matched_skills) / 6.0) * weights["technical_skills"]))

    # 2. Responsibilities / Domain Depth Match (Max 25)
    resp_pts = 0
    if profile_id == "AI_ENGINEER":
        domain_anchors = ["llm", "generative ai", "ai agent", "prompt engineering", "fastapi", "docker", "rag", "rest api"]
    else: # TEST_ENGINEER
        domain_anchors = ["hil", "sil", "ecu", "ecu-test", "canoe", "inca", "dspace", "diagnostics", "uds", "obd"]

    anchors_hit = sum(1 for a in domain_anchors if a in combined)
    resp_ratio = anchors_hit / len(domain_anchors)
    resp_pts = min(weights["responsibilities"], int(resp_ratio * 2.5 * weights["responsibilities"]))

    # 3. Experience Match (Max 15)
    # Check if job requires specific years of experience
    exp_pts = weights["experience"]
    exp_matches = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience", combined)
    required_years = None
    if exp_matches:
        try:
            required_years = max([int(x) for x in exp_matches if int(x) <= 25])
            if required_years > candidate_exp + 3: # e.g. asks for 11+ years
                exp_pts = int(weights["experience"] * 0.5)
            elif required_years <= candidate_exp + 2: # 1-9 years: great fit
                exp_pts = weights["experience"]
        except Exception:
            exp_pts = weights["experience"]

    # 4. Job Title Relevance (Max 10)
    title_pts = 0
    for t in target_titles:
        t_norm = normalize(t)
        if t_norm in title_n:
            title_pts = weights["title_relevance"]
            break
        elif any(word in title_n for word in t_norm.split() if len(word) > 3):
            title_pts = max(title_pts, int(weights["title_relevance"] * 0.6))

    # 5. Location & Work Arrangement (Max 10)
    loc_pts = 0
    is_remote = any(r in combined for r in REMOTE_TERMS) or "remote" in location.lower()
    is_hybrid = any(h in combined for h in HYBRID_TERMS)
    
    preferred_countries = [c.lower() for c in config.get("worldwide_locations", {}).get("preferred_countries", [])]
    is_preferred_country = any(c in location.lower() for c in preferred_countries)

    if is_remote:
        loc_pts = weights["location_work_arrangement"]
    elif is_preferred_country:
        loc_pts = weights["location_work_arrangement"] if is_hybrid else int(weights["location_work_arrangement"] * 0.8)
    else:
        loc_pts = int(weights["location_work_arrangement"] * 0.5)

    # 6. Visa Sponsorship Match (Max 5)
    sponsorship_pts = 0
    visa_status = "UNKNOWN"

    has_confirmed_sponsorship = any(term in combined for term in CONFIRMED_SPONSORSHIP_TERMS)
    has_denied_sponsorship = any(term in combined for term in DENIED_SPONSORSHIP_TERMS)

    if has_confirmed_sponsorship:
        visa_status = "CONFIRMED"
        sponsorship_pts = weights["sponsorship_preference"]
    elif has_denied_sponsorship:
        visa_status = "NOT_OFFERED"
        sponsorship_pts = 0
    else:
        visa_status = "UNKNOWN"
        # Remote jobs or international locations without denial get neutral score
        sponsorship_pts = int(weights["sponsorship_preference"] * 0.6) if is_remote else int(weights["sponsorship_preference"] * 0.4)

    # Calculate Total Score
    total_score = skill_pts + resp_pts + exp_pts + title_pts + loc_pts + sponsorship_pts

    # Penalties
    work_auth_penalty = 0
    if has_denied_sponsorship and not is_remote:
        work_auth_penalty = 25 # Strict penalty for on-site positions requiring existing local work permit
        total_score = max(0, total_score - work_auth_penalty)

    total_score = max(5, min(100, total_score))

    # Generate Explainable Summary
    explanation_parts = [
        f"Skills ({skill_pts}/{weights['technical_skills']}): Matched {len(matched_skills)} core skills",
        f"Responsibilities ({resp_pts}/{weights['responsibilities']})",
        f"Experience ({exp_pts}/{weights['experience']}): Candidate 7.4y vs req {required_years or 'Flexible'}y",
        f"Title ({title_pts}/{weights['title_relevance']})",
        f"Location ({loc_pts}/{weights['location_work_arrangement']}): {'Remote' if is_remote else location or 'Global'}",
        f"Sponsorship ({sponsorship_pts}/{weights['sponsorship_preference']}): {visa_status}"
    ]
    if work_auth_penalty > 0:
        explanation_parts.append(f"Penalty: -{work_auth_penalty} (On-site work authorization required)")

    return {
        "score": total_score,
        "visa_sponsorship_status": visa_status,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:10],
        "work_arrangement": "Remote" if is_remote else ("Hybrid" if is_hybrid else "On-site"),
        "explanation": " | ".join(explanation_parts),
        "breakdown": {
            "skills": skill_pts,
            "responsibilities": resp_pts,
            "experience": exp_pts,
            "title": title_pts,
            "location": loc_pts,
            "sponsorship": sponsorship_pts,
            "penalty": work_auth_penalty
        }
    }
