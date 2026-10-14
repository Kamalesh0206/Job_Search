import re
from typing import Dict, Any, Optional, Tuple, List

# Core anchor keywords that signify genuine AI/LLM work (not just generic Python)
AI_CORE_ANCHORS = [
    "generative ai", "genai", "llm", "large language model", "gpt", "gemini",
    "prompt engineering", "ai agent", "ai agents", "agentic", "rag",
    "vector database", "retrieval augmented generation", "langchain", "llamaindex",
    "artificial intelligence", "deep learning", "machine learning", "neural network",
    "fine-tuning", "model deployment", "hugging face", "pytorch", "tensorflow"
]

# Core anchor keywords that signify genuine Automotive / Embedded Test Engineering (not just web QA)
TEST_CORE_ANCHORS = [
    "hil", "sil", "hardware-in-the-loop", "software-in-the-loop", "ecu",
    "ecu-test", "tracetronic", "canoe", "canalyzer", "vector", "inca",
    "dspace", "scalexio", "etas", "labcar", "systemdesk", "controldesk",
    "can bus", "can-bus", "lin bus", "flexray", "automotive ethernet",
    "uds", "iso 14229", "obd", "obd-ii", "obdonuds", "diagnostic testing",
    "powertrain", "automotive embedded", "v&v", "verification and validation",
    "embedded software test", "ecu validation", "autosar"
]

# Irrelevant / generic QA indicators that should NOT be classified as Automotive Test Engineer
GENERIC_WEB_QA = [
    "selenium", "cypress", "playwright qa", "appium", "manual tester", "qa tester",
    "loadrunner", "jmeter", "test rail", "testrail", "postman testing"
]

def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\u2013\u2014/_|(),:\-\.]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def contains_term(text_n: str, term: str) -> bool:
    term_n = normalize(term)
    # Match with word boundary or exact phrase
    pattern = r"\b" + re.escape(term_n) + r"\b"
    return bool(re.search(pattern, text_n))

def find_matched_terms(text: str, terms: List[str]) -> List[str]:
    text_n = normalize(text)
    matched = []
    for t in terms:
        if contains_term(text_n, t):
            matched.append(t)
    return matched

def classify_job(title: str, description: str, config: Dict[str, Any], active_profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Classifies a job into one of:
      1. AI_ENGINEER
      2. TEST_ENGINEER
      3. BOTH
      4. IRRELEVANT
      
    Strict rules:
      - Python alone does NOT qualify as AI Engineer.
      - General testing alone does NOT qualify as Automotive Test Engineer.
      - Ambiguous postings are flagged for review.
    """
    title_n = normalize(title)
    desc_n = normalize(description)
    combined = title_n + " " + desc_n

    ai_conf = config.get("profiles", {}).get("AI_ENGINEER", {})
    test_conf = config.get("profiles", {}).get("TEST_ENGINEER", {})

    # Check negative exclusions per profile
    ai_excludes = ai_conf.get("exclude_terms", [])
    test_excludes = test_conf.get("exclude_terms", [])

    is_ai_excluded = any(contains_term(title_n, term) for term in ai_excludes)
    is_test_excluded = any(contains_term(title_n, term) for term in test_excludes)

    # 1. Check title matches
    ai_title_matches = [t for t in ai_conf.get("target_titles", []) if contains_term(title_n, t)]
    test_title_matches = [t for t in test_conf.get("target_titles", []) if contains_term(title_n, t)]

    # 2. Check core anchor terms in description
    ai_anchors_found = find_matched_terms(combined, AI_CORE_ANCHORS)
    test_anchors_found = find_matched_terms(combined, TEST_CORE_ANCHORS)
    generic_qa_found = find_matched_terms(combined, GENERIC_WEB_QA)

    # Specific rule: Python alone check
    has_python = contains_term(combined, "python")
    only_python_no_ai = has_python and len(ai_anchors_found) == 0

    # Specific rule: Generic QA vs Automotive embedded check
    is_pure_web_qa = len(generic_qa_found) >= 2 and len(test_anchors_found) == 0

    # Evaluate AI Engineer qualifications
    is_ai = False
    ai_confidence = 0.0
    if not is_ai_excluded:
        if ai_title_matches:
            # Title strongly suggests AI
            is_ai = True
            ai_confidence = 0.90 if len(ai_anchors_found) >= 1 else 0.70
        elif len(ai_anchors_found) >= 2 and not only_python_no_ai:
            # Strong AI context in description even if title is generic
            is_ai = True
            ai_confidence = 0.80

    # Evaluate Test Engineer qualifications
    is_test = False
    test_confidence = 0.0
    if not is_test_excluded and not is_pure_web_qa:
        if test_title_matches and (len(test_anchors_found) >= 1 or "automotive" in title_n or "ecu" in title_n or "hil" in title_n or "sil" in title_n or "embedded" in title_n):
            is_test = True
            test_confidence = 0.90
        elif len(test_anchors_found) >= 2:
            is_test = True
            test_confidence = 0.85
        elif test_title_matches and len(test_anchors_found) == 0:
            # Ambiguous test title without automotive/HIL/ECU anchors
            is_test = False
            test_confidence = 0.40

    # Determine final category
    if is_ai and is_test:
        category = "BOTH"
        confidence = min(ai_confidence, test_confidence)
        explanation = f"Matched both AI anchors ({', '.join(ai_anchors_found[:3])}) and Automotive Test anchors ({', '.join(test_anchors_found[:3])})."
        ambiguous = False
    elif is_ai:
        category = "AI_ENGINEER"
        confidence = ai_confidence
        explanation = f"Matched AI profile: titles={ai_title_matches[:2]}, anchors={ai_anchors_found[:4]}"
        ambiguous = (ai_confidence < 0.75)
    elif is_test:
        category = "TEST_ENGINEER"
        confidence = test_confidence
        explanation = f"Matched Automotive/Embedded Test profile: titles={test_title_matches[:2]}, anchors={test_anchors_found[:4]}"
        ambiguous = (test_confidence < 0.75)
    else:
        category = "IRRELEVANT"
        confidence = 0.0
        reasons = []
        if is_ai_excluded or is_test_excluded:
            reasons.append("Excluded title term matched")
        if only_python_no_ai:
            reasons.append("Mentions Python alone without genuine GenAI/LLM/AI anchor skills")
        if is_pure_web_qa:
            reasons.append("General web/mobile QA rather than Automotive/Embedded/HIL testing")
        if not reasons:
            reasons.append("Neither AI nor Automotive Test engineering criteria met")
        explanation = "; ".join(reasons)
        ambiguous = False

    return {
        "category": category,
        "confidence": round(confidence, 2),
        "explanation": explanation,
        "ambiguous": ambiguous,
        "ai_title_matches": ai_title_matches,
        "test_title_matches": test_title_matches,
        "ai_anchors": ai_anchors_found,
        "test_anchors": test_anchors_found
    }