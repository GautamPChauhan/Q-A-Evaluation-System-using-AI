from keybert import KeyBERT

_model = None

def get_model():
    """Lazy loader for the KeyBERT model to avoid startup overhead and potential connection errors."""
    global _model
    if _model is None:
        print("Loading KeyBERT model (all-MiniLM-L6-v2)... this may take a moment.")
        try:
            _model = KeyBERT("all-MiniLM-L6-v2")
            print("KeyBERT model loaded successfully.")
        except Exception as e:
            print(f"Error loading KeyBERT model from Hugging Face: {e}")
            print("Falling back to a basic model or failing gracefully.")
            # We could try to return a dummy model or re-raise
            raise e
    return _model

def extract_keywords(expected_answer, top_n=12):
    """
    ONE-TIME keyword extraction from teacher's expected answer
    """
    model = get_model()
    keywords = model.extract_keywords(
        expected_answer,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        top_n=top_n
    )
    return list(set(k[0].lower() for k in keywords))
