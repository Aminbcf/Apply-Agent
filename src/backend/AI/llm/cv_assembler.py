"""cv_assembler.py

Deterministically assembles a moderncv LaTeX document from structured JSON sections.
"""

import logging

logger = logging.getLogger(__name__)

CV_LATEX_TEMPLATE = r"""\documentclass[11pt,a4paper]{moderncv}
\moderncvstyle{banking}
\moderncvcolor{blue}
\usepackage[margin=1.1cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage{fontawesome5}
\name{_FIRST_NAME_}{_LAST_NAME_}
\title{_TITLE_}
\phone[mobile]{_PHONE_}
\email{_EMAIL_}
_LINKEDIN_LINE_
_GITHUB_LINE_
\begin{document}
\makecvtitle

\section{Summary}
\cvitem{}{_SUMMARY_}

\section{Experience}
_EXPERIENCE_ENTRIES_

\section{Education}
_EDUCATION_ENTRIES_

\section{Skills}
_SKILLS_ENTRIES_

\section{Projects}
_PROJECT_ENTRIES_
\end{document}
"""

def _validate_header(sections: dict, safe: dict) -> None:
    if "header" in sections and isinstance(sections["header"], dict):
        for k in safe["header"]:
            safe["header"][k] = sections["header"].get(k) or ""

def _validate_experience(sections: dict, safe: dict) -> None:
    if "experience" in sections and isinstance(sections["experience"], list):
        for exp in sections["experience"]:
            if isinstance(exp, dict):
                safe["experience"].append({
                    "company": exp.get("company", ""),
                    "role": exp.get("role", ""),
                    "location": exp.get("location", ""),
                    "dates": exp.get("dates", ""),
                    "bullets": exp.get("bullets", [])
                })

def _validate_education(sections: dict, safe: dict) -> None:
    if "education" in sections and isinstance(sections["education"], list):
        for edu in sections["education"]:
            if isinstance(edu, dict):
                safe["education"].append({
                    "institution": edu.get("institution", ""),
                    "degree": edu.get("degree", ""),
                    "field": edu.get("field", ""),
                    "dates": edu.get("dates", ""),
                    "gpa": edu.get("gpa", "")
                })

def _validate_projects(sections: dict, safe: dict) -> None:
    if "projects" in sections and isinstance(sections["projects"], list):
        for proj in sections["projects"]:
            if isinstance(proj, dict):
                safe["projects"].append({
                    "name": proj.get("name", ""),
                    "tech": proj.get("tech", ""),
                    "dates": proj.get("dates", ""),
                    "bullets": proj.get("bullets", [])
                })

def validate_cv_sections(sections: dict) -> dict:
    """Fills missing keys with safe defaults to ensure assembly never crashes."""
    safe = {
        "header": {
            "name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "location": "",
            "title": ""
        },
        "summary": {"summary": ""},
        "experience": [],
        "education": [],
        "skills": {"languages": [], "frameworks": [], "tools": [], "other": []},
        "projects": []
    }

    _validate_header(sections, safe)
            
    if "summary" in sections and isinstance(sections["summary"], dict):
        safe["summary"]["summary"] = sections["summary"].get("summary") or ""
        
    _validate_experience(sections, safe)
    _validate_education(sections, safe)

    if "skills" in sections and isinstance(sections["skills"], dict):
        for k in safe["skills"]:
            val = sections["skills"].get(k, [])
            safe["skills"][k] = val if isinstance(val, list) else []

    _validate_projects(sections, safe)

    return safe

def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in regular text."""
    if not text:
        return ""
    # minimal escaping for common characters
    chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    escaped = ""
    for char in text:
        escaped += chars.get(char, char)
    return escaped

def _assemble_experience(data: dict) -> str:
    exp_lines = []
    for exp in data["experience"]:
        title = _escape_latex(exp["role"])
        company = _escape_latex(exp["company"])
        location = _escape_latex(exp["location"])
        dates = _escape_latex(exp["dates"])
        
        bullets_str = ""
        if exp["bullets"]:
            bullets_str = "\\begin{itemize}\n"
            for b in exp["bullets"]:
                bullets_str += f"  \\item {_escape_latex(str(b))}\n"
            bullets_str += "\\end{itemize}"
            
        exp_lines.append(f"\\cventry{{{dates}}}{{{title}}}{{{company}}}{{{location}}}{{}}{{{bullets_str}}}")
    return "\n".join(exp_lines)

def _assemble_education(data: dict) -> str:
    edu_lines = []
    for edu in data["education"]:
        degree_field = _escape_latex(f"{edu['degree']} in {edu['field']}" if edu['field'] else edu['degree'])
        inst = _escape_latex(edu["institution"])
        dates = _escape_latex(edu["dates"])
        gpa = _escape_latex(edu["gpa"])
        edu_lines.append(f"\\cventry{{{dates}}}{{{degree_field}}}{{{inst}}}{{}}{{{gpa}}}{{}}")
    return "\n".join(edu_lines)

def _assemble_projects(data: dict) -> str:
    proj_lines = []
    for proj in data["projects"]:
        name = _escape_latex(proj["name"])
        tech = _escape_latex(proj["tech"])
        dates = _escape_latex(proj["dates"])
        
        bullets_str = ""
        if proj["bullets"]:
            bullets_str = "\\begin{itemize}\n"
            for b in proj["bullets"]:
                bullets_str += f"  \\item {_escape_latex(str(b))}\n"
            bullets_str += "\\end{itemize}"
            
        proj_lines.append(f"\\cventry{{{dates}}}{{{name}}}{{{tech}}}{{}}{{}}{{{bullets_str}}}")
    return "\n".join(proj_lines)

def assemble_cv_latex(sections: dict) -> str:
    """Fills the LaTeX template with the provided sections."""
    CV_LATEX_TEMPLATE = r"""\documentclass[11pt,a4paper]{moderncv}
\moderncvstyle{banking}
\moderncvcolor{blue}
\usepackage[margin=1.1cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage{fontawesome5}
\name{_FIRST_NAME_}{_LAST_NAME_}
\title{_TITLE_}
\phone[mobile]{_PHONE_}
\email{_EMAIL_}
_LINKEDIN_LINE_
_GITHUB_LINE_
\begin{document}
\makecvtitle

\section{Summary}
\cvitem{}{_SUMMARY_}

\section{Experience}
_EXPERIENCE_ENTRIES_

\section{Education}
_EDUCATION_ENTRIES_

\section{Skills}
_SKILLS_ENTRIES_

\section{Projects}
_PROJECT_ENTRIES_
\end{document}
"""
    data = validate_cv_sections(sections)
    latex = CV_LATEX_TEMPLATE

    # Header
    header = data["header"]
    name_parts = header["name"].split(" ", 1)
    first_name = _escape_latex(name_parts[0]) if name_parts else ""
    last_name = _escape_latex(name_parts[1]) if len(name_parts) > 1 else ""
    
    latex = latex.replace("_FIRST_NAME_", first_name)
    latex = latex.replace("_LAST_NAME_", last_name)
    latex = latex.replace("_TITLE_", _escape_latex(header["title"]))
    latex = latex.replace("_PHONE_", _escape_latex(header["phone"]))
    latex = latex.replace("_EMAIL_", _escape_latex(header["email"]))
    
    linkedin = header["linkedin"]
    if linkedin:
        # strip url parts if any
        linkedin = linkedin.replace("https://", "").replace("www.", "").replace("linkedin.com/in/", "")
        latex = latex.replace("_LINKEDIN_LINE_", f"\\social[linkedin]{{{_escape_latex(linkedin)}}}")
    else:
        latex = latex.replace("_LINKEDIN_LINE_", "")
        
    github = header["github"]
    if github:
        github = github.replace("https://", "").replace("www.", "").replace("github.com/", "")
        latex = latex.replace("_GITHUB_LINE_", f"\\social[github]{{{_escape_latex(github)}}}")
    else:
        latex = latex.replace("_GITHUB_LINE_", "")

    # Summary
    latex = latex.replace("_SUMMARY_", _escape_latex(data["summary"]["summary"]))

    # Experience
    latex = latex.replace("_EXPERIENCE_ENTRIES_", _assemble_experience(data))

    # Education
    latex = latex.replace("_EDUCATION_ENTRIES_", _assemble_education(data))

    # Skills
    skills = data["skills"]
    skill_lines = []
    for category, items in skills.items():
        if items:
            cat_name = _escape_latex(category.capitalize())
            items_str = _escape_latex(", ".join(str(i) for i in items))
            skill_lines.append(f"\\cvitem{{{cat_name}}}{{{items_str}}}")
            
    latex = latex.replace("_SKILLS_ENTRIES_", "\n".join(skill_lines))

    # Projects
    latex = latex.replace("_PROJECT_ENTRIES_", _assemble_projects(data))

    return latex
