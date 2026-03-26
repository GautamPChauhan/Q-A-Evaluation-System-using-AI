import spacy
import re

# Load English tokenizer, tagger, parser and NER
try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    _nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    """Convert to lowercase, remove unnecessary punctuation, normalize whitespace.
    
    Preserves mathematical operators (+, -, *, /, =, <, >), programming symbols
    (parentheses, brackets, braces), and common technical characters so that
    answers involving code, math, or formulas are not destroyed.
    """
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    # Keep alphanumeric, whitespace, sentence punctuation, math/programming symbols
    # Preserved: . , ? ! + - * / = ( ) [ ] { } < > : ; _ @ # % & ^ ~
    text = re.sub(r'[^a-z0-9\s.,?!+\-*/=()<>\[\]{}_:;@#%&^~\']', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def sentence_tokenize(text):
    """Split text into sentences using spaCy."""
    if not text.strip():
        return []
        
    doc = _nlp(text)
    # Extract sentences and clean them
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences

def extract_lemmas(text):
    """Extract lemmatized, non-stopword tokens for keyword matching."""
    doc = _nlp(text)
    return [t.lemma_.lower() for t in doc if not t.is_stop and not t.is_punct and t.text.strip()]

def preprocess_for_evaluation(text):
    """End-to-end preprocessing."""
    cleaned = clean_text(text)
    sentences = sentence_tokenize(cleaned)
    lemmas = extract_lemmas(cleaned)
    
    return {
        "raw": text,
        "cleaned": cleaned,
        "sentences": sentences,
        "lemmas": lemmas
    }
