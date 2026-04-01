"""
PDF QA Engine - Extracts answers from PDF documents using Groq AI
Integrated into EduAI for automated answer extraction during exam creation

Two-Phase Answer Strategy:
  Phase 1: Extract answer from PDF book content
  Phase 2: If book answer is weak/incomplete, enhance with AI general knowledge
  Final: Merge both into a comprehensive model answer proportional to max marks
"""

import os
import time
import json
import PyPDF2
from groq import Groq
from dotenv import load_dotenv

# Try to import pdfplumber (preferred), fallback to PyPDF2 only
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = None

# ── Rate Limit Configuration ──────────────────────────────────
# Groq free tier: 30 requests/min, 15,000 tokens/min
# Reduce wait times with adaptive retry on 429 errors
RATE_LIMIT_WAIT = 8          # Base wait between API calls (seconds)
RATE_LIMIT_RETRY_WAIT = 30   # Wait on rate-limit error before retry
MAX_RETRIES = 3              # Max retries per API call


def _get_groq_client():
    """Lazy initialization of Groq client"""
    global groq_client
    if groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise Exception("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
        groq_client = Groq(api_key=api_key)
    return groq_client


def extract_text_from_pdf(pdf_path):
    """Extract text content from PDF file using multiple methods"""
    text = ""

    # Method 1: Try pdfplumber first (better for most PDFs)
    if HAS_PDFPLUMBER:
        try:
            print(f"Attempting to extract text using pdfplumber...")
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        print(f"Warning: Could not extract page {page_num + 1} with pdfplumber: {str(e)}")
                        continue

            if text.strip():
                print(f"Successfully extracted {len(text)} characters using pdfplumber")
                return text.strip()
        except Exception as e:
            print(f"pdfplumber failed: {str(e)}, trying PyPDF2...")

    # Method 2: Fallback to PyPDF2
    try:
        print(f"Attempting to extract text using PyPDF2...")
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    if page_text:
                        try:
                            page_text = page_text.encode('utf-8', 'surrogatepass').decode('utf-8', 'ignore')
                        except:
                            page_text = page_text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

                        page_text = page_text.replace('\x00', '')
                        page_text = ''.join(char for char in page_text if char.isprintable() or char in '\n\r\t ')
                        text += page_text + "\n"

                except Exception as page_error:
                    print(f"Warning: Skipping page {page_num + 1}: {str(page_error)}")
                    continue

        if text.strip():
            print(f"Successfully extracted {len(text)} characters using PyPDF2")
            return text.strip()

    except Exception as e:
        print(f"PyPDF2 also failed: {str(e)}")

    raise Exception(
        "Could not extract text from PDF. Possible reasons:\n"
        "1. PDF contains only images (scanned document) - needs OCR\n"
        "2. PDF is password protected\n"
        "3. PDF is corrupted\n"
        "Please try a different PDF or use a text-based PDF."
    )


def _call_groq(system_prompt, user_prompt, max_tokens=1024):
    """Helper to call Groq API with adaptive retry on rate-limit errors."""
    client = _get_groq_client()
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=max_tokens,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str or "limit" in error_str:
                if attempt < MAX_RETRIES:
                    wait = RATE_LIMIT_RETRY_WAIT * attempt
                    print(f"  Rate limit hit (attempt {attempt}/{MAX_RETRIES}). Waiting {wait}s...")
                    time.sleep(wait)
                    continue
            raise  # Re-raise non-rate-limit errors or final attempt failures


def _get_marks_guidance(max_score):
    """Return answer length guidance based on marks"""
    if max_score <= 2:
        return "2-4 sentences (short answer)"
    elif max_score <= 5:
        return "5-8 sentences (medium answer with key points)"
    elif max_score <= 8:
        return "8-12 sentences (detailed answer with examples)"
    else:
        return "12-20 sentences (comprehensive, well-structured answer with examples and explanations)"


def phase1_extract_from_book(question, pdf_text, max_score):
    """
    Phase 1: Extract answer strictly from PDF book content.
    Returns the answer text and a quality flag.
    """
    length_guide = _get_marks_guidance(max_score)

    # Truncate PDF to 15,000 chars to stay within free-tier limits
    truncated_text = pdf_text[:15000] if len(pdf_text) > 15000 else pdf_text

    prompt = f"""You are reading a textbook/document. Answer the following exam question using ONLY the document content.

Document Text:
{truncated_text}

Question (worth {max_score} marks): {question}

Instructions:
- Answer using ONLY information from the document above
- Your answer should be approximately {length_guide} — proportional to {max_score} marks
- If only partial information is available, write what you can find and end with: [PARTIAL]
- If no relevant information is found at all, respond with exactly: [NOT_FOUND]
- Structure the answer clearly with key points

Answer:"""

    try:
        answer = _call_groq(
            "You are an exam answer generator that extracts answers from textbook content. "
            "Always produce answers proportional to the marks allocated.",
            prompt,
            max_tokens=1024
        )
        return answer.strip()
    except Exception as e:
        return f"[ERROR] {str(e)}"


def phase2_enhance_with_ai(question, book_answer, max_score):
    """
    Phase 2: If the book answer was weak, partial, or not found,
    enhance it with AI's own knowledge to create a complete model answer.
    """
    length_guide = _get_marks_guidance(max_score)

    if "[NOT_FOUND]" in book_answer:
        # No book content found — generate entirely from AI knowledge
        prompt = f"""You are an expert teacher creating a model answer for an exam.

Question (worth {max_score} marks): {question}

Instructions:
- Provide a comprehensive, accurate model answer using your knowledge
- Your answer should be approximately {length_guide} — proportional to {max_score} marks
- Include key concepts, definitions, examples where appropriate
- Structure the answer clearly so it can be used to evaluate student responses
- Do NOT mention that this is AI-generated

Model Answer:"""
    else:
        # Partial book content found — merge book answer + AI knowledge
        prompt = f"""You are an expert teacher improving a model answer for an exam.

Question (worth {max_score} marks): {question}

Partial answer found in the textbook:
{book_answer}

Instructions:
- The textbook answer above is incomplete or too short for {max_score} marks
- Enhance and expand it with additional accurate information from your knowledge
- Your final answer should be approximately {length_guide} — proportional to {max_score} marks
- Keep the textbook information as the core, add supplementary details around it
- Include key concepts, definitions, examples where appropriate
- Produce a single unified answer (do NOT separate "book part" and "AI part")
- Do NOT mention that this was enhanced or that parts came from AI

Final Model Answer:"""

    try:
        answer = _call_groq(
            "You are an expert teacher creating comprehensive model answers for exams. "
            "Your answers are accurate, well-structured, and proportional to the marks allocated.",
            prompt,
            max_tokens=1024
        )
        return answer.strip()
    except Exception as e:
        # If AI enhancement fails, return whatever we had from the book
        return book_answer.replace("[PARTIAL]", "").strip() if book_answer else f"Error: {str(e)}"


def generate_answer_for_question(question, pdf_text, max_score):
    """
    Two-phase answer generation for a single question:
      Phase 1: Try to extract from book
      Phase 2: If insufficient, enhance with AI general knowledge
    Returns the final model answer string.
    """
    print(f"  Phase 1: Extracting from book...")
    book_answer = phase1_extract_from_book(question, pdf_text, max_score)

    # Decide if Phase 2 is needed
    needs_enhancement = False

    if "[NOT_FOUND]" in book_answer or "[ERROR]" in book_answer:
        print(f"  Phase 1 result: Not found in book. Moving to Phase 2 (AI knowledge)...")
        needs_enhancement = True
    elif "[PARTIAL]" in book_answer:
        print(f"  Phase 1 result: Partial answer found. Moving to Phase 2 (enhancing)...")
        needs_enhancement = True
    else:
        # Check if the answer is too short for the marks
        word_count = len(book_answer.split())
        min_words = int(max_score * 8)  # Roughly 8 words per mark as minimum
        if word_count < min_words:
            print(f"  Phase 1 result: Answer too short ({word_count} words, need ~{min_words}). Moving to Phase 2...")
            needs_enhancement = True
        else:
            print(f"  Phase 1 result: Good answer from book ({word_count} words). Skipping Phase 2.")

    if needs_enhancement:
        # Adaptive wait before Phase 2 call to respect rate limits
        print(f"  Waiting {RATE_LIMIT_WAIT}s for rate limits before Phase 2...")
        time.sleep(RATE_LIMIT_WAIT)

        final_answer = phase2_enhance_with_ai(question, book_answer, max_score)
        return final_answer
    else:
        return book_answer


def extract_answers_from_pdf(questions_data, pdf_path):
    """
    Main orchestrator: For each question, run the two-phase answer extraction.
    Phase 1: Extract from PDF book
    Phase 2: Enhance with AI knowledge if book content is insufficient

    Args:
        questions_data: list of dicts with keys 'question_text' and 'max_score'
        pdf_path: path to the PDF file

    Returns:
        list of dicts with keys 'question_text', 'model_answer', 'max_score'
    """
    print(f"Extracting text from PDF: {pdf_path}")
    pdf_text = extract_text_from_pdf(pdf_path)

    if not pdf_text:
        raise Exception("Could not extract any text from the PDF file.")

    print(f"PDF text extracted: {len(pdf_text)} characters")

    results = []
    total = len(questions_data)

    for idx, q in enumerate(questions_data):
        question_text = str(q['question_text'])
        max_score = float(q['max_score'])

        print(f"\n--- Question {idx + 1}/{total} (Max Marks: {max_score}) ---")
        print(f"  Q: {question_text[:100]}...")

        try:
            final_answer = generate_answer_for_question(question_text, pdf_text, max_score)
        except Exception as e:
            final_answer = f"Error generating answer: {str(e)}"

        results.append({
            'question_text': question_text,
            'model_answer': str(final_answer),
            'max_score': max_score
        })

        # Wait between questions to respect TPM limits (only if more questions remain)
        if idx + 1 < total:
            print(f"  Waiting {RATE_LIMIT_WAIT}s before next question (rate limit)...")
            time.sleep(RATE_LIMIT_WAIT)

    print(f"\n=== All {total} questions processed successfully! ===")
    return results
