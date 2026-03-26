from .extractor import extract_keywords
from .synonyms import generate_synonyms
from .normalizer import normalize


def build_keyword_config(expected_answer, max_marks):
    """
    Builds IMMUTABLE keyword configuration for a question
    """
    keywords = extract_keywords(expected_answer)

    weights = {}
    synonyms = {}

    for kw in keywords:
        # Phrase > single word
        weights[kw] = 2.0 if len(kw.split()) > 1 else 1.0
        synonyms[kw] = generate_synonyms(kw)

    return {
        "keywords": keywords,
        "weights": weights,
        "synonyms": synonyms,
        "max_marks": max_marks
    }
