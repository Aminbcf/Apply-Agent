"""cover_letter_assembler.py

Assembles a formatted plain-text cover letter from structured JSON sections.
"""

COVER_LETTER_TEMPLATE = """{greeting}

{hook}

{experience_paragraph}

{value_proposition}

{closing}
"""

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
    
    # Strip excessive newlines
    cl_text = "\n\n".join(line.strip() for line in cl_text.split("\n\n") if line.strip())
    
    return cl_text
