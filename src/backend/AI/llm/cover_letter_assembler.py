"""cover_letter_assembler.py

Assembles a formatted plain-text cover letter from structured JSON sections.
"""

COVER_LETTER_TEMPLATE = """{greeting}

{hook}

{experience_paragraph}

{value_proposition}

{closing}
"""

_BANNED_PHRASES = (
    "references",
    "références",
    "your experience paragraph here",
    "your value proposition paragraph here",
    "your compelling opening hook here",
    "your closing sentence here",
    "your professional summary here",
    "output schema",
    "example json",
    "instructions:",
)


def _dedupe_paragraphs(text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    deduped = []
    seen = set()

    for paragraph in paragraphs:
        normalized = " ".join(paragraph.split())
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(paragraph)

    return "\n\n".join(deduped)


def _limit_paragraphs(text: str, max_paragraphs: int = 3) -> str:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    cleaned = []

    for paragraph in paragraphs:
        lower_paragraph = paragraph.lower()
        if any(phrase in lower_paragraph for phrase in _BANNED_PHRASES):
            continue
        cleaned.append(paragraph)
        if len(cleaned) >= max_paragraphs:
            break

    return "\n\n".join(cleaned)

def validate_cl_sections(sections: dict) -> dict:
    safe = {
        "hook": {
            "greeting": "Dear Hiring Manager,",
            "hook": ""
        },
        "experience": {
            "experience_paragraph": ""
        },
        "value": {
            "value_proposition": ""
        },
        "closing": {
            "closing": "Thank you for your time and consideration."
        }
    }
    
    if "hook" in sections and isinstance(sections["hook"], dict):
        safe["hook"]["greeting"] = sections["hook"].get("greeting") or safe["hook"]["greeting"]
        safe["hook"]["hook"] = sections["hook"].get("hook", "")
        
    if "experience" in sections and isinstance(sections["experience"], dict):
        safe["experience"]["experience_paragraph"] = sections["experience"].get("experience_paragraph", "")
        
    if "value" in sections and isinstance(sections["value"], dict):
        safe["value"]["value_proposition"] = sections["value"].get("value_proposition", "")
        
    if "closing" in sections and isinstance(sections["closing"], dict):
        safe["closing"]["closing"] = sections["closing"].get("closing", "")
        
    return safe

def assemble_cover_letter(sections: dict) -> str:
    """Assembles a cover letter from sections."""
    data = validate_cl_sections(sections)
    
    cl_text = COVER_LETTER_TEMPLATE.format(
        greeting=data["hook"]["greeting"],
        hook=data["hook"]["hook"],
        experience_paragraph=data["experience"]["experience_paragraph"],
        value_proposition=data["value"]["value_proposition"],
        closing=data["closing"]["closing"]
    )
    
    # Strip excessive newlines and remove accidental duplicate paragraphs.
    cl_text = _dedupe_paragraphs(cl_text)
    cl_text = _limit_paragraphs(cl_text)
    
    return cl_text
