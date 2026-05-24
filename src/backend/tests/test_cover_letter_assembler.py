from AI.llm.cover_letter_assembler import assemble_cover_letter


def test_assemble_cover_letter_deduplicates_paragraphs():
    sections = {
        "hook": {
            "greeting": "Dear Hiring Manager,",
            "hook": "I am excited about this role.",
        },
        "experience": {
            "experience_paragraph": "I am excited about this role.",
        },
        "value": {
            "value_proposition": "I bring strong execution and collaboration.",
        },
        "closing": {
            "closing": "Sincerely, John Doe",
        },
    }

    text = assemble_cover_letter(sections)

    assert text.count("I am excited about this role.") == 1
    assert "Sincerely, John Doe" not in text


def test_assemble_cover_letter_limits_paragraphs():
    sections = {
        "hook": {
            "greeting": "Dear Hiring Manager,",
            "hook": "Paragraph one.",
        },
        "experience": {
            "experience_paragraph": "Paragraph two.",
        },
        "value": {
            "value_proposition": "Paragraph three.",
        },
        "closing": {
            "closing": "Paragraph four should be dropped.",
        },
    }

    text = assemble_cover_letter(sections)

    assert text.count("\n\n") <= 2
    assert "Paragraph four should be dropped." not in text