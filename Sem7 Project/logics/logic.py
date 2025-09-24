from sentence_transformers import SentenceTransformer, util
import re

# Load SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

def evaluate_answer(student_answer, model_answer, keywords, operator="AND"):
    """
    Evaluate student's answer based on keywords and semantic similarity.
    Weight: 40% keywords, 60% semantic similarity
    """

    # --- 1. Keyword Matching ---
    student_text = student_answer.lower()
    keyword_list = [k.strip().lower() for k in keywords.split(",")]
    matched = [k for k in keyword_list if k in student_text]

    total_keywords = len(keyword_list)
    matched_keywords = len(matched)

    # Apply logical operators
    if operator == "AND":
        keyword_score = 1.0 if matched_keywords == total_keywords else matched_keywords / total_keywords
    elif operator == "OR":
        keyword_score = 1.0 if matched_keywords > 0 else 0.0
    elif operator == "XOR":
        keyword_score = 1.0 if matched_keywords == 1 else 0.0
    elif operator == "NAND":
        keyword_score = 1.0 if matched_keywords < total_keywords else 0.0
    elif operator == "NOR":
        keyword_score = 1.0 if matched_keywords == 0 else 0.0
    else:
        keyword_score = matched_keywords / total_keywords if total_keywords > 0 else 0.0

    # --- 2. Semantic Similarity (Context) ---
    embeddings = model.encode([student_answer, model_answer], convert_to_tensor=True)
    context_score = util.cos_sim(embeddings[0], embeddings[1]).item()

    # --- 3. Weighted Final Score ---
    final_score = (0.4 * keyword_score) + (0.6 * context_score)

    return {
        "keywords_matched": matched,
        "keyword_score": round(keyword_score, 3),
        "context_score": round(context_score, 3),
        "final_score": round(final_score, 3)
    }


# Example usage
student = "The CPU is the brain of the computer and controls all operations."
model_ans = "CPU is the central processing unit and it manages all tasks."
keywords = "CPU, brain, operations"

result = evaluate_answer(student, model_ans, keywords, operator="AND")
print(result)
