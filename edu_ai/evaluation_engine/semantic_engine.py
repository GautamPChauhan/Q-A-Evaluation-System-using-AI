from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np

# Try to import scipy for Hungarian algorithm; fall back to greedy if unavailable
try:
    from scipy.optimize import linear_sum_assignment
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# Global model instance
_model = None

# Cache for model embeddings to avoid recomputing for every student
_model_embedding_cache = {}

def get_semantic_model():
    """Lazy loader for the SBERT model."""
    global _model
    if _model is None:
        print("Loading SentenceTransformer (all-mpnet-base-v2)...")
        # Use GPU if available
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        _model = SentenceTransformer('all-mpnet-base-v2', device=device)
        print(f"SentenceTransformer loaded on {device}.")
    return _model


def _hungarian_matching(cosine_scores_np, model_sentences, student_sentences):
    """
    Optimal one-to-one matching using the Hungarian (Munkres) algorithm.
    
    Each model sentence is matched to exactly one student sentence, and
    each student sentence can be used at most once. This prevents a student
    from inflating their score by repeating a single high-quality sentence.
    
    The cost matrix is (1 - similarity) so that minimizing cost maximizes
    total similarity.
    """
    n_model = len(model_sentences)
    n_student = len(student_sentences)

    # Build cost matrix: rows = model, cols = student
    # Pad with zeros if dimensions are unequal (unmatched entries get score 0)
    size = max(n_model, n_student)
    cost_matrix = np.ones((size, size), dtype=np.float64)

    for i in range(n_model):
        for j in range(n_student):
            cost_matrix[i][j] = 1.0 - cosine_scores_np[i][j]

    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    matched_pairs = []
    total_score = 0.0

    for row, col in zip(row_indices, col_indices):
        if row >= n_model:
            continue  # This is a padding row, skip
        
        if col < n_student:
            score_val = float(cosine_scores_np[row][col])
        else:
            score_val = 0.0  # Model sentence with no student match
        
        score_val = max(0.0, min(1.0, score_val))

        matched_pairs.append({
            "model_sentence": model_sentences[row],
            "best_student_sentence": student_sentences[col] if col < n_student else "[UNMATCHED]",
            "similarity_score": round(score_val, 4)
        })
        total_score += score_val

    return total_score, matched_pairs


def _greedy_exclusive_matching(cosine_scores, model_sentences, student_sentences):
    """
    Greedy one-to-one matching fallback when scipy is unavailable.
    
    Iterates through all (model, student) pairs sorted by descending similarity.
    Each model sentence and each student sentence is used at most once.
    """
    n_model = len(model_sentences)
    n_student = len(student_sentences)

    # Build a flat list of (score, model_idx, student_idx) and sort descending
    pairs = []
    for i in range(n_model):
        for j in range(n_student):
            pairs.append((float(cosine_scores[i][j]), i, j))
    pairs.sort(key=lambda x: x[0], reverse=True)

    used_model = set()
    used_student = set()
    matched_pairs = []
    total_score = 0.0

    for score_val, m_idx, s_idx in pairs:
        if m_idx in used_model or s_idx in used_student:
            continue
        
        score_val = max(0.0, min(1.0, score_val))
        
        matched_pairs.append({
            "model_sentence": model_sentences[m_idx],
            "best_student_sentence": student_sentences[s_idx],
            "similarity_score": round(score_val, 4)
        })
        total_score += score_val
        used_model.add(m_idx)
        used_student.add(s_idx)

        if len(used_model) == n_model:
            break  # All model sentences matched

    # Handle unmatched model sentences (student wrote too few sentences)
    for i in range(n_model):
        if i not in used_model:
            matched_pairs.append({
                "model_sentence": model_sentences[i],
                "best_student_sentence": "[UNMATCHED]",
                "similarity_score": 0.0
            })

    return total_score, matched_pairs


def compute_semantic_score(model_sentences, student_sentences, question_id=None):
    """
    Compute sentence-level semantic similarity using strict one-to-one matching.
    
    Uses the Hungarian Algorithm (optimal) if scipy is available, otherwise falls
    back to a greedy exclusive matching. In both cases, each student sentence can 
    only be matched to one model sentence, preventing score inflation via repetition.
    
    Returns:
        semantic_similarity_score (float): Average of matched-pair scores.
        matched_pairs (list[dict]): Per-pair details for explainability.
    """
    if not model_sentences or not student_sentences:
        return 0.0, []

    model = get_semantic_model()

    # Encode student sentences
    student_embeddings = model.encode(student_sentences, convert_to_tensor=True)

    # Encode or retrieve model sentences from cache
    if question_id and question_id in _model_embedding_cache:
        model_embeddings = _model_embedding_cache[question_id]
    else:
        model_embeddings = model.encode(model_sentences, convert_to_tensor=True)
        if question_id:
            _model_embedding_cache[question_id] = model_embeddings

    # Compute cosine similarity matrix: shape (n_model, n_student)
    cosine_scores = util.cos_sim(model_embeddings, student_embeddings)

    if HAS_SCIPY:
        cosine_np = cosine_scores.cpu().numpy()
        total_score, matched_pairs = _hungarian_matching(cosine_np, model_sentences, student_sentences)
    else:
        total_score, matched_pairs = _greedy_exclusive_matching(cosine_scores, model_sentences, student_sentences)

    # Aggregate: Average across all model sentences
    semantic_similarity_score = total_score / len(model_sentences)

    return round(semantic_similarity_score, 4), matched_pairs
