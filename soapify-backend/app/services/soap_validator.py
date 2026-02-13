import re

REQUIRED_SECTIONS = [
    "SUBJECTIVE:",
    "OBJECTIVE:",
    "ASSESSMENT:",
    "PLAN:",
]

FORBIDDEN_PATTERNS = [
    r"^\s*-\s+",        # bullet point
    r"^\s*\*\s+",      # bullet point
    r"^\s*\d+\.\s+",   # numbered list
    r"```",            # code blocks
    r"^#+\s+",         # markdown headers
]

ALLOWED_EMPTY_VALUE = "not mentioned"


def validate_soap_output(text: str) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, "Empty output"

    clean_text = text.strip()

    # Must start exactly with SUBJECTIVE
    if not clean_text.startswith("SUBJECTIVE:"):
        return False, "SOAP must start with SUBJECTIVE"

    # All sections present
    for section in REQUIRED_SECTIONS:
        if section not in clean_text:
            return False, f"Missing section: {section}"

    # Correct order
    positions = [clean_text.index(sec) for sec in REQUIRED_SECTIONS]
    if positions != sorted(positions):
        return False, "Sections out of order"

    # Forbidden markdown patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, clean_text, re.MULTILINE):
            return False, "Forbidden markdown formatting detected"

    # Validate content under each section
    for i, section in enumerate(REQUIRED_SECTIONS):
        start = clean_text.index(section) + len(section)
        end = (
            clean_text.index(REQUIRED_SECTIONS[i + 1])
            if i < len(REQUIRED_SECTIONS) - 1
            else len(clean_text)
        )

        content = clean_text[start:end].strip().lower()

        if not content:
            return False, f"Empty content under {section}"

        if content == ALLOWED_EMPTY_VALUE or content == f"{ALLOWED_EMPTY_VALUE}.":
            continue

    return True, "Valid SOAP"
