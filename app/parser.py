import re
from typing import List, Optional

from .schemas import ParsedFields, Question


# Common patterns are kept compiled for efficiency and clarity.
NAME_PATTERNS = [
    re.compile(r"Name\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
    re.compile(r"Student\s+Name\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
]

EXAM_NAME_PATTERNS = [
    re.compile(r"Exam\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
    re.compile(r"Examination\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
]

ROLL_NO_PATTERNS = [
    re.compile(r"Roll\s*No\.?\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
    re.compile(r"Roll\s*Number\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
]

TOTAL_MARKS_PATTERNS = [
    re.compile(r"Total\s+Marks\s*[:\-]\s*(?P<value>\d+)", re.IGNORECASE),
    re.compile(r"Maximum\s+Marks\s*[:\-]\s*(?P<value>\d+)", re.IGNORECASE),
]


QUESTION_BLOCK_PATTERN = re.compile(
    r"""
    (?:Q(?:uestion)?\s*        # 'Q' or 'Question'
     (?P<num>\d+)[\.\):\-]?)   # capture the question number
    \s*
    (?P<text>                  # capture question text
        (?:.|\n)*?             # non-greedy up to next question or end
    )
    (?=                        # lookahead: next question or end
        \nQ(?:uestion)?\s*\d+  # another question starts
        | \Z                   # or end of string
    )
""",
    re.IGNORECASE | re.VERBOSE,
)

MARKS_INLINE_PATTERN = re.compile(
    r"\b(\d+)\s*marks\b", re.IGNORECASE
)


def _extract_first_match(text: str, patterns: list[re.Pattern]) -> Optional[str]:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = match.group("value").strip()
            # Clean trailing dots etc.
            return re.sub(r"[\.]+$", "", value).strip()
    return None


def _extract_questions(text: str) -> List[Question]:
    questions: List[Question] = []
    for match in QUESTION_BLOCK_PATTERN.finditer(text):
        num_str = match.group("num")
        q_text = match.group("text") or ""
        marks = _extract_marks_from_question(q_text)

        try:
            num = int(num_str)
        except ValueError:
            continue

        questions.append(
            Question(
                question_number=num,
                question_text=q_text.strip(),
                marks=marks,
            )
        )
    return questions


def _extract_marks_from_question(q_text: str) -> Optional[int]:
    m = MARKS_INLINE_PATTERN.search(q_text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def parse_text_to_fields(text: str) -> ParsedFields:
    """
    Parse OCR text to extract structured exam/student fields.
    """
    name = _extract_first_match(text, NAME_PATTERNS)
    exam_name = _extract_first_match(text, EXAM_NAME_PATTERNS)
    roll_number = _extract_first_match(text, ROLL_NO_PATTERNS)
    total_marks_str = _extract_first_match(text, TOTAL_MARKS_PATTERNS)
    total_marks = int(total_marks_str) if total_marks_str and total_marks_str.isdigit() else None

    questions = _extract_questions(text)

    return ParsedFields(
        name=name,
        exam_name=exam_name,
        roll_number=roll_number,
        total_marks=total_marks,
        questions=questions,
    )
