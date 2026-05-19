"""
Raw CV Parser - Converts unstructured/semi-structured CV text into standardized format.
Handles common CV formats including sections for Summary, Highlights, Experience, Education, and Skills.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ParsedExperience:
    """Represents a single job experience."""
    title: str
    company: str
    location: str
    start_date: str
    end_date: str
    description: str
    accomplishments: List[str]


@dataclass
class ParsedEducation:
    """Represents an education entry."""
    degree: str
    field: str
    year: str
    institution: str
    location: str


class RawCVParser:
    """Parse raw CV text into structured format."""
    
    def __init__(self):
        """Initialize the parser."""
        self.section_patterns = {
            'summary': r'(?:summary|overview|professional summary|executive summary)',
            'highlights': r'(?:highlights|key skills|core competencies|technical summary)',
            'experience': r'(?:experience|professional experience|work history|career history)',
            'education': r'(?:education|academic)',
            'skills': r'(?:skills|technical skills|core skills|competencies)',
        }
    
    def parse(self, cv_text: str) -> Dict:
        """
        Parse raw CV text into structured format.
        
        Args:
            cv_text: Raw CV text
            
        Returns:
            Structured CV dictionary
        """
        cv_data = {
            'title': self._extract_title(cv_text),
            'summary': self._extract_summary(cv_text),
            'highlights': self._extract_highlights(cv_text),
            'experience': self._extract_experience(cv_text),
            'education': self._extract_education(cv_text),
            'skills': self._extract_skills(cv_text),
        }
        
        return {k: v for k, v in cv_data.items() if v}  # Remove empty fields
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract job title from CV (usually first line or first capitalized phrase)."""
        lines = text.strip().split('\n')
        
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) > 5 and len(line) < 150:
                # Check if it looks like a title (mostly capitalized, no URLs)
                if line.isupper() or (line.count(' ') > 0 and line[0].isupper()):
                    if 'http' not in line.lower() and '@' not in line:
                        return line
        
        return None
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract summary section."""
        summary_match = re.search(
            r'(?:summary|overview|professional summary|executive summary)\s*\n(.*?)(?=\n(?:highlights|experience|education|skills|[A-Z][A-Z\s]{3,})\s*\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if summary_match:
            summary_text = summary_match.group(1).strip()
            # Clean up and limit length
            summary_text = re.sub(r'\s+', ' ', summary_text)
            return summary_text[:2000] if summary_text else None
        
        return None
    
    def _extract_highlights(self, text: str) -> Optional[Dict[str, List[str]]]:
        """Extract highlights/key skills section."""
        highlights_match = re.search(
            r'(?:highlights|key skills|core competencies|technical summary)\s*\n(.*?)(?=\n(?:experience|education|skills)\s*\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not highlights_match:
            return None
        
        highlights_text = highlights_match.group(1).strip()
        highlights_dict = {}
        
        # Parse categories like "OS/Platforms:", "Networking:", etc.
        categories = re.split(r'\n(?=[A-Za-z\s/]+:)', highlights_text)
        
        for category in categories:
            lines = category.strip().split('\n')
            if not lines:
                continue
            
            # First line is usually the category
            cat_line = lines[0]
            if ':' in cat_line:
                cat_name = cat_line.split(':')[0].strip()
                # Get items from this category
                items = []
                for line in lines[1:]:
                    line = line.strip()
                    if line:
                        items.append(line)
                
                if items:
                    highlights_dict[cat_name] = items
        
        return highlights_dict if highlights_dict else None
    
    def _extract_experience(self, text: str) -> Optional[List[Dict]]:
        """Extract experience section."""
        exp_match = re.search(
            r'(?:experience|professional experience|work history|career history)\s*\n(.*?)(?=\n(?:education|skills)\s*\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not exp_match:
            return None
        
        exp_text = exp_match.group(1).strip()
        experiences = []
        
        # Split by job titles (usually at start of lines with job title pattern)
        # Look for patterns like "Job Title" followed by dates or "Company Name"
        job_blocks = re.split(
            r'\n(?=[A-Z][A-Za-z\s/\-]+\n(?:\s*(?:January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2})[^\n]*to[^\n]*|(?:Company|Organization)))',
            exp_text
        )
        
        for block in job_blocks:
            if not block.strip():
                continue
            
            job_data = self._parse_job_block(block)
            if job_data:
                experiences.append(job_data)
        
        return experiences if experiences else None
    
    def _parse_job_block(self, block: str) -> Optional[Dict]:
        """Parse a single job experience block."""
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        job_data = {
            'title': None,
            'company': None,
            'location': None,
            'start_date': None,
            'end_date': None,
            'description': '',
            'accomplishments': []
        }
        
        idx = 0
        
        # Extract job title (first line)
        if idx < len(lines):
            job_data['title'] = lines[idx]
            idx += 1
        
        # Extract dates and company info
        date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2})\s+(\d{4})\s+to\s+(January|February|March|April|May|June|July|August|September|October|November|December|Current|\d{1,2})\s+(\d{4}|Current)'
        
        for i in range(idx, min(idx + 5, len(lines))):
            line = lines[i]
            
            # Check for dates
            date_match = re.search(date_pattern, line)
            if date_match:
                job_data['start_date'] = f"{date_match.group(1)} {date_match.group(2)}"
                job_data['end_date'] = f"{date_match.group(3)} {date_match.group(4)}" if date_match.group(4) else "Current"
                idx = i + 1
                break
            
            # Check for company
            if 'company' in line.lower() or 'organization' in line.lower():
                # Next lines might have company name and location
                continue
            
            # If it doesn't match date pattern and we don't have company yet
            if not job_data['company'] and len(line) < 100:
                job_data['company'] = line
                idx = i + 1
                break
        
        # Extract location
        for i in range(idx, min(idx + 3, len(lines))):
            line = lines[i]
            if ',' in line and len(line) < 50:  # Likely a location
                job_data['location'] = line
                idx = i + 1
                break
        
        # Rest is description and accomplishments
        remaining = '\n'.join(lines[idx:])
        
        # Split description and accomplishments
        # Accomplishments often start with "Selected Accomplishments", "Accomplishments", or bullet points
        accomplishment_match = re.search(
            r'(?:selected accomplishments|accomplishments)(.*?)(?:\n[A-Z]|\Z)',
            remaining,
            re.IGNORECASE | re.DOTALL
        )
        
        if accomplishment_match:
            description = remaining[:accomplishment_match.start()].strip()
            accomplishments_text = accomplishment_match.group(1).strip()
            
            # Parse accomplishment bullets
            accomplishments = [
                line.strip() for line in accomplishments_text.split('\n')
                if line.strip() and not line.strip().startswith(('Selected', 'Accomplishments'))
            ]
            job_data['accomplishments'] = accomplishments
        else:
            description = remaining
        
        job_data['description'] = description.strip()
        
        return job_data
    
    def _extract_education(self, text: str) -> Optional[List[Dict]]:
        """Extract education section."""
        edu_match = re.search(
            r'(?:education|academic)\s*\n(.*?)(?=\n(?:skills)\s*\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not edu_match:
            return None
        
        edu_text = edu_match.group(1).strip()
        educations = []
        
        # Split by degree lines
        degree_blocks = re.split(r'\n(?=[A-Z][a-z]+\s+of\s+[A-Z])', edu_text)
        
        for block in degree_blocks:
            if not block.strip():
                continue
            
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if not lines:
                continue
            
            edu_data = {
                'degree': lines[0] if lines else None,
                'field': None,
                'year': None,
                'institution': None,
                'location': None
            }
            
            # Look for field, year, institution
            for line in lines[1:]:
                # Check for year (4 digits)
                year_match = re.search(r'\d{4}', line)
                if year_match and not edu_data['year']:
                    edu_data['year'] = year_match.group()
                
                # Check for institution (often in ALL CAPS or specific patterns)
                if 'university' in line.lower() or 'college' in line.lower() or 'school' in line.lower():
                    edu_data['institution'] = line
                
                # Location
                if ',' in line and len(line) < 100:
                    edu_data['location'] = line
                
                # Field of study
                if '/' in line or ':' not in line and len(line) < 100 and 'university' not in line.lower():
                    edu_data['field'] = line
            
            educations.append(edu_data)
        
        return educations if educations else None
    
    def _extract_skills(self, text: str) -> Optional[List[str]]:
        """Extract skills section."""
        skills_match = re.search(
            r'(?:skills|technical skills|core skills|competencies)\s*\n(.*?)(?:\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not skills_match:
            return None
        
        skills_text = skills_match.group(1).strip()
        
        # Parse skills - can be comma-separated, newline-separated, or tagged
        skills = []
        
        # Try comma-separated first
        if ',' in skills_text:
            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
        else:
            # Try newline-separated
            skills = [s.strip() for s in skills_text.split('\n') if s.strip()]
        
        # Clean up
        skills = [s for s in skills if len(s) > 1 and len(s) < 100]
        
        return skills if skills else None


def parse_raw_cv(cv_text: str) -> Dict:
    """
    Convenience function to parse raw CV text.
    
    Args:
        cv_text: Raw CV text
        
    Returns:
        Structured CV dictionary
    """
    parser = RawCVParser()
    return parser.parse(cv_text)


# Example usage
if __name__ == "__main__":
    sample_cv = """
    DIRECTOR OF INFORMATION TECHNOLOGY AND ANALYTICS
    
    Summary
    Accomplished senior manager with over 15 years of experience leading complex projects and managing resources to optimize enterprise
    technology and support business objectives. 
    Committed to quality and service excellence with aptitude for launching new technology platforms.
    
    Highlights
    OS/Platforms: 
    Microsoft Windows Server 2008/2012, Exchange 2010, IIS, Active Directory, DNS
    Networking: 
    Cisco LAN/WAN (ASA/switching), TCP/IP, VPN, VoIP, SIP
    
    Experience
    Director of Information Technology and Analytics
    January 2005 to Current
    Company Name
    City, State
    
    Market-leading global credit asset management firm with $4 Billion AUM and over 120 employees worldwide.
    Directed the firm's word-wide Information Technology strategy.
    
    Selected Accomplishments
    Developed and led a technology strategy for the firm that supports strong business alignments.
    Enabled revenue growth by leading the timely deployment of high-performance virtual computing environment.
    
    Education
    Bachelor of Science: Psychology/History, 1998
    Rutgers University
    City, State
    
    Skills
    Active Directory, Antivirus, asset management, Backup Exec, budget, business systems, cabling, CISCO
    """
    
    parsed = parse_raw_cv(sample_cv)
    print("Parsed CV:")
    print(parsed)
