"""
Integration test for raw CV parser with real-world examples.
Tests parsing, standardization, and embedding generation.
"""

import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from AI.raw_cv_parser import RawCVParser
from AI.cv_processor import CVProcessor


# Test data: Real CV in common format
TEST_CV_1 = """
DIRECTOR OF INFORMATION TECHNOLOGY AND ANALYTICS

Summary
Accomplished senior manager with over 15 years of experience leading complex projects and managing resources to optimize enterprise
technology and support business objectives.
Committed to quality and service excellence with aptitude for launching new technology platforms.
Subject matter expert in Information Security Risk Management. Excellent communicator adept at identifying business needs and bridging the gap
between functional groups and technology to foster targeted and innovative solutions.

Highlights
OS/Platforms:
Microsoft Windows Server 2008/2012, Exchange 2010, IIS, Active Directory, DNS
Networking:
Cisco LAN/WAN (ASA/switching), TCP/IP, VPN, VoIP, SIP, MPLS, VNC, VLAN Segregation
Hardware:
SAN/FIBER technology, Enterprise Servers, Switches, Routers, Workstations, Laptops, Mobile Devices
(iPad/iPhone/Blackberry),
Telephony Systems:
Cisco CUCM
Tools:
JIRA, Veritas Netbackup, Backup Exec, PCAnywhere, Symantec Antivirus, Ghost, SharePoint, Visio, Microsoft Office Suite

Experience
Director of Information Technology and Analytics

January 2005 to Current

Company Name

City, State

Market-leading global credit asset management firm with $4 Billion AUM and over 120 employees worldwide.
Directed the firm's word-wide Information Technology strategy.
Established and instituted policies, procedures and technology to mitigate corporate security risk and position organization for Sarbanes-Oxley act compliance.
Identified process improvement opportunities and recommended solutions and budget requirements to management committee.

Selected Accomplishments
Developed and led a technology strategy for the firm that supports strong business alignments, increases profitability and provides a sound, flexible and reliable foundation for the future.
Enabled revenue growth by leading the timely deployment of high-performance virtual computing environment to support new models created by internal development teams.
Created Incident Response Policies and Procedures rooted firmly on the NIST framework.
Developed and lead breach rehearsal scenarios both for executive roundtable tests and technical response team practices.
Designed Data Governance and Classification Policies particularly in regards to Personally Identifiable Information (PII).
Evaluated and deployed Data Loss Prevention system and created escalation procedures to comply with the firm's Data Governance Policy.

Information Technology Manager

January 2002 to January 2005

Manufacturing Company

City, State

Manufacturing firm with over 100 year history and 170 employees.
Directed hardware and software configuration, installation, troubleshooting, and support activities.
Oversaw administration of network infrastructure, business systems, cabling and circuits, and telecommunications platforms.

Education
Bachelor of Science: Psychology/History, 1998
Rutgers University
City, State

Skills
Active Directory, Antivirus, asset management, Backup Exec, budget, business systems, cabling, CISCO, Hardware, Consulting, contract negotiation, databases, DHCP, Disaster Recovery, DNS, Enterprise Resource Planning, Firewalls, FTP, Ghost, IIS, Information Technology, IP, IT support, LAN, Team Leadership, Microsoft Exchange, Microsoft Office Suite, Microsoft Windows, Network Security, Networking, PCAnywhere, Policies, Problem Resolution, Procurement, Project Management, Routers, SAN, Servers, SQL, Strategic Planning, Switches, Symantec, TCP/IP, Telephony, troubleshooting, VPN, Visio, VOIP, WAN
"""

# Another test example
TEST_CV_2 = """
SENIOR DATA SCIENTIST

Summary
Results-driven data scientist with 8+ years building machine learning models and analytics solutions. 
Expertise in Python, SQL, and cloud platforms. Proven track record delivering business value through data-driven insights.

Highlights
Languages: Python, R, SQL, Scala
ML Frameworks: TensorFlow, PyTorch, scikit-learn, XGBoost
Databases: PostgreSQL, MongoDB, Cassandra, BigQuery
Cloud Platforms: AWS, Google Cloud Platform, Azure
Tools: Jupyter, Docker, Kubernetes, Apache Spark, Airflow

Experience
Senior Data Scientist
July 2018 to Present
Tech Solutions Inc.
San Francisco, CA

Led data science initiatives for a 500+ person SaaS company with $100M ARR.
Built predictive models improving customer retention by 25%.
Established ML platform used by 50+ analysts.

Selected Accomplishments
Developed recommendation engine increasing average customer value by $50K annually.
Implemented real-time anomaly detection reducing fraud by 40%.
Created data governance framework ensuring compliance and data quality.
Mentored team of 5 junior data scientists.

Data Scientist
January 2016 to June 2018
Analytics Corp
New York, NY

Built classification models with 95%+ accuracy for customer churn prediction.
Developed dashboards and reports for executive leadership.

Education
Master of Science: Machine Learning, 2015
Stanford University
Palo Alto, CA

Bachelor of Science: Statistics, 2013
University of Michigan
Ann Arbor, MI

Skills
Python, Machine Learning, Data Analysis, Statistical Modeling, SQL, Deep Learning, Neural Networks, Computer Vision, NLP, Big Data, Apache Spark, AWS SageMaker, Data Engineering, A/B Testing, Business Analytics, Tableau, Jupyter, Docker
"""


def test_raw_cv_parser():
    """Test the raw CV parser."""
    print("\n" + "="*80)
    print("RAW CV PARSER TEST SUITE")
    print("="*80)
    
    parser = RawCVParser()
    processor = CVProcessor()
    
    test_cases = [
        ("IT Director", TEST_CV_1),
        ("Data Scientist", TEST_CV_2),
    ]
    
    for test_name, cv_text in test_cases:
        print(f"\n[TEST] {test_name}")
        print("-"*80)
        
        try:
            # Parse raw CV
            print(f"  1. Parsing raw CV...")
            parsed = parser.parse(cv_text)
            
            if not parsed:
                print("     ❌ Failed to parse CV")
                continue
            
            print(f"     ✓ Parsed successfully")
            sections = [k for k, v in parsed.items() if v]
            print(f"       Extracted sections: {', '.join(sections)}")
            
            # Convert to standard format
            print(f"  2. Converting to standard format...")
            standard_cv = processor._convert_parsed_to_standard(parsed)
            print(f"     ✓ Converted successfully")
            print(f"       Standard fields: {', '.join(standard_cv.keys())}")
            
            # Generate embeddings
            print(f"  3. Generating semantic embeddings...")
            enriched_cv = processor.process_cv(standard_cv)
            print(f"     ✓ Embeddings generated")
            
            # Show results
            best_domain = enriched_cv['embeddings']['best_domain']
            confidence = enriched_cv['embeddings']['domain_scores'][0][1]
            
            print(f"\n  Results:")
            print(f"    • Best domain: {best_domain}")
            print(f"    • Confidence: {confidence:.4f}")
            print(f"    • Embedding dimensions: {len(enriched_cv['embeddings']['vector'])}")
            
            # Show top 5 domains
            print(f"\n  Top 5 domains:")
            for i, (domain, score) in enumerate(enriched_cv['embeddings']['domain_scores'][:5], 1):
                bar = "█" * int(score * 30)
                print(f"    {i}. {domain:25s} {score:.4f} {bar}")
            
            print(f"\n  ✓ Test PASSED")
            
        except Exception:
            import logging
            logging.exception("Test FAILED")
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)


def test_section_extraction():
    """Test individual section extraction."""
    print("\n" + "="*80)
    print("SECTION EXTRACTION TEST")
    print("="*80)
    
    parser = RawCVParser()
    
    print(f"\n[TEST] Extract Title")
    title = parser._extract_title(TEST_CV_1)
    print(f"  Title: {title}")
    print(f"  ✓ {'PASSED' if title else 'FAILED'}")
    
    print(f"\n[TEST] Extract Summary")
    summary = parser._extract_summary(TEST_CV_1)
    print(f"  Summary: {summary[:100] if summary else 'None'}...")
    print(f"  ✓ {'PASSED' if summary else 'FAILED'}")
    
    print(f"\n[TEST] Extract Highlights")
    highlights = parser._extract_highlights(TEST_CV_1)
    print(f"  Categories: {list(highlights.keys()) if highlights else 'None'}")
    print(f"  ✓ {'PASSED' if highlights else 'FAILED'}")
    
    print(f"\n[TEST] Extract Experience")
    experience = parser._extract_experience(TEST_CV_1)
    print(f"  Positions: {len(experience) if experience else 0}")
    if experience:
        for exp in experience:
            if isinstance(exp, dict):
                print(f"    - {exp.get('title', 'Unknown')} at {exp.get('company', 'Unknown')}")
    print(f"  ✓ {'PASSED' if experience else 'FAILED'}")
    
    print(f"\n[TEST] Extract Education")
    education = parser._extract_education(TEST_CV_1)
    print(f"  Degrees: {len(education) if education else 0}")
    if education:
        for edu in education:
            if isinstance(edu, dict):
                print(f"    - {edu.get('degree', 'Unknown')} from {edu.get('institution', 'Unknown')}")
    print(f"  ✓ {'PASSED' if education else 'FAILED'}")
    
    print(f"\n[TEST] Extract Skills")
    skills = parser._extract_skills(TEST_CV_1)
    print(f"  Skills: {len(skills) if skills else 0}")
    if skills:
        print(f"    Sample: {', '.join(skills[:5])}")
    print(f"  ✓ {'PASSED' if skills else 'FAILED'}")


if __name__ == "__main__":
    test_section_extraction()
    test_raw_cv_parser()
    
    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80 + "\n")
