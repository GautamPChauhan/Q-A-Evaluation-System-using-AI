from nltk.corpus import wordnet as wn

def generate_synonyms(keyword):
    """
    Controlled synonym expansion
    """
    synonyms = set()
    for word in keyword.split():
        for syn in wn.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().replace("_", " "))
    return list(synonyms)
