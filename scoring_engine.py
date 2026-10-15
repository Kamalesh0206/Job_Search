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

# Skill equivalence mapping for semantic normalization
SKILL_EQUIVALENCE = {
    "large language models": "llm",
    "large language model": "llm",
    "llms": "llm",
    "llm applications": "llm",
    "llm": "llm",
    "generative ai": "generative ai",
    "genai": "generative ai",
    "ai agents": "ai agents",
    "ai agent": "ai agents",
    "agentic ai": "ai agents",
    "hardware-in-the-loop": "hil testing",
    "hardware in the loop": "hil testing",
    "hil": "hil testing",
    "hil testing": "hil testing",
    "software-in-the-loop": "sil testing",
    "software in the loop": "sil testing",
    "sil": "sil testing",
    "sil testing": "sil testing",
    "ecu-test": "ecu-test",
    "ecu test": "ecu-test",
    "tracetronic": "ecu-test",
    "tracetronic ecu-test": "ecu-test",
    "vector canoe": "canoe",
    "canoe": "canoe",
    "canalyzer": "canalyzer",
    "vector canalyzer": "canalyzer",
    "etas inca": "inca",
    "inca": "inca",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "rag": "rag",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
    "vector databases": "vector databases",
    "vector database": "vector databases",
    "vector db": "vector databases",
    "rest apis": "rest apis",
    "rest api": "rest apis",
    "restful apis": "rest apis",
    "prompt engineering": "prompt engineering",
    "prompting": "prompt engineering",
    "uds": "uds",
    "iso 14229": "uds",
    "obd-ii": "obd-ii",
    "obd2": "obd-ii",
    "obd ii": "obd-ii",
    "obdonuds": "obdonuds",
    "dspace scalexio": "dspace scalexio",
    "scalexio": "dspace scalexio",
    "etas labcar": "etas labcar",
    "labcar": "etas labcar",
    "can": "can",
    "can bus": "can",
    "lin": "lin",
    "lin bus": "lin",
    "flexray": "flexray"
}

MANDATORY_DISQUALIFIERS = [
    ("Active Security Clearance Required", [
        "active secret clearance", "active top secret", "secret clearance required",
        "must hold secret clearance", "ts/sci", "polygraph required", "top secret clearance"
    ]),
    ("US Citizenship Required without Sponsorship", [
        "must be a us citizen", "us citizenship required", "gc or us citizen only",
        "only us citizens", "no visa sponsorship", "must be us citizen"
    ])
]

def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\u2013\u2014/_|(),:\-\.]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_canonical_skill(skill_name: str) -> str:
    norm = normalize(skill_name)
    return SKILL_EQUIVALENCE.get(norm, norm)

def calculate_relevance(
    job: Dict[str, Any],
    profile_id: str,
    config: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes a 0 to 100 explainable match score with equivalent skill normalization
    and mandatory qualification evaluation.
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
    skill_weights = profile_conf.get("skill_weights", {})

    # 1. Technical Skills Match with Semantic Normalization (Max 35)
    matched_skills = []
    missing_required_skills = []
    missing_preferred_skills = []
    weighted_matched_points = 0.0
    total_possible_weight = 0.0

    for skill in target_skills:
        weight = float(skill_weights.get(skill, 1.0))
        total_possible_weight += weight
        canon_skill = get_canonical_skill(skill)
        s_norm = normalize(skill)

        # Check direct or canonical equivalence
        matched = False
        pattern = r"\b" + re.escape(s_norm) + r"\b"
        if re.search(pattern, desc_n) or re.search(pattern, title_n):
            matched = True
        else:
            # Check equivalent terms
            for term, canon in SKILL_EQUIVALENCE.items():
                if canon == canon_skill:
                    t_pat = r"\b" + re.escape(term) + r"\b"
                    if re.search(t_pat, desc_n) or re.search(t_pat, title_n):
                        matched = True
                        break

        if matched:
            matched_skills.append(skill)
            weighted_matched_points += weight
        else:
            if weight >= 1.1:
                missing_required_skills.append(skill)
            else:
                missing_preferred_skills.append(skill)

    # Scale skill points
    skill_ratio = min(1.0, (weighted_matched_points / 7.0)) if weighted_matched_points > 0 else 0.0
    skill_pts = min(weights["technical_skills"], int(skill_ratio * weights["technical_skills"]))

    # 2. Responsibilities / Domain Depth Match (Max 25)
    if profile_id == "AI_ENGINEER":
        domain_anchors = ["llm", "generative ai", "ai agent", "prompt engineering", "fastapi", "docker", "rag", "rest api"]
    else: # TEST_ENGINEER
        domain_anchors = ["hil", "sil", "ecu", "ecu-test", "canoe", "inca", "dspace", "diagnostics", "uds", "obd"]

    anchors_hit = sum(1 for a in domain_anchors if a in combined)
    resp_ratio = anchors_hit / len(domain_anchors)
    resp_pts = min(weights["responsibilities"], int(resp_ratio * 2.5 * weights["responsibilities"]))

    # 3. Experience Match (Max 15) & Mandatory Experience Check
    exp_pts = weights["experience"]
    exp_matches = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience", combined)
    required_years = None
    mandatory_gaps = []
    mandatory_requirements_pass = True

    if exp_matches:
        try:
            required_years = max([int(x) for x in exp_matches if int(x) <= 25])
            if required_years > candidate_exp + 4: # Asks for 12+ years
                exp_pts = int(weights["experience"] * 0.4)
                mandatory_requirements_pass = False
                mandatory_gaps.append(f"Requires {required_years}+ years experience (candidate has {candidate_exp}y)")
            elif required_years > candidate_exp + 2:
                exp_pts = int(weights["experience"] * 0.6)
            elif required_years <= candidate_exp + 2:
                exp_pts = weights["experience"]
        except Exception:
            exp_pts = weights["experience"]

    # 4. Mandatory Qualifications Evaluation (Security Clearance & Citizenship)
    for rule_name, terms in MANDATORY_DISQUALIFIERS:
        for t in terms:
            if t in combined:
                mandatory_requirements_pass = False
                mandatory_gaps.append(f"Disqualifier detected: {rule_name}")
                break

    # 5. Job Title Relevance (Max 10)
    title_pts = 0
    for t in target_titles:
        t_norm = normalize(t)
        if t_norm in title_n:
            title_pts = weights["title_relevance"]
            break
        elif any(word in title_n for word in t_norm.split() if len(word) > 3):
            title_pts = max(title_pts, int(weights["title_relevance"] * 0.6))

    # 6. Location & Work Arrangement (Max 10)
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

    # 7. Visa Sponsorship Match (Max 5)
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
        if not is_remote:
            mandatory_requirements_pass = False
            mandatory_gaps.append("Mandatory requirement gap: No visa sponsorship offered for on-site position")
    else:
        visa_status = "UNKNOWN"
        sponsorship_pts = int(weights["sponsorship_preference"] * 0.6) if is_remote else int(weights["sponsorship_preference"] * 0.4)

    total_score = skill_pts + resp_pts + exp_pts + title_pts + loc_pts + sponsorship_pts

    # Disqualification penalty
    if not mandatory_requirements_pass:
        total_score = min(total_score, 60) # Capped below auto-apply threshold

    total_score = max(5, min(100, total_score))

    # Summary explanation
    explanation_parts = [
        f"Skills ({skill_pts}/{weights['technical_skills']}): {len(matched_skills)} matched",
        f"Responsibilities ({resp_pts}/{weights['responsibilities']})",
        f"Experience ({exp_pts}/{weights['experience']})",
        f"Title ({title_pts}/{weights['title_relevance']})",
        f"Location: {'Remote' if is_remote else location or 'Global'}",
        f"Sponsorship: {visa_status}"
    ]
    if mandatory_gaps:
        explanation_parts.append(f"Gaps: {'; '.join(mandatory_gaps)}")

    return {
        "score": total_score,
        "match_score": total_score,
        "visa_sponsorship_status": visa_status,
        "matched_skills": matched_skills,
        "missing_skills": (missing_required_skills + missing_preferred_skills)[:10],
        "missing_required_skills": missing_required_skills[:5],
        "missing_preferred_skills": missing_preferred_skills[:5],
        "mandatory_requirements_pass": mandatory_requirements_pass,
        "mandatory_gaps": mandatory_gaps,
        "work_arrangement": "Remote" if is_remote else ("Hybrid" if is_hybrid else "On-site"),
        "explanation": " | ".join(explanation_parts),
        "breakdown": {
            "skills": skill_pts,
            "responsibilities": resp_pts,
            "experience": exp_pts,
            "title": title_pts,
            "location": loc_pts,
            "sponsorship": sponsorship_pts
        }
    }

if __name__ == "__main__":
    import json
    conf = json.load(open("config.json", "r", encoding="utf-8"))
    
    # Test case: 75% match
    res_high = calculate_relevance({
        "title": "Senior AI Engineer",
        "description": "Building LLM multi-agent systems with Python, FastAPI, Docker, RAG with vector databases. Remote worldwide.",
        "location": "Remote"
    }, "AI_ENGINEER", conf)
    print("High Match Score:", res_high["score"])
    print("Mandatory pass:", res_high["mandatory_requirements_pass"])
    assert res_high["score"] > 70
    assert res_high["mandatory_requirements_pass"] is True

    # Test case: Disqualification
    res_disq = calculate_relevance({
        "title": "AI Engineer",
        "description": "Python, LLM, prompt engineering. Must have active top secret clearance.",
        "location": "Washington, DC"
    }, "AI_ENGINEER", conf)
    print("Disqualified Score:", res_disq["score"])
    print("Mandatory pass:", res_disq["mandatory_requirements_pass"])
    assert res_disq["mandatory_requirements_pass"] is False
    assert res_disq["score"] <= 70
    print("[PASS] Scoring engine tests passed.")
