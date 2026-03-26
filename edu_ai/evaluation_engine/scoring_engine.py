import json
import numpy as np
import re
from .preprocessing import preprocess_for_evaluation
from .semantic_engine import compute_semantic_score, get_semantic_model
from .nli_engine import validate_meaning
from .keyword_engine import extract_keywords_from_model_answer, evaluate_keywords

# ────────────────────────────────────────────────────────────────
# ENHANCED PRODUCTION SCORING CONFIGURATION
# ────────────────────────────────────────────────────────────────
SCORING_CONFIG = {
    # Component Weights (50 / 30 / 20 formula)
    "weight_sentence_match": 0.5,    # 50% Hungarian 1:1 Sentence Matching
    "weight_concept_coverage": 0.3, # 30% Weighted Importance-based Coverage
    "weight_analogy_keyword": 0.2,   # 20% Analogy/Partial Credit & Keywords
    
    # Matching Thresholds (Production-Level Fairness)
    "thresh_full": 0.7,             # Default threshold for 1.0 credit
    "thresh_partial": 0.5,          # Default threshold for 0.5 credit
    "thresh_weak": 0.3,             # Default threshold for 0.25 credit
    
    # Analogy-Specific Thresholds (Vocabulary Mismatch Tolerance)
    "thresh_analogy_partial": 0.45, # Allow lower similarity for analogies
    "thresh_analogy_cap": 0.7,      # Maximum credit for metaphorical expressions
    
    # Other Production Settings
    "concept_ratio": 0.4,           # Top 40% embedding-norm sentences are concepts
    "error_penalty": 1.0,           # Points deducted per critical misconception
    "error_max_penalty": 2.0,       # Capped penalty to avoid negative scores
    "normalization_scale": 5.0,     # Normalize to 0-5 for grading
    "rounding_step": 0.5,           # Round to nearest 0.5 for interpretability
    "irrelevant_threshold": 0.3,    # Score = 0 if matches are below this
}

# Heuristic ANALOGY markers
ANALOGY_MARKERS = [
    r"\blike\b", r"\bsimilar to\b", r"\bworks like\b", r"\bthink of it as\b",
    r"\bas if\b", r"\bcomparable to\b", r"\banalogy\b", r"\bmetaphor\b"
]

# COMMON MISCONCEPTIONS (Can be expanded per subject)
COMMON_ERRORS = [
    "ai and ml are the same", "java and javascript are related",
    "ram is for long term storage", "html is a programming language"
]


def detect_analogy(sentence):
    """Detect heuristic analogy markers in a student sentence."""
    text = sentence.lower()
    for marker in ANALOGY_MARKERS:
        if re.search(marker, text):
            return True
    return False


def apply_threshold_credit(similarity, is_analogy=False):
    """
    Apply fairness-based credit logic (1.0 / 0.5 / 0.25 / 0).
    
    If analogy is detected:
      - Lowers threshold for partial credit (tolerance for vocabulary gap)
      - Caps maximum credit at 0.7 (ensures technical term usage is still incentivized)
    """
    if is_analogy:
        # Analogy specific logic
        if similarity >= 0.6:
            return 0.7  # Capped at 0.7 for metaphorical expression
        elif similarity >= SCORING_CONFIG["thresh_analogy_partial"]:
            return 0.5
        elif similarity >= SCORING_CONFIG["thresh_weak"]:
            return 0.25
        return 0.0
    else:
        # Default logic
        if similarity >= SCORING_CONFIG["thresh_full"]:
            return 1.0
        elif similarity >= SCORING_CONFIG["thresh_partial"]:
            return 0.5
        elif similarity >= SCORING_CONFIG["thresh_weak"]:
            return 0.25
        return 0.0


def compute_weighted_concept_score(model_sentences, student_sentences, question_id=None):
    """
    Identifies top concept sentences via embedding norms (information density).
    Uses norms as weights in the coverage denominator for better accuracy.
    """
    if not model_sentences or not student_sentences:
        return 0.0, []

    model = get_semantic_model()
    model_embeddings = model.encode(model_sentences, convert_to_numpy=True)
    student_embeddings = model.encode(student_sentences, convert_to_numpy=True)
    norms = np.linalg.norm(model_embeddings, axis=1)

    # Select top-k concepts
    top_k = max(1, int(len(model_sentences) * SCORING_CONFIG["concept_ratio"]))
    indices = np.argsort(norms)[-top_k:][::-1]

    total_credit = 0.0
    total_possible_weight = 0.0
    details = []

    for idx in indices:
        concept_emb = model_embeddings[idx]
        weight = float(norms[idx])
        total_possible_weight += weight
        
        # Calculate max similarity to any student sentence
        dots = np.dot(student_embeddings, concept_emb)
        norms_s = np.linalg.norm(student_embeddings, axis=1)
        similarities = dots / (norms_s * np.linalg.norm(concept_emb) + 1e-8)
        
        best_sim = float(np.max(similarities))
        best_s_idx = int(np.argmax(similarities))
        
        student_sent = student_sentences[best_s_idx]
        is_analogy = detect_analogy(student_sent)
        
        credit = apply_threshold_credit(best_sim, is_analogy)
        total_credit += (credit * weight)

        details.append({
            "concept": model_sentences[idx],
            "match": student_sent,
            "similarity": round(best_sim, 4),
            "is_analogy": is_analogy,
            "credit": credit
        })

    score = total_credit / total_possible_weight if total_possible_weight > 0 else 0.0
    return round(score, 4), details


def detect_misconception_penalty(student_text, validated_pairs):
    """
    Detect fatal errors or NLI contradictions.
    Returns penalty points and reason.
    """
    penalty = 0.0
    reasons = []

    # 1. Check for NLI Contradictions
    contradictions = [p for p in validated_pairs if p.get("nli_status") == "contradicted"]
    if contradictions:
        # Subtract for active hallucinations
        c_penalty = len(contradictions) * 0.5
        penalty += c_penalty
        for c in contradictions:
            reasons.append(f"Contradiction: '{c['best_student_sentence']}'")

    # 2. Check for manual misconceptions pattern
    text_lower = student_text.lower()
    for error in COMMON_ERRORS:
        if error in text_lower:
            penalty += SCORING_CONFIG["error_penalty"]
            reasons.append(f"Factual Error: '{error}' detected")

    # Cap penalty
    penalty = min(penalty, SCORING_CONFIG["error_max_penalty"])
    return round(penalty, 2), reasons


def evaluate_hybrid_answer(student_answer, model_answer, max_marks, question_id=None, pre_extracted_keywords=None):
    """
    Enhanced Evaluation Pipeline:
    - 50% Sentence Matching Score (Hungarian + Fairness Thresholds)
    - 30% Weighted Concept Coverage Score (Norm-based weights + Analogy tolerance)
    - 20% Analogy/Keyword Adjustment Layer
    - MINUS Error Penalty (Misconceptions + Contradictions)
    """
    # 1. Edge Case: Empty Answer
    if not student_answer or not student_answer.strip():
        return format_json_output(0.0, 0.0, 0.0, 0.0, 0, max_marks, [], [], [], [], [], 0.0)

    # 2. Preprocessing
    student_data = preprocess_for_evaluation(student_answer)
    model_data = preprocess_for_evaluation(model_answer)
    
    student_sentences = student_data["sentences"] or [student_data["cleaned"]]
    model_sentences = model_data["sentences"] or [model_data["cleaned"]]

    # 3. Component 1: Sentence Match Score (50%)
    # Use Hungarian Algorithm result from semantic_engine
    raw_sem_score, matched_pairs = compute_semantic_score(model_sentences, student_sentences, question_id)
    validated_pairs = validate_meaning(matched_pairs)
    
    # Apply Threshold-based Credit to every match
    sentence_match_credit_sum = 0.0
    for p in validated_pairs:
        # Penalize contradiction by making adjusted similarity 0
        if p.get("nli_status") == "contradicted":
            p["credit_awarded"] = 0.0
        else:
            is_analog = detect_analogy(p["best_student_sentence"])
            p["is_analogy"] = is_analog
            p["credit_awarded"] = apply_threshold_credit(p["similarity_score"], is_analog)
        
        sentence_match_credit_sum += p["credit_awarded"]
    
    # 50% component = Average credit across all model sentences
    sentence_matching_score = sentence_match_credit_sum / len(model_sentences)

    # 4. Component 2: Weighted Concept Coverage (30%)
    concept_score, concept_details = compute_weighted_concept_score(model_sentences, student_sentences, question_id)

    # 5. Component 3: Analogy/Keyword Blend (20%)
    # We blend keywords here to ensure specific terminology is tracked
    keywords = pre_extracted_keywords if pre_extracted_keywords else extract_keywords_from_model_answer(model_answer)
    kw_raw_score, matched_kws, missing_kws = evaluate_keywords(student_data["raw"], student_data["lemmas"], keywords)
    
    # Analogy bonus: ratio of analogy sentences (max 1.0)
    analogy_count = sum(1 for p in validated_pairs if p.get("is_analogy", False))
    analogy_ratio = min(1.0, analogy_count / (len(student_sentences) or 1))
    
    # 20% bucket = Better of keywords or analogy presence (balanced for technical vs creative)
    analogy_kw_score = 0.7 * kw_raw_score + 0.3 * analogy_ratio

    # 6. Final Aggregate Scoring
    w1, w2, w3 = SCORING_CONFIG["weight_sentence_match"], SCORING_CONFIG["weight_concept_coverage"], SCORING_CONFIG["weight_analogy_keyword"]
    
    raw_final_score = (w1 * sentence_matching_score) + (w2 * concept_score) + (w3 * analogy_kw_score)
    
    # 7. Error Penalty
    penalty_marks, error_reasons = detect_misconception_penalty(student_data["raw"], validated_pairs)
    
    # Apply normalization to scale 0-5
    scale = SCORING_CONFIG["normalization_scale"]
    scaled_score = raw_final_score * scale
    final_output_score = max(0.0, scaled_score - penalty_marks)
    
    # Step: Round to nearest 0.5 for interpretability
    rounded_score = round(final_output_score * 2) / 2
    
    # Final Marks Awarded (scaled to max_marks)
    marks_awarded = round((rounded_score / scale) * max_marks, 2)

    # Diagnostics logic
    matched_sentences = [
        f"[{p['nli_status'].upper()}{' - ANALOGY' if p.get('is_analogy') else ''}] '{p['best_student_sentence']}' matches '{p['model_sentence']}'"
        for p in validated_pairs if p["credit_awarded"] > 0
    ]

    return format_json_output(
        sem_score=sentence_matching_score,
        concept_score=concept_score,
        kw_score=analogy_kw_score,
        final_score=rounded_score / scale, # 0-1 range
        marks=marks_awarded,
        max_marks=max_marks,
        matched_sents=matched_sentences,
        missing_concepts=error_reasons,
        contradictions=[e for e in error_reasons if "Contradiction" in e],
        matched_kws=[k["keyword"] for k in matched_kws],
        missing_kws=missing_kws,
        penalty=penalty_marks,
        concept_details=concept_details,
        validated_pairs=validated_pairs
    )


def format_json_output(sem_score, concept_score, kw_score, final_score, marks, max_marks, 
                                          matched_sents, missing_concepts, contradictions, 
                                          matched_kws, missing_kws, penalty,
                                          concept_details=None, validated_pairs=None):
    """Formats the final evaluation into the structured JSON dictionary."""
    return {
        "evaluation_summary": {
            "grade_on_5_scale": float(round(final_score * 5, 1)),
            "marks_awarded": float(marks),
            "max_marks": float(max_marks),
            "penalty_applied": float(penalty)
        },
        "component_scores": {
            "sentence_match_50pct": round(sem_score, 3),
            "concept_coverage_30pct": round(concept_score, 3),
            "analogy_keywords_20pct": round(kw_score, 3)
        },
        "analysis": {
            "matched_sentences": matched_sents,
            "factual_errors": [m for m in missing_concepts if "Error" in m or "Contradiction" in m],
            "keywords_matched": matched_kws,
            "keywords_missing": missing_kws,
            "concept_coverage_details": concept_details or [],
            "sentence_pairing_details": [
                {
                    "model_sentence": p.get("model_sentence", ""),
                    "student_sentence": p.get("best_student_sentence", ""),
                    "similarity": round(p.get("similarity_score", 0), 3),
                    "credit_awarded": p.get("credit_awarded", 0),
                    "is_analogy": p.get("is_analogy", False),
                    "status": p.get("nli_status", "kept")
                }
                for p in (validated_pairs or [])
            ]
        }
    }
