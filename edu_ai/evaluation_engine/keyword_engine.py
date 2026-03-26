from rapidfuzz import fuzz
from keybert import KeyBERT
from nltk.corpus import wordnet as wn
import nltk

# Ensure wordnet is downloaded
try:
    wn.synsets('dog')
except LookupError:
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download('wordnet')
    nltk.download('omw-1.4')

_keybert_model = None

def get_keybert_model():
    """Lazy loader for the KeyBERT model."""
    global _keybert_model
    if _keybert_model is None:
        print("Loading KeyBERT model (all-MiniLM-L6-v2)...")
        _keybert_model = KeyBERT("all-MiniLM-L6-v2")
    return _keybert_model

def extract_keywords_from_model_answer(text, top_n=15):
    """
    Extract key phrases using KeyBERT from the model answer.
    """
    if not text.strip():
        return []

    model = get_keybert_model()
    keywords = model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3), # Unigrams, bigrams, trigrams
        stop_words="english",
        top_n=top_n
    )
    # Extract just the text, lowercase it
    return list(set(k[0].lower() for k in keywords))

def get_wordnet_synonyms(word):
    """Generate WordNet synonyms for a given word."""
    synonyms = set()
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " ").lower())
    return list(synonyms)

def evaluate_keywords(student_answer_raw, student_lemmas, target_keywords, keyword_weights=None):
    """
    4-Tier Keyword Matching logic with importance-weighted scoring:
    1. Exact match (string in raw text) -> weight * 1.0
    2. Lemmatized match (in lemmatized tokens) -> weight * 0.8
    3. Synonym match (via WordNet) -> weight * 0.6
    4. Fuzzy match (rapidfuzz >= 85) -> weight * 0.5
    
    Args:
        student_answer_raw: Raw student answer text.
        student_lemmas: List of lemmatized tokens from the student answer.
        target_keywords: List of keywords to check.
        keyword_weights: Optional dict {keyword: importance_weight}. 
                         Defaults to 2.0 for phrases, 1.0 for single words.
    """
    if not target_keywords:
        return 0.0, [], []

    # Build weights dict if not provided
    if keyword_weights is None:
        keyword_weights = {}
        for kw in target_keywords:
            keyword_weights[kw] = 2.0 if len(kw.split()) > 1 else 1.0

    matched = []
    missing = []
    total_weighted_score = 0.0
    total_possible_weight = 0.0

    student_text_lower = student_answer_raw.lower()

    for kw in target_keywords:
        kw_lower = kw.lower()
        weight = keyword_weights.get(kw, 1.0)
        total_possible_weight += weight
        
        # 1. Exact Match
        if kw_lower in student_text_lower:
            total_weighted_score += weight * 1.0
            matched.append({"keyword": kw, "type": "exact", "score": 1.0, "weight": weight})
            continue
            
        # 2. Lemma Match
        kw_tokens = kw_lower.split()
        if len(kw_tokens) == 1 and kw_lower in student_lemmas:
            total_weighted_score += weight * 0.8
            matched.append({"keyword": kw, "type": "lemma", "score": 0.8, "weight": weight})
            continue
            
        # 3. Synonym Match (only for single words)
        synonym_matched = False
        if len(kw_tokens) == 1:
            syns = get_wordnet_synonyms(kw_lower)
            for syn in syns:
                if syn in student_text_lower:
                    total_weighted_score += weight * 0.6
                    matched.append({"keyword": kw, "type": "synonym", "score": 0.6, "weight": weight})
                    synonym_matched = True
                    break
        if synonym_matched:
            continue
            
        # 4. Fuzzy Match
        fuzzy_matched = False
        # Compare keyword against all student lemmas for fuzzy match
        for lemma in student_lemmas:
            if fuzz.ratio(kw_lower, lemma) >= 85:
                total_weighted_score += weight * 0.5
                matched.append({"keyword": kw, "type": "fuzzy", "score": 0.5, "weight": weight})
                fuzzy_matched = True
                break
                
        if not fuzzy_matched:
            missing.append(kw)

    # Calculate final keyword score normalized to 0.0 - 1.0
    # Uses importance-weighted denominator instead of simple count
    if total_possible_weight > 0:
        keyword_score = total_weighted_score / total_possible_weight
    else:
        keyword_score = 0.0
    keyword_score = min(1.0, keyword_score)  # Cap at 1.0
    
    return round(keyword_score, 4), matched, missing
