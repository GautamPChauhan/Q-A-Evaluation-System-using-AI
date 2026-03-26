from transformers import pipeline
import torch

_nli_model = None

# ────────────────────────────────────────────────────────────────
# CONFIGURABLE THRESHOLDS
# Move these to a config file or environment variables for tuning
# without code changes.
# ────────────────────────────────────────────────────────────────
EVAL_CONFIG = {
    "contradiction_threshold": 0.5,   # If contradiction prob > this → score = 0
    "entailment_threshold": 0.6,      # If entailment prob > this → keep full score
    "neutral_penalty_factor": 0.5,    # Score multiplier for neutral/weak entailment
}

def get_nli_model():
    """Lazy loader for the NLI model."""
    global _nli_model
    if _nli_model is None:
        print("Loading NLI Model (facebook/bart-large-mnli)... this may take a moment.")
        # Use GPU if available
        device = 0 if torch.cuda.is_available() else -1
        # Use the standard text-classification pipeline for NLI pairs
        _nli_model = pipeline(
            "text-classification", 
            model="facebook/bart-large-mnli", 
            device=device
        )
        print(f"NLI model loaded on device {device}.")
    return _nli_model

def validate_meaning(matched_pairs, config=None):
    """
    Validates the meaning of semantic matches using NLI.
    
    Input:
        matched_pairs: list of dicts with 'model_sentence', 'best_student_sentence', 'similarity_score'
        config: optional dict to override EVAL_CONFIG thresholds
    Output:
        modified list with 'adjusted_similarity_score' and NLI insights.
    """
    if not matched_pairs:
        return []

    # Merge defaults with any provided overrides
    cfg = {**EVAL_CONFIG, **(config or {})}
    contradiction_thresh = cfg["contradiction_threshold"]
    entailment_thresh = cfg["entailment_threshold"]
    neutral_penalty = cfg["neutral_penalty_factor"]

    model = get_nli_model()
    
    validated_pairs = []
    
    # Skip NLI for unmatched pairs (where student sentence is "[UNMATCHED]")
    pairs_to_process = []
    unmatched_indices = set()
    for idx, pair in enumerate(matched_pairs):
        if pair.get("best_student_sentence") == "[UNMATCHED]":
            unmatched_indices.add(idx)
        else:
            pairs_to_process.append(pair)
    
    # Input format for BART MNLI pipeline: {"text": premise, "text_pair": hypothesis}
    # Premise = student sentence
    # Hypothesis = model sentence
    nli_inputs = [
        {"text": pair["best_student_sentence"], "text_pair": pair["model_sentence"]}
        for pair in pairs_to_process
    ]
    
    # Batch predict
    nli_results = []
    if nli_inputs:
        try:
            nli_results = model(nli_inputs, top_k=None)  # Returns all probabilities
        except Exception as e:
            print(f"NLI batch error: {e}. Falling back to individual predictions.")
            nli_results = []
            for inp in nli_inputs:
                try:
                    nli_results.append(model(inp, top_k=None))
                except Exception as inner_e:
                    print(f"NLI individual error: {inner_e}")
                    nli_results.append([
                        {"label": "entailment", "score": 0.33},
                        {"label": "contradiction", "score": 0.33},
                        {"label": "neutral", "score": 0.34},
                    ])

    # Process results
    result_idx = 0
    for idx, pair in enumerate(matched_pairs):
        semantic_score = pair["similarity_score"]
        
        if idx in unmatched_indices:
            # Unmatched model sentence → score stays 0
            validated_pair = dict(pair)
            validated_pair["adjusted_similarity_score"] = 0.0
            validated_pair["nli_status"] = "unmatched"
            validated_pair["nli_probs"] = {
                "entailment": 0.0,
                "contradiction": 0.0,
                "neutral": 0.0
            }
            validated_pairs.append(validated_pair)
            continue
        
        result = nli_results[result_idx]
        result_idx += 1
        
        # Parse probabilities
        probs = {res['label'].lower(): res['score'] for res in result}
        
        entailment_prob = probs.get('entailment', 0.0)
        contradiction_prob = probs.get('contradiction', 0.0)
        neutral_prob = probs.get('neutral', 0.0)
        
        adjusted_score = semantic_score
        status = "kept"
        
        # Scoring adjustment rules (configurable thresholds)
        if contradiction_prob > contradiction_thresh:
            adjusted_score = 0.0
            status = "contradicted"
        elif entailment_prob > entailment_thresh:
            adjusted_score = semantic_score  # Keep full score
            status = "entailed"
        else:
            # Neutral or weak entailment → apply penalty
            adjusted_score = semantic_score * neutral_penalty
            status = "neutral"
            
        validated_pair = dict(pair)
        validated_pair["adjusted_similarity_score"] = round(adjusted_score, 4)
        validated_pair["nli_status"] = status
        validated_pair["nli_probs"] = {
            "entailment": round(entailment_prob, 3),
            "contradiction": round(contradiction_prob, 3),
            "neutral": round(neutral_prob, 3)
        }
        
        validated_pairs.append(validated_pair)
        
    return validated_pairs
