from keyword_engine.config_builder import build_keyword_config
from keyword_engine.evaluator import evaluate_answer
from keyword_engine.scorer import calculate_marks


# PHASE A: QUESTION SETUP

expected_answer = """
Python is a high-level, interpreted programming language
known for its simplicity and readability.
"""

MAX_MARKS = 10

keyword_config = build_keyword_config(
    expected_answer=expected_answer,
    max_marks=MAX_MARKS
)

# print("KEYWORD CONFIG (fixed for all students):")
# print(keyword_config)


# PHASE B: STUDENT ANSWER

student_answer = """
Python high level interpreted simplicity readability language.
"""

raw_score, matched, missing = evaluate_answer(
    student_answer,
    keyword_config
)

final_marks = calculate_marks(raw_score, keyword_config)

print("\nEVALUATION RESULT:")
print("Matched:", matched)
print("Missing:", missing)
print("Marks:", final_marks, "/", MAX_MARKS)

