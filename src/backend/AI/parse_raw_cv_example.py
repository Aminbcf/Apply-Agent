"""
Example demonstrating raw CV parsing and semantic embedding generation.
Shows how to process raw CVs from common formats.
"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from AI.raw_cv_parser import parse_raw_cv
from AI.cv_processor import CVProcessor


# Raw CV text from Kaggle dataset format
SAMPLE_RAW_CV = """
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
 
January 2005
 
to 
Current
 
Company Name
 
City
 
, 
State

Market-leading global credit asset management firm with $4 Billion AUM and over 120 employees worldwide.
Directed the firm's word-wide Information Technology strategy.
Established and instituted policies, procedures and technology to mitigate corporate security risk and position ZAIS for Sarbanes-Oxley act
compliance.
Identified process improvement opportunities and recommended solutions and budget requirements to management committee.
Managed team of 6 resources responsible for technology management and support operations encompassing all aspects of IT infrastructure
including workstations, server platforms, IP telephony, L3 network infrastructure, network security, disaster recovery, Storage Area
Networks and videoconferencing.
Directed project teams through all lifecycle phases handling technical escalation events.
Evaluated and deployed DLP solution.
Chairman of the firm's cybersecurity committee responsible for advancing the firm's security posture.
Selected Accomplishments Developed and led a technology strategy for the firm that supports strong business alignments, increases
profitability and provides a sound, flexible and reliable foundation for the future.
Enabled revenue growth by leading the timely deployment of high-performance virtual computing environment to support new models
created by internal development teams.
Created Incident Response Policies and Procedures rooted firmly on the NIST framework.
Developed and lead breach rehearsal scenarios both for executive roundtable tests and technical response team practices.
Designed Data Governance and Classification Policies particularly in regards to Personally Identifiable Information (PII).
Evaluated and deployed Data Loss Prevention system (Symantec) and created escalation procedures to comply with the firm's Data
Governance Policy.
Managed all security vendor relationships through the contract negotiation lifecycle and Service Level Agreement reviews.
Developed associates to their fullest potential by providing challenging opportunities that enhanced associate's career growth.
Recruited and developed appropriate talent pool to insure adequate bench strength and succession planning.
Managed logistics, procurement and deployment of IT infrastructure in Dallas, Baton Rouge, Shanghai, Dublin, London, Singapore and
Tokyo locations inclusive of establishing a sustainable model for support.
Established a viable Disaster Recovery strategy with a physical to virtual solution and liaison with all business units to generate the firm's
Business Continuity plan.
Spearheaded the analog to VOIP conversion of ZAIS IPT and video infrastructures (Cisco CUCM environment).
Transformed IT support and organizational interaction practices, fostering strong, collaborative work environment.
while developing robust help desk systems and processes for improved trouble ticket initiation and visibility.
Led the firm's Cybersecurity enhancement effort by managing the design, implementation and maintenance of the 
Advanced Threat
Protection system, Next Generation Firewalls and Mobile Computing Security.
Developed the firms Cybersecurity Policy and Incident Response Team firmly rooted on the NIST framework.
Responded to audit requests from potential and current investors, met with them to discuss finding, and guided them through the due
diligence process.
Responded to external auditors and lead remediation efforts if needed.
Reported all audits to the executive board.
Fostered a culture of security awareness in the firm by obtaining executive level support for Cybersecurity initiatives and enabling
acceptance of security measures through user education.

Information Technology Manager
 
January 2002
 
to 
January 2005
 
Company Name
 
City
 
, 
State

Manufacturing firm with over 100 year history and 170 employees.
Directed hardware and software configuration, installation, troubleshooting, and support activities.
Oversaw administration of network infrastructure, business systems, cabling and circuits, and telecommunications platforms.Established and managed relationships with technology vendors and service providers.
Monitored and tracked call volumes, service requests, and performance metrics.
Led work order documentation and change request management.
Selected Accomplishments Designed and led Windows 2003 migration team.
Administered CISCO multi-VLAN layer 3 switched LAN/WAN.
Designed and administered CISCO VPN solution.
Led the procurement, configuration and administration of all infrastructure projects.
Engineered and deployed Microsoft Exchange 2003 solution including web access/spam protection/security.
Planned and implemented Enterprise Resource Planning project.
Responsible for disaster recovery plan/execution.
Supervised IT staff and coordinated all consultants.

Education
Bachelor of Science: Psychology/History, 1998
Rutgers University
City, State

Skills
Active Directory, Antivirus, asset management, Backup Exec, budget, business systems, cabling, CISCO, Competitive, Hardware, Consulting,
contract negotiation, conversion, credit, client, databases, DHCP, Disaster Recovery, documentation, DNS, due diligence, Enterprise Resource
Planning, Firewalls, FTP, Ghost, help desk, IIS, imaging, Information Technology, IP, IT support, LAN, Laptops, Team Leadership, logistics,
Loss Prevention, managing, Market, Mentoring, access, Exchange, Microsoft Exchange 2003, Microsoft Office Suite, SharePoint, Microsoft
Windows, Windows, Windows 2000, Windows NT, word, migration, Enterprise, network security, network, Networking, Networks, Next, OS,
organizational, PCAnywhere, Policies, Problem Resolution, processes, process improvement, procurement, Project Management, Proposal
Development, Requirements Analysis, Routers, SAN, Sarbanes-Oxley, Servers, Service Level Agreement, sound, SQL, strategy, Strategic
Planning, Switches, Symantec, TCP/IP, telecommunications, Telephony, troubleshooting, upgrades, upgrade, Veritas, Veritas Netbackup, video,
VPN, Visio, VOIP, WAN
"""


def main():
    """Run parsing and embedding example."""
    
    print("\n" + "=" * 80)
    print("RAW CV PARSING AND SEMANTIC EMBEDDING EXAMPLE")
    print("=" * 80)
    
    print("\n[1] Parsing raw CV text...")
    print("-" * 80)
    
    # Step 1: Parse raw CV
    parsed_cv = parse_raw_cv(SAMPLE_RAW_CV)
    
    print(f"\n✓ Successfully parsed CV!")
    print(f"\nExtracted sections:")
    for section, value in parsed_cv.items():
        if value:
            if isinstance(value, str):
                print(f"  • {section}: {value[:80]}...")
            elif isinstance(value, list):
                print(f"  • {section}: {len(value)} items")
                if len(value) <= 3:
                    for item in value:
                        print(f"    - {item}")
            elif isinstance(value, dict):
                print(f"  • {section}: {len(value)} categories")
                for key in list(value.keys())[:3]:
                    print(f"    - {key}: {len(value[key])} items")
    
    print("\n[2] Converting to standard format...")
    print("-" * 80)
    
    # Step 2: Convert to standard format
    processor = CVProcessor()
    standard_cv = processor._convert_parsed_to_standard(parsed_cv)
    
    print(f"\n✓ Converted to standard format:")
    for key, value in standard_cv.items():
        if value:
            if isinstance(value, str):
                preview = value[:100].replace('\n', ' ')
                print(f"  • {key}: {preview}...")
            elif isinstance(value, list):
                print(f"  • {key}: {len(value)} items")
                for item in value[:3]:
                    print(f"    - {item[:60]}")
    
    print("\n[3] Generating semantic embeddings...")
    print("-" * 80)
    
    # Step 3: Process with embeddings
    enriched_cv = processor.process_cv(standard_cv)
    
    print(f"\n✓ Successfully generated embeddings!")
    print(f"\nEmbedding Results:")
    print(f"  • Best matching domain: {enriched_cv['embeddings']['best_domain']}")
    print(f"  • Embedding vector dimensions: {len(enriched_cv['embeddings']['vector'])}")
    print(f"  • Top 5 domain matches:")
    
    for i, (domain, score) in enumerate(enriched_cv['embeddings']['domain_scores'], 1):
        bar_length = int(score * 40)
        bar = "█" * bar_length
        print(f"    {i}. {domain:25s} {score:.4f}  {bar}")
    
    print("\n[4] Domain Classification Confidence")
    print("-" * 80)
    
    scores = enriched_cv['embeddings']['domain_scores']
    best_domain = scores[0][0]
    best_score = scores[0][1]
    second_best = scores[1][0] if len(scores) > 1 else None
    second_score = scores[1][1] if len(scores) > 1 else 0
    
    confidence = ((best_score - second_score) / best_score) * 100 if best_score > 0 else 0
    
    print(f"\n  Primary classification: {best_domain}")
    print(f"  Confidence score: {best_score:.4f}")
    print(f"  Confidence margin: {confidence:.1f}%")
    print(f"  Secondary option: {second_best} ({second_score:.4f})")
    
    print("\n[5] Full Enriched CV Data")
    print("-" * 80)
    print("\nStructure:")
    print(json.dumps({
        k: v if not isinstance(v, list) or len(str(v)) < 80 else f"[{len(v)} items]"
        for k, v in enriched_cv.items()
        if k != 'embeddings' or (isinstance(enriched_cv['embeddings'], dict))
    }, indent=2)[:500])
    
    print("\n" + "=" * 80)
    print("✓ Example completed successfully!")
    print("=" * 80)
    
    print("\nUsage via API:")
    print("""
    curl -X POST http://localhost:8000/parse-raw-cv \\
      -H "Content-Type: application/json" \\
      -d '{"raw_cv_text": "YOUR_RAW_CV_TEXT_HERE"}'
    """)
    
    print("\nUsage in Python:")
    print("""
    from AI.cv_processor import CVProcessor
    
    processor = CVProcessor()
    enriched_cv = processor.parse_and_process_raw_cv(raw_cv_text)
    print(f"Domain: {enriched_cv['embeddings']['best_domain']}")
    """)


if __name__ == "__main__":
    main()
