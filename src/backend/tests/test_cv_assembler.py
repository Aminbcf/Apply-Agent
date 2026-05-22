import pytest
from AI.llm.cv_assembler import assemble_cv_latex, validate_cv_sections

def test_validate_cv_sections_empty():
    safe = validate_cv_sections({})
    assert safe["header"]["name"] == ""
    assert safe["experience"] == []

def test_validate_cv_sections_partial():
    safe = validate_cv_sections({
        "header": {"name": "John Doe"}
    })
    assert safe["header"]["name"] == "John Doe"
    assert safe["header"]["email"] == ""
    assert safe["experience"] == []

def test_assemble_cv_latex():
    sections = {
        "header": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "github.com/johndoe",
            "location": "NY",
            "title": "Engineer"
        },
        "summary": {"summary": "A good engineer."},
        "experience": [
            {
                "company": "Tech",
                "role": "Dev",
                "location": "NY",
                "dates": "2020-2021",
                "bullets": ["Did stuff", "Did more stuff"]
            }
        ],
        "education": [],
        "skills": {"languages": ["Python", "C++"]},
        "projects": []
    }
    
    latex = assemble_cv_latex(sections)
    
    assert "\\name{John}{Doe}" in latex
    assert "\\title{Engineer}" in latex
    assert "\\email{john@example.com}" in latex
    assert "\\social[linkedin]{johndoe}" in latex
    assert "\\social[github]{johndoe}" in latex
    assert "A good engineer." in latex
    assert "\\cventry{2020-2021}{Dev}{Tech}{NY}{}" in latex
    assert "\\item Did stuff" in latex
    assert "\\cvitem{Languages}{Python, C++}" in latex
