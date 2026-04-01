import spacy
import re

_nlp = spacy.load("en_core_web_sm")

def normalize(text):
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
    doc = _nlp(text)
    return [t.lemma_ for t in doc if not t.is_stop and not t.is_punct]
