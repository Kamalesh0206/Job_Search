import re

def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\u2013\u2014/_|(),:]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def _count_terms(text: str, terms):
    return sum(1 for term in terms if normalize(term) in text)

def classify_job(title: str, description: str, config: dict):
    title_n = normalize(title)
    desc_n = normalize(description)
    combined = f"{title_n} {desc_n}"

    if any(normalize(x) in title_n for x in config.get("exclude_title_terms", [])):
        return None

    scores = {}
    for family, rules in config["role_families"].items():
        # Title is weighted more strongly than description/context.
        title_score = _count_terms(title_n, rules.get("title_terms", [])) * 5
        context_score = _count_terms(combined, rules.get("context_terms", []))
        scores[family] = title_score + context_score

    # Special handling for generic "Product Manager".
    # AI context promotes the role into AI Product Manager.
    if "product manager" in title_n:
        ai_terms = config["role_families"]["AI Product Manager"]["context_terms"]
        technical_terms = config["role_families"]["Technical Product Manager"]["context_terms"]
        ai_hits = _count_terms(combined, ai_terms)
        tech_hits = _count_terms(combined, technical_terms)
        if ai_hits >= 2:
            scores["AI Product Manager"] += 8
        elif tech_hits >= 2:
            scores["Technical Product Manager"] += 6

    best_family = max(scores, key=scores.get)
    best_score = scores[best_family]

    # Require a meaningful match; avoids unrelated jobs.
    if best_score < 5:
        return None
    return best_family
