from rapidfuzz import fuzz
from .normalizer import normalize

def evaluate_answer(student_answer, keyword_config):
    tokens = normalize(student_answer)

    matched = []
    missing = []
    raw_score = 0.0

    for kw in keyword_config["keywords"]:
        weight = keyword_config["weights"][kw]
        syns = keyword_config["synonyms"].get(kw, [])

        found = False

        for token in tokens:
            if token in kw:
                raw_score += weight
                matched.append((kw, "exact"))
                found = True
                break

            if token in syns:
                raw_score += weight * 0.85
                matched.append((kw, "synonym"))
                found = True
                break

            if fuzz.ratio(token, kw) >= 85:
                raw_score += weight * 0.75
                matched.append((kw, "spelling"))
                found = True
                break

        if not found:
            missing.append(kw)

    return raw_score, matched, missing
