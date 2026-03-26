def calculate_marks(raw_score, keyword_config):
    max_raw = sum(keyword_config["weights"].values())
    max_marks = keyword_config["max_marks"]

    if max_raw == 0:
        return 0.0

    return round((raw_score / max_raw) * max_marks, 2)
